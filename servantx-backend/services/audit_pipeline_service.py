import hashlib
import json
import csv
import uuid
import os
from datetime import timedelta
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select, update

from core_services.db_service import AsyncSessionLocal
from models import AuditFinding, BatchRun, Document, DocumentRole, ParsedData
from services.edi_835_parser import parse_claim_835
from services.repricing_service import (
    build_line_findings,
    reprice_medicare_line,
    reprice_tx_medicaid_line,
)
from services.pipeline_config_service import get_payer_workflow_config

# Shared claim-splitting / payer-detection utilities now live in
# claim_adjudication_service so both the batch pipeline and the single-
# receipt flow use the same code.
from services.claim_adjudication_service import (
    extract_payer_metadata as _extract_payer_metadata,
    normalize_payer_key as _normalize_payer_key,
    split_835_claim_loops as _split_claim_loops,
    _split_segments,
)


CLAIM_SCHEMA_VERSION = "claim_835_v1"


def _read_storage_file(relative_path: str) -> str:
    storage_root = Path("uploads")
    full_path = storage_root / relative_path
    if not full_path.exists():
        raise FileNotFoundError(f"Storage file not found: {relative_path}")
    return full_path.read_text(encoding="utf-8", errors="ignore")


def _dict_to_notes_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=True)


def _parse_iso_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


async def _enqueue_stage2_parse(document_id: str):
    from tasks.parse import task_parse_claim_edi

    if os.getenv("ENABLE_CELERY_ASYNC", "false").lower() != "true":
        await run_stage2_parse_claim(document_id=document_id)
        return

    try:
        task_parse_claim_edi.delay(document_id)
    except Exception:
        # Keep local dev usable without Redis/Celery running.
        await run_stage2_parse_claim(document_id=document_id)


async def _enqueue_stage3_reprice(document_id: str):
    from tasks.reprice import task_reprice_claim

    if os.getenv("ENABLE_CELERY_ASYNC", "false").lower() != "true":
        await run_stage3_reprice_claim(document_id=document_id)
        return

    try:
        task_reprice_claim.delay(document_id)
    except Exception:
        await run_stage3_reprice_claim(document_id=document_id)


async def _enqueue_stage4_summarize(batch_id: str):
    from tasks.summarize import task_summarize_batch

    if os.getenv("ENABLE_CELERY_ASYNC", "false").lower() != "true":
        await run_stage4_summarize_batch(batch_id=batch_id)
        return

    try:
        task_summarize_batch.delay(batch_id)
    except Exception:
        await run_stage4_summarize_batch(batch_id=batch_id)


async def run_stage1_ingest_835_file(file_document_id: str, batch_id: str) -> Dict[str, Any]:
    async with AsyncSessionLocal() as db:
        file_doc_result = await db.execute(
            select(Document).where(
                Document.id == file_document_id,
                Document.batch_run_id == batch_id,
            )
        )
        file_document = file_doc_result.scalar_one_or_none()
        if not file_document:
            return {"status": "error", "message": "File document not found"}

        if not file_document.source_file_path:
            return {"status": "error", "message": "File document missing source_file_path"}

        batch_result = await db.execute(select(BatchRun).where(BatchRun.id == batch_id))
        batch = batch_result.scalar_one_or_none()
        if not batch:
            return {"status": "error", "message": "Batch run not found"}

        raw_text = _read_storage_file(file_document.source_file_path)
        payer_name, payer_id = _extract_payer_metadata(raw_text)
        payer_key = _normalize_payer_key(payer_name, payer_id)
        claims = _split_claim_loops(raw_text)

        if not claims:
            file_document.status = "error"
            file_document.notes = "No CLP claim loops found in uploaded 835 file."
            batch.failed_claim_count += 1
            await db.commit()
            return {"status": "error", "message": "No CLP claim loops found"}

        created_claim_ids: List[str] = []
        for index, claim_raw in enumerate(claims, start=1):
            claim_document = Document(
                receipt_id=None,
                hospital_id=file_document.hospital_id,
                batch_run_id=batch.id,
                contract_id=None,
                document_role=DocumentRole.CLAIM,
                parent_document_id=file_document.id,
                payer_key=payer_key,
                name=f"Claim {index} from {file_document.source_file_name or file_document.id}",
                status="queued_parse",
                amount=0.0,
                receipt_amount=0.0,
                contract_amount=0.0,
                underpayment_amount=0.0,
                notes=None,
                rules_applied=None,
            )
            db.add(claim_document)
            await db.flush()

            payload = {
                "schema_version": CLAIM_SCHEMA_VERSION,
                "batch_id": batch.id,
                "document_id": claim_document.id,
                "parent_file_document_id": file_document.id,
                "payer": {
                    "payer_key": payer_key,
                    "payer_name": payer_name,
                    "payer_id": payer_id,
                    "payer_type": "MEDICARE" if payer_key == "MEDICARE" else ("MEDICAID" if payer_key == "TX_MEDICAID_FFS" else "OTHER"),
                    "state": "TX" if payer_key == "TX_MEDICAID_FFS" else None,
                },
                "raw_claim_edi": claim_raw,
                "raw_edi_evidence": {
                    "claim_hash": hashlib.sha256(claim_raw.encode("utf-8")).hexdigest(),
                    "segment_count": len(_split_segments(claim_raw)),
                },
            }

            parsed_data = ParsedData(
                batch_id=batch.id,
                document_id=claim_document.id,
                schema_version=CLAIM_SCHEMA_VERSION,
                payload=payload,
            )
            db.add(parsed_data)
            created_claim_ids.append(claim_document.id)

        file_document.status = "parsed"
        file_document.amount = float(len(created_claim_ids))
        file_document.payer_key = payer_key
        file_document.notes = _dict_to_notes_json(
            {
                "stage": "ingest_complete",
                "claims_created": len(created_claim_ids),
                "payer_name": payer_name,
                "payer_id": payer_id,
            }
        )

        batch.status = "parsing"
        batch.claim_document_count = (batch.claim_document_count or 0) + len(created_claim_ids)
        batch.started_at = batch.started_at or datetime.utcnow()
        batch.updated_at = datetime.utcnow()

        await db.commit()

    for claim_document_id in created_claim_ids:
        await _enqueue_stage2_parse(claim_document_id)

    return {
        "status": "ok",
        "batch_id": batch_id,
        "file_document_id": file_document_id,
        "claims_created": len(created_claim_ids),
    }


async def run_stage2_parse_claim(document_id: str) -> Dict[str, Any]:
    async with AsyncSessionLocal() as db:
        doc_result = await db.execute(select(Document).where(Document.id == document_id))
        document = doc_result.scalar_one_or_none()
        if not document:
            return {"status": "error", "stage": 2, "message": "Document not found", "document_id": document_id}

        parsed_result = await db.execute(select(ParsedData).where(ParsedData.document_id == document.id))
        parsed_data = parsed_result.scalar_one_or_none()
        if not parsed_data:
            return {"status": "error", "stage": 2, "message": "ParsedData seed record missing", "document_id": document_id}

        payload = parsed_data.payload or {}
        raw_claim_edi = payload.get("raw_claim_edi")
        if not raw_claim_edi:
            document.status = "error"
            document.notes = "Missing raw_claim_edi in ParsedData payload."
            await db.commit()
            return {"status": "error", "stage": 2, "message": "Missing raw_claim_edi", "document_id": document_id}

        parsed_payload = parse_claim_835(
            raw_claim_edi=raw_claim_edi,
            batch_id=document.batch_run_id or payload.get("batch_id") or "",
            document_id=document.id,
            parent_file_document_id=document.parent_document_id,
            payer=payload.get("payer"),
        )

        parsed_data.schema_version = CLAIM_SCHEMA_VERSION
        parsed_data.payload = parsed_payload

        claim_data = parsed_payload.get("claim", {})
        provider_data = parsed_payload.get("provider", {})
        payer_data = parsed_payload.get("payer", {})

        document.payer_key = payer_data.get("payer_key")
        document.dos_start = _parse_iso_date(claim_data.get("service_date_start"))
        document.dos_end = _parse_iso_date(claim_data.get("service_date_end"))
        document.billing_npi = provider_data.get("billing_provider_npi")
        document.rendering_npi = provider_data.get("rendering_provider_npi")
        document.facility_npi = provider_data.get("facility_npi")
        document.status = "parsed"
        document.updated_at = datetime.utcnow()

        if document.batch_run_id:
            batch_result = await db.execute(select(BatchRun).where(BatchRun.id == document.batch_run_id))
            batch = batch_result.scalar_one_or_none()
            if batch and batch.status in ("queued", "parsing"):
                batch.status = "reviewing"
                batch.updated_at = datetime.utcnow()

        await db.commit()

    await _enqueue_stage3_reprice(document.id)
    return {"status": "ok", "stage": 2, "document_id": document_id}


async def run_stage3_reprice_claim(document_id: str) -> Dict[str, Any]:
    should_enqueue_summary = False
    batch_id_for_summary: Optional[str] = None

    async with AsyncSessionLocal() as db:
        doc_result = await db.execute(select(Document).where(Document.id == document_id))
        document = doc_result.scalar_one_or_none()
        if not document:
            return {"status": "error", "stage": 3, "message": "Document not found", "document_id": document_id}

        parsed_result = await db.execute(select(ParsedData).where(ParsedData.document_id == document.id))
        parsed_data = parsed_result.scalar_one_or_none()
        if not parsed_data:
            document.status = "error"
            document.notes = "ParsedData record missing for repricing."
            await db.commit()
            return {"status": "error", "stage": 3, "message": "ParsedData missing", "document_id": document_id}

        payload = parsed_data.payload or {}
        payer = payload.get("payer", {}) or {}
        claim = payload.get("claim", {}) or {}
        provider = payload.get("provider", {}) or {}
        service_lines = payload.get("service_lines", []) or []
        payer_key = payer.get("payer_key") or document.payer_key or "OTHER"

        existing_findings_result = await db.execute(
            select(AuditFinding).where(AuditFinding.document_id == document.id)
        )
        for finding in existing_findings_result.scalars().all():
            await db.delete(finding)

        repricing_lines: List[Dict[str, Any]] = []
        findings_written = 0
        total_expected = 0.0
        total_paid = 0.0
        total_variance = 0.0

        for line in service_lines:
            context = {
                "provider": provider,
                "service_date_start": claim.get("service_date_start"),
            }
            if payer_key == "MEDICARE":
                repricing_result = await reprice_medicare_line(db=db, line=line, context=context)
            elif payer_key == "TX_MEDICAID_FFS":
                repricing_result = await reprice_tx_medicaid_line(db=db, line=line, context=context)
            else:
                repricing_result = {
                    "errors": ["MISSING_RATE_MATCH"],
                    "expected_allowed": None,
                    "actual_paid": float(line.get("line_payment_amount") or 0.0),
                    "variance_amount": None,
                    "variance_percent": None,
                    "rate_source": "UNSUPPORTED_PAYER_PHASE1",
                    "locality_code": None,
                    "locality_source": "UNKNOWN",
                    "confidence_score": 10.0,
                }

            expected_allowed = repricing_result.get("expected_allowed")
            actual_paid = float(repricing_result.get("actual_paid") or float(line.get("line_payment_amount") or 0.0))
            variance_amount = (
                float(repricing_result.get("variance_amount"))
                if repricing_result.get("variance_amount") is not None
                else (float(expected_allowed) - actual_paid if expected_allowed is not None else 0.0)
            )
            variance_percent = (
                float(repricing_result.get("variance_percent"))
                if repricing_result.get("variance_percent") is not None
                else ((variance_amount / float(expected_allowed) * 100.0) if expected_allowed else 0.0)
            )

            if expected_allowed is not None:
                total_expected += float(expected_allowed)
            total_paid += actual_paid
            if variance_amount > 0:
                total_variance += variance_amount

            line_findings = build_line_findings(line=line, repricing_result=repricing_result)
            finding_codes = {finding["finding_code"] for finding in line_findings}
            if "ALLOWED_MISMATCH" in finding_codes:
                repricing_result["confidence_score"] = max(
                    0.0,
                    float(repricing_result.get("confidence_score") or 0.0) - 20.0,
                )
            elif "LOCALITY_UNKNOWN" in finding_codes:
                repricing_result["confidence_score"] = max(
                    0.0,
                    float(repricing_result.get("confidence_score") or 0.0) - 10.0,
                )
            for finding_payload in line_findings:
                finding = AuditFinding(
                    batch_id=document.batch_run_id or "",
                    document_id=document.id,
                    finding_code=finding_payload["finding_code"],
                    severity=finding_payload["severity"],
                    confidence_score=finding_payload.get("confidence_score"),
                    variance_amount=finding_payload.get("variance_amount"),
                    metadata_json={
                        "line_number": line.get("line_number"),
                        "cpt_hcpcs": line.get("cpt_hcpcs"),
                        "modifiers": line.get("modifiers", []),
                        "place_of_service": line.get("place_of_service"),
                        "repricing_result": repricing_result,
                    },
                )
                db.add(finding)
                findings_written += 1

            repricing_lines.append(
                {
                    "line_number": line.get("line_number"),
                    "cpt_hcpcs": line.get("cpt_hcpcs"),
                    "modifiers": line.get("modifiers", []),
                    "units": line.get("units"),
                    "place_of_service": line.get("place_of_service"),
                    "line_service_date": line.get("line_service_date"),
                    "expected_allowed": round(float(expected_allowed), 2) if expected_allowed is not None else None,
                    "actual_paid": round(actual_paid, 2),
                    "variance_amount": round(variance_amount, 2),
                    "variance_percent": round(variance_percent, 2),
                    "rate_source": repricing_result.get("rate_source"),
                    "locality_code": repricing_result.get("locality_code"),
                    "locality_source": repricing_result.get("locality_source"),
                    "confidence_score": repricing_result.get("confidence_score"),
                    "errors": repricing_result.get("errors", []),
                }
            )

        payload_with_repricing = dict(payload)
        payload_with_repricing["repricing"] = {
            "line_results": repricing_lines,
            "totals": {
                "expected_allowed_total": round(total_expected, 2),
                "actual_paid_total": round(total_paid, 2),
                "variance_total": round(total_variance, 2),
            },
        }
        await db.execute(
            update(ParsedData)
            .where(ParsedData.id == parsed_data.id)
            .values(payload=payload_with_repricing, updated_at=datetime.utcnow())
        )
        parsed_data.payload = payload_with_repricing

        document.amount = round(total_variance, 2)
        document.receipt_amount = round(total_paid, 2)
        document.contract_amount = round(total_expected, 2)
        document.underpayment_amount = round(total_variance, 2)
        document.status = "reviewed"
        document.updated_at = datetime.utcnow()

        if document.batch_run_id:
            batch_id_for_summary = document.batch_run_id
            batch_result = await db.execute(select(BatchRun).where(BatchRun.id == document.batch_run_id))
            batch = batch_result.scalar_one_or_none()
            if batch:
                reviewed_count_result = await db.execute(
                    select(func.count(Document.id)).where(
                        Document.batch_run_id == batch.id,
                        Document.document_role == DocumentRole.CLAIM,
                        Document.status.in_(["reviewed", "synthesized", "appeal_ready"]),
                    )
                )
                reviewed_count = int(reviewed_count_result.scalar() or 0)
                batch.processed_claim_count = reviewed_count
                batch.status = "reviewing"
                batch.updated_at = datetime.utcnow()

                if batch.claim_document_count > 0 and reviewed_count >= batch.claim_document_count:
                    batch.status = "synthesizing"
                    should_enqueue_summary = True

        await db.commit()

    if should_enqueue_summary and batch_id_for_summary:
        await _enqueue_stage4_summarize(batch_id_for_summary)

    return {
        "status": "ok",
        "stage": 3,
        "document_id": document_id,
        "findings_created": findings_written,
        "variance_total": round(total_variance, 2),
    }


async def run_stage4_summarize_batch(batch_id: str) -> Dict[str, Any]:
    async with AsyncSessionLocal() as db:
        batch_result = await db.execute(select(BatchRun).where(BatchRun.id == batch_id))
        batch = batch_result.scalar_one_or_none()
        if not batch:
            return {"status": "error", "stage": 4, "message": "Batch not found", "batch_id": batch_id}

        docs_result = await db.execute(
            select(Document).where(
                Document.batch_run_id == batch_id,
                Document.document_role == DocumentRole.CLAIM,
            )
        )
        claim_docs = docs_result.scalars().all()

        parsed_rows_result = await db.execute(select(ParsedData).where(ParsedData.batch_id == batch_id))
        parsed_rows = parsed_rows_result.scalars().all()
        parsed_by_doc_id = {row.document_id: row.payload or {} for row in parsed_rows}

        total_claims = len(claim_docs)
        total_service_lines = 0
        total_paid = 0.0
        total_expected = 0.0
        total_variance = 0.0
        claims_flagged = 0

        cpt_variance: Dict[str, float] = {}
        provider_variance: Dict[str, float] = {}
        pattern_variance: Dict[str, Dict[str, Any]] = {}

        for doc in claim_docs:
            payload = parsed_by_doc_id.get(doc.id, {})
            repricing = payload.get("repricing", {})
            line_results = repricing.get("line_results", []) or []
            totals = repricing.get("totals", {}) or {}

            total_service_lines += len(line_results)
            total_paid += float(totals.get("actual_paid_total") or 0.0)
            total_expected += float(totals.get("expected_allowed_total") or 0.0)
            doc_variance = float(totals.get("variance_total") or 0.0)
            total_variance += doc_variance
            if doc_variance > 0:
                claims_flagged += 1

            provider_key = doc.facility_npi or doc.rendering_npi or doc.billing_npi or "UNKNOWN_PROVIDER"
            provider_variance[provider_key] = provider_variance.get(provider_key, 0.0) + doc_variance

            for line in line_results:
                line_variance = float(line.get("variance_amount") or 0.0)
                cpt = line.get("cpt_hcpcs") or "UNKNOWN_CPT"
                cpt_variance[cpt] = cpt_variance.get(cpt, 0.0) + line_variance

                modifiers = line.get("modifiers", []) or []
                modifier_value = modifiers[0] if modifiers else ""
                pattern_key = (
                    f"{doc.payer_key or 'OTHER'}|{cpt}|{modifier_value}|"
                    f"{line.get('place_of_service') or 'UNK'}|{line.get('locality_code') or 'UNK'}"
                )
                current = pattern_variance.get(pattern_key)
                if not current:
                    current = {
                        "payerKey": doc.payer_key or "OTHER",
                        "cptHcpcs": cpt,
                        "modifier": modifier_value or None,
                        "placeOfService": line.get("place_of_service"),
                        "localityCode": line.get("locality_code"),
                        "claimCount": 0,
                        "totalVariance": 0.0,
                        "confidenceSum": 0.0,
                        "confidenceCount": 0,
                    }
                current["claimCount"] += 1
                current["totalVariance"] += line_variance
                if line.get("confidence_score") is not None:
                    current["confidenceSum"] += float(line.get("confidence_score") or 0.0)
                    current["confidenceCount"] += 1
                pattern_variance[pattern_key] = current

        top_cpts = [
            {"cptHcpcs": cpt, "totalVariance": round(amount, 2)}
            for cpt, amount in sorted(cpt_variance.items(), key=lambda item: item[1], reverse=True)[:10]
        ]
        top_providers = [
            {"providerId": provider_id, "totalVariance": round(amount, 2)}
            for provider_id, amount in sorted(provider_variance.items(), key=lambda item: item[1], reverse=True)[:10]
        ]

        top_patterns: List[Dict[str, Any]] = []
        for _, pattern in sorted(
            pattern_variance.items(),
            key=lambda item: item[1]["totalVariance"],
            reverse=True,
        )[:20]:
            confidence_avg = (
                pattern["confidenceSum"] / pattern["confidenceCount"] if pattern["confidenceCount"] > 0 else 0.0
            )
            top_patterns.append(
                {
                    "payerKey": pattern["payerKey"],
                    "cptHcpcs": pattern["cptHcpcs"],
                    "modifier": pattern["modifier"],
                    "placeOfService": pattern["placeOfService"],
                    "localityCode": pattern["localityCode"],
                    "claimCount": pattern["claimCount"],
                    "totalVariance": round(pattern["totalVariance"], 2),
                    "confidence": round(confidence_avg, 2),
                }
            )

        summary_json = {
            "total_claims": total_claims,
            "total_service_lines": total_service_lines,
            "total_paid": round(total_paid, 2),
            "total_expected": round(total_expected, 2),
            "total_variance": round(total_variance, 2),
            "claims_flagged": claims_flagged,
            "top_cpts": top_cpts,
            "top_providers": top_providers,
            "top_patterns": top_patterns,
            "synthesized_at": datetime.utcnow().isoformat(),
        }
        executive_summary = (
            f"Processed {total_claims} claims and {total_service_lines} service lines. "
            f"Expected ${total_expected:,.2f}, paid ${total_paid:,.2f}, total variance ${total_variance:,.2f}. "
            f"{claims_flagged} claims were flagged for possible underpayment."
        )

        batch.executive_summary = executive_summary
        batch.reconciliation_json = summary_json
        batch.status = "synthesized"
        batch.updated_at = datetime.utcnow()

        for doc in claim_docs:
            if doc.status == "reviewed":
                doc.status = "synthesized"

        await db.commit()

    return {
        "status": "ok",
        "stage": 4,
        "batch_id": batch_id,
        "summary": summary_json,
    }


async def run_stage5_build_appeals(
    batch_id: str,
    payer_key: Optional[str] = None,
    minimum_variance: Optional[float] = None,
) -> Dict[str, Any]:
    minimum_variance = float(minimum_variance if minimum_variance is not None else 0.01)
    workflow_config = get_payer_workflow_config()
    appeals_root = Path("uploads") / "appeals" / batch_id
    appeals_root.mkdir(parents=True, exist_ok=True)

    async with AsyncSessionLocal() as db:
        batch_result = await db.execute(select(BatchRun).where(BatchRun.id == batch_id))
        batch = batch_result.scalar_one_or_none()
        if not batch:
            return {"status": "error", "stage": 5, "message": "Batch not found", "batch_id": batch_id}

        docs_result = await db.execute(
            select(Document).where(
                Document.batch_run_id == batch_id,
                Document.document_role == DocumentRole.CLAIM,
            )
        )
        claim_docs = docs_result.scalars().all()
        if not claim_docs:
            return {"status": "error", "stage": 5, "message": "No claim documents found", "batch_id": batch_id}

        parsed_result = await db.execute(select(ParsedData).where(ParsedData.batch_id == batch_id))
        parsed_rows = parsed_result.scalars().all()
        parsed_by_doc_id = {row.document_id: row.payload or {} for row in parsed_rows}

        # If payer is not explicitly provided, use the highest-variance payer in batch.
        if not payer_key:
            payer_totals: Dict[str, float] = {}
            for doc in claim_docs:
                payer = doc.payer_key or "OTHER"
                payer_totals[payer] = payer_totals.get(payer, 0.0) + float(doc.underpayment_amount or 0.0)
            payer_key = max(payer_totals.items(), key=lambda kv: kv[1])[0]

        selected_docs = [doc for doc in claim_docs if (doc.payer_key or "OTHER") == payer_key and float(doc.underpayment_amount or 0.0) >= minimum_variance]
        if not selected_docs:
            return {
                "status": "error",
                "stage": 5,
                "message": "No eligible claims matched filters",
                "batch_id": batch_id,
                "payer_key": payer_key,
            }

        claims_output: List[Dict[str, Any]] = []
        variance_rows: List[Dict[str, Any]] = []
        raw_evidence_chunks: List[str] = []
        total_expected = 0.0
        total_paid = 0.0
        total_variance = 0.0

        for doc in selected_docs:
            payload = parsed_by_doc_id.get(doc.id, {})
            claim_data = payload.get("claim", {}) or {}
            repricing = payload.get("repricing", {}) or {}
            line_results = repricing.get("line_results", []) or []
            raw_edi_evidence = payload.get("raw_edi_evidence", {}) or {}

            claim_lines = []
            for line in line_results:
                expected = float(line.get("expected_allowed") or 0.0)
                paid = float(line.get("actual_paid") or 0.0)
                variance = float(line.get("variance_amount") or 0.0)
                if variance < minimum_variance:
                    continue

                claim_lines.append(
                    {
                        "cpt": line.get("cpt_hcpcs"),
                        "modifiers": line.get("modifiers", []),
                        "units": line.get("units"),
                        "pos": line.get("place_of_service"),
                        "dos": line.get("line_service_date"),
                        "expected": round(expected, 2),
                        "paid": round(paid, 2),
                        "variance": round(variance, 2),
                        "rate_source": line.get("rate_source"),
                    }
                )
                variance_rows.append(
                    {
                        "claim_document_id": doc.id,
                        "payer_claim_control_number": claim_data.get("payer_claim_control_number"),
                        "cpt_hcpcs": line.get("cpt_hcpcs"),
                        "modifiers": ",".join(line.get("modifiers", [])),
                        "pos": line.get("place_of_service"),
                        "dos": line.get("line_service_date"),
                        "expected": round(expected, 2),
                        "paid": round(paid, 2),
                        "variance": round(variance, 2),
                        "rate_source": line.get("rate_source"),
                        "locality_code": line.get("locality_code"),
                        "locality_source": line.get("locality_source"),
                    }
                )
                total_expected += expected
                total_paid += paid
                total_variance += variance

            if claim_lines:
                claims_output.append(
                    {
                        "claim_document_id": doc.id,
                        "payer_claim_control_number": claim_data.get("payer_claim_control_number"),
                        "service_lines": claim_lines,
                    }
                )
                raw_evidence_chunks.append(
                    "\n".join(
                        [
                            f"Document: {doc.id}",
                            f"CLP: {raw_edi_evidence.get('clp_segment', '')}",
                            f"SVC: {' | '.join(raw_edi_evidence.get('svc_segments', []))}",
                            f"CAS: {' | '.join(raw_edi_evidence.get('cas_segments', []))}",
                        ]
                    )
                )

        packet_id = str(uuid.uuid4())
        payer_cfg = workflow_config.get(payer_key, {})
        deadline_days = int(payer_cfg.get("deadline_days", 120))
        deadline_date = (datetime.utcnow() + timedelta(days=deadline_days)).date().isoformat()

        variance_table_name = f"{packet_id}_variance_table.csv"
        variance_table_path = appeals_root / variance_table_name
        with open(variance_table_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=[
                    "claim_document_id",
                    "payer_claim_control_number",
                    "cpt_hcpcs",
                    "modifiers",
                    "pos",
                    "dos",
                    "expected",
                    "paid",
                    "variance",
                    "rate_source",
                    "locality_code",
                    "locality_source",
                ],
            )
            writer.writeheader()
            for row in variance_rows:
                writer.writerow(row)

        claim_evidence_name = f"{packet_id}_raw_835_evidence.txt"
        claim_evidence_path = appeals_root / claim_evidence_name
        claim_evidence_path.write_text("\n\n".join(raw_evidence_chunks), encoding="utf-8")

        form_name = f"{packet_id}_forms.json"
        form_path = appeals_root / form_name
        form_payload = {
            "forms": payer_cfg.get("required_forms", []),
            "required_fields": payer_cfg.get("required_fields", []),
            "appeal_type": payer_cfg.get("appeal_type"),
            "payer_key": payer_key,
        }
        form_path.write_text(json.dumps(form_payload, indent=2), encoding="utf-8")

        cover_letter_name = f"{packet_id}_cover_letter.txt"
        cover_letter_path = appeals_root / cover_letter_name
        cover_letter_text = (
            f"Appeal packet {packet_id}\n"
            f"Payer: {payer_key}\n"
            f"Appeal type: {payer_cfg.get('appeal_type', 'REDETERMINATION')}\n"
            f"Claims included: {len(claims_output)}\n"
            f"Total variance: ${total_variance:,.2f}\n"
            f"Generated at: {datetime.utcnow().isoformat()}\n"
        )
        cover_letter_path.write_text(cover_letter_text, encoding="utf-8")

        packet = {
            "packet_id": packet_id,
            "payer_key": payer_key,
            "appeal_type": payer_cfg.get("appeal_type", "REDETERMINATION"),
            "submission": {
                "method": payer_cfg.get("submission_method", "MAIL"),
                "destination": payer_cfg.get("destination", "Configured destination"),
                "deadline_date": deadline_date,
            },
            "forms": [
                {
                    "form_id": form_id,
                    "format": "JSON",
                    "storage_key": f"appeals/{batch_id}/{form_name}",
                }
                for form_id in payer_cfg.get("required_forms", [])
            ],
            "cover_letter": {
                "format": "TXT",
                "storage_key": f"appeals/{batch_id}/{cover_letter_name}",
            },
            "variance_table": {
                "format": "CSV",
                "storage_key": f"appeals/{batch_id}/{variance_table_name}",
            },
            "rate_evidence": [
                {
                    "format": "CSV",
                    "storage_key": f"appeals/{batch_id}/{variance_table_name}",
                    "version_label": "phase1_runtime",
                }
            ],
            "claim_evidence": [
                {
                    "format": "TXT",
                    "storage_key": f"appeals/{batch_id}/{claim_evidence_name}",
                    "description": "835 CLP/SVC/CAS extracts",
                }
            ],
            "claims": claims_output,
            "totals": {
                "expected": round(total_expected, 2),
                "paid": round(total_paid, 2),
                "variance": round(total_variance, 2),
            },
            "checklist": {
                "required_fields_complete": len(claims_output) > 0 and len(variance_rows) > 0,
                "missing_items": [],
            },
        }

        merged_reconciliation = batch.reconciliation_json or {}
        merged_reconciliation["appeal_packet"] = packet
        merged_reconciliation["appeal_generated_at"] = datetime.utcnow().isoformat()
        batch.reconciliation_json = merged_reconciliation
        batch.status = "appeal_ready"
        batch.updated_at = datetime.utcnow()
        batch.finished_at = datetime.utcnow()

        for doc in selected_docs:
            doc.status = "appeal_ready"

        await db.commit()

    return {
        "status": "ok",
        "stage": 5,
        "batch_id": batch_id,
        "payer_key": payer_key,
        "packet": packet,
    }

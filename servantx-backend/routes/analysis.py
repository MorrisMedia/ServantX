from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from core_services.db_service import AsyncSessionLocal
from models import BatchRun, Document, DocumentRole, ParsedData
from routes.auth import get_current_user
from schemas import AnalysisSummaryResponse, PatternRow


router = APIRouter(prefix="/analysis", tags=["analysis"])


def _merge_top_rows(rows: List[Dict[str, Any]], key_field: str, value_field: str, top_n: int = 10) -> List[Dict[str, Any]]:
    accumulator: Dict[str, float] = {}
    for row in rows:
        key = str(row.get(key_field) or "UNKNOWN")
        accumulator[key] = accumulator.get(key, 0.0) + float(row.get(value_field) or 0.0)
    return [
        {key_field: key, value_field: round(value, 2)}
        for key, value in sorted(accumulator.items(), key=lambda item: item[1], reverse=True)[:top_n]
    ]


@router.get("", response_model=AnalysisSummaryResponse)
async def get_analysis_summary(
    batch_id: Optional[str] = Query(None, alias="batchId"),
    current_user: dict = Depends(get_current_user),
):
    try:
        async with AsyncSessionLocal() as db:
            query = select(BatchRun).where(BatchRun.hospital_id == current_user["hospital_id"])
            if batch_id:
                query = query.where(BatchRun.id == batch_id)
            batches_result = await db.execute(query)
            batches = list(batches_result.scalars().all())

        if not batches:
            return AnalysisSummaryResponse(
                totalClaims=0,
                totalServiceLines=0,
                totalPaid=0.0,
                totalExpected=0.0,
                totalVariance=0.0,
                claimsFlagged=0,
                topCpts=[],
                topProviders=[],
                topPatterns=[],
            )

        total_claims = 0
        total_service_lines = 0
        total_paid = 0.0
        total_expected = 0.0
        total_variance = 0.0
        claims_flagged = 0
        all_cpts: List[Dict[str, Any]] = []
        all_providers: List[Dict[str, Any]] = []
        all_patterns: List[Dict[str, Any]] = []

        for batch in batches:
            summary = batch.reconciliation_json or {}
            total_claims += int(summary.get("total_claims", 0))
            total_service_lines += int(summary.get("total_service_lines", 0))
            total_paid += float(summary.get("total_paid", 0.0))
            total_expected += float(summary.get("total_expected", 0.0))
            total_variance += float(summary.get("total_variance", 0.0))
            claims_flagged += int(summary.get("claims_flagged", 0))
            all_cpts.extend(summary.get("top_cpts", []))
            all_providers.extend(summary.get("top_providers", []))
            all_patterns.extend(summary.get("top_patterns", []))

        merged_top_cpts = _merge_top_rows(all_cpts, key_field="cptHcpcs", value_field="totalVariance", top_n=10)
        merged_top_providers = _merge_top_rows(all_providers, key_field="providerId", value_field="totalVariance", top_n=10)

        pattern_accumulator: Dict[Tuple[str, str, str, str, str], Dict[str, Any]] = {}
        for row in all_patterns:
            key = (
                str(row.get("payerKey") or "OTHER"),
                str(row.get("cptHcpcs") or "UNKNOWN"),
                str(row.get("modifier") or ""),
                str(row.get("placeOfService") or "UNK"),
                str(row.get("localityCode") or "UNK"),
            )
            current = pattern_accumulator.get(key)
            if not current:
                current = {
                    "payerKey": key[0],
                    "cptHcpcs": key[1],
                    "modifier": key[2] or None,
                    "placeOfService": key[3],
                    "localityCode": key[4],
                    "claimCount": 0,
                    "totalVariance": 0.0,
                    "confidence": 0.0,
                    "confidenceCount": 0,
                }
            current["claimCount"] += int(row.get("claimCount", 0))
            current["totalVariance"] += float(row.get("totalVariance", 0.0))
            if row.get("confidence") is not None:
                current["confidence"] += float(row.get("confidence", 0.0))
                current["confidenceCount"] += 1
            pattern_accumulator[key] = current

        merged_patterns: List[PatternRow] = []
        for _, row in sorted(
            pattern_accumulator.items(),
            key=lambda item: item[1]["totalVariance"],
            reverse=True,
        )[:20]:
            avg_confidence = row["confidence"] / row["confidenceCount"] if row["confidenceCount"] > 0 else 0.0
            merged_patterns.append(
                PatternRow(
                    payerKey=row["payerKey"],
                    cptHcpcs=row["cptHcpcs"],
                    modifier=row["modifier"],
                    placeOfService=row["placeOfService"],
                    localityCode=row["localityCode"],
                    claimCount=row["claimCount"],
                    totalVariance=round(row["totalVariance"], 2),
                    confidence=round(avg_confidence, 2),
                )
            )

        return AnalysisSummaryResponse(
            totalClaims=total_claims,
            totalServiceLines=total_service_lines,
            totalPaid=round(total_paid, 2),
            totalExpected=round(total_expected, 2),
            totalVariance=round(total_variance, 2),
            claimsFlagged=claims_flagged,
            topCpts=[PatternRow(**{**row, "claimCount": 0, "confidence": 0.0}) for row in merged_top_cpts],
            topProviders=merged_top_providers,
            topPatterns=merged_patterns,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analysis summary: {str(e)}",
        )


@router.get("/patterns", response_model=List[PatternRow])
async def get_analysis_patterns(
    batch_id: Optional[str] = Query(None, alias="batchId"),
    current_user: dict = Depends(get_current_user),
):
    try:
        async with AsyncSessionLocal() as db:
            doc_query = select(Document).where(
                Document.hospital_id == current_user["hospital_id"],
                Document.document_role == DocumentRole.CLAIM,
            )
            if batch_id:
                doc_query = doc_query.where(Document.batch_run_id == batch_id)
            docs_result = await db.execute(doc_query)
            docs = docs_result.scalars().all()
            doc_ids = [doc.id for doc in docs]

            if not doc_ids:
                return []

            parsed_result = await db.execute(
                select(ParsedData).where(ParsedData.document_id.in_(doc_ids))
            )
            parsed_rows = parsed_result.scalars().all()

            doc_map = {doc.id: doc for doc in docs}
            pattern_accumulator: Dict[Tuple[str, str, str, str, str], Dict[str, Any]] = {}
            for parsed in parsed_rows:
                payload = parsed.payload or {}
                repricing = payload.get("repricing", {})
                for line in repricing.get("line_results", []) or []:
                    doc = doc_map.get(parsed.document_id)
                    payer_key = (doc.payer_key if doc else None) or (payload.get("payer", {}) or {}).get("payer_key") or "OTHER"
                    cpt = str(line.get("cpt_hcpcs") or "UNKNOWN")
                    modifiers = line.get("modifiers", []) or []
                    modifier = str(modifiers[0] if modifiers else "")
                    pos = str(line.get("place_of_service") or "UNK")
                    locality = str(line.get("locality_code") or "UNK")
                    key = (payer_key, cpt, modifier, pos, locality)
                    current = pattern_accumulator.get(key)
                    if not current:
                        current = {
                            "payerKey": payer_key,
                            "cptHcpcs": cpt,
                            "modifier": modifier or None,
                            "placeOfService": pos,
                            "localityCode": locality,
                            "claimCount": 0,
                            "totalVariance": 0.0,
                            "confidence": 0.0,
                            "confidenceCount": 0,
                        }
                    current["claimCount"] += 1
                    current["totalVariance"] += float(line.get("variance_amount") or 0.0)
                    if line.get("confidence_score") is not None:
                        current["confidence"] += float(line.get("confidence_score") or 0.0)
                        current["confidenceCount"] += 1
                    pattern_accumulator[key] = current

        patterns: List[PatternRow] = []
        for _, row in sorted(
            pattern_accumulator.items(),
            key=lambda item: item[1]["totalVariance"],
            reverse=True,
        ):
            avg_confidence = row["confidence"] / row["confidenceCount"] if row["confidenceCount"] > 0 else 0.0
            patterns.append(
                PatternRow(
                    payerKey=row["payerKey"],
                    cptHcpcs=row["cptHcpcs"],
                    modifier=row["modifier"],
                    placeOfService=row["placeOfService"],
                    localityCode=row["localityCode"],
                    claimCount=row["claimCount"],
                    totalVariance=round(row["totalVariance"], 2),
                    confidence=round(avg_confidence, 2),
                )
            )
        return patterns
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch analysis patterns: {str(e)}",
        )


@router.get("/coverage")
async def get_rate_coverage_report(
    batch_id: Optional[str] = Query(None, alias="batchId"),
    current_user: dict = Depends(get_current_user),
):
    """
    Coverage quality report for rates/locality matching and sanity checks.
    """
    try:
        async with AsyncSessionLocal() as db:
            doc_query = select(Document).where(
                Document.hospital_id == current_user["hospital_id"],
                Document.document_role == DocumentRole.CLAIM,
            )
            if batch_id:
                doc_query = doc_query.where(Document.batch_run_id == batch_id)
            docs_result = await db.execute(doc_query)
            docs = docs_result.scalars().all()
            doc_ids = [doc.id for doc in docs]
            if not doc_ids:
                return {
                    "lineCount": 0,
                    "matchedRateCount": 0,
                    "knownLocalityCount": 0,
                    "matchedRatePercent": 0.0,
                    "knownLocalityPercent": 0.0,
                    "allowedMismatchCount": 0,
                    "topMissingRateCpts": [],
                }

            parsed_result = await db.execute(select(ParsedData).where(ParsedData.document_id.in_(doc_ids)))
            parsed_rows = parsed_result.scalars().all()

        line_count = 0
        matched_rate_count = 0
        known_locality_count = 0
        allowed_mismatch_count = 0
        missing_rate_cpt_counts: Dict[str, int] = {}

        for parsed in parsed_rows:
            payload = parsed.payload or {}
            repricing = payload.get("repricing", {}) or {}
            for line in repricing.get("line_results", []) or []:
                line_count += 1
                errors = set(line.get("errors", []) or [])
                cpt = str(line.get("cpt_hcpcs") or "UNKNOWN")
                expected = line.get("expected_allowed")
                locality_code = line.get("locality_code")

                if expected is not None:
                    matched_rate_count += 1
                if locality_code:
                    known_locality_count += 1
                if "ALLOWED_MISMATCH" in errors:
                    allowed_mismatch_count += 1
                if "MISSING_RATE_MATCH" in errors:
                    missing_rate_cpt_counts[cpt] = missing_rate_cpt_counts.get(cpt, 0) + 1

        top_missing = [
            {"cptHcpcs": cpt, "count": count}
            for cpt, count in sorted(missing_rate_cpt_counts.items(), key=lambda item: item[1], reverse=True)[:10]
        ]
        return {
            "lineCount": line_count,
            "matchedRateCount": matched_rate_count,
            "knownLocalityCount": known_locality_count,
            "matchedRatePercent": round((matched_rate_count / line_count * 100.0), 2) if line_count else 0.0,
            "knownLocalityPercent": round((known_locality_count / line_count * 100.0), 2) if line_count else 0.0,
            "allowedMismatchCount": allowed_mismatch_count,
            "topMissingRateCpts": top_missing,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch coverage report: {str(e)}",
        )

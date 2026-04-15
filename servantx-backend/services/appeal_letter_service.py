"""
Generates payer-addressed appeal letters for underpaid claims.

Given a Document with underpayment findings, produces a formal appeal letter
that cites:
  - Specific contract terms (from rule_library)
  - Medicare/Medicaid fee schedule basis
  - Regulatory citations (42 CFR, state Medicaid rules)
  - Exact underpayment amount and calculation
"""

import json
from typing import Optional
from datetime import date

from sqlalchemy import select

from core_services.db_service import AsyncSessionLocal
import asyncio
from core_services.openai_service import chat_with_openai_async, chat_with_openai_async_tracked
from services.cost_service import log_ai_cost
from models import Contract, Document, ParsedData, AuditFinding


SYSTEM_PROMPT = """You are a healthcare revenue integrity specialist drafting a formal underpayment appeal letter to a payer.
Write a professional, fact-based letter. Be specific about amounts and contract terms.
Cite relevant regulations. Format as a business letter. Do not be aggressive or accusatory.
Output only the letter text — no commentary."""


async def generate_appeal_letter(
    document_id: str,
    hospital_id: str,
    additional_context: str = "",
) -> dict:
    """
    Generates a formal appeal letter for an underpaid claim.

    Returns: {
        "success": bool,
        "letter": str,           # Full appeal letter text
        "appeal_status": "drafted",
        "summary": str,          # 1-2 sentence summary
        "error": str,            # only present on failure
    }
    """
    try:
        async with AsyncSessionLocal() as db:
            # Fetch Document
            doc_result = await db.execute(
                select(Document).where(
                    Document.id == document_id,
                    Document.hospital_id == hospital_id,
                )
            )
            document = doc_result.scalar_one_or_none()
            if not document:
                return {"success": False, "error": "Document not found or access denied"}

            # Fetch ParsedData
            parsed_result = await db.execute(
                select(ParsedData).where(ParsedData.document_id == document_id)
            )
            parsed = parsed_result.scalar_one_or_none()

            # Fetch AuditFindings
            finding_result = await db.execute(
                select(AuditFinding).where(AuditFinding.document_id == document_id)
            )
            findings = finding_result.scalars().all()

            # Fetch Contract
            contract = None
            if document.contract_id:
                contract_result = await db.execute(
                    select(Contract).where(Contract.id == document.contract_id)
                )
                contract = contract_result.scalar_one_or_none()

        # --- Extract claim data ---
        parsed_payload = parsed.payload if parsed else {}
        claim_info = parsed_payload.get("claim_info", {}) if parsed_payload else {}
        repricing = parsed_payload.get("repricing", {}) if parsed_payload else {}

        # Hospital / payer info
        hospital_name = claim_info.get("billing_provider_name") or "Hospital"
        payer_key = document.payer_key or claim_info.get("payer_id") or "UNKNOWN"
        payer_name = claim_info.get("payer_name") or repricing.get("payer_name") or ""
        claim_id = (
            claim_info.get("claim_id")
            or claim_info.get("claim_number")
            or document.name
            or document.id
        )
        patient_account = claim_info.get("patient_account_number") or claim_info.get("patient_id") or "N/A"

        # Date of service
        dos_start = document.dos_start
        dos_end = document.dos_end
        if dos_start and dos_end and dos_start != dos_end:
            dos = f"{dos_start} – {dos_end}"
        elif dos_start:
            dos = str(dos_start)
        else:
            dos = claim_info.get("statement_from_date") or claim_info.get("service_date") or "N/A"

        claim_type = claim_info.get("claim_type") or claim_info.get("type_of_bill") or "Professional/Facility"

        # Financial data — prefer document fields, fall back to repricing payload
        expected_payment = float(repricing.get("expected_payment") or repricing.get("allowed_amount") or document.contract_amount or 0.0)
        actual_paid = float(repricing.get("actual_paid") or repricing.get("paid_amount") or document.receipt_amount or 0.0)
        variance = float(repricing.get("variance") or repricing.get("underpayment") or document.underpayment_amount or 0.0)
        variance_pct = float(repricing.get("variance_percent") or (
            (variance / expected_payment * 100.0) if expected_payment > 0 else 0.0
        ))
        repricing_method = repricing.get("repricing_method") or "CONTRACT_ANALYSIS"
        rate_source = repricing.get("rate_source") or "CONTRACT"

        # Contract summary
        contract_summary = "No contract on file."
        if contract and contract.rule_library:
            rl = contract.rule_library
            if isinstance(rl, dict):
                summary_parts = []
                if rl.get("payer_name"):
                    summary_parts.append(f"Payer: {rl['payer_name']}")
                if rl.get("contract_type"):
                    summary_parts.append(f"Type: {rl['contract_type']}")
                if rl.get("payment_basis"):
                    summary_parts.append(f"Payment basis: {rl['payment_basis']}")
                if rl.get("reimbursement_rates"):
                    summary_parts.append(f"Reimbursement rates: {json.dumps(rl['reimbursement_rates'])[:500]}")
                elif rl.get("rules"):
                    rules_text = json.dumps(rl["rules"])[:500]
                    summary_parts.append(f"Key rules: {rules_text}")
                contract_summary = "; ".join(summary_parts) if summary_parts else json.dumps(rl)[:800]
            elif isinstance(rl, str):
                contract_summary = rl[:800]
        elif contract and contract.notes:
            contract_summary = contract.notes[:500]

        # Findings summary
        findings_list = []
        for f in findings:
            finding_str = f"{f.finding_code} ({f.severity})"
            if f.variance_amount:
                finding_str += f" — variance ${float(f.variance_amount):,.2f}"
            if f.metadata_json:
                desc = f.metadata_json.get("description") or f.metadata_json.get("message") or ""
                if desc:
                    finding_str += f": {desc}"
            findings_list.append(finding_str)
        findings_summary = "\n".join(findings_list) if findings_list else "Underpayment identified via fee schedule comparison."

        # Build user prompt
        user_prompt = f"""Draft an appeal letter for the following underpaid claim:

HOSPITAL: {hospital_name}
PAYER: {payer_key} ({payer_name or 'Unknown'})
CLAIM ID: {claim_id}
PATIENT ACCOUNT: {patient_account}
DATE OF SERVICE: {dos}
CLAIM TYPE: {claim_type}

CONTRACT BASIS:
{contract_summary}

REPRICING ANALYSIS:
Expected payment: ${expected_payment:,.2f}
Actual payment received: ${actual_paid:,.2f}
Underpayment amount: ${variance:,.2f} ({variance_pct:.1f}%)
Pricing method used: {repricing_method}
Rate source: {rate_source}

FINDINGS:
{findings_summary}
"""
        if additional_context:
            user_prompt += f"\nADDITIONAL CONTEXT: {additional_context}\n"

        user_prompt += f"\nWrite a formal appeal letter requesting payment of the ${variance:,.2f} underpayment."

        # Call OpenAI
        letter, usage = await chat_with_openai_async_tracked(
            text=user_prompt,
            prompt=SYSTEM_PROMPT,
            model="gpt-4.1",
        )
        asyncio.ensure_future(log_ai_cost(
            service="appeal_letter",
            provider="openai",
            model="gpt-4.1",
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            latency_ms=usage.get("latency_ms"),
            document_id=document_id,
            success=bool(letter),
        ))

        if not letter:
            return {"success": False, "error": "AI returned empty response"}

        summary = (
            f"Appeal letter drafted for claim {claim_id} against {payer_key}. "
            f"Requesting recovery of ${variance:,.2f} underpayment ({variance_pct:.1f}% variance)."
        )

        return {
            "success": True,
            "letter": letter,
            "appeal_status": "drafted",
            "summary": summary,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

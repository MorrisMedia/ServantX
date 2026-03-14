"""
Unified per-claim adjudication orchestrator.

This service replaces the old "send everything to GPT and compare one number"
approach.  When a billing record (receipt) is uploaded, this module:

  1. Detects file format (835, CSV, other)
  2. Splits multi-claim files into individual claim loops
  3. Parses each claim's structured fields
  4. Detects claim type (Professional / Institutional IP / Institutional OP)
  5. Routes to the appropriate repricing engine
  6. Creates a Document (role=CLAIM) per claim with per-line variance data
  7. Aggregates results back to the Receipt level

Both the single-receipt upload path and the batch audit pipeline share the
same core parsing + repricing functions.
"""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from services.billing_record_text_extraction_service import extract_billing_record_text
from services.edi_835_parser import parse_claim_835
from services.ipps_repricing_service import reprice_ipps_claim
from services.opps_repricing_service import reprice_opps_claim


# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════

CLAIM_SCHEMA_VERSION = "claim_adjudication_v1"


# ═══════════════════════════════════════════════════════════════════════════
# File Format Detection
# ═══════════════════════════════════════════════════════════════════════════

def detect_file_format(raw_text: str, file_name: str = "") -> str:
    """
    Classify the billing record file type.

    Returns one of: '835', '837I', '837P', 'CSV', 'JSON', 'UNKNOWN'.
    """
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

    # EDI detection — look at the first ~2000 chars
    head = raw_text[:2000].replace("\r", "").replace("\n", "")

    if "ISA*" in head or "GS*" in head or "ST*835*" in head or "CLP*" in head:
        if "ST*835" in head or "CLP*" in raw_text[:5000]:
            return "835"
        if "ST*837" in head:
            # Differentiate 837I from 837P via the implementation guide id
            if "005010X223" in head or "HC:1" in head:
                return "837I"
            return "837P"
        return "835"  # default EDI to 835

    if ext in ("edi", "dat", "hl7", "hlz"):
        # Only classify as 835 if it actually has CLP segments
        if "CLP*" in raw_text[:10000]:
            return "835"
        # HL7 messages have MSH segments
        if "MSH|" in raw_text[:2000]:
            return "UNKNOWN"
        # .dat files could be fixed-width — not structured enough for claim splitting
        return "UNKNOWN"

    if ext == "csv" or (ext == "" and "," in raw_text[:500] and "\n" in raw_text[:500]):
        return "CSV"

    if ext == "json":
        return "JSON"

    # Try sniffing CSV-like content
    lines = raw_text.strip().split("\n")
    if len(lines) > 1 and "," in lines[0] and len(lines[0].split(",")) >= 3:
        return "CSV"

    return "UNKNOWN"


# ═══════════════════════════════════════════════════════════════════════════
# Payer Detection
# ═══════════════════════════════════════════════════════════════════════════

def _split_segments(raw_text: str) -> List[str]:
    """Basic X12 segment splitting."""
    flattened = raw_text.replace("\r", "").replace("\n", "")
    return [segment.strip() for segment in flattened.split("~") if segment.strip()]


def extract_payer_metadata(raw_text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract payer name and payer ID from 835 N1*PR segment."""
    payer_name = None
    payer_id = None
    for segment in _split_segments(raw_text):
        if segment.startswith("N1*PR*"):
            parts = segment.split("*")
            if len(parts) > 2:
                payer_name = parts[2].strip() or None
            if len(parts) > 4:
                payer_id = parts[4].strip() or None
            break
    return payer_name, payer_id


def normalize_payer_key(payer_name: Optional[str], payer_id: Optional[str]) -> str:
    """Normalize payer identifiers to a canonical key."""
    name = (payer_name or "").upper()
    pid = (payer_id or "").upper()

    if "MEDICARE" in name or pid.startswith("MEDICARE"):
        if "PART A" in name or "MA" in pid:
            return "MEDICARE_PART_A"
        if "PART B" in name or "MB" in pid:
            return "MEDICARE"
        return "MEDICARE"
    if "TEXAS MEDICAID" in name or "TX MEDICAID" in name or pid.startswith("TXMCD"):
        return "TX_MEDICAID_FFS"
    return "OTHER"


# ═══════════════════════════════════════════════════════════════════════════
# 835 Claim Splitting
# ═══════════════════════════════════════════════════════════════════════════

def split_835_claim_loops(raw_text: str) -> List[str]:
    """
    Split an 835 file into individual claim-level EDI strings (one per CLP loop).
    Reusable by both single-receipt and batch audit paths.
    """
    segments = _split_segments(raw_text)
    claims: List[List[str]] = []
    current_claim: List[str] = []

    for segment in segments:
        if segment.startswith("CLP*"):
            if current_claim:
                claims.append(current_claim)
                current_claim = []
        if segment.startswith("CLP*") or current_claim:
            current_claim.append(segment)

    if current_claim:
        claims.append(current_claim)

    return ["~".join(segs) + "~" for segs in claims]


# ═══════════════════════════════════════════════════════════════════════════
# CSV Claim Parsing
# ═══════════════════════════════════════════════════════════════════════════

def _detect_csv_delimiter(raw_text: str) -> str:
    """Auto-detect CSV delimiter from first line."""
    first_line = raw_text.split("\n", 1)[0]
    # Count candidate delimiters
    for delim in ["|", "\t", ","]:
        if first_line.count(delim) >= 2:
            return delim
    return ","


def parse_csv_claims(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parse a CSV/pipe/tab-delimited billing record where each row is a claim
    or service line.

    Supports:
      - Comma-separated (standard CSV)
      - Pipe-delimited (MAC remittance format)
      - Tab-delimited

    Column name matching is case-insensitive and flexible (underscores, spaces,
    abbreviations all work).

    Returns a list of structured claim dicts.
    """
    delimiter = _detect_csv_delimiter(raw_text)
    reader = csv.DictReader(io.StringIO(raw_text), delimiter=delimiter)
    if not reader.fieldnames:
        return []

    # Normalize headers to lowercase with underscores
    normalized_fields = {h: h.strip().lower().replace(" ", "_").replace("-", "_") for h in reader.fieldnames}

    claims: List[Dict[str, Any]] = []
    for row_idx, row in enumerate(reader, start=1):
        normalized_row = {normalized_fields.get(k, k): (v.strip() if v else "") for k, v in row.items()}

        def _get(keys: List[str], default: str = "") -> str:
            for k in keys:
                val = normalized_row.get(k, "")
                if val:
                    return val
            return default

        def _getf(keys: List[str], default: float = 0.0) -> float:
            val = _get(keys)
            try:
                return float(val.replace(",", "").replace("$", ""))
            except (ValueError, AttributeError):
                return default

        claim = {
            "row_number": row_idx,
            "claim_id": _get(["claim_id", "claim_number", "clm_id", "claim_control_number"]),
            "patient_control_number": _get(["patient_control_number", "patient_acct", "pcn",
                                             "pat_mrn", "pat_mbi"]),
            "payer_claim_control_number": _get(["payer_claim_control_number", "pccn", "icn"]),
            "drg_code": _get(["drg_code", "drg", "ms_drg", "msdrg", "ms_drg_code"]),
            "drg_weight": _getf(["drg_wt", "drg_weight", "drg_wght", "relative_weight"]),
            "cpt_hcpcs": _get(["cpt_hcpcs", "cpt", "hcpcs", "procedure_code", "cpt_code",
                                "hcpcs_code", "hcpcs_cd"]),
            "revenue_code": _get(["revenue_code", "rev_code", "rev_cd"]),
            "type_of_bill": _get(["type_of_bill", "tob", "bill_type", "tob_code"]),
            "total_charges": _getf(["total_charges", "charges", "billed_amount", "billed",
                                     "charge_amount", "tot_chg", "cov_chg", "chg_amt"]),
            "claim_payment_amount": _getf(["claim_payment_amount", "payment", "paid",
                                            "paid_amount", "payment_amount", "tot_paid",
                                            "total_paid", "net_paid", "gross_pay",
                                            "total_payment"]),
            "units": _getf(["units", "qty", "quantity"], default=1.0),
            "modifiers": _get(["modifiers", "modifier"]),
            "payer_name": _get(["payer", "payer_name", "insurance", "payer_id"]),
            "service_date": _get(["service_date", "dos", "date_of_service",
                                   "service_date_start", "serv_dt", "adm_dt"]),
            "discharge_date": _get(["discharge_date", "dsch_dt", "discharge_dt"]),
            "discharge_status": _get(["discharge_status", "patient_status",
                                       "discharge_code", "dsch_stat"]),
            "place_of_service": _get(["place_of_service", "pos"]),
            "provider_npi": _get(["prov_npi", "provider_npi", "npi", "billing_npi",
                                   "attend_npi"]),
            # MAC remittance IPPS component fields
            "op_base_pay": _getf(["op_base_pay", "operating_payment", "base_payment"]),
            "dsh_amount": _getf(["dsh_amt", "dsh_amount", "dsh_pay"]),
            "ime_amount": _getf(["ime_amt", "ime_amount", "ime_pay"]),
            "capital_pay": _getf(["cap_pay", "capital_pay", "capital_payment",
                                   "capital_amount"]),
            "outlier_amount": _getf(["outlier_amt", "outlier_amount", "outlier_pay"]),
            "sequester_amount": _getf(["sequester_amt", "sequester_amount"]),
            "sequester_pct": _getf(["sequester_pct", "sequestration_pct"]),
            "deductible": _getf(["deduct", "deductible", "deductible_amt"]),
            "pay_status": _get(["pay_status", "payment_status", "status"]),
        }
        claims.append(claim)

    return claims


# ═══════════════════════════════════════════════════════════════════════════
# Claim Type Detection
# ═══════════════════════════════════════════════════════════════════════════

def detect_claim_type(claim: Dict[str, Any]) -> str:
    """
    Classify a single parsed claim as:
        PROFESSIONAL        – CMS-1500 / Part B
        INSTITUTIONAL_IP    – UB-04 / Part A inpatient
        INSTITUTIONAL_OP    – UB-04 / Part A outpatient

    Detection signals (in priority order):
        1. DRG present → inpatient
        2. Type of Bill (TOB):
           - 11x, 12x → inpatient
           - 13x, 14x, 71x, 73x, 83x, 85x → outpatient
        3. Revenue codes present → institutional (then use TOB/DRG to decide IP vs OP)
        4. claim_type field from parser (835 CLP)
        5. CPT/HCPCS codes in E/M range → professional
        6. Payer key: MEDICARE_PART_A → likely institutional
        7. Default → PROFESSIONAL
    """
    drg_code = (claim.get("drg_code") or "").strip()
    tob = (claim.get("type_of_bill") or "").strip()
    revenue_code = (claim.get("revenue_code") or "").strip()
    cpt = (claim.get("cpt_hcpcs") or "").strip()
    claim_type_field = (claim.get("claim_type") or "").upper()
    payer_key = (claim.get("payer_key") or claim.get("payer_name") or "").upper()
    claim_status_code = (claim.get("claim_status_code") or "").strip()

    # 1. DRG present → inpatient
    if drg_code:
        return "INSTITUTIONAL_IP"

    # 2. Type of Bill codes
    # TOB can be 3 digits (classification + frequency) or 4 digits
    # (leading 0 + classification + frequency).  The classification is
    # always the 2nd and 3rd characters of the 4-digit form, or 1st and
    # 2nd of the 3-digit form.
    if tob:
        if len(tob) == 4:
            tob_class = tob[1:3]  # e.g. "0111" -> "11"
        elif len(tob) == 3:
            tob_class = tob[:2]   # e.g. "111" -> "11"
        else:
            tob_class = tob[:2]
        inpatient_classes = {"11", "12", "18", "21", "28", "41"}
        outpatient_classes = {"13", "14", "71", "73", "83", "85"}
        if tob_class in inpatient_classes:
            return "INSTITUTIONAL_IP"
        if tob_class in outpatient_classes:
            return "INSTITUTIONAL_OP"

    # 3. Revenue codes → institutional
    if revenue_code:
        # Revenue codes suggest institutional; use DRG absence to guess OP
        return "INSTITUTIONAL_OP"

    # 4. claim_type from 835 parser
    if "INSTITUTIONAL" in claim_type_field or "INPATIENT" in claim_type_field:
        return "INSTITUTIONAL_IP"
    if "OUTPATIENT" in claim_type_field:
        return "INSTITUTIONAL_OP"

    # 5. 835 CLP claim status code: 1=inpatient, 2=outpatient, etc.
    if claim_status_code == "1":
        return "INSTITUTIONAL_IP"
    if claim_status_code in ("2", "3", "4"):
        return "INSTITUTIONAL_OP" if claim_status_code == "2" else "PROFESSIONAL"

    # 6. Payer key hint
    if "PART_A" in payer_key or "PART A" in payer_key:
        return "INSTITUTIONAL_IP"

    # 7. CPT / HCPCS analysis — if present, likely professional
    if cpt:
        return "PROFESSIONAL"

    return "PROFESSIONAL"


# ═══════════════════════════════════════════════════════════════════════════
# Contract Matching
# ═══════════════════════════════════════════════════════════════════════════

def match_contract_for_claim(
    claim: Dict[str, Any],
    contracts: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Select the best contract to use for repricing a claim.

    Matching logic:
      1. If payer_key contains 'MEDICARE' → prefer contract with 'medicare' in name/type
      2. If payer_key contains 'MEDICAID' → prefer contract with 'medicaid' in name/type
      3. First contract with a non-empty rule_library
      4. First contract with text (fallback for the AI analysis path)
    """
    payer_key = (claim.get("payer_key") or "").upper()

    # Score each contract
    scored: List[Tuple[int, Dict[str, Any]]] = []
    for contract in contracts:
        score = 0
        name = (contract.get("name") or "").upper()
        rl = contract.get("rule_library") or {}
        ct = (rl.get("contract_type") or "").upper() if isinstance(rl, dict) else ""

        # Payer alignment
        if "MEDICARE" in payer_key:
            if "MEDICARE" in name or "MEDICARE" in ct:
                score += 10
        elif "MEDICAID" in payer_key:
            if "MEDICAID" in name or "MEDICAID" in ct:
                score += 10

        # Has rule library
        if rl and isinstance(rl, dict) and rl.get("rule_count", 0) > 0:
            score += 5

        # Has text
        if contract.get("text", "").strip():
            score += 1

        scored.append((score, contract))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else None


# ═══════════════════════════════════════════════════════════════════════════
# Per-Claim Repricing Router
# ═══════════════════════════════════════════════════════════════════════════

async def reprice_single_claim(
    parsed_claim: Dict[str, Any],
    claim_type: str,
    rule_library: Optional[Dict[str, Any]],
    service_lines: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Route a single parsed claim to the correct repricing engine.

    Returns a standardized result dict with:
        claim_type, repricing_method, expected_payment, actual_paid,
        variance_amount, variance_percent, errors, confidence_score,
        rate_source, per_line_results (if applicable), components
    """

    if claim_type == "INSTITUTIONAL_IP":
        return reprice_ipps_claim(claim=parsed_claim, rule_library=rule_library)

    if claim_type == "INSTITUTIONAL_OP":
        return reprice_opps_claim(claim=parsed_claim, rule_library=rule_library)

    # PROFESSIONAL — use existing per-line repricing from repricing_service
    # We import lazily to avoid circular imports and because we need an async
    # db session for the DB-backed MPFS/Medicaid lookups.
    from core_services.db_service import AsyncSessionLocal
    from services.repricing_service import (
        build_line_findings,
        reprice_medicare_line,
        reprice_tx_medicaid_line,
    )

    payer_key = (parsed_claim.get("payer_key") or "").upper()
    lines = service_lines or parsed_claim.get("service_lines") or []
    provider = parsed_claim.get("provider") or {}

    if not lines:
        as_paid = float(parsed_claim.get("claim_payment_amount") or 0.0)
        return {
            "errors": ["NO_SERVICE_LINES"],
            "claim_type": "PROFESSIONAL",
            "repricing_method": "MPFS" if "MEDICARE" in payer_key else "FEE_SCHEDULE",
            "expected_payment": None,
            "actual_paid": round(as_paid, 2),
            "variance_amount": None,
            "variance_percent": None,
            "confidence_score": 10.0,
            "rate_source": "NONE",
            "per_line_results": [],
            "components": None,
        }

    total_expected = 0.0
    total_paid = 0.0
    total_variance = 0.0
    all_errors: List[str] = []
    line_results: List[Dict[str, Any]] = []

    async with AsyncSessionLocal() as db:
        for line in lines:
            context = {
                "provider": provider,
                "service_date_start": parsed_claim.get("service_date_start")
                    or parsed_claim.get("service_date"),
            }

            if "MEDICARE" in payer_key:
                result = await reprice_medicare_line(db=db, line=line, context=context)
            elif "MEDICAID" in payer_key:
                result = await reprice_tx_medicaid_line(db=db, line=line, context=context)
            else:
                # Contract-based repricing via rule library
                result = _reprice_line_from_rule_library(line, rule_library)

            expected = result.get("expected_allowed")
            actual = float(result.get("actual_paid") or float(line.get("line_payment_amount") or 0.0))
            var = (
                float(result.get("variance_amount"))
                if result.get("variance_amount") is not None
                else ((float(expected) - actual) if expected is not None else 0.0)
            )

            if expected is not None:
                total_expected += float(expected)
            total_paid += actual
            if var > 0:
                total_variance += var
            all_errors.extend(result.get("errors", []))

            line_results.append({
                "line_number": line.get("line_number"),
                "cpt_hcpcs": line.get("cpt_hcpcs"),
                "modifiers": line.get("modifiers", []),
                "units": line.get("units"),
                "expected_allowed": round(float(expected), 2) if expected is not None else None,
                "actual_paid": round(actual, 2),
                "variance_amount": round(var, 2),
                "rate_source": result.get("rate_source"),
                "confidence_score": result.get("confidence_score"),
                "errors": result.get("errors", []),
            })

    overall_variance_pct = (total_variance / total_expected * 100) if total_expected > 0 else 0.0
    # Deduplicate errors
    unique_errors = list(dict.fromkeys(all_errors))

    avg_confidence = (
        sum(lr.get("confidence_score") or 0 for lr in line_results) / len(line_results)
        if line_results else 0.0
    )

    return {
        "errors": unique_errors,
        "claim_type": "PROFESSIONAL",
        "repricing_method": "MPFS" if "MEDICARE" in payer_key else "FEE_SCHEDULE",
        "expected_payment": round(total_expected, 2) if total_expected > 0 else None,
        "actual_paid": round(total_paid, 2),
        "variance_amount": round(total_variance, 2),
        "variance_percent": round(overall_variance_pct, 2),
        "confidence_score": round(avg_confidence, 2),
        "rate_source": line_results[0].get("rate_source") if line_results else "NONE",
        "per_line_results": line_results,
        "components": None,
    }


def _reprice_line_from_rule_library(
    line: Dict[str, Any],
    rule_library: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Attempt to reprice a professional service line using the contract rule library
    when no Medicare/Medicaid DB rates are available (i.e. commercial payer).
    """
    cpt = (line.get("cpt_hcpcs") or "").strip()
    actual_paid = float(line.get("line_payment_amount") or 0.0)
    units = float(line.get("units") or 1.0) or 1.0

    if not rule_library or not cpt:
        return {
            "errors": ["MISSING_RATE_MATCH"],
            "expected_allowed": None,
            "actual_paid": round(actual_paid, 2),
            "variance_amount": None,
            "variance_percent": None,
            "rate_source": "NO_RULE_LIBRARY",
            "confidence_score": 10.0,
        }

    # Search fee schedule
    fee_schedule = rule_library.get("fee_schedule") or []
    for entry in fee_schedule:
        if (entry.get("code") or "").strip() == cpt:
            rate = entry.get("rate")
            if rate is not None:
                try:
                    expected = float(rate) * units
                    variance = expected - actual_paid
                    variance_pct = (variance / expected * 100) if expected > 0 else 0.0
                    return {
                        "errors": [],
                        "expected_allowed": round(expected, 2),
                        "actual_paid": round(actual_paid, 2),
                        "variance_amount": round(variance, 2),
                        "variance_percent": round(variance_pct, 2),
                        "rate_source": "CONTRACT_FEE_SCHEDULE",
                        "confidence_score": 75.0,
                    }
                except (TypeError, ValueError):
                    pass

    # Search percentage rules for applicable benchmark
    pct_rules = rule_library.get("percentage_rules") or []
    for rule in pct_rules:
        benchmark = (rule.get("benchmark") or "").lower()
        if benchmark == "billed_charges":
            billed = float(line.get("line_charge_amount") or 0.0)
            if billed > 0:
                pct = float(rule.get("percent", 100)) / 100.0
                expected = billed * pct
                variance = expected - actual_paid
                variance_pct = (variance / expected * 100) if expected > 0 else 0.0
                return {
                    "errors": [],
                    "expected_allowed": round(expected, 2),
                    "actual_paid": round(actual_paid, 2),
                    "variance_amount": round(variance, 2),
                    "variance_percent": round(variance_pct, 2),
                    "rate_source": f"CONTRACT_PCT_CHARGES_{rule.get('percent')}",
                    "confidence_score": 60.0,
                }

    return {
        "errors": ["MISSING_RATE_MATCH"],
        "expected_allowed": None,
        "actual_paid": round(actual_paid, 2),
        "variance_amount": None,
        "variance_percent": None,
        "rate_source": "RULE_LIBRARY_NO_MATCH",
        "confidence_score": 15.0,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Full Adjudication Pipeline (single receipt)
# ═══════════════════════════════════════════════════════════════════════════

async def adjudicate_receipt(
    receipt_data: Dict[str, Any],
    hospital_id: str,
    contracts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Run the full per-claim adjudication pipeline on a single receipt.

    Parameters
    ----------
    receipt_data : dict
        Receipt record including fileUrl, fileName, id.
    hospital_id : str
        Hospital owning this receipt.
    contracts : list of dict
        Contracts with keys: id, name, text, rule_library.

    Returns
    -------
    dict with:
        receipt_id, claims_processed, total_expected, total_paid,
        total_variance, has_underpayment, claim_results, documents_created
    """
    from services.document_service import create_document

    receipt_id = receipt_data["id"]
    file_url = receipt_data.get("fileUrl", "")
    file_name = receipt_data.get("fileName", "")

    # ── Step 1: Extract text ──
    raw_text = extract_billing_record_text(file_url, file_name)
    if raw_text.startswith(("Error", "Warning:", "File not found")):
        return _error_result(receipt_id, f"Text extraction failed: {raw_text[:200]}")

    # ── Step 2: Detect format ──
    file_format = detect_file_format(raw_text, file_name)

    # ── Step 3: Split into claims ──
    parsed_claims: List[Dict[str, Any]] = []

    if file_format == "835":
        payer_name, payer_id = extract_payer_metadata(raw_text)
        payer_key = normalize_payer_key(payer_name, payer_id)

        claim_loops = split_835_claim_loops(raw_text)
        for idx, loop_edi in enumerate(claim_loops, start=1):
            parsed = parse_claim_835(
                raw_claim_edi=loop_edi,
                batch_id="",
                document_id="",
                parent_file_document_id=None,
                payer={"payer_key": payer_key, "payer_name": payer_name, "payer_id": payer_id},
            )
            claim_data = parsed.get("claim", {})
            claim_data["payer_key"] = payer_key
            claim_data["provider"] = parsed.get("provider", {})
            claim_data["service_lines"] = parsed.get("service_lines", [])
            claim_data["raw_edi_evidence"] = parsed.get("raw_edi_evidence", {})
            claim_data["claim_index"] = idx
            parsed_claims.append(claim_data)

    elif file_format == "CSV":
        csv_claims = parse_csv_claims(raw_text)
        for claim in csv_claims:
            # Derive payer key from CSV payer column
            payer_name = claim.get("payer_name")
            payer_key = normalize_payer_key(payer_name, None)
            claim["payer_key"] = payer_key
            claim["claim_index"] = claim.get("row_number", 0)
            parsed_claims.append(claim)

    elif file_format == "JSON":
        # Try to parse JSON claims (e.g. FHIR bundles)
        try:
            data = json.loads(raw_text)
            # FHIR Bundle with Claim resources
            if isinstance(data, dict) and data.get("resourceType") == "Bundle":
                entries = data.get("entry", [])
                for idx, entry in enumerate(entries, start=1):
                    resource = entry.get("resource", {})
                    if resource.get("resourceType") in ("Claim", "ExplanationOfBenefit"):
                        total_val = resource.get("total", {}).get("value", 0.0)
                        parsed_claims.append({
                            "payer_key": "OTHER",
                            "total_charges": float(total_val),
                            "claim_payment_amount": float(resource.get("payment", {}).get("amount", {}).get("value", 0.0)),
                            "claim_index": idx,
                            "claim_id": resource.get("id", f"fhir-{idx}"),
                        })
            # Array of claim objects
            elif isinstance(data, list):
                for idx, item in enumerate(data, start=1):
                    if isinstance(item, dict):
                        parsed_claims.append({
                            "payer_key": normalize_payer_key(item.get("payer"), None),
                            "total_charges": float(item.get("total_charges") or item.get("charges") or 0.0),
                            "claim_payment_amount": float(item.get("payment") or item.get("paid") or 0.0),
                            "claim_index": idx,
                            "claim_id": item.get("claim_id", f"json-{idx}"),
                            "drg_code": item.get("drg_code") or item.get("drg"),
                            "cpt_hcpcs": item.get("cpt") or item.get("cpt_hcpcs"),
                        })
        except (json.JSONDecodeError, TypeError):
            pass  # Fall through to the UNKNOWN handler below

    if not parsed_claims and file_format not in ("835", "CSV"):
        # Unsupported or unknown format — fall back to single-claim treatment
        # Treat the entire file as a single claim so a document is still created
        parsed_claims.append({
            "payer_key": "OTHER",
            "total_charges": 0.0,
            "claim_payment_amount": 0.0,
            "claim_index": 1,
            "raw_text": raw_text[:5000],  # Truncated for notes
        })

    if not parsed_claims:
        # No structured claims found — fall back to a single summary document.
        # This happens with HL7, fixed-width, or other non-standard formats.
        from services.document_service import create_document as _create_doc
        doc = await _create_doc(
            receipt_id=receipt_id,
            hospital_id=hospital_id,
            contract_id=contracts[0]["id"] if contracts else None,
            amount=0.0,
            status="not_submitted",
            name=f"Unparseable format ({file_format}): {file_name}",
            notes=f"File format '{file_format}' could not be split into individual claims. Manual review recommended.",
            rules_applied=f"type:UNKNOWN,method:NONE,format:{file_format}",
            receipt_amount=0.0,
            contract_amount=0.0,
            underpayment_amount=0.0,
        )
        return {
            "receipt_id": receipt_id,
            "file_format": file_format,
            "claims_processed": 0,
            "total_expected": 0.0,
            "total_paid": 0.0,
            "total_variance": 0.0,
            "has_underpayment": False,
            "claim_results": [],
            "documents_created": [doc],
        }

    # ── Step 4-5: Detect type, route to repricing, create documents ──
    claim_results: List[Dict[str, Any]] = []
    documents_created: List[Dict[str, Any]] = []
    total_expected = 0.0
    total_paid = 0.0
    total_variance = 0.0
    has_underpayment = False

    for claim in parsed_claims:
        claim_type = detect_claim_type(claim)
        contract = match_contract_for_claim(claim, contracts)
        rule_library = (contract.get("rule_library") if contract else None) or {}
        contract_id = contract.get("id") if contract else None

        repricing_result = await reprice_single_claim(
            parsed_claim=claim,
            claim_type=claim_type,
            rule_library=rule_library if isinstance(rule_library, dict) else {},
            service_lines=claim.get("service_lines"),
        )

        expected = repricing_result.get("expected_payment")
        paid = float(repricing_result.get("actual_paid") or 0.0)
        variance = float(repricing_result.get("variance_amount") or 0.0)

        if expected is not None:
            total_expected += float(expected)
        total_paid += paid
        if variance > 0:
            total_variance += variance
            has_underpayment = True

        claim_result = {
            "claim_index": claim.get("claim_index"),
            "claim_type": claim_type,
            **repricing_result,
        }
        claim_results.append(claim_result)

        # Create Document for this claim
        status = "not_submitted"
        claim_label = (
            claim.get("patient_control_number")
            or claim.get("claim_id")
            or f"Claim #{claim.get('claim_index', '?')}"
        )
        doc_name = f"{claim_type}: {claim_label} from {file_name}"

        notes_payload = {
            "claim_type": claim_type,
            "repricing_method": repricing_result.get("repricing_method"),
            "file_format": file_format,
            "errors": repricing_result.get("errors", []),
            "confidence_score": repricing_result.get("confidence_score"),
            "rate_source": repricing_result.get("rate_source"),
        }
        if repricing_result.get("components"):
            notes_payload["components"] = repricing_result["components"]
        if repricing_result.get("per_line_results"):
            notes_payload["per_line_count"] = len(repricing_result["per_line_results"])

        rules_applied_parts = [
            f"type:{claim_type}",
            f"method:{repricing_result.get('repricing_method', 'UNKNOWN')}",
        ]
        if repricing_result.get("drg_code"):
            rules_applied_parts.append(f"drg:{repricing_result['drg_code']}")
        if repricing_result.get("rate_source"):
            rules_applied_parts.append(f"rate:{repricing_result['rate_source']}")

        doc_data = await create_document(
            receipt_id=receipt_id,
            hospital_id=hospital_id,
            contract_id=contract_id,
            amount=max(0.0, variance),
            status=status,
            name=doc_name,
            notes=json.dumps(notes_payload, separators=(",", ":")),
            rules_applied=",".join(rules_applied_parts),
            receipt_amount=paid,
            contract_amount=float(expected) if expected is not None else 0.0,
            underpayment_amount=max(0.0, variance),
        )
        documents_created.append(doc_data)

    # If no documents were created (shouldn't happen), create a summary one
    if not documents_created:
        doc_data = await create_document(
            receipt_id=receipt_id,
            hospital_id=hospital_id,
            contract_id=contracts[0]["id"] if contracts else None,
            amount=0.0,
            status="not_submitted",
            name=f"No Claims: {file_name}",
            notes="No claims could be parsed or repriced from this billing record.",
            rules_applied=None,
            receipt_amount=0.0,
            contract_amount=0.0,
            underpayment_amount=0.0,
        )
        documents_created.append(doc_data)

    return {
        "receipt_id": receipt_id,
        "file_format": file_format,
        "claims_processed": len(claim_results),
        "total_expected": round(total_expected, 2),
        "total_paid": round(total_paid, 2),
        "total_variance": round(total_variance, 2),
        "has_underpayment": has_underpayment,
        "claim_results": claim_results,
        "documents_created": documents_created,
    }


def _error_result(receipt_id: str, message: str) -> Dict[str, Any]:
    return {
        "receipt_id": receipt_id,
        "file_format": "UNKNOWN",
        "claims_processed": 0,
        "total_expected": 0.0,
        "total_paid": 0.0,
        "total_variance": 0.0,
        "has_underpayment": False,
        "claim_results": [],
        "documents_created": [],
        "error": message,
    }

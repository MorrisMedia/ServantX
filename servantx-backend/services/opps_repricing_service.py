"""
OPPS (Outpatient Prospective Payment System) repricing service – stub.

This is a placeholder that returns a structured result indicating the claim
is an outpatient institutional claim.  A full OPPS/APC-based calculator can
be added here in a future phase.

For now it extracts any available outpatient rates from the contract rule
library and produces a percent-of-charges or percent-of-Medicare estimate
when the contract specifies one.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select


def reprice_opps_claim(
    claim: Dict[str, Any],
    rule_library: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Reprice a single outpatient institutional claim.

    For now this is a best-effort calculation using the contract's outpatient
    rate fields:
      - outpatient_percent_of_medicare
      - outpatient_percent_of_charges
      - outpatient_base_rate

    Full APC-level repricing (per HCPCS, status indicators, packaging) is a
    future enhancement.
    """
    lib = rule_library or {}
    total_charges = float(claim.get("total_charges") or claim.get("total_charge_amount") or 0.0)
    as_paid = float(claim.get("claim_payment_amount") or 0.0)

    errors: List[str] = []
    expected: Optional[float] = None
    rate_source = "OPPS_STUB"

    # ── Try percent-of-charges ──
    pct_charges = lib.get("outpatient_percent_of_charges")
    if pct_charges is not None and total_charges > 0:
        try:
            expected = total_charges * (float(pct_charges) / 100.0)
            rate_source = f"OPPS_PCT_CHARGES_{pct_charges}"
        except (TypeError, ValueError):
            pass

    # ── Try percent-of-Medicare (we'd need the Medicare APC allowed, so just
    #    note it for now if we have no expected yet) ──
    if expected is None:
        pct_medicare = lib.get("outpatient_percent_of_medicare")
        if pct_medicare is not None:
            errors.append("OPPS_MEDICARE_APC_LOOKUP_NOT_IMPLEMENTED")
            rate_source = f"OPPS_PCT_MEDICARE_{pct_medicare}_STUB"

    # ── Try flat outpatient base rate ──
    if expected is None:
        base_rate = lib.get("outpatient_base_rate") or lib.get("opps_payment_rate")
        if base_rate is not None:
            try:
                expected = float(base_rate)
                rate_source = "OPPS_FLAT_BASE_RATE"
            except (TypeError, ValueError):
                pass

    # ── Fallback ──
    if expected is None:
        errors.append("OPPS_CALCULATION_NOT_AVAILABLE")
        return {
            "errors": errors,
            "claim_type": "INSTITUTIONAL_OP",
            "repricing_method": "OPPS_STUB",
            "expected_payment": None,
            "actual_paid": round(as_paid, 2),
            "variance_amount": None,
            "variance_percent": None,
            "confidence_score": 10.0,
            "rate_source": rate_source,
            "components": None,
        }

    variance = expected - as_paid
    variance_pct = (variance / expected * 100.0) if expected > 0 else 0.0

    return {
        "errors": errors,
        "claim_type": "INSTITUTIONAL_OP",
        "repricing_method": "OPPS_STUB",
        "expected_payment": round(expected, 2),
        "actual_paid": round(as_paid, 2),
        "variance_amount": round(variance, 2),
        "variance_percent": round(variance_pct, 2),
        "confidence_score": 50.0 if not errors else 30.0,
        "rate_source": rate_source,
        "components": {
            "total_charges": round(total_charges, 2),
            "note": "OPPS stub — full APC-level repricing not yet implemented.",
        },
    }


async def reprice_opps_claim_with_db(
    claim: Dict[str, Any],
    rule_library: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Full APC-based OPPS repricing. Looks up each HCPCS in opps_apc_rates table.
    Falls back to the existing contract-based calculation if DB lookup fails.
    """
    from core_services.db_service import AsyncSessionLocal
    from models import OppsApcRate

    # Extract service lines or fall back to single claim CPT
    service_lines = claim.get("service_lines") or []
    single_cpt = claim.get("cpt_hcpcs", "").strip()
    if not service_lines and single_cpt:
        service_lines = [{"cpt_hcpcs": single_cpt, "line_payment_amount": float(claim.get("claim_payment_amount") or 0), "units": 1}]

    if not service_lines:
        # No line detail — fall back to existing stub logic
        return reprice_opps_claim(claim, rule_library)

    total_expected = 0.0
    total_paid = 0.0
    total_variance = 0.0
    line_results: List[Dict[str, Any]] = []
    errors: List[str] = []

    async with AsyncSessionLocal() as db:
        for line in service_lines:
            cpt = (line.get("cpt_hcpcs") or "").strip()
            actual = float(line.get("line_payment_amount") or 0.0)
            units = max(float(line.get("units") or 1.0), 0.0)

            if not cpt:
                errors.append("MISSING_HCPCS")
                continue

            result = await db.execute(
                select(OppsApcRate).where(
                    OppsApcRate.hcpcs_code == cpt,
                    OppsApcRate.year == 2026,
                ).limit(1)
            )
            apc_row = result.scalar_one_or_none()

            if apc_row:
                expected_line = float(apc_row.payment_rate) * units
                variance_line = expected_line - actual
                total_expected += expected_line
                total_paid += actual
                if variance_line > 0:
                    total_variance += variance_line
                line_results.append({
                    "cpt_hcpcs": cpt,
                    "apc_code": apc_row.apc_code,
                    "expected_allowed": round(expected_line, 2),
                    "actual_paid": round(actual, 2),
                    "variance_amount": round(variance_line, 2),
                    "rate_source": f"CMS_OPPS_2026_APC_{apc_row.apc_code}",
                    "confidence_score": 85.0,
                    "errors": [],
                })
            else:
                errors.append(f"OPPS_APC_NOT_FOUND_{cpt}")
                line_results.append({
                    "cpt_hcpcs": cpt,
                    "expected_allowed": None,
                    "actual_paid": round(actual, 2),
                    "variance_amount": None,
                    "rate_source": "OPPS_APC_NOT_FOUND",
                    "confidence_score": 15.0,
                    "errors": [f"OPPS_APC_NOT_FOUND_{cpt}"],
                })

    if not line_results or not any(r.get("expected_allowed") for r in line_results):
        # No APC matches found — fall back to contract-based stub
        fallback = reprice_opps_claim(claim, rule_library)
        fallback["repricing_method"] = "OPPS_CONTRACT_FALLBACK"
        return fallback

    overall_pct = (total_variance / total_expected * 100) if total_expected > 0 else 0.0
    avg_confidence = sum(r.get("confidence_score", 0) for r in line_results) / len(line_results) if line_results else 0.0

    return {
        "errors": list(set(errors)),
        "claim_type": "INSTITUTIONAL_OP",
        "repricing_method": "OPPS_APC_2026",
        "expected_payment": round(total_expected, 2),
        "actual_paid": round(total_paid, 2),
        "variance_amount": round(total_variance, 2),
        "variance_percent": round(overall_pct, 2),
        "confidence_score": round(avg_confidence, 2),
        "rate_source": "CMS_OPPS_2026",
        "per_line_results": line_results,
        "components": None,
    }

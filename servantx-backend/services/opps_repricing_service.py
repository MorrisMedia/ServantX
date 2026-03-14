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

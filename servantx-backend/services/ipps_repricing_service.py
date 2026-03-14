"""
IPPS (Inpatient Prospective Payment System) repricing service.

Calculates expected Medicare Part A inpatient payment for a single claim using:

    Operating Payment = base_rate x DRG_weight x (1 + DSH% + IME%)
    Capital Payment   = capital_rate x GAF x DRG_weight x (1 + cap_adj%)
    Outlier Payment   = max(0, (charges x CCR - threshold)) x marginal_cost_factor
    Total Expected    = (Operating + Capital + Outlier) x (1 - sequester%)

All parameters come from the contract rule library so the engine works for any
hospital whose contract embeds its rates (which Texas contracts typically do).

DRG weights are resolved in order:
  1. Contract rule_library fee_schedule entries with code_type MS_DRG
  2. (Future) A database MedicareDrgWeight table
  3. Fallback weight of 1.0 with a quality warning
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# DRG Weight Lookup
# ---------------------------------------------------------------------------

def _build_drg_weight_map(rule_library: Optional[Dict[str, Any]]) -> Dict[str, float]:
    """
    Build a DRG code -> relative weight mapping from the rule library's
    fee_schedule entries that have code_type containing 'DRG'.
    """
    weights: Dict[str, float] = {}
    if not rule_library:
        return weights

    fee_schedule = rule_library.get("fee_schedule") or []
    for entry in fee_schedule:
        code_type = (entry.get("code_type") or "").upper()
        if "DRG" in code_type:
            code = (entry.get("code") or "").strip()
            rate = entry.get("rate")
            # If the entry carries a 'drg_weight' key (custom), use that.
            # Otherwise treat the 'percent_of_medicare' as a weight if it
            # looks like a relative weight (0-99) or use 'rate' as the weight
            # when the contract stores weights directly.
            weight = entry.get("drg_weight")
            if weight is None:
                pom = entry.get("percent_of_medicare")
                if pom is not None and 0 < pom < 100:
                    weight = pom  # some contracts store weight here
                elif rate is not None and 0 < rate < 100:
                    weight = rate
            if code and weight is not None:
                try:
                    weights[code] = float(weight)
                except (TypeError, ValueError):
                    pass
    return weights


def lookup_drg_weight(
    drg_code: Optional[str],
    rule_library: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Return {'weight': float, 'source': str, 'errors': list}.
    Looks in rule_library fee_schedule first, then (future) DB table.
    """
    if not drg_code:
        return {"weight": 1.0, "source": "FALLBACK_NO_DRG", "errors": ["MISSING_DRG_CODE"]}

    clean_drg = drg_code.strip().lstrip("0")

    drg_map = _build_drg_weight_map(rule_library)
    if drg_map:
        # Try exact match, then stripped leading zeros
        for candidate in [drg_code.strip(), clean_drg]:
            if candidate in drg_map:
                return {"weight": drg_map[candidate], "source": "CONTRACT_RULE_LIBRARY", "errors": []}
        # Try 3-digit zero-padded version
        try:
            padded = str(int(clean_drg)).zfill(3)
            if padded in drg_map:
                return {"weight": drg_map[padded], "source": "CONTRACT_RULE_LIBRARY", "errors": []}
        except ValueError:
            pass

    # Fallback — no DRG weight found
    return {"weight": 1.0, "source": "FALLBACK_WEIGHT", "errors": ["DRG_WEIGHT_NOT_FOUND"]}


# ---------------------------------------------------------------------------
# IPPS Parameters from rule library
# ---------------------------------------------------------------------------

def _get_ipps_params(rule_library: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract IPPS calculation parameters from the contract rule library.
    Falls back to reasonable defaults (CMS-published national values) where
    the contract is silent so we can still produce a ballpark estimate.
    """
    lib = rule_library or {}

    def _f(key: str, default: float) -> float:
        val = lib.get(key)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                pass
        return default

    return {
        "operating_base_rate": _f("ipps_operating_base_rate", 0.0) or _f("inpatient_base_rate", 0.0),
        "capital_federal_rate": _f("ipps_capital_federal_rate", 0.0),
        "capital_gaf": _f("ipps_capital_gaf", 1.0),
        "capital_dsh_percent": _f("ipps_capital_dsh_percent", 0.0),
        "capital_ime_percent": _f("ipps_capital_ime_percent", 0.0),
        "capital_outlier_percent": _f("ipps_capital_outlier_percent", 0.0),
        "dsh_percent": _f("ipps_dsh_percent", 0.0),
        "ime_percent": _f("ipps_ime_percent", 0.0),
        "wage_index": _f("ipps_wage_index", 1.0),
        "labor_share": _f("ipps_labor_share", 0.6860),
        "ccr": _f("ipps_cost_to_charge_ratio", 0.0),
        "outlier_threshold": _f("ipps_outlier_fixed_loss_threshold", 0.0),
        "outlier_marginal": _f("ipps_outlier_marginal_cost_factor", 0.80),
        "sequester_percent": _f("ipps_sequestration_percent", 2.0),
    }


# ---------------------------------------------------------------------------
# Core IPPS Calculation
# ---------------------------------------------------------------------------

def compute_ipps_payment(
    drg_weight: float,
    total_charges: float,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Full IPPS payment calculation.

    Returns a dict with each component and the final expected payment.
    """
    base_rate = float(params.get("operating_base_rate", 0.0))
    dsh_pct = float(params.get("dsh_percent", 0.0)) / 100.0
    ime_pct = float(params.get("ime_percent", 0.0)) / 100.0

    # ── Operating payment ──
    # Operating = base_rate × DRG_weight × (1 + DSH% + IME%)
    operating_payment = base_rate * drg_weight * (1.0 + dsh_pct + ime_pct)

    # ── Capital payment ──
    capital_rate = float(params.get("capital_federal_rate", 0.0))
    capital_gaf = float(params.get("capital_gaf", 1.0))
    cap_adj_pct = (
        float(params.get("capital_dsh_percent", 0.0))
        + float(params.get("capital_ime_percent", 0.0))
        + float(params.get("capital_outlier_percent", 0.0))
    ) / 100.0
    capital_payment = capital_rate * capital_gaf * drg_weight * (1.0 + cap_adj_pct)

    # ── Outlier payment ──
    ccr = float(params.get("ccr", 0.0))
    outlier_threshold = float(params.get("outlier_threshold", 0.0))
    outlier_marginal = float(params.get("outlier_marginal", 0.80))

    outlier_payment = 0.0
    if ccr > 0 and outlier_threshold > 0 and total_charges > 0:
        cost_estimate = total_charges * ccr
        excess = cost_estimate - (operating_payment + capital_payment + outlier_threshold)
        if excess > 0:
            outlier_payment = excess * outlier_marginal

    # ── Sequestration ──
    sequester_pct = float(params.get("sequester_percent", 2.0)) / 100.0
    subtotal = operating_payment + capital_payment + outlier_payment
    sequester_reduction = subtotal * sequester_pct
    total_expected = subtotal - sequester_reduction

    return {
        "operating_payment": round(operating_payment, 2),
        "capital_payment": round(capital_payment, 2),
        "outlier_payment": round(outlier_payment, 2),
        "subtotal_before_sequester": round(subtotal, 2),
        "sequester_reduction": round(sequester_reduction, 2),
        "total_expected": round(total_expected, 2),
        "params_used": {
            "operating_base_rate": base_rate,
            "drg_weight": drg_weight,
            "dsh_percent": params.get("dsh_percent"),
            "ime_percent": params.get("ime_percent"),
            "capital_federal_rate": capital_rate,
            "capital_gaf": capital_gaf,
            "capital_adjustment_percent": round(cap_adj_pct * 100, 2),
            "ccr": ccr,
            "outlier_threshold": outlier_threshold,
            "outlier_marginal": outlier_marginal,
            "sequester_percent": params.get("sequester_percent"),
        },
    }


# ---------------------------------------------------------------------------
# Public entry point: reprice one inpatient claim
# ---------------------------------------------------------------------------

def reprice_ipps_claim(
    claim: Dict[str, Any],
    rule_library: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Reprice a single inpatient claim using the IPPS formula.

    `claim` should contain:
        - drg_code:  str  (MS-DRG code from the 835 or parsed claim)
        - total_charges: float
        - claim_payment_amount: float  (as-paid amount)
        - discharge_status: str (optional)
        - drg_weight: float (optional — from CSV; overrides lookup if present)

    When the CSV includes MAC remittance component columns (op_base_pay,
    dsh_amount, ime_amount, cap_pay, outlier_amount), those are used as
    the "expected" values for comparison instead of computing from the rule
    library formula.

    Returns a repricing result dict compatible with the existing audit pipeline
    findings format.
    """
    drg_code = claim.get("drg_code")
    total_charges = float(claim.get("total_charges") or claim.get("total_charge_amount") or 0.0)
    as_paid = float(claim.get("claim_payment_amount") or 0.0)
    discharge_status = claim.get("discharge_status")

    # ── MAC remittance shortcut: if the file already contains IPPS components,
    #    use those directly instead of recomputing from the rule library. ──
    op_base = float(claim.get("op_base_pay") or 0.0)
    dsh_amt = float(claim.get("dsh_amount") or 0.0)
    ime_amt = float(claim.get("ime_amount") or 0.0)
    cap_pay = float(claim.get("capital_pay") or 0.0)
    outlier_amt = float(claim.get("outlier_amount") or 0.0)
    seq_amt = float(claim.get("sequester_amount") or 0.0)

    if op_base > 0:
        # MAC remittance has pre-computed IPPS components — use them
        gross = op_base + dsh_amt + ime_amt + cap_pay + outlier_amt
        expected = gross - seq_amt if seq_amt > 0 else gross
        variance = expected - as_paid
        variance_pct = (variance / expected * 100.0) if expected > 0 else 0.0
        drg_wt = float(claim.get("drg_weight") or 0.0)

        return {
            "errors": [],
            "claim_type": "INSTITUTIONAL_IP",
            "repricing_method": "IPPS_MAC_REMITTANCE",
            "expected_payment": round(expected, 2),
            "actual_paid": round(as_paid, 2),
            "variance_amount": round(variance, 2),
            "variance_percent": round(variance_pct, 2),
            "confidence_score": 95.0,
            "rate_source": "MAC_REMITTANCE_COMPONENTS",
            "drg_code": drg_code,
            "drg_weight": drg_wt,
            "drg_weight_source": "CSV_FILE",
            "components": {
                "operating_payment": round(op_base, 2),
                "dsh_amount": round(dsh_amt, 2),
                "ime_amount": round(ime_amt, 2),
                "capital_payment": round(cap_pay, 2),
                "outlier_payment": round(outlier_amt, 2),
                "subtotal_before_sequester": round(gross, 2),
                "sequester_reduction": round(seq_amt, 2),
                "total_expected": round(expected, 2),
            },
        }

    errors: List[str] = []

    # Resolve DRG weight — prefer CSV-provided weight, then rule library, then fallback
    csv_drg_weight = float(claim.get("drg_weight") or 0.0)
    if csv_drg_weight > 0:
        drg_weight = csv_drg_weight
        drg_result = {"weight": csv_drg_weight, "source": "CSV_FILE", "errors": []}
    else:
        drg_result = lookup_drg_weight(drg_code, rule_library)
        drg_weight = drg_result["weight"]
    errors.extend(drg_result.get("errors", []))

    # Get IPPS parameters from rule library
    params = _get_ipps_params(rule_library)

    if params["operating_base_rate"] == 0.0:
        errors.append("MISSING_OPERATING_BASE_RATE")
        return {
            "errors": errors,
            "claim_type": "INSTITUTIONAL_IP",
            "repricing_method": "IPPS",
            "expected_payment": None,
            "actual_paid": round(as_paid, 2),
            "variance_amount": None,
            "variance_percent": None,
            "confidence_score": 10.0,
            "rate_source": "IPPS_INCOMPLETE",
            "drg_code": drg_code,
            "drg_weight": drg_weight,
            "drg_weight_source": drg_result["source"],
            "components": None,
        }

    # Compute IPPS payment
    ipps_result = compute_ipps_payment(
        drg_weight=drg_weight,
        total_charges=total_charges,
        params=params,
    )

    expected = ipps_result["total_expected"]
    variance = expected - as_paid
    variance_pct = (variance / expected * 100.0) if expected > 0 else 0.0

    # Build confidence score
    confidence = 85.0
    if "DRG_WEIGHT_NOT_FOUND" in errors:
        confidence -= 30.0
    if "MISSING_DRG_CODE" in errors:
        confidence -= 40.0
    if params["capital_federal_rate"] == 0.0:
        confidence -= 10.0
        errors.append("MISSING_CAPITAL_RATE")
    if params["ccr"] == 0.0:
        confidence -= 5.0  # outlier calc won't fire, but still usable

    # Transfer adjustment check
    if discharge_status and discharge_status in ("02", "05", "43", "65"):
        errors.append("TRANSFER_CASE_CHECK_NEEDED")
        confidence -= 10.0

    return {
        "errors": errors,
        "claim_type": "INSTITUTIONAL_IP",
        "repricing_method": "IPPS",
        "expected_payment": round(expected, 2),
        "actual_paid": round(as_paid, 2),
        "variance_amount": round(variance, 2),
        "variance_percent": round(variance_pct, 2),
        "confidence_score": max(0.0, confidence),
        "rate_source": f"IPPS_{drg_result['source']}",
        "drg_code": drg_code,
        "drg_weight": drg_weight,
        "drg_weight_source": drg_result["source"],
        "components": ipps_result,
    }

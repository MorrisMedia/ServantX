"""
Pricing Orchestrator — runs one or more pricing engines on a single parsed claim.

Pricing Modes
-------------
AUTO     : Detect payer from claim's payer_key. Route to:
           - MEDICARE claim → MPFS / IPPS / OPPS fee schedules (DB-backed)
           - TX_MEDICAID → TX Medicaid FFS (DB-backed)
           - OTHER → Contract rule library. If low confidence (<40), also run AI.
MEDICARE : Force Medicare fee schedules regardless of payer field in invoice.
MEDICAID : Force state Medicaid fee schedule (hospital.state determines which state).
           Currently TX only; others fall back to CONTRACT.
CONTRACT : Use contract rule library + AI analysis. Skip fee schedule engines.
ALL      : Run ALL applicable engines (fee schedule + contract rules + AI).
           Surface all results. recommended = highest variance where confidence >= 30.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


async def price_claim(
    parsed_claim: Dict[str, Any],
    claim_type: str,           # PROFESSIONAL | INSTITUTIONAL_IP | INSTITUTIONAL_OP
    contracts: List[Dict[str, Any]],  # [{id, name, text, rule_library}]
    hospital_id: str,
    pricing_mode: str,         # AUTO | MEDICARE | MEDICAID | CONTRACT | ALL
    state: Optional[str],      # Two-letter state for Medicaid routing
    receipt_raw_text: str,     # Full raw text of the receipt file (for AI)
    receipt_name: str,         # Filename for logging/display
) -> Dict[str, Any]:
    """
    Run one or more pricing engines on a single parsed claim and return a
    unified comparison result.

    Returns
    -------
    {
        "recommended": { ...repricing result dict... },
        "all_results": [ {"engine": "MPFS", ...}, ... ],
        "pricing_mode_used": "AUTO",
        "engines_run": ["MPFS", "CONTRACT"],
    }
    """
    # Local imports to avoid circular dependencies at module level
    from services.claim_adjudication_service import reprice_single_claim, match_contract_for_claim
    from services.ai_analysis_service import analyze_underpayment

    all_results: List[Dict[str, Any]] = []
    payer_key = (parsed_claim.get("payer_key") or "OTHER").upper()

    # ── Engine 1: Fee Schedule ──
    # Run when: AUTO (with Medicare/Medicaid payer), MEDICARE forced, or ALL
    run_fee_schedule = (
        pricing_mode == "MEDICARE"
        or pricing_mode == "ALL"
        or (pricing_mode == "AUTO" and "MEDICARE" in payer_key)
        or (pricing_mode == "MEDICAID" and state)
        or (pricing_mode == "AUTO" and "MEDICAID" in payer_key)
    )

    if run_fee_schedule:
        # For forced MEDICARE mode: temporarily set payer_key to MEDICARE so
        # reprice_single_claim routes to the fee schedule engine.
        claim_for_fee = dict(parsed_claim)
        if pricing_mode == "MEDICARE":
            claim_for_fee["payer_key"] = "MEDICARE"
        elif pricing_mode == "MEDICAID":
            # Force TX Medicaid for now (only state implemented)
            claim_for_fee["payer_key"] = "TX_MEDICAID_FFS"

        fee_result = await reprice_single_claim(
            parsed_claim=claim_for_fee,
            claim_type=claim_type,
            rule_library={},  # don't use contract library in fee-schedule run
            service_lines=claim_for_fee.get("service_lines"),
        )
        fee_payer = (claim_for_fee.get("payer_key") or "").upper()
        if claim_type == "PROFESSIONAL" and "MEDICARE" in fee_payer:
            engine_name = "MPFS"
        elif claim_type == "INSTITUTIONAL_IP":
            engine_name = "IPPS"
        elif claim_type == "INSTITUTIONAL_OP":
            engine_name = "OPPS"
        elif "MEDICAID" in fee_payer:
            engine_name = "TX_MEDICAID"
        else:
            engine_name = "FEE_SCHEDULE"

        all_results.append({**fee_result, "engine": engine_name})

    # ── Engine 2: Contract Rules ──
    # Run when: CONTRACT, ALL, or AUTO with no fee schedule or OTHER payer
    run_contract = (
        pricing_mode in ("CONTRACT", "ALL")
        or (pricing_mode == "AUTO" and ("OTHER" in payer_key or not run_fee_schedule))
    )

    matched_contract = match_contract_for_claim(parsed_claim, contracts) if contracts else None

    if run_contract and matched_contract:
        rule_library = matched_contract.get("rule_library") or {}
        if rule_library and isinstance(rule_library, dict) and rule_library.get("rule_count", 0) > 0:
            contract_result = await reprice_single_claim(
                parsed_claim=parsed_claim,
                claim_type=claim_type,
                rule_library=rule_library,
                service_lines=parsed_claim.get("service_lines"),
            )
            all_results.append({**contract_result, "engine": "CONTRACT"})

    # ── Engine 3: AI Analysis ──
    # Run when: CONTRACT or ALL mode, UNKNOWN format, or deterministic engines have low confidence
    deterministic_confidence = (
        max((r.get("confidence_score") or 0) for r in all_results) if all_results else 0
    )

    run_ai = (
        pricing_mode in ("CONTRACT", "ALL")
        or (pricing_mode == "AUTO" and deterministic_confidence < 40)
        or (not all_results)  # nothing else worked
    )

    if run_ai and matched_contract:
        contract_text = matched_contract.get("text") or ""
        rule_library = matched_contract.get("rule_library")
        if contract_text or rule_library:
            try:
                ai_raw = await analyze_underpayment(
                    contract_text=contract_text,
                    receipt_text=receipt_raw_text,
                    contract_name=matched_contract.get("name", "Contract"),
                    receipt_name=receipt_name,
                    rule_library=rule_library,
                    hospital_id=hospital_id,
                )
                # Normalize to standard repricing result shape
                ai_variance = float(ai_raw.get("underpayment_amount") or 0.0)
                ai_expected = float(ai_raw.get("contract_amount") or 0.0)
                ai_actual = float(ai_raw.get("receipt_amount") or 0.0)
                ai_pct = (ai_variance / ai_expected * 100) if ai_expected > 0 else 0.0
                all_results.append({
                    "engine": "AI",
                    "repricing_method": "AI_CONTRACT_ANALYSIS",
                    "expected_payment": round(ai_expected, 2) if ai_expected > 0 else None,
                    "actual_paid": round(ai_actual, 2),
                    "variance_amount": round(ai_variance, 2),
                    "variance_percent": round(ai_pct, 2),
                    "confidence_score": 55.0 if ai_raw.get("has_underpayment") else 40.0,
                    "rate_source": "AI_ANALYSIS",
                    "errors": [],
                    "ai_reasoning": ai_raw.get("reasoning", ""),
                    "contract_name": matched_contract.get("name"),
                })
            except Exception:
                # AI failure is non-fatal
                pass

    # ── Select recommended result ──
    if not all_results:
        # Nothing ran — return a zero result
        return {
            "recommended": {
                "errors": ["NO_PRICING_ENGINE_AVAILABLE"],
                "claim_type": claim_type,
                "repricing_method": "NONE",
                "expected_payment": None,
                "actual_paid": float(parsed_claim.get("claim_payment_amount") or 0.0),
                "variance_amount": None,
                "variance_percent": None,
                "confidence_score": 0.0,
                "rate_source": "NONE",
                "per_line_results": [],
                "components": None,
            },
            "all_results": [],
            "pricing_mode_used": pricing_mode,
            "engines_run": [],
        }

    # For ALL mode: pick highest variance where confidence >= 30
    # For other modes: pick highest confidence
    if pricing_mode == "ALL":
        eligible = [
            r for r in all_results
            if (r.get("confidence_score") or 0) >= 30 and (r.get("variance_amount") or 0) > 0
        ]
        recommended = (
            max(eligible, key=lambda r: r.get("variance_amount") or 0)
            if eligible
            else max(all_results, key=lambda r: r.get("confidence_score") or 0)
        )
    else:
        recommended = max(all_results, key=lambda r: r.get("confidence_score") or 0)

    engines_run = [r.get("engine", "UNKNOWN") for r in all_results]

    return {
        "recommended": recommended,
        "all_results": all_results,
        "pricing_mode_used": pricing_mode,
        "engines_run": engines_run,
    }

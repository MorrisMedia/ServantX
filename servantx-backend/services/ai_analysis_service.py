import json
import asyncio
import csv
import io
import re
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
from core_services.openai_service import chat_with_openai_async
from services.contract_rules_engine import extract_candidate_rule_lines, extract_conditions
from services.phi_service import deidentify_835_text, reidentify_text


class PaymentAnalysis(BaseModel):
    payment_description: str
    expected_amount: float
    actual_amount: float
    difference: float
    has_violation: bool
    reasoning: str


class UnderpaymentAnalysis(BaseModel):
    has_underpayment: bool
    underpayment_amount: float
    contract_amount: float
    receipt_amount: float
    reasoning: str


def _to_float(value: object) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).strip()
    if not cleaned:
        return None
    cleaned = cleaned.replace("$", "").replace(",", "")
    try:
        return float(cleaned)
    except Exception:
        return None


def _extract_835_claim_payment(receipt_text: str) -> Optional[float]:
    clp_match = re.search(
        r"CLP\*[^*~]*\*[^*~]*\*([0-9]+(?:\.[0-9]+)?)\*([0-9]+(?:\.[0-9]+)?)",
        receipt_text,
        flags=re.IGNORECASE,
    )
    if not clp_match:
        return None
    # CLP04 is the claim payment amount.
    return _to_float(clp_match.group(2))


def _extract_delimited_payment(receipt_text: str) -> Optional[float]:
    lines = [line for line in receipt_text.splitlines() if line.strip()]
    if len(lines) < 2:
        return None

    delimiter = None
    if "," in lines[0]:
        delimiter = ","
    elif "|" in lines[0]:
        delimiter = "|"
    if delimiter is None:
        return None

    try:
        sample = "\n".join(lines[:20])
        reader = csv.DictReader(io.StringIO(sample), delimiter=delimiter)
        row = next(reader, None)
    except Exception:
        row = None

    if not row:
        return None

    normalized = {str(k).strip().lower(): v for k, v in row.items()}
    primary_keys = (
        "claim_payment_amount",
        "line_payment_amount",
        "payment_amount",
        "amount_paid",
        "paid_amount",
        "paid",
        "payment",
        "net_pay",
        "net_amount",
        "reimbursement",
    )
    secondary_keys = (
        "allowed_amount",
        "line_allowed_amount",
        "cov_chg",
        "tot_chg",
        "total_charge",
        "total",
    )

    for key in primary_keys:
        for column, value in normalized.items():
            if key in column:
                parsed = _to_float(value)
                if parsed is not None:
                    return parsed

    for key in secondary_keys:
        for column, value in normalized.items():
            if key in column:
                parsed = _to_float(value)
                if parsed is not None:
                    return parsed

    return None


def _extract_free_text_payment(receipt_text: str) -> Optional[float]:
    keyword_match = re.search(
        r"(?i)(?:net\s*pay|amount\s*paid|payment\s*amount|paid)\D{0,20}\$?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)",
        receipt_text,
    )
    if keyword_match:
        return _to_float(keyword_match.group(1))

    amount_matches = re.findall(r"\$?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", receipt_text)
    if not amount_matches:
        return None
    # Use the first monetary amount as a weak fallback.
    return _to_float(amount_matches[0])


def _extract_actual_paid(receipt_text: str) -> Tuple[Optional[float], str]:
    amount = _extract_835_claim_payment(receipt_text)
    if amount is not None:
        return amount, "from 835 CLP04 payment amount"

    amount = _extract_delimited_payment(receipt_text)
    if amount is not None:
        return amount, "from delimited billing record payment field"

    amount = _extract_free_text_payment(receipt_text)
    if amount is not None:
        return amount, "from free-text amount parsing"

    return None, "no payment amount found in billing record"


def _infer_receipt_period(receipt_text: str) -> Optional[str]:
    text = (receipt_text or "").lower()
    if not text:
        return None

    if re.search(r"\bq[1-4]\b|\bquarter(?:ly)?\b|per quarter", text):
        return "quarterly"
    if re.search(r"\bmonthly\b|per month|/month", text):
        return "monthly"
    if re.search(
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
        text,
    ):
        return "monthly"
    if re.search(r"\bannual(?:ly)?\b|per year|/year|per annum|fiscal year", text):
        return "annual"
    if re.search(r"\bweekly\b|per week|/week", text):
        return "weekly"
    if re.search(r"\bdaily\b|per day|/day", text):
        return "daily"
    return None


def _infer_rule_period(rule_line: str, conditions: Dict) -> Optional[str]:
    if isinstance(conditions.get("period"), str):
        return str(conditions.get("period"))

    text = (rule_line or "").lower()
    if any(token in text for token in ("per service", "each service", "per claim", "per visit")):
        return "per_service"
    if any(token in text for token in ("per hour", "hourly")):
        return "hourly"
    if any(token in text for token in ("per day", "daily")):
        return "daily"
    if any(token in text for token in ("per week", "weekly")):
        return "weekly"
    if any(token in text for token in ("per month", "monthly", "/month")):
        return "monthly"
    if any(token in text for token in ("per quarter", "quarterly", "/quarter", "q1", "q2", "q3", "q4")):
        return "quarterly"
    if any(token in text for token in ("per year", "yearly", "annual", "annually", "per annum", "/year")):
        return "annual"
    return None


def _convert_amount_between_periods(amount: float, source_period: str, target_period: str) -> float:
    annual_scale = {
        "annual": 1.0,
        "quarterly": 4.0,
        "monthly": 12.0,
        "weekly": 52.0,
        "daily": 365.0,
    }
    if source_period not in annual_scale or target_period not in annual_scale:
        return amount
    annualized_amount = amount * annual_scale[source_period]
    return annualized_amount / annual_scale[target_period]


def _extract_expected_from_rules(contract_text: str, receipt_text: str = "") -> Tuple[Optional[float], str]:
    candidate_lines = extract_candidate_rule_lines(contract_text)
    if not candidate_lines:
        return None, "no contract rules found for expected amount"

    prioritized: List[Tuple[float, int, str]] = []
    non_prioritized: List[Tuple[float, int, str]] = []
    priority_tokens = ("reimbursement", "payment", "rate", "baseline", "allowed", "amount")
    receipt_period = _infer_receipt_period(receipt_text)
    seen_candidates = set()

    for line in candidate_lines:
        conditions = extract_conditions(line) or {}
        line_lower = line.lower()
        line_period = _infer_rule_period(line, conditions)
        line_candidates: List[Tuple[float, str]] = []

        currency_amounts = re.findall(
            r"(?i)(?:\$\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)|([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*(?:usd|dollars?))",
            line,
        )
        for direct_match in currency_amounts:
            raw_value = direct_match[0] or direct_match[1]
            parsed = _to_float(raw_value)
            if parsed is None or parsed <= 0:
                continue
            line_candidates.append((parsed, raw_value))

        for raw_amount in conditions.get("amounts", []):
            parsed = _to_float(raw_amount)
            if parsed is None or parsed <= 0:
                continue
            # Avoid using year-like values (for example from contract titles/dates).
            raw_str = str(raw_amount).strip().lower()
            if (
                parsed.is_integer()
                and 1900 <= int(parsed) <= 2100
                and ("$" not in raw_str)
                and ("usd" not in raw_str)
                and ("dollar" not in raw_str)
            ):
                continue
            line_candidates.append((parsed, str(raw_amount)))

        for parsed, raw_value in line_candidates:
            normalized_amount = parsed
            period_note = ""
            if (
                receipt_period
                and line_period
                and receipt_period != line_period
                and line_period in {"annual", "quarterly", "monthly", "weekly", "daily"}
            ):
                converted = _convert_amount_between_periods(parsed, line_period, receipt_period)
                normalized_amount = round(converted, 2)
                period_note = (
                    f" [normalized {parsed:.2f} from {line_period} to {receipt_period}"
                    f" => {normalized_amount:.2f}]"
                )

            if normalized_amount <= 0:
                continue

            score = 0
            if any(token in line_lower for token in priority_tokens):
                score += 3
            if line_period:
                score += 1
            if receipt_period and line_period == receipt_period:
                score += 1
            if "$" in str(raw_value) or "usd" in str(raw_value).lower() or "dollar" in str(raw_value).lower():
                score += 1
            if conditions.get("comparisonOperator"):
                score += 1

            signature = (round(normalized_amount, 2), line)
            if signature in seen_candidates:
                continue
            seen_candidates.add(signature)

            evidence = f"{line}{period_note}"
            if any(token in line_lower for token in priority_tokens):
                prioritized.append((normalized_amount, score, evidence))
            else:
                non_prioritized.append((normalized_amount, score, evidence))

    ranked = prioritized if prioritized else non_prioritized
    if ranked:
        ranked.sort(key=lambda item: (-item[1], item[0]))
    chosen = ranked[0] if ranked else None
    if not chosen:
        return None, "no numeric rule amount found in contract rules"

    return chosen[0], f"from contract rule line: {chosen[2]}"


def _deterministic_rule_fallback(
    contract_text: str,
    receipt_text: str,
    contract_name: str,
) -> Dict:
    expected_amount, expected_source = _extract_expected_from_rules(contract_text, receipt_text)
    actual_amount, actual_source = _extract_actual_paid(receipt_text)

    if expected_amount is None or actual_amount is None:
        missing = []
        if expected_amount is None:
            missing.append("expected amount")
        if actual_amount is None:
            missing.append("actual paid amount")
        reason = (
            "Deterministic rules fallback could not compute underpayment because "
            + " and ".join(missing)
            + f". Contract source: {expected_source}. Receipt source: {actual_source}."
        )
        return {
            "has_underpayment": False,
            "underpayment_amount": 0.0,
            "contract_amount": float(expected_amount or 0.0),
            "receipt_amount": float(actual_amount or 0.0),
            "reasoning": reason,
            "contract_name": contract_name,
        }

    underpayment_amount = round(max(expected_amount - actual_amount, 0.0), 2)
    has_underpayment = underpayment_amount > 0
    reasoning = (
        "Deterministic rules fallback used (AI unavailable or no structured AI output). "
        f"Expected {expected_amount:.2f} ({expected_source}); "
        f"Paid {actual_amount:.2f} ({actual_source}); "
        f"Underpayment {underpayment_amount:.2f}."
    )
    return {
        "has_underpayment": has_underpayment,
        "underpayment_amount": underpayment_amount,
        "contract_amount": round(expected_amount, 2),
        "receipt_amount": round(actual_amount, 2),
        "reasoning": reasoning,
        "contract_name": contract_name,
    }


def _format_rule_library_for_prompt(rule_library: Optional[Dict]) -> str:
    """Format the rule library into a concise summary for the AI prompt."""
    if not rule_library:
        return ""

    sections: List[str] = []

    # Contract metadata
    meta_parts = []
    if rule_library.get("contract_type"):
        meta_parts.append(f"Type: {rule_library['contract_type']}")
    if rule_library.get("payer_name"):
        meta_parts.append(f"Payer: {rule_library['payer_name']}")
    if rule_library.get("state"):
        meta_parts.append(f"State: {rule_library['state']}")
    if rule_library.get("effective_date"):
        meta_parts.append(f"Effective: {rule_library['effective_date']}")
    if meta_parts:
        sections.append("CONTRACT: " + " | ".join(meta_parts))

    # Inpatient
    ip_parts = []
    if rule_library.get("inpatient_method"):
        ip_parts.append(f"Method: {rule_library['inpatient_method']}")
    if rule_library.get("inpatient_base_rate"):
        ip_parts.append(f"Base rate: ${rule_library['inpatient_base_rate']}")
    if rule_library.get("inpatient_percent_of_medicare"):
        ip_parts.append(f"{rule_library['inpatient_percent_of_medicare']}% of Medicare")
    if ip_parts:
        sections.append("INPATIENT: " + " | ".join(ip_parts))

    # Per-diem rates
    for pd in (rule_library.get("per_diem_rates") or []):
        if isinstance(pd, dict):
            sections.append(f"  Per-diem {pd.get('service_type','')}: ${pd.get('rate',0)}/day")

    # Outpatient
    op_parts = []
    if rule_library.get("outpatient_method"):
        op_parts.append(f"Method: {rule_library['outpatient_method']}")
    if rule_library.get("outpatient_base_rate"):
        op_parts.append(f"Base rate: ${rule_library['outpatient_base_rate']}")
    if rule_library.get("outpatient_percent_of_medicare"):
        op_parts.append(f"{rule_library['outpatient_percent_of_medicare']}% of Medicare")
    if op_parts:
        sections.append("OUTPATIENT: " + " | ".join(op_parts))

    # Fee schedule (summarize first 30 entries)
    fee_entries = rule_library.get("fee_schedule") or []
    if fee_entries:
        lines = []
        for entry in fee_entries[:30]:
            if isinstance(entry, dict):
                parts = [f"{entry.get('code_type','')}: {entry.get('code','')}"]
                if entry.get("rate"):
                    parts.append(f"${entry['rate']}")
                if entry.get("percent_of_medicare"):
                    parts.append(f"{entry['percent_of_medicare']}% Medicare")
                if entry.get("description"):
                    parts.append(entry["description"])
                lines.append(" | ".join(parts))
        if lines:
            sections.append("FEE SCHEDULE:\n  " + "\n  ".join(lines))

    # Percentage rules
    for pr in (rule_library.get("percentage_rules") or []):
        if isinstance(pr, dict):
            parts = [f"{pr.get('percent',0)}% of {pr.get('benchmark','')}"]
            if pr.get("applies_to"):
                parts.append(f"for {pr['applies_to']}")
            sections.append("PCT RULE: " + " | ".join(parts))

    # Stop-loss
    for sl in (rule_library.get("stop_loss_provisions") or []):
        if isinstance(sl, dict):
            sections.append(f"STOP-LOSS: ${sl.get('threshold',0)} ({sl.get('threshold_type','')})")

    # Timely filing
    for tf in (rule_library.get("timely_filing_rules") or []):
        if isinstance(tf, dict):
            sections.append(f"TIMELY FILING: {tf.get('deadline_days',0)} {tf.get('deadline_type','')} days")

    # Payment timelines
    for pt in (rule_library.get("payment_timelines") or []):
        if isinstance(pt, dict):
            sections.append(f"PAYMENT TERMS: NET {pt.get('days',0)} ({pt.get('timeline_type','')})")

    # General rules (first 20)
    for gr in (rule_library.get("general_payment_rules") or [])[:20]:
        if isinstance(gr, dict) and gr.get("rule_text"):
            sections.append(f"RULE: {gr['rule_text'][:200]}")

    if not sections:
        return ""

    return "\n".join(sections)


async def analyze_underpayment(
    contract_text: str,
    receipt_text: str,
    contract_name: str,
    receipt_name: str,
    rule_library: Optional[Dict] = None,
    hospital_id: Optional[str] = None,
) -> Dict:
    """
    Async function to analyze underpayment using OpenAI.

    PHI in the receipt (835 EDI) is de-identified via phi_service before
    being sent to the external API. The LLM only sees opaque tokens.
    """
    print(f"\n[AI SERVICE] Starting async analysis for {contract_name}...", flush=True)

    # ── HIPAA: De-identify PHI in 835 receipt text before sending to LLM ───
    phi_token_map: Dict[str, str] = {}
    safe_receipt_text = receipt_text
    if hospital_id and receipt_text:
        safe_receipt_text, phi_token_map = deidentify_835_text(receipt_text, hospital_id)
        print(f"[PHI] De-identified {len(phi_token_map)} PHI tokens from receipt text", flush=True)
    # Contract text never contains patient PHI — send as-is.

    print(f"\n{'='*80}", flush=True)
    print(f"ANALYZING UNDERPAYMENT WITH OPENAI (ASYNC)", flush=True)
    print(f"{'='*80}", flush=True)
    print(f"Contract: {contract_name}", flush=True)
    print(f"Receipt: {receipt_name}", flush=True)
    print(f"\nContract Text Preview (first 500 chars):", flush=True)
    print(contract_text[:500] if contract_text else "No text", flush=True)
    print(f"\nReceipt Text Preview (first 500 chars, de-identified):", flush=True)
    print(safe_receipt_text[:500] if safe_receipt_text else "No text", flush=True)
    print(f"{'='*80}\n", flush=True)

    system_prompt = """You are an expert revenue integrity analyst specialized in identifying hospital underpayments. 

Key principles:
- The RECEIPT amount is your base truth - never modify it
- Always prorate the CONTRACT to match the RECEIPT's time period (not the other way around)
- receipt_amount = exact amount from receipt (unchanged)
- contract_amount = prorated contract amount (converted to match receipt's period)
- underpayment_amount = contract_amount - receipt_amount
- Show step-by-step prorating calculations in reasoning
- Be conservative: when unclear, favor no underpayment over false positives
- Extract amounts accurately from contracts and receipts
- Always respond in valid JSON format"""
    
    # Build rule library summary for the prompt
    library_summary = _format_rule_library_for_prompt(rule_library)
    library_section = ""
    if library_summary:
        library_section = f"""
EXTRACTED PAYMENT RULE LIBRARY (use these as your primary reference for expected payments):
{library_summary}

"""

    user_prompt = f"""Analyze the following contract and receipt to identify any underpayment issues.

CONTRACT ({contract_name}):
{contract_text[:4000] if contract_text else "No contract text available"}
{library_section}
RECEIPT ({receipt_name}):
{safe_receipt_text[:4000] if safe_receipt_text else "No receipt text available"}

Your task:
1. IDENTIFY PAYMENT STRUCTURE in the contract:
   - Look for payment frequency: annual, monthly, quarterly, per-visit, per-procedure, per-service
   - Look for rate cards, fee schedules, or service-specific pricing
   - Identify if this is a lump sum contract or per-service contract
   - Note any payment terms, schedules, or conditions

2. EXTRACT THE CORRECT PAYMENT AMOUNT FROM RECEIPT (CRITICAL):
   - Look for: "Net Pay", "Total Payment", "Amount Paid", "Payment Amount", "Total", "Net Amount"
   - IGNORE these fields: "Gross Salary", "YTD Total", "Annual Salary", "Year to Date", "Cumulative"
   - IGNORE deduction amounts - we want what was actually PAID, not deducted
   - If you see multiple amounts, choose the one labeled as the actual payment/net pay
   - The payment amount is typically the FINAL amount after all deductions
   - Double-check: If the amount seems way too high compared to context, you may be reading the wrong field

3. IDENTIFY THE RECEIPT'S EXACT TIME PERIOD:
   - Look for explicit dates: "January 2024", "Q1 2024", "Fiscal Year 2024", etc.
   - Look for keywords: "monthly", "quarterly", "annual", "per month", "this month", etc.
   - Look for date ranges: "01/01/24 - 01/31/24" = monthly, "01/01/24 - 12/31/24" = annual
   - If the receipt shows ONE MONTH worth of service/payment, it's MONTHLY
   - If the receipt shows THREE MONTHS, it's QUARTERLY  
   - If the receipt shows TWELVE MONTHS or a full year, it's ANNUAL
   - Be SPECIFIC - don't use vague terms like "payment period"
   - STATE EXPLICITLY: "This receipt is for [MONTHLY/QUARTERLY/ANNUAL] payment"

4. EXPLICITLY STATE THE RECEIPT'S TIME PERIOD:
   - Based on step 3, explicitly state: "This receipt represents a [MONTHLY/QUARTERLY/ANNUAL] payment"
   - If you cannot determine the exact period, look at the amount and context clues
   - Common clues:
     * If receipt shows ~1/12 of annual amount → likely monthly
     * If receipt shows ~1/4 of annual amount → likely quarterly
     * If receipt shows similar amount to annual contract → likely annual
   - The receipt's time period is your BASE - everything else adjusts to match it
   - DO NOT change or multiply the receipt amount - it is the ACTUAL amount paid

5. PRORATE THE CONTRACT TO MATCH THE RECEIPT'S PERIOD:
   - Take the contract amount and convert it to match the receipt's time period
   - If receipt is monthly and contract is annual: contract_amount ÷ 12
   - If receipt is quarterly and contract is annual: contract_amount ÷ 4  
   - If receipt is monthly and contract is quarterly: contract_amount ÷ 3
   - Show your calculation clearly (e.g., "$24,000/year ÷ 12 = $2,000/month expected")
   
5. CALCULATE AMOUNTS:
   - receipt_amount: The EXACT amount from the receipt (DO NOT MODIFY THIS)
   - contract_amount: The prorated contract amount matching the receipt's time period
   - underpayment_amount: contract_amount - receipt_amount (if positive, there's underpayment)
   
   Example:
   - Contract says: $24,000/year
   - Receipt shows: $1,800 for one month
   - Your calculation: "$24,000 ÷ 12 = $2,000/month expected"
   - contract_amount: 2000
   - receipt_amount: 1800
   - underpayment_amount: 200

7. CALCULATE UNDERPAYMENT:
   - Underpayment = (prorated contract amount) - (actual receipt amount)
   - Flag has_underpayment = true ONLY if underpayment_amount > 0
   - If structures fundamentally don't match (e.g., annual lump sum vs per-service receipt with no per-service rate in contract), set has_underpayment = false
   - Explain clearly in reasoning why you did or didn't flag an underpayment

8. PROVIDE CLEAR REASONING (MUST INCLUDE):
   - LINE 1: "Receipt Analysis: This receipt is for a [MONTHLY/QUARTERLY/ANNUAL] payment of $X"
   - LINE 2: "Contract Terms: Contract specifies $Y per [MONTH/QUARTER/YEAR]"
   - LINE 3: "Prorating: $Y [contract period] ÷ Z = $A per [receipt period]" (if periods differ)
   - LINE 4: "Comparison: Expected $A, Paid $X"
   - LINE 5: "Underpayment: $A - $X = $B" (or "No underpayment" if negative)
   - If you cannot make a valid comparison, explain why
   - NEVER use vague terms like "payment period" - always say MONTHLY, QUARTERLY, or ANNUAL

CRITICAL RULES:
- Extract the CORRECT amount from receipt - look for "Net Pay" or "Total Payment", NOT "Gross Salary" or "YTD"
- ALWAYS use the receipt's time period as your base - NEVER modify the receipt amount
- ALWAYS prorate the CONTRACT to match the RECEIPT's time period:
  * If receipt is monthly and contract is annual: contract ÷ 12
  * If receipt is quarterly and contract is annual: contract ÷ 4
  * If receipt is monthly and contract is quarterly: contract ÷ 3
- The receipt_amount field should contain the EXACT amount from the receipt (unchanged)
- The contract_amount field should contain the PRORATED contract amount (converted to match receipt's period)
- The underpayment_amount = contract_amount - receipt_amount
- If the contract is a lump sum (annual/monthly) but the receipt is for a single per-service visit, DO NOT flag underpayment unless the contract also specifies a per-service rate
- If you cannot find a matching rate for the specific service in the receipt, set has_underpayment = false
- Be thorough in searching for amounts - they may appear in tables, headers, or summary sections
- When in doubt, favor false negatives over false positives
- ALWAYS show your step-by-step prorating math in the reasoning field

EXAMPLE TO FOLLOW:
Contract: "$24,000 per year"
Receipt: "$1,800" for "October 2024"

YOUR RESPONSE MUST BE:
- receipt_amount: 1800
- contract_amount: 2000
- underpayment_amount: 200
- reasoning: "Receipt Analysis: This receipt is for a MONTHLY payment of $1,800 (October 2024). Contract Terms: Contract specifies $24,000 per YEAR. Prorating: $24,000 annual ÷ 12 months = $2,000 per MONTH. Comparison: Expected $2,000, Paid $1,800. Underpayment: $2,000 - $1,800 = $200."

WRONG EXAMPLE (DO NOT DO THIS):
- receipt_amount: 21600 (WRONG - never multiply receipt!)
- contract_amount: 24000
- underpayment_amount: 2400
- reasoning: "The receipt shows $1,800 payment period..." (WRONG - too vague!)
"""
    
    try:
        result = await chat_with_openai_async(
            text=user_prompt,
            prompt=system_prompt,
            model="gpt-4.1",
            schema=UnderpaymentAnalysis
        )

        if not isinstance(result, dict) or not result:
            return _deterministic_rule_fallback(
                contract_text=contract_text,
                receipt_text=receipt_text,
                contract_name=contract_name,
            )
        
        print(f"\n{'='*80}", flush=True)
        print(f"AI ANALYSIS RESULT for {contract_name}", flush=True)
        print(f"{'='*80}", flush=True)
        print(json.dumps(result, indent=2), flush=True)
        print(f"{'='*80}\n", flush=True)
        
        return {
            "has_underpayment": result.get("has_underpayment", False),
            "underpayment_amount": float(result.get("underpayment_amount", 0.0)),
            "contract_amount": float(result.get("contract_amount", 0.0)),
            "receipt_amount": float(result.get("receipt_amount", 0.0)),
            "reasoning": result.get("reasoning", "Analysis completed."),
            "contract_name": contract_name
        }
    
    except Exception as e:
        print(f"[AI SERVICE] Error analyzing underpayment for {contract_name}: {e}", flush=True)
        return _deterministic_rule_fallback(
            contract_text=contract_text,
            receipt_text=receipt_text,
            contract_name=contract_name,
        )


async def analyze_receipt_against_all_contracts(
    receipt_text: str,
    receipt_name: str,
    contracts: List[Dict],
    hospital_id: Optional[str] = None,
) -> List[Dict]:
    """
    Analyze a receipt against all contracts in parallel.
    Returns a list of analysis results for each contract.
    """
    print(f"\n[AI SERVICE] Starting parallel analysis against {len(contracts)} contract(s)...", flush=True)

    # Create tasks for all contract analyses
    tasks = []
    for contract in contracts:
        task = analyze_underpayment(
            contract_text=contract.get("text", ""),
            receipt_text=receipt_text,
            contract_name=contract.get("name", "Unknown Contract"),
            receipt_name=receipt_name,
            rule_library=contract.get("rule_library"),
            hospital_id=hospital_id,
        )
        tasks.append(task)
    
    # Run all analyses in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results, handling any exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"[AI SERVICE] Error in analysis task {i}: {result}", flush=True)
            processed_results.append({
                "has_underpayment": False,
                "underpayment_amount": 0.0,
                "contract_amount": 0.0,
                "receipt_amount": 0.0,
                "reasoning": f"Error during analysis: {str(result)}",
                "contract_name": contracts[i].get("name", "Unknown Contract")
            })
        else:
            processed_results.append(result)
    
    print(f"[AI SERVICE] Completed parallel analysis. Found {sum(1 for r in processed_results if r.get('has_underpayment'))} violation(s).", flush=True)
    
    return processed_results

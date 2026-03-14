"""
AI-powered exhaustive rule library extraction.

When a contract is uploaded, this service sends the full contract text to GPT
with a detailed prompt designed to extract every payment verification data point
into a structured ContractRuleLibrary.  A deterministic regex pass supplements
or replaces the AI output when the API key is unavailable.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from core_services.openai_service import chat_with_openai_async
from services.rule_library_schema import (
    AuthRequirement,
    CarveOut,
    CaseRate,
    ContractRuleLibrary,
    DenialRule,
    EscalatorClause,
    FeeScheduleEntry,
    GenericPaymentRule,
    PaymentTimeline,
    PercentageRule,
    PerDiemRate,
    StopLossProvision,
    TimelyFilingRule,
)

# ---------------------------------------------------------------------------
#  AI prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a hospital revenue-integrity analyst.  Your job is to read a payer
contract and produce a **complete, exhaustive** structured extraction of every
payment rule, rate, condition, code, percentage, deadline, penalty, carve-out,
stop-loss threshold, and escalator clause in the document.

The output MUST capture everything a billing auditor needs to determine whether
a specific invoice / claim was paid correctly.

### What to extract

1. **Contract metadata** — payer name, plan, contract type (medicare / medicaid /
   commercial / managed_care / workers_comp / tricare / va), effective &
   termination dates, auto-renewal, state, provider NPI & tax ID.

2. **Inpatient payment methodology** — DRG base rate, per-diem rates (by
   service type with tiered day ranges if applicable), case rates, percent of
   Medicare / Medicaid / billed charges.

   **IPPS-specific fields (CRITICAL for institutional inpatient claims)**:
   - ipps_operating_base_rate: Operating standardized amount (e.g., $6,730.32)
   - ipps_capital_federal_rate: Capital Federal Rate (e.g., $524.15)
   - ipps_capital_gaf: Capital Geographic Adjustment Factor (e.g., 0.9980)
   - ipps_capital_dsh_percent: Capital DSH adjustment %
   - ipps_capital_ime_percent: Capital IME adjustment %
   - ipps_capital_outlier_percent: Capital outlier % (e.g., 8.0 for 8%)
   - ipps_dsh_percent: Operating DSH % (e.g., 5.28)
   - ipps_ime_percent: Operating IME % (e.g., 5.41)
   - ipps_wage_index: Area Wage Index
   - ipps_labor_share: Labor-related share of base rate (~0.6860)
   - ipps_cost_to_charge_ratio: Hospital CCR for outlier calculation
   - ipps_outlier_fixed_loss_threshold: Fixed-loss cost threshold for outliers
   - ipps_outlier_marginal_cost_factor: Marginal cost factor (typically 0.80)
   - ipps_sequestration_percent: Medicare sequestration reduction (e.g., 2.0)
   Look for formulas like "Op = $X × DRG_Wt + DSH (Y%) + IME (Z%)" and
   extract each component.  Any mention of "standardized amount", "base rate",
   "DRG weight", "DSH", "IME", "capital", "sequestration", "outlier" in the
   context of inpatient payment should be extracted to the ipps_ fields.

3. **Outpatient payment methodology** — APC rates, fee schedule, percent of
   Medicare / billed charges, case rates.  Also extract OPPS-specific fields:
   opps_payment_rate, opps_wage_index, opps_labor_share, opps_sequestration_percent.

4. **Fee schedule / rate card** — every line item.  For each entry capture:
   code, code_type (CPT / HCPCS / DRG / APC / REVENUE / ICD10_PCS / ICD10_CM /
   MS_DRG / APR_DRG), description, dollar rate, rate_type (per_service /
   per_diem / per_case / per_unit / per_hour / flat), percent-of-Medicare,
   percent-of-Medicaid, percent-of-billed, modifier, place of service, revenue
   code, min/max amounts, effective/termination dates, any qualifying
   conditions.

5. **Percentage-based rules** — every rule that says "X% of [benchmark]".
   Capture benchmark (medicare / medicaid / billed_charges / drg_weight /
   apc_rate / fee_schedule / base_rate), the percentage, what services it
   applies to, any code ranges, and conditions.

6. **Stop-loss / outlier provisions** — thresholds, per-case or aggregate,
   what happens above threshold.

7. **Carve-outs** — services excluded from the standard methodology, how
   they're reimbursed instead, specific codes.

8. **Timely filing rules** — deadlines in days for initial claims, corrected
   claims, appeals, reconsiderations.  Calendar or business days.  Penalties.

9. **Payment timelines** — NET days, interest rates for late payment.

10. **Denial rules** — conditions that lead to denial or reduction, affected
    codes, appeal process.

11. **Escalator clauses** — annual increases (CPI, fixed %, Medicare update
    factor).

12. **Prior authorization requirements** — services that need pre-auth,
    penalty for missing auth (reduction %, denial).

13. **General payment rules** — any other payment-related clause.  Capture
    the verbatim or paraphrased text, category, amounts, percentages, codes,
    and conditions.

### Output format

Return valid JSON conforming to the ContractRuleLibrary schema.  Use `null` for
fields that are not mentioned in the contract.  Do NOT invent data.  If the
contract says "110% of Medicare", capture percent=110.0 and benchmark="medicare".
If a code is mentioned (e.g., CPT 99213), include it.  Be exhaustive — miss
nothing.  Every dollar amount, every percentage, every code, every deadline.

### Important rules
- Extract ALL codes mentioned: CPT, HCPCS, DRG, MS-DRG, APR-DRG, APC,
  Revenue codes, ICD-10-CM, ICD-10-PCS.
- Extract ALL percentages tied to specific conditions (e.g., "85% of Medicare
  for outpatient surgery").
- Extract ALL dollar amounts with their context.
- Capture tiered / graduated rates (e.g., "days 1-3: $2,500/day,
  days 4+: $1,800/day").
- Capture code ranges (e.g., "CPT 10021-69990 at 115% of Medicare").
- If the contract references an external fee schedule (e.g., "CMS OPPS fee
  schedule"), note that in conditions.
- Count total discrete rules extracted in rule_count.
"""


async def extract_rule_library_with_ai(
    contract_text: str,
    contract_name: str,
) -> Optional[Dict[str, Any]]:
    """
    Send the contract text to GPT and get back a structured rule library.
    Returns None if AI is unavailable or extraction fails.
    """
    if not contract_text or not contract_text.strip():
        return None

    # Truncate very long contracts to stay within token limits while
    # keeping as much content as possible.
    max_chars = 60_000  # ~15k tokens for GPT-4o
    text_for_ai = contract_text[:max_chars] if len(contract_text) > max_chars else contract_text

    user_prompt = f"""Extract the complete payment rule library from this contract.

CONTRACT NAME: {contract_name}

CONTRACT TEXT:
{text_for_ai}

Return a JSON object conforming to the ContractRuleLibrary schema.  Be exhaustive."""

    try:
        result = await chat_with_openai_async(
            text=user_prompt,
            prompt=_SYSTEM_PROMPT,
            model="gpt-4o-mini",
            schema=ContractRuleLibrary,
        )

        if not isinstance(result, dict) or not result:
            print(f"[RULE LIBRARY] AI returned empty result for {contract_name}", flush=True)
            return None

        print(
            f"[RULE LIBRARY] AI extraction succeeded for {contract_name}: "
            f"{result.get('rule_count', '?')} rules",
            flush=True,
        )
        return result

    except Exception as exc:
        print(f"[RULE LIBRARY] AI extraction failed for {contract_name}: {exc}", flush=True)
        return None


# ---------------------------------------------------------------------------
#  Deterministic (regex) fallback
# ---------------------------------------------------------------------------


def _find_all_codes(text: str) -> List[FeeScheduleEntry]:
    """Extract every recognizable billing code and any associated rate."""
    entries: List[FeeScheduleEntry] = []
    seen = set()

    # CPT / HCPCS
    for m in re.finditer(
        r"(?i)\b(?:CPT|HCPCS)\s*(?:code\s*)?[:#-]?\s*([A-Z]?\d{4,5}[A-Z]?)"
        r"(?:\s*(?:[-–]\s*|through\s+)([A-Z]?\d{4,5}[A-Z]?))?",
        text,
    ):
        code_start = m.group(1).upper()
        code_end = m.group(2).upper() if m.group(2) else None

        # Look for associated dollar amount within 80 chars
        context = text[m.start(): min(len(text), m.end() + 80)]
        rate_match = re.search(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)", context)
        rate = float(rate_match.group(1).replace(",", "")) if rate_match else None

        # Look for associated percentage
        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?(?:medicare|medicaid|billed|charges)?", context, re.I)
        pom = None
        if pct_match:
            pct_val = float(pct_match.group(1))
            context_lower = context.lower()
            if "medicaid" in context_lower:
                pom = None  # will go to percent_of_medicaid
            elif "billed" in context_lower or "charges" in context_lower:
                pass
            else:
                pom = pct_val  # default to percent_of_medicare

        code_type = "HCPCS" if code_start[0].isalpha() else "CPT"
        key = (code_start, code_type)
        if key not in seen:
            seen.add(key)
            entry = FeeScheduleEntry(
                code=code_start,
                code_type=code_type,
                rate=rate,
                rate_type="per_service",
                percent_of_medicare=pom,
                conditions=f"through {code_end}" if code_end else None,
            )
            entries.append(entry)

    # DRG / MS-DRG / APR-DRG
    for m in re.finditer(r"(?i)\b(?:MS[- ]?DRG|APR[- ]?DRG|DRG)\s*[:#-]?\s*(\d{1,4})", text):
        code = m.group(1)
        code_type = "MS_DRG" if "MS" in m.group(0).upper() else "APR_DRG" if "APR" in m.group(0).upper() else "DRG"
        context = text[m.start(): min(len(text), m.end() + 80)]
        rate_match = re.search(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)", context)
        rate = float(rate_match.group(1).replace(",", "")) if rate_match else None
        key = (code, code_type)
        if key not in seen:
            seen.add(key)
            entries.append(FeeScheduleEntry(code=code, code_type=code_type, rate=rate, rate_type="per_case"))

    # APC
    for m in re.finditer(r"(?i)\bAPC\s*[:#-]?\s*(\d{1,5})", text):
        code = m.group(1)
        context = text[m.start(): min(len(text), m.end() + 80)]
        rate_match = re.search(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)", context)
        rate = float(rate_match.group(1).replace(",", "")) if rate_match else None
        key = (code, "APC")
        if key not in seen:
            seen.add(key)
            entries.append(FeeScheduleEntry(code=code, code_type="APC", rate=rate, rate_type="per_service"))

    # Revenue codes
    for m in re.finditer(r"(?i)\b(?:revenue\s+code|rev(?:enue)?)\s*[:#-]?\s*(\d{3,4})", text):
        code = m.group(1)
        context = text[m.start(): min(len(text), m.end() + 80)]
        rate_match = re.search(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)", context)
        rate = float(rate_match.group(1).replace(",", "")) if rate_match else None
        key = (code, "REVENUE")
        if key not in seen:
            seen.add(key)
            entries.append(FeeScheduleEntry(code=code, code_type="REVENUE", rate=rate))

    # ICD-10
    for m in re.finditer(r"(?i)\bICD[- ]?10[- ]?(?:CM|PCS)?\s*[:#-]?\s*([A-Z]\d{2}(?:\.\d{1,4})?)", text):
        code = m.group(1).upper()
        code_type = "ICD10_PCS" if "PCS" in m.group(0).upper() else "ICD10_CM"
        key = (code, code_type)
        if key not in seen:
            seen.add(key)
            entries.append(FeeScheduleEntry(code=code, code_type=code_type))

    return entries


def _find_all_percentages(text: str) -> List[PercentageRule]:
    """Extract every percentage-of-benchmark rule."""
    rules: List[PercentageRule] = []
    seen = set()

    for m in re.finditer(
        r"(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?(?:the\s+)?"
        r"(medicare|medicaid|billed\s*charges?|charges?|drg\s*(?:weight|rate)?|apc\s*rate?|fee\s*schedule|base\s*rate|allowable)",
        text,
        re.IGNORECASE,
    ):
        pct = float(m.group(1))
        benchmark_raw = m.group(2).strip().lower()
        benchmark_map = {
            "medicare": "medicare",
            "medicaid": "medicaid",
            "billed charges": "billed_charges",
            "billed charge": "billed_charges",
            "charges": "billed_charges",
            "charge": "billed_charges",
            "drg weight": "drg_weight",
            "drg rate": "drg_weight",
            "drg": "drg_weight",
            "apc rate": "apc_rate",
            "apc": "apc_rate",
            "fee schedule": "fee_schedule",
            "base rate": "base_rate",
            "allowable": "medicare",
        }
        benchmark = benchmark_map.get(benchmark_raw, benchmark_raw)

        # Check surrounding context for service type
        context = text[max(0, m.start() - 100): min(len(text), m.end() + 100)].lower()
        applies_to = None
        for svc in ("inpatient", "outpatient", "emergency", "observation", "surgery", "radiology", "lab", "pharmacy"):
            if svc in context:
                applies_to = svc
                break

        key = (pct, benchmark, applies_to)
        if key not in seen:
            seen.add(key)
            rules.append(PercentageRule(benchmark=benchmark, percent=pct, applies_to=applies_to))

    return rules


def _find_per_diem_rates(text: str) -> List[PerDiemRate]:
    """Extract per-diem rate provisions."""
    rates: List[PerDiemRate] = []
    service_types = {
        "med/surg": "med_surg", "med surg": "med_surg", "medical/surgical": "med_surg",
        "icu": "icu", "intensive care": "icu", "critical care": "icu",
        "nicu": "nicu", "neonatal": "nicu",
        "rehab": "rehab", "rehabilitation": "rehab",
        "psych": "psych", "psychiatric": "psych", "behavioral": "psych",
        "snf": "snf", "skilled nursing": "snf",
        "ltac": "ltac", "long-term acute": "ltac", "long term acute": "ltac",
        "observation": "observation",
    }
    for m in re.finditer(
        r"(?i)\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)\s*(?:per\s+(?:day|diem)|/day|per-diem)",
        text,
    ):
        rate = float(m.group(1).replace(",", ""))
        context = text[max(0, m.start() - 120): min(len(text), m.end() + 60)].lower()
        svc_type = "med_surg"
        for keyword, mapped in service_types.items():
            if keyword in context:
                svc_type = mapped
                break
        rates.append(PerDiemRate(service_type=svc_type, rate=rate))

    return rates


def _find_timely_filing(text: str) -> List[TimelyFilingRule]:
    """Extract timely filing deadlines."""
    rules: List[TimelyFilingRule] = []
    for m in re.finditer(
        r"(?i)(?:timely\s+filing|claim\s+(?:submission|filing)|must\s+(?:be\s+)?(?:filed|submitted))"
        r".{0,80}?(\d{1,4})\s*(calendar|business)?\s*days?",
        text,
    ):
        days = int(m.group(1))
        dtype = m.group(2).lower() if m.group(2) else "calendar"
        rules.append(TimelyFilingRule(deadline_days=days, deadline_type=dtype))

    return rules


def _find_payment_timelines(text: str) -> List[PaymentTimeline]:
    """Extract NET payment terms."""
    timelines: List[PaymentTimeline] = []
    for m in re.finditer(r"(?i)\bnet\s+(\d+)\b", text):
        days = int(m.group(1))
        if 1 <= days <= 365:
            timelines.append(PaymentTimeline(days=days, timeline_type="net"))

    for m in re.finditer(
        r"(?i)(?:payment|reimbursement).{0,60}?(\d{1,3})\s*(?:calendar|business)?\s*days?",
        text,
    ):
        days = int(m.group(1))
        if 1 <= days <= 365:
            context = text[max(0, m.start()): min(len(text), m.end() + 40)].lower()
            ttype = "business" if "business" in context else "calendar"
            timelines.append(PaymentTimeline(days=days, timeline_type=ttype))

    return timelines


def _find_stop_loss(text: str) -> List[StopLossProvision]:
    """Extract stop-loss / outlier provisions."""
    provisions: List[StopLossProvision] = []
    for m in re.finditer(
        r"(?i)(?:stop[- ]?loss|outlier|high[- ]?cost).{0,100}?\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)",
        text,
    ):
        threshold = float(m.group(1).replace(",", ""))
        context = text[max(0, m.start()): min(len(text), m.end() + 100)].lower()
        ttype = "per_case"
        if "aggregate" in context or "annual" in context:
            ttype = "annual_aggregate"
        elif "per day" in context or "per diem" in context:
            ttype = "per_day"

        pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", context)
        pct = float(pct_match.group(1)) if pct_match else None
        provisions.append(StopLossProvision(
            threshold=threshold, threshold_type=ttype, percent_above_threshold=pct
        ))

    return provisions


def _find_general_payment_rules(text: str) -> List[GenericPaymentRule]:
    """Extract general payment clauses that contain dollar amounts or percentages."""
    rules: List[GenericPaymentRule] = []
    payment_keywords = (
        "reimburse", "payment", "compensat", "pay ", "paid ", "allowable",
        "fee ", "rate ", "capitation", "incentive", "bonus", "penalty",
        "withhold", "deduct",
    )
    for line in text.splitlines():
        stripped = line.strip()
        if len(stripped) < 20:
            continue
        lower = stripped.lower()
        if not any(kw in lower for kw in payment_keywords):
            continue
        # Must have a dollar amount or percentage
        has_money = bool(re.search(r"\$\s*\d|%", stripped))
        if not has_money:
            continue
        amounts = [float(a.replace(",", "")) for a in re.findall(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)", stripped)]
        pcts = [float(p) for p in re.findall(r"(\d+(?:\.\d+)?)\s*%", stripped)]
        codes = re.findall(r"(?i)(?:CPT|HCPCS|DRG|APC|revenue)\s*[:#-]?\s*([A-Z0-9]{3,6})", stripped)
        rules.append(GenericPaymentRule(
            rule_text=stripped[:500],
            category="payment",
            amounts=amounts or None,
            percentages=pcts or None,
            codes=[c.upper() for c in codes] or None,
        ))

    return rules


def _extract_metadata(text: str) -> Dict[str, Any]:
    """Pull contract metadata from the text."""
    meta: Dict[str, Any] = {}

    # Contract type
    lower = text.lower()
    if "medicare" in lower and "medicaid" not in lower:
        meta["contract_type"] = "medicare"
    elif "medicaid" in lower:
        meta["contract_type"] = "medicaid"
    elif any(term in lower for term in ("commercial", "ppo", "hmo", "epo")):
        meta["contract_type"] = "commercial"
    elif "managed care" in lower:
        meta["contract_type"] = "managed_care"

    # State
    state_match = re.search(r"(?i)\b(Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming)\b", text)
    if state_match:
        meta["state"] = state_match.group(1)

    # NPI
    npi_match = re.search(r"(?i)(?:NPI|National Provider Identifier)\s*[:#-]?\s*(\d{10})", text)
    if npi_match:
        meta["provider_npi"] = npi_match.group(1)

    # Effective date
    date_match = re.search(
        r"(?i)effective\s*(?:date)?\s*[:#-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})",
        text,
    )
    if date_match:
        meta["effective_date"] = date_match.group(1)

    # Payer name — look near "between" or "payer"
    payer_match = re.search(r"(?i)(?:between|payer|payor|insurer|plan)\s*[:#-]?\s*([A-Z][A-Za-z\s&.,]{3,60}?)(?:\s*(?:and|,|\n))", text)
    if payer_match:
        meta["payer_name"] = payer_match.group(1).strip()

    # Inpatient / outpatient methodology hints
    if re.search(r"(?i)(?:inpatient|IP)\s+.{0,50}?(?:per\s*diem|per day|/day)", text):
        meta["inpatient_method"] = "per_diem"
    elif re.search(r"(?i)(?:inpatient|IP|IPPS)\s+.{0,50}?DRG", text):
        meta["inpatient_method"] = "drg"

    if re.search(r"(?i)(?:outpatient|OP)\s+.{0,50}?APC", text):
        meta["outpatient_method"] = "apc"
    elif re.search(r"(?i)(?:outpatient|OP)\s+.{0,50}?fee\s*schedule", text):
        meta["outpatient_method"] = "fee_schedule"

    # Inpatient / outpatient percent of medicare
    for m in re.finditer(r"(?i)(?:inpatient|IP).{0,80}?(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?medicare", text):
        meta["inpatient_percent_of_medicare"] = float(m.group(1))
    for m in re.finditer(r"(?i)(?:outpatient|OP).{0,80}?(\d+(?:\.\d+)?)\s*%\s*(?:of\s+)?medicare", text):
        meta["outpatient_percent_of_medicare"] = float(m.group(1))

    # ── IPPS-specific fields ──
    # Operating base rate / standardized amount
    for m in re.finditer(
        r"(?i)(?:operating|standardized|base)\s*(?:amount|rate|payment)\s*[:#=]?\s*\$?\s*([0-9][0-9,]*(?:\.\d{1,2})?)",
        text,
    ):
        val = float(m.group(1).replace(",", ""))
        if val > 500:  # reasonable inpatient base rate
            meta["ipps_operating_base_rate"] = val
            meta.setdefault("inpatient_base_rate", val)
            break

    # Capital federal rate
    for m in re.finditer(
        r"(?i)capital\s*(?:federal\s*)?rate\s*[:#=]?\s*\$?\s*([0-9][0-9,]*(?:\.\d{1,2})?)",
        text,
    ):
        meta["ipps_capital_federal_rate"] = float(m.group(1).replace(",", ""))
        break

    # Capital GAF
    for m in re.finditer(r"(?i)(?:capital\s+)?(?:GAF|geographic\s+adjustment\s+factor)\s*[:#=]?\s*([01]\.\d{2,4})", text):
        meta["ipps_capital_gaf"] = float(m.group(1))
        break

    # DSH %
    for m in re.finditer(r"(?i)DSH\s*[:(=]?\s*(\d+(?:\.\d+)?)\s*%", text):
        meta["ipps_dsh_percent"] = float(m.group(1))
        break

    # IME %
    for m in re.finditer(r"(?i)IME\s*[:(=]?\s*(\d+(?:\.\d+)?)\s*%", text):
        meta["ipps_ime_percent"] = float(m.group(1))
        break

    # Sequestration
    for m in re.finditer(r"(?i)sequest(?:er|ration)\s*[:(=]?\s*(\d+(?:\.\d+)?)\s*%", text):
        meta["ipps_sequestration_percent"] = float(m.group(1))
        break

    # Cost-to-charge ratio
    for m in re.finditer(r"(?i)(?:cost[- ]?to[- ]?charge|CCR)\s*(?:ratio)?\s*[:#=]?\s*([01]?\.\d{2,4})", text):
        meta["ipps_cost_to_charge_ratio"] = float(m.group(1))
        break

    # Outlier threshold
    for m in re.finditer(
        r"(?i)(?:outlier|fixed[- ]?loss)\s*(?:threshold|amount)?\s*[:#=]?\s*\$?\s*([0-9][0-9,]*(?:\.\d{1,2})?)",
        text,
    ):
        val = float(m.group(1).replace(",", ""))
        if val > 100:  # reasonable outlier threshold
            meta["ipps_outlier_fixed_loss_threshold"] = val
            break

    # Wage index
    for m in re.finditer(r"(?i)wage\s+index\s*[:#=]?\s*([0-9]\.\d{2,4})", text):
        meta["ipps_wage_index"] = float(m.group(1))
        break

    # If we found IPPS fields, mark as IPPS method
    if any(meta.get(k) for k in ("ipps_operating_base_rate", "ipps_dsh_percent", "ipps_ime_percent")):
        meta["inpatient_method"] = "ipps"

    return meta


def build_rule_library_deterministic(contract_text: str, contract_name: str) -> Dict[str, Any]:
    """
    Build a rule library using only regex / deterministic extraction.
    Used as a fallback when AI is unavailable, or merged with AI output.
    """
    if not contract_text or not contract_text.strip():
        return ContractRuleLibrary(extraction_notes="No contract text available", rule_count=0).model_dump()

    metadata = _extract_metadata(contract_text)
    fee_schedule = _find_all_codes(contract_text)
    percentage_rules = _find_all_percentages(contract_text)
    per_diem_rates = _find_per_diem_rates(contract_text)
    timely_filing = _find_timely_filing(contract_text)
    payment_timelines = _find_payment_timelines(contract_text)
    stop_loss = _find_stop_loss(contract_text)
    general_rules = _find_general_payment_rules(contract_text)

    rule_count = (
        len(fee_schedule)
        + len(percentage_rules)
        + len(per_diem_rates)
        + len(timely_filing)
        + len(payment_timelines)
        + len(stop_loss)
        + len(general_rules)
    )

    library = ContractRuleLibrary(
        **metadata,
        fee_schedule=fee_schedule or None,
        percentage_rules=percentage_rules or None,
        per_diem_rates=per_diem_rates or None,
        timely_filing_rules=timely_filing or None,
        payment_timelines=payment_timelines or None,
        stop_loss_provisions=stop_loss or None,
        general_payment_rules=general_rules or None,
        extraction_notes=f"Deterministic extraction at {datetime.utcnow().isoformat()}",
        rule_count=rule_count,
    )

    return library.model_dump()


def merge_libraries(ai_library: Dict[str, Any], det_library: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge AI and deterministic libraries.  AI takes priority but deterministic
    fills in gaps and adds codes/rules AI may have missed.
    """
    merged = dict(ai_library)

    # For list fields, combine and deduplicate
    list_fields = [
        "fee_schedule", "percentage_rules", "per_diem_rates", "case_rates",
        "stop_loss_provisions", "carve_outs", "timely_filing_rules",
        "payment_timelines", "denial_rules", "escalator_clauses",
        "auth_requirements", "general_payment_rules",
    ]

    for field in list_fields:
        ai_items = ai_library.get(field) or []
        det_items = det_library.get(field) or []
        if not ai_items and det_items:
            merged[field] = det_items
        elif ai_items and det_items:
            # Keep AI items, add deterministic items that aren't duplicates
            ai_codes = set()
            for item in ai_items:
                if isinstance(item, dict) and item.get("code"):
                    ai_codes.add(item["code"])
            for item in det_items:
                if isinstance(item, dict) and item.get("code") and item["code"] not in ai_codes:
                    ai_items.append(item)
            merged[field] = ai_items

    # For scalar fields, prefer AI but fill nulls from deterministic
    scalar_fields = [
        "contract_type", "payer_name", "plan_name", "effective_date",
        "termination_date", "state", "provider_npi", "provider_tax_id",
        "inpatient_base_rate", "inpatient_method", "inpatient_percent_of_medicare",
        "inpatient_percent_of_charges", "outpatient_base_rate", "outpatient_method",
        "outpatient_percent_of_medicare", "outpatient_percent_of_charges",
        # IPPS fields
        "ipps_operating_base_rate", "ipps_capital_federal_rate", "ipps_capital_gaf",
        "ipps_capital_dsh_percent", "ipps_capital_ime_percent", "ipps_capital_outlier_percent",
        "ipps_dsh_percent", "ipps_ime_percent", "ipps_wage_index", "ipps_labor_share",
        "ipps_cost_to_charge_ratio", "ipps_outlier_fixed_loss_threshold",
        "ipps_outlier_marginal_cost_factor", "ipps_sequestration_percent",
        # OPPS fields
        "opps_payment_rate", "opps_wage_index", "opps_labor_share",
        "opps_sequestration_percent",
    ]
    for field in scalar_fields:
        if merged.get(field) is None and det_library.get(field) is not None:
            merged[field] = det_library[field]

    # Recount
    total = 0
    for field in list_fields:
        items = merged.get(field)
        if items:
            total += len(items)
    merged["rule_count"] = total
    merged["extraction_notes"] = (
        f"AI + deterministic merge at {datetime.utcnow().isoformat()}. "
        f"AI: {ai_library.get('rule_count', 0)} rules, "
        f"Deterministic: {det_library.get('rule_count', 0)} rules, "
        f"Merged: {total} rules."
    )

    return merged


async def extract_rule_library(
    contract_text: str,
    contract_name: str,
) -> Dict[str, Any]:
    """
    Main entry point: extract the complete rule library from contract text.
    Uses AI when available, always runs deterministic as supplement/fallback.
    """
    # Always run deterministic extraction
    det_library = build_rule_library_deterministic(contract_text, contract_name)

    # Try AI extraction
    ai_library = await extract_rule_library_with_ai(contract_text, contract_name)

    if ai_library:
        # Merge: AI primary, deterministic fills gaps
        return merge_libraries(ai_library, det_library)
    else:
        print(f"[RULE LIBRARY] Using deterministic-only for {contract_name}", flush=True)
        return det_library

"""
Exhaustive payment rule library schema.

This defines every category of data that must be extracted from a hospital
contract so that billing records can be verified for correctness.
The AI extraction prompt and the deterministic regex engine both produce
output that conforms to this schema.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Individual rule entries ──────────────────────────────────────────────────


class DayRange(BaseModel):
    """A single tier in a per-diem day-range schedule."""
    days: str = Field(description="Day range, e.g. '1-3', '4-10', '11+'")
    rate: float = Field(description="Dollar rate for this day range")


class FeeScheduleEntry(BaseModel):
    """A single line in a fee schedule / rate card."""
    code: str = Field(description="CPT, HCPCS, DRG, APC, Revenue, or ICD code")
    code_type: str = Field(description="Code system: CPT, HCPCS, DRG, APC, REVENUE, ICD10_PCS, ICD10_CM, MS_DRG, APR_DRG")
    description: Optional[str] = Field(default=None, description="Human-readable procedure/service description")
    rate: Optional[float] = Field(default=None, description="Fixed dollar amount for this code")
    rate_type: Optional[str] = Field(default=None, description="per_service | per_diem | per_case | per_unit | per_hour | flat")
    percent_of_medicare: Optional[float] = Field(default=None, description="Percentage of Medicare allowable, e.g. 110.0 means 110%")
    percent_of_medicaid: Optional[float] = Field(default=None, description="Percentage of Medicaid fee schedule")
    percent_of_billed: Optional[float] = Field(default=None, description="Percentage of billed charges")
    modifier: Optional[str] = Field(default=None, description="Modifier code (e.g., 25, 59, TC, 26)")
    place_of_service: Optional[str] = Field(default=None, description="POS code (e.g., 11, 21, 22, 23)")
    revenue_code: Optional[str] = Field(default=None, description="Revenue code if separate from primary code")
    min_amount: Optional[float] = Field(default=None, description="Floor / minimum payment")
    max_amount: Optional[float] = Field(default=None, description="Ceiling / maximum payment / stop-loss threshold")
    effective_date: Optional[str] = Field(default=None, description="Date this rate becomes effective (YYYY-MM-DD)")
    termination_date: Optional[str] = Field(default=None, description="Date this rate expires (YYYY-MM-DD)")
    conditions: Optional[str] = Field(default=None, description="Any qualifying conditions or notes")


class PercentageRule(BaseModel):
    """A percentage-based reimbursement rule tied to a benchmark."""
    benchmark: str = Field(description="What the % is of: medicare | medicaid | billed_charges | drg_weight | apc_rate | fee_schedule | base_rate")
    percent: float = Field(description="The percentage value, e.g. 85.0 for 85%")
    applies_to: Optional[str] = Field(default=None, description="What services this applies to: inpatient | outpatient | all | emergency | observation | etc.")
    service_category: Optional[str] = Field(default=None, description="Specific service category: surgery, radiology, lab, pharmacy, etc.")
    code_range_start: Optional[str] = Field(default=None, description="Start of code range this applies to")
    code_range_end: Optional[str] = Field(default=None, description="End of code range this applies to")
    conditions: Optional[str] = Field(default=None, description="Qualifying conditions")


class PerDiemRate(BaseModel):
    """Per-diem reimbursement rule for inpatient stays."""
    service_type: str = Field(description="med_surg | icu | nicu | rehab | psych | snf | ltac | observation | etc.")
    rate: float = Field(description="Dollar amount per day")
    max_days: Optional[int] = Field(default=None, description="Maximum covered days")
    day_ranges: Optional[List[DayRange]] = Field(default=None, description="Tiered per-diem rates, e.g. days 1-3 at $2500, days 4+ at $1800")
    conditions: Optional[str] = Field(default=None)


class CaseRate(BaseModel):
    """Case rate / bundled payment for a procedure or DRG."""
    code: Optional[str] = Field(default=None, description="DRG, MS-DRG, APR-DRG, APC, or procedure code")
    code_type: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    rate: float = Field(description="Total case rate amount")
    includes: Optional[str] = Field(default=None, description="What the case rate covers")
    excludes: Optional[str] = Field(default=None, description="Carved-out services not included")
    conditions: Optional[str] = Field(default=None)


class StopLossProvision(BaseModel):
    """Outlier / stop-loss / high-cost threshold provisions."""
    threshold: float = Field(description="Dollar threshold that triggers stop-loss")
    threshold_type: str = Field(description="per_case | per_day | annual_aggregate | per_claim")
    reimbursement_above_threshold: Optional[str] = Field(default=None, description="How amounts above threshold are paid, e.g. '80% of charges above threshold'")
    percent_above_threshold: Optional[float] = Field(default=None, description="Percentage paid above threshold")
    conditions: Optional[str] = Field(default=None)


class CarveOut(BaseModel):
    """Services carved out from the standard reimbursement methodology."""
    service: str = Field(description="Description of carved-out service")
    codes: Optional[List[str]] = Field(default=None, description="Specific codes carved out")
    reimbursement_method: Optional[str] = Field(default=None, description="How the carve-out is reimbursed")
    rate: Optional[float] = Field(default=None)
    percent: Optional[float] = Field(default=None)
    conditions: Optional[str] = Field(default=None)


class TimelyFilingRule(BaseModel):
    """Timely filing / claim submission deadlines."""
    deadline_days: int = Field(description="Number of days from date of service")
    deadline_type: str = Field(description="calendar | business")
    applies_to: Optional[str] = Field(default=None, description="initial_claim | corrected_claim | appeal | reconsideration")
    penalty: Optional[str] = Field(default=None, description="What happens if deadline is missed")


class PaymentTimeline(BaseModel):
    """Payment timing / prompt-pay rules."""
    days: int = Field(description="Number of days for payment (e.g., NET 30)")
    timeline_type: str = Field(description="net | calendar | business | from_clean_claim | from_receipt")
    interest_rate: Optional[float] = Field(default=None, description="Interest rate for late payment (%)")
    penalty_description: Optional[str] = Field(default=None)


class DenialRule(BaseModel):
    """Conditions under which claims can be denied or reduced."""
    reason: str = Field(description="Denial reason")
    codes_affected: Optional[List[str]] = Field(default=None)
    recovery_method: Optional[str] = Field(default=None, description="How to appeal or recover")
    conditions: Optional[str] = Field(default=None)


class EscalatorClause(BaseModel):
    """Annual rate increases / escalators."""
    escalator_type: str = Field(description="cpi | fixed_percent | negotiated | medicare_update")
    percent: Optional[float] = Field(default=None, description="Annual increase percentage")
    effective_date: Optional[str] = Field(default=None)
    conditions: Optional[str] = Field(default=None)


class AuthRequirement(BaseModel):
    """Prior authorization / pre-certification requirements."""
    service: str = Field(description="Service requiring authorization")
    codes: Optional[List[str]] = Field(default=None)
    penalty_for_no_auth: Optional[str] = Field(default=None, description="Reduction or denial if no auth obtained")
    reduction_percent: Optional[float] = Field(default=None, description="Percentage reduction without auth")
    conditions: Optional[str] = Field(default=None)


class GenericPaymentRule(BaseModel):
    """Catch-all for any payment rule that doesn't fit the above categories."""
    rule_text: str = Field(description="Verbatim or paraphrased rule from contract")
    category: Optional[str] = Field(default=None, description="payment | penalty | compliance | audit | documentation | other")
    amounts: Optional[List[float]] = Field(default=None)
    percentages: Optional[List[float]] = Field(default=None)
    codes: Optional[List[str]] = Field(default=None)
    conditions: Optional[str] = Field(default=None)


# ── Top-level rule library ───────────────────────────────────────────────────


class ContractRuleLibrary(BaseModel):
    """
    The complete, exhaustive payment rule library extracted from a single
    hospital contract.  Every data point needed to verify whether an invoice
    was paid correctly lives here.
    """

    # ── Metadata ──
    contract_type: Optional[str] = Field(default=None, description="medicare | medicaid | commercial | managed_care | workers_comp | tricare | va | other")
    payer_name: Optional[str] = Field(default=None, description="Name of the payer / insurance company")
    plan_name: Optional[str] = Field(default=None, description="Specific plan name if applicable")
    effective_date: Optional[str] = Field(default=None, description="Contract effective date (YYYY-MM-DD)")
    termination_date: Optional[str] = Field(default=None, description="Contract end date (YYYY-MM-DD)")
    auto_renew: Optional[bool] = Field(default=None)
    state: Optional[str] = Field(default=None, description="State jurisdiction (e.g. TX, CA)")
    provider_npi: Optional[str] = Field(default=None)
    provider_tax_id: Optional[str] = Field(default=None)

    # ── Inpatient rules ──
    inpatient_base_rate: Optional[float] = Field(default=None, description="Base DRG or per-diem rate for inpatient (operating standardized amount)")
    inpatient_method: Optional[str] = Field(default=None, description="drg | per_diem | case_rate | percent_of_charges | percent_of_medicare | ipps")
    inpatient_percent_of_medicare: Optional[float] = Field(default=None)
    inpatient_percent_of_charges: Optional[float] = Field(default=None)
    per_diem_rates: Optional[List[PerDiemRate]] = Field(default=None)
    case_rates: Optional[List[CaseRate]] = Field(default=None)

    # ── IPPS (Inpatient Prospective Payment System) fields ──
    ipps_operating_base_rate: Optional[float] = Field(default=None, description="Operating standardized amount, e.g. $6,730.32")
    ipps_capital_federal_rate: Optional[float] = Field(default=None, description="Capital Federal Rate, e.g. $524.15")
    ipps_capital_gaf: Optional[float] = Field(default=None, description="Capital Geographic Adjustment Factor, e.g. 0.9980")
    ipps_capital_dsh_percent: Optional[float] = Field(default=None, description="Capital DSH adjustment percentage")
    ipps_capital_ime_percent: Optional[float] = Field(default=None, description="Capital IME adjustment percentage")
    ipps_capital_outlier_percent: Optional[float] = Field(default=None, description="Capital outlier adjustment percentage, e.g. 8.0 for 8%")
    ipps_dsh_percent: Optional[float] = Field(default=None, description="Operating Disproportionate Share Hospital (DSH) percentage, e.g. 5.28")
    ipps_ime_percent: Optional[float] = Field(default=None, description="Operating Indirect Medical Education (IME) percentage, e.g. 5.41")
    ipps_wage_index: Optional[float] = Field(default=None, description="Area Wage Index for labor-related adjustments")
    ipps_labor_share: Optional[float] = Field(default=None, description="Labor-related share of the base rate (default ~0.6860)")
    ipps_cost_to_charge_ratio: Optional[float] = Field(default=None, description="Hospital cost-to-charge ratio (CCR) for outlier calculation")
    ipps_outlier_fixed_loss_threshold: Optional[float] = Field(default=None, description="Fixed-loss cost threshold for outliers")
    ipps_outlier_marginal_cost_factor: Optional[float] = Field(default=None, description="Marginal cost factor for outliers (typically 0.80)")
    ipps_sequestration_percent: Optional[float] = Field(default=None, description="Medicare sequestration reduction, e.g. 2.0 for 2%")
    ipps_new_tech_add_on_payments: Optional[List[str]] = Field(default=None, description="New technology add-on payment descriptions (free text)")

    # ── Outpatient rules ──
    outpatient_base_rate: Optional[float] = Field(default=None)
    outpatient_method: Optional[str] = Field(default=None, description="apc | fee_schedule | percent_of_charges | percent_of_medicare | case_rate")
    outpatient_percent_of_medicare: Optional[float] = Field(default=None)
    outpatient_percent_of_charges: Optional[float] = Field(default=None)

    # ── OPPS (Outpatient Prospective Payment System) fields ──
    opps_payment_rate: Optional[float] = Field(default=None, description="Outpatient payment rate / APC base rate")
    opps_wage_index: Optional[float] = Field(default=None, description="Outpatient area wage index")
    opps_labor_share: Optional[float] = Field(default=None, description="Outpatient labor-related share")
    opps_sequestration_percent: Optional[float] = Field(default=None, description="Outpatient sequestration reduction")

    # ── Fee schedules / rate cards ──
    fee_schedule: Optional[List[FeeScheduleEntry]] = Field(default=None, description="Itemized fee schedule entries")

    # ── Percentage-based rules ──
    percentage_rules: Optional[List[PercentageRule]] = Field(default=None)

    # ── Stop-loss / outlier provisions ──
    stop_loss_provisions: Optional[List[StopLossProvision]] = Field(default=None)

    # ── Carve-outs ──
    carve_outs: Optional[List[CarveOut]] = Field(default=None)

    # ── Timely filing ──
    timely_filing_rules: Optional[List[TimelyFilingRule]] = Field(default=None)

    # ── Payment timelines ──
    payment_timelines: Optional[List[PaymentTimeline]] = Field(default=None)

    # ── Denial rules ──
    denial_rules: Optional[List[DenialRule]] = Field(default=None)

    # ── Escalators / annual increases ──
    escalator_clauses: Optional[List[EscalatorClause]] = Field(default=None)

    # ── Auth requirements ──
    auth_requirements: Optional[List[AuthRequirement]] = Field(default=None)

    # ── Catch-all payment rules ──
    general_payment_rules: Optional[List[GenericPaymentRule]] = Field(default=None, description="All other payment-related rules")

    # ── Summary ──
    extraction_notes: Optional[str] = Field(default=None, description="Any notes about the extraction process")
    rule_count: Optional[int] = Field(default=None, description="Total number of discrete rules extracted")

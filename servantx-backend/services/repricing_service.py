from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    LocalityOverride,
    LocalityOverrideEntityType,
    MedicareConversionFactor,
    MedicareGpci,
    MedicareRvuRate,
    MedicareZipLocality,
    TxMedicaidFfsFeeSchedule,
)
from services.pipeline_config_service import (
    get_locality_resolution_rules,
    get_pos_facility_map,
    get_thresholds_config,
)


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _get_units(line: Dict[str, Any]) -> float:
    units = _to_float(line.get("units"), default=1.0)
    return units if units > 0 else 0.0


def compute_medicare_expected_allowed(
    work_rvu: float,
    pe_rvu: float,
    mp_rvu: float,
    work_gpci: float,
    pe_gpci: float,
    mp_gpci: float,
    conversion_factor: float,
    units: float,
) -> float:
    work_component = work_rvu * work_gpci
    pe_component = pe_rvu * pe_gpci
    mp_component = mp_rvu * mp_gpci
    return (work_component + pe_component + mp_component) * conversion_factor * units


def compute_tx_medicaid_expected_allowed(allowed_amount: float, units: float) -> float:
    return allowed_amount * units


def _is_facility_pos(pos: Optional[str]) -> bool:
    config = get_pos_facility_map()
    facility_codes = set(config.get("facility_pos_codes", []))
    return (pos or "") in facility_codes


async def resolve_locality(
    db: AsyncSession,
    provider: Dict[str, Any],
) -> Dict[str, Any]:
    rules = get_locality_resolution_rules()
    override_priority = rules.get("override_priority", ["FACILITY_NPI", "RENDERING_NPI", "BILLING_NPI"])

    entity_values = {
        "FACILITY_NPI": provider.get("facility_npi"),
        "RENDERING_NPI": provider.get("rendering_provider_npi"),
        "BILLING_NPI": provider.get("billing_provider_npi"),
        "TAX_ID": provider.get("tax_id"),
    }

    for entity_type_key in override_priority:
        entity_id = entity_values.get(entity_type_key)
        if not entity_id:
            continue
        try:
            entity_type = LocalityOverrideEntityType[entity_type_key]
        except KeyError:
            continue

        override_result = await db.execute(
            select(LocalityOverride).where(
                LocalityOverride.entity_type == entity_type,
                LocalityOverride.entity_id == entity_id,
            )
        )
        override = override_result.scalars().first()
        if override:
            return {
                "locality_code": override.locality_code,
                "locality_source": "OVERRIDE",
                "locality_confidence": override.confidence,
                "zip_used": override.zip_code,
            }

    service_zip = ((provider.get("service_location") or {}).get("zip") or "")[:5]
    billing_zip = ((provider.get("billing_location") or {}).get("zip") or "")[:5]

    for zip_value, source in [(service_zip, "SERVICE_ZIP"), (billing_zip, "BILLING_ZIP")]:
        if not zip_value:
            continue
        locality_result = await db.execute(
            select(MedicareZipLocality).where(MedicareZipLocality.zip_code == zip_value)
        )
        locality = locality_result.scalars().first()
        if locality:
            return {
                "locality_code": locality.locality_code,
                "locality_source": source,
                "locality_confidence": 90 if source == "SERVICE_ZIP" else 80,
                "zip_used": zip_value,
            }

    return {
        "locality_code": None,
        "locality_source": "UNKNOWN",
        "locality_confidence": int(rules.get("unknown_confidence", 25)),
        "zip_used": None,
    }


async def _get_medicare_rvu_rows(db: AsyncSession, year: int, cpt_hcpcs: str) -> List[MedicareRvuRate]:
    result = await db.execute(
        select(MedicareRvuRate).where(
            MedicareRvuRate.year == year,
            MedicareRvuRate.cpt_hcpcs == cpt_hcpcs,
        )
    )
    return list(result.scalars().all())


async def _get_medicare_gpci(db: AsyncSession, year: int, locality_code: str) -> Optional[MedicareGpci]:
    result = await db.execute(
        select(MedicareGpci).where(
            MedicareGpci.year == year,
            MedicareGpci.locality_code == locality_code,
        )
    )
    return result.scalars().first()


async def _get_medicare_cf(db: AsyncSession, year: int) -> Optional[MedicareConversionFactor]:
    result = await db.execute(
        select(MedicareConversionFactor).where(MedicareConversionFactor.year == year)
    )
    return result.scalars().first()


async def reprice_medicare_line(
    db: AsyncSession,
    line: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    units = _get_units(line)
    if units <= 0:
        return {"errors": ["INVALID_UNITS"], "expected_allowed": None, "confidence_score": 10.0}

    line_dos = _parse_date(line.get("line_service_date")) or _parse_date(context.get("service_date_start"))
    if not line_dos:
        return {"errors": ["MISSING_DOS", "RATE_YEAR_MISSING"], "expected_allowed": None, "confidence_score": 15.0}

    cpt = line.get("cpt_hcpcs")
    if not cpt:
        return {"errors": ["MISSING_RATE_MATCH"], "expected_allowed": None, "confidence_score": 10.0}

    year = line_dos.year
    rvu_rows = await _get_medicare_rvu_rows(db, year=year, cpt_hcpcs=cpt)
    if not rvu_rows:
        return {"errors": ["MISSING_RATE_MATCH"], "expected_allowed": None, "confidence_score": 20.0}

    ambiguous = len(rvu_rows) > 1
    rvu_row = rvu_rows[0]

    locality = await resolve_locality(db=db, provider=context.get("provider") or {})
    locality_code = locality.get("locality_code")
    if not locality_code:
        return {
            "errors": ["LOCALITY_UNKNOWN"],
            "expected_allowed": None,
            "locality_code": None,
            "locality_source": locality.get("locality_source"),
            "confidence_score": float(locality.get("locality_confidence", 25)),
        }

    gpci = await _get_medicare_gpci(db=db, year=year, locality_code=locality_code)
    cf = await _get_medicare_cf(db=db, year=year)
    if not gpci or not cf:
        return {
            "errors": ["MISSING_RATE_MATCH"],
            "expected_allowed": None,
            "locality_code": locality_code,
            "locality_source": locality.get("locality_source"),
            "confidence_score": float(locality.get("locality_confidence", 40)),
        }

    facility = _is_facility_pos(line.get("place_of_service"))
    pe_rvu = rvu_row.pe_rvu_facility if facility else rvu_row.pe_rvu_nonfacility

    expected_allowed = compute_medicare_expected_allowed(
        work_rvu=_to_float(rvu_row.work_rvu),
        pe_rvu=_to_float(pe_rvu),
        mp_rvu=_to_float(rvu_row.mp_rvu),
        work_gpci=_to_float(gpci.work_gpci),
        pe_gpci=_to_float(gpci.pe_gpci),
        mp_gpci=_to_float(gpci.mp_gpci),
        conversion_factor=_to_float(cf.conversion_factor),
        units=units,
    )

    actual_paid = _to_float(line.get("line_payment_amount"), default=0.0)
    variance = expected_allowed - actual_paid
    variance_percent = (variance / expected_allowed * 100.0) if expected_allowed else 0.0

    errors: List[str] = []
    if ambiguous:
        errors.append("AMBIGUOUS_RATE_MATCH")
    if not line.get("place_of_service"):
        errors.append("MISSING_POS")

    return {
        "errors": errors,
        "expected_allowed": round(expected_allowed, 2),
        "actual_paid": round(actual_paid, 2),
        "variance_amount": round(variance, 2),
        "variance_percent": round(variance_percent, 2),
        "rate_source": f"MPFS_{year}+GPCI_{locality_code}",
        "locality_code": locality_code,
        "locality_source": locality.get("locality_source"),
        "confidence_score": min(100.0, float(locality.get("locality_confidence", 70)) + (0 if ambiguous else 5)),
    }


async def reprice_tx_medicaid_line(
    db: AsyncSession,
    line: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    units = _get_units(line)
    if units <= 0:
        return {"errors": ["INVALID_UNITS"], "expected_allowed": None, "confidence_score": 10.0}

    dos = _parse_date(line.get("line_service_date")) or _parse_date(context.get("service_date_start"))
    if not dos:
        return {"errors": ["MISSING_DOS"], "expected_allowed": None, "confidence_score": 15.0}

    cpt = line.get("cpt_hcpcs")
    if not cpt:
        return {"errors": ["MISSING_RATE_MATCH"], "expected_allowed": None, "confidence_score": 15.0}

    modifiers = [modifier for modifier in line.get("modifiers", []) if modifier]
    modifier = modifiers[0] if modifiers else None

    base_query = select(TxMedicaidFfsFeeSchedule).where(
        TxMedicaidFfsFeeSchedule.cpt_hcpcs == cpt,
        TxMedicaidFfsFeeSchedule.effective_start <= dos,
        or_(
            TxMedicaidFfsFeeSchedule.effective_end.is_(None),
            TxMedicaidFfsFeeSchedule.effective_end >= dos,
        ),
    )

    selected_rows: List[TxMedicaidFfsFeeSchedule] = []
    if modifier:
        modifier_result = await db.execute(
            base_query.where(TxMedicaidFfsFeeSchedule.modifier == modifier)
        )
        selected_rows = list(modifier_result.scalars().all())

    if not selected_rows:
        fallback_result = await db.execute(
            base_query.where(TxMedicaidFfsFeeSchedule.modifier.is_(None))
        )
        selected_rows = list(fallback_result.scalars().all())

    if not selected_rows:
        return {"errors": ["MISSING_RATE_MATCH"], "expected_allowed": None, "confidence_score": 25.0}

    ambiguous = len(selected_rows) > 1
    fee_row = selected_rows[0]

    expected_allowed = compute_tx_medicaid_expected_allowed(_to_float(fee_row.allowed_amount), units)
    actual_paid = _to_float(line.get("line_payment_amount"), default=0.0)
    variance = expected_allowed - actual_paid
    variance_percent = (variance / expected_allowed * 100.0) if expected_allowed else 0.0

    errors: List[str] = []
    if ambiguous:
        errors.append("AMBIGUOUS_RATE_MATCH")
    if not line.get("place_of_service"):
        errors.append("MISSING_POS")

    return {
        "errors": errors,
        "expected_allowed": round(expected_allowed, 2),
        "actual_paid": round(actual_paid, 2),
        "variance_amount": round(variance, 2),
        "variance_percent": round(variance_percent, 2),
        "rate_source": "TX_MEDICAID_FFS_FEE_SCHEDULE",
        "locality_code": None,
        "locality_source": "N/A",
        "confidence_score": 85.0 if not ambiguous else 70.0,
    }


def severity_from_variance(variance_amount: float) -> str:
    thresholds = get_thresholds_config().get("severity_thresholds", {})
    critical = float(thresholds.get("critical", 500.0))
    high = float(thresholds.get("high", 50.0))
    medium = float(thresholds.get("medium", 10.0))
    abs_value = abs(variance_amount)
    if abs_value >= critical:
        return "CRITICAL"
    if abs_value >= high:
        return "HIGH"
    if abs_value >= medium:
        return "MEDIUM"
    return "LOW"


def build_line_findings(line: Dict[str, Any], repricing_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    thresholds = get_thresholds_config()
    amount_threshold = float(thresholds.get("underpayment_amount_threshold", 5.0))
    percent_threshold = float(thresholds.get("underpayment_percent_threshold", 3.0))
    allowed_drift_threshold = float(thresholds.get("allowed_drift_threshold", 2.0))

    findings: List[Dict[str, Any]] = []
    errors = repricing_result.get("errors", [])
    variance_amount = _to_float(repricing_result.get("variance_amount"), default=0.0)
    variance_percent = _to_float(repricing_result.get("variance_percent"), default=0.0)
    expected_allowed = repricing_result.get("expected_allowed")
    actual_paid = _to_float(repricing_result.get("actual_paid"), default=0.0)
    confidence = _to_float(repricing_result.get("confidence_score"), default=0.0)

    for error_code in errors:
        findings.append(
            {
                "finding_code": error_code,
                "severity": "MEDIUM" if error_code not in ("INVALID_UNITS", "MISSING_DOS") else "LOW",
                "variance_amount": variance_amount if expected_allowed is not None else None,
                "confidence_score": confidence,
            }
        )

    if expected_allowed is not None:
        line_allowed_amount = _to_float(line.get("line_allowed_amount"), default=0.0)
        if line_allowed_amount > 0 and abs(_to_float(expected_allowed) - line_allowed_amount) > allowed_drift_threshold:
            findings.append(
                {
                    "finding_code": "ALLOWED_MISMATCH",
                    "severity": "MEDIUM",
                    "variance_amount": variance_amount,
                    "confidence_score": confidence,
                }
            )

        if actual_paid > _to_float(expected_allowed):
            findings.append(
                {
                    "finding_code": "PAID_GT_ALLOWED",
                    "severity": "LOW",
                    "variance_amount": variance_amount,
                    "confidence_score": confidence,
                }
            )

        if actual_paid == 0 and _to_float(expected_allowed) > 0:
            findings.append(
                {
                    "finding_code": "ZERO_PAY_POTENTIAL_UNDERPAYMENT",
                    "severity": severity_from_variance(_to_float(expected_allowed)),
                    "variance_amount": _to_float(expected_allowed),
                    "confidence_score": confidence,
                }
            )

        if variance_amount > 0 and (variance_amount > amount_threshold or variance_percent > percent_threshold):
            findings.append(
                {
                    "finding_code": "UNDERPAYMENT_CONFIRMED",
                    "severity": severity_from_variance(variance_amount),
                    "variance_amount": variance_amount,
                    "confidence_score": confidence,
                }
            )
        elif variance_amount > 0:
            findings.append(
                {
                    "finding_code": "UNDERPAYMENT_POSSIBLE",
                    "severity": "LOW",
                    "variance_amount": variance_amount,
                    "confidence_score": confidence,
                }
            )

        if variance_amount > amount_threshold and not line.get("adjustments"):
            findings.append(
                {
                    "finding_code": "UNEXPECTED_ADJUSTMENT_PATTERN",
                    "severity": "LOW",
                    "variance_amount": variance_amount,
                    "confidence_score": confidence,
                }
            )

    return findings

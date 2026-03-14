import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict


CONFIG_DIR = Path(__file__).resolve().parent.parent / "pipeline_configs"


def _read_json(filename: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    path = CONFIG_DIR / filename
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


@lru_cache(maxsize=1)
def get_pos_facility_map() -> Dict[str, Any]:
    return _read_json(
        "pos_facility_map.json",
        {
            "facility_pos_codes": ["19", "21", "22", "23", "24", "26", "31", "32", "51", "52", "61"],
            "default": "nonfacility",
        },
    )


@lru_cache(maxsize=1)
def get_thresholds_config() -> Dict[str, Any]:
    return _read_json(
        "thresholds.json",
        {
            "underpayment_amount_threshold": 5.0,
            "underpayment_percent_threshold": 3.0,
            "allowed_drift_threshold": 2.0,
            "severity_thresholds": {
                "critical": 500.0,
                "high": 50.0,
                "medium": 10.0,
            },
        },
    )


@lru_cache(maxsize=1)
def get_payer_normalization_map() -> Dict[str, Any]:
    return _read_json(
        "payer_normalization_map.json",
        {
            "medicare": ["MEDICARE", "CMS"],
            "tx_medicaid_ffs": ["TX MEDICAID", "TEXAS MEDICAID", "TMHP"],
        },
    )


@lru_cache(maxsize=1)
def get_locality_resolution_rules() -> Dict[str, Any]:
    return _read_json(
        "medicare_locality_resolution_rules.json",
        {
            "order": ["OVERRIDE", "SERVICE_ZIP", "BILLING_ZIP", "UNKNOWN"],
            "override_priority": ["FACILITY_NPI", "RENDERING_NPI", "BILLING_NPI", "TAX_ID"],
            "unknown_confidence": 25,
        },
    )


@lru_cache(maxsize=1)
def get_payer_workflow_config() -> Dict[str, Any]:
    return _read_json(
        "payer_workflow_config.json",
        {
            "MEDICARE": {
                "appeal_type": "REDETERMINATION",
                "required_forms": ["CMS-20027"],
                "submission_method": "MAIL",
                "destination": "Configured MAC destination required",
                "deadline_days": 120,
                "required_fields": [
                    "beneficiary_identifier",
                    "payer_claim_control_number",
                    "date_of_service",
                    "line_item_detail",
                    "disagreement_statement",
                ],
            },
            "TX_MEDICAID_FFS": {
                "appeal_type": "CLAIM_PAYMENT_DISPUTE",
                "required_forms": ["TMHP_APPEAL_LETTER"],
                "submission_method": "PORTAL",
                "destination": "TMHP claims appeal routing",
                "deadline_days": 95,
                "required_fields": [
                    "provider_identifier",
                    "payer_claim_control_number",
                    "date_of_service",
                    "line_item_detail",
                    "dispute_reason",
                ],
            },
        },
    )

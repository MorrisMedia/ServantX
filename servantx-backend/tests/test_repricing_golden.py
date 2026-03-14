import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.repricing_service import (
    build_line_findings,
    compute_medicare_expected_allowed,
    compute_tx_medicaid_expected_allowed,
)


def test_medicare_expected_allowed_golden_case():
    expected = compute_medicare_expected_allowed(
        work_rvu=1.5,
        pe_rvu=1.2,
        mp_rvu=0.3,
        work_gpci=1.02,
        pe_gpci=0.95,
        mp_gpci=1.10,
        conversion_factor=33.3,
        units=2.0,
    )
    assert round(expected, 2) == 199.80


def test_tx_medicaid_expected_allowed_golden_case():
    expected = compute_tx_medicaid_expected_allowed(allowed_amount=47.25, units=3)
    assert round(expected, 2) == 141.75


def test_underpayment_confirmed_finding_generated():
    line = {
        "line_allowed_amount": 0.0,
        "adjustments": [{"group_code": "CO", "reason_code": "45", "amount": 7.66, "quantity": None}],
    }
    repricing_result = {
        "errors": [],
        "expected_allowed": 100.0,
        "actual_paid": 92.0,
        "variance_amount": 8.0,
        "variance_percent": 8.0,
        "confidence_score": 92.0,
    }
    findings = build_line_findings(line=line, repricing_result=repricing_result)
    finding_codes = {finding["finding_code"] for finding in findings}
    assert "UNDERPAYMENT_CONFIRMED" in finding_codes


def test_allowed_mismatch_finding_generated():
    line = {
        "line_allowed_amount": 70.0,
        "adjustments": [],
    }
    repricing_result = {
        "errors": [],
        "expected_allowed": 100.0,
        "actual_paid": 95.0,
        "variance_amount": 5.0,
        "variance_percent": 5.0,
        "confidence_score": 75.0,
    }
    findings = build_line_findings(line=line, repricing_result=repricing_result)
    finding_codes = {finding["finding_code"] for finding in findings}
    assert "ALLOWED_MISMATCH" in finding_codes


def test_zero_pay_potential_underpayment_finding_generated():
    line = {
        "line_allowed_amount": 0.0,
        "adjustments": [],
    }
    repricing_result = {
        "errors": [],
        "expected_allowed": 125.0,
        "actual_paid": 0.0,
        "variance_amount": 125.0,
        "variance_percent": 100.0,
        "confidence_score": 80.0,
    }
    findings = build_line_findings(line=line, repricing_result=repricing_result)
    finding_codes = {finding["finding_code"] for finding in findings}
    assert "ZERO_PAY_POTENTIAL_UNDERPAYMENT" in finding_codes

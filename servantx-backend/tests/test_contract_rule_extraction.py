import os
import sys
import types
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("SENDGRID_TO_EMAIL", "test@example.com")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Lightweight stub for optional dependency used by contract text extraction.
if "docx" not in sys.modules:
    fake_docx = types.ModuleType("docx")
    fake_docx.Document = lambda *_args, **_kwargs: types.SimpleNamespace(paragraphs=[], tables=[])
    sys.modules["docx"] = fake_docx

from services.contract_rules_engine import (
    extract_candidate_rule_lines,
    extract_conditions,
    get_contract_text_with_fallback,
)


def test_extract_conditions_ignores_metadata_year_tokens():
    description = "Processed by contract-rules-engine-v1 at 2026-02-13T18:30:00 with 4 extracted rule(s)."
    conditions = extract_conditions(description)
    assert not conditions or "amounts" not in conditions


def test_extract_conditions_parses_richer_rule_structure():
    description = (
        "CPT 99213 with modifier 25 at POS 22 must be reimbursed at $125.50 per service within 45 days."
    )
    conditions = extract_conditions(description) or {}

    assert "$125.50" in conditions.get("amounts", [])
    assert conditions.get("serviceCodes") == ["99213"]
    assert conditions.get("modifiers") == ["25"]
    assert conditions.get("placeOfService") == ["22"]
    assert conditions.get("timeWindowDays") == [45]
    assert conditions.get("period") == "per_service"


def test_fallback_ignores_processing_metadata_notes(monkeypatch):
    monkeypatch.setattr(
        "services.contract_rules_engine.extract_contract_text",
        lambda *_args, **_kwargs: "Warning: Unsupported contract file type: .doc",
    )
    contract = {
        "name": "Test Contract",
        "fileName": "contract.doc",
        "fileUrl": "contracts/test.doc",
        "notes": "Processed by contract-rules-engine-v1 at 2026-02-13T18:30:00 with 1 extracted rule(s).",
    }
    extracted = get_contract_text_with_fallback(contract)
    assert extracted == ""


def test_candidate_rule_lines_drop_table_of_contents_noise():
    text = "\n".join(
        [
            "Based on HHSC Provider Finance Department SFY 2026 Rate Publications",
            "Article IV SFY 2026 Standard Dollar Amount (SDA) Rates 6",
            "CPT 99213 with modifier 25 at POS 22 must be reimbursed at $125.50 per service within 45 days.",
        ]
    )

    lines = extract_candidate_rule_lines(text)

    assert lines == [
        "CPT 99213 with modifier 25 at POS 22 must be reimbursed at $125.50 per service within 45 days."
    ]



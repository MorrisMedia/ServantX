from datetime import datetime
import hashlib
import re
from typing import Any, Dict, List, Optional, Set

from services.contract_text_extraction_service import extract_contract_text


RULE_KEYWORDS = (
    "must",
    "shall",
    "required",
    "requirement",
    "within",
    "due",
    "net ",
    "payment",
    "reimbursement",
    "underpayment",
    "rate",
    "amount",
    "invoice",
    "documentation",
    "claim",
    "audit",
    "compliance",
    "billing",
    "record",
    "hours",
    "termination",
    "notice",
    "obligation",
    "penalty",
)

ERROR_PREFIXES = (
    "Error extracting text",
    "File not found",
    "Warning:",
)

METADATA_LINE_MARKERS = (
    "processed by contract-rules-engine",
    "extraction warning:",
    "contract-rules-engine-v1 failed",
    "file not found:",
    "error extracting text",
    "warning:",
)

AMOUNT_CONTEXT_KEYWORDS = (
    "payment",
    "paid",
    "pay",
    "reimbursement",
    "underpayment",
    "rate",
    "amount",
    "allowed",
    "allowable",
    "baseline",
    "charge",
    "fee",
    "contracted",
    "per month",
    "per quarter",
    "per year",
    "per annum",
    "per week",
    "per day",
    "per hour",
    "per visit",
    "per claim",
    "per service",
    "monthly",
    "quarterly",
    "annual",
    "yearly",
    "weekly",
    "daily",
)

DATE_CONTEXT_KEYWORDS = (
    "effective",
    "expiration",
    "term",
    "renewal",
    "fiscal",
    "sfy",
    "fy",
    "calendar year",
    "state fiscal year",
    "publication",
    "publications",
    "article",
    "section",
    "chapter",
    "appendix",
    "table of contents",
    "contents",
    "page",
    "date",
    "year",
    "through",
    "from",
    "to",
)

DOCUMENT_KEYWORDS = ("document", "documentation", "claim", "invoice", "submit", "billing record")
COMPARISON_KEYWORDS = ("rate", "amount", "reimbursement", "underpayment", "$", "percent", "x")
VALIDATION_KEYWORDS = ("must", "shall", "required", "within", "due", "net", "termination", "notice")
SYNTHETIC_CONTRACT_RULE_LINES = (
    "Hospital reimbursement baseline is 1200 USD per month.",
    "Any payment below baseline should be treated as underpayment.",
    "Payment terms are NET 30 from invoice date.",
    "After-hours services are reimbursed at 1.5x standard hourly rate.",
)


def normalize_line(raw_line: str) -> str:
    return re.sub(r"\s+", " ", raw_line).strip(" \t-:")


def is_noise_line(line: str) -> bool:
    if len(line) < 12:
        return True
    if re.fullmatch(r"[\W_]+", line):
        return True
    if re.fullmatch(r"(?i)page\s+\d+(\s+of\s+\d+)?", line):
        return True
    return False


def is_extraction_error(text: str) -> bool:
    return any(text.startswith(prefix) for prefix in ERROR_PREFIXES)


def _is_metadata_line(normalized_line: str) -> bool:
    return any(marker in normalized_line for marker in METADATA_LINE_MARKERS)


def _line_has_rule_signal(normalized_line: str) -> bool:
    if any(keyword in normalized_line for keyword in RULE_KEYWORDS):
        return True
    if re.search(r"(?i)\$\s*\d|\b\d+(?:\.\d+)?\s*(?:usd|dollars?)\b", normalized_line):
        return True
    if re.search(r"(?i)\bnet\s+\d+\b", normalized_line):
        return True
    if re.search(r"(?i)\b(?:cpt|hcpcs|modifier|place of service|pos)\b", normalized_line):
        return True
    return False


def _has_strong_rule_signal(normalized_line: str) -> bool:
    strong_tokens = (
        "must",
        "shall",
        "required",
        "within",
        "due",
        "net ",
        "at least",
        "not less than",
        "no less than",
        "at most",
        "not more than",
        "no more than",
        "less than",
        "greater than",
        "no later than",
        "not later than",
    )
    return any(token in normalized_line for token in strong_tokens)


def _has_quantitative_rule_signal(normalized_line: str) -> bool:
    return bool(
        re.search(
            r"(?i)\$\s*\d|\b\d[\d,]*(?:\.\d+)?\s*(?:usd|dollars?|%)\b|"
            r"\bnet\s+\d+\b|\b(?:within|in)\s+\d+\s*(?:business\s*)?days?\b|"
            r"\b\d+(?:\.\d+)?x\b|\bper\s+(?:month|quarter|year|week|day|hour|visit|claim|service)\b|"
            r"\b(?:cpt|hcpcs|modifier|place of service|pos)\b",
            normalized_line,
        )
    )


def _is_heading_or_index_line(normalized_line: str) -> bool:
    if re.search(r"(?i)\btable of contents\b|^contents?$", normalized_line):
        return True
    if re.search(r"(?i)^(article|section|chapter|appendix)\b", normalized_line):
        if re.search(r"\b\d{1,4}$", normalized_line):
            return True
        if not _has_strong_rule_signal(normalized_line):
            return True
    if re.search(r"(?i)^\d+(?:\.\d+)*\s+[a-z].*\b\d{1,4}$", normalized_line):
        return True
    return False


def _is_metadata_only_text(text: str) -> bool:
    raw_lines = [normalize_line(line) for line in text.splitlines() if normalize_line(line)]
    if not raw_lines:
        return True

    metadata_lines = 0
    signal_lines = 0
    for line in raw_lines:
        normalized_line = line.lower()
        if _is_metadata_line(normalized_line):
            metadata_lines += 1
            continue
        if _line_has_rule_signal(normalized_line):
            signal_lines += 1

    return metadata_lines > 0 and signal_lines == 0


def get_contract_text_with_fallback(contract: Dict[str, Any]) -> str:
    file_path = contract.get("filePath") or contract.get("fileUrl") or ""
    file_name = contract.get("fileName") or ""
    extracted_text = extract_contract_text(file_path, file_name) if file_path else ""

    contract_name = str(contract.get("name") or "").lower()
    file_name = str(contract.get("fileName") or "").lower()
    synthetic_fallback_text = "\n".join(SYNTHETIC_CONTRACT_RULE_LINES)
    notes_fallback_text = contract.get("notes") or ""

    # Preserve synthetic fallback even after extra processing notes are appended.
    if "synthetic contract seeded for demo/testing." in notes_fallback_text.lower():
        notes_fallback_text = synthetic_fallback_text

    if is_extraction_error(extracted_text):
        if notes_fallback_text and not _is_metadata_only_text(notes_fallback_text):
            extracted_text = notes_fallback_text
        else:
            extracted_text = ""

    if extracted_text and _is_metadata_only_text(extracted_text):
        extracted_text = ""

    if (not extracted_text.strip()) and (
        contract_name.startswith("synthetic contract") or file_name == "synthetic_contract.pdf"
    ):
        extracted_text = synthetic_fallback_text

    return extracted_text.strip()


def _split_fallback_sentences(text: str) -> List[str]:
    normalized = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    normalized = re.sub(r"(?<=\d)\.(?=\d)", "<DECIMAL_DOT>", normalized)
    sentences = re.split(r"(?<=[.!?;])\s*|(?<=[.!?;])(?=[A-Z])", normalized)
    sentences = [sentence.replace("<DECIMAL_DOT>", ".") for sentence in sentences]
    return [normalize_line(sentence) for sentence in sentences if normalize_line(sentence)]


def extract_candidate_rule_lines(text: str) -> List[str]:
    if not text:
        return []

    matched_lines: List[str] = []
    all_lines: List[str] = []
    seen: Set[str] = set()

    raw_lines = text.splitlines()
    if len(raw_lines) <= 1:
        raw_lines = _split_fallback_sentences(text)

    for raw_line in raw_lines:
        line = normalize_line(raw_line)
        if not line or is_noise_line(line):
            continue

        if len(line) > 600:
            line = line[:600].rstrip()

        normalized_key = line.lower()
        if _is_metadata_line(normalized_key):
            continue
        if _is_heading_or_index_line(normalized_key) and not _has_strong_rule_signal(normalized_key):
            continue
        if normalized_key in seen:
            continue
        seen.add(normalized_key)
        all_lines.append(line)

        if any(keyword in normalized_key for keyword in RULE_KEYWORDS) and (
            _has_strong_rule_signal(normalized_key) or _has_quantitative_rule_signal(normalized_key)
        ):
            matched_lines.append(line)

    # "All rules" behavior: return all matched candidates with no arbitrary truncation.
    if matched_lines:
        return matched_lines
    # If no rule-like lines are matched, still return all normalized lines for full coverage.
    return all_lines


def classify_rule_type(description: str) -> str:
    description_lower = description.lower()

    if any(keyword in description_lower for keyword in DOCUMENT_KEYWORDS):
        return "document"
    if any(keyword in description_lower for keyword in COMPARISON_KEYWORDS):
        return "comparison"
    if any(keyword in description_lower for keyword in VALIDATION_KEYWORDS):
        return "validation"
    return "other"


def _parse_numeric(raw_value: str) -> Optional[float]:
    cleaned = str(raw_value).strip().lower()
    cleaned = cleaned.replace("$", "").replace("usd", "").replace("dollars", "").replace("dollar", "")
    cleaned = cleaned.replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except Exception:
        return None


def _is_year_like_amount(raw_value: str, parsed_value: float, context_window: str) -> bool:
    if not parsed_value.is_integer():
        return False
    int_value = int(parsed_value)
    if int_value < 1900 or int_value > 2100:
        return False

    lowered_raw = raw_value.lower()
    if "$" in lowered_raw or "usd" in lowered_raw or "dollar" in lowered_raw:
        return False

    context_lower = context_window.lower()
    has_amount_context = any(token in context_lower for token in AMOUNT_CONTEXT_KEYWORDS)
    has_date_context = any(token in context_lower for token in DATE_CONTEXT_KEYWORDS)
    return has_date_context or not has_amount_context


def _extract_period(description_lower: str) -> Optional[str]:
    if any(token in description_lower for token in ("per service", "each service", "per claim", "each claim", "per visit", "each visit")):
        return "per_service"
    if any(token in description_lower for token in ("per hour", "hourly", "each hour")):
        return "hourly"
    if any(token in description_lower for token in ("per day", "daily", "each day")):
        return "daily"
    if any(token in description_lower for token in ("per week", "weekly", "each week")):
        return "weekly"
    if any(token in description_lower for token in ("per month", "monthly", "each month", "/month")):
        return "monthly"
    if any(token in description_lower for token in ("per quarter", "quarterly", "each quarter", "/quarter", "q1", "q2", "q3", "q4")):
        return "quarterly"
    if any(token in description_lower for token in ("per year", "yearly", "annual", "annually", "per annum", "/year", "fiscal year")):
        return "annual"
    return None


def extract_conditions(description: str) -> Optional[Dict[str, Any]]:
    conditions: Dict[str, Any] = {}
    description_lower = description.lower()

    amount_candidates: List[str] = []
    seen_amounts: Set[str] = set()

    # Currency-anchored amounts.
    for match in re.finditer(
        r"(?i)(?:\$\s*[0-9][0-9,]*(?:\.\d{1,2})?|[0-9][0-9,]*(?:\.\d{1,2})?\s*(?:usd|dollars?))",
        description,
    ):
        raw_amount = match.group(0).strip()
        parsed = _parse_numeric(raw_amount)
        if parsed is None or parsed <= 0:
            continue
        normalized_key = f"{parsed:.2f}"
        if normalized_key in seen_amounts:
            continue
        seen_amounts.add(normalized_key)
        amount_candidates.append(raw_amount)

    # Bare numeric amounts are accepted only with explicit money/rate syntax.
    explicit_amount_patterns = (
        r"(?i)\b(?:payment|reimbursement|rate|amount|allowed|allowable|fee|baseline|capitation)\s*(?:amount\s*)?"
        r"(?:of|is|at|=|:)?\s*\$?\s*([0-9][0-9,]*(?:\.\d{1,2})?)\b",
        r"(?i)\$?\s*([0-9][0-9,]*(?:\.\d{1,2})?)\s*(?:per|/)\s*(?:month|quarter|year|week|day|hour|visit|claim|service)\b",
    )
    for pattern in explicit_amount_patterns:
        for match in re.finditer(pattern, description):
            raw_amount = match.group(1).strip()
            parsed = _parse_numeric(raw_amount)
            if parsed is None or parsed <= 0:
                continue

            context_window = description[max(0, match.start() - 35): min(len(description), match.end() + 35)]
            context_lower = context_window.lower()

            if re.search(
                rf"(?i)\b(?:within|in|net)\s+{re.escape(raw_amount)}\s*(?:business\s*)?days?\b",
                description,
            ):
                continue
            if re.search(
                rf"(?i)\b(?:cpt|hcpcs|code|modifier|mod|pos|place of service)\s*[:#-]?\s*{re.escape(raw_amount)}\b",
                description,
            ):
                continue
            if re.search(r"(?i)\b(?:tac|§|article|section|chapter|appendix|title|code|bill|legislature|act)\b", context_lower):
                continue
            if _is_year_like_amount(raw_amount, parsed, context_window):
                continue

            normalized_key = f"{parsed:.2f}"
            if normalized_key in seen_amounts:
                continue
            seen_amounts.add(normalized_key)
            amount_candidates.append(raw_amount)

    if amount_candidates:
        conditions["amounts"] = amount_candidates

    net_match = re.search(r"(?i)\bnet\s+(\d+)\b", description)
    if net_match:
        conditions["netDays"] = int(net_match.group(1))

    multiplier_matches = re.findall(r"(?i)\b(\d+(?:\.\d+)?)x\b", description)
    if multiplier_matches:
        multipliers = [float(value) for value in multiplier_matches]
        conditions["multipliers"] = multipliers
        if len(multipliers) == 1:
            conditions["multiplier"] = multipliers[0]

    percent_matches = re.findall(r"(?i)\b(\d+(?:\.\d+)?)\s*%\b", description)
    if percent_matches:
        percents = [float(value) for value in percent_matches]
        conditions["percents"] = percents
        if len(percents) == 1:
            conditions["percent"] = percents[0]

    day_matches = re.findall(
        r"(?i)\b(?:within|no later than|not later than|in)\s+(\d{1,3})\s*(?:business\s*)?days?\b",
        description,
    )
    if day_matches:
        conditions["timeWindowDays"] = sorted({int(value) for value in day_matches})

    service_codes = re.findall(r"(?i)\b(?:cpt|hcpcs|code)\s*[:#-]?\s*([a-z]?\d{4,5}[a-z]?)\b", description)
    if service_codes:
        conditions["serviceCodes"] = sorted({code.upper() for code in service_codes})

    revenue_codes = re.findall(r"(?i)\b(?:revenue code|rev(?:enue)?)\s*[:#-]?\s*(\d{3,4})\b", description)
    if revenue_codes:
        conditions["revenueCodes"] = sorted({code for code in revenue_codes})

    modifier_matches = re.findall(r"(?i)\b(?:modifier|mod)\s*[:#-]?\s*([a-z0-9]{2})\b", description)
    if modifier_matches:
        conditions["modifiers"] = sorted({modifier.upper() for modifier in modifier_matches})

    pos_matches = re.findall(r"(?i)\b(?:place of service|pos)\s*[:#-]?\s*(\d{2})\b", description)
    if pos_matches:
        conditions["placeOfService"] = sorted({pos for pos in pos_matches})

    comparison_operator = None
    if re.search(r"(?i)\b(?:at least|minimum|min\.?|not less than|no less than)\b", description):
        comparison_operator = "gte"
    elif re.search(r"(?i)\b(?:at most|maximum|max\.?|not more than|no more than)\b", description):
        comparison_operator = "lte"
    elif re.search(r"(?i)\b(?:below|less than|under)\b", description):
        comparison_operator = "lt"
    elif re.search(r"(?i)\b(?:above|greater than|over|exceed(?:s|ed)?)\b", description):
        comparison_operator = "gt"
    elif re.search(r"(?i)\b(?:equal(?:s)?|exactly)\b", description):
        comparison_operator = "eq"
    if comparison_operator:
        conditions["comparisonOperator"] = comparison_operator

    period = _extract_period(description_lower)
    if period:
        conditions["period"] = period

    matched_keywords = [keyword for keyword in RULE_KEYWORDS if keyword in description_lower]
    if matched_keywords:
        conditions["keywords"] = matched_keywords[:10]

    return conditions or None


def build_rules_for_contract(contract: Dict[str, Any]) -> List[Dict[str, Any]]:
    extracted_text = get_contract_text_with_fallback(contract)
    candidate_lines = extract_candidate_rule_lines(extracted_text)

    contract_name = contract.get("name", "Contract")
    contract_id = contract.get("id", "unknown-contract")
    created_at = contract.get("uploadedAt") or datetime.utcnow()
    updated_at = created_at

    if not candidate_lines:
        candidate_lines = [
            f"Review payment terms in {contract_name} and verify billing records against the contracted amount."
        ]

    rules: List[Dict[str, Any]] = []
    for index, description in enumerate(candidate_lines, start=1):
        rule_digest = hashlib.sha1(f"{contract_id}:{description}".encode("utf-8")).hexdigest()[:12]
        rules.append(
            {
                "id": f"rule_{rule_digest}",
                "contractId": contract_id,
                "contractName": contract_name,
                "name": f"{contract_name} Rule {index}",
                "description": description,
                "type": classify_rule_type(description),
                "conditions": extract_conditions(description),
                "createdAt": created_at,
                "updatedAt": updated_at,
                "isActive": True,
            }
        )

    return rules

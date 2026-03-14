from datetime import datetime
from typing import Any, Dict, List, Optional


def _split_segments(raw_text: str) -> List[str]:
    normalized = raw_text.replace("\r", "").replace("\n", "")
    return [segment.strip() for segment in normalized.split("~") if segment.strip()]


def _safe_float(value: Optional[str], default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Optional[str], default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _to_iso_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    if len(value) == 8 and value.isdigit():
        return f"{value[0:4]}-{value[4:6]}-{value[6:8]}"
    try:
        return datetime.fromisoformat(value).date().isoformat()
    except ValueError:
        return None


def _parse_svc_composite(svc_01: str) -> Dict[str, Any]:
    parts = svc_01.split(":")
    # Typical values: HC:99214:25
    code_set = parts[0] if parts else None
    cpt_hcpcs = parts[1] if len(parts) > 1 else None
    modifiers = [part for part in parts[2:] if part]
    return {
        "code_set": code_set,
        "cpt_hcpcs": cpt_hcpcs,
        "modifiers": modifiers,
    }


def parse_claim_835(
    raw_claim_edi: str,
    batch_id: str,
    document_id: str,
    parent_file_document_id: Optional[str],
    payer: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    segments = _split_segments(raw_claim_edi)

    clp_segment = ""
    svc_segments: List[str] = []
    cas_segments: List[str] = []
    trace_number = None

    payer_payload = payer or {}
    payer_key = payer_payload.get("payer_key") or "OTHER"
    payer_name = payer_payload.get("payer_name")
    payer_id = payer_payload.get("payer_id")
    payer_type = payer_payload.get("payer_type") or ("MEDICARE" if payer_key == "MEDICARE" else "MEDICAID")
    payer_state = payer_payload.get("state")

    claim: Dict[str, Any] = {
        "patient_control_number": None,
        "payer_claim_control_number": None,
        "claim_status_code": None,
        "claim_type": "PROFESSIONAL",
        "total_charge_amount": 0.0,
        "claim_payment_amount": 0.0,
        "patient_responsibility_amount": 0.0,
        "claim_received_date": None,
        "service_date_start": None,
        "service_date_end": None,
    }

    provider: Dict[str, Any] = {
        "billing_provider_name": None,
        "billing_provider_npi": None,
        "rendering_provider_name": None,
        "rendering_provider_npi": None,
        "facility_name": None,
        "facility_npi": None,
        "service_location": {
            "address1": None,
            "city": None,
            "state": None,
            "zip": None,
        },
        "billing_location": {"zip": None},
    }

    service_lines: List[Dict[str, Any]] = []
    current_line: Optional[Dict[str, Any]] = None
    current_nm1_entity: Optional[str] = None

    for segment in segments:
        parts = segment.split("*")
        tag = parts[0]

        if tag == "CLP":
            clp_segment = segment
            claim["patient_control_number"] = parts[1] if len(parts) > 1 else None
            claim["claim_status_code"] = parts[2] if len(parts) > 2 else None
            claim["total_charge_amount"] = _safe_float(parts[3] if len(parts) > 3 else None)
            claim["claim_payment_amount"] = _safe_float(parts[4] if len(parts) > 4 else None)
            claim["patient_responsibility_amount"] = _safe_float(parts[5] if len(parts) > 5 else None)
            claim["payer_claim_control_number"] = parts[7] if len(parts) > 7 else None

        elif tag == "TRN":
            trace_number = parts[2] if len(parts) > 2 else None

        elif tag == "NM1":
            current_nm1_entity = parts[1] if len(parts) > 1 else None
            name = parts[3] if len(parts) > 3 else None
            npi = parts[9] if len(parts) > 9 else None
            if current_nm1_entity == "85":
                provider["billing_provider_name"] = name
                provider["billing_provider_npi"] = npi
            elif current_nm1_entity == "82":
                provider["rendering_provider_name"] = name
                provider["rendering_provider_npi"] = npi
            elif current_nm1_entity in ("77", "FA"):
                provider["facility_name"] = name
                provider["facility_npi"] = npi

        elif tag == "N3":
            address1 = parts[1] if len(parts) > 1 else None
            if current_nm1_entity in ("77", "FA"):
                provider["service_location"]["address1"] = address1

        elif tag == "N4":
            city = parts[1] if len(parts) > 1 else None
            state = parts[2] if len(parts) > 2 else None
            zip_code = parts[3] if len(parts) > 3 else None
            if current_nm1_entity in ("77", "FA"):
                provider["service_location"]["city"] = city
                provider["service_location"]["state"] = state
                provider["service_location"]["zip"] = zip_code
            elif current_nm1_entity == "85":
                provider["billing_location"]["zip"] = zip_code

        elif tag == "DTM":
            qualifier = parts[1] if len(parts) > 1 else None
            date_value = _to_iso_date(parts[2] if len(parts) > 2 else None)
            if qualifier == "050":
                claim["claim_received_date"] = date_value
            elif qualifier in ("232", "150"):
                claim["service_date_start"] = date_value
            elif qualifier in ("233", "151"):
                claim["service_date_end"] = date_value
            elif qualifier == "472" and current_line is not None:
                current_line["line_service_date"] = date_value

        elif tag == "SVC":
            svc_segments.append(segment)
            composite = _parse_svc_composite(parts[1] if len(parts) > 1 else "")
            current_line = {
                "line_number": len(service_lines) + 1,
                "cpt_hcpcs": composite["cpt_hcpcs"],
                "modifiers": composite["modifiers"],
                "units": _safe_int(parts[5] if len(parts) > 5 else None, default=1) or 1,
                "place_of_service": None,
                "line_charge_amount": _safe_float(parts[2] if len(parts) > 2 else None),
                "line_payment_amount": _safe_float(parts[3] if len(parts) > 3 else None),
                "line_allowed_amount": _safe_float(parts[6] if len(parts) > 6 else None),
                "line_service_date": None,
                "adjustments": [],
            }
            service_lines.append(current_line)

        elif tag == "CAS":
            cas_segments.append(segment)
            if current_line is None:
                continue
            group_code = parts[1] if len(parts) > 1 else None
            index = 2
            while index + 1 < len(parts):
                reason_code = parts[index]
                amount = _safe_float(parts[index + 1], default=0.0)
                quantity = parts[index + 2] if index + 2 < len(parts) else None
                current_line["adjustments"].append(
                    {
                        "group_code": group_code,
                        "reason_code": reason_code,
                        "amount": amount,
                        "quantity": quantity,
                    }
                )
                index += 3

    payload = {
        "schema_version": "claim_835_v1",
        "batch_id": batch_id,
        "document_id": document_id,
        "parent_file_document_id": parent_file_document_id,
        "payer": {
            "payer_key": payer_key,
            "payer_name": payer_name,
            "payer_id": payer_id,
            "payer_type": payer_type,
            "state": payer_state,
        },
        "provider": provider,
        "claim": claim,
        "service_lines": service_lines,
        "raw_edi_evidence": {
            "clp_segment": clp_segment,
            "svc_segments": svc_segments,
            "cas_segments": cas_segments,
            "trn_segment": trace_number,
        },
    }
    return payload

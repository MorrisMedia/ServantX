"""
HIPAA PHI De-identification Service

Tokenizes Protected Health Information (PHI) before any data leaves the system
to external AI APIs. Re-hydrates results using the local token map.

PHI fields in 835 EDI claims (18 HIPAA identifiers present):
  - patient_control_number   (CLP01)
  - payer_claim_control_number (CLP07)
  - service_date_start/end   (DTM*232, DTM*233)
  - claim_received_date      (DTM*050)
  - billing_provider_name + billing_provider_npi  (NM1*85)
  - rendering_provider_name + rendering_provider_npi (NM1*82)
  - facility_name + facility_npi  (NM1*77/FA)
  - service_location address  (N3/N4 segments)

Safe to send to LLM (non-PHI):
  cpt_hcpcs, modifiers, units, line amounts, adjustment codes/amounts,
  payer_key, payer_type, claim_type, total/payment amounts.

Usage:
    from services.phi_service import deidentify_claim_payload, reidentify_findings

    safe_payload, token_map = deidentify_claim_payload(claim_dict, hospital_id)
    # ... send safe_payload to LLM ...
    findings_with_phi = reidentify_findings(findings, token_map)
"""

from __future__ import annotations

import hashlib
import hmac
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings

# TTL for PHI token records — 90 days satisfies HIPAA minimum retention
PHI_TOKEN_TTL_DAYS = 90

# PHI field names — used as token prefix labels
PHI_FIELDS = {
    "patient_control_number",
    "payer_claim_control_number",
    "service_date_start",
    "service_date_end",
    "claim_received_date",
    "billing_provider_name",
    "billing_provider_npi",
    "rendering_provider_name",
    "rendering_provider_npi",
    "facility_name",
    "facility_npi",
    "service_address",
    "service_city",
    "service_state",
    "service_zip",
    "billing_zip",
}

# Abbreviated labels for compact token strings
_FIELD_ABBREV = {
    "patient_control_number": "CLM",
    "payer_claim_control_number": "PAY",
    "service_date_start": "DOS",
    "service_date_end": "DOE",
    "claim_received_date": "DRC",
    "billing_provider_name": "BPN",
    "billing_provider_npi": "BNP",
    "rendering_provider_name": "RPN",
    "rendering_provider_npi": "RNP",
    "facility_name": "FCN",
    "facility_npi": "FNP",
    "service_address": "ADR",
    "service_city": "CTY",
    "service_state": "STA",
    "service_zip": "ZIP",
    "billing_zip": "BZP",
}


def _make_token(hospital_id: str, phi_field: str, phi_value: str) -> str:
    """
    Generate a deterministic, opaque token for a PHI value.

    Uses HMAC-SHA256 with the hospital_id as the key so tokens are:
    - Deterministic: same (hospital, field, value) → same token always
    - Opaque: no way to reverse the value without the hospital_id
    - Scoped: tokens from different hospitals don't collide

    Returns a token like: PHI_BNP_a1b2c3d4e5f6g7h8
    """
    key = hospital_id.encode("utf-8")
    message = f"{phi_field}:{phi_value}".encode("utf-8")
    digest = hmac.new(key, message, hashlib.sha256).hexdigest()[:16]
    abbrev = _FIELD_ABBREV.get(phi_field, phi_field[:3].upper())
    return f"PHI_{abbrev}_{digest}"


def deidentify_claim_payload(
    claim: Dict[str, Any],
    hospital_id: str,
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Remove PHI from a parsed 835 claim dict and replace with opaque tokens.

    Returns:
        (safe_claim, token_to_phi_map)

    safe_claim    — safe to send to external LLM (no PHI)
    token_to_phi  — {token: original_value} for local re-hydration
    """
    token_map: Dict[str, str] = {}

    def _tok(field: str, value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        token = _make_token(hospital_id, field, str(value))
        token_map[token] = str(value)
        return token

    safe = {}

    # ── Non-PHI fields passed through as-is ─────────────────────────────────
    for passthrough in (
        "claim_type", "payer_key", "payer_type",
        "total_charge_amount", "claim_payment_amount",
        "claim_status_code", "claim_filing_indicator",
        "service_lines",   # each line has non-PHI CPT/amounts — see below
    ):
        if passthrough in claim and passthrough != "service_lines":
            safe[passthrough] = claim[passthrough]

    # Service lines: CPT, amounts, adjustments are non-PHI
    raw_lines = claim.get("service_lines") or []
    safe_lines = []
    for line in raw_lines:
        safe_lines.append({
            "cpt_hcpcs": line.get("cpt_hcpcs"),
            "modifiers": line.get("modifiers"),
            "units": line.get("units"),
            "line_charge_amount": line.get("line_charge_amount"),
            "line_payment_amount": line.get("line_payment_amount"),
            "adjustments": line.get("adjustments"),
        })
    safe["service_lines"] = safe_lines

    # ── PHI fields — replaced with tokens ────────────────────────────────────
    safe["patient_control_number"] = _tok(
        "patient_control_number", claim.get("patient_control_number")
    )
    safe["payer_claim_control_number"] = _tok(
        "payer_claim_control_number", claim.get("payer_claim_control_number")
    )
    safe["service_date_start"] = _tok(
        "service_date_start", claim.get("service_date_start")
    )
    safe["service_date_end"] = _tok(
        "service_date_end", claim.get("service_date_end")
    )
    safe["claim_received_date"] = _tok(
        "claim_received_date", claim.get("claim_received_date")
    )

    # Provider info (nested dict or flat)
    provider = claim.get("provider") or {}
    safe_provider: Dict[str, Any] = {}
    safe_provider["billing_provider_npi"] = _tok(
        "billing_provider_npi", provider.get("billing_provider_npi")
    )
    safe_provider["billing_provider_name"] = _tok(
        "billing_provider_name", provider.get("billing_provider_name")
    )
    safe_provider["rendering_provider_npi"] = _tok(
        "rendering_provider_npi", provider.get("rendering_provider_npi")
    )
    safe_provider["rendering_provider_name"] = _tok(
        "rendering_provider_name", provider.get("rendering_provider_name")
    )
    safe_provider["facility_npi"] = _tok(
        "facility_npi", provider.get("facility_npi")
    )
    safe_provider["facility_name"] = _tok(
        "facility_name", provider.get("facility_name")
    )
    # Locality code (non-PHI, used for Medicare repricing) — passthrough
    safe_provider["locality_code"] = provider.get("locality_code")

    # Address fields — tokenized
    loc = provider.get("service_location") or {}
    safe_provider["service_location"] = {
        "address1": _tok("service_address", loc.get("address1")),
        "city": _tok("service_city", loc.get("city")),
        "state": _tok("service_state", loc.get("state")),
        "zip": _tok("service_zip", loc.get("zip")),
    }
    billing_loc = provider.get("billing_location") or {}
    safe_provider["billing_location"] = {
        "zip": _tok("billing_zip", billing_loc.get("zip")),
    }
    safe["provider"] = safe_provider

    return safe, token_map


def deidentify_835_text(raw_edi: str, hospital_id: str) -> Tuple[str, Dict[str, str]]:
    """
    Regex-tokenize PHI directly in raw 835 EDI text.

    Used when the LLM needs the raw EDI string (e.g. underpayment analysis).
    Replaces known PHI patterns while preserving EDI structure.

    Returns (tokenized_edi_text, token_to_phi_map).
    """
    token_map: Dict[str, str] = {}

    def _replace(field: str, value: str) -> str:
        tok = _make_token(hospital_id, field, value)
        token_map[tok] = value
        return tok

    result = raw_edi

    # CLP segment structure:
    # CLP*CLP01*CLP02*CLP03*CLP04*CLP05*CLP06*CLP07
    # CLP01 = patient_control_number
    # CLP02 = claim_status_code
    # CLP03 = total_charge_amount
    # CLP04 = claim_payment_amount
    # CLP05 = patient_responsibility_amount
    # CLP06 = claim_filing_indicator
    # CLP07 = payer_claim_control_number (ICN/DCN)
    def _clp_sub(m: re.Match) -> str:
        orig = m.group(0)
        pcn_orig = m.group(1)
        pccn_orig = m.group(2)
        pcn_tok = _replace("patient_control_number", pcn_orig)
        pccn_tok = _replace("payer_claim_control_number", pccn_orig)
        # Replace from right first to avoid index shifting on longer tokens
        result_seg = orig[::-1].replace(pccn_orig[::-1], pccn_tok[::-1], 1)[::-1]
        result_seg = result_seg.replace(pcn_orig, pcn_tok, 1)
        return result_seg

    result = re.sub(
        # CLP01          CLP02-06 (5 fields)                        CLP07
        r"CLP\*([^*~]+)(?:\*[^*~]*){5}\*([^*~]+)",
        _clp_sub,
        result,
    )

    # DTM segments: DTM*232*YYYYMMDD, DTM*233*YYYYMMDD, DTM*050*YYYYMMDD
    _dtm_field_map = {"232": "service_date_start", "233": "service_date_end", "050": "claim_received_date"}

    def _dtm_sub(m: re.Match) -> str:
        qualifier = m.group(1)
        date_val = m.group(2)
        field = _dtm_field_map.get(qualifier)
        if field:
            tok = _replace(field, date_val)
            return m.group(0).replace(date_val, tok, 1)
        return m.group(0)

    result = re.sub(r"DTM\*(232|233|050)\*([0-9]{8})", _dtm_sub, result)

    # NM1 segments — provider names (NM103) and NPIs (NM109)
    # NM1*85 = billing provider, NM1*82 = rendering, NM1*77/FA = facility
    # Structure: NM1*qualifier*entity_type*last_org*first*mid*prefix*suffix*id_qual*npi
    _nm1_type_map = {
        "85": ("billing_provider_name", "billing_provider_npi"),
        "82": ("rendering_provider_name", "rendering_provider_npi"),
        "77": ("facility_name", "facility_npi"),
        "FA": ("facility_name", "facility_npi"),
    }

    def _nm1_sub(m: re.Match) -> str:
        entity = m.group(1)
        mapping = _nm1_type_map.get(entity)
        if not mapping:
            return m.group(0)
        name_field, npi_field = mapping
        # Split the full segment on field delimiter
        parts = m.group(0).split("*")
        # NM103 = index 3 (org/last name)
        if len(parts) > 3 and parts[3]:
            parts[3] = _replace(name_field, parts[3])
        # NM109 = the element after NM108 (the ID qualifier, typically "XX")
        # Use dynamic lookup instead of hardcoded index 9, since segments vary.
        id_qual_indices = [i for i, p in enumerate(parts) if p in ("XX", "SY", "PI", "FI")]
        if id_qual_indices:
            npi_idx = id_qual_indices[-1] + 1
            if npi_idx < len(parts) and parts[npi_idx]:
                raw_npi = parts[npi_idx].rstrip("~")
                if raw_npi:
                    tok = _replace(npi_field, raw_npi)
                    parts[npi_idx] = parts[npi_idx].replace(raw_npi, tok, 1)
        return "*".join(parts)

    # Match NM1 provider segments: qualifier + any number of fields until ~
    # NM1*qualifier*NM102*NM103(name)*NM104*NM105*NM106*NM107*NM108*NM109(NPI)
    result = re.sub(
        r"NM1\*(85|82|77|FA)(?:\*[^*~]*)*",
        _nm1_sub,
        result,
    )

    # N3 address line (service location)
    def _n3_sub(m: re.Match) -> str:
        addr = _replace("service_address", m.group(1))
        return f"N3*{addr}"

    result = re.sub(r"N3\*([^*~]+)", _n3_sub, result)

    # N4 city/state/zip
    def _n4_sub(m: re.Match) -> str:
        city = _replace("service_city", m.group(1))
        state = _replace("service_state", m.group(2))
        zip_val = _replace("service_zip", m.group(3))
        return f"N4*{city}*{state}*{zip_val}"

    result = re.sub(r"N4\*([^*~]+)\*([^*~]+)\*([^*~]+)", _n4_sub, result)

    return result, token_map


def reidentify_text(text: str, token_map: Dict[str, str]) -> str:
    """Replace tokens in text back with original PHI values."""
    for token, phi_value in token_map.items():
        text = text.replace(token, phi_value)
    return text


def reidentify_dict(obj: Any, token_map: Dict[str, str]) -> Any:
    """Recursively replace tokens in a dict/list/str structure with PHI values."""
    if isinstance(obj, str):
        return reidentify_text(obj, token_map)
    if isinstance(obj, dict):
        return {k: reidentify_dict(v, token_map) for k, v in obj.items()}
    if isinstance(obj, list):
        return [reidentify_dict(item, token_map) for item in obj]
    return obj


# ── Database persistence (async) ─────────────────────────────────────────────

async def store_phi_tokens(
    db: AsyncSession,
    hospital_id: str,
    token_map: Dict[str, str],
    document_id: Optional[str] = None,
) -> None:
    """
    Persist token→PHI mappings to the phi_token_map table.

    Uses INSERT ... ON CONFLICT DO NOTHING so repeated calls with the same
    (hospital_id, token) are idempotent.
    """
    from models import PhiTokenMap
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    from sqlalchemy import text

    if not token_map:
        return

    expires_at = datetime.utcnow() + timedelta(days=PHI_TOKEN_TTL_DAYS)

    for token, phi_value in token_map.items():
        # Determine field from token prefix
        parts = token.split("_", 2)
        phi_field = parts[1] if len(parts) >= 2 else "unknown"

        existing = await db.execute(
            select(PhiTokenMap).where(
                PhiTokenMap.hospital_id == hospital_id,
                PhiTokenMap.token == token,
            )
        )
        if existing.scalar_one_or_none() is None:
            db.add(PhiTokenMap(
                hospital_id=hospital_id,
                document_id=document_id,
                token=token,
                phi_field=phi_field,
                phi_value=phi_value,
                expires_at=expires_at,
            ))

    await db.commit()


async def lookup_phi_token(
    db: AsyncSession,
    hospital_id: str,
    token: str,
) -> Optional[str]:
    """Look up the original PHI value for a token."""
    from models import PhiTokenMap

    result = await db.execute(
        select(PhiTokenMap).where(
            PhiTokenMap.hospital_id == hospital_id,
            PhiTokenMap.token == token,
            PhiTokenMap.expires_at > datetime.utcnow(),
        )
    )
    row = result.scalar_one_or_none()
    return row.phi_value if row else None


async def fetch_token_map_for_document(
    db: AsyncSession,
    hospital_id: str,
    document_id: str,
) -> Dict[str, str]:
    """
    Retrieve all token→PHI mappings for a specific document.
    Used to re-hydrate LLM findings after the fact.
    """
    from models import PhiTokenMap

    result = await db.execute(
        select(PhiTokenMap).where(
            PhiTokenMap.hospital_id == hospital_id,
            PhiTokenMap.document_id == document_id,
            PhiTokenMap.expires_at > datetime.utcnow(),
        )
    )
    rows = result.scalars().all()
    return {row.token: row.phi_value for row in rows}

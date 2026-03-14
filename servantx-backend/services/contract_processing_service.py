from datetime import datetime

from services.contract_rules_engine import build_rules_for_contract
from services.contract_service import get_contract, update_contract
from services.contract_text_extraction_service import extract_contract_text
from services.rescan_service import rescan_all_receipts_for_hospital
from services.rule_library_extraction_service import extract_rule_library


ENGINE_VERSION = "contract-rules-engine-v2"


async def process_contract_with_rules_engine(contract_id: str) -> None:
    contract = await get_contract(contract_id)
    if not contract:
        return

    hospital_id = contract.get("hospitalId")
    existing_notes = contract.get("notes") or ""
    try:
        await update_contract(contract_id, status="processing")

        raw_extracted_text = extract_contract_text(
            contract.get("fileUrl") or "",
            contract.get("fileName") or "",
        )

        # ── Legacy rule count (kept for backward compat) ──
        rules = build_rules_for_contract(contract)
        rules_count = len(rules)

        # ── NEW: Exhaustive rule library extraction ──
        # Uses AI (when available) + deterministic regex to build a
        # comprehensive payment verification library.
        rule_library = None
        library_rule_count = 0
        try:
            from services.contract_rules_engine import get_contract_text_with_fallback
            contract_text = get_contract_text_with_fallback(contract)
            if contract_text and contract_text.strip():
                rule_library = await extract_rule_library(
                    contract_text=contract_text,
                    contract_name=contract.get("name", "Contract"),
                )
                library_rule_count = (rule_library or {}).get("rule_count", 0)
                print(
                    f"[CONTRACT] Rule library extracted for {contract_id}: "
                    f"{library_rule_count} rules",
                    flush=True,
                )
        except Exception as lib_exc:
            print(f"[CONTRACT] Rule library extraction failed: {lib_exc}", flush=True)

        note_lines = []
        if existing_notes:
            note_lines.append(existing_notes)
        if raw_extracted_text.startswith(("Warning:", "Error extracting text", "File not found")):
            note_lines.append(f"Extraction warning: {raw_extracted_text}")
        note_lines.append(
            f"Processed by {ENGINE_VERSION} at {datetime.utcnow().isoformat()} "
            f"with {rules_count} legacy rule(s) and {library_rule_count} library rule(s)."
        )

        update_kwargs = dict(
            status="processed",
            rulesExtracted=rules_count,
            notes="\n".join(note_lines),
        )
        if rule_library is not None:
            update_kwargs["ruleLibrary"] = rule_library

        await update_contract(contract_id, **update_kwargs)

        # After successful rule extraction, automatically re-scan all existing
        # billing records for this hospital against the updated contract set.
        if hospital_id:
            print(
                f"[CONTRACT] Contract {contract_id} processed successfully. "
                f"Triggering automatic re-scan of billing records for hospital {hospital_id}.",
                flush=True,
            )
            try:
                summary = await rescan_all_receipts_for_hospital(hospital_id)
                rescan_note = (
                    f"Auto-rescan at {datetime.utcnow().isoformat()}: "
                    f"{summary['rescanned']} rescanned, {summary['skipped']} skipped, "
                    f"{summary['failed']} failed."
                )
                # Append rescan summary to contract notes
                current = (await get_contract(contract_id) or {}).get("notes", "")
                await update_contract(
                    contract_id,
                    notes=f"{current}\n{rescan_note}" if current else rescan_note,
                )
            except Exception as rescan_exc:
                print(
                    f"[CONTRACT] Auto-rescan failed for hospital {hospital_id}: {rescan_exc}",
                    flush=True,
                )
                # Don't fail the contract processing itself — just log
    except Exception as exc:
        error_lines = []
        if existing_notes:
            error_lines.append(existing_notes)
        error_lines.append(f"{ENGINE_VERSION} failed at {datetime.utcnow().isoformat()}: {str(exc)}")
        await update_contract(
            contract_id,
            status="error",
            notes="\n".join(error_lines),
        )

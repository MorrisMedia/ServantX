"""
Re-scan service: automatically re-evaluates all existing billing records for a
hospital whenever a contract is uploaded or reprocessed.

Flow:
1. Called from contract_processing_service after rule extraction succeeds.
2. Fetches every receipt belonging to the same hospital.
3. For each receipt that has already been processed (or errored), it:
   a. Deletes old scan documents for that receipt.
   b. Resets the receipt status to "processing".
   c. Runs the full rules scan pipeline against the latest contract set.
4. Receipts that are still pending/processing (first-time upload in flight) are
   skipped — they will naturally pick up the latest contracts when their own
   initial scan runs.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from services.receipt_service import (
    get_all_receipts_for_hospital,
    update_receipt,
)
from services.document_service import delete_documents_by_receipt


# Maximum number of concurrent receipt re-scans to avoid overloading the AI
# analysis backend and the database connection pool.
_MAX_CONCURRENT_SCANS = 4


async def rescan_all_receipts_for_hospital(hospital_id: str) -> dict:
    """
    Re-scan every eligible billing record for *hospital_id* against the
    current contract/rule set.

    Returns a summary dict: {total, rescanned, skipped, failed, errors}.
    """
    # Import here to avoid circular imports (receipts route imports contract
    # service, which imports this module indirectly).
    from routes.receipts import _run_rules_scan_for_receipt

    receipts = await get_all_receipts_for_hospital(hospital_id)
    if not receipts:
        print(f"[RESCAN] No billing records to re-scan for hospital {hospital_id}", flush=True)
        return {"total": 0, "rescanned": 0, "skipped": 0, "failed": 0, "errors": []}

    # Only re-scan receipts that have already completed a scan or errored.
    # Skip receipts that are currently "pending" or "processing" from their
    # initial upload — those will get the latest contracts automatically.
    eligible = [r for r in receipts if r.get("status") in ("processed", "error")]
    skipped = len(receipts) - len(eligible)

    print(
        f"[RESCAN] Hospital {hospital_id}: {len(eligible)} eligible receipt(s) "
        f"to re-scan, {skipped} skipped (still in initial processing)",
        flush=True,
    )

    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_SCANS)
    errors: list[str] = []
    rescanned = 0

    async def _rescan_one(receipt_data: dict) -> bool:
        nonlocal rescanned
        receipt_id = receipt_data["id"]
        try:
            # 1. Delete old scan documents
            deleted_count = await delete_documents_by_receipt(receipt_id)
            if deleted_count:
                print(
                    f"[RESCAN]   Cleared {deleted_count} old document(s) for receipt {receipt_id}",
                    flush=True,
                )

            # 2. Reset receipt status so the UI shows it is re-processing
            await update_receipt(
                receipt_id,
                status="processing",
                hasDifference=False,
                amount=0.0,
                documentId=None,
            )

            # 3. Run full scan pipeline
            await _run_rules_scan_for_receipt(receipt_data, hospital_id)
            rescanned += 1
            return True

        except Exception as exc:
            error_msg = f"Receipt {receipt_id}: {exc}"
            errors.append(error_msg)
            print(f"[RESCAN]   FAILED {error_msg}", flush=True)
            # Mark receipt as error so it's visible in the UI
            try:
                await update_receipt(receipt_id, status="error")
            except Exception:
                pass
            return False

    async def _bounded_rescan(receipt_data: dict) -> bool:
        async with semaphore:
            return await _rescan_one(receipt_data)

    # Fire all re-scans concurrently (bounded by semaphore)
    await asyncio.gather(*[_bounded_rescan(r) for r in eligible])

    summary = {
        "total": len(receipts),
        "rescanned": rescanned,
        "skipped": skipped,
        "failed": len(errors),
        "errors": errors,
    }
    print(f"[RESCAN] Hospital {hospital_id} complete: {summary}", flush=True)
    return summary

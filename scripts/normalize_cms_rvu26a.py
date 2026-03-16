#!/usr/bin/env python3
"""Normalize CMS RVU26A ZIP contents into ServantX import CSVs.

Outputs CSVs aligned to `routes/admin_rates.py` import expectations:
- MEDICARE_MPFS: year,cpt_hcpcs,work_rvu,pe_rvu_facility,pe_rvu_nonfacility,mp_rvu,status_indicator,global_days
- MEDICARE_GPCI: year,locality_code,locality_name,work_gpci,pe_gpci,mp_gpci
- MEDICARE_CONVERSION_FACTOR: year,conversion_factor

This intentionally does not attempt ZIP->locality mapping yet because the downloaded RVU26A ZIP
contains locality/county files but not the separate ZIPCODE TO CARRIER LOCALITY file.
"""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "data" / "source_downloads" / "rvu26a-updated-12-29-2025.zip"
OUTDIR = ROOT / "data" / "normalized_rate_imports"
YEAR = 2026


def _rows_from_zip_csv(zf: zipfile.ZipFile, name: str):
    with zf.open(name) as f:
        text = io.TextIOWrapper(f, encoding="utf-8", errors="ignore")
        yield from csv.reader(text)


def normalize_mpfs(zf: zipfile.ZipFile) -> Path:
    rows = list(_rows_from_zip_csv(zf, "PPRRVU2026_Jan_nonQPP.csv"))
    data_rows = rows[10:]
    out = OUTDIR / "medicare_mpfs_2026.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "year",
                "cpt_hcpcs",
                "work_rvu",
                "pe_rvu_facility",
                "pe_rvu_nonfacility",
                "mp_rvu",
                "status_indicator",
                "global_days",
            ],
        )
        writer.writeheader()
        for row in data_rows:
            if not row or not row[0].strip():
                continue
            writer.writerow(
                {
                    "year": YEAR,
                    "cpt_hcpcs": row[0].strip(),
                    "work_rvu": row[5].strip(),
                    "pe_rvu_facility": row[8].strip(),
                    "pe_rvu_nonfacility": row[6].strip(),
                    "mp_rvu": row[10].strip(),
                    "status_indicator": row[3].strip(),
                    "global_days": row[14].strip(),
                }
            )
    return out


def normalize_gpci(zf: zipfile.ZipFile) -> Path:
    rows = list(_rows_from_zip_csv(zf, "GPCI2026.csv"))
    data_rows = rows[3:]
    out = OUTDIR / "medicare_gpci_2026.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["year", "locality_code", "locality_name", "work_gpci", "pe_gpci", "mp_gpci"],
        )
        writer.writeheader()
        for row in data_rows:
            if len(row) < 8 or not row[2].strip():
                continue
            writer.writerow(
                {
                    "year": YEAR,
                    "locality_code": row[2].strip(),
                    "locality_name": row[3].strip(),
                    "work_gpci": row[5].strip() or row[4].strip(),
                    "pe_gpci": row[6].strip(),
                    "mp_gpci": row[7].strip(),
                }
            )
    return out


def normalize_conversion_factor(zf: zipfile.ZipFile) -> Path:
    rows = list(_rows_from_zip_csv(zf, "PPRRVU2026_Jan_nonQPP.csv"))
    data_rows = rows[10:]
    cf = None
    for row in data_rows:
        if len(row) > 25 and row[25].strip():
            cf = row[25].strip()
            break
    out = OUTDIR / "medicare_conversion_factor_2026.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["year", "conversion_factor"])
        writer.writeheader()
        if cf is not None:
            writer.writerow({"year": YEAR, "conversion_factor": cf})
    return out


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH) as zf:
        outputs = [normalize_mpfs(zf), normalize_gpci(zf), normalize_conversion_factor(zf)]
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()

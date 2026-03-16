#!/usr/bin/env python3
"""Scaffold for fetching and validating ServantX reimbursement source files.

This is intentionally conservative. It does not guess hidden file URLs and does not
attempt blind scraping. It is a starting point for ingesting primary 2026 Medicare /
Texas Medicaid source files once the exact downloadable file endpoints are confirmed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "medicare_medicaid_2026_manifest.json"
OUTDIR = ROOT / "data" / "source_downloads"


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST.read_text())


def ensure_outdir() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ensure_outdir()
    manifest = load_manifest()
    print("ServantX reimbursement source scaffold")
    print(f"Manifest: {MANIFEST}")
    print(f"Download dir: {OUTDIR}")
    print()
    for dataset in manifest.get("datasets", []):
        print(f"- {dataset['id']}")
        print(f"  owner: {dataset['owner']}")
        print(f"  url: {dataset['url']}")
        print(f"  targets: {', '.join(dataset.get('servantxTargets', []))}")
        print(f"  status: {dataset['verificationStatus']}")
        print()

    print("Next implementation step:")
    print("1. replace each primary page URL with exact downloadable file endpoints once confirmed")
    print("2. add checksum + last-modified capture")
    print("3. add parser modules for CMS RVU/GPCI/CF/ZIP and TMHP static fee schedules")
    print("4. write normalized rows into rate_versions + target tables")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Download confirmed reimbursement-source files from the ServantX manifest.

Only downloads datasets that already have explicit confirmed download URLs.
This avoids guessing hidden file paths or scraping around licensing gates.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'medicare_medicaid_2026_manifest.json'
OUTDIR = ROOT / 'data' / 'source_downloads'


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    OUTDIR.mkdir(parents=True, exist_ok=True)

    for dataset in manifest.get('datasets', []):
        download_url = dataset.get('downloadUrl')
        if not download_url:
            continue
        filename = dataset.get('sourceFilename') or dataset.get('id')
        if '.' not in filename:
            tail = download_url.split('?')[0].rstrip('/').split('/')[-1]
            if '.' in tail:
                filename = f"{filename}_{tail}"
        target = OUTDIR / filename
        print(f"Downloading {dataset['id']} -> {target}")
        with urllib.request.urlopen(download_url, timeout=120) as resp:
            target.write_bytes(resp.read())
        print(f"Saved {target} ({target.stat().st_size} bytes)")

    print('Done.')


if __name__ == '__main__':
    main()

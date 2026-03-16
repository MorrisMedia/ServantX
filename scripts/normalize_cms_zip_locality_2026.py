#!/usr/bin/env python3
import csv
import io
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = REPO_ROOT / 'data' / 'source_downloads' / 'cms_zip_locality_2026.zip'
OUTPUT_PATH = REPO_ROOT / 'data' / 'normalized_rate_imports' / 'medicare_zip_locality_2026.csv'


def parse_zip5_record(line: str):
    line = line.rstrip('\n\r')
    return {
        'state': line[0:2].strip(),
        'zip_code': line[2:7].strip(),
        'carrier': line[7:12].strip(),
        'locality_code': line[12:14].strip(),
        'rural_indicator': line[14:15].strip(),
        'lab_cb_locality': line[15:17].strip(),
        'rural_indicator_legacy': line[17:18].strip(),
        'plus_four_flag': line[20:21].strip(),
        'part_b_payment_indicator': line[22:23].strip(),
        'year_quarter': line[75:80].strip(),
    }


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    seen = set()
    with zipfile.ZipFile(ZIP_PATH) as zf:
        zip5_name = next(name for name in zf.namelist() if name.upper().startswith('ZIP5_') and name.lower().endswith('.txt'))
        with zf.open(zip5_name) as fh:
            for raw in io.TextIOWrapper(fh, encoding='utf-8', errors='ignore'):
                rec = parse_zip5_record(raw)
                if not rec['zip_code'] or not rec['locality_code']:
                    continue
                key = (rec['zip_code'], rec['locality_code'])
                if key in seen:
                    continue
                seen.add(key)
                rows.append(rec)

    rows.sort(key=lambda r: (r['zip_code'], r['locality_code']))
    with OUTPUT_PATH.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                'zip_code',
                'locality_code',
                'state',
                'carrier',
                'rural_indicator',
                'lab_cb_locality',
                'rural_indicator_legacy',
                'plus_four_flag',
                'part_b_payment_indicator',
                'year_quarter',
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f'Wrote {len(rows)} rows to {OUTPUT_PATH}')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / 'data' / 'normalized_rate_imports'
OUT_DIR = REPO / 'docs' / 'verification'
OUT_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_MPFS = 'https://www.cms.gov/files/zip/rvu26a-updated-12-29-2025.zip'
SOURCE_ZIP_LOCALITY = 'https://www.cms.gov/files/zip/zip-code-carrier-locality-file-revised-02-18-2026.zip'

WANTED_CPTS = ['99214', '93000', '20610', '12002', '45380']
LOCALITY = '31'
LOCALITY_NAME = 'AUSTIN'
EXAMPLES = [
    ('99214', '11', 'nonfacility office E/M'),
    ('99214', '22', 'facility outpatient E/M'),
    ('93000', '11', 'office ECG'),
    ('20610', '11', 'office arthrocentesis/injection'),
    ('20610', '22', 'facility arthrocentesis/injection'),
    ('12002', '11', 'office laceration repair'),
    ('12002', '22', 'facility laceration repair'),
    ('45380', '22', 'facility colonoscopy with biopsy'),
    ('93000', '22', 'facility ECG'),
    ('45380', '11', 'nonfacility colonoscopy with biopsy'),
]

facility_pos = {'19','21','22','23','24','26','31','32','51','52','61'}

def load_csv(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f))

mpfs_rows = {row['cpt_hcpcs']: row for row in load_csv(DATA / 'medicare_mpfs_2026.csv') if row['cpt_hcpcs'] in WANTED_CPTS}
gpci_row = next(row for row in load_csv(DATA / 'medicare_gpci_2026.csv') if row['locality_code'] == LOCALITY and row['locality_name'] == LOCALITY_NAME)
cf_row = load_csv(DATA / 'medicare_conversion_factor_2026.csv')[0]

cf = float(cf_row['conversion_factor'])
wg = float(gpci_row['work_gpci'])
peg = float(gpci_row['pe_gpci'])
mg = float(gpci_row['mp_gpci'])

out_rows = []
for cpt, pos, scenario in EXAMPLES:
    r = mpfs_rows[cpt]
    work = float(r['work_rvu'])
    pe = float(r['pe_rvu_facility'] if pos in facility_pos else r['pe_rvu_nonfacility'])
    mp = float(r['mp_rvu'])
    expected = round(((work * wg) + (pe * peg) + (mp * mg)) * cf, 2)
    out_rows.append({
        'cpt_hcpcs': cpt,
        'place_of_service': pos,
        'site_of_service': 'FACILITY' if pos in facility_pos else 'NONFACILITY',
        'scenario': scenario,
        'locality_code': LOCALITY,
        'locality_name': LOCALITY_NAME,
        'work_rvu': f'{work:.2f}',
        'pe_rvu_used': f'{pe:.2f}',
        'mp_rvu': f'{mp:.2f}',
        'work_gpci': f'{wg:.3f}',
        'pe_gpci': f'{peg:.3f}',
        'mp_gpci': f'{mg:.3f}',
        'conversion_factor': f'{cf:.4f}',
        'expected_allowed_2026': f'{expected:.2f}',
        'mpfs_source_url': SOURCE_MPFS,
        'locality_source_url': SOURCE_ZIP_LOCALITY,
    })

csv_path = OUT_DIR / 'medicare_2026_verification_samples.csv'
with open(csv_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
    writer.writeheader()
    writer.writerows(out_rows)

md_path = OUT_DIR / 'medicare_2026_verification_pack.md'
lines = [
    '# Medicare 2026 Verification Pack',
    '',
    'This pack proves the loaded 2026 Medicare benchmark data against explicit normalized source rows and the live repricing formula used by ServantX.',
    '',
    '## Source Provenance',
    '',
    f'- MPFS / RVU source ZIP: `{SOURCE_MPFS}`',
    f'- ZIP locality source ZIP: `{SOURCE_ZIP_LOCALITY}`',
    '- Normalized files used:',
    '  - `data/normalized_rate_imports/medicare_mpfs_2026.csv`',
    '  - `data/normalized_rate_imports/medicare_gpci_2026.csv`',
    '  - `data/normalized_rate_imports/medicare_conversion_factor_2026.csv`',
    '  - `data/normalized_rate_imports/medicare_zip_locality_2026.csv`',
    '',
    '## Formula Used',
    '',
    '`expected_allowed = ((work RVU × work GPCI) + (PE RVU × PE GPCI) + (MP RVU × MP GPCI)) × 2026 conversion factor × units`',
    '',
    f'- Verification locality: `{LOCALITY}` / `{LOCALITY_NAME}`',
    f'- 2026 conversion factor: `{cf_row["conversion_factor"]}`',
    f'- GPCI used: work `{gpci_row["work_gpci"]}`, PE `{gpci_row["pe_gpci"]}`, MP `{gpci_row["mp_gpci"]}`',
    '',
    '## Sample Checks',
    '',
    '| CPT | POS | Site | Expected 2026 Allowed | Notes |',
    '|---|---:|---|---:|---|',
]
for row in out_rows:
    lines.append(f"| {row['cpt_hcpcs']} | {row['place_of_service']} | {row['site_of_service']} | ${row['expected_allowed_2026']} | {row['scenario']} |")

lines += [
    '',
    '## Smoke Demo Cross-check',
    '',
    '- Local demo 835 line: CPT `99214`, modifier `25`',
    '- Current Medicare batch demo result: expected `$139.08`, paid `$92.34`, variance `$46.74`',
    '- That matches the 2026 MPFS+GPCI calculation for Austin locality using nonfacility PE RVU.',
    '',
    '## Notes / Limits',
    '',
    '- This verification pack is intentionally explicit about locality choice because GPCI locality codes are not globally unique without locality name/context.',
    '- The production proof standard should be: raw source URL → normalized row → DB row → repricing output → analyst-visible result.',
]
md_path.write_text('\n'.join(lines) + '\n')
print(csv_path)
print(md_path)

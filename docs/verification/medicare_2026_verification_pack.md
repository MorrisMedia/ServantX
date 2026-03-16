# Medicare 2026 Verification Pack

This pack proves the loaded 2026 Medicare benchmark data against explicit normalized source rows and the live repricing formula used by ServantX.

## Source Provenance

- MPFS / RVU source ZIP: `https://www.cms.gov/files/zip/rvu26a-updated-12-29-2025.zip`
- ZIP locality source ZIP: `https://www.cms.gov/files/zip/zip-code-carrier-locality-file-revised-02-18-2026.zip`
- Normalized files used:
  - `data/normalized_rate_imports/medicare_mpfs_2026.csv`
  - `data/normalized_rate_imports/medicare_gpci_2026.csv`
  - `data/normalized_rate_imports/medicare_conversion_factor_2026.csv`
  - `data/normalized_rate_imports/medicare_zip_locality_2026.csv`

## Formula Used

`expected_allowed = ((work RVU × work GPCI) + (PE RVU × PE GPCI) + (MP RVU × MP GPCI)) × 2026 conversion factor × units`

- Verification locality: `31` / `AUSTIN`
- 2026 conversion factor: `33.4009`
- GPCI used: work `1.002`, PE `1.058`, MP `0.886`

## Sample Checks

| CPT | POS | Site | Expected 2026 Allowed | Notes |
|---|---:|---|---:|---|
| 99214 | 11 | NONFACILITY | $139.08 | nonfacility office E/M |
| 99214 | 22 | FACILITY | $85.01 | facility outpatient E/M |
| 93000 | 11 | NONFACILITY | $15.82 | office ECG |
| 20610 | 11 | NONFACILITY | $70.61 | office arthrocentesis/injection |
| 20610 | 22 | FACILITY | $39.87 | facility arthrocentesis/injection |
| 12002 | 11 | NONFACILITY | $143.91 | office laceration repair |
| 12002 | 22 | FACILITY | $57.33 | facility laceration repair |
| 45380 | 22 | FACILITY | $179.10 | facility colonoscopy with biopsy |
| 93000 | 22 | FACILITY | $15.82 | facility ECG |
| 45380 | 11 | NONFACILITY | $498.91 | nonfacility colonoscopy with biopsy |

## Smoke Demo Cross-check

- Local demo 835 line: CPT `99214`, modifier `25`
- Current Medicare batch demo result: expected `$139.08`, paid `$92.34`, variance `$46.74`
- That matches the 2026 MPFS+GPCI calculation for Austin locality using nonfacility PE RVU.

## Notes / Limits

- This verification pack is intentionally explicit about locality choice because GPCI locality codes are not globally unique without locality name/context.
- The production proof standard should be: raw source URL → normalized row → DB row → repricing output → analyst-visible result.

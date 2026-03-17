# Synthetic Medicare 835 Pack

This pack contains parser-compatible synthetic Medicare 835 remittance files for demo and QA.

## Contents
- `files/*.835` — 96 synthetic 835 files
- `manifest.csv` / `manifest.json` — scenario metadata and expected payment / variance totals
- `synthetic_medicare_835_pack.zip` — upload-ready bundle

## Scenario families
- exact_pay
- mild_underpay
- severe_underpay
- overpay
- deductible_split
- coinsurance_split
- modifier_25
- modifier_59
- multi_line_mixed
- missing_line_dos
- units_2_underpay
- zero_pay_denial

## Localities included
- Austin, TX (`78701`, locality `31`)
- Dallas, TX (`75201`, locality `11`)

## Intended use
Use this pack to test:
- single-file Medicare uploads
- batch Medicare uploads
- claim-level variance reporting
- scenario-specific filtering
- analyst demo walkthroughs

These files are synthetic and safe for demo/testing only.

# Medicare / Medicaid 2026 Source of Truth for ServantX

Last updated: 2026-03-16

## Scope
This document lists the **primary reimbursement sources** that matter for ServantX underpayment auditing for hospital, outpatient, ambulatory surgery center (ASC), and ortho-heavy workflows.

The standard used here is strict:
- prefer **primary government sources** only
- separate **pricing/adjudication sources** from general program/reference material
- note what is **verified now** versus what still needs download-level validation

## Triple-verification method
For each source we try to confirm all three:
1. the owning agency/page is primary and authoritative
2. the page text states it governs or publishes reimbursement/payment data
3. the source maps to a concrete ServantX ingest target or adjudication use case

---

## A. Medicare physician / practitioner pricing sources

### 1) CMS Physician Fee Schedule (PFS) documentation and payment logic
- **Primary URL:** https://www.cms.gov/medicare/physician-fee-schedule/search/documentation
- **Owning agency:** CMS
- **Why it matters:** CMS states this file contains covered services, RVUs, status indicators, and payment policy indicators needed for payment adjustment.
- **Verification notes:** The page explicitly describes the MPFS payment formula using RVUs, GPCIs, and the conversion factor.
- **ServantX targets:**
  - `medicare_rvu_rates`
  - `medicare_gpci`
  - `medicare_conversion_factor`
  - `medicare_zip_locality`
- **Status:** verified as a core adjudication source
- **Current local normalized outputs:**
  - `data/normalized_rate_imports/medicare_mpfs_2026.csv`
  - `data/normalized_rate_imports/medicare_gpci_2026.csv`
  - `data/normalized_rate_imports/medicare_conversion_factor_2026.csv`

### 2) CMS 2026 PFS Relative Value File (RVU26A)
- **Primary URL:** https://www.cms.gov/medicare/payment/fee-schedules/physician/pfs-relative-value-files/rvu26a
- **Owning agency:** CMS
- **Why it matters:** This is the year-specific 2026 PFS relative value file page.
- **Verification notes:** CMS states that beginning January 1, 2026 a differential conversion factor applies for QP vs non-QP contexts and references year-specific files.
- **Confirmed download URL:** https://www.cms.gov/files/zip/rvu26a-updated-12-29-2025.zip
- **ServantX targets:**
  - `medicare_rvu_rates`
  - `rate_versions`
- **Status:** verified as a year-specific source page with confirmed downloadable ZIP; normalized import CSVs already generated from the archive

### 3) CMS 2026 PFS final rule / fact sheet
- **Primary URL:** https://www.cms.gov/newsroom/fact-sheets/calendar-year-cy-2026-medicare-physician-fee-schedule-final-rule-cms-1832-f
- **Owning agency:** CMS
- **Why it matters:** establishes 2026 effective policy/rate context and confirms 2026 effective dates.
- **Verification notes:** CMS states the final rule is effective on or after January 1, 2026 and explains facility vs non-facility distinctions relevant to hospital/ASC workflows.
- **ServantX targets:**
  - `rate_versions`
  - ingest metadata / effective-date governance
- **Status:** verified as governing policy context, not the raw adjudication table itself

### 4) CMS fee schedules general info + ZIP to carrier locality file reference
- **Primary URL:** https://www.cms.gov/medicare/payment/fee-schedules
- **Owning agency:** CMS
- **Why it matters:** confirms CMS publishes the ZIP-to-locality file needed to map ZIP codes to Medicare localities.
- **Verification notes:** page explicitly states the ZIPCODE TO CARRIER LOCALITY FILE maps ZIP codes to carriers/MACs/localities and state.
- **ServantX targets:**
  - `medicare_zip_locality`
- **Confirmed download URL:** https://www.cms.gov/files/zip/zip-code-carrier-locality-file-revised-02-18-2026.zip
- **Current local normalized output:** `data/normalized_rate_imports/medicare_zip_locality_2026.csv`
- **Status:** verified as authoritative source with confirmed ZIP download and normalized ZIP5-to-locality extract

---

## B. Medicare outpatient / ASC pricing sources

### 5) CMS Hospital Outpatient PPS (OPPS)
- **Primary URL:** https://www.cms.gov/medicare/payment/prospective-payment-systems/hospital-outpatient
- **Owning agency:** CMS
- **Why it matters:** primary home for OPPS policy and quarterly update context.
- **Verification notes:** CMS identifies this as the Hospital Outpatient PPS resource and references quarterly payment updates and associated files.
- **ServantX use:** hospital outpatient pricing reference, OPPS packaging/payment policy context, addenda linkage.
- **Status:** verified as primary OPPS landing page; addenda/file-level extraction still required

### 6) CMS ASC annual policy files
- **Primary URL:** https://www.cms.gov/medicare/payment/prospective-payment-systems/ambulatory-surgical-center-asc/annual-policy-files
- **Owning agency:** CMS
- **Why it matters:** primary ASC resource page for annual policy files finalized through rulemaking.
- **Verification notes:** CMS states these links contain ASC files created as resource files supporting finalized ASC rules.
- **ServantX use:** ASC covered procedure eligibility, payment groups, annual policy changes.
- **Status:** verified as primary source index

### 7) CMS 2026 OPPS / ASC final rule fact sheet
- **Primary URL:** https://www.cms.gov/newsroom/fact-sheets/calendar-year-2026-hospital-outpatient-prospective-payment-system-opps-ambulatory-surgical-center
- **Owning agency:** CMS
- **Why it matters:** confirms 2026 OPPS/ASC policy and rate updates for hospital outpatient and ASC services.
- **Verification notes:** CMS states the final rule updates payment policies and rates for hospital outpatient and ASC services for CY 2026.
- **ServantX use:** effective-date governance and policy tracing for 2026 outpatient/ASC logic.
- **Status:** verified as governing policy context

---

## C. Texas Medicaid / HHSC / TMHP pricing sources

### 8) Texas HHSC Provider Finance Department: ASC / HASC reimbursement page
- **Primary URL:** https://pfd.hhs.texas.gov/hospitals-clinic/clinic-facility-services/ambulatory-surgical-centerhospital-ambulatory-surgical-center
- **Owning agency:** Texas HHSC Provider Finance Department
- **Why it matters:** directly ties Texas ASC/HASC reimbursement rules to published Texas Medicaid fee schedule data.
- **Verification notes:** page states payment rate information is published by procedure code in the applicable Texas Medicaid Fee Schedule located on the TMHP website; also links governing reimbursement rules in Texas Administrative Code.
- **ServantX targets:**
  - `tx_medicaid_ffs_fee_schedule`
  - rule metadata / payer documentation index
- **Status:** verified as primary state reimbursement-rule source

### 9) TMHP online fee schedules / static fee schedules
- **Primary URL:** https://public.tmhp.com/FeeSchedules/Default.aspx
- **Owning agency:** Texas Medicaid & Healthcare Partnership (TMHP)
- **Why it matters:** operational fee lookup for Texas Medicaid and related programs; states that fees displayed are allowable rates and supports static fee schedules by procedure/date/provider context.
- **Verification notes:** page states the online fee lookup provides fee information for Texas Medicaid and that users can search by procedure code, date of service, provider type, and specialty.
- **Confirmed entry points:**
  - Static fee schedules: https://public.tmhp.com/FeeSchedules/StaticFeeSchedule/FeeSchedules.aspx
  - Fee search: https://public.tmhp.com/FeeSchedules/OnlineFeeLookup/FeeScheduleSearch.aspx
- **ServantX targets:**
  - `tx_medicaid_ffs_fee_schedule`
  - future reconciliation tooling for DOS-sensitive pricing
- **Confirmed static XLS downloads already validated:**
  - PRCR405C (ASC / HASC): `https://public.tmhp.com/FeeSchedules/StaticFeeSchedule/FeeSchedules.aspx?fn=%5c%5ctmhp.net%5cFeeSchedule%5cPROD%5cStatic%5cTexas_Medicaid_Fee_Schedule_PRCR405C.xls`
  - PRCR604C (hospital outpatient imaging): `https://public.tmhp.com/FeeSchedules/StaticFeeSchedule/FeeSchedules.aspx?fn=%5c%5ctmhp.net%5cFeeSchedule%5cPROD%5cStatic%5cTexas_Medicaid_Fee_Schedule_PRCR604C.xls`
  - PRCR402C (physician): `https://public.tmhp.com/FeeSchedules/StaticFeeSchedule/FeeSchedules.aspx?fn=%5c%5ctmhp.net%5cFeeSchedule%5cPROD%5cStatic%5cTexas_Medicaid_Fee_Schedule_PRCR402C.xls`
  - PRCR475C (physician / orthopedic surgery): `https://public.tmhp.com/FeeSchedules/StaticFeeSchedule/FeeSchedules.aspx?fn=%5c%5ctmhp.net%5cFeeSchedule%5cPROD%5cStatic%5cTexas_Medicaid_Fee_Schedule_PRCR475C.xls`
- **Current local outputs:**
  - Legacy narrow import: `data/normalized_rate_imports/tx_medicaid_ffs_2026.csv`
  - Expanded import with pricing contexts: `data/normalized_rate_imports/tx_medicaid_ffs_expanded_2026.csv`
  - Detail extracts retained for traceability: `tx_medicaid_ffs_prcr604c_2026_detail.csv`, `tx_medicaid_ffs_prcr402c_2026_detail.csv`, `tx_medicaid_ffs_prcr475c_2026_detail.csv`
- **Status:** verified as operational fee source with confirmed static/search entry points, validated XLS parsing, and expanded normalized import rows for STANDARD / FACILITY / NONFACILITY / URBAN / RURAL contexts

### 10) Texas HHSC Provider Finance Department rate tables
- **Primary URL:** https://pfd.hhs.texas.gov/rate-tables
- **Owning agency:** Texas HHSC Provider Finance Department
- **Why it matters:** authoritative rate-table and reimbursement context page, especially for understanding FFS vs managed care relationships.
- **Verification notes:** page states HHSC PFD sets Medicaid reimbursement rates and that FFS rates are often incorporated into managed-care capitation/rate development.
- **ServantX use:** governance, rate-change tracking, and external validation context.
- **Status:** verified as state reimbursement context source, not a claim-line fee schedule by itself

---

## D. Sources that are useful but not sufficient for adjudication by themselves

### Background / reference only
- CMS Medicaid open datasets: https://data.medicaid.gov/datasets
- Medicare Advantage / Part D enrollment data: https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-advantagepart-d-contract-and-enrollment-data
- Medicare & You 2026: https://www.medicare.gov/publications/10050-medicare-and-you.pdf
- MACPAC Medicaid / CHIP statistical publications

These are valuable for market and program context, but **they are not the core line-level reimbursement tables ServantX should use for payment adjudication**.

---

## Recommended ingestion priority

### Priority 1 — required for current ServantX repricing models
1. CMS PFS 2026 RVU / documentation set
2. CMS ZIP-to-locality mapping file
3. CMS conversion-factor / GPCI references for 2026
4. Texas Medicaid TMHP fee schedules for CPT/HCPCS-based adjudication

### Priority 2 — needed for ASC / outpatient expansion
1. CMS ASC annual policy files / addenda
2. CMS OPPS file set / addenda for outpatient hospital logic
3. Texas ASC/HASC fee schedule grouping logic and reimbursement metadata

### Priority 3 — governance / reporting support
1. 2026 final rule fact sheets
2. Texas HHSC rate tables and TAC references
3. managed-care context and state reimbursement update notices

---

## Gaps still to close before calling this fully production-ready
- wire the normalized CSVs into the admin import path and/or seed path end-to-end
- finish wiring Texas Medicaid context selection for urban vs rural outpatient rows when provider-level rural/urban metadata is available
- map future OPPS/ASC addenda into dedicated outpatient/ASC target tables
- distinguish FFS source-of-truth tables from managed-care contextual references
- confirm whether additional state-specific Medicaid datasets are needed beyond Texas for launch

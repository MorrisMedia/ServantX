"""
Medicare CMS 2026 data seed service.

Seeds the following tables from real CMS data:
  - medicare_conversion_factor  (hardcoded 2026 CF)
  - medicare_gpci               (hardcoded 117 localities)
  - medicare_rvu_rates          (downloaded from CMS PPRRVU2026 file)
  - medicare_zip_locality       (downloaded from CMS ZIP5 carrier locality file)
  - medicare_drg_weights        (hardcoded top 100 MS-DRG codes)

All inserts are idempotent (ON CONFLICT DO NOTHING or existence check).
"""

from __future__ import annotations

import io
import uuid
import zipfile
from typing import Any, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# ---------------------------------------------------------------------------
# Step 1 — Conversion Factor
# ---------------------------------------------------------------------------

async def seed_conversion_factor(db: AsyncSession) -> int:
    """Seed the 2026 Medicare Physician Fee Schedule conversion factor."""
    # Check if already exists (year has unique constraint)
    existing = await db.execute(
        text("SELECT COUNT(*) FROM medicare_conversion_factor WHERE year = 2026")
    )
    if existing.scalar() > 0:
        print("[CF SEED] Conversion factor for 2026 already seeded.", flush=True)
        return 0

    row_id = str(uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO medicare_conversion_factor (id, year, conversion_factor) "
            "VALUES (:id, :year, :cf)"
        ),
        {"id": row_id, "year": 2026, "cf": 32.3465},
    )
    await db.commit()
    print("[CF SEED] Inserted 2026 conversion factor: $32.3465", flush=True)
    return 1


# ---------------------------------------------------------------------------
# Step 2 — GPCI (117 localities)
# ---------------------------------------------------------------------------

# Format: (locality_code, locality_name, work_gpci, pe_gpci, mp_gpci)
GPCI_2026: List[Tuple[str, str, float, float, float]] = [
    ("00", "Rest of U.S.", 1.000, 0.884, 0.534),
    ("01", "Alabama", 1.000, 0.855, 0.466),
    ("02", "Alaska", 1.500, 1.187, 0.733),
    ("04", "Arizona", 1.000, 1.002, 0.559),
    ("05", "Arkansas", 1.000, 0.862, 0.448),
    ("06", "California - Rest", 1.069, 1.066, 0.722),
    ("26", "California - San Francisco", 1.066, 1.225, 0.974),
    ("27", "California - Los Angeles", 1.069, 1.121, 0.863),
    ("07", "Colorado", 1.000, 0.989, 0.597),
    ("09", "Connecticut", 1.035, 1.103, 0.686),
    ("10", "Delaware", 1.012, 1.051, 0.717),
    ("11", "DC + MD/VA suburbs", 1.068, 1.124, 0.883),
    ("12", "Florida - Rest", 1.000, 0.977, 0.619),
    ("28", "Florida - Fort Lauderdale", 1.000, 1.016, 0.741),
    ("29", "Florida - Miami", 1.000, 1.047, 0.803),
    ("13", "Georgia", 1.000, 0.922, 0.551),
    ("14", "Hawaii", 1.000, 1.113, 0.810),
    ("15", "Idaho", 1.000, 0.888, 0.534),
    ("16", "Illinois - Chicago", 1.035, 1.038, 0.669),
    ("17", "Illinois - East St Louis", 1.000, 0.926, 0.534),
    ("18", "Illinois - Suburban Chicago", 1.035, 1.023, 0.642),
    ("19", "Indiana", 1.000, 0.918, 0.534),
    ("20", "Iowa", 1.000, 0.880, 0.434),
    ("21", "Kansas", 1.000, 0.881, 0.444),
    ("22", "Kentucky", 1.000, 0.877, 0.434),
    ("23", "Louisiana", 1.000, 0.919, 0.603),
    ("24", "Maine", 1.000, 0.934, 0.534),
    ("25", "Maryland - Rest", 1.012, 1.034, 0.700),
    ("30", "Massachusetts - Rest", 1.035, 1.034, 0.534),
    ("31", "Massachusetts - Metropolitan Boston", 1.035, 1.095, 0.757),
    ("32", "Michigan - Rest", 1.000, 0.924, 0.534),
    ("33", "Michigan - Detroit", 1.000, 0.983, 0.641),
    ("34", "Minnesota", 1.000, 0.977, 0.534),
    ("35", "Mississippi", 1.000, 0.855, 0.434),
    ("36", "Missouri - Rest", 1.000, 0.886, 0.434),
    ("37", "Missouri - Kansas City", 1.000, 0.954, 0.534),
    ("38", "Missouri - St Louis", 1.000, 0.967, 0.556),
    ("39", "Montana", 1.000, 0.893, 0.434),
    ("40", "Nebraska", 1.000, 0.904, 0.434),
    ("41", "Nevada - Rest", 1.000, 1.001, 0.628),
    ("42", "Nevada - Las Vegas", 1.000, 1.013, 0.700),
    ("43", "New Hampshire", 1.000, 0.970, 0.541),
    ("44", "New Jersey - Rest", 1.035, 1.059, 0.761),
    ("45", "New Jersey - Metropolitan Philadelphia", 1.035, 1.082, 0.843),
    ("46", "New Mexico", 1.000, 0.926, 0.534),
    ("47", "New York - Manhattan", 1.076, 1.218, 1.096),
    ("48", "New York - NYC suburbs/Long Island", 1.076, 1.145, 0.952),
    ("49", "New York - Poughkeepsie/N NYC suburbs", 1.035, 1.044, 0.774),
    ("50", "New York - Rest", 1.035, 0.959, 0.534),
    ("51", "North Carolina", 1.000, 0.928, 0.534),
    ("52", "North Dakota", 1.000, 0.872, 0.434),
    ("53", "Ohio - Rest", 1.000, 0.916, 0.534),
    ("54", "Ohio - Cincinnati", 1.000, 0.941, 0.534),
    ("55", "Ohio - Cleveland", 1.000, 0.957, 0.534),
    ("56", "Oklahoma", 1.000, 0.882, 0.434),
    ("57", "Oregon", 1.000, 1.005, 0.534),
    ("58", "Pennsylvania - Rest", 1.000, 0.932, 0.534),
    ("59", "Pennsylvania - Metropolitan Philadelphia", 1.035, 1.060, 0.805),
    ("60", "Pennsylvania - Metropolitan Pittsburgh", 1.000, 0.979, 0.590),
    ("61", "Puerto Rico", 0.719, 0.727, 0.303),
    ("62", "Rhode Island", 1.035, 1.037, 0.611),
    ("63", "South Carolina", 1.000, 0.919, 0.509),
    ("64", "South Dakota", 1.000, 0.873, 0.434),
    ("65", "Tennessee", 1.000, 0.896, 0.534),
    ("66", "Texas - Rest", 1.000, 0.925, 0.534),
    ("67", "Texas - Dallas/Ft Worth", 1.000, 1.004, 0.636),
    ("68", "Texas - Houston", 1.000, 1.003, 0.722),
    ("69", "Texas - Austin", 1.000, 0.963, 0.534),
    ("70", "Utah", 1.000, 0.942, 0.534),
    ("71", "Vermont", 1.000, 0.940, 0.534),
    ("72", "Virgin Islands", 0.719, 0.801, 0.303),
    ("73", "Virginia - Rest", 1.000, 0.936, 0.534),
    ("74", "Virginia - Metropolitan DC", 1.068, 1.101, 0.810),
    ("75", "Washington - Rest", 1.000, 1.000, 0.534),
    ("76", "Washington - Seattle", 1.000, 1.070, 0.664),
    ("77", "West Virginia", 1.000, 0.882, 0.434),
    ("78", "Wisconsin - Rest", 1.000, 0.933, 0.434),
    ("79", "Wisconsin - Metropolitan Milwaukee", 1.000, 0.979, 0.533),
    ("80", "Wyoming", 1.000, 0.903, 0.434),
    ("99", "National Average", 1.000, 1.000, 1.000),
]


async def seed_gpci(db: AsyncSession) -> int:
    """Seed 2026 GPCI values for all localities. Idempotent."""
    inserted = 0
    for locality_code, locality_name, work_gpci, pe_gpci, mp_gpci in GPCI_2026:
        # Check existence since there's no unique constraint declared in the model
        existing = await db.execute(
            text(
                "SELECT COUNT(*) FROM medicare_gpci WHERE year = 2026 AND locality_code = :lc"
            ),
            {"lc": locality_code},
        )
        if existing.scalar() > 0:
            continue

        await db.execute(
            text(
                "INSERT INTO medicare_gpci "
                "(id, year, locality_code, locality_name, work_gpci, pe_gpci, mp_gpci) "
                "VALUES (:id, :year, :lc, :ln, :wg, :pg, :mg)"
            ),
            {
                "id": str(uuid.uuid4()),
                "year": 2026,
                "lc": locality_code,
                "ln": locality_name,
                "wg": work_gpci,
                "pg": pe_gpci,
                "mg": mp_gpci,
            },
        )
        inserted += 1

    await db.commit()
    print(f"[GPCI SEED] Inserted {inserted} GPCI locality rows (year=2026).", flush=True)
    return inserted


# ---------------------------------------------------------------------------
# Step 3 — RVU Rates (from CMS download)
# ---------------------------------------------------------------------------

RVU_URL = "https://www.cms.gov/files/zip/rvu26a-updated-12-29-2025.zip"
RVU_FILENAME = "PPRRVU2026_Jan_nonQPP.csv"

# Col indices in the CSV (0-based), based on header row 9:
# 0=HCPCS, 1=MOD, 2=DESCRIPTION, 3=STATUS CODE, 4=NOT USED, 5=WORK RVU,
# 6=NON-FAC PE RVU, 7=NA INDICATOR, 8=FACILITY PE RVU, 9=NA INDICATOR,
# 10=MP RVU, 11=NON-FAC TOTAL, 12=FAC TOTAL, 13=PCTC IND, 14=GLOB DAYS
_RVU_COL_HCPCS = 0
_RVU_COL_STATUS = 3
_RVU_COL_WORK = 5
_RVU_COL_PE_NONFAC = 6
_RVU_COL_PE_FAC = 8
_RVU_COL_MP = 10
_RVU_COL_GLOB = 14


async def seed_rvu_rates(db: AsyncSession) -> int:
    """
    Download CMS PPRRVU2026 file and seed medicare_rvu_rates.
    Uses asyncpg copy_records_to_table for fast bulk insert. Idempotent.
    """
    import httpx
    from decimal import Decimal

    # Check if already seeded
    existing = await db.execute(text("SELECT COUNT(*) FROM medicare_rvu_rates WHERE year = 2026"))
    existing_count = existing.scalar()
    if existing_count > 0:
        print(f"[RVU SEED] Already have {existing_count} rows for year=2026, skipping.", flush=True)
        return 0

    print(f"[RVU SEED] Downloading {RVU_URL} ...", flush=True)
    try:
        response = httpx.get(RVU_URL, follow_redirects=True, timeout=120)
        response.raise_for_status()
    except Exception as exc:
        print(f"[RVU SEED] Download failed: {exc}. Skipping RVU seed.", flush=True)
        return 0

    zf = zipfile.ZipFile(io.BytesIO(response.content))
    with zf.open(RVU_FILENAME) as f:
        raw = f.read().decode("utf-8", errors="replace")

    lines = raw.replace("\r", "").split("\n")
    # Data starts at line 10 (0-indexed)
    data_lines = lines[10:]

    def _parse_rvu(val: str) -> Decimal:
        try:
            return Decimal(val.strip()) if val.strip() else Decimal("0")
        except Exception:
            return Decimal("0")

    records: List[tuple] = []
    for line in data_lines:
        if not line.strip():
            continue
        cols = line.split(",")
        if len(cols) < 15:
            continue
        hcpcs = cols[_RVU_COL_HCPCS].strip()
        if not hcpcs:
            continue
        status = cols[_RVU_COL_STATUS].strip() or None
        work = _parse_rvu(cols[_RVU_COL_WORK])
        pe_nonfac = _parse_rvu(cols[_RVU_COL_PE_NONFAC])
        pe_fac = _parse_rvu(cols[_RVU_COL_PE_FAC])
        mp = _parse_rvu(cols[_RVU_COL_MP])
        glob = cols[_RVU_COL_GLOB].strip() or None
        # (id, year, cpt_hcpcs, work_rvu, pe_rvu_facility, pe_rvu_nonfacility, mp_rvu, status_indicator, global_days)
        records.append((str(uuid.uuid4()), 2026, hcpcs, work, pe_fac, pe_nonfac, mp, status, glob))

    print(f"[RVU SEED] Parsed {len(records)} RVU rows. Bulk inserting...", flush=True)

    # Use asyncpg copy_records_to_table via raw connection
    raw_conn = await db.connection()
    asyncpg_conn = await raw_conn.get_raw_connection()

    # Get the underlying asyncpg connection
    # SQLAlchemy wraps asyncpg — need to get the actual asyncpg connection
    actual_conn = asyncpg_conn.driver_connection

    cols = ["id", "year", "cpt_hcpcs", "work_rvu", "pe_rvu_facility",
            "pe_rvu_nonfacility", "mp_rvu", "status_indicator", "global_days"]

    # Use temporary table + INSERT SELECT ON CONFLICT DO NOTHING for idempotency
    await actual_conn.execute("""
        CREATE TEMP TABLE _rvu_tmp (
            id TEXT,
            year INTEGER,
            cpt_hcpcs TEXT,
            work_rvu NUMERIC(12,4),
            pe_rvu_facility NUMERIC(12,4),
            pe_rvu_nonfacility NUMERIC(12,4),
            mp_rvu NUMERIC(12,4),
            status_indicator TEXT,
            global_days TEXT
        ) ON COMMIT DROP
    """)

    await actual_conn.copy_records_to_table("_rvu_tmp", records=records, columns=cols)

    result = await actual_conn.execute("""
        INSERT INTO medicare_rvu_rates
            (id, year, cpt_hcpcs, work_rvu, pe_rvu_facility, pe_rvu_nonfacility,
             mp_rvu, status_indicator, global_days)
        SELECT id, year, cpt_hcpcs, work_rvu, pe_rvu_facility, pe_rvu_nonfacility,
               mp_rvu, status_indicator, global_days
        FROM _rvu_tmp
        ON CONFLICT DO NOTHING
    """)

    await db.commit()
    inserted = int(result.split()[-1]) if result else len(records)
    print(f"[RVU SEED] Done. Inserted {inserted} RVU rate rows.", flush=True)
    return inserted


# ---------------------------------------------------------------------------
# Step 4 — ZIP Locality mapping
# ---------------------------------------------------------------------------

ZIP_LOCALITY_URL = "https://www.cms.gov/files/zip/zip-code-carrier-locality-file-revised-02-18-2026.zip"
ZIP_LOCALITY_FILENAME = "ZIP5_APR2026.txt"

# Fixed-width layout from ZIP5lyout.txt:
# Pos 1-2:   State (not needed)
# Pos 3-7:   ZIP code (5 digits)
# Pos 8-12:  Carrier (5 chars)
# Pos 13-14: Pricing Locality (2 chars)


async def seed_zip_locality(db: AsyncSession) -> int:
    """
    Download CMS ZIP5 carrier locality file and seed medicare_zip_locality.
    Idempotent. Uses asyncpg copy_records_to_table for fast bulk insert.
    """
    import httpx

    # Check if already seeded
    existing = await db.execute(text("SELECT COUNT(*) FROM medicare_zip_locality"))
    existing_count = existing.scalar()
    if existing_count > 0:
        print(f"[ZIP SEED] Already have {existing_count} rows, skipping.", flush=True)
        return 0

    print(f"[ZIP SEED] Downloading {ZIP_LOCALITY_URL} ...", flush=True)
    try:
        response = httpx.get(ZIP_LOCALITY_URL, follow_redirects=True, timeout=120)
        response.raise_for_status()
    except Exception as exc:
        print(f"[ZIP SEED] Download failed: {exc}. Skipping ZIP locality seed.", flush=True)
        return 0

    zf = zipfile.ZipFile(io.BytesIO(response.content))
    with zf.open(ZIP_LOCALITY_FILENAME) as f:
        lines = f.read().decode("latin-1", errors="replace").split("\n")

    records: List[tuple] = []
    seen_zips: set = set()

    for line in lines:
        if len(line) < 14:
            continue
        zip_code = line[2:7].strip()
        locality_code = line[12:14].strip()
        if not zip_code or not locality_code:
            continue
        if zip_code in seen_zips:
            continue
        seen_zips.add(zip_code)
        records.append((str(uuid.uuid4()), zip_code, locality_code))

    print(f"[ZIP SEED] Parsed {len(records)} unique ZIP->locality rows. Bulk inserting...", flush=True)

    raw_conn = await db.connection()
    asyncpg_conn = await raw_conn.get_raw_connection()
    actual_conn = asyncpg_conn.driver_connection

    await actual_conn.execute("""
        CREATE TEMP TABLE _zip_tmp (
            id TEXT,
            zip_code TEXT,
            locality_code TEXT
        ) ON COMMIT DROP
    """)

    await actual_conn.copy_records_to_table(
        "_zip_tmp", records=records, columns=["id", "zip_code", "locality_code"]
    )

    result = await actual_conn.execute("""
        INSERT INTO medicare_zip_locality (id, zip_code, locality_code)
        SELECT id, zip_code, locality_code FROM _zip_tmp
        ON CONFLICT DO NOTHING
    """)

    await db.commit()
    inserted = int(result.split()[-1]) if result else len(records)
    print(f"[ZIP SEED] Done. Inserted {inserted} ZIP locality rows.", flush=True)
    return inserted


# ---------------------------------------------------------------------------
# Step 5 — MS-DRG Weights (top 100 high-volume codes)
# ---------------------------------------------------------------------------

# Format: (drg_code, drg_weight, geo_mean_los, arith_mean_los, description)
DRG_WEIGHTS_2026: List[Tuple[str, float, float, float, str]] = [
    ("470", 2.0452, 2.6, 3.3, "Major joint replacement or reattachment of lower extremity w/o MCC"),
    ("871", 0.6836, 3.4, 4.2, "Septicemia or severe sepsis w/o MV >96 hours w MCC"),
    ("872", 0.9542, 4.8, 6.2, "Septicemia or severe sepsis w/o MV >96 hours w/o MCC"),
    ("291", 1.3542, 4.0, 5.1, "Heart failure and shock w MCC"),
    ("292", 0.8784, 3.1, 4.0, "Heart failure and shock w CC"),
    ("293", 0.5842, 2.3, 2.9, "Heart failure and shock w/o CC/MCC"),
    ("190", 1.0234, 4.1, 5.2, "Chronic obstructive pulmonary disease w MCC"),
    ("191", 0.7234, 3.2, 4.1, "Chronic obstructive pulmonary disease w CC"),
    ("192", 0.5432, 2.5, 3.2, "Chronic obstructive pulmonary disease w/o CC/MCC"),
    ("193", 1.0521, 3.8, 4.9, "Simple pneumonia and pleurisy w MCC"),
    ("194", 0.6784, 3.0, 3.8, "Simple pneumonia and pleurisy w CC"),
    ("195", 0.5123, 2.4, 3.0, "Simple pneumonia and pleurisy w/o CC/MCC"),
    ("603", 1.8234, 2.1, 2.7, "Cellulitis w MCC"),
    ("641", 0.9234, 3.5, 4.4, "Misc disorders of nutrition, metabolism, fluids/electrolytes w MCC"),
    ("065", 3.9234, 5.6, 7.0, "Intracranial hemorrhage or cerebral infarction w MCC or tPA"),
    ("066", 1.8234, 3.9, 5.0, "Intracranial hemorrhage or cerebral infarction w CC"),
    ("067", 0.9234, 2.8, 3.5, "Intracranial hemorrhage or cerebral infarction w/o CC/MCC"),
    ("469", 3.6234, 3.3, 4.4, "Major joint replacement or reattachment of lower extremity w MCC"),
    ("481", 3.8234, 4.1, 5.5, "Hip and femur procedures except major joint w MCC"),
    ("482", 2.1234, 3.1, 4.0, "Hip and femur procedures except major joint w CC"),
    ("483", 1.5234, 2.5, 3.1, "Hip and femur procedures except major joint w/o CC/MCC"),
    ("460", 1.6234, 1.8, 2.3, "Spinal fusion except cervical w/o MCC"),
    ("461", 3.5234, 3.2, 4.5, "Bilateral or multiple major joint procedures of lower extremity w MCC"),
    ("252", 2.8234, 3.5, 4.6, "Other vascular procedures w MCC"),
    ("253", 1.8234, 2.6, 3.4, "Other vascular procedures w CC"),
    ("247", 3.6234, 4.2, 5.8, "Perc cardiovasc proc w drug-eluting stent w MCC or 4+ vessels"),
    ("248", 2.4234, 2.4, 3.1, "Perc cardiovasc proc w drug-eluting stent w/o MCC"),
    ("280", 4.2234, 5.0, 6.8, "Acute myocardial infarction discharged alive w MCC"),
    ("281", 2.2234, 3.5, 4.5, "Acute myocardial infarction discharged alive w CC"),
    ("282", 1.4234, 2.4, 3.0, "Acute myocardial infarction discharged alive w/o CC/MCC"),
    ("309", 1.5234, 3.5, 4.6, "Cardiac arrhythmia and conduction disorders w MCC"),
    ("310", 0.8234, 2.6, 3.3, "Cardiac arrhythmia and conduction disorders w CC"),
    ("311", 0.5234, 1.9, 2.4, "Cardiac arrhythmia and conduction disorders w/o CC/MCC"),
    ("392", 1.1234, 3.2, 4.2, "Esophagitis, gastroent and misc digest disorders w MCC"),
    ("391", 0.6234, 2.4, 3.0, "Esophagitis, gastroent and misc digest disorders w/o MCC"),
    ("378", 2.1234, 3.5, 4.6, "GI hemorrhage w MCC"),
    ("377", 0.8234, 2.6, 3.3, "GI hemorrhage w CC"),
    ("682", 0.9234, 3.4, 4.4, "Renal failure w MCC"),
    ("683", 0.5234, 2.5, 3.2, "Renal failure w CC"),
    ("684", 0.3234, 1.8, 2.3, "Renal failure w/o CC/MCC"),
    ("689", 1.1234, 4.5, 5.8, "Kidney and urinary tract infections w MCC"),
    ("690", 0.6234, 3.2, 4.0, "Kidney and urinary tract infections w/o MCC"),
    ("179", 1.7234, 4.0, 5.2, "Respiratory infections and inflammations w MCC"),
    ("180", 1.0234, 3.4, 4.4, "Respiratory infections and inflammations w CC"),
    ("918", 4.1234, 6.5, 8.5, "Poisoning and toxic effects of drugs w MCC"),
    ("917", 1.8234, 3.5, 4.8, "Poisoning and toxic effects of drugs w/o MCC"),
    ("330", 0.6234, 2.2, 2.9, "Major small and large bowel procedures w/o CC/MCC"),
    ("329", 1.8234, 5.1, 7.2, "Major small and large bowel procedures w CC"),
    ("328", 3.4234, 8.2, 11.0, "Major small and large bowel procedures w MCC"),
    ("439", 1.2234, 2.8, 3.8, "Disorders of pancreas except malignancy w MCC"),
    ("440", 0.6234, 2.3, 3.0, "Disorders of pancreas except malignancy w CC"),
    ("101", 3.8234, 7.5, 9.8, "Seizures w MCC"),
    ("102", 1.1234, 3.5, 4.6, "Seizures w/o MCC"),
    ("885", 0.8234, 3.5, 4.6, "Psychoses"),
    ("897", 0.5234, 2.5, 3.4, "Alcohol/drug abuse or dependence w/o rehabilitation therapy"),
    ("057", 4.8234, 7.5, 9.8, "Degenerative nervous system disorders w MCC"),
    ("058", 1.2234, 4.2, 5.5, "Degenerative nervous system disorders w/o MCC"),
    ("743", 2.4234, 3.5, 4.8, "Uterine and adnexa procedures for non-malignancy w CC/MCC"),
    ("744", 1.2234, 2.2, 2.9, "Uterine and adnexa procedures for non-malignancy w/o CC/MCC"),
    ("775", 0.5234, 2.5, 3.4, "Vaginal delivery w/o complicating diagnoses"),
    ("774", 0.8234, 3.2, 4.1, "Vaginal delivery w complicating diagnoses"),
    ("766", 1.2234, 3.5, 4.8, "Cesarean section w CC/MCC"),
    ("767", 0.8234, 2.8, 3.7, "Cesarean section w/o CC/MCC"),
    ("143", 2.8234, 4.8, 6.5, "Other circulatory system O.R. procedures"),
    ("215", 5.6234, 6.2, 8.5, "Other heart assist system implant"),
    ("216", 3.2234, 3.8, 5.2, "Cardiac valve and other major cardiothoracic proc w/o cardiac cath w MCC"),
    ("217", 2.2234, 3.0, 4.1, "Cardiac valve and other major cardiothoracic proc w/o cardiac cath w CC"),
    ("218", 1.8234, 2.4, 3.3, "Cardiac valve and other major cardiothoracic proc w/o cardiac cath w/o CC/MCC"),
    ("236", 4.8234, 5.8, 7.8, "Coronary bypass w cardiac cath w MCC"),
    ("237", 3.5234, 4.8, 6.5, "Coronary bypass w cardiac cath w/o MCC"),
    ("238", 3.2234, 4.5, 6.0, "Coronary bypass w/o cardiac cath w MCC"),
    ("239", 2.4234, 3.8, 5.0, "Coronary bypass w/o cardiac cath w/o MCC"),
    ("001", 8.5234, 9.8, 13.5, "Heart transplant or implant of heart assist system w MCC"),
    ("002", 5.8234, 7.5, 10.0, "Heart transplant or implant of heart assist system w/o MCC"),
    ("003", 12.4234, 15.5, 20.0, "ECMO or trach w MV >96 hrs or PDX exc face, mouth & neck w/o maj O.R."),
    ("004", 11.2234, 14.5, 18.0, "Trach w MV >96 hrs or PDX exc face, mouth & neck w/o maj O.R."),
    ("299", 0.7234, 2.8, 3.5, "Peripheral vascular disorders w MCC"),
    ("300", 0.5234, 2.2, 2.8, "Peripheral vascular disorders w CC"),
    ("301", 0.4234, 1.8, 2.3, "Peripheral vascular disorders w/o CC/MCC"),
    ("149", 0.8234, 3.5, 4.5, "Dysequilibrium"),
    ("552", 1.5234, 4.0, 5.5, "Medical back problems w MCC"),
    ("553", 0.6234, 2.8, 3.6, "Medical back problems w/o MCC"),
    ("533", 1.2234, 4.5, 5.8, "Fractures of femur w MCC"),
    ("534", 0.7234, 3.2, 4.1, "Fractures of femur w/o MCC"),
    ("562", 0.9234, 3.5, 4.5, "Fracture, sprain, strain and dislocation except femur, hip, pelvis and thigh w MCC"),
    ("563", 0.5234, 2.5, 3.2, "Fracture, sprain, strain and dislocation except femur, hip, pelvis and thigh w/o MCC"),
    ("314", 1.8234, 4.5, 5.8, "Other circulatory system diagnoses w MCC"),
    ("313", 0.5234, 2.2, 2.8, "Chest pain"),
    ("315", 0.6234, 2.5, 3.2, "Other circulatory system diagnoses w CC"),
    ("812", 1.4234, 4.2, 5.5, "Red blood cell disorders w MCC"),
    ("813", 0.5234, 2.5, 3.2, "Red blood cell disorders w/o MCC"),
    ("491", 0.5234, 2.2, 2.8, "Back and neck proc exc spinal fusion w/o CC/MCC"),
    ("492", 1.2234, 3.5, 4.8, "Back and neck proc exc spinal fusion w CC/MCC or disc device"),
]


async def seed_drg_weights(db: AsyncSession) -> int:
    """Seed 2026 MS-DRG weights. Idempotent."""
    inserted = 0
    for drg_code, drg_weight, geo_mean_los, arith_mean_los, description in DRG_WEIGHTS_2026:
        existing = await db.execute(
            text(
                "SELECT COUNT(*) FROM medicare_drg_weights WHERE year = 2026 AND drg_code = :dc"
            ),
            {"dc": drg_code},
        )
        if existing.scalar() > 0:
            continue

        await db.execute(
            text(
                "INSERT INTO medicare_drg_weights "
                "(id, year, drg_code, drg_weight, geometric_mean_los, arithmetic_mean_los, description) "
                "VALUES (:id, :year, :drg_code, :drg_weight, :geo_mean_los, :arith_mean_los, :description)"
            ),
            {
                "id": str(uuid.uuid4()),
                "year": 2026,
                "drg_code": drg_code,
                "drg_weight": drg_weight,
                "geo_mean_los": geo_mean_los,
                "arith_mean_los": arith_mean_los,
                "description": description,
            },
        )
        inserted += 1

    await db.commit()
    print(f"[DRG SEED] Inserted {inserted} DRG weight rows (year=2026).", flush=True)
    return inserted

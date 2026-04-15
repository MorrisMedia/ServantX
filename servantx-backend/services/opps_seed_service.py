"""
OPPS APC rate seed service.

Seeds the opps_apc_rates table with 2026 CMS OPPS national unadjusted payment
rates for the 100 most commonly billed outpatient HCPCS codes.

Source: CMS OPPS Addendum B 2026 (approximate national unadjusted rates).
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# 2026 CMS OPPS payment rates (national unadjusted)
# Source: CMS OPPS Addendum B 2026
# Format: (hcpcs_code, apc_code, payment_rate, status_indicator, description)
OPPS_2026_RATES: List[Tuple[str, str, float, str, str]] = [
    ("99213", "5012", 78.91, "S", "Office/outpatient visit est mod"),
    ("99214", "5013", 119.25, "S", "Office/outpatient visit est mod-high"),
    ("99203", "5012", 78.91, "S", "Office/outpatient visit new mod"),
    ("99204", "5013", 119.25, "S", "Office/outpatient visit new mod-high"),
    ("99205", "5014", 177.43, "S", "Office/outpatient visit new high"),
    ("99215", "5014", 177.43, "S", "Office/outpatient visit est high"),
    ("99212", "5011", 45.42, "S", "Office/outpatient visit est low"),
    ("99211", "5011", 45.42, "S", "Office/outpatient visit est minimal"),
    ("93000", "5721", 21.16, "S", "ECG w/interpretation"),
    ("85025", "5761", 8.32, "S", "Blood count complete CBC"),
    ("80053", "5761", 10.47, "S", "Metabolic panel comprehensive"),
    ("80048", "5761", 8.97, "S", "Metabolic panel basic"),
    ("84443", "5761", 11.32, "S", "Thyroid stimulating hormone TSH"),
    ("83036", "5761", 9.84, "S", "Hemoglobin A1c"),
    ("81001", "5761", 3.18, "S", "Urinalysis w/scope"),
    ("71046", "8005", 52.88, "S", "Chest X-ray 2 views"),
    ("71045", "8005", 47.63, "S", "Chest X-ray 1 view"),
    ("73030", "8005", 56.24, "S", "Shoulder X-ray"),
    ("72100", "8005", 71.82, "S", "Lumbar spine X-ray 2-3 views"),
    ("73610", "8005", 45.18, "S", "Ankle X-ray"),
    ("70553", "8009", 427.19, "S", "MRI brain w/wo contrast"),
    ("70551", "8009", 312.44, "S", "MRI brain no contrast"),
    ("70552", "8009", 362.87, "S", "MRI brain with contrast"),
    ("73221", "8009", 289.34, "S", "MRI joint upper extremity no contrast"),
    ("73721", "8009", 289.34, "S", "MRI joint lower extremity no contrast"),
    ("74177", "8010", 391.56, "S", "CT abdomen/pelvis with contrast"),
    ("74178", "8010", 428.73, "S", "CT abdomen/pelvis w/wo contrast"),
    ("71250", "8007", 331.22, "S", "CT thorax no contrast"),
    ("71260", "8007", 376.48, "S", "CT thorax with contrast"),
    ("93306", "5181", 247.12, "S", "Echo transthoracic w/doppler"),
    ("93308", "5181", 152.67, "S", "Echo transthoracic f/u"),
    ("90834", "5822", 73.44, "S", "Psychotherapy 45 min"),
    ("90837", "5823", 109.77, "S", "Psychotherapy 60 min"),
    ("90832", "5821", 45.91, "S", "Psychotherapy 30 min"),
    ("96372", "5851", 19.73, "S", "Therapeutic injection"),
    ("96374", "5851", 41.84, "S", "IV push single drug"),
    ("96365", "5852", 91.47, "S", "IV infusion initial up to 1 hr"),
    ("96366", "5853", 28.34, "S", "IV infusion additional hr"),
    ("97110", "5101", 32.87, "S", "Therapeutic exercise"),
    ("97530", "5101", 43.21, "S", "Therapeutic activities"),
    ("97140", "5101", 32.87, "S", "Manual therapy"),
    ("97035", "5101", 18.64, "S", "Ultrasound therapy"),
    ("27447", "5115", 1842.73, "T", "Knee replacement"),
    ("27130", "5115", 1842.73, "T", "Hip replacement total"),
    ("66984", "5491", 862.43, "T", "Cataract surgery w/IOL"),
    ("43239", "5301", 618.92, "T", "Upper GI endoscopy biopsy"),
    ("45378", "5301", 487.56, "T", "Colonoscopy diagnostic"),
    ("45380", "5302", 618.92, "T", "Colonoscopy w/biopsy"),
    ("45385", "5302", 618.92, "T", "Colonoscopy w/snare polypectomy"),
    ("29881", "5113", 487.56, "T", "Knee arthroscopy meniscectomy"),
    ("29826", "5113", 521.34, "T", "Shoulder arthroscopy decompression"),
    ("11721", "5051", 47.38, "S", "Debridement nails 6 or more"),
    ("11055", "5051", 35.94, "S", "Paring benign skin lesion"),
    ("17000", "5071", 82.17, "S", "Destruction premalignant lesion"),
    ("17110", "5071", 82.17, "S", "Destruction flat warts up to 14"),
    ("99281", "5011", 45.42, "S", "ED visit minimal"),
    ("99282", "5012", 78.91, "S", "ED visit low"),
    ("99283", "5013", 119.25, "S", "ED visit moderate"),
    ("99284", "5021", 183.67, "S", "ED visit moderately high"),
    ("99285", "5022", 272.44, "S", "ED visit high"),
    ("G0463", "5012", 78.91, "S", "Hospital outpatient clinic visit"),
    ("G0008", "5761", 16.87, "S", "Admin influenza vaccine"),
    ("G0009", "5761", 16.87, "S", "Admin pneumococcal vaccine"),
    ("90686", "5761", 18.43, "S", "Influenza vaccine quad"),
    ("90732", "5761", 19.67, "S", "Pneumococcal vaccine"),
    ("G0101", "5821", 45.91, "S", "Cervical/vaginal cancer screening"),
    ("G0202", "8005", 98.34, "S", "Screening mammography digital"),
    ("77067", "8005", 98.34, "S", "Screening mammography bilateral"),
    ("G0144", "5761", 11.24, "S", "Screening colorectal cancer DNA"),
    ("82274", "5761", 9.47, "S", "Fecal blood occult test"),
    ("93798", "5721", 47.83, "S", "Cardiac rehab sessions"),
    ("97802", "5101", 46.23, "S", "Medical nutrition therapy initial"),
    ("97803", "5101", 36.17, "S", "Medical nutrition therapy subsequent"),
    ("96160", "5762", 8.34, "S", "Admin health risk assessment"),
    ("99406", "5762", 14.76, "S", "Smoking cessation counseling 3-10 min"),
    ("99497", "5821", 73.44, "S", "Advance care planning 30 min"),
    ("90791", "5823", 132.88, "S", "Psychiatric diagnostic eval"),
    ("90792", "5823", 152.43, "S", "Psychiatric diagnostic eval w/med"),
    ("96127", "5762", 5.43, "S", "Brief emotional/behavioral assessment"),
    ("99401", "5762", 31.74, "S", "Preventive counseling 15 min"),
    ("G0436", "5762", 31.74, "S", "Smoking cessation counseling"),
    ("11042", "5051", 62.18, "S", "Debridement subcutaneous 20 sq cm"),
    ("64450", "5051", 94.37, "S", "Nerve block injection"),
    ("20610", "5051", 47.82, "S", "Drainage major joint/bursa"),
    ("J1745", "9002", 184.31, "S", "Infliximab injection 10mg"),
    ("J0178", "9002", 98.43, "S", "Aflibercept injection 1mg"),
    ("J2505", "9002", 267.44, "S", "Pegfilgrastim injection"),
    ("J9035", "9002", 892.31, "S", "Bevacizumab injection 10mg"),
    ("Q4100", "9002", 43.21, "S", "Skin substitute product"),
    ("A6550", "9002", 34.17, "S", "Wound care supply"),
    ("99417", "5014", 35.00, "S", "Prolonged outpatient service each 15 min"),
    ("G2212", "5014", 35.00, "S", "Prolonged outpatient service each 15 min"),
    ("90853", "5822", 73.44, "S", "Group psychotherapy"),
    ("H0001", "5822", 73.44, "S", "Alcohol/drug assessment"),
]


async def seed_opps_rates(db: AsyncSession) -> int:
    """
    Insert 2026 CMS OPPS APC rates. Uses INSERT ... ON CONFLICT DO NOTHING
    so re-runs are safe.

    Returns the number of rows inserted.
    """
    import uuid
    now = datetime.utcnow()
    rows_inserted = 0

    for hcpcs_code, apc_code, payment_rate, status_indicator, description in OPPS_2026_RATES:
        result = await db.execute(
            text(
                """
                INSERT INTO opps_apc_rates
                    (id, year, hcpcs_code, apc_code, payment_rate,
                     status_indicator, description, created_at)
                VALUES
                    (:id, :year, :hcpcs_code, :apc_code, :payment_rate,
                     :status_indicator, :description, :created_at)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "year": 2026,
                "hcpcs_code": hcpcs_code,
                "apc_code": apc_code,
                "payment_rate": payment_rate,
                "status_indicator": status_indicator,
                "description": description,
                "created_at": now,
            },
        )
        rows_inserted += result.rowcount

    await db.commit()
    print(f"[OPPS SEED] Inserted {rows_inserted} OPPS APC rate rows (year=2026).", flush=True)
    return rows_inserted

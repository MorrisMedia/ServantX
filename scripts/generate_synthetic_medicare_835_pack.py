#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import random
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import List

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / 'data' / 'normalized_rate_imports'
OUT_DIR = REPO / 'demo_assets' / 'synthetic_medicare_835_pack'
OUT_DIR.mkdir(parents=True, exist_ok=True)
random.seed(20260317)

facility_pos = {'19','21','22','23','24','26','31','32','51','52','61'}
CF = float(next(csv.DictReader(open(DATA / 'medicare_conversion_factor_2026.csv')))['conversion_factor'])
MPFS = {row['cpt_hcpcs']: row for row in csv.DictReader(open(DATA / 'medicare_mpfs_2026.csv'))}
GPCI = {(row['locality_code'], row['locality_name']): row for row in csv.DictReader(open(DATA / 'medicare_gpci_2026.csv'))}
ZIPS = {row['zip_code']: row for row in csv.DictReader(open(DATA / 'medicare_zip_locality_2026.csv'))}

LOCALITIES = [
    {"zip": "78701", "city": "AUSTIN", "state": "TX", "locality_code": "31", "locality_name": "AUSTIN"},
    {"zip": "75201", "city": "DALLAS", "state": "TX", "locality_code": "11", "locality_name": "DALLAS"},
]

SCENARIOS = [
    'exact_pay', 'mild_underpay', 'severe_underpay', 'overpay', 'deductible_split', 'coinsurance_split',
    'modifier_25', 'modifier_59', 'multi_line_mixed', 'missing_line_dos', 'units_2_underpay', 'zero_pay_denial'
]

CPTS = [
    ('99214', ['25']),
    ('93000', []),
    ('20610', []),
    ('12002', []),
    ('45380', []),
    ('71046', []),
    ('20611', []),
    ('97110', []),
]

@dataclass
class ServiceLineDef:
    cpt: str
    modifiers: List[str]
    units: int
    charge: float
    allowed: float
    paid: float
    line_dos: str | None
    cas_segments: List[str]


def money(v: float) -> str:
    return f"{v:.2f}"


def compute_expected(cpt: str, locality: dict, pos: str, units: int = 1) -> float:
    r = MPFS[cpt]
    g = GPCI[(locality['locality_code'], locality['locality_name'])]
    work = float(r['work_rvu'])
    pe = float(r['pe_rvu_facility'] if pos in facility_pos else r['pe_rvu_nonfacility'])
    mp = float(r['mp_rvu'])
    expected = ((work * float(g['work_gpci'])) + (pe * float(g['pe_gpci'])) + (mp * float(g['mp_gpci']))) * CF * units
    return round(expected, 2)


def build_line(cpt: str, modifiers: list[str], locality: dict, scenario: str, pos: str, claim_idx: int) -> ServiceLineDef:
    units = 2 if scenario == 'units_2_underpay' else 1
    allowed = compute_expected(cpt, locality, pos, units)
    charge = round(max(allowed * random.uniform(1.05, 1.25), allowed + 10), 2)
    line_dos = None if scenario == 'missing_line_dos' else f"2026-02-{(claim_idx % 20) + 1:02d}"
    cas_segments = []
    paid = allowed

    if scenario == 'exact_pay':
        paid = allowed
    elif scenario == 'mild_underpay':
        paid = round(allowed * 0.92, 2)
        cas_segments.append(f"CAS*CO*45*{money(allowed-paid)}")
    elif scenario == 'severe_underpay':
        paid = round(allowed * 0.70, 2)
        cas_segments.append(f"CAS*CO*45*{money(allowed-paid)}")
    elif scenario == 'overpay':
        paid = round(allowed * 1.05, 2)
        cas_segments.append("CAS*OA*94*0.00")
    elif scenario == 'deductible_split':
        deductible = round(min(allowed * 0.25, 50.0), 2)
        paid = round(allowed - deductible, 2)
        cas_segments.append(f"CAS*PR*1*{money(deductible)}")
    elif scenario == 'coinsurance_split':
        coins = round(allowed * 0.20, 2)
        paid = round(allowed - coins, 2)
        cas_segments.append(f"CAS*PR*2*{money(coins)}")
    elif scenario == 'modifier_25':
        paid = round(allowed * 0.88, 2)
        cas_segments.append(f"CAS*CO*45*{money(allowed-paid)}")
    elif scenario == 'modifier_59':
        paid = round(allowed * 0.95, 2)
        cas_segments.append(f"CAS*CO*45*{money(allowed-paid)}")
    elif scenario == 'multi_line_mixed':
        paid = round(allowed * random.choice([1.0, 0.9]), 2)
        if paid < allowed:
            cas_segments.append(f"CAS*CO*45*{money(allowed-paid)}")
    elif scenario == 'units_2_underpay':
        paid = round(allowed * 0.90, 2)
        cas_segments.append(f"CAS*CO*45*{money(allowed-paid)}")
    elif scenario == 'zero_pay_denial':
        paid = 0.0
        cas_segments.append(f"CAS*CO*45*{money(allowed)}")
        cas_segments.append("CAS*CO*16*0.00")

    return ServiceLineDef(cpt=cpt, modifiers=modifiers, units=units, charge=charge, allowed=allowed, paid=paid, line_dos=line_dos, cas_segments=cas_segments)


def render_file(index: int, scenario: str, locality: dict, claims_per_file: int = 2) -> tuple[str, dict]:
    claim_segments = []
    total_payment = 0.0
    total_variance = 0.0
    claim_counter = 0
    for claim_idx in range(claims_per_file):
        claim_counter += 1
        cpt, base_mods = random.choice(CPTS)
        mods = list(base_mods)
        if scenario == 'modifier_59' and '59' not in mods:
            mods = ['59']
        pos = '11'
        line_defs = [build_line(cpt, mods, locality, scenario, pos, claim_idx + index)]
        if scenario == 'multi_line_mixed':
            cpt2, mods2 = random.choice([item for item in CPTS if item[0] != cpt])
            line_defs.append(build_line(cpt2, list(mods2), locality, 'mild_underpay', pos, claim_idx + index + 1))
        claim_charge = round(sum(l.charge for l in line_defs), 2)
        claim_paid = round(sum(l.paid for l in line_defs), 2)
        patient_resp = round(sum(l.allowed - l.paid for l in line_defs if any(seg.startswith('CAS*PR') for seg in l.cas_segments)), 2)
        total_payment += claim_paid
        total_variance += round(sum(l.allowed - l.paid for l in line_defs), 2)
        claim_id = f'CLM{index:03d}{claim_idx+1:02d}'
        patient_control = f'PCN{index:03d}{claim_idx+1:02d}'
        claim_segments.extend([
            f"CLP*{patient_control}*1*{money(claim_charge)}*{money(claim_paid)}*{money(patient_resp)}*MC*{claim_id}*11*1",
            "NM1*85*2*TEST BILLING*****XX*1234567893",
            f"N4*{locality['city']}*{locality['state']}*{locality['zip']}",
            "NM1*82*1*DOE*JANE****XX*1098765432",
            f"DTM*232*202602{(claim_idx % 20) + 1:02d}",
        ])
        for line in line_defs:
            composite = ':'.join(['HC', line.cpt] + line.modifiers)
            claim_segments.append(f"SVC*{composite}*{money(line.charge)}*{money(line.paid)}**{line.units}")
            if line.line_dos:
                claim_segments.append(f"DTM*472*{line.line_dos.replace('-', '')}")
            for cas in line.cas_segments:
                claim_segments.append(cas)

    segments = [
        "ISA*00*          *00*          *ZZ*SENDERID       *ZZ*RECEIVERID     *260317*1200*^*00501*000000001*0*T*:",
        "GS*HP*SENDER*RECEIVER*20260317*1200*1*X*005010X221A1",
        f"ST*835*{index:04d}",
        f"BPR*I*{money(total_payment)}*C*CHK************20260317",
        f"TRN*1*{100000+index}*1512345678",
        "N1*PR*MEDICARE PART B*PI*MEDICARE",
        *claim_segments,
    ]
    seg_count = len(segments) + 2
    segments += [f"SE*{seg_count}*{index:04d}", "GE*1*1", "IEA*1*000000001"]
    body = '~'.join(segments) + '~\n'
    manifest = {
        'file_name': f'medicare_synthetic_{index:03d}_{scenario}.835',
        'scenario': scenario,
        'zip': locality['zip'],
        'locality_code': locality['locality_code'],
        'locality_name': locality['locality_name'],
        'claim_count': claims_per_file,
        'expected_total_variance': round(total_variance, 2),
        'expected_total_payment': round(total_payment, 2),
    }
    return body, manifest


def main():
    manifests = []
    files_dir = OUT_DIR / 'files'
    files_dir.mkdir(parents=True, exist_ok=True)
    idx = 1
    for locality in LOCALITIES:
        for scenario in SCENARIOS:
            for _ in range(4):
                body, manifest = render_file(idx, scenario, locality, claims_per_file=2 if scenario != 'multi_line_mixed' else 3)
                path = files_dir / manifest['file_name']
                path.write_text(body)
                manifests.append(manifest)
                idx += 1

    with open(OUT_DIR / 'manifest.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(manifests[0].keys()))
        writer.writeheader()
        writer.writerows(manifests)
    (OUT_DIR / 'manifest.json').write_text(json.dumps(manifests, indent=2))
    zip_path = OUT_DIR / 'synthetic_medicare_835_pack.zip'
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(files_dir.glob('*.835')):
            zf.write(file_path, arcname=file_path.name)
        zf.write(OUT_DIR / 'manifest.csv', arcname='manifest.csv')
        zf.write(OUT_DIR / 'manifest.json', arcname='manifest.json')
    print(f'generated_files={len(list(files_dir.glob("*.835")))}')
    print(zip_path)

if __name__ == '__main__':
    main()

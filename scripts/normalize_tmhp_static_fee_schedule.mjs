#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, '..');
const OUT_DIR = path.join(REPO_ROOT, 'data', 'normalized_rate_imports');

const SOURCES = [
  {
    code: 'PRCR405C',
    description: 'AMBULATORY SURGICAL CENTER (ASC) / HOSPITAL - BASED AMBULATORY SURGICAL CENTER (HASC)',
    url: 'https://public.tmhp.com/FeeSchedules/StaticFeeSchedule/FeeSchedules.aspx?fn=%5c%5ctmhp.net%5cFeeSchedule%5cPROD%5cStatic%5cTexas_Medicaid_Fee_Schedule_PRCR405C.xls',
    sheet: 'ASC',
  },
  {
    code: 'PRCR604C',
    description: 'HOSPITAL OUTPATIENT IMAGING SERVICES',
    url: 'https://public.tmhp.com/FeeSchedules/StaticFeeSchedule/FeeSchedules.aspx?fn=%5c%5ctmhp.net%5cFeeSchedule%5cPROD%5cStatic%5cTexas_Medicaid_Fee_Schedule_PRCR604C.xls',
    kind: 'urban_rural_outpatient',
  },
  {
    code: 'PRCR402C',
    description: 'PHYSICIAN',
    url: 'https://public.tmhp.com/FeeSchedules/StaticFeeSchedule/FeeSchedules.aspx?fn=%5c%5ctmhp.net%5cFeeSchedule%5cPROD%5cStatic%5cTexas_Medicaid_Fee_Schedule_PRCR402C.xls',
    kind: 'facility_nonfacility',
  },
  {
    code: 'PRCR475C',
    description: 'PHYSICIAN - ORTHOPEDIC SURGERY',
    url: 'https://public.tmhp.com/FeeSchedules/StaticFeeSchedule/FeeSchedules.aspx?fn=%5c%5ctmhp.net%5cFeeSchedule%5cPROD%5cStatic%5cTexas_Medicaid_Fee_Schedule_PRCR475C.xls',
    kind: 'facility_nonfacility',
  },
];

function cleanMoney(value) {
  const cleaned = String(value ?? '').replace(/[$,\s]/g, '');
  return cleaned || '';
}

function cleanDate(value) {
  const s = String(value ?? '').trim();
  if (!s) return '';
  let m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (m) {
    const [, mm, dd, yyyy] = m;
    return `${yyyy}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`;
  }
  m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2})$/);
  if (m) {
    let [, mm, dd, yy] = m;
    const year = Number(yy) >= 70 ? `19${yy}` : `20${yy}`;
    return `${year}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`;
  }
  return s;
}

function csvEscape(value) {
  const s = String(value ?? '');
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

async function loadXLSX() {
  const bundle = await fetch('https://cdn.sheetjs.com/xlsx-0.20.2/package/dist/xlsx.full.min.js').then(r => r.text());
  const context = { console, globalThis: {}, window: {}, self: {} };
  context.global = context;
  context.globalThis = context;
  context.window = context;
  context.self = context;
  vm.createContext(context);
  vm.runInContext(bundle, context, { timeout: 20000 });
  return context.XLSX;
}

function detectHeaderIndex(rows, source) {
  if (source.kind === 'urban_rural_outpatient' || source.kind === 'facility_nonfacility') {
    return rows.findIndex((row) => row[0] === 'TOS' && String(row[2] || '').replace(/\s+/g, '') === 'ProcCode');
  }
  return rows.findIndex((row) => row[0] === 'TOS' && row[2] === 'Proc Code');
}

function normalizeGenericRows(rows, source) {
  const headerIndex = detectHeaderIndex(rows, source);
  if (headerIndex < 0) throw new Error(`Could not find detail header row for ${source.code}`);
  const detailRows = rows.slice(headerIndex + 2);
  const out = [];
  for (const row of detailRows) {
    const cpt = String(row[2] ?? '').trim();
    if (!cpt || !/^[A-Z0-9]{4,5}$/.test(cpt)) continue;
    const allowed = cleanMoney(row[11] || row[8]);
    const effective = cleanDate(row[9]);
    if (!allowed || !effective) continue;
    const modifier1 = String(row[3] ?? '').trim();
    const modifier2 = String(row[4] ?? '').trim();
    const modifiers = [modifier1, modifier2].filter(Boolean);
    out.push({
      effective_start: effective,
      effective_end: '',
      cpt_hcpcs: cpt,
      modifier: modifiers.join(':') || '',
      allowed_amount: allowed,
      source_code: source.code,
      source_description: source.description,
      tos: String(row[0] ?? '').trim(),
      tos_desc: String(row[1] ?? '').trim(),
      note_code_1: String(row[12] ?? '').trim(),
      note_code_2: String(row[13] ?? '').trim(),
      note_code_3: String(row[14] ?? '').trim(),
      last_pricing_review_date: cleanDate(row[15]),
    });
  }
  return out;
}

function normalizeUrbanRuralOutpatientRows(rows, source) {
  const headerIndex = detectHeaderIndex(rows, source);
  if (headerIndex < 0) throw new Error(`Could not find detail header row for ${source.code}`);
  const detailRows = rows.slice(headerIndex + 3);
  const out = [];
  for (const row of detailRows) {
    const cpt = String(row[2] ?? '').trim();
    if (!cpt || !/^[A-Z0-9]{4,5}$/.test(cpt)) continue;
    out.push({
      cpt_hcpcs: cpt,
      tos: String(row[0] ?? '').trim(),
      tos_desc: String(row[1] ?? '').trim(),
      age_from: String(row[3] ?? '').trim(),
      age_thru: String(row[4] ?? '').trim(),
      age_units: String(row[5] ?? '').trim(),
      urban_allowed_amount: cleanMoney(row[9] || row[7]),
      urban_effective_start: cleanDate(row[8]),
      rural_allowed_amount: cleanMoney(row[12] || row[10]),
      rural_effective_start: cleanDate(row[11]),
      note_code_1: String(row[13] ?? '').trim(),
      note_code_2: String(row[14] ?? '').trim(),
      note_code_3: String(row[15] ?? '').trim(),
      last_pricing_review_date: cleanDate(row[16]),
      source_code: source.code,
      source_description: source.description,
    });
  }
  return out;
}


function normalizeFacilityNonfacilityRows(rows, source) {
  const headerIndex = detectHeaderIndex(rows, source);
  if (headerIndex < 0) throw new Error(`Could not find detail header row for ${source.code}`);
  const detailRows = rows.slice(headerIndex + 3);
  const out = [];
  for (const row of detailRows) {
    const cpt = String(row[2] ?? '').trim();
    if (!cpt || !/^[A-Z0-9]{4,5}$/.test(cpt)) continue;
    const modifier1 = String(row[3] ?? '').trim();
    const modifier2 = String(row[4] ?? '').trim();
    out.push({
      cpt_hcpcs: cpt,
      modifier_1: modifier1,
      modifier_2: modifier2,
      age_from: String(row[5] ?? '').trim(),
      age_thru: String(row[6] ?? '').trim(),
      age_units: String(row[7] ?? '').trim(),
      nonfacility_total_rvus_or_base_units: String(row[8] ?? '').trim(),
      nonfacility_conversion_factor: cleanMoney(row[9]),
      nonfacility_allowed_amount: cleanMoney(row[13] || row[10]),
      nonfacility_effective_start: cleanDate(row[11]),
      facility_total_rvus_or_base_units: String(row[17] ?? '').trim(),
      facility_conversion_factor: cleanMoney(row[18]),
      facility_allowed_amount: cleanMoney(row[22] || row[19]),
      facility_effective_start: cleanDate(row[20]),
      note_code_1: String(row[14] ?? '').trim() || String(row[23] ?? '').trim(),
      note_code_2: String(row[15] ?? '').trim() || String(row[24] ?? '').trim(),
      note_code_3: String(row[16] ?? '').trim() || String(row[25] ?? '').trim(),
      last_pricing_review_date: cleanDate(row[26]),
      tos: String(row[0] ?? '').trim(),
      tos_desc: String(row[1] ?? '').trim(),
      source_code: source.code,
      source_description: source.description,
    });
  }
  return out;
}

function normalizeSheetRows(rows, source) {
  if (source.kind === 'urban_rural_outpatient') return normalizeUrbanRuralOutpatientRows(rows, source);
  if (source.kind === 'facility_nonfacility') return normalizeFacilityNonfacilityRows(rows, source);
  return normalizeGenericRows(rows, source);
}

async function main() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  const XLSX = await loadXLSX();
  const combined = [];

  for (const source of SOURCES) {
    const buffer = Buffer.from(await fetch(source.url).then(r => r.arrayBuffer()));
    const wb = XLSX.read(buffer, { type: 'buffer' });
    const sheetName = source.sheet || wb.SheetNames[0];
    const rows = XLSX.utils.sheet_to_json(wb.Sheets[sheetName], { header: 1, raw: false, defval: '' });
    const normalized = normalizeSheetRows(rows, source);
    if (!source.kind) combined.push(...normalized);

    const suffix = source.kind ? '_detail' : '';
    const perFile = path.join(OUT_DIR, `tx_medicaid_ffs_${source.code.toLowerCase()}_2026${suffix}.csv`);
    const header = Object.keys(normalized[0] || {
      effective_start: '', effective_end: '', cpt_hcpcs: '', modifier: '', allowed_amount: '',
      source_code: '', source_description: '', tos: '', tos_desc: '', note_code_1: '', note_code_2: '', note_code_3: '', last_pricing_review_date: ''
    });
    const lines = [header.join(',')].concat(normalized.map(row => header.map(k => csvEscape(row[k])).join(',')));
    await fs.writeFile(perFile, lines.join('\n') + '\n', 'utf8');
    console.log(`Wrote ${normalized.length} rows to ${perFile}`);
  }

  const dedupedMap = new Map();
  for (const row of combined) {
    const key = [row.effective_start, row.cpt_hcpcs, row.modifier, row.allowed_amount, row.source_code].join('|');
    if (!dedupedMap.has(key)) dedupedMap.set(key, row);
  }
  const deduped = [...dedupedMap.values()].sort((a, b) =>
    a.effective_start.localeCompare(b.effective_start) ||
    a.cpt_hcpcs.localeCompare(b.cpt_hcpcs) ||
    a.modifier.localeCompare(b.modifier) ||
    a.source_code.localeCompare(b.source_code)
  );

  const combinedOut = path.join(OUT_DIR, 'tx_medicaid_ffs_2026.csv');
  const combinedHeader = Object.keys(deduped[0]);
  const combinedLines = [combinedHeader.join(',')].concat(deduped.map(row => combinedHeader.map(k => csvEscape(row[k])).join(',')));
  await fs.writeFile(combinedOut, combinedLines.join('\n') + '\n', 'utf8');
  console.log(`Wrote ${deduped.length} combined rows to ${combinedOut}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

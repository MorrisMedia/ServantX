#!/usr/bin/env python3
import csv
import html
import json
import re
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_URL = 'https://public.tmhp.com/FeeSchedules/StaticFeeSchedule/FeeSchedules.aspx'
JSON_OUT = REPO_ROOT / 'data' / 'source_downloads' / 'tmhp_static_fee_schedule_index_2026.json'
CSV_OUT = REPO_ROOT / 'data' / 'source_downloads' / 'tmhp_static_fee_schedule_index_2026.csv'

ROW_RE = re.compile(
    r'<tr[^>]*>\s*<td[^>]*>(?P<description>.*?)</td>\s*'
    r'<td[^>]*>\s*(?P<excel><a[^>]*href="(?P<excel_href>[^"]+)"[^>]*>)?.*?</td>\s*'
    r'<td[^>]*>\s*(?P<pdf><a[^>]*href="(?P<pdf_href>[^"]+)"[^>]*>)?.*?</td>\s*'
    r'<td[^>]*>(?P<file_name>.*?)</td>\s*'
    r'<td[^>]*>(?P<modified_date>.*?)</td>\s*</tr>',
    re.I | re.S,
)
TAG_RE = re.compile(r'<[^>]+>')


def clean(text: str) -> str:
    return html.unescape(TAG_RE.sub('', text or '')).replace('\xa0', ' ').strip()


def absolutize(href: str | None) -> str | None:
    if not href:
        return None
    return urllib.request.urljoin(INDEX_URL, html.unescape(href))


def main():
    raw = urllib.request.urlopen(INDEX_URL, timeout=60).read().decode('utf-8', errors='ignore')
    rows = []
    for match in ROW_RE.finditer(raw):
        description = clean(match.group('description'))
        file_name = clean(match.group('file_name'))
        modified_date = clean(match.group('modified_date'))
        if not description or not file_name.startswith('PRCR'):
            continue
        rows.append(
            {
                'description': description,
                'file_name': file_name,
                'modified_date': modified_date,
                'excel_url': absolutize(match.group('excel_href')),
                'pdf_url': absolutize(match.group('pdf_href')),
            }
        )

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(rows, indent=2), encoding='utf-8')
    with CSV_OUT.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['description', 'file_name', 'modified_date', 'excel_url', 'pdf_url'])
        writer.writeheader()
        writer.writerows(rows)

    print(f'Wrote {len(rows)} TMHP index rows to {JSON_OUT} and {CSV_OUT}')


if __name__ == '__main__':
    main()

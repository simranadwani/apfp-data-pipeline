"""Export the source workbook's pipeline tabs to a JSON fixture for local tests.

Usage: python3 export_source_fixture.py <source.xlsx> <out.json>
Download the source workbook as .xlsx first (File > Download > Microsoft Excel).
Dates are written as {"__date__": "YYYY-MM-DDTHH:MM:SS"} so the test harness
can turn them back into Date objects, the way SpreadsheetApp returns them.
"""
import datetime
import json
import sys

import openpyxl

TABS = [
    '2. Outcome Progress',
    '3. Support',
    '4. Decision Tracker',
    '5. Dividends',
    '6. Committed & Spent Tracker',
    '7. Organisation Maturity',
    '8. Grant Registry',
    '9. Organisation Registry',
]


def cell(v):
    if isinstance(v, datetime.datetime):
        return {'__date__': v.isoformat()}
    if isinstance(v, datetime.date):
        return {'__date__': datetime.datetime(v.year, v.month, v.day).isoformat()}
    return '' if v is None else v


def main(src, out):
    wb = openpyxl.load_workbook(src, data_only=True)
    result = {}
    for name in TABS:
        rows = [[cell(v) for v in r] for r in wb[name].iter_rows(values_only=True)]
        while rows and all(v == '' for v in rows[-1]):
            rows.pop()
        width = max((max((i + 1 for i, v in enumerate(r) if v != ''), default=0) for r in rows), default=0)
        result[name] = [r[:width] for r in rows]
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

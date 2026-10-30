from pathlib import Path
from datetime import datetime, timezone
import sqlite3
import sys
from openpyxl import load_workbook

BASE = Path(__file__).resolve().parent
DATABASE = BASE / 'TPA_Operations.db'
ROOT = BASE / 'sample_data'

WORKBOOKS = {
    'Insurance Company A': (ROOT / 'Intranet - Insurance Company A' / 'Insurance Company A.xlsx', 'Insurance Company A', 'Remaining Balance'),
    'Insurance Company B': (ROOT / 'Intranet - Insurance Company B' / 'Insurance Company B.xlsx', 'Insurance Company B', 'Insurance Company B Remaining Balance'),
    'Insurance Company C': (ROOT / 'Intranet - Insurance Company C' / 'Insurance Company C.xlsx', 'Insurance Company C', 'Insurance Company C Remaining Balance'),
}

def sync_company(name):
    path, sheet, key = WORKBOOKS[name]
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        value = wb[sheet]['E4'].value
    finally:
        wb.close()
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name}!E4 is not numeric: {value!r}')
    # A successful check is distinct from a change to the source workbook.
    checked_at = datetime.now(timezone.utc).isoformat(timespec='seconds')
    modified_at = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec='seconds')
    with sqlite3.connect(DATABASE, timeout=10) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS CEO_KPIs (
            KPI_Name TEXT PRIMARY KEY,
            KPI_Value REAL NOT NULL,
            Updated_At TEXT NOT NULL
        )''')
        conn.execute('''INSERT INTO CEO_KPIs (KPI_Name, KPI_Value, Updated_At)
            VALUES (?, ?, ?)
            ON CONFLICT(KPI_Name) DO UPDATE SET
            KPI_Value=excluded.KPI_Value,
            Updated_At=excluded.Updated_At''',
            (key, float(value), datetime.now().isoformat(timespec='seconds')))
        conn.execute('''CREATE TABLE IF NOT EXISTS KPI_Monitor (
            Company TEXT PRIMARY KEY,
            Last_Check_At TEXT NOT NULL,
            Workbook_Modified_At TEXT NOT NULL
        )''')
        conn.execute('''INSERT INTO KPI_Monitor (Company, Last_Check_At, Workbook_Modified_At)
            VALUES (?, ?, ?)
            ON CONFLICT(Company) DO UPDATE SET
            Last_Check_At=excluded.Last_Check_At,
            Workbook_Modified_At=excluded.Workbook_Modified_At''',
            (name, checked_at, modified_at))
    print(f'SUCCESS - {name} Remaining Balance: {value:,.2f}', flush=True)
    return value

if __name__ == '__main__':
    names = [sys.argv[1]] if len(sys.argv) > 1 else list(WORKBOOKS)
    for name in names:
        if name not in WORKBOOKS:
            print(f'Unknown company: {name}', file=sys.stderr)
            sys.exit(2)
    failures = 0
    for name in names:
        try:
            sync_company(name)
        except (OSError, ValueError, KeyError, sqlite3.Error) as exc:
            failures += 1
            print(f'FAILED - {name}: {type(exc).__name__}: {exc}', file=sys.stderr, flush=True)
    if failures:
        sys.exit(1)

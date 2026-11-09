# TPA Operations Dashboard — Technical Implementation

This document describes the current public implementation and the programming techniques it demonstrates. See [architectural.md](architectural.md) for component relationships and [README.md](README.md) for setup instructions.

## 1. Dependencies and file layout

`requirements.txt` lists Flask, openpyxl and Waitress without pinned versions. Python's standard library supplies pathlib, datetime, sqlite3, sys and time. SQLite does not require a separate server installation.

| Location | Content |
| --- | --- |
| `src/create_sample_data.py` | Fictional workbook generator |
| `src/sync_balances.py` | Excel-to-SQLite synchronization |
| `src/watch_balances.py` | Polling monitor |
| `src/historical_dashboard.py` | Flask application and embedded frontend |
| `src/sample_data/` | Generated workbook folders |
| `src/TPA_Operations.db` | Generated database |

Paths are based on each script's `__file__`, rather than the shell's current directory. The documented commands are nevertheless run from the repository root so the virtual environment and import paths resolve as shown in the README.

Configuration is currently hardcoded in the Python modules. `.env.example` is a reference template; no dotenv loader or environment-based override is implemented.

## 2. Fictional sample data

The generator creates one worksheet per workbook, using the company name as the sheet title. Each workbook contains a fictional-data notice and a literal numeric value in E4.

| Company / worksheet | Workbook relative to `src/sample_data/` | Initial E4 |
| --- | --- | ---: |
| Insurance Company A | `Intranet - Insurance Company A/Insurance Company A.xlsx` | 50,000.00 |
| Insurance Company B | `Intranet - Insurance Company B/Insurance Company B.xlsx` | 75,000.00 |
| Insurance Company C | `Intranet - Insurance Company C/Insurance Company C.xlsx` | 100,000.00 |

The generator checks for existing targets and opens output files in exclusive-create mode. It refuses to overwrite existing workbooks. It does not seed SQLite or invent past observations. A failure during generation can leave a partial set of files; creation of the entire set is not transactional.

## 3. Workbook synchronization

`WORKBOOKS` maps each company to a tuple containing its file path, worksheet name and KPI identifier.

| Company | KPI identifier |
| --- | --- |
| Insurance Company A | `Remaining Balance` |
| Insurance Company B | `Insurance Company B Remaining Balance` |
| Insurance Company C | `Insurance Company C Remaining Balance` |

These identifiers match `KEYS` in the dashboard. Matching is exact, including spaces and punctuation.

`sync_company(name)` performs the following operations (is composed of 6 actions, and represents actually a small ETL pipeline (Export, Transform, Load). 

1. Opens the workbook with `read_only=True` and `data_only=True`. Read only=True should only read the file and not change it, while data only=True retrieves only the values and not the formulas from the file.  
2. Reads E4 from the configured worksheet and closes the workbook in a `finally` block. `try` and `finally` are structured in a way that ensures that the operation ends even if the reading fails.
3. Rejects boolean values and values that are not Python integers or floats. Accepts floating decimals values `float` and integers `Int`. 
4. Reads the file modification timestamp and records the successful-check time; `checked_at` Python successfully checks the last successful workbook value and `modified_at` Python checks the last modification time reported. 
5. After it connects to SQL it creates the two ingestion tables if needed and upserts their records within one transaction per company. One table is CEO_KPIs table and the other table is KPI_Monitor table. 
6. Prints the synchronized value and returns it. 

`data_only=True` uses a saved formula result when E4 contains a formula. The script neither calculates Excel formulas nor runs macros. A cached result must have been saved by a spreadsheet application. Numeric validation currently does not explicitly reject NaN or infinity.

### Command-line behavior

From the repository root:

```cmd
.venv\Scripts\python.exe src\sync_balances.py
```

With no argument, all configured companies are attempted. To synchronize one company, use its exact name in quotes:

```cmd
.venv\Scripts\python.exe src\sync_balances.py "Insurance Company A"
```

An unknown company exits with code 2. Caught file, value, key or SQLite errors are reported per company; if any such synchronization fails, the script exits with code 1. Successful completion exits normally. Other exception types are not comprehensively handled by this one-off command.

## 4. Monitoring logic

`watch_balances.py` imports `WORKBOOKS` and `sync_company` from its sibling module. Watch_balances.py continuously checks the Excel files and decides when to run `sync_balances.py`. 

| Setting | Value | Meaning |
| --- | ---: | --- |
| `CHECK_SECONDS` | 3 | Sleep between polling passes |
| `PERIODIC_RECHECK_SECONDS` | 60 | Recheck interval since a successful synchronization |

The first pass synchronizes available files. Later passes synchronize files whose modification timestamp changed or whose recheck is due. Tracking dictionaries are updated only after a successful call. Exceptions are printed and the loop continues, allowing subsequent retries. Ctrl+C stops monitoring gracefully.

Retry state is held in memory, so restarting the process begins a new initial check. There is no exponential backoff, durable queue or operating-system file-event subscription.

## 5. SQLite schema - Read Workbook synchronization

### 1st Table `CEO_KPIs`

| Column | Definition | Purpose |
| --- | --- | --- |
| `KPI_Name` | TEXT PRIMARY KEY | Unique configured KPI identifier |
| `KPI_Value` | REAL NOT NULL | Latest synchronized balance |
| `Updated_At` | TEXT NOT NULL | Successful synchronization time |

### 2nd Table `KPI_Monitor`

| Column | Definition | Purpose |
| --- | --- | --- |
| `Company` | TEXT PRIMARY KEY | Configured company label |
| `Last_Check_At` | TEXT NOT NULL | Most recent successful check |
| `Workbook_Modified_At` | TEXT NOT NULL | Source file modification time |

### 3rd Table `TPA_Balance_History`

| Column | Definition | Purpose |
| --- | --- | --- |
| `ID` | INTEGER PRIMARY KEY AUTOINCREMENT | Observation identifier |
| `Company` | TEXT NOT NULL | Company label |
| `Balance` | REAL NOT NULL | Observed balance |
| `Recorded_At` | TEXT NOT NULL | Observation timestamp |

Connections use a ten-second SQLite timeout and context-managed transactions. Query values are passed using SQL parameters. REAL storage uses floating-point values and should not be described as exact decimal accounting storage.

### Timestamp conventions

`Last_Check_At` and `Workbook_Modified_At` use timezone-aware UTC ISO strings. `Updated_At` and history timestamps use local `datetime.now()` values without timezone offsets. The history cutoff uses the same local convention as history insertion. This inconsistency should be standardized before cross-timezone use; existing timestamps must not simply be relabelled as UTC.

## 6. Flask routes and history behavior

| Request | Behavior |
| --- | --- |
| `GET /` | Renders the embedded dashboard page |
| `GET /api/history` | Uses Company A and a 30-day window by default |
| `GET /api/history?company=Insurance%20Company%20B&days=7` | Returns all current balances and Company B's recent history |
| Unknown company | HTTP 400, `Invalid company` |
| Non-integer days or a period other than 7, 30, 90 | HTTP 400, `Invalid period` |
| Caught SQLite error | HTTP 503, `Database unavailable` |

The JSON response contains `balances`, a company-to-value mapping, and `history`, a list of objects with `value` and `recorded_at` fields. Missing current values remain null. If the database file is absent, the endpoint returns HTTP 200 with null balances and empty history. If a database exists but lacks the required current-KPI table, the SQLite error returns 503; initial synchronization should therefore run first.

For each current value, the endpoint selects the latest history row by descending ID. It inserts an observation if no previous row exists or the absolute difference exceeds `0.000001`. It then selects the chosen company's rows at or after the period cutoff, ordered by ID.

A request can record changes for all three companies, even when the user is viewing one company's chart. Sequential unchanged requests avoid new observations, but simultaneous requests can race because the check-and-insert operation has no dedicated duplicate-prevention constraint. GET requests are not read-only in this implementation.

## 7. Browser presentation

The page is embedded in a Python string and rendered with `render_template_string()`. JavaScript fetches the API on load, after selection changes and every three seconds. No WebSocket or charting library is used.

The browser draws an SVG polyline and circles, scales the axes to the returned timestamps and values, and adds point tooltips. A single observation appears as a dot. Company buttons and 7D/30D/90D buttons trigger new requests. Values are formatted to two decimal places without currency conversion.

The connected indicator reports successful API communication. It does not display `KPI_Monitor` freshness information. Failed refreshes can leave the previously displayed balances visible. Requests can overlap, so rapid selection changes may allow an older response to replace a newer view.

## 8. Validation and demonstrated skills

The developer manually verified the Windows setup, sample generation, synchronization and Waitress serving. On 3 November 2026, editing the fictional Company A balance from 50,000 to 48,000 was confirmed to update the dashboard and produce a second connected history point.

That scenario demonstrates the integration of file monitoring, Excel extraction, SQLite persistence, API delivery and visualization. It is a manual functional check, not an automated regression suite or proof of all failure modes.

Technical skills shown include Python module reuse, dictionaries and tuple unpacking, pathlib-based paths, resource cleanup, exception handling, polling and retries, SQL upserts, parameterized queries, Flask routing, JSON responses, WSGI serving and SVG-based browser visualization.

## 9. Operational limitations

No authentication, HTTPS, alerts or database migration system is included. The current dependency list is unpinned. Console errors may reveal configured paths or invalid source values, so logs from operational installations must not be published without review.

The demo should stay on localhost. Stop the monitor and web server before making a simple file-copy backup of the database. Broader deployment, financial precision, source freshness, automated tests and request-independent history are future improvements rather than capabilities claimed here.

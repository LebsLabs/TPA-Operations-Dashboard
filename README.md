# TPA Operations Dashboard

A Python dashboard that reads running balances from Excel workbooks, stores current values and historical observations in SQLite, and displays them through a Flask web interface served by Waitress.

**Portfolio edition:** This repository uses anonymized company names and a generator for fictional sample data. Operational workbooks, private paths and real financial records are excluded.

## Why this project was built

The project began with a department manager's request for email notifications when a running balance fell below a threshold. A dashboard was proposed to provide continuous visibility of balances and their movements across several insurance companies.

The intended internal setup is a small laptop connected to two display screens, allowing the department to monitor balances without repeatedly opening individual Excel workbooks. This screen deployment is a planned use case; the public edition demonstrates the application locally. 

## Features

- Displays the latest recorded balance for Insurance Company A, B and C.
- Reads cell `E4` from each configured Excel worksheet without modifying the workbook.
- Stores current balances and workbook-check metadata in SQLite.
- Includes a monitor that checks for file changes, periodically rechecks workbooks and retries unsuccessful reads.
- Displays historical observations using selectable 7-, 30- and 90-day charts.
- Refreshes dashboard data every three seconds.
- Generates three fictional Excel workbooks for an independent local demonstration.

## Technology stack

| Technology | Role |
| --- | --- |
| Python | Data extraction, monitoring and application logic |
| openpyxl | Reads saved Excel values and generates sample workbooks |
| SQLite | Stores current balances, check metadata and historical observations |
| Flask | Provides the web page and JSON API |
| Waitress | Serves the Flask application locally |
| HTML, CSS and JavaScript | Browser layout, automatic refresh and SVG charts |

## Application files

The application scripts are located in `src/`.

| File | Purpose |
| --- | --- |
| `create_sample_data.py` | Creates fictional `.xlsx` workbooks with numeric balances in `E4` |
| `sync_balances.py` | Validates saved balance values and updates the database |
| `watch_balances.py` | Calls synchronization when workbooks change or a periodic check is due |
| `historical_dashboard.py` | Displays balances and records historical changes observed during API requests |

After downloading and extracting the ZIP, run create_sample_data.py to generate the demo workbooks in src/sample_data/. Then run sync_balances.py to create the database at src/TPA_Operations.db.

## Run the fictional demonstration on Windows

Install Python with the Windows `py` launcher available. The instructions below use **Command Prompt** and have been checked through sample generation, synchronization and local dashboard startup on Windows.

### 1. Prepare the project folder

Download the repository ZIP and extract it into a separate demonstration folder. For the commands below, use:

```text
%USERPROFILE%\TPA_Dashboard
```

That folder should directly contain `requirements.txt` and `src`. If you use another location, adjust the `cd` commands accordingly.

### 2. Create an environment and install dependencies

```cmd
cd /d "%USERPROFILE%\TPA_Dashboard"
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Generate sample workbooks and synchronize balances

Run these commands once for a fresh demonstration:

```cmd
.venv\Scripts\python.exe src\create_sample_data.py
.venv\Scripts\python.exe src\sync_balances.py
```

Expected fictional balances:

| Company | Starting balance |
| --- | ---: |
| Insurance Company A | 50,000.00 |
| Insurance Company B | 75,000.00 |
| Insurance Company C | 100,000.00 |

The generator refuses to overwrite existing sample workbooks. On subsequent launches, keep the existing samples and skip the generation command. It does not generate historical readings.

### 4. Start the dashboard

```cmd
.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:5002 src.historical_dashboard:app
```

Keep this window open and visit [http://127.0.0.1:5002/](http://127.0.0.1:5002/).

Port `5002` is used for the demonstration. Binding to `127.0.0.1` makes it accessible only from the same computer.

### 5. Start automatic monitoring

In a second Command Prompt window, run:

```cmd
cd /d "%USERPROFILE%\TPA_Dashboard"
.venv\Scripts\python.exe src\watch_balances.py
```

Keep both windows open while monitoring. To try an update, change `E4` in one of the generated demo workbooks, save it and leave the dashboard open. The monitor is designed to synchronize the new value, after which the next browser request can record a historical observation.

## How historical readings work

The monitor updates the latest balances. Historical observations are recorded separately by the dashboard API when it receives a request and detects a change from the last stored value.

History therefore depends on dashboard requests. Intermediate changes can be missed between requests or while the dashboard is closed. Observation timestamps indicate when the application recorded a value, not when the underlying business transaction occurred.

A new demonstration initially shows one dot per company. A line requires at least two recorded observations. Selecting 90 days changes the viewing window; it does not create older data.

## Validation status

Sample-data generation, synchronization of all three balances and display through Waitress were manually verified on Windows. Automatic monitoring was manually verified by changing a fictional Excel balance from 50,000 to 48,000 and confirming that the dashboard balance and historical chart updated. A complete automated test suite is not included.

<img width="1891" height="934" alt="image" src="https://github.com/user-attachments/assets/c6bab5b3-e9c6-423c-854e-e8994f10690e" />
## Configuration and limitations

- Workbook paths, worksheet names and KPI mappings are defined in `src/sync_balances.py`. Matching company labels and KPI mappings are used in `src/historical_dashboard.py`.
- The demo uses `.xlsx` workbooks. Both scripts must reference the same database file.
- `.env.example` is a reference template only; the current application does not load its settings.
- openpyxl reads saved formula results; it does not calculate formulas or execute VBA. Formula-based balances must have numeric cached results saved by Excel.
- The dashboard does not show source freshness metadata. A connected browser does not establish that a workbook was recently read successfully.
- Amounts are displayed without currency labels or conversion. Compare balances only when their units are consistent.
- This prototype has no built-in authentication or HTTPS. The documented setup is intended for local demonstration.

## Stop and back up

Press **Ctrl+C** in both Command Prompt windows to stop Waitress and monitoring.

With both processes stopped, copy `src/TPA_Operations.db` to a separate backup location. This preserves current balances and recorded history. Back up source workbooks separately if needed.

Do not commit private configuration, operational workbooks, databases or logs to the public repository.

## Future improvements

- Record history during synchronization, independently of browser requests.
- Display the last successful workbook check and flag stale readings.
- Externalize configuration and add automated integration tests.
- Introduce authentication and HTTPS for any approved shared deployment.

## Author and rights

Author:
GitHub:

Project: TPA Operational Dashboard

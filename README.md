# TPA Operations Dashboard

## 1. Intro 

or TPA Dashboard stands for Third Party Administration Dashboard and it is a dashboard written mainly in Python that reads running balances from excel workbooks, store current values in SQLite, and displays them through Flask. Of course, the version of the dashboard that is uploaded in this repository is slightly different from the original as the files are sanitized.  

## 2. Scope of the dashboard

This project is connected to the GOP Generator project [GOP Generator](https://github.com/LebsLabs/GOP-Generator). In fact, it was requested that the GOP Generator should have an automatic email alert when a running balance falls below a certain threshold. A dashboard was proposed as a solution to provide continuous visibility of balances and their movements across several insurance companies.

## 3. How does it work

Using Python, the application reads the latest recorded balances for Insurance Companies A and B from cell `E4` in each configured Excel worksheet, storing the data and workbook-check metadata in a `.db` file. It periodically rechecks the workbooks and retries unsuccessful reads. It then displays selectable 7-, 30-, and 90-day charts through a web browser — see the dashboard in the picture below:

<img width="1891" height="934" alt="image" src="https://github.com/user-attachments/assets/c6bab5b3-e9c6-423c-854e-e8994f10690e" />

## 4. Run the fictional demonstration on Windows

Install Python with the Windows `py` launcher available. The instructions below use **Command Prompt** and have been checked through sample generation, synchronization and local dashboard startup on Windows.

### a) Prepare the project folder

Download the repository ZIP and extract it into a separate demonstration folder. For the commands below, use:

```text
%USERPROFILE%\TPA_Dashboard
```

That folder should directly contain `requirements.txt` and `src`. If you use another location, adjust the `cd` commands accordingly.

### b) Create an environment and install dependencies

```cmd
cd /d "%USERPROFILE%\TPA_Dashboard"
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### c) Generate sample workbooks and synchronize balances

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

### d) Start the dashboard

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

## 8. Validation status

Sample-data generation, synchronization of all three balances and display through Waitress were manually verified on Windows. Automatic monitoring was manually verified by changing a fictional Excel balance from 50,000 to 48,000 and confirming that the dashboard balance and historical chart updated. A complete automated test suite is not included.

## 9. Configuration and limitations

- Workbook paths, worksheet names and KPI mappings are defined in `src/sync_balances.py`. Matching company labels and KPI mappings are used in `src/historical_dashboard.py`.
- The demo uses `.xlsx` workbooks. Both scripts must reference the same database file.
- `.env.example` is a reference template only; the current application does not load its settings.
- openpyxl reads saved formula results; it does not calculate formulas or execute VBA. Formula-based balances must have numeric cached results saved by Excel.
- The dashboard does not show source freshness metadata. A connected browser does not establish that a workbook was recently read successfully.
- Amounts are displayed without currency labels or conversion. Compare balances only when their units are consistent.
- This prototype has no built-in authentication or HTTPS. The documented setup is intended for local demonstration.

## 10. Stop and back up

Press **Ctrl+C** in both Command Prompt windows to stop Waitress and monitoring.

With both processes stopped, copy `src/TPA_Operations.db` to a separate backup location. This preserves current balances and recorded history. Back up source workbooks separately if needed.

Do not commit private configuration, operational workbooks, databases or logs to the public repository.

## 11. Future improvements

- Record history during synchronization, independently of browser requests.
- Display the last successful workbook check and flag stale readings.
- Externalize configuration and add automated integration tests.
- Introduce authentication and HTTPS for any approved shared deployment.
Project: TPA Operational Dashboard

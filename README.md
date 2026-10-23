# CEO Operations Dashboard

**A Python dashboard for monitoring operational KPIs from Excel workbooks and visualizing historical changes.**

> **Portfolio edition:** The public repository should contain sanitized code and synthetic sample data only. No internal company financial records, workbook paths, credentials, or corporate identifiers.

## Overview

The CEO Operations Dashboard is a prototype designed to make selected operational metrics easier to monitor. It reads values from locally synchronized Excel workbooks, stores current KPI readings in SQLite, and displays balances and historical trends through a Flask web interface.

The original prototype was developed for a local Windows environment. This public version is intended to demonstrate the technical approach without exposing employer data.

## Features

| Feature | Implementation |
| --- | --- |
| Excel KPI extraction | `openpyxl` reads selected cells from `.xlsm` files without running macros |
| Automated monitoring | Python checks workbook changes and retries transient read failures |
| Current KPI storage | SQLite stores the latest recorded values |
| Historical visualization | Dashboard displays recorded balance observations over time |
| Web dashboard | Flask provides the browser interface and API endpoints |
| Local serving | Waitress can serve the Flask application locally |

## Architecture

```text
Excel workbooks (read-only access)
            |
            v
     Python monitoring
            |
            v
       SQLite database
            |
            v
        Flask app
            |
            v
   Browser dashboard / chart
```

## Technology stack

- Python
- Flask
- SQLite
- openpyxl
- Waitress
- HTML / CSS / JavaScript

## Repository status

This README is part of a **GitHub preparation pack**. Add only reviewed, sanitized versions of the real application files. Do not publish this as a runnable release until the configuration has been externalized and the demo tested using synthetic data.

## Local development

After the sanitized application files and a pinned `requirements.txt` have been added:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The original prototype runs a local Flask application and a separate Excel monitoring process. The precise commands and demo setup should be documented here after the sanitized code is tested.

## Security and privacy

- Never commit actual SQLite databases, Excel workbooks, secrets, or real financial balances.
- Replace internal OneDrive / SharePoint paths with environment-driven configuration or synthetic examples.
- Remove company-specific names and identifiers from public code, screenshots, logs, and commit history.
- The prototype has **no built-in user authentication or HTTPS**. Do not expose it to a public network or describe it as production-secure.
- The public portfolio demo should use synthetic sample data only.

## What this project demonstrates

- Integrating Python with Excel-based workflows
- Working with SQLite and historical KPI observations
- Separating data collection from presentation
- Building a web dashboard with Flask
- Handling local file synchronization and transient errors
- Preparing an internal prototype for maintainable, privacy-conscious publication

## Screenshots

Add screenshots from a **synthetic-data demonstration** to `screenshots/` after reviewing them for confidential information.

## Future improvements

- Externalized configuration and automated tests
- Stronger historical data capture independent of the dashboard process
- Authenticated, HTTPS-enabled deployment in an approved environment
- Additional KPI metrics and reporting views

## License

No license has been selected yet. Add one only after confirming that you own the code and are authorized to publish it.

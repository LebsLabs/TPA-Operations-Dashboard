"""Monitor configured Excel workbooks and synchronize their KPI readings.

Workbook definitions and data extraction are provided by sync_balances.py.
"""

import time

from sync_balances import WORKBOOKS, sync_company

CHECK_SECONDS = 3
PERIODIC_RECHECK_SECONDS = 60


def main():
    # Failed reads are retried even if the file modification time is unchanged.
    last_success_mtime = {}
    last_success_check = {}

    print(f"Monitoring {len(WORKBOOKS)} configured workbook(s)...", flush=True)
    print("Press Ctrl+C to stop.", flush=True)

    try:
        while True:
            now = time.monotonic()
            for name, (path, _, _) in WORKBOOKS.items():
                try:
                    mtime = path.stat().st_mtime_ns
                    due = (
                        name not in last_success_mtime
                        or mtime != last_success_mtime[name]
                        or now - last_success_check.get(name, 0)
                        >= PERIODIC_RECHECK_SECONDS
                    )
                    if due:
                        sync_company(name)
                        last_success_mtime[name] = mtime
                        last_success_check[name] = time.monotonic()
                except (OSError, ValueError, KeyError) as exc:
                    print(
                        f"{name}: temporarily unavailable: "
                        f"{type(exc).__name__}: {exc}",
                        flush=True,
                    )
                except Exception as exc:
                    print(
                        f"{name}: synchronization error: "
                        f"{type(exc).__name__}: {exc}",
                        flush=True,
                    )
            time.sleep(CHECK_SECONDS)
    except KeyboardInterrupt:
        print("\nWorkbook monitoring stopped.", flush=True)


if __name__ == "__main__":
    main()

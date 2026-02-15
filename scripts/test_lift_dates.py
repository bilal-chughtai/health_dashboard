#!/usr/bin/env python3
"""Test lift-dates CSV and ManualConnector locally. Run from repo root:
    python scripts/test_lift_dates.py
"""
import os
import sys
from pathlib import Path

# Add project root so dashboard imports work
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from datetime import datetime, timedelta

from dashboard.connectors.manual import _fetch_lift_dates_from_csv, ManualConnector
from dashboard.secret import get_lift_dates_csv_url


def main() -> None:
    url = get_lift_dates_csv_url() or os.environ.get("LIFT_DATES_SHEET_CSV_URL")
    if not url:
        print("LIFT_DATES_SHEET_CSV_URL not set in .secrets.json or env.")
        print("Add it to .secrets.json (repo root) and run again.")
        return

    print("Fetching lift dates from CSV...")
    dates = _fetch_lift_dates_from_csv(url, debug=True)
    if not dates:
        print("No dates parsed. Check CSV URL and that the sheet has a 'Date' column (YYYY-MM-DD).")
        return

    sorted_dates = sorted(dates)
    print(f"Parsed {len(sorted_dates)} lift dates: {sorted_dates[0]} to {sorted_dates[-1]}")
    print("First 5:", sorted_dates[:5])
    print("Last 5:", sorted_dates[-5:])

    print("\nManualConnector.get_data() for the last 60 days:")
    end = datetime.now()
    start = end - timedelta(days=60)
    connector = ManualConnector()
    manual_list = connector.get_data(start, end)
    print(f"  Returned {len(manual_list)} ManualData entries (lift=True)")
    for m in manual_list[:5]:
        print(f"    {m.date.date()} lift={m.lift}")
    if len(manual_list) > 5:
        print(f"    ... and {len(manual_list) - 5} more")

    print("\nLift-dates feature is working locally.")


if __name__ == "__main__":
    main()

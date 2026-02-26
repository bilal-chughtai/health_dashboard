"""Lift-dates CSV fetching. Kept separate so the dashboard can use it without importing connectors."""
import io
import logging
from datetime import date

import pandas as pd
import requests

logger = logging.getLogger(__name__)


def fetch_lift_dates_from_csv(csv_url: str, debug: bool = False) -> set[date]:
    """Fetch CSV from URL and return set of date objects found in the Date column (YYYY-MM-DD)."""
    if debug:
        print("[manual] Fetching lift-dates CSV...")
    try:
        resp = requests.get(csv_url, timeout=10)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        if debug:
            print(f"[manual] CSV: {len(df)} rows, columns: {list(df.columns)}")
    except Exception as e:
        if debug:
            print(f"[manual] Failed to fetch/parse CSV: {e}")
        logger.warning("Failed to fetch lift dates CSV: %s", e)
        return set()
    dates: set[date] = set()
    if "Date" in df.columns:
        parsed = pd.to_datetime(df["Date"], format="%Y-%m-%d", errors="coerce")
    else:
        parsed = pd.to_datetime(df.iloc[:, 0], format="%Y-%m-%d", errors="coerce")
    for v in parsed.dropna():
        if hasattr(v, "date"):
            dates.add(v.date())
    if debug:
        print(f"[manual] Parsed {len(dates)} unique lift dates")
    return dates

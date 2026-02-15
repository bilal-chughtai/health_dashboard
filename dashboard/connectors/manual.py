import io
import logging
from datetime import datetime

import pandas as pd
import requests
from typing import List

from dashboard.models import ManualData
from dashboard.secret import get_lift_dates_csv_url
from dashboard.connectors.base import Connector

logger = logging.getLogger(__name__)


def _fetch_lift_dates_from_csv(csv_url: str, debug: bool = True) -> set:
    """Fetch CSV from URL and return set of date objects found in the Date column."""
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
    # Spreadsheet uses YYYY-MM-DD (e.g. 2026-01-16)
    dates = set()
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


class ManualConnector(Connector[ManualData]):
    """Connector for manual data: lift dates from configured Google Sheet CSV plus form entries."""

    @property
    def source_name(self) -> str:
        """Return the name of the data source."""
        return "manual"

    def get_data(self, start_date: datetime, end_date: datetime) -> List[ManualData]:
        """Return ManualData with lift=True for every date in the lift-dates CSV (if configured).
        Ignores start/end so one sync backfills all lift days from the sheet."""
        csv_url = get_lift_dates_csv_url()
        if not csv_url:
            print("[manual] No LIFT_DATES_SHEET_CSV_URL in .secrets.json")
            return []
        print(f"[manual] URL configured (length {len(csv_url)})")
        lift_dates = _fetch_lift_dates_from_csv(csv_url, debug=True)
        if not lift_dates:
            print("[manual] No dates parsed from CSV; check Date column is YYYY-MM-DD")
            return []
        result: List[ManualData] = []
        for d in sorted(lift_dates):
            result.append(
                ManualData(
                    source="manual",
                    date=datetime.combine(d, datetime.min.time()),
                    bodyweight_kg=None,
                    lift=True,
                )
            )
        print(f"[manual] Returning {len(result)} ManualData entries (lift=True)")
        return result

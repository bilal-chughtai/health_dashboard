import logging
from datetime import datetime
from typing import List

from dashboard.models import ManualData
from dashboard.secret import get_lift_dates_csv_url
from dashboard.lift_dates import fetch_lift_dates_from_csv
from dashboard.connectors.base import Connector

logger = logging.getLogger(__name__)


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
        lift_dates = fetch_lift_dates_from_csv(csv_url, debug=True)
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

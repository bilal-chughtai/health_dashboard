from typing import List
from dashboard.models import ManualData
from datetime import datetime


def get_data(start_date: datetime, end_date: datetime) -> List[ManualData]:
    """Return empty list - manual data is now handled directly in the dashboard."""
    return []

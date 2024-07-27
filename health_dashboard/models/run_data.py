from health_dashboard.models.health_data import HealthData
from datetime import datetime


class DailyRunData(HealthData):
    """
    Stores DAILY run data. If multiple runs in a day, stores as one entry.
    """
    
    def __init__(self, timestamp: datetime, source: str, distance: float, duration: float):
        super().__init__(timestamp, source)
        self.distance = distance # in km
        self.duration = duration # in hours

    def __repr__(self) -> str:
        return f"RunData({super().__repr__()}, distance: {self.distance}, time: {self.time})"

    @staticmethod
    def id() -> str:
        return "daily_run"

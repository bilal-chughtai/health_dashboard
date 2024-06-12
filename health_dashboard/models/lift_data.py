from datetime import datetime

from health_dashboard.models.health_data import HealthData


class LiftData(HealthData):
    def __init__(self, timestamp: datetime, source: str, score: int):
        """
        Initialize a Bodywight instance.

        :param timestamp: A datetime object representing when this data was recorded.
        :param source: A string representing the source of this data.
        :param score: A boolean (1 or 0) representing whether lifting occured or not.
        """
        super().__init__(timestamp, source)
        self.score = score

    def __repr__(self) -> str:
        return f"LiftData({super().__repr__()}, score: {self.score})"

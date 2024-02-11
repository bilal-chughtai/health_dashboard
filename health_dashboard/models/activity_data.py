from models.health_data import HealthData
from datetime import datetime

class ActivityData(HealthData):
    def __init__(self, timestamp: datetime, source: str, score: int):
        """
        Initialize a SleepData instance.

        :param timestamp: A datetime object representing when this sleep data was recorded.
        :param source: A string representing the source of this sleep data.
        :param score: An integer representing the activity score.
        """
        super().__init__(timestamp, source)
        self.score = score

    def __repr__(self) -> str:
        return f"ActivityData({super().__repr__()}, score: {self.score})"
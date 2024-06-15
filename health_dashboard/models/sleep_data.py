from health_dashboard.models.health_data import HealthData
from datetime import datetime

class SleepData(HealthData):
    def __init__(self, 
                timestamp: datetime, 
                source: str, 
                score: int, 
                duration: int | None = None):
        """
        Initialize a SleepData instance.

        :param timestamp: A datetime object representing when this sleep data was recorded.
        :param source: A string representing the source of this sleep data.
        :param score: An integer representing the sleep score.
        """
        super().__init__(timestamp, source)
        self.score = score
        self.duration = duration

    def __repr__(self) -> str:
        return f"SleepData({super().__repr__()}, score: {self.score}, duration: {self.duration} hours)"
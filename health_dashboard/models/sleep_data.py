from health_dashboard.models.health_data import HealthData
from datetime import datetime

class SleepData(HealthData):
    def __init__(self, 
                timestamp: datetime, 
                source: str, 
                score: int, 
                duration: float | None = None):
        super().__init__(timestamp, source)
        self.score = score
        self.duration = duration

    def __repr__(self) -> str:
        return f"SleepData({super().__repr__()}, score: {self.score}, duration: {self.duration} hours)"
    
    @staticmethod
    def id() -> str:
        return "sleep"
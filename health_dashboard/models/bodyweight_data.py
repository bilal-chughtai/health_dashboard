from health_dashboard.models.health_data import HealthData
from datetime import datetime


class BodyweightData(HealthData):
    def __init__(self, timestamp: datetime, source: str, score: float):
        super().__init__(timestamp, source)
        self.score = score

    def __repr__(self) -> str:
        return f"BodyWeight({super().__repr__()}, score: {self.score}kg)"
    
    @staticmethod
    def id() -> str:
        return "bodyweight"

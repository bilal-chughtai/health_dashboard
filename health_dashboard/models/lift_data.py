from datetime import datetime

from health_dashboard.models.health_data import HealthData


class LiftData(HealthData):
    def __init__(self, timestamp: datetime, source: str, score: int):
        super().__init__(timestamp, source)
        self.score = score

    def __repr__(self) -> str:
        return f"LiftData({super().__repr__()}, score: {self.score})"
    
    @staticmethod
    def id() -> str:
        return "lift"

from datetime import datetime

class HealthData():
    def __init__(self, timestamp: datetime, source: str):
        """
        Initialize a HealthData instance.

        :param timestamp: A datetime object representing when this data was recorded.
        :param source: A string representing the source of this data (e.g., "Fitbit", "Apple Health").
        """
        self.timestamp = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
        self.source = source

    def __repr__(self) -> str:
        return f"timestamp: {self.timestamp}, source: {self.source}"
from abc import ABC

from health_dashboard.models.health_data import HealthData


class APIConnector(ABC):
    def __init__(self):
        """
        Initialize the API connector with an access token.
        """

    def get_all_data(self) -> list[HealthData]:
        """
        Placeholder method for fetching data. Specific connectors will implement this method.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

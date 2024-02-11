# Assuming SleepData is defined in models/sleep_data.py
from models.health_data import HealthData
from models.sleep_data import SleepData
from models.readiness_data import ReadinessData
from models.activity_data import ActivityData
from datetime import datetime
from oura_ring import OuraClient
from connectors.api_connector import APIConnector

class OuraConnector(APIConnector):
    def __init__(self, access_token: str):
        """
        Initialize the OuraConnector with an access token.

        :param access_token: The access token for the Oura API.
        """
        super().__init__(access_token)
        self.client = OuraClient(access_token)
        self.source_name = "oura"
        
    def get_all_data(self, start_date: str = None, end_date: str = None) -> list[HealthData]:
        """
        Fetch all data from the Oura API and return a list of HealthData objects.

        :param start_date: The start date for fetching data in YYYY-MM-DD format. Defaults to yesterday.
        :param end_date: The end date for fetching data in YYYY-MM-DD format. Defaults to today.
        :return: A list of SleepData objects with the sleep data from the Oura API.
        """
        sleep_data = self.get_daily_sleep(start_date, end_date)
        readiness_data = self.get_daily_readiness(start_date, end_date)
        activity_data = self.get_daily_activity(start_date, end_date)
        all_data = sleep_data + readiness_data + activity_data
        return all_data
        
    def get_daily_sleep(self, start_date: str = None, end_date: str = None) -> list[SleepData]:
        """
        Fetch daily sleep data for a specified date range and return a list of SleepData objects.

        :param start_date: The start date for fetching sleep data in YYYY-MM-DD format. Defaults to yesterday.
        :param end_date: The end date for fetching sleep data in YYYY-MM-DD format. Defaults to today.
        :return: A list of SleepData objects with the sleep data from the Oura API.
        """
        # Fetch sleep data from the Oura API
        with OuraClient(self.access_token) as client:
            sleep_data_response = client.get_daily_sleep(start_date=start_date, end_date=end_date)

        # Transform the API response into SleepData objects
        sleep_data_objects = []
        for sleep_entry in sleep_data_response:
            # Each entry is one day of sleep data
            timestamp = sleep_entry["timestamp"]
            sleep_score = sleep_entry["score"]
            sleep_data = SleepData(timestamp=timestamp, source=self.source_name, score=sleep_score)
            sleep_data_objects.append(sleep_data)

        return sleep_data_objects
    
    def get_daily_readiness(self, start_date: str = None, end_date: str = None) -> list[ReadinessData]:
        """
        Fetch daily readiness data for a specified date range and return a list of ReadinessData objects.

        :param start_date: The start date for fetching readiness data in YYYY-MM-DD format. Defaults to yesterday.
        :param end_date: The end date for fetching readiness data in YYYY-MM-DD format. Defaults to today.
        :return: A list of ReadinessData objects with the readiness data from the Oura API.
        """
        # Fetch readiness data from the Oura API
        with OuraClient(self.access_token) as client:
            readiness_data_response = client.get_daily_readiness(start_date=start_date, end_date=end_date)

        # Transform the API response into ReadinessData objects
        readiness_data_objects = []
        for readiness_entry in readiness_data_response:
            # Each entry is one day of readiness data
            timestamp = datetime.fromisoformat(readiness_entry["timestamp"])
            readiness_score = readiness_entry["score"]
            readiness_data = ReadinessData(timestamp=timestamp, source=self.source_name, score=readiness_score)
            readiness_data_objects.append(readiness_data)

        return readiness_data_objects
    
    def get_daily_activity(self, start_date: str = None, end_date: str = None) -> list[ActivityData]:
        """
        Fetch daily activity data for a specified date range and return a list of ActivityData objects.

        :param start_date: The start date for fetching activity data in YYYY-MM-DD format. Defaults to yesterday.
        :param end_date: The end date for fetching activity data in YYYY-MM-DD format. Defaults to today.
        :return: A list of ActivityData objects with the activity data from the Oura API.
        """
        # Fetch activity data from the Oura API
        with OuraClient(self.access_token) as client:
            activity_data_response = client.get_daily_activity(start_date=start_date, end_date=end_date)

        # Transform the API response into ActivityData objects
        activity_data_objects = []
        for activity_entry in activity_data_response:
            # Each entry is one day of activity data
            timestamp = datetime.fromisoformat(activity_entry["timestamp"])
            activity_score = activity_entry["score"]
            activity_data = ActivityData(timestamp=timestamp, source=self.source_name, score=activity_score)
            activity_data_objects.append(activity_data)

        return activity_data_objects


import os
from pprint import pprint

from dotenv import load_dotenv
from health_dashboard.models.steps_data import StepsData
from health_dashboard.models.health_data import HealthData
from health_dashboard.models.sleep_data import SleepData
from health_dashboard.models.readiness_data import ReadinessData
from health_dashboard.models.activity_data import ActivityData
from datetime import datetime
from oura_ring import OuraClient
from health_dashboard.connectors.api_connector import APIConnector

class OuraConnector(APIConnector):
    def __init__(self):
        """
        Initialize the OuraConnector with an access token.

        :param access_token: The access token for the Oura API.
        """
        load_dotenv()
        oura_access_token = os.getenv('OURA_ACCESS_TOKEN')
        if not oura_access_token:
            raise ValueError("No OURA_ACCESS_TOKEN provided")
        self.client = OuraClient(oura_access_token)
        self.source_name = "oura"

    from typing import Sequence
    
    def get_all_data(self, start_date: str | None = None, end_date: str | None = None) -> Sequence[HealthData]:
        """
        Fetch all data from the Oura API and return a list of HealthData objects.
    
        :param start_date: The start date for fetching data in YYYY-MM-DD format. Defaults to yesterday.
        :param end_date: The end date for fetching data in YYYY-MM-DD format. Defaults to today.
        :return: A list of SleepData objects with the sleep data from the Oura API.
        """
        sleep_data = self.get_daily_sleep(start_date, end_date)
        readiness_data = self.get_daily_readiness(start_date, end_date)
        activity_data = self.get_daily_activity(start_date, end_date)
        steps_data = self.get_steps_data(start_date, end_date)
        all_data = sleep_data + readiness_data + activity_data + steps_data
        return all_data

    def get_daily_sleep(self, start_date: str | None = None, end_date: str | None = None) -> list[SleepData]:
        """
        Fetch daily sleep data for a specified date range and return a list of SleepData objects.

        :param start_date: The start date for fetching sleep data in YYYY-MM-DD format. Defaults to yesterday.
        :param end_date: The end date for fetching sleep data in YYYY-MM-DD format. Defaults to today.
        :return: A list of SleepData objects with the sleep data from the Oura API.
        """
        
        # Daily Sleep Scores
        sleep_data_response = self.client.get_daily_sleep(start_date=start_date, end_date=end_date)
        
        # Sleep Duration Data
        duration_data_response = self.client.get_sleep_periods(start_date=start_date, end_date=end_date)
        
        assert isinstance(sleep_data_response, list)
        assert isinstance(duration_data_response, list)
        
        # Transform the API response into SleepData objects
        sleep_data_objects = []
        for sleep_entry in sleep_data_response:

            timestamp = sleep_entry["timestamp"]
            day = sleep_entry["day"]
            durations = [x["total_sleep_duration"] for x in duration_data_response if x["day"] == day]

            if len(durations) == 0:
                duration = 0
            else:
                duration = sum(durations) / 3600 # convert to hours

            sleep_score = sleep_entry["score"]
            sleep_data = SleepData(timestamp=timestamp, source=self.source_name, score=sleep_score, duration=duration)
            sleep_data_objects.append(sleep_data)

        return sleep_data_objects

    def get_daily_readiness(self, start_date: str | None = None, end_date: str |None = None) -> list[ReadinessData]:
        """
        Fetch daily readiness data for a specified date range and return a list of ReadinessData objects.

        :param start_date: The start date for fetching readiness data in YYYY-MM-DD format. Defaults to yesterday.
        :param end_date: The end date for fetching readiness data in YYYY-MM-DD format. Defaults to today.
        :return: A list of ReadinessData objects with the readiness data from the Oura API.
        """
        # Fetch readiness data from the Oura API
        readiness_data_response = self.client.get_daily_readiness(start_date=start_date, end_date=end_date)
        assert isinstance(readiness_data_response, list)
        # Transform the API response into ReadinessData objects
        readiness_data_objects = []
        for readiness_entry in readiness_data_response:
            # Each entry is one day of readiness data
            timestamp = datetime.fromisoformat(readiness_entry["timestamp"])
            readiness_score = readiness_entry["score"]
            readiness_data = ReadinessData(timestamp=timestamp, source=self.source_name, score=readiness_score)
            readiness_data_objects.append(readiness_data)

        return readiness_data_objects

    def get_daily_activity(self, start_date: str | None = None, end_date: str | None = None) -> list[ActivityData]:
        """
        Fetch daily activity data for a specified date range and return a list of ActivityData objects.

        :param start_date: The start date for fetching activity data in YYYY-MM-DD format. Defaults to yesterday.
        :param end_date: The end date for fetching activity data in YYYY-MM-DD format. Defaults to today.
        :return: A list of ActivityData objects with the activity data from the Oura API.
        """
        # Fetch activity data from the Oura API
        activity_data_response = self.client.get_daily_activity(start_date=start_date, end_date=end_date)
        assert isinstance(activity_data_response, list)
        # Transform the API response into ActivityData objects
        activity_data_objects = []
        for activity_entry in activity_data_response:
            # Each entry is one day of activity data
            timestamp = datetime.fromisoformat(activity_entry["timestamp"])
            activity_score = activity_entry["score"]
            activity_data = ActivityData(timestamp=timestamp, source=self.source_name, score=activity_score)
            activity_data_objects.append(activity_data)

        return activity_data_objects

    def get_steps_data(self, start_date: str | None = None, end_date: str | None = None) -> list[StepsData]:
        """
        Fetch daily steps data for a specified date range and return a list of StepsData objects.

        :param start_date: The start date for fetching steps data in YYYY-MM-DD format. Defaults to yesterday.
        :param end_date: The end date for fetching steps data in YYYY-MM-DD format. Defaults to today.
        :return: A list of StepsData objects with the steps data from the Oura API.
        """
        # Fetch steps data from the Oura API
        activity_response = self.client.get_daily_activity(start_date=start_date, end_date=end_date)
        assert isinstance(activity_response, list)
        # Transform the API response into StepsData objects
        steps_data_objects = []
        for activity_entry in activity_response:
            # Each entry is one day of steps data
            timestamp = datetime.fromisoformat(activity_entry["timestamp"])
            steps = activity_entry["steps"] 
            steps_data = StepsData(timestamp=timestamp, source=self.source_name, score=int(steps))
            steps_data_objects.append(steps_data)

        return steps_data_objects

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence
from health_dashboard.connectors.api_connector import APIConnector
from health_dashboard.models.health_data import HealthData
from health_dashboard.models.run_data import DailyRunData
from health_dashboard.utils import get_secrets
import time
import json
from stravalib import Client, model
from stravalib.client import BatchedResultsIterator

@dataclass
class TempRunData:
    duration: float
    distance: float
        

class StravaConnector(APIConnector):
    def __init__(self):
        super().__init__()
        self.source_name = "strava"
        secrets = get_secrets(".secrets.json")
        self.client_id = secrets["STRAVA_CLIENT_ID"]
        self.client_secret = secrets["STRAVA_CLIENT_SECRET"]
        self.token_file_path = "strava_access_token.json"

    def _get_client(self) -> Client:
        client = Client()
        access_token = self._load_token()

        if self._token_expired(access_token):
            access_token = self._refresh_token(client, access_token)

        self._update_client_token(client, access_token)
        return client

    def _load_token(self) -> dict[str, str]:
        try:
            with open(self.token_file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_token(self, token: dict[str, str]):
        with open(self.token_file_path, "w") as f:
            json.dump(token, f, indent=4)

    def _token_expired(self, access_token: dict[str, str]) -> bool:
        expires_at = access_token.get("expires_at")
        assert expires_at is not None
        expires_at = float(expires_at)
        return datetime.now() > datetime.fromtimestamp(expires_at)

    def _refresh_token(
        self, client: Client, access_token: dict[str, str]
    ) -> dict[str, str]:
        print("Info: Strava token has expired, will refresh")
        refresh_response = client.refresh_access_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            refresh_token=access_token["refresh_token"],
        )
        refresh_response["expires_at"] = int(refresh_response["expires_at"])
        self._save_token(refresh_response)
        print("Refreshed token saved to file")
        return refresh_response

    def _update_client_token(self, client: Client, access_token: dict[str, str]):
        client.access_token = access_token["access_token"]

    def get_all_data(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> Sequence[HealthData]:
        self.client = self._get_client()
        activities = self.client.get_activities(after=start_date, before=end_date)
        run_data = self.get_run_data(activities)
        return run_data
        
    def get_run_data(self, activities: BatchedResultsIterator[model.Activity]) -> list[DailyRunData]:
        run_data = defaultdict(list)
        for activity in activities:
            activity_dict = activity.to_dict()
            if activity_dict["sport_type"] != "Run":
                continue
            duration = activity_dict["moving_time"].seconds / 3600
            distance = activity_dict["distance"] / 1000
            timestamp = activity_dict["start_date"]
            date = timestamp.date()
            run_data[date].append(
                TempRunData(duration=duration, distance=distance)
            )
        daily_run_data = []
        for date, runs in run_data.items():
            total_duration = sum(run.duration for run in runs)
            total_distance = sum(run.distance for run in runs)
            daily_run_data.append(
                DailyRunData(
                    timestamp=date,
                    source=self.source_name,
                    duration=total_duration,
                    distance=total_distance,
                )
            )
        return daily_run_data
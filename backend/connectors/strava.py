from datetime import datetime, timedelta
from typing import TypedDict, cast, Any
import json
import time
import requests
import logging
from stravalib import Client, model
from stravalib.client import BatchedResultsIterator
from stravalib.protocol import AccessInfo
from stravalib.exc import RateLimitExceeded

from backend.models import StravaData
from backend.files import get_secrets
from backend.connectors.base import Connector

class StravaConnector(Connector[StravaData]):
    """Connector for Strava data"""
    def __init__(self):
        """Initialize the StravaConnector with API credentials."""
        secrets = get_secrets(".secrets.json")
        self.client_id = secrets["STRAVA_CLIENT_ID"]
        self.client_secret = secrets["STRAVA_CLIENT_SECRET"]
        self.token_file_path = "strava_access_token.json"
        self.client = None

    @property
    def source_name(self) -> str:
        """Return the name of the data source."""
        return "strava"


    def _get_client(self) -> Client:
        """Get an authenticated Strava client."""
        client = Client()
        access_token = self._load_token()

        if self._token_expired(access_token):
            access_token = self._refresh_token(client, access_token)

        self._update_client_token(client, access_token)
        return client

    def _load_token(self) -> dict[str, Any]:
        """Load the access token from file."""
        try:
            with open(self.token_file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_token(self, token: dict[str, Any]):
        """Save the access token to file."""
        with open(self.token_file_path, "w") as f:
            json.dump(token, f, indent=4)

    def _token_expired(self, access_token: dict[str, Any]) -> bool:
        """Check if the access token has expired."""
        expires_at = access_token.get("expires_at")
        if not expires_at:
            return True
        return datetime.now() > datetime.fromtimestamp(float(expires_at))

    def _refresh_token(
        self, client: Client, access_token: dict[str, Any]
    ) -> dict[str, Any]:
        """Refresh the expired access token."""
        print("Info: Strava token has expired, will refresh")
        refresh_response = client.refresh_access_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            refresh_token=access_token["refresh_token"],
        )
        # Convert AccessInfo to dict using vars()
        refresh_dict = vars(refresh_response)
        token_dict = {
            "access_token": str(refresh_dict["access_token"]),
            "refresh_token": str(refresh_dict["refresh_token"]),
            "expires_at": int(refresh_dict["expires_at"]),
            "token_type": "Bearer"
        }
        self._save_token(token_dict)
        print("Refreshed token saved to file")
        return token_dict

    def _update_client_token(self, client: Client, access_token: dict[str, Any]):
        """Update the client with the access token."""
        client.access_token = access_token["access_token"]

    def get_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> list[StravaData]:
        """Fetch Strava data for the given date range."""
        # Get authenticated client
        if not self.client:
            self.client = self._get_client()

        # Get activities
        activities = self.client.get_activities(
            after=start_date.strftime("%Y-%m-%d"),
            before=end_date.strftime("%Y-%m-%d")
        )

        # Transform activities into StravaData objects
        strava_data_list = []
        for activity in activities:
            # Skip non-run activities or activities with missing data
            if (not hasattr(activity, "type") or 
                activity.type != "Run" or 
                not hasattr(activity, "start_date") or 
                not activity.start_date or 
                not hasattr(activity, "moving_time") or 
                not activity.moving_time or 
                not hasattr(activity, "distance") or 
                not activity.distance):
                continue

            # Convert timestamps and units
            duration_hours = float(activity.moving_time) / 3600  # Convert seconds to hours
            distance_km = float(activity.distance) / 1000  # Convert meters to kilometers

            strava_data = StravaData(
                source=self.source_name,
                date=activity.start_date,
                total_distance_km=distance_km,
                total_duration_hours=duration_hours
            )
            strava_data_list.append(strava_data)

        return strava_data_list 
from datetime import datetime, timedelta
from typing import TypedDict, cast, Any
import pandas as pd
import requests
import json
import logging
from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

from backend.models import GarminData
from backend.files import get_secrets
from backend.connectors.base import Connector

logger = logging.getLogger(__name__)

class DailyTotals(TypedDict):
    distance: float
    duration: float
    steps: int | None
    resting_heart_rate: int | None
    hrv: int | None
    vo2_max: float | None

class GarminConnector(Connector[GarminData]):
    """Connector for Garmin Connect data"""
    def __init__(self):
        """Initialize the GarminConnector with API credentials."""
        secrets = get_secrets(".secrets.json")
        self.email = secrets["GARMIN_EMAIL"]
        self.password = secrets["GARMIN_PASSWORD"]
        self.client = None

    @property
    def source_name(self) -> str:
        """Return the name of the data source."""
        return "garmin"

    def _get_client(self) -> Garmin:
        """Get an authenticated Garmin client."""
        try:
            client = Garmin(self.email, self.password)
            client.login()
            return client
        except (
            GarminConnectConnectionError,
            GarminConnectTooManyRequestsError,
        ) as err:
            logger.error("Error during Garmin Connect authentication: %s", err)
            raise

    def get_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> list[GarminData]:
        """Fetch Garmin running data and steps for the given date range."""
        # Get authenticated client
        if not self.client:
            self.client = self._get_client()

        # Get activities for the date range
        activities = self.client.get_activities_by_date(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            activitytype="running"  # Only get running activities
        )

        # Get steps data for each day in the range
        steps_data: dict[str, int | None] = {}
        try:
            steps_response = self.client.get_daily_steps(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            # The response is a list of daily step entries
            if isinstance(steps_response, list):
                for entry in steps_response:
                    if isinstance(entry, dict):
                        calendar_date = entry.get("calendarDate")
                        steps = entry.get("steps")
                        if isinstance(calendar_date, str) and isinstance(steps, (int, type(None))):
                            steps_data[calendar_date] = steps
        except Exception as e:
            logger.warning(f"Failed to get steps data: {e}")

        # Get RHR and HRV data for each day
        rhr_data: dict[str, int | None] = {}
        hrv_data: dict[str, int | None] = {}
        vo2_max_data: dict[str, float | None] = {}
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            try:
                # Get max metrics data
                max_metrics_response = self.client.get_max_metrics(date_str)
                if isinstance(max_metrics_response, list) and len(max_metrics_response) > 0:
                    first_metric = max_metrics_response[0] # type: ignore
                    if isinstance(first_metric, dict):
                        metrics = first_metric.get("generic", {})
                        vo2_max = metrics.get("vo2MaxPreciseValue")
                        vo2_max_data[date_str] = float(vo2_max) if vo2_max is not None else None
                    else:
                        vo2_max_data[date_str] = None
                else:
                    vo2_max_data[date_str] = None

                # Get RHR data
                rhr_response = self.client.get_rhr_day(date_str)
                if isinstance(rhr_response, dict) and "allMetrics" in rhr_response:
                    metrics = rhr_response["allMetrics"].get("metricsMap", {})
                    rhr_metrics = metrics.get("WELLNESS_RESTING_HEART_RATE", [])
                    if rhr_metrics and isinstance(rhr_metrics, list) and len(rhr_metrics) > 0:
                        rhr_value = int(rhr_metrics[0]["value"])
                        rhr_data[date_str] = rhr_value
                    else:
                        rhr_data[date_str] = None
                else:
                    rhr_data[date_str] = None

                # Get HRV data
                hrv_response = self.client.get_hrv_data(date_str)
                if isinstance(hrv_response, dict) and "hrvSummary" in hrv_response:
                    hrv_summary = hrv_response["hrvSummary"]
                    if "lastNightAvg" in hrv_summary:
                        hrv_value = hrv_summary["lastNightAvg"]
                        hrv_data[date_str] = hrv_value
                    else:
                        hrv_data[date_str] = None
                else:
                    hrv_data[date_str] = None
            except Exception as e:
                logger.warning(f"Failed to get RHR/HRV data for {date_str}: {e}")
                rhr_data[date_str] = None
                hrv_data[date_str] = None
            current_date += timedelta(days=1)

        # Group activities by date and sum up distances and durations
        daily_data: dict[str, DailyTotals] = {}
        for activity in activities:
            date = activity["startTimeLocal"].split(" ")[0]  # Get just the date part
            if date not in daily_data:
                daily_data[date] = {
                    "distance": 0.0,
                    "duration": 0.0,
                    "steps": steps_data.get(date),
                    "resting_heart_rate": rhr_data.get(date),
                    "hrv": hrv_data.get(date),
                    "vo2_max": vo2_max_data.get(date)
                }
            
            # Convert distance from meters to kilometers
            daily_data[date]["distance"] += float(activity["distance"]) / 1000
            # Convert duration from seconds to hours
            daily_data[date]["duration"] += float(activity["duration"]) / 3600

        # Add days that only have steps/RHR/HRV/VO2 max data
        for date in set(list(steps_data.keys()) + list(rhr_data.keys()) + list(hrv_data.keys()) + list(vo2_max_data.keys())):
            if date not in daily_data:
                daily_data[date] = {
                    "distance": 0.0,
                    "duration": 0.0,
                    "steps": steps_data.get(date),
                    "resting_heart_rate": rhr_data.get(date),
                    "hrv": hrv_data.get(date),
                    "vo2_max": vo2_max_data.get(date)
                }

        # Transform into GarminData objects
        garmin_data_list = []
        for date_str, totals in daily_data.items():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            garmin_data = GarminData(
                source=self.source_name,
                date=date,
                total_distance_km=totals["distance"],
                total_duration_hours=totals["duration"],
                steps=totals["steps"],
                resting_heart_rate=totals["resting_heart_rate"],
                hrv=totals["hrv"],
                vo2_max=totals["vo2_max"]
            )
            garmin_data_list.append(garmin_data)

        return garmin_data_list 
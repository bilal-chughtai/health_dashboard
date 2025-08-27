from datetime import datetime, timedelta
from typing import TypedDict, cast, Any
import logging
from oura_ring import OuraClient
import requests

from dashboard.models import OuraData
from dashboard.secret import get_all_secrets
from dashboard.connectors.base import Connector

logger = logging.getLogger(__name__)


class OuraSleepEntry(TypedDict):
    day: str
    score: int
    timestamp: str


class OuraSleepPeriod(TypedDict):
    day: str
    deep_sleep_duration: int
    light_sleep_duration: int
    rem_sleep_duration: int
    total_sleep_duration: int | None
    heart_rate: dict[str, Any] | None
    hrv: dict[str, Any] | None


class OuraReadinessEntry(TypedDict):
    day: str
    score: int
    timestamp: str


class OuraActivityEntry(TypedDict):
    day: str
    score: int
    steps: int
    timestamp: str


class OuraConnector(Connector[OuraData]):
    """Connector for Oura Ring data"""

    def __init__(self):
        """Initialize the OuraConnector with an access token."""
        secrets = get_all_secrets()
        self.access_token = secrets.OURA_ACCESS_TOKEN.get_secret_value()
        self.client = OuraClient(self.access_token)

    @property
    def source_name(self) -> str:
        """Return the name of the data source."""
        return "oura"

    def _calculate_weighted_average(
        self, items: list[float | None], interval: int
    ) -> float | None:
        """Calculate weighted average of a list of values, ignoring None values."""
        if not items or all(x is None for x in items):
            return None

        # Filter out None values and calculate weighted sum
        valid_items = [(x, interval) for x in items if x is not None]
        if not valid_items:
            return None

        total_weight = sum(weight for _, weight in valid_items)
        weighted_sum = sum(value * weight for value, weight in valid_items)

        return weighted_sum / total_weight

    def get_data(self, start_date: datetime, end_date: datetime) -> list[OuraData]:
        """Fetch Oura Ring data for the given date range."""
        # Convert datetime to YYYY-MM-DD strings for the API
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # Get sleep data
        sleep_data = cast(
            list[OuraSleepEntry],
            self.client.get_daily_sleep(start_date=start_str, end_date=end_str),
        )
        sleep_periods = cast(
            list[OuraSleepPeriod],
            self.client.get_sleep_periods(start_date=start_str, end_date=end_str),
        )

        # Get readiness data
        readiness_data = cast(
            list[OuraReadinessEntry],
            self.client.get_daily_readiness(start_date=start_str, end_date=end_str),
        )

        # Get activity data
        activity_data = cast(
            list[OuraActivityEntry],
            self.client.get_daily_activity(start_date=start_str, end_date=end_str),
        )

        # Group sleep periods by day for duration and HR/HRV calculation
        periods_by_day: dict[str, list[OuraSleepPeriod]] = {}
        for period in sleep_periods:
            if period["day"] not in periods_by_day:
                periods_by_day[period["day"]] = []
            periods_by_day[period["day"]].append(period)

        # Transform and combine the data
        oura_data_list = []
        for sleep_entry in sleep_data:
            date = datetime.strptime(sleep_entry["day"], "%Y-%m-%d")

            # Find matching readiness and activity data
            readiness_entry = next(
                (r for r in readiness_data if r["day"] == sleep_entry["day"]), None
            )
            activity_entry = next(
                (a for a in activity_data if a["day"] == sleep_entry["day"]), None
            )

            # Calculate total sleep duration and weighted averages for HR/HRV
            total_duration = 0
            total_hr_weighted = 0
            total_hrv_weighted = 0
            total_weight = 0
            lowest_hr = None

            # New calculations for time in bed, deep sleep, REM sleep, and efficiency
            total_time_in_bed = 0
            total_deep_sleep = 0
            total_rem_sleep = 0
            total_light_sleep = 0

            for period in periods_by_day.get(sleep_entry["day"], []):
                # Calculate duration
                duration = period.get("total_sleep_duration")
                if duration is None:
                    duration = (
                        period["deep_sleep_duration"]
                        + period["light_sleep_duration"]
                        + period["rem_sleep_duration"]
                    )
                total_duration += duration

                # Accumulate sleep stage durations
                total_deep_sleep += period.get("deep_sleep_duration", 0)
                total_rem_sleep += period.get("rem_sleep_duration", 0)
                total_light_sleep += period.get("light_sleep_duration", 0)

                # Use raw time_in_bed field
                period_time_in_bed = period.get("time_in_bed", 0)
                if period_time_in_bed:
                    total_time_in_bed += period_time_in_bed

                # Calculate weighted averages for HR and HRV
                heart_rate_data = period.get("heart_rate")
                if heart_rate_data is not None and isinstance(heart_rate_data, dict):
                    hr_items = heart_rate_data.get("items")
                    hr_interval = heart_rate_data.get("interval")
                    if (
                        hr_items is not None
                        and hr_interval is not None
                        and isinstance(hr_items, list)
                    ):
                        hr_items = cast(list[float | None], hr_items)
                        hr_avg = self._calculate_weighted_average(hr_items, hr_interval)
                        if hr_avg is not None:
                            total_hr_weighted += hr_avg * duration
                            total_weight += duration

                        # Track lowest heart rate
                        valid_hrs = [x for x in hr_items if x is not None]
                        if valid_hrs:
                            period_lowest = int(
                                min(valid_hrs)
                            )  # Convert to int since that's what the model expects
                            if lowest_hr is None or period_lowest < lowest_hr:
                                lowest_hr = period_lowest

                hrv_data = period.get("hrv")
                if hrv_data is not None and isinstance(hrv_data, dict):
                    hrv_items = hrv_data.get("items")
                    hrv_interval = hrv_data.get("interval")
                    if (
                        hrv_items is not None
                        and hrv_interval is not None
                        and isinstance(hrv_items, list)
                    ):
                        hrv_items = cast(list[float | None], hrv_items)
                        hrv_avg = self._calculate_weighted_average(
                            hrv_items, hrv_interval
                        )
                        if hrv_avg is not None:
                            total_hrv_weighted += hrv_avg * duration

            # Calculate final averages
            sleep_heart_rate = (
                total_hr_weighted / total_weight if total_weight > 0 else None
            )
            sleep_hrv = total_hrv_weighted / total_weight if total_weight > 0 else None

            # Calculate sleep efficiency
            sleep_efficiency = None
            if total_time_in_bed > 0 and total_duration > 0:
                sleep_efficiency = (total_duration / total_time_in_bed) * 100

            # Print new calculations for sanity checking
            print(f"Date: {sleep_entry['day']}")
            print(f"  Time in bed: {total_time_in_bed / 3600:.2f}h")
            print(f"  Deep sleep: {total_deep_sleep / 3600:.2f}h")
            print(f"  REM sleep: {total_rem_sleep / 3600:.2f}h")
            print(f"  Light sleep: {total_light_sleep / 3600:.2f}h")
            print(f"  Total sleep: {total_duration / 3600:.2f}h")
            print(
                f"  Sleep efficiency: {sleep_efficiency:.1f}%"
                if sleep_efficiency
                else "  Sleep efficiency: N/A"
            )
            print()

            oura_data = OuraData(
                source=self.source_name,
                date=date,
                sleep_score=sleep_entry.get("score"),
                sleep_duration_hours=total_duration / 3600
                if total_duration > 0
                else None,
                readiness_score=readiness_entry.get("score")
                if readiness_entry
                else None,
                activity_score=activity_entry.get("score") if activity_entry else None,
                steps=activity_entry.get("steps") if activity_entry else None,
                sleep_heart_rate=sleep_heart_rate,
                sleep_lowest_heart_rate=lowest_hr,
                sleep_hrv=sleep_hrv,
                time_in_bed_hours=total_time_in_bed / 3600
                if total_time_in_bed > 0
                else None,
                deep_sleep_hours=total_deep_sleep / 3600
                if total_deep_sleep > 0
                else None,
                rem_sleep_hours=total_rem_sleep / 3600 if total_rem_sleep > 0 else None,
                light_sleep_hours=total_light_sleep / 3600
                if total_light_sleep > 0
                else None,
                sleep_efficiency_percent=sleep_efficiency,
            )
            oura_data_list.append(oura_data)

        return oura_data_list

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import TypeVar, Literal, ClassVar, Dict, Any

class MetricCategory(str, Enum):
    RECOVERY = "recovery"
    ACTIVITY = "activity"
    NUTRITION = "nutrition"

class MetricMetadata(BaseModel):
    """Metadata for health metrics"""
    pretty_name: str = Field(description="Human-readable name for the metric")
    category: MetricCategory = Field(description="Category of the metric")
    description: str = Field(description="Detailed description of the metric")
    unit: str | None = Field(None, description="Unit of measurement if applicable")
    sum_weekly: bool = Field(False, description="Whether to sum this metric over weeks instead of averaging")
    display_delay: int = Field(1, description="Days to wait before displaying (0=same day, 1=next day, etc.)")
    min_value: float | None = Field(None, description="Minimum reasonable value for this metric for random data gen")
    max_value: float | None = Field(None, description="Maximum reasonable value for this metric for random data gen")

class BaseData(BaseModel):
    """Base model for all data"""
    model_config = ConfigDict(extra='ignore')  # Ignore extra fields when loading old data
    
    source: str = Field(description="Source of the data")
    date: datetime = Field(description="Date of the data")

    # Class variable to store metadata
    _field_metadata: ClassVar[Dict[str, MetricMetadata]] = {}

    @classmethod
    def get_field_metadata(cls, field_name: str) -> MetricMetadata | None:
        """Get metadata for a field without affecting serialization"""
        return cls._field_metadata.get(field_name)

class OuraData(BaseData):
    """Complete daily data from Oura Ring"""
    sleep_score: int | None = Field(None, description="Sleep score (0-100)")
    sleep_duration_hours: float | None = Field(None, description="Total sleep duration in hours")
    readiness_score: int | None = Field(None, description="Readiness score (0-100)")
    activity_score: int | None = Field(None, description="Activity score (0-100)")
    steps: int | None = Field(None, description="Daily step count")
    sleep_heart_rate: float | None = Field(None, description="Average heart rate during sleep")
    sleep_lowest_heart_rate: int | None = Field(None, description="Lowest heart rate during sleep")
    sleep_hrv: float | None = Field(None, description="Average heart rate variability during sleep")

    # Define metadata separately from fields
    _field_metadata = {
        "sleep_score": MetricMetadata(
            pretty_name="Sleep Score",
            category=MetricCategory.RECOVERY,
            description="Overall sleep quality score from Oura Ring",
            unit="score",
            sum_weekly=False,
            display_delay=0,
            min_value=60,
            max_value=100
        ),
        "sleep_duration_hours": MetricMetadata(
            pretty_name="Sleep Duration",
            category=MetricCategory.RECOVERY,
            description="Total time spent sleeping",
            unit="hours",
            sum_weekly=False,
            display_delay=0,
            min_value=6,  # Minimum reasonable sleep
            max_value=10  # Maximum reasonable sleep
        ),
        "readiness_score": MetricMetadata(
            pretty_name="Readiness Score",
            category=MetricCategory.RECOVERY,
            description="Overall readiness score from Oura Ring",
            unit="score",
            sum_weekly=False,
            display_delay=0,
            min_value=60,
            max_value=100
        ),
        "activity_score": MetricMetadata(
            pretty_name="Activity Score",
            category=MetricCategory.ACTIVITY,
            description="Overall activity score from Oura Ring",
            unit="score",
            sum_weekly=False,
            display_delay=1,
            min_value=60,
            max_value=100
        ),
        "steps": MetricMetadata(
            pretty_name="Steps",
            category=MetricCategory.ACTIVITY,
            description="Total daily steps",
            unit="steps",
            sum_weekly=False,
            display_delay=1,
            min_value=2000,
            max_value=40000  # Very active day
        ),
        "sleep_heart_rate": MetricMetadata(
            pretty_name="Sleep Avg HR",
            category=MetricCategory.RECOVERY,
            description="Average heart rate during sleep",
            unit="bpm",
            sum_weekly=False,
            display_delay=0,
            min_value=35,  # Very fit athlete
            max_value=60   # High during sleep
        ),
        "sleep_lowest_heart_rate": MetricMetadata(
            pretty_name="Sleep Lowest HR",
            category=MetricCategory.RECOVERY,
            description="Lowest heart rate recorded during sleep",
            unit="bpm",
            sum_weekly=False,
            display_delay=0,
            min_value=40,  # Elite athlete
            max_value=60   # High lowest HR
        ),
        "sleep_hrv": MetricMetadata(
            pretty_name="Sleep Avg HRV",
            category=MetricCategory.RECOVERY,
            description="Average heart rate variability during sleep",
            unit="ms",
            sum_weekly=False,
            display_delay=0,
            min_value=40,  # Very low HRV
            max_value=90  # Very high HRV
        )
    }

class CronometerData(BaseData):
    """Complete daily nutrition data from Cronometer"""
    calories: float | None = Field(None, description="Total calories consumed")
    protein: float | None = Field(None, description="Protein in grams")
    carbs: float | None = Field(None, description="Carbohydrates in grams")
    fat: float | None = Field(None, description="Fat in grams")

    _field_metadata = {
        "calories": MetricMetadata(
            pretty_name="Calories",
            category=MetricCategory.NUTRITION,
            description="Total daily caloric intake",
            unit="kcal",
            sum_weekly=False,
            display_delay=1,
            min_value=1000,  # Minimum safe intake
            max_value=3000  # Very high intake
        ),
        "protein": MetricMetadata(
            pretty_name="Protein",
            category=MetricCategory.NUTRITION,
            description="Total protein intake",
            unit="g",
            sum_weekly=False,
            display_delay=1,
            min_value=50,
            max_value=200  # Very high protein diet
        ),
        "carbs": MetricMetadata(
            pretty_name="Carbs",
            category=MetricCategory.NUTRITION,
            description="Total carbohydrate intake",
            unit="g",
            sum_weekly=False,
            display_delay=1,
            min_value=100,
            max_value=300  # Very high carb diet
        ),
        "fat": MetricMetadata(
            pretty_name="Fat",
            category=MetricCategory.NUTRITION,
            description="Total fat intake",
            unit="g",
            sum_weekly=False,
            display_delay=1,
            min_value=100,
            max_value=300  # Very high fat diet
        )
    }

class StravaData(BaseData):
    """Complete daily run data from Strava"""
    total_distance_km: float | None = Field(None, description="Total distance in kilometers")
    total_duration_hours: float | None = Field(None, description="Total duration in hours")

    _field_metadata = {
        "total_distance_km": MetricMetadata(
            pretty_name="Running Distance",
            category=MetricCategory.ACTIVITY,
            description="Total running distance",
            unit="km",
            sum_weekly=True,
            display_delay=1,
            min_value=0,
            max_value=10  # marathon
        ),
        "total_duration_hours": MetricMetadata(
            pretty_name="Running Duration",
            category=MetricCategory.ACTIVITY,
            description="Total running time",
            unit="hours",
            sum_weekly=True,
            display_delay=1,
            min_value=0,
            max_value=4  
        )
    }

class GarminData(BaseData):
    """Data from Garmin Connect activities."""
    total_distance_km: float | None = Field(None, description="Total distance in kilometers")
    total_duration_hours: float | None = Field(None, description="Total duration in hours")
    steps: int | None = Field(None, description="Daily step count")
    resting_heart_rate: int | None = Field(None, description="Resting heart rate in BPM")
    hrv: int | None = Field(None, description="Heart rate variability in ms")
    vo2_max: float | None = Field(None, description="VO2 max value")

    _field_metadata = {
        "total_distance_km": MetricMetadata(
            pretty_name="Running Distance",
            category=MetricCategory.ACTIVITY,
            description="Total activity distance from Garmin",
            unit="km",
            sum_weekly=True,
            display_delay=0,
            min_value=0,
            max_value=4  # Ultra marathon
        ),
        "total_duration_hours": MetricMetadata(
            pretty_name="Running Duration",
            category=MetricCategory.ACTIVITY,
            description="Total activity duration from Garmin",
            unit="hours",
            sum_weekly=True,
            display_delay=0,
            min_value=0,
            max_value=4  # Full day of activity
        ),
        "steps": MetricMetadata(
            pretty_name="Steps",
            category=MetricCategory.ACTIVITY,
            description="Total daily steps from Garmin",
            unit="steps",
            sum_weekly=False,
            display_delay=1,
            min_value=2000,
            max_value=30000  # Very active day
        ),
        "resting_heart_rate": MetricMetadata(
            pretty_name="Resting HR",
            category=MetricCategory.RECOVERY,
            description="Resting heart rate measured by Garmin",
            unit="bpm",
            sum_weekly=False,
            display_delay=1,
            min_value=40,  # Elite athlete
            max_value=60  # High resting HR
        ),
        "hrv": MetricMetadata(
            pretty_name="Sleep Avg HRV",
            category=MetricCategory.RECOVERY,
            description="Heart rate variability measured by Garmin",
            unit="ms",
            sum_weekly=False,
            display_delay=0,
            min_value=40,  # Very low HRV
            max_value=90  # Very high HRV
        ),
        "vo2_max": MetricMetadata(
            pretty_name="VO2 Max",
            category=MetricCategory.ACTIVITY,
            description="Maximum oxygen consumption measured by Garmin",
            unit="ml/kg/min",
            sum_weekly=False,
            display_delay=0,
            min_value=45,  # Very low VO2 max
            max_value=60   # Elite athlete
        )
    }

class ManualData(BaseData):
    """Data manually entered for tracking lifts and bodyweight"""
    bodyweight_kg: float | None = Field(None, description="Bodyweight in kilograms")
    lift: bool | None = Field(None, description="Whether a lift was done on this day")

    _field_metadata = {
        "bodyweight_kg": MetricMetadata(
            pretty_name="Bodyweight",
            category=MetricCategory.NUTRITION,
            description="Daily bodyweight measurement",
            unit="kg",
            sum_weekly=False,
            display_delay=0,
            min_value=70,  # Very low weight
            max_value=90  # Very high weight
        ),
        "lift": MetricMetadata(
            pretty_name="Lift",
            category=MetricCategory.ACTIVITY,
            description="Whether a lift was done on this day",
            unit=None,
            sum_weekly=True,
            display_delay=0,
            min_value=0,  # Boolean represented as 0/1
            max_value=1
        )
    }

AppData = TypeVar('AppData', OuraData, CronometerData, StravaData, GarminData, ManualData)

class DailyData(BaseModel):
    """Combined daily data from all sources"""
    model_config = ConfigDict(extra='ignore')  # Ignore extra fields when loading old data
    
    date: datetime = Field(description="Date of the data")
    oura: OuraData | None = None
    cronometer: CronometerData | None = None
    strava: StravaData | None = None
    garmin: GarminData | None = None
    manual: ManualData | None = None
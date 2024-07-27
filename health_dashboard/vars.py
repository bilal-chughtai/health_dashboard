from health_dashboard.models.activity_data import ActivityData
from health_dashboard.models.bodyweight_data import BodyweightData
from health_dashboard.models.health_data import HealthData
from health_dashboard.models.lift_data import LiftData
from health_dashboard.models.nutrition_data import NutritionData
from health_dashboard.models.readiness_data import ReadinessData
from health_dashboard.models.run_data import DailyRunData
from health_dashboard.models.sleep_data import SleepData
from health_dashboard.models.steps_data import StepsData

# Map for resolving type strings to classes
type_map = {
    "SleepData": SleepData,
    "ReadinessData": ReadinessData,
    "ActivityData": ActivityData,
    "StepsData": StepsData,
    "BodyweightData": BodyweightData,
    "LiftData": LiftData,
    "NutritionData": NutritionData,
    "DailyRunData": DailyRunData,
}


df_col_order = [
    "date",
    "bodyweight",
    "sleep",
    "readiness",
    "activity",
    "steps",
    "lift",
    "nutrition_calories",
    "nutrition_carbs",
    "nutrition_fat",
    "nutrition_protein",
    "sleep_duration",
    "daily_run_duration",
    "daily_run_distance"
]

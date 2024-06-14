from datetime import datetime
from health_dashboard.models.health_data import HealthData


class NutritionData(HealthData):
    def __init__(
        self,
        timestamp: datetime,
        source: str,
        calories: float,
        protein: float,
        carbs: float,
        fat: float,
    ):
        """
        Initialize a NutritionData instance.

        :param timestamp: A datetime object representing when this nutrition data was recorded.
        :param source: A string representing the source of this nutrition data.
        :param calories: A float representing the number of calories consumed.
        :param protein: A float representing the amount of protein consumed (in grams).
        :param carbs: A float representing the amount of carbohydrates consumed (in grams).
        :param fat: A float representing the amount of fat consumed (in grams).
        """
        super().__init__(timestamp, source)
        self.calories = calories
        self.protein = protein
        self.carbs = carbs
        self.fat = fat

    def __repr__(self) -> str:
        return f"NutritionData({super().__repr__()}, calories: {self.calories}, protein: {self.protein}g, carbs: {self.carbs}g, fat: {self.fat}g)"

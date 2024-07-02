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
        super().__init__(timestamp, source)
        self.calories = calories
        self.protein = protein
        self.carbs = carbs
        self.fat = fat

    def __repr__(self) -> str:
        return f"NutritionData({super().__repr__()}, calories: {self.calories}, protein: {self.protein}g, carbs: {self.carbs}g, fat: {self.fat}g)"
    
    @staticmethod
    def id() -> str:
        return "nutrition"

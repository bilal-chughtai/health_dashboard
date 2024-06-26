import json
from typing import Dict, List

from health_dashboard.models.activity_data import ActivityData
from health_dashboard.models.bodyweight_data import BodyweightData
from health_dashboard.models.health_data import \
    HealthData  # Ensure this is your base class for health data types
from health_dashboard.models.lift_data import LiftData
from health_dashboard.models.readiness_data import ReadinessData
from health_dashboard.models.sleep_data import SleepData
from health_dashboard.models.steps_data import StepsData


import json
from typing import Dict

from health_dashboard.models.health_data import HealthData 
from health_dashboard.models.sleep_data import SleepData 
from health_dashboard.models.nutrition_data import NutritionData

# Map for resolving type strings to classes
type_map = {
    'SleepData': SleepData,
    'ReadinessData': ReadinessData,
    'ActivityData': ActivityData,
    'StepsData': StepsData,
    'BodyweightData': BodyweightData,
    'LiftData': LiftData,
    'NutritionData': NutritionData
}

class DataStore:
    def __init__(self, filename: str = "data/health_data_store.json"):
        self.filename = filename

    def load_data(self) -> Dict[str, HealthData]:
        """Load health data from a JSON file into a dictionary."""
        
        try:
            with open(self.filename, "r") as file:
                data = json.load(file)
                return {k: self._deserialize(v) for k, v in data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            print("No data store found. Creating data store")
            self.save_data({})
            return {}

    def save_data(self, health_data_dict: Dict[str, HealthData]):
        """Save the health data dictionary to a JSON file."""
        with open(self.filename, "w") as file:
            json.dump({k: self._serialize(v) for k, v in health_data_dict.items()}, file, indent=4, default=str)

    def add_data(self, new_data: HealthData):
        """Add or update health data in the store."""
        data_key = self._generate_key(new_data)
        data_dict = self.load_data()

        # Update the entry directly since dictionary keys are unique
        data_dict[data_key] = new_data

        # Save the updated dictionary back to the file
        self.save_data(data_dict)

    def get_all_data(self) -> List[HealthData]:
        """Retrieve all health data from the store."""
        data_dict = self.load_data()
        return list(data_dict.values())

    def _serialize(self, data: HealthData) -> Dict:
        """Convert HealthData object to a dictionary, including the type for deserialization."""
        data_dict = data.__dict__.copy()
        data_dict['type'] = data.__class__.__name__
        return data_dict

    def _deserialize(self, data: Dict) -> HealthData:
        """Convert a dictionary back to a HealthData object based on its type."""
        data_type = data.pop('type', None)
        data_class = type_map.get(data_type)
        if data_class:
            return data_class(**data)
        raise ValueError(f"Unknown data type: {data_type}")

    def _generate_key(self, data: HealthData) -> str:
        """Generate a unique key for each data entry based on its class name and timestamp."""
        return f"{data.__class__.__name__}_{data.timestamp.isoformat()}"




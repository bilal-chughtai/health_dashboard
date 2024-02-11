from models.health_data import HealthData
from collections import defaultdict
import pandas as pd

CLASS_NAMES_TO_COLUMN_NAMES = {
    "SleepData": "sleep",
    "ReadinessData": "readiness",
    "ActivityData": "activity"
}


class DataFrameExporter:
    def __init__(self):
        pass

    def list_to_dataframe(self, data_list: list[HealthData]) -> pd.DataFrame:
        # Prepare a dictionary to hold data with days as keys
        data_dict = defaultdict(lambda: defaultdict(list))

        # Iterate over the list to populate the dictionary
        for data in data_list:
            day = data.timestamp.date()
            class_name = data.__class__.__name__
            
            # Dynamically find score attributes and values
            for attr, value in data.__dict__.items():
                if "score" in attr:
                    data_dict[day][f"{CLASS_NAMES_TO_COLUMN_NAMES[class_name]}_{attr}"].append(value)

        # Convert the nested dictionary into a DataFrame-friendly format
        formatted_data = []
        for day, scores in data_dict.items():
            row = {'day': day}
            for score_type, score_values in scores.items():
                # Assuming we want the average score if there are multiple entries per day
                row[score_type] = sum(score_values) / len(score_values)
            formatted_data.append(row)

        # create the dataframe
        df = pd.DataFrame(formatted_data)
        df = df.sort_values(by='day')
        
        return df
    
    def write_df_to_csv(self, df: pd.DataFrame, filename: str = "data/health_data.csv"):
        df.to_csv(filename, index=False)
        print(f"Data successfully exported to CSV: '{filename}'.")

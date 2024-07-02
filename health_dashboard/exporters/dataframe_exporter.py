from datetime import datetime
from health_dashboard.models.health_data import HealthData
from collections import defaultdict
import pandas as pd
from health_dashboard.vars import df_col_order


# TODO: figure out a better place for this to live

class DataFrameExporter:
    def __init__(self):
        pass

    def list_to_dataframe(self, data_list: list[HealthData]) -> pd.DataFrame:
        # Prepare a dictionary to hold data with days as keys
        data_dict = defaultdict(lambda: defaultdict(list))

        # Iterate over the list to populate the dictionary
        for data in data_list:
            day = data.timestamp.date()
            
            # Dynamically find score attributes and values
            for attr, value in data.__dict__.items():
                if "timestamp" in attr or attr.startswith("_") or "source" in attr:
                    # ignore these attributes
                    continue
                if "score" in attr:
                    data_dict[day][f"{data.id()}"].append(value)
                else:
                    data_dict[day][f"{data.id()}_{attr}"].append(value)

        # Convert the nested dictionary into a DataFrame-friendly format
        formatted_data = []
        for day, scores in data_dict.items():
            row = {'date': day}
            for score_type, score_values in scores.items():
                # Assuming we want the average score if there are multiple entries per day
                row[score_type] = score_values[0] if len(score_values) == 1 else sum(score_values) / len(score_values)
            formatted_data.append(row)

        # create the dataframe
        df = pd.DataFrame(formatted_data)
        df = df.sort_values(by='date')
        df = df[df_col_order]
        return df

    def write_df_to_csv(self, df: pd.DataFrame, filename: str = "data/health_data.csv"):
        df.to_csv(filename, index=False)
        print(f"{datetime.now()}: Data successfully exported to CSV: '{filename}'.")

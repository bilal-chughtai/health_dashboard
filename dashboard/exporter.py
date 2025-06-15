import pandas as pd
from datetime import datetime
from typing import List
from pathlib import Path
from dashboard.models import DailyData
from .registry import registry

def flatten_daily_data(daily: DailyData) -> dict:
    row = {"date": daily.date}
    # Use registry to get all sources
    for source_name in registry.get_sources():
        source_obj = getattr(daily, source_name, None)
        if source_obj is not None:
            for attr, value in source_obj.model_dump().items():
                if attr == "date" or attr == "source":
                    continue
                row[f"{source_name}__{attr}"] = value
    return row

class DataFrameExporter:
    @staticmethod
    def list_to_dataframe(data: List[DailyData]) -> pd.DataFrame:
        rows = [flatten_daily_data(d) for d in data]
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values(by="date")
        return df

    @staticmethod
    def write_df_to_csv(df: pd.DataFrame, filename: Path) -> None:
        """Write the DataFrame to a CSV file."""
        df.to_csv(filename, index=False) 

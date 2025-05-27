import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from typing import cast, List, Optional

from dashboard.models import AppData, DailyData
from dashboard.connectors import get_connectors
from dashboard.registry import registry
from dashboard.data_store import load_data, save_data, update_data
from dashboard.exporter import DataFrameExporter
from dashboard.files import download_and_decrypt_json, encrypt_and_upload_json, encrypt_and_upload_csv

def assemble_app_data_into_daily_data(app_data: list[AppData]) -> list[DailyData]:
    """Assemble app data into DailyData objects, grouped by date."""
    data_by_date = defaultdict(dict)
    for data in app_data:
        data_by_date[data.date][data.source] = data

    daily_data_list = []
    for date, sources in data_by_date.items():
        daily_data = DailyData(date=date)
        for source in registry.get_sources():
            setattr(daily_data, source, sources.get(source))
        daily_data_list.append(daily_data)
    return sorted(daily_data_list, key=lambda x: x.date)


def get_daily_data(start_date: datetime, end_date: datetime, only_connectors: Optional[List[str]] = None) -> list[DailyData]:
    """Fetch and combine data from all connectors (or only those in only_connectors) for the given date range."""
    all_app_data = []
    for connector in get_connectors():
        if only_connectors is not None and connector.source_name not in only_connectors:
            continue
        print(f"Fetching data from connector: {connector.source_name}...")
        try:
            data = connector.get_data(start_date, end_date)
            all_app_data.extend(data)
        except Exception as e:
            print(f"Warning: Failed to fetch data from {connector.source_name}: {str(e)}")
            continue
    return assemble_app_data_into_daily_data(all_app_data)


def main():
    parser = argparse.ArgumentParser(description="Fetch health data for a given past number of days.")
    parser.add_argument("--past_days", type=int, default=7, help="Number of past days to fetch data (default: 7)")
    parser.add_argument("--apps", type=str, help="Comma-separated list of app names to fetch data from (e.g. oura,garmin) (default: use all apps)")
    parser.add_argument("--online", action="store_true", help="Sync data with AWS S3 (download at start, upload at end)")
    args = parser.parse_args()

    # (0) If online mode, try to download data from AWS
    if args.online:
        print("Online mode: Attempting to download data from AWS...")
        if download_and_decrypt_json():
            print("Successfully downloaded data from AWS.")
        else:
            print("No existing data found in AWS, using local data.")

    # (1) Load old data
    old_data = load_data()
    print(f"Loaded {len(old_data)} old DailyData entries.")

    # (2) Fetch new data (for the past_days days)
    # Ignore today's data, because it's not complete yet
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=args.past_days)
    only_connectors = args.apps.split(",") if args.apps else None
    new_data: list[DailyData] = get_daily_data(start_date, end_date, only_connectors)
    print(f"Fetched {len(new_data)} new DailyData entries.")

    # (3) Update (merge) old and new data (overwriting by date) using update_data
    updated_data = update_data(old_data, new_data)
    print(f"Updated data now contains {len(updated_data)} DailyData entries.")

    # (4) Save the updated list to a JSON file (using save_data)
    save_data(updated_data)
    print(f"Updated DailyData saved locally.")

    # (5) Export a CSV (using DataFrameExporter)
    df = DataFrameExporter.list_to_dataframe(updated_data)
    DataFrameExporter.write_df_to_csv(df)
    print(f"CSV exported locally.")

    # (6) If online mode, upload both files to AWS
    if args.online:
        print("Online mode: Uploading data to AWS...")
        encrypt_and_upload_json()
        encrypt_and_upload_csv()
        print("Successfully uploaded data to AWS.")


if __name__ == "__main__":
    main()
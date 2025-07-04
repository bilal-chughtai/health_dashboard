import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from typing import cast, List, Optional
from pathlib import Path

from dashboard.models import AppData, DailyData
from dashboard.connectors import get_connectors
from dashboard.registry import registry
from dashboard.data_store import load_data, save_data, update_data
from dashboard.exporter import DataFrameExporter
from dashboard.files import download_and_decrypt_file, encrypt_and_upload_file
from dashboard.random import generate_random_data

# Default file paths
DEFAULT_JSON_PATH = Path("data/health_data.json")
DEFAULT_CSV_PATH = Path("data/health_data.csv")

# Random data file paths
RANDOM_JSON_PATH = Path("data/random_health_data.json")
RANDOM_CSV_PATH = Path("data/random_health_data.csv")


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


def random_main(online: bool = False) -> None:
    """Generate 2 years of random data and save it locally/online."""
    print("Generating 2 years of random health data...")
    
    # Generate random data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*2)
    random_data = generate_random_data(start_date, end_date)
    print(f"Generated {len(random_data)} days of random data")
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    
    # Export to CSV
    df = DataFrameExporter.list_to_dataframe(random_data)
    DataFrameExporter.write_df_to_csv(df, RANDOM_CSV_PATH)
    print(f"Random data CSV exported to {RANDOM_CSV_PATH}")
    
    # If online mode, upload to AWS
    if online:
        print("Online mode: Uploading random data to AWS...")
        encrypt_and_upload_file(RANDOM_CSV_PATH)
        print("Successfully uploaded random data to AWS.")


def online_main(past_days: int, only_connectors: Optional[List[str]] = None) -> None:
    """Main function for fetching and syncing real data."""
    # (0) Try to download data from AWS
    print("Online mode: Attempting to download data from AWS...")
    if download_and_decrypt_file(DEFAULT_JSON_PATH):
        print("Successfully downloaded data from AWS.")
    else:
        print("No existing data found in AWS, using local data.")

    # (1) Load old data
    old_data = load_data(DEFAULT_JSON_PATH)
    print(f"Loaded {len(old_data)} old DailyData entries.")

    # (2) Fetch new data (for the past_days days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=past_days)
    new_data: list[DailyData] = get_daily_data(start_date, end_date, only_connectors)
    print(f"Fetched {len(new_data)} new DailyData entries.")

    # (3) Update (merge) old and new data
    updated_data = update_data(old_data, new_data)
    print(f"Updated data now contains {len(updated_data)} DailyData entries.")

    # (4) Save the updated list to a JSON file
    save_data(updated_data, DEFAULT_JSON_PATH)
    print(f"Updated DailyData saved locally.")

    # (5) Export a CSV
    df = DataFrameExporter.list_to_dataframe(updated_data)
    DataFrameExporter.write_df_to_csv(df, DEFAULT_CSV_PATH)
    print(f"CSV exported locally.")

    # (6) Upload both files to AWS
    print("Online mode: Uploading data to AWS...")
    encrypt_and_upload_file(DEFAULT_JSON_PATH)
    encrypt_and_upload_file(DEFAULT_CSV_PATH)
    print("Successfully uploaded data to AWS.")


def main():
    parser = argparse.ArgumentParser(description="Fetch health data for a given past number of days.")
    parser.add_argument("--past_days", type=int, default=7, help="Number of past days to fetch data (default: 7)")
    parser.add_argument("--apps", type=str, help="Comma-separated list of app names to fetch data from (e.g. oura,garmin) (default: use all apps)")
    parser.add_argument("--online", action="store_true", help="Sync data with AWS S3 (download at start, upload at end)")
    parser.add_argument("--random", action="store_true", help="Generate 2 years of random data instead of fetching real data")
    args = parser.parse_args()

    if args.random:
        random_main(args.online)
    else:
        online_main(args.past_days, args.apps.split(",") if args.apps else None)


if __name__ == "__main__":
    main()
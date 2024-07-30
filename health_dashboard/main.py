import os
from dotenv import load_dotenv
from health_dashboard.datastore.data_store import DataStore
from health_dashboard.exporters.google_sheet_exporter import GoogleSheetExporter
from health_dashboard.exporters.dataframe_exporter import DataFrameExporter
from datetime import datetime, timedelta

from health_dashboard.connectors.oura_connector import OuraConnector
from health_dashboard.connectors.gsheet_connector import GSheetConnector
from health_dashboard.connectors.cronometer_connector import CronometerConnector
from health_dashboard.connectors.strava_connector import StravaConnector


def get_connector_data(connector, start_date, end_date):
    try:
        print(f"{datetime.now()}: Getting data from {connector.source_name}...")
        return connector.get_all_data(start_date, end_date)
    except Exception as e:
        print(f"Error getting data from {connector.source_name}: {str(e)}")
        return []


def main():
    # Initialize connectors
    oura_connector = OuraConnector()
    gsheet_connector = GSheetConnector()
    cronometer_connector = CronometerConnector()
    strava_connector = StravaConnector()
    connectors = [
        oura_connector,
        gsheet_connector,
        cronometer_connector,
        strava_connector,
    ]

    # Initialize the DataStore
    data_store = DataStore()

    # get todays date and a week ago
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    week_ago = today - timedelta(days=7)

    tomorrow_str = tomorrow.isoformat()
    week_ago_str = week_ago.isoformat()

    # Get data and store it using DataStore
    for connector in connectors:
        data = get_connector_data(connector, week_ago_str, tomorrow_str)
        for data_entry in data:
            data_store.add_data(data_entry)

    # Retrieve and print all stored data
    all_stored_data = data_store.get_all_data()

    dataframe_exporter = DataFrameExporter()
    df = dataframe_exporter.list_to_dataframe(all_stored_data)
    dataframe_exporter.write_df_to_csv(df)
    google_sheet_exporter = GoogleSheetExporter()
    google_sheet_exporter.export_dataframe_to_sheet(df)


if __name__ == "__main__":
    main()

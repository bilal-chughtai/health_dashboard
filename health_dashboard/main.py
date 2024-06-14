import os
from dotenv import load_dotenv
from health_dashboard.connectors.oura_connector import OuraConnector
from health_dashboard.datastore.data_store import DataStore 
from health_dashboard.exporters.google_sheet_exporter import GoogleSheetExporter
from health_dashboard.exporters.dataframe_exporter import DataFrameExporter
from datetime import datetime, timedelta

from health_dashboard.connectors.gsheet_connector import GSheetConnector
from health_dashboard.connectors.cronometer_connector import CronometerConnector

def main():
    load_dotenv()
    oura_access_token = os.getenv('OURA_ACCESS_TOKEN')
    
    # Initialize connectors
    oura_connector = OuraConnector(oura_access_token)
    gsheet_connector = GSheetConnector()
    cronometer_connector = CronometerConnector()
    connectors = [oura_connector, gsheet_connector, cronometer_connector]
    
    # Initialize the DataStore
    data_store = DataStore()
    
    # get todays date and a week ago
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    today_str = today.isoformat()
    week_ago_str = week_ago.isoformat()
    
    # Get data and store it using DataStore
    for connector in connectors:
        print(f"Getting data from {connector.source_name}...")
        data = connector.get_all_data(week_ago_str, today_str)  
        for data_entry in data:
            data_store.add_data(data_entry)
    
    # Retrieve and print all stored data
    all_stored_data = data_store.get_all_data()
    
    dataframe_exporter = DataFrameExporter()
    df = dataframe_exporter.list_to_dataframe(all_stored_data)
    dataframe_exporter.write_df_to_csv(df)
    google_sheet_exporter = GoogleSheetExporter()
    google_sheet_exporter.export_dataframe_to_sheet(df)
    


if __name__ == '__main__':
    main()

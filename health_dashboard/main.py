import os
from dotenv import load_dotenv
from connectors.oura_connector import OuraConnector
from datastore.data_store import DataStore 
from exporters.google_sheet_exporter import GoogleSheetExporter
from datetime import datetime, timedelta

def main():
    load_dotenv()
    oura_access_token = os.getenv('OURA_ACCESS_TOKEN')
    
    # Initialize connectors
    oura_connector = OuraConnector(oura_access_token)
    connectors = [oura_connector]
    
    # Initialize the DataStore
    data_store = DataStore()
    
    # get todays date and a week ago
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    today_str = today.isoformat()
    week_ago_str = week_ago.isoformat()
    
    # Get data and store it using DataStore
    for connector in connectors:
        data = connector.get_all_data(week_ago_str, today_str)  
        for data_entry in data:
            data_store.add_data(data_entry)
    
    # Retrieve and print all stored data
    all_stored_data = data_store.get_all_data()
    
    # Initialize the GoogleSheetExporter
    google_sheet_exporter = GoogleSheetExporter()
    df = google_sheet_exporter.list_to_dataframe(all_stored_data)
    google_sheet_exporter.export_dataframe_to_sheet(df)
    


if __name__ == '__main__':
    main()

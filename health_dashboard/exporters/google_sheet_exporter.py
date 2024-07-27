from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe
import pandas as pd
from collections import defaultdict


class GoogleSheetExporter:
    def __init__(self, credentials_json_path="google_service_account.json"):
        self.credentials_json_path = credentials_json_path
        self.client = self.authenticate_google_sheets()
        self.sheet_name = "Health"
        self.worksheet_name = "api"
        
    def authenticate_google_sheets(self):
        """Authenticate with Google Sheets API using service account credentials."""
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_json_path, scope) # type: ignore
        return gspread.authorize(creds) # type: ignore

    def export_dataframe_to_sheet(self, df):
        """
        Export a pandas DataFrame to a Google Sheet.

        Parameters:
        - df: The pandas DataFrame to export.
        - sheet_name: The name of the Google Sheet (must already exist).
        - worksheet_name: The name of the worksheet in the Google Sheet to export to (defaults to 'Sheet1').
        """
        try:
            sheet = self.client.open(self.sheet_name).worksheet(self.worksheet_name)
        except gspread.SpreadsheetNotFound:
            print(f"Spreadsheet named '{self.sheet_name}' not found.")
            return
        except gspread.WorksheetNotFound:
            print(f"Worksheet named '{self.worksheet_name}' not found in '{self.sheet_name}'.")
            return
        
        # Use gspread_dataframe to export the DataFrame to the specified Google Sheet and worksheet
        df = self.add_missing_days(df)
        set_with_dataframe(sheet, df, include_index=False)

        print(f"{datetime.now()}: Data successfully exported to Google Sheets: '{self.sheet_name}' in worksheet '{self.worksheet_name}'.")
    
    def add_missing_days(self, df):
        """Add missing days to the dataframe and fill in the missing values with blank strings.
        
        Parameters:
        - df: The dataframe to add missing days to.
        """
        # Create a defaultdict to store the data
        data = defaultdict(list)
        
        # Get the date range from the dataframe
        date_range = pd.date_range(start=df['date'].min(), end=df['date'].max())
        
        # Iterate over the date range and add missing days to the defaultdict
        for date in date_range:
            date = date.date()
            if date not in df['date'].values:
                data['date'].append(date)
                for metric in df.columns[1:]:
                    data[metric].append('')
        
        # Create a new dataframe from the defaultdict
        missing_days_df = pd.DataFrame(data)
        
        # Concatenate the original dataframe and the new dataframe with missing days
        df = pd.concat([df, missing_days_df])
        
        # Sort the dataframe by date
        df = df.sort_values(by='date', ascending=False)
        
        return df
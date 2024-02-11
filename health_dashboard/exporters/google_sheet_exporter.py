import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe
import pandas as pd
from models.health_data import HealthData
from collections import defaultdict

CLASS_NAMES_TO_COLUMN_NAMES = {
    "SleepData": "sleep",
    "ReadinessData": "readiness",
    "ActivityData": "activity"
}

class GoogleSheetExporter:
    def __init__(self, credentials_json_path="google_service_account.json"):
        self.credentials_json_path = credentials_json_path
        self.client = self.authenticate_google_sheets()
        self.sheet_name = "Health"
        self.worksheet_name = "api"
        
    def authenticate_google_sheets(self):
        """Authenticate with Google Sheets API using service account credentials."""
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_json_path, scope)
        return gspread.authorize(creds)

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
        set_with_dataframe(sheet, df, include_index=False)

        print(f"Data successfully exported to Google Sheets: '{self.sheet_name}' in worksheet '{self.worksheet_name}'.")
        
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

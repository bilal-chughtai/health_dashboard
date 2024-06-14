from datetime import datetime
from health_dashboard.connectors.api_connector import APIConnector
from oauth2client.service_account import ServiceAccountCredentials
import gspread

from health_dashboard.models.bodyweight_data import BodyweightData
from health_dashboard.models.lift_data import LiftData

class GSheetConnector(APIConnector):
    def __init__(self, credentials_json_path="google_service_account.json"):
        self.credentials_json_path = credentials_json_path
        self.client = self.authenticate_google_sheets()
        self.sheet_name = "Health"
        self.worksheet_name = "manual"
        self.source_name = "google_sheets"
        
    def authenticate_google_sheets(self):
        """Authenticate with Google Sheets API using service account credentials."""
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_json_path, scope)
        return gspread.authorize(creds)

    def get_all_data(self, start_date: str, end_date: str):
        """
        Note that the start_date and end_date parameters are not used in this method.
        """
        sheet = self.client.open(self.sheet_name).worksheet(self.worksheet_name)
        all_records = sheet.get_all_records()
        all_bodyweight_data = self.get_bodyweight_data(all_records)
        all_lift_data = self.get_lift_data(all_records)
        return all_bodyweight_data + all_lift_data

            
    def get_timestamp(self, date_str: str) -> datetime:
        """
        Convert a date string in the format "YYYY-MM-DD" to a datetime object.
        """
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return None
        
    def get_bodyweight_data(self, records: list[dict[str, str]]) -> list[BodyweightData]:
        """
        Convert a list of records from the Google Sheet into BodyweightData objects.
        """
        bodyweight_data = []
        for record in records:
            date_str = record.get("date")
            weight_str = record.get("bodyweight")
            if date_str and weight_str:
                timestamp = self.get_timestamp(date_str)
                weight = float(weight_str.removesuffix("kg"))
                bodyweight = BodyweightData(timestamp=timestamp, source="google_sheet", score=weight)
                bodyweight_data.append(bodyweight)
        return bodyweight_data
    
    def get_lift_data(self, records: list[dict[str, str]]) -> list[LiftData]:
        """
        Convert a list of records from the Google Sheet into LiftData objects.
        """
        lift_data = []
        for record in records:
            date_str = record.get("date")
            lift_str = record.get("lift")
            timestamp = self.get_timestamp(date_str)
            lift = 1 if lift_str == "TRUE" else 0
            if timestamp is not None and timestamp < datetime.now() and lift == 1:
                lift = LiftData(timestamp=timestamp, source="google_sheet", score=lift)
                lift_data.append(lift)
        return lift_data
    
    
    
        
        
from datetime import datetime
from typing import Sequence, Type
from health_dashboard.connectors.api_connector import APIConnector
from oauth2client.service_account import ServiceAccountCredentials # type: ignore
import gspread # type: ignore

from health_dashboard.models.bodyweight_data import BodyweightData
from health_dashboard.models.health_data import HealthData
from health_dashboard.models.lift_data import LiftData

class GSheetConnector(APIConnector):
    def __init__(self, credentials_json_path: str ="google_service_account.json"):
        self.credentials_json_path = credentials_json_path
        self.client = self.authenticate_google_sheets()
        self.sheet_name = "Health"
        self.worksheet_name = "manual"
        self.source_name = "google_sheets"
        
    def authenticate_google_sheets(self):
        """Authenticate with Google Sheets API using service account credentials."""
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_json_path, scope) # type: ignore
        return gspread.authorize(creds) # type: ignore

    def get_all_data(self, start_date: str | None, end_date: str | None) -> Sequence[HealthData]:
        """
        Note that the start_date and end_date parameters are not used in this method.
        """
        if start_date or end_date:
            print(f"{datetime.now()}: Warning: start_date and end_date parameters are not used in GSheetConnector.get_all_data")
            
        sheet = self.client.open(self.sheet_name).worksheet(self.worksheet_name)
        all_records = sheet.get_all_records()
        all_bodyweight_data = self.get_bodyweight_data(all_records)
        all_lift_data = self.get_lift_data(all_records)
        return list(all_bodyweight_data) + list(all_lift_data)

            
    def get_timestamp(self, date_str: str) -> datetime:
        """
        Convert a date string in the format "YYYY-MM-DD" to a datetime object.
        """
        return datetime.strptime(date_str, "%Y-%m-%d")
        
    def get_bodyweight_data(self, records: list[dict[str, int|float|str]]) -> Sequence[BodyweightData]:
        """
        Convert a list of records from the Google Sheet into BodyweightData objects.
        """
        bodyweight_data = []
        for record in records:
            date_str = record.get("date")
            weight_str = record.get("bodyweight")
            if date_str and weight_str:
                if not isinstance(date_str, str):
                    date_str = str(date_str)
                timestamp = self.get_timestamp(date_str)
                if not isinstance(weight_str, str):
                    weight_str = str(weight_str)
                weight = float(weight_str.removesuffix("kg"))
                bodyweight = BodyweightData(timestamp=timestamp, source="google_sheet", score=weight)
                bodyweight_data.append(bodyweight)
        return bodyweight_data
    
    def get_lift_data(self, records: list[dict[str, str | int | float]]) -> Sequence[LiftData]:
        """
        Convert a list of records from the Google Sheet into LiftData objects.
        """
        lift_data = []
        for record in records:
            date_str = record.get("date")
            lift_str = record.get("lift")
            if not isinstance(date_str, str):
                date_str = str(date_str)
            if date_str == "":
                continue
            timestamp = self.get_timestamp(date_str)
            lift = 1 if lift_str == "TRUE" else 0
            if timestamp is not None and timestamp < datetime.now() and lift == 1:
                lift = LiftData(timestamp=timestamp, source="google_sheet", score=lift)
                lift_data.append(lift)
        return lift_data
    
    
    
        
        
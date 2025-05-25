from datetime import datetime
import logging
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import json

from backend.models import GSheetData
from backend.files import get_secrets
from backend.connectors.base import Connector

logger = logging.getLogger(__name__)

class GSheetConnector(Connector[GSheetData]):
    """Connector for Google Sheets data tracking lifts and bodyweight"""
    def __init__(self):
        """Initialize the GSheetConnector with credentials."""
        secrets = get_secrets(".secrets.json")
        self.service_account_info = secrets["GOOGLE_SERVICE_ACCOUNT"]
        self.sheet_name = secrets["GSHEET_SHEET_NAME"]
        self.worksheet_name = secrets["GSHEET_WORKSHEET_NAME"]
        self.client = self.authenticate_google_sheets()

    def authenticate_google_sheets(self):
        """Authenticate with Google Sheets API using service account credentials from secrets."""
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(self.service_account_info, scope)  # type: ignore
        return gspread.authorize(creds)  # type: ignore

    @property
    def source_name(self) -> str:
        """Return the name of the data source."""
        return "gsheet"

    def get_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> list[GSheetData]:
        """Fetch lift and bodyweight data from Google Sheets for the given date range."""
        try:
            sheet = self.client.open(self.sheet_name).worksheet(self.worksheet_name)
            records = sheet.get_all_records()

            gsheet_data_list = []
            for record in records:
                try:
                    date_str = record.get("date")
                    weight_str = record.get("bodyweight")
                    lift_str = record.get("lift")

                    if not date_str:
                        continue

                    # Convert date string to datetime
                    if not isinstance(date_str, str):
                        date_str = str(date_str)
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # Skip if outside date range
                    if not (start_date <= date <= end_date):
                        continue

                    # Parse bodyweight
                    bodyweight = None
                    if weight_str:
                        if not isinstance(weight_str, str):
                            weight_str = str(weight_str)
                        bodyweight = float(weight_str.removesuffix("kg"))

                    # Parse lift boolean
                    lift = None
                    if lift_str is not None:
                        lift = lift_str == "TRUE"

                    gsheet_data = GSheetData(
                        source=self.source_name,
                        date=date,
                        bodyweight_kg=bodyweight,
                        lift=lift
                    )
                    gsheet_data_list.append(gsheet_data)

                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing record {record}: {e}")
                    continue

            return gsheet_data_list

        except Exception as e:
            logger.error(f"Error fetching data from Google Sheets: {e}")
            return [] 
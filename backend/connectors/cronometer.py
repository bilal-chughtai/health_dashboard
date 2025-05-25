import csv
from datetime import datetime
from io import StringIO
import requests
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
import time

from backend.models import CronometerData
from backend.files import get_secrets
from backend.connectors.base import Connector

class CronometerConnector(Connector[CronometerData]):
    """Connector for Cronometer data"""
    def __init__(self):
        """Initialize the CronometerConnector with credentials."""
        self.base_url = "https://cronometer.com/cronometer/app"
        self.secrets = get_secrets(".secrets.json")
        self.sesnonce = None
        self.fetchnonce = None

    @property
    def source_name(self) -> str:
        """Return the name of the data source."""
        return "cronometer"

    def _session_authenticate(self):
        """Authenticate the session using Selenium and obtain the sesnonce cookie."""
        url = "https://cronometer.com/login/"
        options = FirefoxOptions()
        options.add_argument("--headless")

        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)

        try:
            driver.get(url)
            time.sleep(2)

            username_field = driver.find_element(By.ID, "username")
            username_field.send_keys(self.secrets["CRONOMETER_USERNAME"])

            password_field = driver.find_element(By.ID, "password")
            password_field.send_keys(self.secrets["CRONOMETER_PASSWORD"])

            driver.find_element(By.ID, "login-button").click()
            time.sleep(2)

            cookie = driver.get_cookie("sesnonce")
            if not cookie or not isinstance(cookie["value"], str):
                raise ValueError("Failed to get valid sesnonce cookie")
            self.sesnonce = cookie["value"]

        finally:
            driver.quit()

    def _authenticate(self):
        """Authenticate with the Cronometer API to obtain a nonce token."""
        if not self.sesnonce:
            raise ValueError("No sesnonce available. Call _session_authenticate first.")

        payload = f"7|0|8|https://cronometer.com/cronometer/|4BF489C39F5BC40ED3964A8458F88DB5|com.cronometer.shared.rpc.CronometerService|generateAuthorizationToken|java.lang.String/2004016611|I|com.cronometer.shared.user.AuthScope/2065601159|{self.sesnonce}|1|2|3|4|4|5|6|6|7|8|2942452|3600|7|2|"
        headers = {
            "Accept": "*/*",
            "Content-Type": "text/x-gwt-rpc; charset=UTF-8",
            "Origin": "https://cronometer.com",
            "Referer": "https://cronometer.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "X-Gwt-Module-Base": "https://cronometer.com/cronometer/",
            "X-Gwt-Permutation": "740E914EA0E4DE17AA7B9F35DE500171",
        }
        response = requests.post(self.base_url, data=payload, headers=headers)
        self.fetchnonce = response.text.split('"')[1]

    def get_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> list[CronometerData]:
        """Fetch Cronometer data for the given date range."""
        # Authenticate if needed
        if not self.sesnonce or not self.fetchnonce:
            self._session_authenticate()
            self._authenticate()

        # Convert datetime to YYYY-MM-DD strings for the API
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # Fetch nutrition data
        url = f"https://cronometer.com/export?nonce={self.fetchnonce}&generate=dailySummary&start={start_str}&end={end_str}"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Warning: Failed to fetch data from Cronometer API. Status code: {response.status_code}")
            return [] 

        # Parse CSV response
        csv_file = StringIO(response.text)
        csv_reader = csv.DictReader(csv_file)
        nutrition_entries = list(csv_reader)

        # Transform into CronometerData objects
        nutrition_data_list = []
        for entry in nutrition_entries:
            date = datetime.strptime(entry["Date"], "%Y-%m-%d")
            nutrition_data = CronometerData(
                source=self.source_name,
                date=date,
                calories=float(entry["Energy (kcal)"]),
                protein=float(entry["Protein (g)"]),
                carbs=float(entry["Carbs (g)"]),
                fat=float(entry["Fat (g)"])
            )
            nutrition_data_list.append(nutrition_data)

        return nutrition_data_list 
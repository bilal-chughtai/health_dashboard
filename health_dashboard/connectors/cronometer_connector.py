import csv
from io import StringIO
import json
from typing import Sequence, Type
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from health_dashboard.models.health_data import HealthData
from health_dashboard.models.nutrition_data import NutritionData
from health_dashboard.connectors.api_connector import APIConnector
from health_dashboard.utils import get_secrets


class CronometerConnector(APIConnector):
    def __init__(self):
        """
        Initialize the CronometerConnector with credentials.

        :param username: The username for the Cronometer account.
        :param password: The password for the Cronometer account.
        """
        self.source_name = "cronometer"
        self.base_url = "https://cronometer.com/cronometer/app"
        self.secrets = get_secrets(".secrets.json")

    def _session_authenticate(self, username: str, password: str):
        """
        Authenticate the session using Selenium and obtain the sesnonce cookie.
        """
        # Replace 'path/to/chromedriver' with the actual path to your ChromeDriver
        chrome_driver_path = "/opt/homebrew/Caskroom/chromedriver/126.0.6478.61/chromedriver-mac-arm64/chromedriver"

        # URL to open
        url = "https://cronometer.com/login/"

        # Set up Chrome options to use the existing user profile
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # type: ignore

        # Initialize the WebDriver
        service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            driver.get(url)
            time.sleep(2)

            username_field = driver.find_element(By.ID, "username")
            username_field.send_keys(username)

            password_field = driver.find_element(By.ID, "password")
            password_field.send_keys(password)

            driver.find_element(By.ID, "login-button").click()
            time.sleep(2)

            # Get the cookies
            cookie = driver.get_cookie("sesnonce")  # type: ignore
            if not cookie:
                raise ValueError("sesnonce cookie not found")
            if not isinstance(cookie["value"], str):
                raise ValueError("sesnonce cookie value is not a string")

            self.sesnonce = cookie["value"]

        finally:
            # Close the driver
            pass
            driver.quit()

    def _authenticate(self):
        """
        Authenticate with the Cronometer API to obtain a nonce token.
        """
        payload = f"7|0|8|https://cronometer.com/cronometer/|4BF489C39F5BC40ED3964A8458F88DB5|com.cronometer.shared.rpc.CronometerService|generateAuthorizationToken|java.lang.String/2004016611|I|com.cronometer.shared.user.AuthScope/2065601159|{self.sesnonce}|1|2|3|4|4|5|6|6|7|8|2942452|3600|7|2|"
        headers = {
            "Accept": "*/*",
            "Content-Type": "text/x-gwt-rpc; charset=UTF-8",
            "Origin": "https://cronometer.com",
            "Referer": "https://cronometer.com/",
            "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "X-Gwt-Module-Base": "https://cronometer.com/cronometer/",
            "X-Gwt-Permutation": "740E914EA0E4DE17AA7B9F35DE500171",
            "X-Newrelic-Id": "Ug4CWFJQGwAAVlVaDgk=",
        }
        response = requests.post(self.base_url, data=payload, headers=headers)
        response_text = response.text
        self.fetchnonce = response_text.split('"')[1]

    def get_all_data(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> Sequence[NutritionData]:
        """
        Fetch all data from the Cronometer API and return a list of HealthData objects.

        :param start_date: The start date for fetching data in YYYY-MM-DD format. Defaults to yesterday.
        :param end_date: The end date for fetching data in YYYY-MM-DD format. Defaults to today.
        :return: A list of HealthData objects with the data from the Cronometer API.
        """
        self._session_authenticate(
            self.secrets["CRONOMETER_USERNAME"], self.secrets["CRONOMETER_PASSWORD"]
        )
        self._authenticate()
        nutrition_data = self.get_daily_nutrition(start_date, end_date)
        return nutrition_data

    def get_daily_nutrition(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> Sequence[NutritionData]:
        """
        Fetch daily nutrition data for a specified date range and return a list of NutritionData objects.

        :param start_date: The start date for fetching nutrition data in YYYY-MM-DD format. Defaults to yesterday.
        :param end_date: The end date for fetching nutrition data in YYYY-MM-DD format. Defaults to today.
        :return: A list of NutritionData objects with the nutrition data from the Cronometer API.
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=1)).strftime(
                "%Y-%m-%d"
            )
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        url = f"https://cronometer.com/export?nonce={self.fetchnonce}&generate=dailySummary&start={start_date}&end={end_date}"
        response = requests.get(url)
        code = response.status_code
        if code == 200:
            response_csv = response.text
        else:
            print(
                f"{datetime.now()}: Warning: Failed to fetch data from Cronometer API. Status code: {code}"
            )
            return []

        csv_file = StringIO(response_csv)
        csv_reader = csv.DictReader(csv_file)
        response_json = [row for row in csv_reader]

        # Transform the API response into NutritionData objects
        nutrition_data_objects = []
        for nutrition_entry in response_json:
            timestamp = datetime.strptime(nutrition_entry["Date"], "%Y-%m-%d")
            calories = float(nutrition_entry["Energy (kcal)"])
            protein = float(nutrition_entry["Protein (g)"])
            carbs = float(nutrition_entry["Carbs (g)"])
            fat = float(nutrition_entry["Fat (g)"])
            nutrition_data = NutritionData(
                timestamp=timestamp,
                source=self.source_name,
                calories=calories,
                protein=protein,
                carbs=carbs,
                fat=fat,
            )
            nutrition_data_objects.append(nutrition_data)

        return nutrition_data_objects

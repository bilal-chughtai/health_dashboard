# %%
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from pprint import pprint

# Replace 'path/to/chromedriver' with the actual path to your ChromeDriver
chrome_driver_path = "/opt/homebrew/Caskroom/chromedriver/126.0.6478.61/chromedriver-mac-arm64/chromedriver"

# Path to your Chrome user data directory
# chrome_user_data_path = "/Users/bilal/Library/Application Support/Google/Chrome"  # Update with your actual path

# URL to open
url = "https://cronometer.com/login/"  # Replace with the actual URL

# Set up Chrome options to use the existing user profile
chrome_options = Options()
# chrome_options.add_argument(f"user-data-dir=selenium")  # Path to your Chrome profile
chrome_options.add_argument("--headless")  # Run in headless mode, i.e., without a GUI

# Initialize the WebDriver
service = Service(chrome_driver_path)
print(f"service: {service}")
driver = webdriver.Chrome(service=service, options=chrome_options)
print(f"driver: {driver}")


try:
    driver.get(url)
    time.sleep(2)

    username = driver.find_element(By.ID, 'username')
    username.send_keys("brchughtaii@gmail.com")

    password = driver.find_element(By.ID, "password")
    password.send_keys("j6r8xpmUr2u8D#F")
    
    driver.find_element(By.ID, "login-button").click()

    time.sleep(2)
    
    # Get the cookies
    cookies = driver.get_cookies()
    pprint(f"cookies: {cookies}")
    sesnonce_cookie = None
    for cookie in cookies:
        if cookie["name"] == "sesnonce":
            sesnonce = cookie["value"]
            break

    if not sesnonce:
        raise ValueError("sesnonce cookie not found")
    else:
        print(f"sesnonce: {sesnonce}")
        
finally:
    # Close the driver
    driver.quit()

# %%


import requests

url = "https://cronometer.com/cronometer/app"
payload = f"7|0|8|https://cronometer.com/cronometer/|4BF489C39F5BC40ED3964A8458F88DB5|com.cronometer.shared.rpc.CronometerService|generateAuthorizationToken|java.lang.String/2004016611|I|com.cronometer.shared.user.AuthScope/2065601159|{sesnonce}|1|2|3|4|4|5|6|6|7|8|2942452|3600|7|2|"

headers = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
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

response = requests.post(url, data=payload, headers=headers)

response = response.text
print(f"Response: {response}")
nonce = response.split('"')[1]
print(f"Nonce: {nonce}")
url = f"https://cronometer.com/export?nonce={nonce}&generate=dailySummary&start=2024-06-07&end=2024-06-13"
response = requests.get(url)
print(f"Response: {response.text}")

# %%

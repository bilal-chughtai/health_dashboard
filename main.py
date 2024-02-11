# %%
import os
from dotenv import load_dotenv
from oura_ring import OuraClient
import pandas as pd
from dataclasses import dataclass
load_dotenv()
oura_access_token = os.getenv('OURA_ACCESS_TOKEN')

# %%

@dataclass
class OuraRecord:
    """
    A class to represent one day of data from the Oura ring.
    """
    day: str # in the format "YYYY-MM-DD"
    sleep_score: int
    activity_score: int
    readiness_score: int
    


oura_client = OuraClient(oura_access_token)
# %%
sleep = oura_client.get_daily_sleep("2024-02-01")
df = pd.json_normalize(sleep)

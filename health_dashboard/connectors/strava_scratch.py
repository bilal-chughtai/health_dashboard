# %%
from datetime import datetime
from pprint import pprint
from stravalib.client import Client, BatchedResultsIterator, model
import requests

client = Client()
client.access_token = "bbb61395f56eafa859c11f368ee7ddda54514d58"
# %%
activities = client.get_activities(after="2024-07-01")

# %%
print(activities)
# %%
for activity in activities:
    my_dict = activity.to_dict()
    pprint(my_dict)

# %%
if time.time() > access_token["expires_at"]:
    print("Token has expired, will refresh")
    refresh_response = client.refresh_access_token(
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=access_token["refresh_token"],
    )
    access_token = refresh_response
    with open("../access_token.pickle", "wb") as f:
        pickle.dump(refresh_response, f)
    print("Refreshed token saved to file")
    client.access_token = refresh_response["access_token"]
    client.refresh_token = refresh_response["refresh_token"]
    client.token_expires_at = refresh_response["expires_at"]

else:
    print(
        "Token still valid, expires at {}".format(
            time.strftime(
                "%a, %d %b %Y %H:%M:%S %Z", time.localtime(access_token["expires_at"])
            )
        )
    )
    client.access_token = access_token["access_token"]
    client.refresh_token = access_token["refresh_token"]
    client.token_expires_at = access_token["expires_at"]

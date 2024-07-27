import json


def get_secrets(path: str = ".secrets.json"):
    with open(path) as f:
        secrets = json.load(f)
    return secrets

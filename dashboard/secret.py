from pathlib import Path
from typing import Optional
import json
from pydantic import BaseModel, Field, SecretStr, validator
from pydantic_settings import BaseSettings
import streamlit as st


class GoogleServiceAccount(BaseModel):
    type: str
    project_id: str
    private_key_id: str
    private_key: SecretStr
    client_email: str
    client_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_x509_cert_url: str
    universe_domain: str


class SharedSecrets(BaseSettings):
    """Secrets that are shared with the frontend (Streamlit)."""
    # AWS credentials
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: SecretStr
    AWS_S3_BUCKET_NAME: str
    AWS_CSV_FILENAME: str  # Filename of the encrypted CSV in S3
    ENCRYPTION_KEY: SecretStr

    @classmethod
    def from_json_file(cls, filepath: str | Path) -> "SharedSecrets":
        """Load secrets from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls(**data)


class AllSecrets(SharedSecrets):
    """All secrets including backend-only ones."""
    # Cronometer credentials
    CRONOMETER_USERNAME: str
    CRONOMETER_PASSWORD: SecretStr
    
    # Strava credentials
    STRAVA_CLIENT_SECRET: SecretStr
    STRAVA_CLIENT_ID: str
    
    # Oura credentials
    OURA_ACCESS_TOKEN: SecretStr
    
    # Garmin credentials
    GARMIN_EMAIL: str
    GARMIN_PASSWORD: SecretStr
    
    # Google Sheets configuration
    GSHEET_SHEET_NAME: str
    GSHEET_WORKSHEET_NAME: str
    GOOGLE_SERVICE_ACCOUNT: GoogleServiceAccount

    @classmethod
    def from_json_file(cls, filepath: str | Path) -> "AllSecrets":
        """Load secrets from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls(**data)

    def model_dump_json(self, **kwargs) -> str:
        """Override to handle SecretStr serialization."""
        data = self.model_dump(mode="json")
        # Convert SecretStr to plain strings for JSON serialization
        for key, value in data.items():
            if isinstance(value, SecretStr):
                data[key] = value.get_secret_value()
            elif isinstance(value, dict) and isinstance(value.get("private_key"), SecretStr):
                data[key]["private_key"] = value["private_key"].get_secret_value()
        return json.dumps(data, **kwargs)


# Global secrets instances
_shared_secrets: Optional[SharedSecrets] = None
_all_secrets: Optional[AllSecrets] = None


def _convert_streamlit_secrets_to_shared() -> Optional[SharedSecrets]:
    """Convert Streamlit secrets to our SharedSecrets model if available."""
    try:
        # Check if we're running in Streamlit and secrets are available
        if not st.secrets:
            return None
            
        # Convert Streamlit secrets to our model format
        secrets_dict = {
            "AWS_ACCESS_KEY_ID": st.secrets["aws_access_key_id"],
            "AWS_SECRET_ACCESS_KEY": SecretStr(st.secrets["aws_secret_access_key"]),
            "AWS_S3_BUCKET_NAME": st.secrets["aws_s3_bucket_name"],
            "AWS_CSV_FILENAME": st.secrets["aws_csv_filename"],
            "ENCRYPTION_KEY": SecretStr(st.secrets["encryption_key"]),
        }
        
        return SharedSecrets(**secrets_dict)
    except Exception as e:
        print(f"Warning: Failed to load Streamlit secrets: {str(e)}")
        return None


def get_shared_secrets() -> SharedSecrets:
    """Get the global shared secrets instance, initializing it if necessary."""
    global _shared_secrets
    if _shared_secrets is None:
        # First try to load from Streamlit secrets
        streamlit_secrets = _convert_streamlit_secrets_to_shared()
        if streamlit_secrets is not None:
            _shared_secrets = streamlit_secrets
            return _shared_secrets
            
        # Fall back to JSON file if Streamlit secrets aren't available
        secrets_path = Path(__file__).parent.parent / ".secrets.json"
        if not secrets_path.exists():
            raise FileNotFoundError(f"Secrets file not found at {secrets_path}")
        try:
            _shared_secrets = SharedSecrets.from_json_file(secrets_path)
        except Exception as e:
            raise ValueError(f"Failed to load shared secrets from {secrets_path}: {str(e)}")
    return _shared_secrets


def get_all_secrets() -> AllSecrets:
    """Get the global all secrets instance, initializing it if necessary."""
    global _all_secrets
    if _all_secrets is None:
        secrets_path = Path(__file__).parent.parent / ".secrets.json"
        if not secrets_path.exists():
            raise FileNotFoundError(f"Secrets file not found at {secrets_path}")
        _all_secrets = AllSecrets.from_json_file(secrets_path)
    return _all_secrets


def set_shared_secrets(secrets: SharedSecrets) -> None:
    """Set the global shared secrets instance manually."""
    global _shared_secrets
    _shared_secrets = secrets


def set_all_secrets(secrets: AllSecrets) -> None:
    """Set the global all secrets instance manually."""
    global _all_secrets
    _all_secrets = secrets

import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, SecretStr
from pydantic_settings import BaseSettings
import streamlit as st

logger = logging.getLogger(__name__)


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

    model_config = ConfigDict(extra="ignore")  # e.g. LIFT_DATES_SHEET_CSV_URL lives only in .secrets.json

    # AWS credentials
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: SecretStr
    AWS_S3_BUCKET_NAME: str
    AWS_JSON_FILENAME: str  # Filename of the encrypted JSON in S3
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
            elif isinstance(value, dict) and isinstance(
                value.get("private_key"), SecretStr
            ):
                data[key]["private_key"] = value["private_key"].get_secret_value()
        return json.dumps(data, **kwargs)


# Global secrets instances
_shared_secrets: Optional[SharedSecrets] = None
_all_secrets: Optional[AllSecrets] = None


def _convert_streamlit_secrets_to_shared() -> Optional[SharedSecrets]:
    """Convert Streamlit secrets to our SharedSecrets model if available."""
    try:
        if not st.secrets:
            logger.info("Secrets: st.secrets is empty or not set")
            return None

        secrets_dict = {
            "AWS_ACCESS_KEY_ID": st.secrets["aws_access_key_id"],
            "AWS_SECRET_ACCESS_KEY": SecretStr(st.secrets["aws_secret_access_key"]),
            "AWS_S3_BUCKET_NAME": st.secrets["aws_s3_bucket_name"],
            "AWS_JSON_FILENAME": st.secrets["aws_json_filename"],
            "ENCRYPTION_KEY": SecretStr(st.secrets["encryption_key"]),
        }
        logger.info("Secrets: loaded from Streamlit (st.secrets)")
        return SharedSecrets(**secrets_dict)
    except Exception as e:
        logger.warning("Secrets: Streamlit conversion failed: %s", e, exc_info=True)
        return None


def _streamlit_secrets_failure_reason() -> str:
    """Run conversion and return the exception message if it fails (for error reporting)."""
    try:
        if not st.secrets:
            return "st.secrets is empty or not set"
        st.secrets["aws_access_key_id"]
        st.secrets["aws_secret_access_key"]
        st.secrets["aws_s3_bucket_name"]
        st.secrets["aws_json_filename"]
        st.secrets["encryption_key"]
        return "unknown (conversion failed)"
    except Exception as e:
        return str(e)


def get_shared_secrets() -> SharedSecrets:
    """Get the global shared secrets instance, initializing it if necessary."""
    global _shared_secrets
    if _shared_secrets is None:
        logger.info("Secrets: loading shared secrets (Streamlit first, then .secrets.json)")
        streamlit_secrets = _convert_streamlit_secrets_to_shared()
        if streamlit_secrets is not None:
            _shared_secrets = streamlit_secrets
            return _shared_secrets

        secrets_path = Path(__file__).parent.parent / ".secrets.json"
        if not secrets_path.exists():
            reason = _streamlit_secrets_failure_reason()
            logger.error(
                "Secrets: .secrets.json not found and Streamlit secrets unavailable: %s",
                reason,
            )
            raise FileNotFoundError(
                "Secrets not available. "
                "On Streamlit Cloud: set secrets in App → Settings → Secrets "
                "(aws_access_key_id, aws_secret_access_key, aws_s3_bucket_name, aws_json_filename, encryption_key). "
                f"Streamlit secrets reason: {reason}. "
                "Locally: add .secrets.json in the project root."
            )
        logger.info("Secrets: loading from .secrets.json at %s", secrets_path)
        try:
            _shared_secrets = SharedSecrets.from_json_file(secrets_path)
        except Exception as e:
            logger.exception("Secrets: failed to load from .secrets.json: %s", e)
            raise ValueError(
                f"Failed to load shared secrets from {secrets_path}: {str(e)}"
            )
    return _shared_secrets


def get_lift_dates_csv_url() -> Optional[str]:
    """Backend-only: read lift-dates CSV URL from .secrets.json (not exposed to Streamlit)."""
    try:
        path = Path(__file__).parent.parent / ".secrets.json"
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            url = data.get("LIFT_DATES_SHEET_CSV_URL")
            if url:
                logger.debug("Secrets: LIFT_DATES_SHEET_CSV_URL found in .secrets.json")
            return url
        logger.debug("Secrets: .secrets.json not found, no lift-dates URL")
    except Exception as e:
        logger.debug("Secrets: could not read lift-dates URL: %s", e)
    return None


def get_all_secrets() -> AllSecrets:
    """Get the global all secrets instance, initializing it if necessary."""
    global _all_secrets
    if _all_secrets is None:
        secrets_path = Path(__file__).parent.parent / ".secrets.json"
        logger.info("Secrets: loading all secrets from %s", secrets_path)
        if not secrets_path.exists():
            logger.error("Secrets: file not found at %s", secrets_path)
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

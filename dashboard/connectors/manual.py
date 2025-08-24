from datetime import datetime
import logging
import json
from typing import List, Dict, Tuple, Any

from dashboard.models import ManualData
from dashboard.secret import get_shared_secrets
from dashboard.connectors.base import Connector
from dashboard.files import get_s3_client, decrypt_data

logger = logging.getLogger(__name__)


class ManualConnector(Connector[ManualData]):
    """Connector for manually entered data from temp JSON files"""

    def __init__(self):
        """Initialize the ManualConnector with AWS credentials."""
        secrets = get_shared_secrets()
        self.bucket_name = secrets.AWS_S3_BUCKET_NAME
        self.s3_client = get_s3_client()

    @property
    def source_name(self) -> str:
        """Return the name of the data source."""
        return "manual"

    def get_data(self, start_date: datetime, end_date: datetime) -> List[ManualData]:
        """No op, as dashboard deals with manual data now directly."""
        return []

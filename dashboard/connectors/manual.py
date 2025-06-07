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

    def list_temp_files(self) -> List[Dict[str, Any]]:
        """List all temp JSON files from S3 and their contents."""
        try:
            # List all objects in the bucket with temp_ prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='temp_'
            )
            
            if 'Contents' not in response:
                logger.info("No temp files found in S3")
                return []
            
            temp_files = []
            for obj in response['Contents']:
                try:
                    key = obj['Key']
                    # Get and decrypt the file
                    response = self.s3_client.get_object(
                        Bucket=self.bucket_name,
                        Key=key
                    )
                    encrypted_data = response['Body'].read()
                    decrypted_data = decrypt_data(encrypted_data)
                    
                    # Parse JSON
                    temp_data = json.loads(decrypted_data.decode('utf-8'))
                    temp_data['key'] = key  # Add the S3 key for later deletion
                    temp_files.append(temp_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing temp file {obj['Key']}: {e}")
                    continue
            
            # Sort by timestamp
            temp_files.sort(key=lambda x: x['timestamp'])
            return temp_files
            
        except Exception as e:
            logger.error(f"Error listing temp files from S3: {e}")
            return []

    def delete_temp_files(self, keys: List[str]) -> None:
        """Delete temp files from S3 in batches."""
        if not keys:
            return
            
        try:
            # Delete objects in batches of 1000 (S3 limit)
            for i in range(0, len(keys), 1000):
                batch = keys[i:i + 1000]
                delete_response = self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': [{'Key': key} for key in batch]}
                )
                if 'Errors' in delete_response:
                    for error in delete_response['Errors']:
                        logger.error(f"Error deleting {error['Key']}: {error['Message']}")
                else:
                    logger.info(f"Successfully deleted {len(batch)} temp files")
        except Exception as e:
            logger.error(f"Error deleting temp files: {e}")

    def process_temp_files(self, temp_files: List[Dict[str, Any]], start_date: datetime, end_date: datetime) -> Tuple[List[ManualData], List[str]]:
        """Process temp files into ManualData objects and collect keys for deletion."""
        manual_data_list = []
        keys_to_delete = []
        
        for temp_file in temp_files:
            try:
                data = temp_file['data']
                key = temp_file['key']
                
                # Convert date string to datetime
                data_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
                
                # Only process files within date range
                if start_date <= data_date <= end_date:
                    # Create ManualData object
                    manual_data = ManualData(
                        source=self.source_name,
                        date=data_date,
                        bodyweight_kg=data.get('manual__bodyweight_kg'),
                        lift=data.get('manual__lift')
                    )
                    manual_data_list.append(manual_data)
                    keys_to_delete.append(key)
                    
            except Exception as e:
                logger.warning(f"Error processing temp file data: {e}")
                continue
        
        return manual_data_list, keys_to_delete

    def get_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[ManualData]:
        """Fetch manual data from temp JSON files for the given date range."""
        try:
            # List all temp files
            temp_files = self.list_temp_files()
            
            # Process files and get data and keys to delete
            manual_data_list, keys_to_delete = self.process_temp_files(temp_files, start_date, end_date)
            
            # Delete processed files
            self.delete_temp_files(keys_to_delete)
            
            return manual_data_list

        except Exception as e:
            logger.error(f"Error fetching data from temp files: {e}")
            return [] 
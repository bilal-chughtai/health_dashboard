import json
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from typing import Optional, Literal
from datetime import datetime
from cryptography.fernet import Fernet
import base64

"""Utility functions and constants for the health dashboard."""

# Default file paths
DEFAULT_JSON_PATH = "data/health_data.json"
DEFAULT_CSV_PATH = "data/health_data.csv"

def get_secrets(path: str = ".secrets.json"):
    """Get secrets from the specified JSON file."""
    with open(path) as f:
        secrets = json.load(f)
    return secrets

def get_encryption_key() -> bytes:
    """Get the encryption key from secrets and convert it to a Fernet key."""
    secrets = get_secrets()
    # Pad or truncate the key to 32 bytes and encode as base64
    key = secrets['ENCRYPTION_KEY'].encode()
    key = key.ljust(32, b'=')[:32]  # Pad with = or truncate to 32 bytes
    return base64.urlsafe_b64encode(key)

def encrypt_data(data: bytes) -> bytes:
    """Encrypt the given data using Fernet symmetric encryption."""
    f = Fernet(get_encryption_key())
    return f.encrypt(data)

def decrypt_data(encrypted_data: bytes) -> bytes:
    """Decrypt the given data using Fernet symmetric encryption."""
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_data)

# AWS S3 Operations
def get_s3_client():
    """Get an S3 client using credentials from secrets."""
    secrets = get_secrets()
    return boto3.client(
        's3',
        aws_access_key_id=secrets['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=secrets['AWS_SECRET_ACCESS_KEY']
    )

def handle_file_aws(
    operation: Literal["upload", "download"],
    file_type: Literal["json", "csv"],
    local_path: Optional[str] = None
) -> bool:
    """
    Unified function to handle file operations with AWS S3.
    
    Args:
        operation: Either "upload" or "download"
        file_type: Either "json" or "csv"
        local_path: Optional local path to use instead of default paths
        
    Returns:
        bool: True if successful, False if file doesn't exist in S3 (download only)
    """
    # Set up paths and keys
    if file_type == "json":
        default_path = DEFAULT_JSON_PATH
        s3_key = 'health_data.json'
    else:  # csv
        default_path = DEFAULT_CSV_PATH
        s3_key = 'health_data.csv'
    
    local_path = local_path or default_path
    
    try:
        s3_client = get_s3_client()
        secrets = get_secrets()
        bucket = secrets['AWS_S3_BUCKET_NAME']
        
        if operation == "upload":
            # Check if local file exists
            if not Path(local_path).exists():
                raise FileNotFoundError(f"Local {file_type} file not found: {local_path}")
            
            # Read and encrypt the file
            with open(local_path, 'rb') as f:
                data = f.read()
            encrypted_data = encrypt_data(data)
            
            # Upload encrypted data
            s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=encrypted_data
            )
            return True
            
        else:  # download
            try:
                # Get encrypted data from S3
                response = s3_client.get_object(
                    Bucket=bucket,
                    Key=s3_key
                )
                encrypted_data = response['Body'].read()
                
                # Decrypt and write the file
                decrypted_data = decrypt_data(encrypted_data)
                with open(local_path, 'wb') as f:
                    f.write(decrypted_data)
                
                return True
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    # File doesn't exist in S3
                    return False
                # Re-raise other AWS errors
                raise
                
    except Exception as e:
        # Re-raise any errors
        raise

# Convenience functions that use the unified handler
def encrypt_and_upload_json(local_path: Optional[str] = None) -> None:
    """Upload the local JSON file to AWS S3 with encryption."""
    handle_file_aws("upload", "json", local_path)

def encrypt_and_upload_csv(local_path: Optional[str] = None) -> None:
    """Upload the local CSV file to AWS S3 with encryption."""
    handle_file_aws("upload", "csv", local_path)

def download_and_decrypt_json(local_path: Optional[str] = None) -> bool:
    """Download and decrypt the JSON file from AWS S3."""
    return handle_file_aws("download", "json", local_path)

def download_and_decrypt_csv(local_path: Optional[str] = None) -> bool:
    """Download and decrypt the CSV file from AWS S3."""
    return handle_file_aws("download", "csv", local_path)

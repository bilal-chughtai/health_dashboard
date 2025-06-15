import json
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from typing import Union
from datetime import datetime
from cryptography.fernet import Fernet
import base64

from dashboard.secret import get_shared_secrets

"""Utility functions for file encryption and AWS S3 operations."""

def get_encryption_key() -> bytes:
    """Get the encryption key from secrets and convert it to a Fernet key."""
    secrets = get_shared_secrets()
    # Pad or truncate the key to 32 bytes and encode as base64
    key = secrets.ENCRYPTION_KEY.get_secret_value().encode()
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

def get_s3_client():
    """Get an S3 client using credentials from secrets."""
    secrets = get_shared_secrets()
    return boto3.client(
        's3',
        aws_access_key_id=secrets.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=secrets.AWS_SECRET_ACCESS_KEY.get_secret_value()
    )

def encrypt_and_upload_file(local_path: Union[str, Path]) -> None:
    """
    Upload a local file to AWS S3 with encryption.
    The AWS key will be the same as the local filename.
    
    Args:
        local_path: Path to the local file to upload (string or Path object)
    """
    local_path = Path(local_path)
    if not local_path.exists():
        raise FileNotFoundError(f"Local file not found: {local_path}")
    
    # Ensure parent directory exists
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        s3_client = get_s3_client()
        secrets = get_shared_secrets()
        bucket = secrets.AWS_S3_BUCKET_NAME
        
        # Read and encrypt the file
        with open(local_path, 'rb') as f:
            data = f.read()
        encrypted_data = encrypt_data(data)
        
        # Upload encrypted data using filename as key
        s3_client.put_object(
            Bucket=bucket,
            Key=local_path.name,
            Body=encrypted_data
        )
    except Exception as e:
        raise Exception(f"Failed to upload {local_path}: {str(e)}")

def download_and_decrypt_file(local_path: Union[str, Path]) -> bool:
    """
    Download and decrypt a file from AWS S3.
    The AWS key is assumed to be the same as the local filename.
    
    Args:
        local_path: Path where the decrypted file should be saved (string or Path object)
        
    Returns:
        bool: True if successful, False if file doesn't exist in S3
    """
    local_path = Path(local_path)
    
    # Ensure parent directory exists
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        s3_client = get_s3_client()
        secrets = get_shared_secrets()
        bucket = secrets.AWS_S3_BUCKET_NAME
        
        try:
            # Get encrypted data from S3 using filename as key
            response = s3_client.get_object(
                Bucket=bucket,
                Key=local_path.name
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
        raise Exception(f"Failed to download {local_path}: {str(e)}")

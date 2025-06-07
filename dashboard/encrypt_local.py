#!/usr/bin/env python3
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from dashboard.files import encrypt_data, decrypt_data
from dashboard.secret import get_shared_secrets

def encrypt_and_save(data: Dict[str, Any], output_dir: str | Path, filename: str | None = None) -> str:
    """
    Encrypt data and save it to a local file.
    
    Args:
        data: Dictionary containing the data to encrypt
        output_dir: Directory to save the encrypted file
        filename: Optional filename (defaults to timestamp-based name)
    
    Returns:
        Path to the saved file
    """
    # Create output directory if it doesn't exist
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"temp_{timestamp}.json"
    
    # Ensure filename has .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Convert data to JSON string
    json_data = json.dumps(data, default=str)
    
    # Encrypt the data
    encrypted_data = encrypt_data(json_data.encode('utf-8'))
    
    # Save to file
    output_path = output_dir / filename
    with open(output_path, 'wb') as f:
        f.write(encrypted_data)
    
    return str(output_path)

def encrypt_health_data(input_file: str | Path, output_dir: str | Path = "data") -> str:
    """
    Encrypt the health data file and save it with _encrypted suffix.
    
    Args:
        input_file: Path to the health data file (CSV or JSON)
        output_dir: Directory to save the encrypted file
    
    Returns:
        Path to the saved encrypted file
    """
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename
    output_filename = f"{input_path.stem}_encrypted{input_path.suffix}"
    output_path = output_dir / output_filename
    
    # Read and encrypt the file
    with open(input_path, 'rb') as f:
        data = f.read()
    
    # If the file is already encrypted, decrypt it first
    try:
        data = decrypt_data(data)
    except Exception:
        # If decryption fails, assume it's not encrypted
        pass
    
    # Encrypt the data
    encrypted_data = encrypt_data(data)
    
    # Save to file
    with open(output_path, 'wb') as f:
        f.write(encrypted_data)
    
    return str(output_path)

def main():
    """Main function to handle command line arguments and save data."""
    parser = argparse.ArgumentParser(description='Encrypt and save data locally')
    parser.add_argument('--data', type=str, help='JSON string containing the data to encrypt')
    parser.add_argument('--file', type=str, help='Path to JSON file containing the data to encrypt')
    parser.add_argument('--output-dir', type=str, default='data', help='Directory to save encrypted files')
    parser.add_argument('--filename', type=str, help='Optional filename for the encrypted file')
    parser.add_argument('--health-data', action='store_true', help='Encrypt health data files in the data directory')
    
    args = parser.parse_args()
    
    try:
        if args.health_data:
            # Encrypt all health data files in the data directory
            data_dir = Path("data")
            if not data_dir.exists():
                print("No data directory found")
                exit(1)
            
            for file in data_dir.glob("health_data*"):
                if not file.name.endswith('_encrypted'):
                    try:
                        output_path = encrypt_health_data(file, args.output_dir)
                        print(f"Encrypted {file.name} to {output_path}")
                    except Exception as e:
                        print(f"Error encrypting {file.name}: {e}")
            
        elif args.data and args.file:
            parser.error("Cannot specify both --data and --file")
        elif args.data:
            data = json.loads(args.data)
            output_path = encrypt_and_save(data, args.output_dir, args.filename)
            print(f"Data encrypted and saved to: {output_path}")
        elif args.file:
            with open(args.file, 'r') as f:
                data = json.load(f)
            output_path = encrypt_and_save(data, args.output_dir, args.filename)
            print(f"Data encrypted and saved to: {output_path}")
        else:
            # Default behavior: encrypt health data files
            data_dir = Path("data")
            if not data_dir.exists():
                parser.error("No data directory found and no input specified")
            
            for file in data_dir.glob("health_data*"):
                if not file.name.endswith('_encrypted'):
                    try:
                        output_path = encrypt_health_data(file, args.output_dir)
                        print(f"Encrypted {file.name} to {output_path}")
                    except Exception as e:
                        print(f"Error encrypting {file.name}: {e}")
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        exit(1)
    except Exception as e:
        print(f"Error saving data: {e}")
        exit(1)

if __name__ == "__main__":
    main() 
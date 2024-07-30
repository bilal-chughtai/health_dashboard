#!/bin/bash

# Get the directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to that directory
cd "$SCRIPT_DIR"

# Activate the virtual environment
source .venv/bin/activate

# Run the script
python health_dashboard/main.py >> log.txt 2>&1
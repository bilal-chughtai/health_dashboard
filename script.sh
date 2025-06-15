#!/bin/bash

# Get the directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to that directory
cd "$SCRIPT_DIR"

# Activate the virtual environment
source .venv/bin/activate

# Print current date and time
echo "Current datetime: $(date)" >> log.txt

# Run the script
python -m dashboard.main --online >> log.txt 2>&1
echo "" >> log.txt

# Run the script in random mode
python -m dashboard.random --online --random >> random_log.txt 2>&1
echo "" >> random_log.txt
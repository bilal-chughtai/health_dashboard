#!/bin/bash

# Get the directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to that directory
cd "$SCRIPT_DIR"

# Run the script
poetry run python health_dashboard/main.py
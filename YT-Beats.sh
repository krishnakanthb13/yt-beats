#!/bin/bash

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python
if ! command_exists python3; then
    echo "Error: Python 3 is not installed."
    echo "Please install python3 (brew install python / sudo apt install python3)"
    exit 1
fi

# Run the app
echo "Starting YT-Beats..."
# Use python3 explicitely
python3 -m src.app

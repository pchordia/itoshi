#!/bin/bash
# Launch script for Anime Video Generator GUI

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project directory
cd "$DIR"

# Run the GUI app
python3 src/gui_app.py



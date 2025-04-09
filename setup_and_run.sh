#!/bin/bash

# Step 1: Create and activate the virtual environment
python3 -m venv venv
source venv/bin/activate

# Step 2: Upgrade pip and install required packages
pip install --upgrade pip
pip install -r requirements.txt

# Step 3: Prompt user for Spotify API credentials
echo "Enter your Spotify Client ID:"
read CLIENT_ID
echo "Enter your Spotify Client Secret:"
read CLIENT_SECRET

# Step 4: Create config.json with the provided credentials
CONFIG_FILE="config.json"
echo "{
  \"client_id\": \"$CLIENT_ID\",
  \"client_secret\": \"$CLIENT_SECRET\"
}" > $CONFIG_FILE

echo "Configuration saved to $CONFIG_FILE."

# Step 5: Run the application
python main.py

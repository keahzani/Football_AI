#!/bin/bash

echo "Setting up Football Predictor..."

# Create necessary directories
mkdir -p data/raw
mkdir -p models/saved
mkdir -p .streamlit

# Initialize database
echo "Initializing database..."
python setup_database.py

# Download historical data
echo "Downloading historical match data..."
python main.py download

# Train models
echo "Training prediction models..."
python main.py train

echo "Setup complete! Starting Streamlit..."

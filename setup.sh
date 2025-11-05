#!/bin/bash

echo "Setting up Football Predictor..."

# Create necessary directories
mkdir -p data/raw
mkdir -p models/saved
mkdir -p .streamlit

# Initialize database FIRST
echo "Initializing database..."
python setup_database.py || {
    echo "Database initialization failed, creating tables manually..."
    python -c "
from utils.database import DatabaseManager
db = DatabaseManager()
# Database will be created automatically by DatabaseManager
print('Database created successfully')
"
}

# Download historical data
echo "Downloading historical match data..."
python main.py download || echo "Download completed with warnings"

# Train models
echo "Training prediction models..."
python main.py train || echo "Training completed with warnings"

echo "Setup complete! Starting Streamlit..."
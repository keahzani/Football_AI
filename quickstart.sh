#!/bin/bash
# Quick Start Script for Football Prediction System

echo "=========================================="
echo "FOOTBALL PREDICTION SYSTEM - QUICK START"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Install dependencies
echo "Step 1: Installing dependencies..."
pip install -r requirements.txt --quiet
if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo ""

# Setup database
echo "Step 2: Initializing database..."
python3 main.py setup
if [ $? -eq 0 ]; then
    echo "✓ Database initialized"
else
    echo "❌ Failed to initialize database"
    exit 1
fi
echo ""

# Download data
echo "Step 3: Downloading historical data (this may take 5-10 minutes)..."
python3 main.py download
if [ $? -eq 0 ]; then
    echo "✓ Historical data downloaded"
else
    echo "❌ Failed to download data"
    exit 1
fi
echo ""

# Train models
echo "Step 4: Training models (this may take 10-15 minutes)..."
python3 main.py train
if [ $? -eq 0 ]; then
    echo "✓ Models trained"
else
    echo "❌ Failed to train models"
    exit 1
fi
echo ""

echo "=========================================="
echo "✓ SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "You can now make predictions:"
echo ""
echo "  python3 main.py predict"
echo "  python3 main.py status"
echo "  python3 main.py teams --league \"Premier League\""
echo ""
echo "See README.md for more commands and usage examples."
echo ""

"""
Configuration file for Football Prediction System
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
DB_PATH = DATA_DIR / "football.db"

# Create directories if they don't exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# League configurations
LEAGUES = {
    'premier_league': {
        'name': 'Premier League',
        'country': 'England',
        'code': 'E0',
        'api_id': 39,
        'avg_goals': 2.8,
        'seasons': ['2021', '2022', '2023', '2024']
    },
    'la_liga': {
        'name': 'La Liga',
        'country': 'Spain',
        'code': 'SP1',
        'api_id': 140,
        'avg_goals': 2.7,
        'seasons': ['2021', '2022', '2023', '2024']
    },
    'bundesliga': {
        'name': 'Bundesliga',
        'country': 'Germany',
        'code': 'D1',
        'api_id': 78,
        'avg_goals': 3.1,
        'seasons': ['2021', '2022', '2023', '2024']
    },
    'serie_a': {
        'name': 'Serie A',
        'country': 'Italy',
        'code': 'I1',
        'api_id': 135,
        'avg_goals': 2.6,
        'seasons': ['2021', '2022', '2023', '2024']
    },
    'ligue_1': {
        'name': 'Ligue 1',
        'country': 'France',
        'code': 'F1',
        'api_id': 61,
        'avg_goals': 2.7,
        'seasons': ['2021', '2022', '2023', '2024']
    }
}

# URLs for data sources
FOOTBALL_DATA_UK_BASE_URL = "https://www.football-data.co.uk"

# API-Football configuration (optional)
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY', '')
API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
API_FOOTBALL_RATE_LIMIT = 100

# Model configuration
MODEL_PARAMS = {
    'xgboost': {
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 200,
        'objective': 'multi:softprob',
        'num_class': 3,
        'random_state': 42
    }
}

# Feature engineering parameters
FORM_MATCHES = 5
H2H_MATCHES = 5
MIN_MATCHES_FOR_PREDICTION = 5

# Prediction thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.65
MEDIUM_CONFIDENCE_THRESHOLD = 0.50

# Betting parameters
BANKROLL = 1000
MAX_BET_PERCENTAGE = 0.05
KELLY_FRACTION = 0.25

# Database schema version
DB_VERSION = "1.0"

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

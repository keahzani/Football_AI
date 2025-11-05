"""
Database setup and utility functions
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
from config.config import DB_PATH

class DatabaseManager:
    """Manages all database operations"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.connection = None
        
    def connect(self):
        """Create database connection"""
        self.connection = sqlite3.connect(self.db_path)
        return self.connection
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def initialize_database(self):
        """Create all necessary tables"""
        with self.connect() as conn:
            cursor = conn.cursor()
            
            # Teams table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_name TEXT NOT NULL,
                    league_id INTEGER NOT NULL,
                    country TEXT,
                    founded INTEGER,
                    UNIQUE(team_name, league_id)
                )
            """)
            
            # Leagues table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leagues (
                    league_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    league_name TEXT NOT NULL UNIQUE,
                    country TEXT NOT NULL,
                    league_code TEXT,
                    api_id INTEGER
                )
            """)
            
            # Matches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    league_id INTEGER NOT NULL,
                    season TEXT NOT NULL,
                    date TEXT NOT NULL,
                    home_team_id INTEGER NOT NULL,
                    away_team_id INTEGER NOT NULL,
                    home_goals INTEGER,
                    away_goals INTEGER,
                    result TEXT CHECK(result IN ('H', 'D', 'A')),
                    home_shots INTEGER,
                    away_shots INTEGER,
                    home_shots_on_target INTEGER,
                    away_shots_on_target INTEGER,
                    home_corners INTEGER,
                    away_corners INTEGER,
                    home_fouls INTEGER,
                    away_fouls INTEGER,
                    home_yellow INTEGER,
                    away_yellow INTEGER,
                    home_red INTEGER,
                    away_red INTEGER,
                    FOREIGN KEY (league_id) REFERENCES leagues (league_id),
                    FOREIGN KEY (home_team_id) REFERENCES teams (team_id),
                    FOREIGN KEY (away_team_id) REFERENCES teams (team_id),
                    UNIQUE(league_id, date, home_team_id, away_team_id)
                )
            """)
            
            # Odds table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS odds (
                    odds_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER NOT NULL,
                    bookmaker TEXT,
                    home_odds REAL,
                    draw_odds REAL,
                    away_odds REAL,
                    odds_type TEXT DEFAULT 'closing',
                    FOREIGN KEY (match_id) REFERENCES matches (match_id)
                )
            """)
            
            # Team statistics table (rolling stats)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS team_stats (
                    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    matches_played INTEGER,
                    wins INTEGER,
                    draws INTEGER,
                    losses INTEGER,
                    goals_scored INTEGER,
                    goals_conceded INTEGER,
                    points INTEGER,
                    league_position INTEGER,
                    form_last_5 REAL,
                    home_form_last_5 REAL,
                    away_form_last_5 REAL,
                    FOREIGN KEY (team_id) REFERENCES teams (team_id),
                    UNIQUE(team_id, date)
                )
            """)
            
            # Fixtures table (upcoming matches)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fixtures (
                    fixture_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    league_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    home_team_id INTEGER NOT NULL,
                    away_team_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'scheduled',
                    venue TEXT,
                    last_updated TEXT,
                    FOREIGN KEY (league_id) REFERENCES leagues (league_id),
                    FOREIGN KEY (home_team_id) REFERENCES teams (team_id),
                    FOREIGN KEY (away_team_id) REFERENCES teams (team_id),
                    UNIQUE(league_id, date, home_team_id, away_team_id)
                )
            """)
            
            # Predictions table (to track accuracy)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER,
                    fixture_id INTEGER,
                    prediction_date TEXT NOT NULL,
                    home_win_prob REAL NOT NULL,
                    draw_prob REAL NOT NULL,
                    away_win_prob REAL NOT NULL,
                    predicted_result TEXT CHECK(predicted_result IN ('H', 'D', 'A')),
                    actual_result TEXT CHECK(actual_result IN ('H', 'D', 'A', NULL)),
                    correct INTEGER,
                    confidence_level TEXT,
                    model_version TEXT,
                    FOREIGN KEY (match_id) REFERENCES matches (match_id),
                    FOREIGN KEY (fixture_id) REFERENCES fixtures (fixture_id)
                )
            """)
            
            # Head to head table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS head_to_head (
                    h2h_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team1_id INTEGER NOT NULL,
                    team2_id INTEGER NOT NULL,
                    last_updated TEXT,
                    matches_played INTEGER,
                    team1_wins INTEGER,
                    draws INTEGER,
                    team2_wins INTEGER,
                    avg_goals REAL,
                    FOREIGN KEY (team1_id) REFERENCES teams (team_id),
                    FOREIGN KEY (team2_id) REFERENCES teams (team_id),
                    UNIQUE(team1_id, team2_id)
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_matches_teams ON matches(home_team_id, away_team_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fixtures_date ON fixtures(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_stats_date ON team_stats(date)")
            
            conn.commit()
            print("Database initialized successfully!")
    
    def insert_league(self, league_name: str, country: str, league_code: str, api_id: int = None) -> int:
        """Insert a league and return its ID"""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO leagues (league_name, country, league_code, api_id)
                VALUES (?, ?, ?, ?)
            """, (league_name, country, league_code, api_id))
            conn.commit()
            
            cursor.execute("SELECT league_id FROM leagues WHERE league_name = ?", (league_name,))
            return cursor.fetchone()[0]
    
    def insert_team(self, team_name: str, league_id: int, country: str = None) -> int:
        """Insert a team and return its ID"""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO teams (team_name, league_id, country)
                VALUES (?, ?, ?)
            """, (team_name, league_id, country))
            conn.commit()
            
            cursor.execute("""
                SELECT team_id FROM teams WHERE team_name = ? AND league_id = ?
            """, (team_name, league_id))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def get_team_id(self, team_name: str, league_id: int) -> Optional[int]:
        """Get team ID by name and league"""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT team_id FROM teams WHERE team_name = ? AND league_id = ?
            """, (team_name, league_id))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Execute a SELECT query and return results"""
        with self.connect() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = None):
        """Execute an INSERT/UPDATE/DELETE query"""
        with self.connect() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
    
    def get_dataframe(self, query: str, params: tuple = None) -> pd.DataFrame:
        """Execute query and return as pandas DataFrame"""
        with self.connect() as conn:
            if params:
                return pd.read_sql_query(query, conn, params=params)
            else:
                return pd.read_sql_query(query, conn)

# Initialize database on import
if __name__ == "__main__":
    db = DatabaseManager()
    db.initialize_database()
    
    # Insert leagues
    from config.config import LEAGUES
    for league_key, league_info in LEAGUES.items():
        league_id = db.insert_league(
            league_info['name'],
            league_info['country'],
            league_info['code'],
            league_info.get('api_id')
        )
        print(f"Inserted/verified {league_info['name']} (ID: {league_id})")

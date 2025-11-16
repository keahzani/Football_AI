"""
Database Setup Script
Initializes all database tables
"""
import sqlite3
from pathlib import Path

# Define database path directly
DATABASE_PATH = Path(__file__).parent / 'data' / 'football.db'

def setup_database():
    """Create all database tables"""
    print("="*70)
    print("INITIALIZING DATABASE")
    print("="*70)
    
    # Ensure data directory exists
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create leagues table
    print("\nCreating leagues table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leagues (
            league_id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_name TEXT UNIQUE NOT NULL,
            country TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create teams table
    print("Creating teams table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            team_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT NOT NULL,
            league_id INTEGER,
            country TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (league_id) REFERENCES leagues (league_id),
            UNIQUE(team_name, league_id)
        )
    """)
    
    # Create matches table
    print("Creating matches table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id INTEGER,
            date DATE,
            home_team_id INTEGER,
            away_team_id INTEGER,
            home_goals INTEGER,
            away_goals INTEGER,
            result TEXT,
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
            season TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (league_id) REFERENCES leagues (league_id),
            FOREIGN KEY (home_team_id) REFERENCES teams (team_id),
            FOREIGN KEY (away_team_id) REFERENCES teams (team_id)
        )
    """)
    
    # Create odds table
    print("Creating odds table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS odds (
            odds_id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id INTEGER,
            bookmaker TEXT,
            home_odds REAL,
            draw_odds REAL,
            away_odds REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
    """)
    
    # Create fixtures table (for upcoming matches)
    print("Creating fixtures table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fixtures (
            fixture_id INTEGER PRIMARY KEY AUTOINCREMENT,
            league_id INTEGER,
            date DATE,
            home_team_id INTEGER,
            away_team_id INTEGER,
            status TEXT DEFAULT 'scheduled',
            venue TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (league_id) REFERENCES leagues (league_id),
            FOREIGN KEY (home_team_id) REFERENCES teams (team_id),
            FOREIGN KEY (away_team_id) REFERENCES teams (team_id)
        )
    """)
    
    # Create team_injuries table (optional - for future use)
    print("Creating team_injuries table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_injuries (
            injury_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER,
            player_name TEXT,
            injury_type TEXT,
            severity TEXT,
            status TEXT,
            expected_return DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams (team_id)
        )
    """)
    
    # Create indexes for better performance
    print("Creating indexes...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_matches_date 
        ON matches(date)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_matches_teams 
        ON matches(home_team_id, away_team_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_fixtures_date 
        ON fixtures(date)
    """)
    
    # Insert default leagues
    print("\nInserting default leagues...")
    leagues = [
        ('Premier League', 'England'),
        ('La Liga', 'Spain'),
        ('Bundesliga', 'Germany'),
        ('Serie A', 'Italy'),
        ('Ligue 1', 'France'),
        ('Scottish Premiership', 'Scotland'),
        ('Primeira Liga', 'Portugal'),
        ('Eredivisie', 'Netherlands'),
        ('Belgian Pro League', 'Belgium')
    ]
    
    for league_name, country in leagues:
        cursor.execute("""
            INSERT OR IGNORE INTO leagues (league_name, country)
            VALUES (?, ?)
        """, (league_name, country))
        print(f"  ✓ {league_name}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\n" + "="*70)
    print("✓ DATABASE INITIALIZED SUCCESSFULLY")
    print("="*70)
    print(f"\nDatabase location: {DATABASE_PATH}")
    print("\nTables created:")
    print("  ✓ leagues")
    print("  ✓ teams")
    print("  ✓ matches")
    print("  ✓ fixtures")
    print("  ✓ team_injuries")
    print("\nYou can now run:")
    print("  python main.py download")
    print("  python main.py train")
    print("="*70)

if __name__ == "__main__":
    setup_database()
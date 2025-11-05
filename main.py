#!/usr/bin/env python3
"""
Football Prediction System - Command Line Interface
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.database import DatabaseManager
from scrapers.historical_downloader import HistoricalDataDownloader
from features.engineer import FeatureEngineer
from models.train import MatchPredictor
from prediction.predict import FootballPredictor
from config.config import LEAGUES

def setup_database():
    """Initialize database"""
    print("Initializing database...")
    db = DatabaseManager()
    db.initialize_database()
    
    # Insert leagues
    for league_key, league_info in LEAGUES.items():
        league_id = db.insert_league(
            league_info['name'],
            league_info['country'],
            league_info['code'],
            league_info.get('api_id')
        )
        print(f"✓ {league_info['name']}")
    print("\n✓ Database initialized!")

def download_data():
    """Download historical data"""
    print("Downloading historical match data...")
    downloader = HistoricalDataDownloader()
    all_data = downloader.download_all_leagues()
    
    print("\nSaving to database...")
    for league_name, df in all_data.items():
        downloader.save_to_database(league_name, df)
    
    print("\n✓ Data download complete!")

def train_models():
    """Train prediction models"""
    print("Training prediction models...")
    predictor = MatchPredictor()
    results = predictor.train_all_leagues(save_models=True)
    print("\n✓ Training complete!")

def predict_matches(league: str = None, days: int = 7):
    """Predict upcoming matches"""
    predictor = FootballPredictor()
    predictor.load_models()
    
    # Convert league name to key
    league_key = None
    if league:
        for key, info in LEAGUES.items():
            if info['name'].lower() == league.lower() or key == league.lower():
                league_key = key
                break
        
        if not league_key:
            print(f"League '{league}' not found!")
            print(f"Available leagues: {', '.join([info['name'] for info in LEAGUES.values()])}")
            return
    
    predictions = predictor.predict_upcoming_fixtures(league_key=league_key, days_ahead=days)
    
    if not predictions:
        print("No upcoming fixtures found!")
        return
    
    print(f"\nFound {len(predictions)} upcoming matches:")
    for pred in predictions:
        predictor.display_prediction(pred)

def predict_specific_match(home_team: str, away_team: str, league: str):
    """Predict a specific match"""
    predictor = FootballPredictor()
    predictor.load_models()
    
    # Find league
    league_key = None
    league_id = None
    for key, info in LEAGUES.items():
        if info['name'].lower() == league.lower() or key == league.lower():
            league_key = key
            # Get league ID
            result = predictor.db.execute_query(
                "SELECT league_id FROM leagues WHERE league_name = ?",
                (info['name'],)
            )
            if result:
                league_id = result[0][0]
            break
    
    if not league_key or not league_id:
        print(f"League '{league}' not found!")
        return
    
    # Find teams
    home_team_result = predictor.db.execute_query(
        "SELECT team_id FROM teams WHERE team_name LIKE ? AND league_id = ?",
        (f"%{home_team}%", league_id)
    )
    
    away_team_result = predictor.db.execute_query(
        "SELECT team_id FROM teams WHERE team_name LIKE ? AND league_id = ?",
        (f"%{away_team}%", league_id)
    )
    
    if not home_team_result:
        print(f"Home team '{home_team}' not found in {league}!")
        return
    
    if not away_team_result:
        print(f"Away team '{away_team}' not found in {league}!")
        return
    
    home_team_id = home_team_result[0][0]
    away_team_id = away_team_result[0][0]
    
    prediction = predictor.predict_match(home_team_id, away_team_id, league_id)
    predictor.display_prediction(prediction)

def list_teams(league: str):
    """List all teams in a league"""
    db = DatabaseManager()
    
    # Find league
    league_id = None
    league_name = None
    for key, info in LEAGUES.items():
        if info['name'].lower() == league.lower() or key == league.lower():
            result = db.execute_query(
                "SELECT league_id, league_name FROM leagues WHERE league_name = ?",
                (info['name'],)
            )
            if result:
                league_id, league_name = result[0]
            break
    
    if not league_id:
        print(f"League '{league}' not found!")
        return
    
    # Get teams
    teams = db.execute_query(
        "SELECT team_name FROM teams WHERE league_id = ? ORDER BY team_name",
        (league_id,)
    )
    
    print(f"\nTeams in {league_name}:")
    print("="*50)
    for team in teams:
        print(f"  - {team[0]}")
    print(f"\nTotal: {len(teams)} teams")

def show_status():
    """Show system status"""
    db = DatabaseManager()
    
    print("\n" + "="*70)
    print("FOOTBALL PREDICTION SYSTEM - STATUS")
    print("="*70)
    
    # Database stats
    total_matches = db.execute_query("SELECT COUNT(*) FROM matches")[0][0]
    total_teams = db.execute_query("SELECT COUNT(*) FROM teams")[0][0]
    total_fixtures = db.execute_query("SELECT COUNT(*) FROM fixtures")[0][0]
    
    print(f"\nDatabase:")
    print(f"  Matches: {total_matches}")
    print(f"  Teams: {total_teams}")
    print(f"  Fixtures: {total_fixtures}")
    
    # Models
    print(f"\nTrained Models:")
    from pathlib import Path
    from config.config import MODELS_DIR
    
    for league_key, league_info in LEAGUES.items():
        model_path = MODELS_DIR / f"{league_key}_model.pkl"
        if model_path.exists():
            print(f"  ✓ {league_info['name']}")
        else:
            print(f"  ✗ {league_info['name']} (not trained)")
    print("="*70)

def update_fixtures(days_ahead: int = 7):
    """Update upcoming fixtures and team news"""
    from scrapers.fixtures_scraper import AdvancedFixturesScraper
    
    scraper = AdvancedFixturesScraper()
    result = scraper.update_all_fixtures(days_ahead=days_ahead)
    
    print(f"\n✓ Update complete!")
    print(f"  Fixtures: {result['fixtures']}")
    print(f"  Team news: {result['team_news']}")
    print(f"\nNow run: python main.py predict")

def show_status():
    """Show system status"""
    db = DatabaseManager()
    
    print("\n" + "="*70)
    print("FOOTBALL PREDICTION SYSTEM - STATUS")
    print("="*70)
    
    # Database stats
    total_matches = db.execute_query("SELECT COUNT(*) FROM matches")[0][0]
    total_teams = db.execute_query("SELECT COUNT(*) FROM teams")[0][0]
    total_fixtures = db.execute_query("SELECT COUNT(*) FROM fixtures")[0][0]
    
    print(f"\nDatabase:")
    print(f"  Matches: {total_matches}")
    print(f"  Teams: {total_teams}")
    print(f"  Fixtures: {total_fixtures}")
    
    # Models
    print(f"\nTrained Models:")
    from pathlib import Path
    from config.config import MODELS_DIR
    
    for league_key, league_info in LEAGUES.items():
        model_path = MODELS_DIR / f"{league_key}_model.pkl"
        if model_path.exists():
            print(f"  ✓ {league_info['name']}")
        else:
            print(f"  ✗ {league_info['name']} (not trained)")
    
    print("="*70)

def main():
    parser = argparse.ArgumentParser(
        description='Football Match Prediction System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initial setup (run once)
  python main.py setup              # Initialize database
  python main.py download           # Download historical data
  python main.py train              # Train models
  
  # Making predictions
  python main.py predict            # Predict all upcoming matches
  python main.py predict --league "Premier League" --days 3
  python main.py match --home "Arsenal" --away "Chelsea" --league "Premier League"
  
  # Utilities
  python main.py teams --league "La Liga"
  python main.py status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Setup command
    subparsers.add_parser('setup', help='Initialize database')
    
    # Download command
    subparsers.add_parser('download', help='Download historical data')
    
    # Train command
    subparsers.add_parser('train', help='Train prediction models')
    
    # Predict command
    predict_parser = subparsers.add_parser('predict', help='Predict upcoming matches')
    predict_parser.add_argument('--league', type=str, help='Filter by league')
    predict_parser.add_argument('--days', type=int, default=7, help='Days ahead to predict')
    
    # Match command
    match_parser = subparsers.add_parser('match', help='Predict specific match')
    match_parser.add_argument('--home', type=str, required=True, help='Home team name')
    match_parser.add_argument('--away', type=str, required=True, help='Away team name')
    match_parser.add_argument('--league', type=str, required=True, help='League name')
    
    # Teams command
    teams_parser = subparsers.add_parser('teams', help='List teams in a league')
    teams_parser.add_argument('--league', type=str, required=True, help='League name')
    
    # Status command
    subparsers.add_parser('status', help='Show system status')
    
    # Update fixtures command
    update_parser = subparsers.add_parser('update-fixtures', help='Fetch upcoming fixtures and team news')
    update_parser.add_argument('--days', type=int, default=7, help='Days ahead to fetch')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'setup':
            setup_database()
        elif args.command == 'download':
            download_data()
        elif args.command == 'train':
            train_models()
        elif args.command == 'predict':
            predict_matches(args.league, args.days)
        elif args.command == 'match':
            predict_specific_match(args.home, args.away, args.league)
        elif args.command == 'teams':
            list_teams(args.league)
        elif args.command == 'status':
            show_status()
        elif args.command == 'update-fixtures':
            update_fixtures(args.days)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

"""
Download historical match data from football-data.co.uk
"""
import requests
import pandas as pd
from pathlib import Path
from typing import Dict, List
import time
from config.config import LEAGUES, RAW_DATA_DIR, FOOTBALL_DATA_UK_BASE_URL
from utils.database import DatabaseManager

class HistoricalDataDownloader:
    """Downloads historical match data from football-data.co.uk"""
    
    def __init__(self):
        self.base_url = FOOTBALL_DATA_UK_BASE_URL
        self.db = DatabaseManager()
        
    def download_league_season(self, league_code: str, season: str) -> pd.DataFrame:
        """
        Download a single league season
        
        Args:
            league_code: League code (e.g., 'E0' for Premier League)
            season: Season year (e.g., '2324' for 2023-24)
        
        Returns:
            DataFrame with match data
        """
        # Convert season format: '2023' -> '2324'
        if len(season) == 4:
            season_code = season[2:4] + str(int(season[2:4]) + 1)
        else:
            season_code = season
            
        url = f"{self.base_url}/mmz4281/{season_code}/{league_code}.csv"
        
        try:
            print(f"Downloading {league_code} season {season_code} from {url}")
            df = pd.read_csv(url)
            
            # Add season column
            df['Season'] = f"{season}-{int(season)+1}"
            
            print(f"✓ Downloaded {len(df)} matches")
            return df
            
        except Exception as e:
            print(f"✗ Error downloading {league_code} {season_code}: {e}")
            return pd.DataFrame()
    
    def download_all_leagues(self, seasons: List[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Download all configured leagues for specified seasons
        
        Args:
            seasons: List of season years (e.g., ['2021', '2022', '2023'])
        
        Returns:
            Dictionary of league_name -> DataFrame
        """
        all_data = {}
        
        for league_key, league_info in LEAGUES.items():
            league_name = league_info['name']
            league_code = league_info['code']
            league_seasons = seasons or league_info.get('seasons', [])
            
            print(f"\n{'='*60}")
            print(f"Downloading {league_name}")
            print(f"{'='*60}")
            
            league_data = []
            
            for season in league_seasons:
                df = self.download_league_season(league_code, season)
                if not df.empty:
                    league_data.append(df)
                time.sleep(1)  # Be nice to the server
            
            if league_data:
                combined_df = pd.concat(league_data, ignore_index=True)
                all_data[league_name] = combined_df
                
                # Save to CSV
                output_path = RAW_DATA_DIR / f"{league_key}_raw.csv"
                combined_df.to_csv(output_path, index=False)
                print(f"\n✓ Saved {len(combined_df)} matches to {output_path}")
            
        return all_data
    
    def standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names across different seasons
        (football-data.co.uk sometimes changes column names)
        """
        # Create column mapping for consistency
        column_mapping = {
            'Div': 'Division',
            'Date': 'Date',
            'HomeTeam': 'HomeTeam',
            'AwayTeam': 'AwayTeam',
            'FTHG': 'HomeGoals',
            'FTAG': 'AwayGoals',
            'FTR': 'Result',
            'HTHG': 'HT_HomeGoals',
            'HTAG': 'HT_AwayGoals',
            'HTR': 'HT_Result',
            'HS': 'HomeShots',
            'AS': 'AwayShots',
            'HST': 'HomeShotsTarget',
            'AST': 'AwayShotsTarget',
            'HC': 'HomeCorners',
            'AC': 'AwayCorners',
            'HF': 'HomeFouls',
            'AF': 'AwayFouls',
            'HY': 'HomeYellow',
            'AY': 'AwayYellow',
            'HR': 'HomeRed',
            'AR': 'AwayRed',
            'B365H': 'B365_Home',
            'B365D': 'B365_Draw',
            'B365A': 'B365_Away',
        }
        
        # Rename columns that exist
        existing_mappings = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=existing_mappings)
        
        return df
    
    def save_to_database(self, league_name: str, df: pd.DataFrame):
        """
        Save downloaded data to database
        
        Args:
            league_name: Name of the league
            df: DataFrame with match data
        """
        if df.empty:
            print(f"No data to save for {league_name}")
            return
        
        # Standardize columns
        df = self.standardize_columns(df)
        
        # Get league ID
        league_query = "SELECT league_id FROM leagues WHERE league_name = ?"
        result = self.db.execute_query(league_query, (league_name,))
        
        if not result:
            print(f"League {league_name} not found in database")
            return
        
        league_id = result[0][0]
        
        # Process each match
        matches_added = 0
        matches_skipped = 0
        
        for _, row in df.iterrows():
            try:
                # Get or create teams
                home_team = row['HomeTeam']
                away_team = row['AwayTeam']
                
                home_team_id = self.db.insert_team(home_team, league_id)
                away_team_id = self.db.insert_team(away_team, league_id)
                
                # Convert date format (DD/MM/YYYY to YYYY-MM-DD)
                date_str = row['Date']
                if '/' in date_str:
                    parts = date_str.split('/')
                    if len(parts[2]) == 2:  # Two-digit year
                        year = '20' + parts[2]
                    else:
                        year = parts[2]
                    date_formatted = f"{year}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                else:
                    date_formatted = date_str
                
                # Insert match
                match_query = """
                    INSERT OR IGNORE INTO matches 
                    (league_id, season, date, home_team_id, away_team_id, 
                     home_goals, away_goals, result,
                     home_shots, away_shots, home_shots_on_target, away_shots_on_target,
                     home_corners, away_corners, home_fouls, away_fouls,
                     home_yellow, away_yellow, home_red, away_red)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                self.db.execute_update(match_query, (
                    league_id,
                    row.get('Season', ''),
                    date_formatted,
                    home_team_id,
                    away_team_id,
                    int(row.get('HomeGoals', 0)),
                    int(row.get('AwayGoals', 0)),
                    row.get('Result', ''),
                    int(row.get('HomeShots', 0)) if pd.notna(row.get('HomeShots')) else None,
                    int(row.get('AwayShots', 0)) if pd.notna(row.get('AwayShots')) else None,
                    int(row.get('HomeShotsTarget', 0)) if pd.notna(row.get('HomeShotsTarget')) else None,
                    int(row.get('AwayShotsTarget', 0)) if pd.notna(row.get('AwayShotsTarget')) else None,
                    int(row.get('HomeCorners', 0)) if pd.notna(row.get('HomeCorners')) else None,
                    int(row.get('AwayCorners', 0)) if pd.notna(row.get('AwayCorners')) else None,
                    int(row.get('HomeFouls', 0)) if pd.notna(row.get('HomeFouls')) else None,
                    int(row.get('AwayFouls', 0)) if pd.notna(row.get('AwayFouls')) else None,
                    int(row.get('HomeYellow', 0)) if pd.notna(row.get('HomeYellow')) else None,
                    int(row.get('AwayYellow', 0)) if pd.notna(row.get('AwayYellow')) else None,
                    int(row.get('HomeRed', 0)) if pd.notna(row.get('HomeRed')) else None,
                    int(row.get('AwayRed', 0)) if pd.notna(row.get('AwayRed')) else None,
                ))
                
                # Insert odds if available
                if 'B365_Home' in row and pd.notna(row['B365_Home']):
                    # Get match_id
                    match_id_query = """
                        SELECT match_id FROM matches 
                        WHERE league_id = ? AND date = ? 
                        AND home_team_id = ? AND away_team_id = ?
                    """
                    match_result = self.db.execute_query(
                        match_id_query, 
                        (league_id, date_formatted, home_team_id, away_team_id)
                    )
                    
                    if match_result:
                        match_id = match_result[0][0]
                        odds_query = """
                            INSERT OR IGNORE INTO odds 
                            (match_id, bookmaker, home_odds, draw_odds, away_odds)
                            VALUES (?, ?, ?, ?, ?)
                        """
                        self.db.execute_update(odds_query, (
                            match_id,
                            'Bet365',
                            float(row['B365_Home']),
                            float(row['B365_Draw']),
                            float(row['B365_Away'])
                        ))
                
                matches_added += 1
                
            except Exception as e:
                matches_skipped += 1
                if matches_skipped <= 5:  # Only print first few errors
                    print(f"Error processing match: {e}")
        
        print(f"\n✓ Database update complete:")
        print(f"  - Matches added: {matches_added}")
        print(f"  - Matches skipped: {matches_skipped}")

def main():
    """Main function to download all historical data"""
    print("="*70)
    print("FOOTBALL PREDICTION SYSTEM - HISTORICAL DATA DOWNLOADER")
    print("="*70)
    
    downloader = HistoricalDataDownloader()
    
    # Download all leagues
    print("\nStep 1: Downloading data from football-data.co.uk...")
    all_data = downloader.download_all_leagues()
    
    # Save to database
    print("\nStep 2: Saving to database...")
    for league_name, df in all_data.items():
        print(f"\nProcessing {league_name}...")
        downloader.save_to_database(league_name, df)
    
    print("\n" + "="*70)
    print("✓ Historical data download complete!")
    print("="*70)
    
    # Print summary
    db = DatabaseManager()
    total_matches = db.execute_query("SELECT COUNT(*) FROM matches")[0][0]
    total_teams = db.execute_query("SELECT COUNT(*) FROM teams")[0][0]
    
    print(f"\nDatabase Summary:")
    print(f"  - Total matches: {total_matches}")
    print(f"  - Total teams: {total_teams}")
    print(f"  - Leagues: {len(LEAGUES)}")

if __name__ == "__main__":
    main()

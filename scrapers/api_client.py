"""
API-Football Client
Fetches live league standings and fixtures from API-Football.com
"""
import requests
from typing import Dict, List, Optional
import pandas as pd
from config.config import API_FOOTBALL_KEY, API_FOOTBALL_BASE_URL

class APIFootballClient:
    """Client for API-Football.com"""
    
    def __init__(self):
        self.base_url = API_FOOTBALL_BASE_URL
        self.headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': API_FOOTBALL_KEY
        }
        
    def get_league_standings(self, league_id: int, season: int = 2024) -> Optional[Dict]:
        """
        Get current standings for a league
        
        Args:
            league_id: API league ID (e.g., 39 for Premier League)
            season: Year (e.g., 2024 for 2024-25 season)
            
        Returns:
            Dictionary with standings data
        """
        url = f"{self.base_url}/standings"
        params = {
            'league': league_id,
            'season': season
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('response') and len(data['response']) > 0:
                return data['response'][0]
            return None
            
        except Exception as e:
            print(f"Error fetching standings for league {league_id}: {e}")
            return None
    
    def get_standings_dataframe(self, league_id: int, season: int = 2024) -> Optional[pd.DataFrame]:
        """
        Get standings as pandas DataFrame
        
        Args:
            league_id: API league ID
            season: Year
            
        Returns:
            DataFrame with standings or None
        """
        data = self.get_league_standings(league_id, season)
        
        if not data or 'league' not in data:
            return None
            
        standings = data['league']['standings'][0]  # Get main standings
        
        # Extract relevant data
        rows = []
        for team_data in standings:
            row = {
                'Rank': team_data['rank'],
                'Team': team_data['team']['name'],
                'Logo': team_data['team']['logo'],
                'Played': team_data['all']['played'],
                'Won': team_data['all']['win'],
                'Drawn': team_data['all']['draw'],
                'Lost': team_data['all']['lose'],
                'GF': team_data['all']['goals']['for'],
                'GA': team_data['all']['goals']['against'],
                'GD': team_data['goalsDiff'],
                'Points': team_data['points'],
                'Form': team_data['form']
            }
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def get_all_standings(self, leagues_config: Dict) -> Dict[str, pd.DataFrame]:
        """
        Get standings for all configured leagues
        
        Args:
            leagues_config: Dictionary of league configurations
            
        Returns:
            Dictionary mapping league names to DataFrames
        """
        all_standings = {}
        
        for league_key, league_info in leagues_config.items():
            league_name = league_info['name']
            league_id = league_info.get('api_id')
            
            if league_id:
                print(f"Fetching standings for {league_name}...")
                df = self.get_standings_dataframe(league_id)
                
                if df is not None:
                    all_standings[league_name] = df
                    print(f"✓ Got {len(df)} teams")
                else:
                    print(f"✗ No data available")
        
        return all_standings
    
    def get_team_form_details(self, league_id: int, team_name: str, season: int = 2024) -> List[Dict]:
        """
        Get detailed form information for a team
        
        Args:
            league_id: API league ID
            team_name: Team name
            season: Year
            
        Returns:
            List of recent match results
        """
        standings = self.get_league_standings(league_id, season)
        
        if not standings or 'league' not in standings:
            return []
        
        # Find team in standings
        for team_data in standings['league']['standings'][0]:
            if team_data['team']['name'].lower() == team_name.lower():
                form = team_data.get('form', '')
                # Form is like "WWDLW" (W=Win, D=Draw, L=Loss)
                return [{'result': char} for char in form]
        
        return []
    
    def check_api_status(self) -> Dict:
        """
        Check API status and remaining requests
        
        Returns:
            Dictionary with API status info
        """
        url = f"{self.base_url}/status"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {'error': str(e)}

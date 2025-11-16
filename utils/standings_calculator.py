"""
Standings Calculator
Calculates league standings from match data in the database
No external API required - works entirely from local data
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sqlite3

class StandingsCalculator:
    """Calculate league standings from database match data"""
    
    def __init__(self, db_path: str):
        """
        Initialize calculator with database path
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
    
    def get_current_season(self, league_name: str) -> Optional[str]:
        """
        Get the most recent season for a league
        
        Args:
            league_name: Name of the league
            
        Returns:
            Season code (e.g., '2526' for 2025-26)
        """
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT season, COUNT(*) as match_count, MAX(date) as latest_date
        FROM matches m
        JOIN leagues l ON m.league_id = l.league_id
        WHERE l.league_name = ?
        GROUP BY season
        ORDER BY season DESC
        LIMIT 1
        """
        
        result = pd.read_sql_query(query, conn, params=(league_name,))
        conn.close()
        
        if not result.empty:
            return result.iloc[0]['season']
        return None
    
    def calculate_standings(self, league_name: str, season: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Calculate standings for a league and season
        
        Args:
            league_name: Name of the league
            season: Season code (if None, uses most recent)
            
        Returns:
            DataFrame with standings or None
        """
        conn = sqlite3.connect(self.db_path)
        
        # Get current season if not specified
        if season is None:
            season = self.get_current_season(league_name)
            if season is None:
                conn.close()
                return None
        
        # Get all matches for this league and season
        query = """
        SELECT 
            m.match_id,
            m.date,
            m.season,
            ht.team_name as home_team,
            at.team_name as away_team,
            m.home_goals,
            m.away_goals,
            m.result
        FROM matches m
        JOIN leagues l ON m.league_id = l.league_id
        JOIN teams ht ON m.home_team_id = ht.team_id
        JOIN teams at ON m.away_team_id = at.team_id
        WHERE l.league_name = ? AND m.season = ?
        ORDER BY m.date
        """
        
        matches_df = pd.read_sql_query(query, conn, params=(league_name, season))
        conn.close()
        
        if matches_df.empty:
            return None
        
        # Initialize standings dictionary
        teams = set(matches_df['home_team'].unique()) | set(matches_df['away_team'].unique())
        standings = {}
        
        for team in teams:
            standings[team] = {
                'Team': team,
                'Played': 0,
                'Won': 0,
                'Drawn': 0,
                'Lost': 0,
                'GF': 0,
                'GA': 0,
                'GD': 0,
                'Points': 0,
                'Home_W': 0,
                'Home_D': 0,
                'Home_L': 0,
                'Away_W': 0,
                'Away_D': 0,
                'Away_L': 0,
                'Form': [],
                'Last_5_Points': 0
            }
        
        # Process each match
        for _, match in matches_df.iterrows():
            home_team = match['home_team']
            away_team = match['away_team']
            home_goals = match['home_goals']
            away_goals = match['away_goals']
            result = match['result']
            
            # Update matches played
            standings[home_team]['Played'] += 1
            standings[away_team]['Played'] += 1
            
            # Update goals
            standings[home_team]['GF'] += home_goals
            standings[home_team]['GA'] += away_goals
            standings[away_team]['GF'] += away_goals
            standings[away_team]['GA'] += home_goals
            
            # Update results and points
            if result == 'H':  # Home win
                standings[home_team]['Won'] += 1
                standings[home_team]['Points'] += 3
                standings[home_team]['Home_W'] += 1
                standings[home_team]['Form'].append('W')
                
                standings[away_team]['Lost'] += 1
                standings[away_team]['Away_L'] += 1
                standings[away_team]['Form'].append('L')
                
            elif result == 'A':  # Away win
                standings[away_team]['Won'] += 1
                standings[away_team]['Points'] += 3
                standings[away_team]['Away_W'] += 1
                standings[away_team]['Form'].append('W')
                
                standings[home_team]['Lost'] += 1
                standings[home_team]['Home_L'] += 1
                standings[home_team]['Form'].append('L')
                
            else:  # Draw
                standings[home_team]['Drawn'] += 1
                standings[home_team]['Points'] += 1
                standings[home_team]['Home_D'] += 1
                standings[home_team]['Form'].append('D')
                
                standings[away_team]['Drawn'] += 1
                standings[away_team]['Points'] += 1
                standings[away_team]['Away_D'] += 1
                standings[away_team]['Form'].append('D')
        
        # Calculate goal difference and format form
        for team in standings:
            standings[team]['GD'] = standings[team]['GF'] - standings[team]['GA']
            
            # Get last 5 results
            form_list = standings[team]['Form'][-5:]
            standings[team]['Form'] = ''.join(form_list) if form_list else '-'
            
            # Calculate last 5 points
            last_5_results = standings[team]['Form']
            standings[team]['Last_5_Points'] = (
                last_5_results.count('W') * 3 + 
                last_5_results.count('D') * 1
            )
        
        # Convert to DataFrame
        standings_df = pd.DataFrame.from_dict(standings, orient='index')
        
        # Sort by Points, GD, GF
        standings_df = standings_df.sort_values(
            by=['Points', 'GD', 'GF'], 
            ascending=[False, False, False]
        ).reset_index(drop=True)
        
        # Add rank
        standings_df.insert(0, 'Rank', range(1, len(standings_df) + 1))
        
        return standings_df
    
    def get_home_standings(self, league_name: str, season: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get home-only standings"""
        full_standings = self.calculate_standings(league_name, season)
        
        if full_standings is None:
            return None
        
        # Create home standings
        home_df = full_standings[['Team', 'Home_W', 'Home_D', 'Home_L']].copy()
        home_df['Played'] = home_df['Home_W'] + home_df['Home_D'] + home_df['Home_L']
        home_df['Points'] = home_df['Home_W'] * 3 + home_df['Home_D']
        
        home_df = home_df.sort_values('Points', ascending=False).reset_index(drop=True)
        home_df.insert(0, 'Rank', range(1, len(home_df) + 1))
        
        return home_df
    
    def get_away_standings(self, league_name: str, season: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get away-only standings"""
        full_standings = self.calculate_standings(league_name, season)
        
        if full_standings is None:
            return None
        
        # Create away standings
        away_df = full_standings[['Team', 'Away_W', 'Away_D', 'Away_L']].copy()
        away_df['Played'] = away_df['Away_W'] + away_df['Away_D'] + away_df['Away_L']
        away_df['Points'] = away_df['Away_W'] * 3 + away_df['Away_D']
        
        away_df = away_df.sort_values('Points', ascending=False).reset_index(drop=True)
        away_df.insert(0, 'Rank', range(1, len(away_df) + 1))
        
        return away_df
    
    def get_form_table(self, league_name: str, season: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get standings based on last 5 matches only"""
        full_standings = self.calculate_standings(league_name, season)
        
        if full_standings is None:
            return None
        
        # Sort by last 5 points
        form_df = full_standings[['Team', 'Form', 'Last_5_Points']].copy()
        form_df = form_df.sort_values('Last_5_Points', ascending=False).reset_index(drop=True)
        form_df.insert(0, 'Rank', range(1, len(form_df) + 1))
        
        return form_df
    
    def get_season_label(self, season_code: str) -> str:
        """
        Convert season code to readable label
        
        Args:
            season_code: e.g., '2526'
            
        Returns:
            e.g., '2025-26'
        """
        if len(season_code) == 4:
            year1 = '20' + season_code[:2]
            year2 = season_code[2:]
            return f"{year1}-{year2}"
        return season_code
    
    def get_all_available_seasons(self, league_name: str) -> List[Tuple[str, str]]:
        """
        Get all available seasons for a league
        
        Args:
            league_name: Name of the league
            
        Returns:
            List of (season_code, season_label) tuples
        """
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT DISTINCT season, COUNT(*) as matches
        FROM matches m
        JOIN leagues l ON m.league_id = l.league_id
        WHERE l.league_name = ?
        GROUP BY season
        ORDER BY season DESC
        """
        
        result = pd.read_sql_query(query, conn, params=(league_name,))
        conn.close()
        
        seasons = []
        for _, row in result.iterrows():
            season_code = row['season']
            season_label = self.get_season_label(season_code)
            seasons.append((season_code, season_label))
        
        return seasons

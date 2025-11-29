"""
Live League Standings Calculator - COMPLETE VERSION
Calculates current standings from database matches
"""
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

class StandingsCalculator:
    """Calculate live league standings from database"""
    
    def __init__(self, db_path: str = "data/football.db"):
        self.db_path = Path(db_path)
        
    def get_current_season(self, league_name: str) -> str:
        """Get the most recent season with matches for a league"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT DISTINCT m.season
        FROM matches m
        JOIN leagues l ON m.league_id = l.league_id
        WHERE l.league_name = ?
        ORDER BY m.season DESC
        LIMIT 1
        """
        
        cursor.execute(query, (league_name,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else '2526'
    
    def format_season_display(self, season_code: str) -> str:
        """Format season code for display"""
        # If already formatted (contains hyphen), return as-is
        if '-' in season_code:
            return season_code
        
        # Format 4-digit codes like "2425"
        if len(season_code) == 4:
            year1 = f"20{season_code[:2]}"
            year2 = season_code[2:]
            return f"{year1}-{year2}"
        
        # Handle other formats
        return season_code
    
    def get_available_seasons(self, league_name: str) -> List[str]:
        """Get all available seasons for a league"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT DISTINCT m.season
        FROM matches m
        JOIN leagues l ON m.league_id = l.league_id
        WHERE l.league_name = ?
        ORDER BY m.season DESC
        """
        
        cursor.execute(query, (league_name,))
        seasons = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return seasons
    
    def get_all_available_seasons(self, league_name: str = None) -> List[tuple]:
        """
        Get all available seasons for a specific league as tuples of (code, label)
        
        Args:
            league_name: League name to get seasons for
        
        Returns:
            List of tuples: [(season_code, display_label), ...]
        """
        if not league_name:
            return []
        
        seasons = self.get_available_seasons(league_name)
        
        # Return as list of tuples: (code, formatted_display)
        return [(season, self.format_season_display(season)) for season in seasons]
    
    def calculate_standings(self, league_name: str, season: Optional[str] = None) -> pd.DataFrame:
        """Calculate standings - each match counted only once"""
        if season is None:
            season = self.get_current_season(league_name)
        
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT DISTINCT
            m.match_id,
            ht.team_name as home_team,
            at.team_name as away_team,
            m.home_goals,
            m.away_goals,
            m.result
        FROM matches m
        JOIN teams ht ON m.home_team_id = ht.team_id
        JOIN teams at ON m.away_team_id = at.team_id
        JOIN leagues l ON m.league_id = l.league_id
        WHERE l.league_name = ? AND m.season = ?
        """
        
        df = pd.read_sql_query(query, conn, params=(league_name, season))
        conn.close()
        
        if df.empty:
            return pd.DataFrame()
        
        teams = set(df['home_team'].unique()) | set(df['away_team'].unique())
        standings = []
        
        for team in teams:
            home_matches = df[df['home_team'] == team]
            away_matches = df[df['away_team'] == team]
            
            played = len(home_matches) + len(away_matches)
            
            # Home stats
            home_wins = len(home_matches[home_matches['result'] == 'H'])
            home_draws = len(home_matches[home_matches['result'] == 'D'])
            home_losses = len(home_matches[home_matches['result'] == 'A'])
            home_gf = int(home_matches['home_goals'].sum())
            home_ga = int(home_matches['away_goals'].sum())
            
            # Away stats
            away_wins = len(away_matches[away_matches['result'] == 'A'])
            away_draws = len(away_matches[away_matches['result'] == 'D'])
            away_losses = len(away_matches[away_matches['result'] == 'H'])
            away_gf = int(away_matches['away_goals'].sum())
            away_ga = int(away_matches['home_goals'].sum())
            
            # Total stats
            wins = home_wins + away_wins
            draws = home_draws + away_draws
            losses = home_losses + away_losses
            gf = home_gf + away_gf
            ga = home_ga + away_ga
            gd = gf - ga
            points = wins * 3 + draws
            
            # Form (last 5 matches)
            team_matches = pd.concat([
                home_matches.assign(is_home=True),
                away_matches.assign(is_home=False)
            ]).sort_index(ascending=False).head(5)
            
            form = []
            for _, match in team_matches.iterrows():
                if match['is_home']:
                    form.append('W' if match['result'] == 'H' else 'D' if match['result'] == 'D' else 'L')
                else:
                    form.append('W' if match['result'] == 'A' else 'D' if match['result'] == 'D' else 'L')
            
            standings.append({
                'Team': team,
                'Played': played,
                'Won': wins,
                'Drawn': draws,
                'Lost': losses,
                'GF': gf,
                'GA': ga,
                'GD': gd,
                'Points': points,
                'Form': ''.join(form)
            })
        
        standings_df = pd.DataFrame(standings)
        standings_df = standings_df.sort_values(
            by=['Points', 'GD', 'GF'], 
            ascending=[False, False, False]
        ).reset_index(drop=True)
        
        standings_df.insert(0, 'Rank', range(1, len(standings_df) + 1))
        
        return standings_df
    
    def get_home_standings(self, league_name: str, season: Optional[str] = None) -> pd.DataFrame:
        """Get home-only standings"""
        if season is None:
            season = self.get_current_season(league_name)
        
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT DISTINCT
            m.match_id,
            ht.team_name as team,
            m.home_goals as gf,
            m.away_goals as ga,
            m.result
        FROM matches m
        JOIN teams ht ON m.home_team_id = ht.team_id
        JOIN leagues l ON m.league_id = l.league_id
        WHERE l.league_name = ? AND m.season = ?
        """
        
        df = pd.read_sql_query(query, conn, params=(league_name, season))
        conn.close()
        
        if df.empty:
            return pd.DataFrame()
        
        teams = df['team'].unique()
        standings = []
        
        for team in teams:
            team_matches = df[df['team'] == team]
            played = len(team_matches)
            wins = len(team_matches[team_matches['result'] == 'H'])
            draws = len(team_matches[team_matches['result'] == 'D'])
            losses = len(team_matches[team_matches['result'] == 'A'])
            gf = int(team_matches['gf'].sum())
            ga = int(team_matches['ga'].sum())
            gd = gf - ga
            points = wins * 3 + draws
            
            standings.append({
                'Team': team,
                'Played': played,
                'Home_W': wins,      # Changed from 'Won'
                'Home_D': draws,     # Changed from 'Drawn'
                'Home_L': losses,    # Changed from 'Lost'
                'GF': gf,
                'GA': ga,
                'GD': gd,
                'Points': points
            })
        
        standings_df = pd.DataFrame(standings)
        if standings_df.empty:
            return standings_df
            
        standings_df = standings_df.sort_values(
            by=['Points', 'GD', 'GF'],
            ascending=[False, False, False]
        ).reset_index(drop=True)
        
        standings_df.insert(0, 'Rank', range(1, len(standings_df) + 1))
        
        return standings_df
    
    def get_away_standings(self, league_name: str, season: Optional[str] = None) -> pd.DataFrame:
        """Get away-only standings"""
        if season is None:
            season = self.get_current_season(league_name)
        
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT DISTINCT
            m.match_id,
            at.team_name as team,
            m.away_goals as gf,
            m.home_goals as ga,
            m.result
        FROM matches m
        JOIN teams at ON m.away_team_id = at.team_id
        JOIN leagues l ON m.league_id = l.league_id
        WHERE l.league_name = ? AND m.season = ?
        """
        
        df = pd.read_sql_query(query, conn, params=(league_name, season))
        conn.close()
        
        if df.empty:
            return pd.DataFrame()
        
        teams = df['team'].unique()
        standings = []
        
        for team in teams:
            team_matches = df[df['team'] == team]
            played = len(team_matches)
            wins = len(team_matches[team_matches['result'] == 'A'])
            draws = len(team_matches[team_matches['result'] == 'D'])
            losses = len(team_matches[team_matches['result'] == 'H'])
            gf = int(team_matches['gf'].sum())
            ga = int(team_matches['ga'].sum())
            gd = gf - ga
            points = wins * 3 + draws
            
            standings.append({
                'Team': team,
                'Played': played,
                'Away_W': wins,      # Changed from 'Won'
                'Away_D': draws,     # Changed from 'Drawn'
                'Away_L': losses,    # Changed from 'Lost'
                'GF': gf,
                'GA': ga,
                'GD': gd,
                'Points': points
            })
        
        standings_df = pd.DataFrame(standings)
        if standings_df.empty:
            return standings_df
            
        standings_df = standings_df.sort_values(
            by=['Points', 'GD', 'GF'],
            ascending=[False, False, False]
        ).reset_index(drop=True)
        
        standings_df.insert(0, 'Rank', range(1, len(standings_df) + 1))
        
        return standings_df
    
    def get_form_table(self, league_name: str, season: Optional[str] = None, num_matches: int = 5) -> pd.DataFrame:
        """Get standings based only on recent form"""
        if season is None:
            season = self.get_current_season(league_name)
        
        conn = sqlite3.connect(self.db_path)
        
        query = """
        SELECT DISTINCT
            m.match_id,
            ht.team_name as home_team,
            at.team_name as away_team,
            m.home_goals,
            m.away_goals,
            m.result
        FROM matches m
        JOIN teams ht ON m.home_team_id = ht.team_id
        JOIN teams at ON m.away_team_id = at.team_id
        JOIN leagues l ON m.league_id = l.league_id
        WHERE l.league_name = ? AND m.season = ?
        """
        
        df = pd.read_sql_query(query, conn, params=(league_name, season))
        conn.close()
        
        if df.empty:
            return pd.DataFrame()
        
        teams = set(df['home_team'].unique()) | set(df['away_team'].unique())
        form_standings = []
        
        for team in teams:
            team_matches = pd.concat([
                df[df['home_team'] == team].assign(is_home=True),
                df[df['away_team'] == team].assign(is_home=False)
            ]).sort_index(ascending=False).head(num_matches)
            
            if len(team_matches) == 0:
                continue
            
            points = 0
            wins = 0
            draws = 0
            losses = 0
            gf = 0
            ga = 0
            
            for _, match in team_matches.iterrows():
                if match['is_home']:
                    gf += match['home_goals']
                    ga += match['away_goals']
                    if match['result'] == 'H':
                        wins += 1
                        points += 3
                    elif match['result'] == 'D':
                        draws += 1
                        points += 1
                    else:
                        losses += 1
                else:
                    gf += match['away_goals']
                    ga += match['home_goals']
                    if match['result'] == 'A':
                        wins += 1
                        points += 3
                    elif match['result'] == 'D':
                        draws += 1
                        points += 1
                    else:
                        losses += 1
            
            form_standings.append({
                'Team': team,
                'Played': len(team_matches),
                'Won': wins,
                'Drawn': draws,
                'Lost': losses,
                'GF': int(gf),
                'GA': int(ga),
                'GD': int(gf - ga),
                'Points': points
            })
        
        form_df = pd.DataFrame(form_standings)
        form_df = form_df.sort_values(
            by=['Points', 'GD', 'GF'],
            ascending=[False, False, False]
        ).reset_index(drop=True)
        
        form_df.insert(0, 'Rank', range(1, len(form_df) + 1))
        
        return form_df
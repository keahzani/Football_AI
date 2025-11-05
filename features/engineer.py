"""
Feature Engineering for Match Prediction
Calculates rolling statistics, form, head-to-head, and other features
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from utils.database import DatabaseManager
from config.config import FORM_MATCHES, H2H_MATCHES, LEAGUES

class FeatureEngineer:
    """Calculate features for match prediction"""
    
    def __init__(self):
        self.db = DatabaseManager()
        
    def calculate_team_form(self, team_id: int, date: str, 
                           num_matches: int = FORM_MATCHES,
                           home_only: bool = False,
                           away_only: bool = False) -> Dict:
        """
        Calculate team form based on recent matches
        
        Args:
            team_id: Team ID
            date: Date before which to calculate form
            num_matches: Number of recent matches to consider
            home_only: Only consider home matches
            away_only: Only consider away matches
        
        Returns:
            Dictionary with form statistics
        """
        # Build query based on home/away filter
        if home_only:
            team_filter = "home_team_id = ?"
            goals_for = "home_goals"
            goals_against = "away_goals"
        elif away_only:
            team_filter = "away_team_id = ?"
            goals_for = "away_goals"
            goals_against = "home_goals"
        else:
            team_filter = "(home_team_id = ? OR away_team_id = ?)"
            
        query = f"""
            SELECT date, home_team_id, away_team_id, 
                   home_goals, away_goals, result
            FROM matches
            WHERE {team_filter} AND date < ?
            ORDER BY date DESC
            LIMIT ?
        """
        
        if home_only or away_only:
            params = (team_id, date, num_matches)
        else:
            params = (team_id, team_id, date, num_matches)
        
        matches = self.db.execute_query(query, params)
        
        if not matches:
            return {
                'matches_played': 0,
                'points': 0,
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'goals_scored': 0,
                'goals_conceded': 0,
                'goals_per_match': 0,
                'goals_conceded_per_match': 0,
                'points_per_match': 0,
                'win_rate': 0,
                'clean_sheets': 0
            }
        
        points = 0
        wins = draws = losses = 0
        goals_scored = goals_conceded = 0
        clean_sheets = 0
        
        for match in matches:
            match_date, home_id, away_id, home_goals, away_goals, result = match
            
            # Determine if team was home or away
            is_home = home_id == team_id
            
            if is_home:
                team_goals = home_goals
                opponent_goals = away_goals
                team_result = result
            else:
                team_goals = away_goals
                opponent_goals = home_goals
                team_result = 'A' if result == 'H' else ('H' if result == 'A' else 'D')
            
            goals_scored += team_goals
            goals_conceded += opponent_goals
            
            if opponent_goals == 0:
                clean_sheets += 1
            
            if team_result == ('H' if is_home else 'A'):
                wins += 1
                points += 3
            elif team_result == 'D':
                draws += 1
                points += 1
            else:
                losses += 1
        
        matches_played = len(matches)
        
        return {
            'matches_played': matches_played,
            'points': points,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_scored': goals_scored,
            'goals_conceded': goals_conceded,
            'goals_per_match': goals_scored / matches_played if matches_played > 0 else 0,
            'goals_conceded_per_match': goals_conceded / matches_played if matches_played > 0 else 0,
            'points_per_match': points / matches_played if matches_played > 0 else 0,
            'win_rate': wins / matches_played if matches_played > 0 else 0,
            'clean_sheets': clean_sheets,
            'clean_sheet_rate': clean_sheets / matches_played if matches_played > 0 else 0
        }
    
    def calculate_head_to_head(self, team1_id: int, team2_id: int, 
                               date: str, num_matches: int = H2H_MATCHES) -> Dict:
        """
        Calculate head-to-head statistics between two teams
        
        Args:
            team1_id: First team ID
            team2_id: Second team ID  
            date: Date before which to calculate H2H
            num_matches: Number of recent H2H matches to consider
        
        Returns:
            Dictionary with H2H statistics
        """
        query = """
            SELECT home_team_id, away_team_id, home_goals, away_goals, result, date
            FROM matches
            WHERE ((home_team_id = ? AND away_team_id = ?) 
                   OR (home_team_id = ? AND away_team_id = ?))
            AND date < ?
            ORDER BY date DESC
            LIMIT ?
        """
        
        matches = self.db.execute_query(
            query, 
            (team1_id, team2_id, team2_id, team1_id, date, num_matches)
        )
        
        if not matches:
            return {
                'h2h_matches': 0,
                'team1_wins': 0,
                'draws': 0,
                'team2_wins': 0,
                'team1_goals_avg': 0,
                'team2_goals_avg': 0,
                'total_goals_avg': 0,
                'team1_win_rate': 0
            }
        
        team1_wins = draws = team2_wins = 0
        team1_goals = team2_goals = 0
        
        for match in matches:
            home_id, away_id, home_goals, away_goals, result, _ = match
            
            # Determine which team was home
            if home_id == team1_id:
                team1_goals += home_goals
                team2_goals += away_goals
                if result == 'H':
                    team1_wins += 1
                elif result == 'D':
                    draws += 1
                else:
                    team2_wins += 1
            else:
                team1_goals += away_goals
                team2_goals += home_goals
                if result == 'A':
                    team1_wins += 1
                elif result == 'D':
                    draws += 1
                else:
                    team2_wins += 1
        
        matches_played = len(matches)
        
        return {
            'h2h_matches': matches_played,
            'team1_wins': team1_wins,
            'draws': draws,
            'team2_wins': team2_wins,
            'team1_goals_avg': team1_goals / matches_played if matches_played > 0 else 0,
            'team2_goals_avg': team2_goals / matches_played if matches_played > 0 else 0,
            'total_goals_avg': (team1_goals + team2_goals) / matches_played if matches_played > 0 else 0,
            'team1_win_rate': team1_wins / matches_played if matches_played > 0 else 0
        }
    
    def calculate_league_position(self, team_id: int, league_id: int, date: str) -> Dict:
        """
        Calculate team's league position and points at a given date
        
        Args:
            team_id: Team ID
            league_id: League ID
            date: Date to calculate position
        
        Returns:
            Dictionary with league position info
        """
        # Get all matches up to this date for the league
        query = """
            SELECT home_team_id, away_team_id, home_goals, away_goals, result
            FROM matches
            WHERE league_id = ? AND date < ?
        """
        
        matches = self.db.execute_query(query, (league_id, date))
        
        # Calculate standings
        standings = {}
        
        for match in matches:
            home_id, away_id, home_goals, away_goals, result = match
            
            # Initialize teams
            if home_id not in standings:
                standings[home_id] = {'points': 0, 'gd': 0, 'gf': 0, 'ga': 0}
            if away_id not in standings:
                standings[away_id] = {'points': 0, 'gd': 0, 'gf': 0, 'ga': 0}
            
            # Update goals
            standings[home_id]['gf'] += home_goals
            standings[home_id]['ga'] += away_goals
            standings[away_id]['gf'] += away_goals
            standings[away_id]['ga'] += home_goals
            
            # Update points
            if result == 'H':
                standings[home_id]['points'] += 3
            elif result == 'A':
                standings[away_id]['points'] += 3
            else:
                standings[home_id]['points'] += 1
                standings[away_id]['points'] += 1
        
        # Calculate goal difference
        for team in standings:
            standings[team]['gd'] = standings[team]['gf'] - standings[team]['ga']
        
        # Sort by points, then goal difference
        sorted_teams = sorted(
            standings.items(),
            key=lambda x: (x[1]['points'], x[1]['gd'], x[1]['gf']),
            reverse=True
        )
        
        # Find team position
        position = None
        total_teams = len(sorted_teams)
        
        for idx, (tid, stats) in enumerate(sorted_teams, 1):
            if tid == team_id:
                position = idx
                team_stats = stats
                break
        
        if position is None:
            return {
                'position': total_teams + 1,
                'points': 0,
                'goal_difference': 0,
                'position_percentile': 0
            }
        
        return {
            'position': position,
            'points': team_stats['points'],
            'goal_difference': team_stats['gd'],
            'goals_for': team_stats['gf'],
            'goals_against': team_stats['ga'],
            'position_percentile': (total_teams - position + 1) / total_teams if total_teams > 0 else 0
        }
    
    def get_match_features(self, home_team_id: int, away_team_id: int, 
                          league_id: int, date: str) -> Dict:
        """
        Calculate all features for a match
        
        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            league_id: League ID
            date: Match date
        
        Returns:
            Dictionary with all features for the match
        """
        features = {}
        
        # Overall form (last 5 matches)
        home_form = self.calculate_team_form(home_team_id, date)
        away_form = self.calculate_team_form(away_team_id, date)
        
        # Home/Away specific form
        home_form_home = self.calculate_team_form(home_team_id, date, home_only=True)
        away_form_away = self.calculate_team_form(away_team_id, date, away_only=True)
        
        # Head to head
        h2h = self.calculate_head_to_head(home_team_id, away_team_id, date)
        
        # League position
        home_position = self.calculate_league_position(home_team_id, league_id, date)
        away_position = self.calculate_league_position(away_team_id, league_id, date)
        
        # Home team features
        features['home_points_last5'] = home_form['points']
        features['home_goals_per_match'] = home_form['goals_per_match']
        features['home_goals_conceded_per_match'] = home_form['goals_conceded_per_match']
        features['home_win_rate'] = home_form['win_rate']
        features['home_form_home_points'] = home_form_home['points']
        features['home_clean_sheet_rate'] = home_form['clean_sheet_rate']
        
        # Away team features  
        features['away_points_last5'] = away_form['points']
        features['away_goals_per_match'] = away_form['goals_per_match']
        features['away_goals_conceded_per_match'] = away_form['goals_conceded_per_match']
        features['away_win_rate'] = away_form['win_rate']
        features['away_form_away_points'] = away_form_away['points']
        features['away_clean_sheet_rate'] = away_form['clean_sheet_rate']
        
        # League position features
        features['home_position'] = home_position['position']
        features['away_position'] = away_position['position']
        features['position_diff'] = away_position['position'] - home_position['position']
        features['home_points_total'] = home_position['points']
        features['away_points_total'] = away_position['points']
        features['home_goal_difference'] = home_position['goal_difference']
        features['away_goal_difference'] = away_position['goal_difference']
        
        # Head to head features
        features['h2h_matches'] = h2h['h2h_matches']
        features['h2h_home_wins'] = h2h['team1_wins']
        features['h2h_draws'] = h2h['draws']
        features['h2h_away_wins'] = h2h['team2_wins']
        features['h2h_home_win_rate'] = h2h['team1_win_rate']
        features['h2h_avg_goals'] = h2h['total_goals_avg']
        
        # Form difference
        features['form_diff'] = home_form['points'] - away_form['points']
        features['goals_diff'] = (home_form['goals_per_match'] - home_form['goals_conceded_per_match']) - \
                                 (away_form['goals_per_match'] - away_form['goals_conceded_per_match'])
        
        # Get league average goals (from config)
        league_name = self.db.execute_query(
            "SELECT league_name FROM leagues WHERE league_id = ?", 
            (league_id,)
        )[0][0]
        
        for league_key, league_info in LEAGUES.items():
            if league_info['name'] == league_name:
                features['league_avg_goals'] = league_info['avg_goals']
                break
        
        return features
    
    def create_training_dataset(self, league_id: int = None, 
                               start_date: str = None,
                               end_date: str = None) -> pd.DataFrame:
        """
        Create a complete training dataset with features and labels
        
        Args:
            league_id: Filter by league (None for all leagues)
            start_date: Start date filter
            end_date: End date filter
        
        Returns:
            DataFrame with features and target variable
        """
        # Build query
        query = """
            SELECT match_id, league_id, date, 
                   home_team_id, away_team_id, result
            FROM matches
            WHERE 1=1
        """
        params = []
        
        if league_id:
            query += " AND league_id = ?"
            params.append(league_id)
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date"
        
        matches = self.db.execute_query(query, tuple(params))
        
        print(f"Creating features for {len(matches)} matches...")
        
        dataset = []
        
        for idx, match in enumerate(matches):
            match_id, league_id, date, home_team_id, away_team_id, result = match
            
            if (idx + 1) % 100 == 0:
                print(f"Processing match {idx + 1}/{len(matches)}")
            
            try:
                features = self.get_match_features(
                    home_team_id, away_team_id, league_id, date
                )
                
                # Add identifiers
                features['match_id'] = match_id
                features['date'] = date
                features['home_team_id'] = home_team_id
                features['away_team_id'] = away_team_id
                features['league_id'] = league_id
                
                # Add target variable
                features['result'] = result
                
                dataset.append(features)
                
            except Exception as e:
                print(f"Error processing match {match_id}: {e}")
                continue
        
        df = pd.DataFrame(dataset)
        print(f"\n✓ Created dataset with {len(df)} matches and {len(df.columns)} features")
        
        return df

def main():
    """Test feature engineering"""
    engineer = FeatureEngineer()
    
    # Create training dataset for Premier League
    print("Creating training dataset for Premier League...")
    df = engineer.create_training_dataset(league_id=1, start_date='2022-01-01')
    
    print(f"\nDataset shape: {df.shape}")
    print(f"\nFeature columns:")
    print(df.columns.tolist())
    print(f"\nFirst few rows:")
    print(df.head())
    
    # Save to CSV
    output_path = "/home/claude/football-predictor/data/processed/training_data.csv"
    df.to_csv(output_path, index=False)
    print(f"\n✓ Saved to {output_path}")

if __name__ == "__main__":
    main()

"""
Enhanced Feature Engineering with Real-time Data
Includes injuries, cards, recent form, and advanced stats
"""
from features.engineer import FeatureEngineer
from utils.database import DatabaseManager
from typing import Dict
import json

class EnhancedFeatureEngineer(FeatureEngineer):
    """Extended feature engineer with real-time team news"""
    
    def __init__(self):
        super().__init__()
        
    def calculate_discipline_record(self, team_id: int, date: str, num_matches: int = 10) -> Dict:
        """
        Calculate team's discipline record (cards, fouls)
        
        Args:
            team_id: Team ID
            date: Date before which to calculate
            num_matches: Number of recent matches
        
        Returns:
            Dictionary with discipline stats
        """
        query = """
            SELECT home_yellow, away_yellow, home_red, away_red,
                   home_fouls, away_fouls, home_team_id
            FROM matches
            WHERE (home_team_id = ? OR away_team_id = ?) AND date < ?
            ORDER BY date DESC
            LIMIT ?
        """
        
        matches = self.db.execute_query(query, (team_id, team_id, date, num_matches))
        
        if not matches:
            return {
                'avg_yellow_cards': 0,
                'avg_red_cards': 0,
                'avg_fouls': 0,
                'discipline_score': 0  # Lower is better
            }
        
        total_yellows = 0
        total_reds = 0
        total_fouls = 0
        
        for match in matches:
            home_yellow, away_yellow, home_red, away_red, home_fouls, away_fouls, home_id = match
            
            is_home = home_id == team_id
            
            if is_home:
                total_yellows += home_yellow or 0
                total_reds += home_red or 0
                total_fouls += home_fouls or 0
            else:
                total_yellows += away_yellow or 0
                total_reds += away_red or 0
                total_fouls += away_fouls or 0
        
        num_matches_actual = len(matches)
        
        return {
            'avg_yellow_cards': total_yellows / num_matches_actual,
            'avg_red_cards': total_reds / num_matches_actual,
            'avg_fouls': total_fouls / num_matches_actual,
            'discipline_score': (total_yellows + total_reds * 3 + total_fouls * 0.1) / num_matches_actual
        }
    
    def calculate_attacking_threat(self, team_id: int, date: str, num_matches: int = 10) -> Dict:
        """
        Calculate attacking threat metrics
        
        Args:
            team_id: Team ID
            date: Date before which to calculate
            num_matches: Number of recent matches
        
        Returns:
            Dictionary with attacking stats
        """
        query = """
            SELECT home_shots, away_shots, home_shots_on_target, away_shots_on_target,
                   home_corners, away_corners, home_goals, away_goals, home_team_id
            FROM matches
            WHERE (home_team_id = ? OR away_team_id = ?) AND date < ?
            ORDER BY date DESC
            LIMIT ?
        """
        
        matches = self.db.execute_query(query, (team_id, team_id, date, num_matches))
        
        if not matches:
            return {
                'avg_shots': 0,
                'avg_shots_on_target': 0,
                'shot_accuracy': 0,
                'avg_corners': 0,
                'conversion_rate': 0
            }
        
        total_shots = 0
        total_shots_on_target = 0
        total_corners = 0
        total_goals = 0
        
        for match in matches:
            h_shots, a_shots, h_sot, a_sot, h_corners, a_corners, h_goals, a_goals, home_id = match
            
            is_home = home_id == team_id
            
            if is_home:
                total_shots += h_shots or 0
                total_shots_on_target += h_sot or 0
                total_corners += h_corners or 0
                total_goals += h_goals or 0
            else:
                total_shots += a_shots or 0
                total_shots_on_target += a_sot or 0
                total_corners += a_corners or 0
                total_goals += a_goals or 0
        
        num_matches_actual = len(matches)
        
        shot_accuracy = (total_shots_on_target / total_shots * 100) if total_shots > 0 else 0
        conversion_rate = (total_goals / total_shots * 100) if total_shots > 0 else 0
        
        return {
            'avg_shots': total_shots / num_matches_actual,
            'avg_shots_on_target': total_shots_on_target / num_matches_actual,
            'shot_accuracy': shot_accuracy,
            'avg_corners': total_corners / num_matches_actual,
            'conversion_rate': conversion_rate
        }
    
    def get_injury_impact(self, team_id: int) -> Dict:
        """
        Get injury impact for a team
        Note: This would query a separate injuries table if populated
        
        Args:
            team_id: Team ID
        
        Returns:
            Dictionary with injury impact
        """
        # Check if we have injury data
        query = """
            SELECT COUNT(*) as injury_count, 
                   SUM(CASE WHEN severity = 'major' THEN 1 ELSE 0 END) as major_injuries
            FROM team_injuries
            WHERE team_id = ? AND status = 'out'
        """
        
        try:
            result = self.db.execute_query(query, (team_id,))
            if result:
                injury_count, major_injuries = result[0]
                return {
                    'total_injuries': injury_count or 0,
                    'major_injuries': major_injuries or 0,
                    'injury_impact_score': (injury_count * 0.5 + major_injuries * 2) if injury_count else 0
                }
        except:
            # Table doesn't exist yet
            pass
        
        return {
            'total_injuries': 0,
            'major_injuries': 0,
            'injury_impact_score': 0
        }
    
    def get_enhanced_match_features(self, home_team_id: int, away_team_id: int,
                                   league_id: int, date: str) -> Dict:
        """
        Calculate all features including enhanced real-time data
        
        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            league_id: League ID
            date: Match date
        
        Returns:
            Dictionary with all enhanced features
        """
        # Get base features
        features = self.get_match_features(home_team_id, away_team_id, league_id, date)
        
        # Add discipline records
        home_discipline = self.calculate_discipline_record(home_team_id, date)
        away_discipline = self.calculate_discipline_record(away_team_id, date)
        
        features['home_discipline_score'] = home_discipline['discipline_score']
        features['home_avg_yellow_cards'] = home_discipline['avg_yellow_cards']
        features['home_avg_red_cards'] = home_discipline['avg_red_cards']
        
        features['away_discipline_score'] = away_discipline['discipline_score']
        features['away_avg_yellow_cards'] = away_discipline['avg_yellow_cards']
        features['away_avg_red_cards'] = away_discipline['avg_red_cards']
        
        # Add attacking threat
        home_attack = self.calculate_attacking_threat(home_team_id, date)
        away_attack = self.calculate_attacking_threat(away_team_id, date)
        
        features['home_avg_shots'] = home_attack['avg_shots']
        features['home_shot_accuracy'] = home_attack['shot_accuracy']
        features['home_conversion_rate'] = home_attack['conversion_rate']
        
        features['away_avg_shots'] = away_attack['avg_shots']
        features['away_shot_accuracy'] = away_attack['shot_accuracy']
        features['away_conversion_rate'] = away_attack['conversion_rate']
        
        # Add injury impact (if available)
        home_injuries = self.get_injury_impact(home_team_id)
        away_injuries = self.get_injury_impact(away_team_id)
        
        features['home_injury_impact'] = home_injuries['injury_impact_score']
        features['away_injury_impact'] = away_injuries['injury_impact_score']
        
        # Calculate differential features
        features['shots_differential'] = home_attack['avg_shots'] - away_attack['avg_shots']
        features['accuracy_differential'] = home_attack['shot_accuracy'] - away_attack['shot_accuracy']
        features['discipline_differential'] = away_discipline['discipline_score'] - home_discipline['discipline_score']
        features['injury_differential'] = away_injuries['injury_impact_score'] - home_injuries['injury_impact_score']
        
        return features

def main():
    """Test enhanced features"""
    engineer = EnhancedFeatureEngineer()
    
    # Test on a match
    print("Testing enhanced feature engineering...")
    features = engineer.get_enhanced_match_features(
        home_team_id=1,
        away_team_id=2,
        league_id=1,
        date='2024-11-01'
    )
    
    print(f"\nTotal features: {len(features)}")
    print(f"\nNew features added:")
    print(f"  - Discipline scores")
    print(f"  - Attacking threat metrics")
    print(f"  - Injury impact")
    print(f"  - Advanced differentials")

if __name__ == "__main__":
    main()

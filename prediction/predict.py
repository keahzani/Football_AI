"""
Match Prediction Interface
Main module for making predictions on matches
"""
import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import shap

from config.config import LEAGUES, MODELS_DIR, HIGH_CONFIDENCE_THRESHOLD, MEDIUM_CONFIDENCE_THRESHOLD
from features.engineer import FeatureEngineer
from utils.database import DatabaseManager

class FootballPredictor:
    """Main class for predicting football matches"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.engineer = FeatureEngineer()
        self.models = {}
        self.feature_columns = {}
        self.explainers = {}
        
    def load_models(self):
        """Load all trained models"""
        print("Loading models...")
        for league_key in LEAGUES.keys():
            try:
                model_path = MODELS_DIR / f"{league_key}_model.pkl"
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.models[league_key] = model_data['model']
                self.feature_columns[league_key] = model_data['feature_columns']
                print(f"✓ Loaded {LEAGUES[league_key]['name']} model")
                
            except FileNotFoundError:
                print(f"✗ Model not found for {LEAGUES[league_key]['name']}")
            except Exception as e:
                print(f"✗ Error loading {LEAGUES[league_key]['name']}: {e}")
    
    def get_team_name(self, team_id: int) -> str:
        """Get team name from ID"""
        result = self.db.execute_query(
            "SELECT team_name FROM teams WHERE team_id = ?",
            (team_id,)
        )
        return result[0][0] if result else f"Team {team_id}"
    
    def get_league_key(self, league_id: int) -> str:
        """Get league key from league ID"""
        result = self.db.execute_query(
            "SELECT league_name FROM leagues WHERE league_id = ?",
            (league_id,)
        )
        
        if not result:
            return None
        
        league_name = result[0][0]
        
        for key, info in LEAGUES.items():
            if info['name'] == league_name:
                return key
        
        return None
    
    def predict_match(self, home_team_id: int, away_team_id: int,
                     league_id: int, date: str = None) -> Dict:
        """
        Predict outcome of a match
        
        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            league_id: League ID
            date: Match date (defaults to today)
        
        Returns:
            Dictionary with prediction results
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Get league key
        league_key = self.get_league_key(league_id)
        if not league_key or league_key not in self.models:
            return {
                'error': 'Model not available for this league',
                'league_id': league_id
            }
        
        # Get team names
        home_team = self.get_team_name(home_team_id)
        away_team = self.get_team_name(away_team_id)
        
        # Calculate features
        try:
            features = self.engineer.get_match_features(
                home_team_id, away_team_id, league_id, date
            )
        except Exception as e:
            return {
                'error': f'Error calculating features: {e}',
                'home_team': home_team,
                'away_team': away_team
            }
        
        # Prepare features for model
        X = pd.DataFrame([features])
        X = X[self.feature_columns[league_key]]
        X = X.fillna(0)
        
        # Make prediction
        model = self.models[league_key]
        probabilities = model.predict_proba(X)[0]
        predicted_class = model.predict(X)[0]
        
        # Map to outcomes
        outcomes = ['Away Win', 'Draw', 'Home Win']
        predicted_outcome = outcomes[predicted_class]
        
        # Determine confidence level
        max_prob = max(probabilities)
        if max_prob >= HIGH_CONFIDENCE_THRESHOLD:
            confidence = 'HIGH'
        elif max_prob >= MEDIUM_CONFIDENCE_THRESHOLD:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        # Generate explanation
        explanation = self._generate_explanation(
            features, home_team, away_team, probabilities, predicted_outcome
        )
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'league': LEAGUES[league_key]['name'],
            'date': date,
            'prediction': {
                'outcome': predicted_outcome,
                'home_win_prob': float(probabilities[2]),
                'draw_prob': float(probabilities[1]),
                'away_win_prob': float(probabilities[0]),
                'confidence': confidence
            },
            'explanation': explanation,
            'features': features
        }
    
    def _generate_explanation(self, features: Dict, home_team: str, 
                            away_team: str, probabilities: np.ndarray,
                            predicted_outcome: str) -> List[str]:
        """
        Generate human-readable explanation for prediction
        
        Args:
            features: Match features
            home_team: Home team name
            away_team: Away team name
            probabilities: Prediction probabilities
            predicted_outcome: Predicted outcome
        
        Returns:
            List of explanation strings
        """
        explanation = []
        
        # Determine likely winner based on prediction
        home_prob = probabilities[2]
        away_prob = probabilities[0]
        draw_prob = probabilities[1]
        
        # Form analysis
        home_form = features.get('home_points_last5', 0)
        away_form = features.get('away_points_last5', 0)
        
        if home_form >= 12:  # 4+ wins
            explanation.append(f"✓ {home_team} in excellent form ({int(home_form)} points from last 5 matches)")
        elif home_form >= 9:  # 3 wins
            explanation.append(f"✓ {home_team} in good form ({int(home_form)} points from last 5)")
        elif home_form <= 3:
            explanation.append(f"⚠ {home_team} in poor form ({int(home_form)} points from last 5)")
        
        if away_form >= 12:
            explanation.append(f"✓ {away_team} in excellent form ({int(away_form)} points from last 5 matches)")
        elif away_form >= 9:
            explanation.append(f"✓ {away_team} in good form ({int(away_form)} points from last 5)")
        elif away_form <= 3:
            explanation.append(f"⚠ {away_team} in poor form ({int(away_form)} points from last 5)")
        
        # Home advantage
        home_form_home = features.get('home_form_home_points', 0)
        if home_form_home >= 12:
            explanation.append(f"✓ {home_team} strong at home ({int(home_form_home)}/15 points)")
        
        # Away form
        away_form_away = features.get('away_form_away_points', 0)
        if away_form_away >= 12:
            explanation.append(f"✓ {away_team} strong away from home ({int(away_form_away)}/15 points)")
        elif away_form_away <= 3:
            explanation.append(f"⚠ {away_team} struggles away from home ({int(away_form_away)}/15 points)")
        
        # League position
        home_pos = features.get('home_position', 0)
        away_pos = features.get('away_position', 0)
        
        if home_pos > 0 and away_pos > 0:
            pos_diff = away_pos - home_pos
            if pos_diff > 5:
                explanation.append(f"✓ {home_team} significantly higher in table (position {int(home_pos)} vs {int(away_pos)})")
            elif pos_diff < -5:
                explanation.append(f"✓ {away_team} significantly higher in table (position {int(away_pos)} vs {int(home_pos)})")
        
        # Head to head
        h2h_matches = features.get('h2h_matches', 0)
        if h2h_matches >= 3:
            h2h_home_wins = features.get('h2h_home_wins', 0)
            h2h_away_wins = features.get('h2h_away_wins', 0)
            h2h_draws = features.get('h2h_draws', 0)
            
            if h2h_home_wins >= h2h_away_wins + 2:
                explanation.append(f"✓ {home_team} dominant in recent H2H ({int(h2h_home_wins)} wins in last {int(h2h_matches)})")
            elif h2h_away_wins >= h2h_home_wins + 2:
                explanation.append(f"✓ {away_team} dominant in recent H2H ({int(h2h_away_wins)} wins in last {int(h2h_matches)})")
        
        # Goal scoring
        home_goals_per_match = features.get('home_goals_per_match', 0)
        away_goals_per_match = features.get('away_goals_per_match', 0)
        
        if home_goals_per_match >= 2.0:
            explanation.append(f"✓ {home_team} scoring well ({home_goals_per_match:.1f} goals/match)")
        
        if away_goals_per_match >= 2.0:
            explanation.append(f"✓ {away_team} scoring well ({away_goals_per_match:.1f} goals/match)")
        
        # Defensive record
        home_conceded = features.get('home_goals_conceded_per_match', 0)
        away_conceded = features.get('away_goals_conceded_per_match', 0)
        
        if home_conceded <= 0.5:
            explanation.append(f"✓ {home_team} strong defensively ({home_conceded:.1f} goals conceded/match)")
        
        if away_conceded >= 2.0:
            explanation.append(f"⚠ {away_team} vulnerable defensively ({away_conceded:.1f} goals conceded/match)")
        
        if not explanation:
            explanation.append("⚠ Limited historical data available for detailed analysis")
        
        return explanation
    
    def predict_upcoming_fixtures(self, league_key: str = None, 
                                 days_ahead: int = 7) -> List[Dict]:
        """
        Predict all upcoming fixtures
        
        Args:
            league_key: Specific league to predict (None for all)
            days_ahead: Number of days ahead to look for fixtures
        
        Returns:
            List of predictions
        """
        # Get upcoming fixtures
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        query = """
            SELECT f.fixture_id, f.league_id, f.date, 
                   f.home_team_id, f.away_team_id,
                   l.league_name
            FROM fixtures f
            JOIN leagues l ON f.league_id = l.league_id
            WHERE f.date <= ? AND f.status = 'scheduled'
            ORDER BY f.date
        """
        
        fixtures = self.db.execute_query(query, (end_date,))
        
        predictions = []
        
        for fixture in fixtures:
            fixture_id, league_id, date, home_team_id, away_team_id, league_name = fixture
            
            # Filter by league if specified
            if league_key:
                league_key_db = self.get_league_key(league_id)
                if league_key_db != league_key:
                    continue
            
            # Make prediction
            prediction = self.predict_match(home_team_id, away_team_id, league_id, date)
            
            if 'error' not in prediction:
                prediction['fixture_id'] = fixture_id
                predictions.append(prediction)
        
        return predictions
    
    def display_prediction(self, prediction: Dict):
        """Display prediction in a nice format"""
        if 'error' in prediction:
            print(f"\n✗ Error: {prediction['error']}")
            return
        
        print(f"\n{'='*70}")
        print(f"{prediction['home_team']} vs {prediction['away_team']}")
        print(f"{prediction['league']} - {prediction['date']}")
        print(f"{'='*70}")
        
        pred = prediction['prediction']
        print(f"\nPrediction:")
        print(f"  Home Win: {pred['home_win_prob']*100:5.1f}%")
        print(f"  Draw:     {pred['draw_prob']*100:5.1f}%")
        print(f"  Away Win: {pred['away_win_prob']*100:5.1f}%")
        print(f"\n  Most Likely: {pred['outcome']}")
        print(f"  Confidence: {pred['confidence']}")
        
        print(f"\nKey Factors:")
        for line in prediction['explanation']:
            print(f"  {line}")
        
        print(f"{'='*70}")

def main():
    """Example usage"""
    predictor = FootballPredictor()
    predictor.load_models()
    
    # Example: Predict upcoming Premier League fixtures
    print("\nPredicting upcoming Premier League fixtures...")
    predictions = predictor.predict_upcoming_fixtures(league_key='premier_league', days_ahead=7)
    
    for pred in predictions[:5]:  # Show first 5
        predictor.display_prediction(pred)

if __name__ == "__main__":
    main()

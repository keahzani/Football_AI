"""
Model Training for Football Match Prediction
Trains XGBoost models for each league
"""
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, log_loss
import xgboost as xgb
from typing import Dict, Tuple
import matplotlib.pyplot as plt

from config.config import LEAGUES, MODELS_DIR, MODEL_PARAMS
from features.engineer import FeatureEngineer
from utils.database import DatabaseManager

class MatchPredictor:
    """Train and evaluate match prediction models"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.engineer = FeatureEngineer()
        self.models = {}
        self.feature_columns = None
        
    def prepare_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features and target variable
        
        Args:
            df: DataFrame with features and result
        
        Returns:
            Tuple of (X, y) where X is features and y is target
        """
        # Define feature columns (exclude identifiers and target)
        exclude_cols = ['match_id', 'date', 'home_team_id', 'away_team_id', 
                       'league_id', 'result']
        
        self.feature_columns = [col for col in df.columns if col not in exclude_cols]
        
        X = df[self.feature_columns]
        
        # Convert result to numeric (0=Away, 1=Draw, 2=Home)
        result_mapping = {'A': 0, 'D': 1, 'H': 2}
        y = df['result'].map(result_mapping)
        
        # Handle missing values
        X = X.fillna(0)
        
        return X, y
    
    def train_model(self, X_train: pd.DataFrame, y_train: pd.Series,
                   X_val: pd.DataFrame = None, y_val: pd.Series = None) -> xgb.XGBClassifier:
        """
        Train XGBoost model
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
        
        Returns:
            Trained XGBoost model
        """
        model = xgb.XGBClassifier(**MODEL_PARAMS['xgboost'])
        
        if X_val is not None and y_val is not None:
            eval_set = [(X_train, y_train), (X_val, y_val)]
            model.fit(
                X_train, y_train,
                eval_set=eval_set,
                verbose=False
            )
        else:
            model.fit(X_train, y_train)
        
        return model
    
    def evaluate_model(self, model: xgb.XGBClassifier, 
                      X_test: pd.DataFrame, y_test: pd.Series,
                      league_name: str = "") -> Dict:
        """
        Evaluate model performance
        
        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels
            league_name: Name of league for reporting
        
        Returns:
            Dictionary with evaluation metrics
        """
        # Predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)
        
        # Accuracy
        accuracy = accuracy_score(y_test, y_pred)
        
        # Log loss (probability calibration)
        logloss = log_loss(y_test, y_pred_proba)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Classification report
        target_names = ['Away Win', 'Draw', 'Home Win']
        report = classification_report(y_test, y_pred, target_names=target_names, output_dict=True)
        
        print(f"\n{'='*60}")
        print(f"Model Evaluation: {league_name}")
        print(f"{'='*60}")
        print(f"Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        print(f"Log Loss: {logloss:.4f}")
        print(f"\nConfusion Matrix:")
        print(f"                Predicted")
        print(f"               Away  Draw  Home")
        print(f"Actual Away  [{cm[0,0]:4d} {cm[0,1]:4d} {cm[0,2]:4d}]")
        print(f"       Draw  [{cm[1,0]:4d} {cm[1,1]:4d} {cm[1,2]:4d}]")
        print(f"       Home  [{cm[2,0]:4d} {cm[2,1]:4d} {cm[2,2]:4d}]")
        
        print(f"\nPer-Class Performance:")
        for outcome in ['Away Win', 'Draw', 'Home Win']:
            print(f"{outcome:10s}: Precision={report[outcome]['precision']:.3f}, "
                  f"Recall={report[outcome]['recall']:.3f}, "
                  f"F1={report[outcome]['f1-score']:.3f}")
        
        # Analyze by match type (favorite vs underdog)
        self._analyze_by_match_type(model, X_test, y_test)
        
        return {
            'accuracy': accuracy,
            'log_loss': logloss,
            'confusion_matrix': cm,
            'classification_report': report
        }
    
    def _analyze_by_match_type(self, model: xgb.XGBClassifier,
                                X_test: pd.DataFrame, y_test: pd.Series):
        """Analyze accuracy by match type (clear favorite, even match, etc.)"""
        if 'position_diff' not in X_test.columns:
            return
        
        position_diff = X_test['position_diff'].values
        y_pred = model.predict(X_test)
        
        # Clear favorite: position difference > 5
        clear_favorite_mask = np.abs(position_diff) > 5
        if clear_favorite_mask.sum() > 0:
            acc = accuracy_score(y_test[clear_favorite_mask], y_pred[clear_favorite_mask])
            print(f"\nClear Favorite matches (pos diff > 5): {acc:.4f} ({acc*100:.2f}%)")
        
        # Even matches: position difference <= 3
        even_match_mask = np.abs(position_diff) <= 3
        if even_match_mask.sum() > 0:
            acc = accuracy_score(y_test[even_match_mask], y_pred[even_match_mask])
            print(f"Even matches (pos diff <= 3):          {acc:.4f} ({acc*100:.2f}%)")
    
    def get_feature_importance(self, model: xgb.XGBClassifier, top_n: int = 15) -> pd.DataFrame:
        """
        Get feature importance from trained model
        
        Args:
            model: Trained model
            top_n: Number of top features to return
        
        Returns:
            DataFrame with feature importance
        """
        importance_df = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': model.feature_importances_
        })
        
        importance_df = importance_df.sort_values('importance', ascending=False).head(top_n)
        
        print(f"\nTop {top_n} Most Important Features:")
        print("="*50)
        for idx, row in importance_df.iterrows():
            print(f"{row['feature']:35s}: {row['importance']:.4f}")
        
        return importance_df
    
    def train_league_model(self, league_name: str, 
                          test_size: float = 0.2,
                          val_size: float = 0.1) -> Dict:
        """
        Train model for a specific league
        
        Args:
            league_name: Name of the league
            test_size: Proportion of data for testing
            val_size: Proportion of training data for validation
        
        Returns:
            Dictionary with model and metrics
        """
        print(f"\n{'='*70}")
        print(f"Training model for {league_name}")
        print(f"{'='*70}")
        
        # Get league ID
        league_id_result = self.db.execute_query(
            "SELECT league_id FROM leagues WHERE league_name = ?",
            (league_name,)
        )
        
        if not league_id_result:
            print(f"League {league_name} not found!")
            return None
        
        league_id = league_id_result[0][0]
        
        # Create dataset
        print("Creating training dataset...")
        df = self.engineer.create_training_dataset(league_id=league_id)
        
        if len(df) < 50:
            print(f"Not enough data for {league_name} (only {len(df)} matches)")
            return None
        
        print(f"Dataset size: {len(df)} matches")
        
        # Prepare data
        X, y = self.prepare_data(df)
        
        # Time-based split (important for time series data!)
        # Sort by date first
        df_sorted = df.sort_values('date').reset_index(drop=True)
        X_sorted = X.iloc[df_sorted.index]
        y_sorted = y.iloc[df_sorted.index]
        
        # Split: 70% train, 10% validation, 20% test
        train_size = int(len(X_sorted) * (1 - test_size - val_size))
        val_size_abs = int(len(X_sorted) * val_size)
        
        X_train = X_sorted.iloc[:train_size]
        y_train = y_sorted.iloc[:train_size]
        
        X_val = X_sorted.iloc[train_size:train_size+val_size_abs]
        y_val = y_sorted.iloc[train_size:train_size+val_size_abs]
        
        X_test = X_sorted.iloc[train_size+val_size_abs:]
        y_test = y_sorted.iloc[train_size+val_size_abs:]
        
        print(f"\nData split:")
        print(f"  Train: {len(X_train)} matches")
        print(f"  Validation: {len(X_val)} matches")
        print(f"  Test: {len(X_test)} matches")
        
        # Train model
        print("\nTraining XGBoost model...")
        model = self.train_model(X_train, y_train, X_val, y_val)
        
        # Evaluate
        metrics = self.evaluate_model(model, X_test, y_test, league_name)
        
        # Feature importance
        importance = self.get_feature_importance(model)
        
        return {
            'model': model,
            'metrics': metrics,
            'feature_importance': importance,
            'feature_columns': self.feature_columns
        }
    
    def train_all_leagues(self, save_models: bool = True) -> Dict:
        """
        Train models for all leagues
        
        Args:
            save_models: Whether to save trained models to disk
        
        Returns:
            Dictionary of league_name -> model results
        """
        results = {}
        
        for league_key, league_info in LEAGUES.items():
            league_name = league_info['name']
            
            result = self.train_league_model(league_name)
            
            if result:
                results[league_name] = result
                
                if save_models:
                    # Save model
                    model_path = MODELS_DIR / f"{league_key}_model.pkl"
                    with open(model_path, 'wb') as f:
                        pickle.dump({
                            'model': result['model'],
                            'feature_columns': result['feature_columns'],
                            'metrics': result['metrics']
                        }, f)
                    print(f"\n✓ Model saved to {model_path}")
        
        # Print summary
        print(f"\n{'='*70}")
        print("TRAINING SUMMARY")
        print(f"{'='*70}")
        for league_name, result in results.items():
            acc = result['metrics']['accuracy']
            print(f"{league_name:20s}: {acc:.4f} ({acc*100:.2f}%)")
        
        return results
    
    def load_model(self, league_key: str) -> Dict:
        """
        Load a trained model from disk
        
        Args:
            league_key: League key (e.g., 'premier_league')
        
        Returns:
            Dictionary with model and metadata
        """
        model_path = MODELS_DIR / f"{league_key}_model.pkl"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        return model_data

def main():
    """Train models for all leagues"""
    print("="*70)
    print("FOOTBALL PREDICTION SYSTEM - MODEL TRAINING")
    print("="*70)
    
    predictor = MatchPredictor()
    results = predictor.train_all_leagues(save_models=True)
    
    print("\n" + "="*70)
    print("✓ Training complete!")
    print("="*70)

if __name__ == "__main__":
    main()

# Football Prediction System - Complete Usage Guide

## Table of Contents
1. [Installation](#installation)
2. [First Time Setup](#first-time-setup)
3. [Making Predictions](#making-predictions)
4. [Understanding Results](#understanding-results)
5. [Advanced Features](#advanced-features)
6. [Maintenance](#maintenance)
7. [Tips for Betting](#tips-for-betting)

---

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- 2GB free disk space
- Internet connection (for data download)

### Step 1: Get the Code
```bash
# If you have the project
cd football-predictor

# Check Python version
python3 --version  # Should be 3.8+
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- pandas (data manipulation)
- numpy (numerical computing)
- scikit-learn (machine learning)
- xgboost (prediction model)
- requests (HTTP requests)
- beautifulsoup4 (web scraping - optional)

---

## First Time Setup

### Quick Setup (Automated)
```bash
# Run the quick start script
./quickstart.sh
```

This will:
1. Install dependencies
2. Initialize database
3. Download 10,000+ historical matches
4. Train models for 5 leagues

**Time Required**: 15-25 minutes

### Manual Setup (Step by Step)

#### Step 1: Initialize Database
```bash
python3 main.py setup
```

Creates the SQLite database with all necessary tables.

#### Step 2: Download Historical Data
```bash
python3 main.py download
```

Downloads data for:
- Premier League (England)
- La Liga (Spain)
- Bundesliga (Germany)
- Serie A (Italy)
- Ligue 1 (France)

From seasons: 2021-22, 2022-23, 2023-24, 2024-25

**Data includes**:
- Match results (home/away goals, winner)
- Shots and shots on target
- Corners, fouls, cards
- Betting odds (Bet365, others)

#### Step 3: Train Models
```bash
python3 main.py train
```

Trains separate XGBoost models for each league.

**Expected output**:
```
Training model for Premier League
Dataset size: 1520 matches
Accuracy: 0.5658 (56.58%)

Training model for La Liga
Dataset size: 1520 matches
Accuracy: 0.5526 (55.26%)
...
```

#### Step 4: Verify Setup
```bash
python3 main.py status
```

Should show:
- Database with 10,000+ matches
- 100+ teams
- 5 trained models

---

## Making Predictions

### Predict All Upcoming Matches
```bash
python3 main.py predict
```

Shows predictions for all upcoming fixtures across all leagues.

### Predict Specific League
```bash
# Premier League only
python3 main.py predict --league "Premier League"

# Next 3 days only
python3 main.py predict --league "La Liga" --days 3
```

### Predict Specific Match
```bash
python3 main.py match --home "Arsenal" --away "Chelsea" --league "Premier League"
```

**Note**: Team names are fuzzy matched, so "Man United", "Manchester United", "Man Utd" all work.

### List Available Teams
```bash
python3 main.py teams --league "Premier League"
```

Use this to see exact team names in the database.

---

## Understanding Results

### Sample Prediction Output

```
======================================================================
Arsenal vs Chelsea
Premier League - 2025-11-10
======================================================================

Prediction:
  Home Win:  58.2%     ← Probability Arsenal wins
  Draw:      23.4%     ← Probability of draw
  Away Win:  18.4%     ← Probability Chelsea wins

  Most Likely: Home Win
  Confidence: MEDIUM    ← HIGH/MEDIUM/LOW

Key Factors:
  ✓ Arsenal in excellent form (13 points from last 5 matches)
  ✓ Arsenal strong at home (12/15 points)
  ⚠ Chelsea struggles away from home (2/15 points)
  ✓ Arsenal won last 3 H2H meetings
  ✓ Arsenal significantly higher in table (position 2 vs 8)
======================================================================
```

### Confidence Levels

| Level | Threshold | Interpretation |
|-------|-----------|----------------|
| **HIGH** | >65% | Strong prediction, clear favorite |
| **MEDIUM** | 50-65% | Moderate prediction, likely outcome |
| **LOW** | <50% | Uncertain, close match |

### What the Factors Mean

**Form Indicators**:
- ✓ "Excellent form" = 12+ points (4+ wins) from last 5
- ✓ "Good form" = 9-11 points (3 wins)
- ⚠ "Poor form" = 0-3 points

**Home/Away Form**:
- Shows performance specifically at home or away
- Maximum 15 points (5 wins)

**League Position**:
- Position difference >5 = significant quality gap
- Higher teams generally favored

**Head-to-Head (H2H)**:
- Recent meetings between these teams
- Can override other factors if dominant

---

## Advanced Features

### Custom Prediction Script

Create a Python script to make predictions programmatically:

```python
from prediction.predict import FootballPredictor

predictor = FootballPredictor()
predictor.load_models()

# Predict match
prediction = predictor.predict_match(
    home_team_id=1,
    away_team_id=2,
    league_id=1,
    date='2025-11-10'
)

print(f"Home win probability: {prediction['prediction']['home_win_prob']:.2%}")
```

### Backtesting

Test model accuracy on historical data:

```python
from models.train import MatchPredictor

predictor = MatchPredictor()

# Test on 2024-25 season
result = predictor.train_league_model("Premier League", test_size=0.3)

print(f"Test accuracy: {result['metrics']['accuracy']:.2%}")
```

### Feature Analysis

See which features matter most:

```python
from models.train import MatchPredictor
import pickle

# Load model
with open('models/premier_league_model.pkl', 'rb') as f:
    model_data = pickle.load(f)

# Get feature importance
importance = model_data['model'].feature_importances_
features = model_data['feature_columns']

# Sort and display
for feat, imp in sorted(zip(features, importance), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{feat:35s}: {imp:.4f}")
```

---

## Maintenance

### Update Historical Data (Monthly)

```bash
# Re-download latest data
python3 main.py download

# Retrain models with new data
python3 main.py train
```

### Track Prediction Accuracy

Check how well predictions are doing:

```python
from utils.database import DatabaseManager

db = DatabaseManager()

# Get predictions from last 30 days
query = """
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) as correct
FROM predictions
WHERE prediction_date >= date('now', '-30 days')
"""

result = db.execute_query(query)
total, correct = result[0]
accuracy = correct / total if total > 0 else 0

print(f"Last 30 days: {correct}/{total} = {accuracy:.2%}")
```

### Database Cleanup

If database gets too large:

```bash
# Backup first
cp data/football.db data/football.db.backup

# Remove old matches (keeping last 3 seasons)
sqlite3 data/football.db "DELETE FROM matches WHERE date < '2022-01-01'"
```

---

## Tips for Betting

### General Principles

1. **High Confidence Predictions (>65%)**: Most reliable
2. **Form is King**: Recent form matters more than league position
3. **Home Advantage**: Worth ~0.5 goals on average
4. **H2H Matters**: Some teams just beat others consistently

### Value Betting Strategy

Compare model probabilities with bookmaker odds:

```python
# Model says Arsenal has 60% chance (implied odds 1.67)
model_prob = 0.60
implied_odds = 1 / model_prob  # 1.67

# Bookmaker offers 2.10
bookmaker_odds = 2.10

# Value bet if bookmaker odds > implied odds
if bookmaker_odds > implied_odds:
    print("Value bet opportunity!")
    edge = (bookmaker_odds * model_prob) - 1
    print(f"Expected edge: {edge:.2%}")
```

### Bankroll Management

**Kelly Criterion** (conservative):

```python
def kelly_stake(probability, odds, bankroll, fraction=0.25):
    """
    Calculate optimal stake using Kelly Criterion
    
    Args:
        probability: Your estimated win probability (0-1)
        odds: Decimal odds offered
        bankroll: Total bankroll
        fraction: Kelly fraction (0.25 = quarter Kelly, conservative)
    """
    q = 1 - probability  # Probability of loss
    kelly = (probability * odds - 1) / (odds - 1)
    
    # Apply fractional Kelly for safety
    kelly *= fraction
    
    # Never bet more than 5% of bankroll
    kelly = min(kelly, 0.05)
    
    stake = bankroll * kelly
    return stake

# Example
stake = kelly_stake(
    probability=0.60,
    odds=2.10,
    bankroll=1000,
    fraction=0.25
)
print(f"Recommended stake: ${stake:.2f}")
```

### Avoiding Common Mistakes

❌ **DON'T**:
- Bet on every match (be selective)
- Chase losses with bigger bets
- Ignore low confidence predictions
- Bet based on emotion/favorite teams

✓ **DO**:
- Focus on high confidence (>60%) predictions
- Use proper bankroll management
- Track your bets and results
- Accept that losses will happen
- Consider model as ONE input, not gospel

### Sample Betting Log

Create a spreadsheet to track:

| Date | Match | Prediction | Odds | Stake | Result | Profit |
|------|-------|------------|------|-------|--------|--------|
| 2025-11-10 | Arsenal vs Chelsea | Home Win (58%) | 1.85 | $50 | Win | +$42.50 |
| 2025-11-11 | Real vs Barca | Draw (35%) | 3.50 | $0 | - | $0 |

Calculate ROI:
```
ROI = (Total Profit / Total Stakes) × 100
```

---

## Troubleshooting

### "No module named 'pandas'"
```bash
pip install -r requirements.txt
```

### "Database is locked"
Close any other programs accessing the database, then:
```bash
rm data/football.db-journal
```

### "Team not found"
```bash
# Check exact team names
python3 main.py teams --league "Premier League"

# Use partial matching
python3 main.py match --home "Man United" --away "City" --league "Premier League"
```

### Low Accuracy
- Ensure you have 3+ seasons of data
- Retrain models monthly
- Remember: 55% is good for football!

### Predictions seem random
Check:
```bash
python3 main.py status
```

Verify:
- 10,000+ matches in database
- All 5 models trained
- Data is recent (2024-25 season included)

---

## Next Steps

### Week 2 Enhancements
1. **Add Web Interface**: Use Streamlit for GUI
2. **Live Odds**: Scrape current bookmaker odds
3. **Telegram Bot**: Get predictions on mobile

### Month 2 Goals
1. **More Leagues**: Add Championship, Eredivisie
2. **Injury Data**: Integrate team news
3. **Ensemble Model**: Combine XGBoost + Poisson
4. **Betting Tracker**: Built-in profit/loss calculator

---

## Questions?

Check the README.md for more details or inspect the code files directly:
- `prediction/predict.py` - Prediction logic
- `features/engineer.py` - Feature calculations
- `models/train.py` - Model training
- `config/config.py` - All settings

**Remember**: This is for educational and personal use. Gamble responsibly!

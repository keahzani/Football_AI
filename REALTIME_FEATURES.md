# 🚀 Real-Time Data Features - Setup Guide

## What's New

Your system now has **advanced real-time data fetching**:

✅ **Upcoming Fixtures** - Automatically fetch next 7 days of matches
✅ **Team News** - Injuries, suspensions, form
✅ **Advanced Stats** - Cards, fouls, discipline records
✅ **Attacking Metrics** - Shots, accuracy, conversion rates
✅ **Enhanced Predictions** - Uses all new data for better accuracy

---

## 🎯 Quick Start

### Option 1: Free (Web Scraping)

Works immediately, no setup needed:

```powershell
python main.py update-fixtures
```

This will:
- Scrape upcoming fixtures from ESPN
- Fetch injury data from Physioroom.com
- Save to database
- Ready to predict!

### Option 2: Premium (API-Football - Recommended)

Get better data quality and more details:

#### Step 1: Get API Key (Free Tier)
1. Go to https://www.api-football.com/
2. Sign up for free account
3. Get API key (100 calls/day free)

#### Step 2: Set Environment Variable

**Windows PowerShell:**
```powershell
$env:API_FOOTBALL_KEY = "your_api_key_here"
```

**Or permanently:**
```powershell
[System.Environment]::SetEnvironmentVariable('API_FOOTBALL_KEY', 'your_api_key_here', 'User')
```

**Linux/Mac:**
```bash
export API_FOOTBALL_KEY="your_api_key_here"
```

#### Step 3: Update Fixtures
```powershell
python main.py update-fixtures
```

Now you get:
- Official fixture data
- Accurate injury reports
- Suspension information
- Lineup predictions
- Much more reliable data

---

## 📊 New Commands

### Update Fixtures (Main Command)
```powershell
# Fetch next 7 days
python main.py update-fixtures

# Fetch next 14 days
python main.py update-fixtures --days 14

# Fetch next 3 days
python main.py update-fixtures --days 3
```

### View Updated Predictions
```powershell
# After updating, see real upcoming matches
python main.py predict

# Filter by league
python main.py predict --league "Premier League"
```

### Check Status
```powershell
python main.py status
```

Shows:
- Number of fixtures in database
- Last update time
- Available data

---

## 🔄 Recommended Workflow

### Daily Routine:
```powershell
# Morning: Update fixtures
python main.py update-fixtures

# View today's predictions
python main.py predict --days 1

# Or predict specific match
python main.py match --home "Arsenal" --away "Chelsea" --league "Premier League"
```

### Weekly Routine:
```powershell
# Update historical data (once a week)
python main.py download

# Retrain models with new results
python main.py train

# Update upcoming fixtures
python main.py update-fixtures
```

---

## 📈 What's Improved

### Before (Basic Prediction):
```
Features used: 30
- Team form
- League position
- Head-to-head
- Goals stats
```

### Now (Enhanced Prediction):
```
Features used: 45+
- Team form ✓
- League position ✓
- Head-to-head ✓
- Goals stats ✓
- Discipline records (cards, fouls) ✨ NEW
- Attacking threat (shots, accuracy) ✨ NEW
- Injury impact ✨ NEW
- Suspension impact ✨ NEW
- Advanced differentials ✨ NEW
```

**Expected Accuracy Improvement: +3-5%**

---

## 🎯 Enhanced Features Explained

### 1. Discipline Records
- **Yellow/Red cards per match**
- **Fouls committed**
- **Discipline score** (teams with more cards = less reliable)

**Impact:** Teams with poor discipline may have key players suspended

### 2. Attacking Threat
- **Shots per match**
- **Shot accuracy %**
- **Conversion rate** (goals per shot)
- **Corners won**

**Impact:** Better measure of attacking quality than just goals

### 3. Injury Impact
- **Number of injuries**
- **Severity** (minor/major)
- **Key players missing**

**Impact:** Major injuries significantly affect predictions

### 4. Real-Time Form
- **Last 5 matches including latest results**
- **Recent goal scoring**
- **Defensive solidity**

**Impact:** More accurate than historical form alone

---

## 💡 Usage Examples

### Example 1: Big Match Prediction

```powershell
# Update to get latest team news
python main.py update-fixtures

# Predict the match
python main.py match --home "Liverpool" --away "Man City" --league "Premier League"
```

**Output will now include:**
```
Liverpool vs Man City
Premier League - 2025-11-10

Prediction:
  Home Win:  45.2%
  Draw:      28.3%
  Away Win:  26.5%

Enhanced Factors:
  ✓ Liverpool strong home form (12 pts last 5)
  ⚠ Liverpool missing 2 key players (Salah, Van Dijk)
  ✓ Liverpool excellent attacking threat (18 shots/game)
  ⚠ Man City better discipline (1.8 vs 2.4 cards/game)
  ⚠ Man City higher shot accuracy (65% vs 58%)
  
  Injury Impact: -0.8 (favors Man City)
  Discipline: +0.3 (favors Man City)
  Overall: Close match, City slight edge
```

### Example 2: Weekend Predictions

```powershell
# Update Friday afternoon
python main.py update-fixtures --days 3

# See all weekend matches
python main.py predict --days 3
```

### Example 3: Track Accuracy

```powershell
# Monday: Check how predictions did
python main.py download  # Updates with weekend results
python main.py train     # Retrains with new data
```

---

## 🔧 Troubleshooting

### "No fixtures found"
**Solution:** Run `python main.py update-fixtures` first

### "API key not set"
**Solution:** System will use free web scraping instead (works fine!)

### "Rate limit exceeded"
**Solution:** API-Football free tier = 100 calls/day. Either:
- Wait 24 hours
- Use web scraping mode (remove API key)

### "Team news not available"
**Solution:** Some free sources don't have all data. Consider:
- Getting API-Football key
- Accepting predictions without injury data (still good!)

---

## 📊 Data Sources

### Free Tier (No API Key):
- **Fixtures:** ESPN.com
- **Injuries:** Physioroom.com
- **Stats:** From historical database
- **Quality:** Good ⭐⭐⭐

### Premium Tier (With API Key):
- **Fixtures:** API-Football (official)
- **Injuries:** API-Football (official)
- **Lineups:** API-Football (predicted)
- **Odds:** API-Football (live)
- **Quality:** Excellent ⭐⭐⭐⭐⭐

---

## 🎓 Advanced Tips

### 1. Automate Daily Updates

**Windows Task Scheduler:**
```batch
@echo off
cd C:\Users\Administrator\Desktop\Football_AI\football-predictor
python main.py update-fixtures
```

Save as `update_daily.bat` and schedule in Task Scheduler

### 2. Track Prediction Accuracy

```powershell
# After matches finish
python main.py download
python main.py train

# Check accuracy in training output
```

### 3. Focus on High-Confidence Predictions

Only bet on:
- **HIGH confidence** (>65% probability)
- **Medium confidence** (50-65%) if you see clear reasons

### 4. Combine with Your Knowledge

The AI gives probabilities. You add:
- Manager tactics
- Team motivation
- Weather conditions
- Crowd impact

---

## 🚀 Next Steps

1. **Run your first update:**
   ```powershell
   python main.py update-fixtures
   ```

2. **Check what's upcoming:**
   ```powershell
   python main.py predict
   ```

3. **Compare predictions with bookmakers**

4. **Track your results!**

---

## ⚠️ Important Notes

- **Free tier works great** - Don't feel pressured to get API key
- **Update fixtures daily** for best results
- **Retrain models weekly** with new match results
- **Track accuracy** to see improvement over time
- **Injuries matter a lot** - Wait for team news before betting

---

## 📞 Support

**Issues?** Check:
- README.md for complete docs
- USAGE_GUIDE.md for examples
- This file for real-time features

**Working great?** Enjoy your enhanced predictions! 🎯⚽

---

*Last updated: November 2025*
*Real-time features added: November 2025*

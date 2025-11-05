# Windows Setup Guide

## Quick Setup for Windows Users

### Step 1: Open PowerShell
- Press `Windows + X`
- Select "Windows PowerShell" or "Terminal"

### Step 2: Navigate to Project
```powershell
cd C:\Users\Administrator\Desktop\Football_AI\football-predictor
```

### Step 3: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

If you get an error, try:
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Step 4: Setup Database
```powershell
python main.py setup
```

### Step 5: Download Data (~10 minutes)
```powershell
python main.py download
```

This downloads 10,000+ historical matches from free sources.

### Step 6: Train Models (~15 minutes)
```powershell
python main.py train
```

This trains 5 XGBoost models (one per league).

### Step 7: Make Predictions!
```powershell
python main.py predict
```

---

## Common Windows Issues

### Issue: "python not recognized"
**Solution**: Install Python from python.org
- Download Python 3.8 or higher
- Check "Add Python to PATH" during installation

### Issue: "pip not found"
**Solution**:
```powershell
python -m ensurepip --upgrade
```

### Issue: SSL Certificate Error
**Solution**:
```powershell
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Issue: Permission Denied
**Solution**: Run PowerShell as Administrator
- Right-click PowerShell
- Select "Run as Administrator"

---

## Verify Installation

Check Python version:
```powershell
python --version
```

Should show: Python 3.8 or higher

Check pip:
```powershell
pip --version
```

List installed packages:
```powershell
pip list
```

---

## Quick Commands Reference

```powershell
# Setup (run once)
python main.py setup
python main.py download
python main.py train

# Daily use
python main.py predict
python main.py predict --league "Premier League"
python main.py status

# Help
python main.py --help
python main.py predict --help
```

---

## File Locations

After setup, you'll have:

```
C:\Users\Administrator\Desktop\Football_AI\football-predictor\
├── data\
│   ├── football.db (your database)
│   └── raw\ (downloaded CSVs)
└── models\
    ├── premier_league_model.pkl
    ├── la_liga_model.pkl
    ├── bundesliga_model.pkl
    ├── serie_a_model.pkl
    └── ligue_1_model.pkl
```

---

## Tips for Windows

1. **Use Windows Terminal** (better than old PowerShell)
   - Install from Microsoft Store

2. **Add Python to PATH** if not done
   - Search "Environment Variables" in Windows
   - Add Python installation folder to PATH

3. **Use Tab Completion**
   - Type `python main.py pr` then press TAB
   - It auto-completes to `python main.py predict`

4. **Create Desktop Shortcut**
   ```powershell
   # Create a batch file
   echo "cd C:\Users\Administrator\Desktop\Football_AI\football-predictor" > predict.bat
   echo "python main.py predict" >> predict.bat
   echo "pause" >> predict.bat
   ```
   
   Double-click `predict.bat` to run predictions!

---

## Next Steps

1. ✅ Complete setup
2. ✅ Make first prediction
3. ✅ Read README.md for detailed docs
4. ✅ Explore USAGE_GUIDE.md for examples

---

**Need more help?** Check README.md or USAGE_GUIDE.md

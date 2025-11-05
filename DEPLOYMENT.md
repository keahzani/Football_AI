# 🚀 Deployment Guide

## Deploy Football Predictor to GitHub & Render

### Step 1: Push to GitHub

1. **Create new repository on GitHub**
   - Go to https://github.com/new
   - Name: `football-predictor`
   - Description: `AI-Powered Football Match Prediction System`
   - Public or Private (your choice)
   - Don't initialize with README (we already have one)

2. **Initialize Git in your local folder**
```powershell
cd C:\Users\Administrator\Desktop\Football_AI\football-predictor
git init
git add .
git commit -m "Initial commit: Football Prediction System with Web Interface"
```

3. **Connect to GitHub and push**
```powershell
git remote add origin https://github.com/YOUR_USERNAME/football-predictor.git
git branch -M main
git push -u origin main
```

---

### Step 2: Deploy to Render

#### Option A: Automatic Deploy (Recommended)

1. **Go to [Render.com](https://render.com)** and sign up/login

2. **Click "New +" → "Web Service"**

3. **Connect GitHub repository**
   - Click "Connect account" if not connected
   - Select your `football-predictor` repository

4. **Configure the service:**
   ```
   Name: football-predictor (or your choice)
   Region: Choose closest to you
   Branch: main
   Runtime: Python 3
   
   Build Command:
   pip install -r requirements.txt
   
   Start Command:
   sh setup.sh && streamlit run app/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
   ```

5. **Choose Plan:**
   - Free tier works perfectly!
   - Note: Free tier sleeps after 15 min of inactivity

6. **Click "Create Web Service"**

7. **Wait for deployment** (~10-15 minutes for first deploy)
   - Render will install dependencies
   - Run setup.sh (initialize DB, download data, train models)
   - Start Streamlit app

8. **Done!** Your app will be live at:
   ```
   https://football-predictor-xxxx.onrender.com
   ```

---

#### Option B: Manual Configuration

If automatic deploy fails, configure manually:

1. **Environment Variables** (Optional)
   - Add `API_FOOTBALL_KEY` if you have one
   - For live fixture updates

2. **Build Command:**
   ```bash
   pip install -r requirements.txt && python setup_database.py && python main.py download && python main.py train
   ```

3. **Start Command:**
   ```bash
   streamlit run app/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false
   ```

---

### Step 3: Verify Deployment

1. **Check Build Logs**
   - Should see: "Downloading historical data..."
   - Should see: "Training models..."
   - Should see: "Setup complete!"

2. **Open your app URL**
   - Navigate to provided Render URL
   - Wait for app to load (first load is slower)
   - Test a prediction!

3. **Common First-Time Delays:**
   - Initial build: 10-15 minutes (downloading data + training)
   - App cold start: 30-60 seconds (free tier)
   - After that: Fast! ⚡

---

### Troubleshooting

#### "Build Failed"
**Solution:** Check these files exist:
- `requirements.txt`
- `setup.sh`
- `Procfile`
- `setup_database.py`

#### "App Crashes on Start"
**Solution:** Check start command includes `$PORT`:
```bash
streamlit run app/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
```

#### "No module named 'streamlit'"
**Solution:** Verify `requirements.txt` includes all dependencies:
```txt
streamlit>=1.28.0
plotly>=5.14.0
xgboost>=1.7.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.2.0
requests>=2.31.0
beautifulsoup4>=4.12.0
```

#### "Database not found"
**Solution:** Ensure `setup.sh` runs before app starts:
```bash
sh setup.sh && streamlit run app/streamlit_app.py ...
```

#### "App is slow"
**Solution:** Normal for free tier!
- First request: 30-60 seconds (cold start)
- Subsequent requests: Fast
- Upgrade to paid tier for always-on

---

### Free Tier Limitations (Render)

✅ **What Works:**
- Full app functionality
- All predictions
- Database updates
- Beautiful interface

⚠️ **Limitations:**
- Sleeps after 15 min inactivity
- 30-60 sec cold start
- 750 hours/month (plenty!)

💡 **Tip:** Upgrade to $7/month for:
- Always-on (no sleep)
- Instant responses
- More resources

---

### Alternative Deployments

#### Streamlit Cloud (Free, Streamlit-specific)

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect GitHub
3. Select repository
4. Main file: `app/streamlit_app.py`
5. Deploy!

**Pros:** Free, optimized for Streamlit
**Cons:** Must run setup manually first

#### Heroku (Free tier ending)

1. Create `Procfile`:
   ```
   web: sh setup.sh && streamlit run app/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. Deploy:
   ```bash
   heroku create football-predictor
   git push heroku main
   heroku open
   ```

#### Railway (Alternative to Render)

Similar to Render:
1. Connect GitHub
2. Configure build/start commands
3. Deploy!

---

### Maintenance

#### Weekly Updates (Recommended)

Use the web interface:
1. Open your deployed app
2. Click **"🔄 Update Database"** in sidebar
3. Wait 10-15 minutes
4. Models updated with latest results!

Or via command line (if you have SSH access):
```bash
python main.py download
python main.py train
```

#### Monitor Usage

Check Render dashboard:
- Build time
- Response time
- Memory usage
- Error logs

---

### Security Notes

✅ **Safe to deploy:**
- No sensitive data in code
- Database is local (SQLite)
- API keys in environment variables (not code)

⚠️ **Don't commit:**
- `.env` files
- API keys in code
- Database files with personal data

---

### Success Checklist

Before deploying, ensure you have:

- [ ] All code files
- [ ] `requirements.txt` with all dependencies
- [ ] `setup.sh` script
- [ ] `Procfile` for Render
- [ ] `.gitignore` (excludes unnecessary files)
- [ ] `.streamlit/config.toml` for production settings
- [ ] `setup_database.py` for DB initialization

---

### Getting Help

**Render Support:**
- Docs: https://render.com/docs
- Community: https://community.render.com

**Streamlit Support:**
- Docs: https://docs.streamlit.io
- Forum: https://discuss.streamlit.io

**This Project:**
- Issues: GitHub Issues tab
- Discussions: GitHub Discussions

---

## 🎉 You're Ready to Deploy!

Your football prediction system will be accessible worldwide at:
```
https://your-app-name.onrender.com
```

Share it with friends! ⚽🎯🌍

---

*Last updated: November 2025*

@echo off
title Football Predictor - Local Server
cd /d C:\Users\Administrator\Desktop\Football_AI\football-predictor
echo.
echo ========================================================
echo   ⚽ Starting Football Match Predictor
echo ========================================================
echo.
echo 🚀 Starting server...
echo.
start "" "http://localhost:8501"
python -m streamlit run app/streamlit_app.py
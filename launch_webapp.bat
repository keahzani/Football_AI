@echo off
echo ========================================
echo   Football Prediction Web App
echo ========================================
echo.
echo Starting web application...
echo Your browser will open automatically.
echo.
echo To stop the app, press Ctrl+C
echo ========================================
echo.

cd /d "%~dp0"
streamlit run app/streamlit_app.py

pause

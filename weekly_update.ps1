# Weekly Update Script - Minimal
Write-Host "🔄 Starting weekly update..." -ForegroundColor Green

Set-Location C:\Users\Administrator\Desktop\Football_AI\football-predictor

Write-Host "📥 Downloading latest matches..." -ForegroundColor Yellow
python main.py download

Write-Host "🔍 Checking for duplicates..." -ForegroundColor Yellow
python check_duplicates.py

Write-Host "📤 Pushing to GitHub..." -ForegroundColor Yellow
git add -f data/football.db
git add data/raw/*.csv 
$date = Get-Date -Format "dd/MM/yyyy"
git commit -m "Weekly update: $date"
git push

Write-Host "✅ Update complete! Streamlit will redeploy in 3 minutes." -ForegroundColor Green
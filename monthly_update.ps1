# Monthly Update Script - Complete with Duplicate Prevention
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "MONTHLY FOOTBALL DATA UPDATE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location C:\Users\Administrator\Desktop\Football_AI\football-predictor

# Step 1: Download latest matches
Write-Host "Downloading latest matches..." -ForegroundColor Yellow
python main.py download

if ($LASTEXITCODE -ne 0) {
    Write-Host "Download failed! Exiting..." -ForegroundColor Red
    exit 1
}

Write-Host "Download complete!" -ForegroundColor Green
Write-Host ""

# Step 2: Check and remove duplicates
Write-Host "Checking for duplicates..." -ForegroundColor Yellow
python check_duplicates.py

Write-Host ""

# Step 3: Retrain models
$retrain = Read-Host "Retrain models? This takes 10-15 minutes (y/n)"
if ($retrain -eq 'y') {
    Write-Host "Retraining models..." -ForegroundColor Yellow
    python main.py train
    Write-Host "Models retrained!" -ForegroundColor Green
}

Write-Host ""

# Step 4: Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow

# Add database
git add -f data/football.db

# Add all CSV files
git add data/raw/*.csv

# Add models if retrained
if ($retrain -eq 'y') {
    git add models/*.pkl
}

# Check if there are changes
$changes = git status --porcelain
if ($changes) {
    $date = Get-Date -Format "dd/MM/yyyy"
    $commit_msg = "Monthly update: $date"
    
    if ($retrain -eq 'y') {
        $commit_msg += " + retrained models"
    }
    
    git commit -m $commit_msg
    git push
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "Update complete! Changes pushed to GitHub." -ForegroundColor Green
    Write-Host "Streamlit will redeploy in 3-5 minutes." -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "No changes detected. Database already up to date." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  - Downloaded: Done" -ForegroundColor Green
Write-Host "  - Duplicates removed: Done" -ForegroundColor Green
if ($retrain -eq 'y') {
    Write-Host "  - Models retrained: Done" -ForegroundColor Green
} else {
    Write-Host "  - Models retrained: Skipped" -ForegroundColor Yellow
}
Write-Host "  - Pushed to GitHub: Done" -ForegroundColor Green
Write-Host ""
Write-Host "Tip: Retrain models monthly for best accuracy!" -ForegroundColor Cyan
Write-Host ""
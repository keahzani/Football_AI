@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0weekly_update.ps1"
pause
@echo off
echo ========================================================
echo   Creating Desktop Shortcuts
echo ========================================================
echo.

set SCRIPT_DIR=%~dp0
set DESKTOP=%USERPROFILE%\Desktop

:: Create Weekly Update shortcut
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\⚽ Weekly Update.lnk'); $s.TargetPath = '%SCRIPT_DIR%Weekly Update.bat'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.IconLocation = 'shell32.dll,13'; $s.Save()"

:: Create Monthly Update shortcut
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\⚽ Monthly Update.lnk'); $s.TargetPath = '%SCRIPT_DIR%Monthly Update.bat'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.IconLocation = 'shell32.dll,1'; $s.Save()"

:: Create Open App shortcut (UPDATED LINE BELOW)
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\⚽ Open Football App.lnk'); $s.TargetPath = '%SCRIPT_DIR%launch_webapp.bat'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.IconLocation = 'shell32.dll,14'; $s.Save()"

echo.
echo ✅ Desktop shortcuts created!
echo.
echo You now have 3 shortcuts on your desktop:
echo   - ⚽ Weekly Update
echo   - ⚽ Monthly Update  
echo   - ⚽ Open Football App
echo.
pause
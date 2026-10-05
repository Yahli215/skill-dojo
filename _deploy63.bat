@echo off
cd /d "%~dp0"
del /f /q ".git\HEAD.lock" 2>nul
del /f /q ".git\index.lock" 2>nul
git add index.html sw.js
git commit -m "Sent-to-Habits verdicts drop out of verdicts list (v63)"
git push
echo.
echo Done. Press any key to close.
pause >nul

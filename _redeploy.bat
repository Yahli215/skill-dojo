@echo off
cd /d "%~dp0"
del /f /q ".git\HEAD.lock" 2>nul
del /f /q ".git\index.lock" 2>nul
git commit --allow-empty -m "trigger: force Pages redeploy"
git push
echo.
echo Done. Press any key to close.
pause >nul

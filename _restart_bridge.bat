@echo off
cd /d "%~dp0"
taskkill /f /im pythonw.exe 2>nul
timeout /t 2 /nobreak >nul
start "" pythonw presence-bridge\bridge.py
echo Bridge restarted. You can close this window.
pause >nul

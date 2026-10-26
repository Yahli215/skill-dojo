@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo  SwitchBot Presence Bridge — installer
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from https://python.org
    pause & exit /b 1
)

:: Create venv
echo [1/3]  Creating virtual environment...
python -m venv venv
if errorlevel 1 ( echo ERROR creating venv. & pause & exit /b 1 )

:: Install packages
echo [2/3]  Installing packages (bleak + aiohttp)...
call venv\Scripts\pip install --quiet bleak aiohttp
if errorlevel 1 ( echo ERROR installing packages. & pause & exit /b 1 )

:: Add to Startup
echo [3/3]  Registering auto-start...
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
copy /Y "%~dp0start.vbs" "%STARTUP%\skill-dojo-presence.vbs" >nul
echo       Shortcut added to: %STARTUP%

echo.
echo ============================================
echo  Installation complete!
echo ============================================
echo.
echo  Next steps:
echo  1. Run:   python discover.py
echo     and copy your sensor's MAC address.
echo  2. Open bridge.py and paste the MAC into
echo     the  MAC = "XX:XX:XX:XX:XX:XX"  line.
echo  3. Run:   python bridge.py
echo     and confirm: curl http://127.0.0.1:8765/presence
echo  4. Log out and back in — bridge starts
echo     automatically from now on.
echo.
pause

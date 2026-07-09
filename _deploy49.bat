@echo off
cd /d "%~dp0"
del /f /q ".git\HEAD.lock" 2>nul
del /f /q ".git\index.lock" 2>nul
git add index.html sw.js
git commit -m "feat: full-width check bar, cleaner habit cards (v49)"
git push
echo.
echo Done. Press any key to close.
pause >nul

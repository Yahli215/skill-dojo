@echo off
cd /d "%~dp0"
del /f /q ".git\HEAD.lock" 2>nul
del /f /q ".git\index.lock" 2>nul
git add index.html sw.js
git commit -m "feat: Disturbing Thoughts Challenge Space, thought FAB, Mind tab (v51)"
git push
echo.
echo Done. Press any key to close.
pause >nul

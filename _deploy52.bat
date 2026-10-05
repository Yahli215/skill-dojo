@echo off
cd /d "%~dp0"
del /f /q ".git\HEAD.lock" 2>nul
del /f /q ".git\index.lock" 2>nul
git add index.html sw.js
git commit -m "fix: archive union merge on pull, no more items deleted on tab-switch (v52)"
git push
echo.
echo Done. Press any key to close.
pause >nul

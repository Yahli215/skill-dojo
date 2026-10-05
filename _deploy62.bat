@echo off
cd /d "%~dp0"
del /f /q ".git\HEAD.lock" 2>nul
del /f /q ".git\index.lock" 2>nul
git add _review-prompt.md
git commit -m "docs: review prompt — high-stakes 3-candidate verdicts (v62)"
git push
echo.
echo Done. Press any key to close.
pause >nul

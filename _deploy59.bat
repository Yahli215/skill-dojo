@echo off
cd /d "%~dp0"
del /f /q ".git\HEAD.lock" 2>nul
del /f /q ".git\index.lock" 2>nul
git add index.html sw.js _review-prompt.md
git commit -m "feat: review log — single freeform textarea, morning Claude classifies (v59)"
git push
echo.
echo Done. Press any key to close.
pause >nul

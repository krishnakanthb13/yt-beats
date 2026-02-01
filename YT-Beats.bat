@echo off
setlocal
title YT-Beats

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not found in PATH.
    pause
    exit /b 1
)

REM We no longer strictly check for MPV here because src.app handles valid detection
REM including Chocolatey paths which might not be in the global PATH for .bat execution.

echo Starting YT-Beats...
python -m src.app

if %errorlevel% neq 0 (
    echo.
    echo Application exited with error code %errorlevel%.
    pause
)
endlocal

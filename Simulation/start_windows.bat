@echo off
setlocal
cd /d "%~dp0"
title LPWAN Edge Intelligence Dashboard

echo ============================================================
echo   LPWAN EDGE INTELLIGENCE - LOCAL DASHBOARD
echo ============================================================
echo.

py -3.13 --version >nul 2>&1
if not errorlevel 1 (
    echo Using Python 3.13...
    py -3.13 run_app.py
) else (
    echo Python 3.13 launcher was not found. Trying the default Python...
    python --version
    if errorlevel 1 (
        echo ERROR: Python is not installed or is not on PATH.
        echo Install Python 3.13 and enable the Python Launcher, then retry.
        pause
        exit /b 1
    )
    python run_app.py
)

if errorlevel 1 (
    echo.
    echo Dashboard did not start. Read the error above.
    echo If port 8000 is already occupied, close the previous dashboard
    echo or run: py -3.13 run_app.py --port 8010
)
echo.
pause
endlocal

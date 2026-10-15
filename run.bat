@echo off
title CRICBRAIN - Men's International Cricket Records (Built by Suyog Shinde)
echo ===================================================================
echo     CRICBRAIN - The Brain Behind Cricket's Greatest Numbers
echo     Agentic AI Powered by Real-Time Google Search Grounding
echo     Built by Suyog Shinde
echo ===================================================================
echo.
echo Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not found in your PATH. Please install Python 3.9+.
    pause
    exit /b 1
)

echo.
echo Launching CRICBRAIN Web Application...
echo Opening your web browser at http://localhost:5050 ...
start http://localhost:5050
echo.
echo Starting Flask Server (Press Ctrl+C to stop)...
python app.py
pause

@echo off
REM Enhanced launcher for the Electric Vehicle Digital Twin
REM This script provides an easy way to start the simulation on Windows with automatic web interface opening

REM Set the project directory path
set PROJECT_PATH=%~dp0
echo Project path: %PROJECT_PATH%

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in your PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Launch the enhanced Python launcher
echo Starting Enhanced Electric Vehicle Digital Twin...
python "%PROJECT_PATH%enhanced_ev_launcher.py"

REM If Python fails, show an error message
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error: Failed to start the Enhanced EV Digital Twin.
    echo.
    echo You can install the required packages with:
    echo pip install numpy pandas matplotlib scipy
    echo.
    pause
)

@echo off
REM All-in-One Launcher for the Electric Vehicle Digital Twin
REM This script provides an easy way to start both the simulation and web interface on Windows

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

REM Check for required packages
python -c "import numpy, pandas, matplotlib, scipy" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing required Python packages...
    python -m pip install numpy pandas matplotlib scipy
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install required packages.
        echo Please run the following command manually:
        echo pip install numpy pandas matplotlib scipy
        pause
        exit /b 1
    )
)

REM Launch the enhanced Python launcher
echo Starting Electric Vehicle Digital Twin...
start /B python "%PROJECT_PATH%enhanced_ev_launcher.py"

echo.
echo If the web interface doesn't open automatically, you can:
echo 1. Run start_web_interface.bat to open just the web interface
echo 2. Open http://localhost:8000 in your browser manually
echo.
echo Press any key to exit this window...
pause >nul

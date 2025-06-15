@echo off
REM Web Interface Launcher for the Electric Vehicle Digital Twin
REM This script provides an easy way to start the web interface on Windows

REM Set the project directory path
set PROJECT_PATH=%~dp0
echo Project path: %PROJECT_PATH%

REM Launch the Python web launcher
echo Starting Electric Vehicle Digital Twin Web Interface...
python "%PROJECT_PATH%web_interface_launcher.py"

REM If Python fails, show an error message
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error: Failed to start the EV Digital Twin Web Interface.
    echo Please make sure Python is installed and in your PATH.
    echo.
    echo You can install the required packages with:
    echo pip install numpy pandas matplotlib scipy
    echo.
    pause
)

# Electric Vehicle Digital Twin - Windows Installation and Usage Guide

## Overview

This document provides comprehensive instructions for installing and using the Electric Vehicle Digital Twin simulation on Windows systems. The simulation allows you to interactively control and visualize various aspects of an electric vehicle's performance in real-time.

## System Requirements

- Windows 10 or 11
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- 500MB free disk space
- Modern web browser (Chrome, Firefox, Edge)

## Installation Instructions

### Step 1: Install Python

1. Download Python from the official website: https://www.python.org/downloads/
2. Run the installer
3. **Important**: Check the box "Add Python to PATH" during installation
4. Complete the installation

### Step 2: Install Required Packages

Open Command Prompt and run:

```
pip install numpy pandas matplotlib scipy
```

### Step 3: Extract the Project Files

1. Extract the `ev_digital_twin_windows.zip` file to a location of your choice
2. Make note of the extraction location (e.g., `C:\Users\YourName\Documents\ev_digital_twin`)

## Running the Simulation

You have three options to run the Electric Vehicle Digital Twin:

### Option 1: All-in-One Launcher (Recommended)

1. Navigate to the extracted project folder
2. Double-click on `run_ev_digital_twin.bat`
3. The simulation and web interface will start automatically
4. Your default web browser will open with the web interface

### Option 2: Enhanced Launcher

1. Navigate to the extracted project folder
2. Double-click on `start_enhanced_ev_digital_twin.bat`
3. This launcher provides more detailed output and options

### Option 3: Web Interface Only

If you only want to access the web interface without starting a new simulation:

1. Navigate to the extracted project folder
2. Double-click on `start_web_interface.bat`
3. Your default web browser will open with the web interface

## Using the Simulation

### Web Interface

The web interface provides a comprehensive dashboard with multiple tabs:

1. **Simulation**: Main control panel for the simulation
   - Use the speed slider to control vehicle speed
   - Start, pause, and stop the simulation
   - Monitor real-time metrics

2. **Battery Details**: Detailed battery information
   - Cell-level monitoring
   - State of charge visualization
   - Temperature distribution

3. **Motor Details**: Motor performance metrics
   - Speed and torque visualization
   - Efficiency calculation
   - RUL (Remaining Useful Life) prediction

4. **Reports**: Generate and download reports
   - Multiple report formats (HTML, CSV, JSON, PDF)
   - Customizable report content
   - Download functionality

### Simulation Controls

The simulation can be controlled through:

1. **Speed Slider**: Adjust the target speed of the vehicle
2. **Start Button**: Begin the simulation
3. **Pause/Resume Button**: Temporarily halt or continue the simulation
4. **Stop Button**: End the simulation

### Data Export

Simulation results are automatically saved to:
- `real_time_simulation_results.csv` in the project directory

## Troubleshooting

### Web Interface Doesn't Open Automatically

If the web interface doesn't open automatically:
1. Open your web browser manually
2. Navigate to: http://localhost:8000

### Missing Python Packages

If you see errors about missing packages:
1. Open Command Prompt
2. Run: `pip install numpy pandas matplotlib scipy`

### Port Already in Use

If you see an error about port 8000 being in use:
1. Close any other instances of the simulation
2. Restart your computer if necessary
3. Try running the simulation again

### Python Not Found

If you see "Python is not installed or not in your PATH":
1. Reinstall Python, making sure to check "Add Python to PATH"
2. Restart your computer
3. Try running the simulation again

## Advanced Configuration

### Modifying Simulation Parameters

You can modify simulation parameters by editing the `enhanced_real_time_simulation.py` file:

- `battery_capacity`: Battery capacity in kWh
- `motor_power`: Motor power in kW
- `vehicle_mass`: Vehicle mass in kg
- And many other parameters

### Custom Web Server Port

To use a different port for the web server:
1. Open `enhanced_ev_launcher.py` in a text editor
2. Find the line: `port = 8000`
3. Change 8000 to your desired port number
4. Save the file

## Support

If you encounter any issues not covered in this guide, please contact support at support@evdigitaltwin.com

## License

This software is provided for educational and research purposes only.

#!/bin/bash

# Run the Electric Vehicle Digital Twin simulation
# This script sets up the Python path and launches the real-time simulation interface

# Add the project directory to Python path
export PYTHONPATH=$PYTHONPATH:/home/ubuntu/ev_digital_twin

# Launch the real-time simulation
python3 -c "from simulation.real_time_simulation import run_real_time_simulation; run_real_time_simulation()"

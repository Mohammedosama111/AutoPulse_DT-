# Electric Vehicle Digital Twin

A comprehensive digital twin simulation of an electric vehicle that models battery and motor behavior in real-time.

## Features

- **Battery Simulation**: Models voltage, current, capacity, and temperature dynamics
- **PMSM Motor Simulation**: Models torque, speed, and efficiency characteristics
- **Vehicle Dynamics**: Simulates vehicle speed, acceleration, and energy consumption
- **Real-time Interactive Interface**: Control the simulation with sliders and buttons
- **Data Export**: Export all simulation data to CSV files for analysis

## Installation

### Prerequisites

- Python 3.10+
- Required Python packages:
  - numpy
  - pandas
  - matplotlib
  - scipy

### Setup

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip3 install numpy pandas matplotlib scipy
```

## Usage

### Running the Interactive Simulation

The easiest way to run the simulation is using the provided shell script:

```bash
./run_simulation.sh
```

This will launch the interactive simulation interface where you can:
- Use the slider to control the target speed
- Use the buttons to start, pause/resume, and stop the simulation
- View real-time plots of vehicle speed, battery SOC, motor power, and distance traveled

### Programmatic Usage

You can also use the digital twin programmatically in your own Python code:

```python
from integration.ev_digital_twin import ElectricVehicleDigitalTwin

# Create EV digital twin with custom parameters
ev = ElectricVehicleDigitalTwin(
    battery_capacity=75.0,      # 75 kWh battery
    battery_nominal_voltage=400.0,  # 400V system
    motor_power=150.0,          # 150 kW motor
    motor_nominal_speed=8000.0, # 8000 rpm
    vehicle_mass=2000.0,        # 2000 kg
    wheel_radius=0.33,          # 33 cm
    gear_ratio=9.0,             # 9:1 gear ratio
    drag_coefficient=0.28,      # Aerodynamic drag coefficient
    frontal_area=2.3,           # 2.3 m²
    rolling_resistance=0.01     # Rolling resistance coefficient
)

# Define a custom speed profile
def speed_profile(t):
    if t < 10.0:
        return t * 3.0  # Accelerate to 30 m/s (108 km/h) in 10 seconds
    elif t < 50.0:
        return 30.0     # Cruise at 30 m/s for 40 seconds
    elif t < 60.0:
        return 30.0 - (t - 50.0) * 3.0  # Decelerate to 0 m/s in 10 seconds
    else:
        return 0.0      # Stop

# Run simulation
results = ev.simulate(speed_profile, duration=70.0, dt=1.0)

# Export results to CSV
ev.export_to_csv("ev_simulation_results.csv")

# Plot results
fig, axes = ev.plot_results()
```

## Project Structure

- `battery_model/`: Battery simulation components
- `motor_model/`: PMSM motor simulation components
- `integration/`: Integration of battery and motor models
- `simulation/`: Real-time simulation interface
- `documentation.md`: Comprehensive documentation
- `run_simulation.sh`: Script to run the interactive simulation

## Data Export

The simulation automatically exports all data to CSV files, including:

- Time (s)
- Vehicle speed (m/s), acceleration (m/s²), distance (m)
- Battery SOC, voltage (V), current (A), temperature (°C)
- Motor speed (rpm), torque (Nm), efficiency (%)
- Power demand (kW)

CSV files are saved in the project directory:
- `ev_simulation_results.csv` for programmatic simulations
- `real_time_simulation_results.csv` for interactive simulations

## Documentation

For detailed information about the implementation, architecture, and technical details, please refer to the [comprehensive documentation](documentation.md).

## License

This project is provided for educational and research purposes.

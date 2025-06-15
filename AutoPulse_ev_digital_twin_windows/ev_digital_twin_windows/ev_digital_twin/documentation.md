# Electric Vehicle Digital Twin Documentation

## Overview

This project implements a digital twin of an electric vehicle that simulates both battery behavior and motor behavior in real-time. The simulation integrates a battery model and a PMSM (Permanent Magnet Synchronous Motor) model to create a comprehensive electric vehicle simulation that tracks key parameters including:

- Battery: voltage, current, capacity, and temperature
- Motor: torque, speed, and efficiency
- Vehicle: speed, acceleration, distance, and power consumption

The digital twin provides both programmatic and interactive interfaces for simulation, with data export capabilities to CSV for further analysis.

## Architecture

The digital twin is structured in a modular architecture with the following components:

1. **Battery Model** - Simulates battery behavior using a physics-based approach
2. **Motor Model** - Simulates PMSM motor behavior with torque and speed control
3. **Integration Layer** - Connects the battery and motor models with vehicle dynamics
4. **Real-time Simulation Interface** - Provides interactive control and visualization

### Directory Structure

```
ev_digital_twin/
├── battery_model/
│   ├── battery_dfn_model.py        # Initial PyBaMM DFN implementation (not used)
│   └── simplified_battery_model.py # Simplified battery model implementation
├── motor_model/
│   ├── pmsm_motor_model.py         # Initial GYM motor implementation (not used)
│   └── simplified_pmsm_motor_model.py # Simplified PMSM motor model
├── integration/
│   └── ev_digital_twin.py          # Integration of battery and motor models
├── simulation/
│   └── real_time_simulation.py     # Real-time simulation interface
└── data_export/                    # Directory for exported simulation data
```

## Component Details

### Battery Model

The battery model simulates the behavior of a lithium-ion battery pack using a simplified physics-based approach. The model tracks:

- State of Charge (SOC)
- Terminal voltage
- Current
- Temperature

The model uses an ODE solver to simulate the battery dynamics, including:
- SOC dynamics through coulomb counting
- Temperature dynamics with joule heating and cooling
- Nonlinear voltage-SOC relationship

### Motor Model

The PMSM motor model simulates the behavior of a permanent magnet synchronous motor using a simplified physics-based approach. The model tracks:

- Speed (rpm)
- Torque (Nm)
- Three-phase currents and voltages
- Efficiency
- Power consumption/regeneration

The model uses an ODE solver to simulate the motor dynamics, including:
- Speed dynamics based on torque balance
- Current dynamics with field-oriented control
- Efficiency calculation based on losses

### Integration Layer

The integration layer connects the battery and motor models with vehicle dynamics to create a complete electric vehicle simulation. It handles:

- Energy flow between battery and motor
- Vehicle dynamics (speed, acceleration, distance)
- Resistive forces (rolling resistance, aerodynamic drag)
- Power demand calculation
- Mechanical coupling between motor and wheels

### Real-time Simulation Interface

The real-time simulation interface provides interactive control and visualization of the EV digital twin. It features:

- Interactive speed control via slider
- Simulation control buttons (start, pause/resume, stop)
- Real-time plotting of key parameters
- Data export to CSV

## Usage Instructions

### Basic Programmatic Usage

```python
from integration.ev_digital_twin import ElectricVehicleDigitalTwin

# Create EV digital twin
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

# Define a speed profile
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

### Interactive Simulation

```python
from simulation.real_time_simulation import RealTimeEVSimulation
from integration.ev_digital_twin import ElectricVehicleDigitalTwin

# Create EV model
ev = ElectricVehicleDigitalTwin(
    battery_capacity=75.0,
    battery_nominal_voltage=400.0,
    motor_power=150.0,
    motor_nominal_speed=8000.0,
    vehicle_mass=2000.0,
    wheel_radius=0.33,
    gear_ratio=9.0,
    drag_coefficient=0.28,
    frontal_area=2.3,
    rolling_resistance=0.01
)

# Create real-time simulation interface
sim = RealTimeEVSimulation(ev)

# Run interactive simulation
sim.run_interactive_simulation()

# Export results
sim.export_to_csv("real_time_simulation_results.csv")
```

## Simulation Parameters

### Battery Parameters

- `capacity`: Battery capacity in Ah
- `nominal_voltage`: Nominal battery voltage in V
- `initial_soc`: Initial state of charge (0.0 to 1.0)

### Motor Parameters

- `nominal_power`: Nominal motor power in kW
- `nominal_speed`: Nominal motor speed in rpm
- `nominal_voltage`: Nominal motor voltage in V

### Vehicle Parameters

- `vehicle_mass`: Vehicle mass in kg
- `wheel_radius`: Wheel radius in m
- `gear_ratio`: Gear ratio between motor and wheels
- `drag_coefficient`: Aerodynamic drag coefficient
- `frontal_area`: Vehicle frontal area in m²
- `rolling_resistance`: Rolling resistance coefficient

## Simulation Outputs

The simulation produces the following outputs:

### Vehicle Dynamics
- Time (s)
- Speed (m/s)
- Acceleration (m/s²)
- Distance (m)
- Power Demand (kW)

### Battery State
- Battery SOC
- Battery Voltage (V)
- Battery Current (A)
- Battery Temperature (°C)

### Motor State
- Motor Speed (rpm)
- Motor Torque (Nm)
- Motor Efficiency (%)

## Implementation Notes

### PyBaMM and GYM Electric Motor Integration

The initial implementation attempted to use PyBaMM for the battery model with the DFN (Doyle-Fuller-Newman) approach and the GYM Electric Motor library for the PMSM motor simulation. However, both libraries presented integration challenges:

1. **PyBaMM DFN Model**: Encountered solver convergence issues with the complex electrochemical model. A simplified battery model was implemented instead using scipy's ODE solver.

2. **GYM Electric Motor**: Encountered parameter compatibility issues with the reference generator. A simplified PMSM motor model was implemented instead using physics-based equations and scipy's ODE solver.

The simplified models maintain the key features required for the digital twin while providing better numerical stability and integration capabilities.

## Future Enhancements

Potential future enhancements to the digital twin include:

1. **Advanced Battery Models**: Integration with more sophisticated battery models that capture aging effects and thermal dynamics.

2. **Detailed Motor Models**: Enhanced motor models with thermal effects and more detailed loss calculations.

3. **Drive Cycle Library**: Pre-defined standard drive cycles (WLTP, NEDC, etc.) for comparative testing.

4. **3D Visualization**: 3D rendering of the vehicle with real-time state visualization.

5. **Fault Simulation**: Capability to simulate various fault conditions in the battery and motor systems.

6. **Machine Learning Integration**: Predictive models for range estimation and component degradation.

## Conclusion

This electric vehicle digital twin provides a comprehensive simulation platform for studying the behavior of electric vehicles under various operating conditions. The modular architecture allows for easy extension and modification of individual components, while the real-time simulation interface enables interactive exploration of the vehicle's performance characteristics.

"""
Enhanced Integration of Battery and Motor Models for Electric Vehicle Digital Twin
---------------------------------------------------------------------------------
This module integrates the enhanced battery and motor models with time tracking in minutes.
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
from datetime import timedelta
from battery_model.enhanced_battery_model import EnhancedBatteryModel
from motor_model.enhanced_motor_model import EnhancedPMSMMotorModel


class EnhancedElectricVehicleDigitalTwin:
    """
    Enhanced digital twin of an electric vehicle that integrates battery and motor models.
    
    This class provides methods to:
    - Initialize an EV model with custom battery and motor parameters
    - Simulate EV behavior with various driving profiles
    - Track all relevant parameters including time in minutes and seconds
    - Calculate energy consumption and efficiency
    - Export simulation results to CSV
    - Generate reports on vehicle performance and component health
    """
    
    def __init__(self, battery_capacity=75.0, battery_nominal_voltage=400.0, 
                 motor_power=150.0, motor_nominal_speed=8000.0, vehicle_mass=2000.0,
                 wheel_radius=0.33, gear_ratio=9.0, drag_coefficient=0.28, 
                 frontal_area=2.3, rolling_resistance=0.01):
        """
        Initialize the electric vehicle digital twin.
        
        Args:
            battery_capacity (float): Battery capacity in Ah
            battery_nominal_voltage (float): Nominal battery voltage in V
            motor_power (float): Motor power in kW
            motor_nominal_speed (float): Motor nominal speed in rpm
            vehicle_mass (float): Vehicle mass in kg
            wheel_radius (float): Wheel radius in m
            gear_ratio (float): Gear ratio between motor and wheels
            drag_coefficient (float): Aerodynamic drag coefficient
            frontal_area (float): Vehicle frontal area in m²
            rolling_resistance (float): Rolling resistance coefficient
        """
        # Initialize battery model
        self.battery = EnhancedBatteryModel(
            initial_soc=0.9,
            capacity=battery_capacity,
            nominal_voltage=battery_nominal_voltage,
            num_cells_series=96,
            num_cells_parallel=4,
            initial_soh=0.95
        )
        
        # Initialize motor model
        self.motor = EnhancedPMSMMotorModel(
            nominal_power=motor_power,
            nominal_speed=motor_nominal_speed,
            nominal_voltage=battery_nominal_voltage,
            motor_type="PMSM",
            pole_pairs=4,
            initial_health=0.95
        )
        
        # Store vehicle parameters
        self.vehicle_mass = vehicle_mass  # kg
        self.wheel_radius = wheel_radius  # m
        self.gear_ratio = gear_ratio
        self.drag_coefficient = drag_coefficient
        self.frontal_area = frontal_area  # m²
        self.rolling_resistance = rolling_resistance
        
        # Current state
        self.current_speed = 0.0  # m/s
        self.current_acceleration = 0.0  # m/s²
        self.current_distance = 0.0  # m
        self.current_power_demand = 0.0  # kW
        self.current_energy_consumption = 0.0  # kWh
        self.current_energy_efficiency = 0.0  # kWh/km
        
        # Time tracking
        self.current_time_seconds = 0.0  # s
        self.current_time_minutes = 0.0  # min
        self.current_time_formatted = "00:00"  # mm:ss
        
        # Simulation results
        self.time_data = []  # s
        self.time_minutes_data = []  # min
        self.time_formatted_data = []  # mm:ss
        self.speed_data = []  # m/s
        self.acceleration_data = []  # m/s²
        self.distance_data = []  # m
        self.power_demand_data = []  # kW
        self.energy_consumption_data = []  # kWh
        self.energy_efficiency_data = []  # kWh/km
        
        # Battery data
        self.battery_soc_data = []
        self.battery_voltage_data = []
        self.battery_current_data = []
        self.battery_temperature_data = []
        self.battery_soh_data = []
        self.battery_rul_data = []
        
        # Motor data
        self.motor_speed_data = []  # rpm
        self.motor_torque_data = []  # Nm
        self.motor_efficiency_data = []
        self.motor_temperature_data = []
        self.motor_health_data = []
        self.motor_rul_data = []
        
        print(f"Enhanced Electric Vehicle Digital Twin initialized with {battery_capacity} Ah battery and {motor_power} kW motor")
    
    def _format_time(self, seconds):
        """
        Format time in seconds to mm:ss format.
        
        Args:
            seconds (float): Time in seconds
        
        Returns:
            str: Formatted time string (mm:ss)
        """
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes:02d}:{remaining_seconds:02d}"
    
    def _calculate_resistive_forces(self, speed):
        """
        Calculate resistive forces acting on the vehicle.
        
        Args:
            speed (float): Vehicle speed in m/s
        
        Returns:
            float: Total resistive force in N
        """
        # Rolling resistance
        f_rolling = self.rolling_resistance * self.vehicle_mass * 9.81  # N
        
        # Aerodynamic drag
        air_density = 1.225  # kg/m³
        f_drag = 0.5 * air_density * self.drag_coefficient * self.frontal_area * speed**2  # N
        
        # Total resistive force
        return f_rolling + f_drag
    
    def _calculate_power_demand(self, speed, acceleration):
        """
        Calculate power demand based on vehicle dynamics.
        
        Args:
            speed (float): Vehicle speed in m/s
            acceleration (float): Vehicle acceleration in m/s²
        
        Returns:
            float: Power demand in kW (positive for propulsion, negative for regeneration)
        """
        # Resistive force
        f_resistive = self._calculate_resistive_forces(speed)
        
        # Acceleration force
        f_acceleration = self.vehicle_mass * acceleration  # N
        
        # Total force
        f_total = f_resistive + f_acceleration  # N
        
        # Power demand (W)
        power_demand = f_total * speed  # W
        
        # Convert to kW
        return power_demand / 1000
    
    def _calculate_motor_torque(self, power_demand, motor_speed):
        """
        Calculate motor torque based on power demand and motor speed.
        
        Args:
            power_demand (float): Power demand in kW
            motor_speed (float): Motor speed in rpm
        
        Returns:
            float: Motor torque in Nm
        """
        # Convert power from kW to W
        power_w = power_demand * 1000
        
        # Convert motor speed from rpm to rad/s
        motor_speed_rad_s = motor_speed * 2 * np.pi / 60
        
        # Calculate torque (T = P / ω)
        if abs(motor_speed_rad_s) < 1e-6:
            # Avoid division by zero
            return 0.0
        
        return power_w / motor_speed_rad_s
    
    def _calculate_wheel_torque(self, motor_torque):
        """
        Calculate wheel torque based on motor torque and gear ratio.
        
        Args:
            motor_torque (float): Motor torque in Nm
        
        Returns:
            float: Wheel torque in Nm
        """
        return motor_torque * self.gear_ratio
    
    def _calculate_acceleration(self, wheel_torque, speed):
        """
        Calculate vehicle acceleration based on wheel torque and current speed.
        
        Args:
            wheel_torque (float): Wheel torque in Nm
            speed (float): Current speed in m/s
        
        Returns:
            float: Acceleration in m/s²
        """
        # Calculate resistive force
        f_resistive = self._calculate_resistive_forces(speed)
        
        # Calculate tractive force from wheel torque
        f_tractive = wheel_torque / self.wheel_radius  # N
        
        # Calculate net force
        f_net = f_tractive - f_resistive  # N
        
        # Calculate acceleration (F = m * a)
        return f_net / self.vehicle_mass
    
    def _update_energy_consumption(self, power_demand, dt):
        """
        Update energy consumption based on power demand.
        
        Args:
            power_demand (float): Power demand in kW
            dt (float): Time step in seconds
        """
        # Convert power (kW) to energy (kWh) for this time step
        energy_step = power_demand * dt / 3600  # kWh
        
        # Update total energy consumption (only count positive power demands)
        if power_demand > 0:
            self.current_energy_consumption += energy_step
        
        # Update energy efficiency (kWh/km)
        distance_km = self.current_distance / 1000
        if distance_km > 0.001:  # Avoid division by very small numbers
            self.current_energy_efficiency = self.current_energy_consumption / distance_km
        else:
            self.current_energy_efficiency = 0.0
    
    def simulate(self, speed_profile, duration, dt=0.1):
        """
        Simulate the electric vehicle with a given speed profile.
        
        Args:
            speed_profile (callable): Function that returns target speed at time t
            duration (float): Simulation duration in seconds
            dt (float): Time step in seconds
        
        Returns:
            dict: Dictionary containing simulation results
        """
        # Reset simulation data arrays
        self.time_data = []
        self.time_minutes_data = []
        self.time_formatted_data = []
        self.speed_data = []
        self.acceleration_data = []
        self.distance_data = []
        self.power_demand_data = []
        self.energy_consumption_data = []
        self.energy_efficiency_data = []
        
        self.battery_soc_data = []
        self.battery_voltage_data = []
        self.battery_current_data = []
        self.battery_temperature_data = []
        self.battery_soh_data = []
        self.battery_rul_data = []
        
        self.motor_speed_data = []
        self.motor_torque_data = []
        self.motor_efficiency_data = []
        self.motor_temperature_data = []
        self.motor_health_data = []
        self.motor_rul_data = []
        
        # Reset current state
        self.current_speed = 0.0
        self.current_acceleration = 0.0
        self.current_distance = 0.0
        self.current_power_demand = 0.0
        self.current_energy_consumption = 0.0
        self.current_energy_efficiency = 0.0
        self.current_time_seconds = 0.0
        self.current_time_minutes = 0.0
        self.current_time_formatted = "00:00"
        
        # Simulation loop
        t = 0.0
        while t < duration:
            # Get target speed from profile
            target_speed = speed_profile(t)
            
            # Simple speed controller (proportional control)
            speed_error = target_speed - self.current_speed
            kp = 0.5  # Proportional gain
            self.current_acceleration = np.clip(kp * speed_error, -5.0, 5.0)  # Limit acceleration
            
            # Update speed
            self.current_speed = max(0.0, self.current_speed + self.current_acceleration * dt)
            
            # Update distance
            self.current_distance += self.current_speed * dt
            
            # Calculate power demand
            self.current_power_demand = self._calculate_power_demand(self.current_speed, self.current_acceleration)
            
            # Calculate motor speed (rpm) from vehicle speed
            motor_speed = self.current_speed / (2 * np.pi * self.wheel_radius) * 60 * self.gear_ratio
            
            # Calculate motor torque
            motor_torque = self._calculate_motor_torque(self.current_power_demand, motor_speed)
            
            # Update battery state based on power demand
            # Create a power profile for the battery
            def battery_power_profile(t_local):
                return self.current_power_demand
            
            # Simulate battery for this time step
            battery_results = self.battery.apply_drive_cycle(battery_power_profile, dt, dt)
            
            # Update motor state based on torque and speed
            # Create a torque profile for the motor
            def motor_torque_profile(t_local):
                return motor_torque
            
            # Simulate motor for this time step
            motor_results = self.motor.simulate(motor_torque_profile, dt, dt)
            
            # Update energy consumption
            self._update_energy_consumption(self.current_power_demand, dt)
            
            # Update time tracking
            self.current_time_seconds = t
            self.current_time_minutes = t / 60
            self.current_time_formatted = self._format_time(t)
            
            # Store data
            self.time_data.append(t)
            self.time_minutes_data.append(t / 60)
            self.time_formatted_data.append(self.current_time_formatted)
            self.speed_data.append(self.current_speed)
            self.acceleration_data.append(self.current_acceleration)
            self.distance_data.append(self.current_distance)
            self.power_demand_data.append(self.current_power_demand)
            self.energy_consumption_data.append(self.current_energy_consumption)
            self.energy_efficiency_data.append(self.current_energy_efficiency)
            
            # Store battery data
            battery_state = self.battery.get_state()
            self.battery_soc_data.append(battery_state["soc"])
            self.battery_voltage_data.append(battery_state["voltage"])
            self.battery_current_data.append(self.current_power_demand * 1000 / battery_state["voltage"] if battery_state["voltage"] > 0 else 0)
            self.battery_temperature_data.append(battery_state["temperature"])
            self.battery_soh_data.append(battery_state["soh"])
            self.battery_rul_data.append(battery_state["rul_cycles"])
            
            # Store motor data
            motor_state = self.motor.get_state()
            self.motor_speed_data.append(motor_state["speed"])
            self.motor_torque_data.append(motor_state["torque"])
            self.motor_efficiency_data.append(motor_state["efficiency"])
            self.motor_temperature_data.append(motor_state["temperature"])
            self.motor_health_data.append(motor_state["health"])
            self.motor_rul_data.append(motor_state["rul_hours"])
            
            # Increment time
            t += dt
        
        # Convert lists to numpy arrays
        self.time_data = np.array(self.time_data)
        self.time_minutes_data = np.array(self.time_minutes_data)
        self.speed_data = np.array(self.speed_data)
        self.acceleration_data = np.array(self.acceleration_data)
        self.distance_data = np.array(self.distance_data)
        self.power_demand_data = np.array(self.power_demand_data)
        self.energy_consumption_data = np.array(self.energy_consumption_data)
        self.energy_efficiency_data = np.array(self.energy_efficiency_data)
        
        self.battery_soc_data = np.array(self.battery_soc_data)
        self.battery_voltage_data = np.array(self.battery_voltage_data)
        self.battery_current_data = np.array(self.battery_current_data)
        self.battery_temperature_data = np.array(self.battery_temperature_data)
        self.battery_soh_data = np.array(self.battery_soh_data)
        self.battery_rul_data = np.array(self.battery_rul_data)
        
        self.motor_speed_data = np.array(self.motor_speed_data)
        self.motor_torque_data = np.array(self.motor_torque_data)
        self.motor_efficiency_data = np.array(self.motor_efficiency_data)
        self.motor_temperature_data = np.array(self.motor_temperature_data)
        self.motor_health_data = np.array(self.motor_health_data)
        self.motor_rul_data = np.array(self.motor_rul_data)
        
        # Return results
        return {
            "time": self.time_data,
            "time_minutes": self.time_minutes_data,
            "time_formatted": self.time_formatted_data,
            "speed": self.speed_data,
            "acceleration": self.acceleration_data,
            "distance": self.distance_data,
            "power_demand": self.power_demand_data,
            "energy_consumption": self.energy_consumption_data,
            "energy_efficiency": self.energy_efficiency_data,
            "battery_soc": self.battery_soc_data,
            "battery_voltage": self.battery_voltage_data,
            "battery_current": self.battery_current_data,
            "battery_temperature": self.battery_temperature_data,
            "battery_soh": self.battery_soh_data,
            "battery_rul": self.battery_rul_data,
            "motor_speed": self.motor_speed_data,
            "motor_torque": self.motor_torque_data,
            "motor_efficiency": self.motor_efficiency_data,
            "motor_temperature": self.motor_temperature_data,
            "motor_health": self.motor_health_data,
            "motor_rul": self.motor_rul_data
        }
    
    def export_to_csv(self, filename="enhanced_ev_simulation_results.csv"):
        """
        Export simulation results to CSV file.
        
        Args:
            filename (str): Output CSV filename
        """
        if len(self.time_data) == 0:
            raise ValueError("No simulation results to export. Run a simulation first.")
        
        # Create DataFrame
        data = {
            "Time (s)": self.time_data,
            "Time (min)": self.time_minutes_data,
            "Time (mm:ss)": self.time_formatted_data,
            "Speed (m/s)": self.speed_data,
            "Speed (km/h)": self.speed_data * 3.6,
            "Acceleration (m/s²)": self.acceleration_data,
            "Distance (m)": self.distance_data,
            "Distance (km)": self.distance_data / 1000,
            "Power Demand (kW)": self.power_demand_data,
            "Energy Consumption (kWh)": self.energy_consumption_data,
            "Energy Efficiency (kWh/km)": self.energy_efficiency_data,
            "Battery SOC": self.battery_soc_data,
            "Battery Voltage (V)": self.battery_voltage_data,
            "Battery Current (A)": self.battery_current_data,
            "Battery Temperature (°C)": self.battery_temperature_data - 273.15,
            "Battery SOH": self.battery_soh_data,
            "Battery RUL (cycles)": self.battery_rul_data,
            "Motor Speed (rpm)": self.motor_speed_data,
            "Motor Torque (Nm)": self.motor_torque_data,
            "Motor Efficiency": self.motor_efficiency_data,
            "Motor Temperature (°C)": self.motor_temperature_data - 273.15,
            "Motor Health": self.motor_health_data,
            "Motor RUL (hours)": self.motor_rul_data
        }
        
        df = pd.DataFrame(data)
        
        # Save to CSV
        df.to_csv(filename, index=False)
        
        print(f"Simulation results exported to {filename}")
    
    def generate_report(self, filename="ev_simulation_report.md"):
        """
        Generate a comprehensive report of the simulation results.
        
        Args:
            filename (str): Output report filename
        """
        if len(self.time_data) == 0:
            raise ValueError("No simulation results to report. Run a simulation first.")
        
        # Calculate summary statistics
        duration_seconds = self.time_data[-1]
        duration_formatted = self._format_time(duration_seconds)
        max_speed = np.max(self.speed_data)
        avg_speed = np.mean(self.speed_data)
        max_acceleration = np.max(self.acceleration_data)
        max_deceleration = np.min(self.acceleration_data)
        total_distance = self.distance_data[-1]
        max_power = np.max(self.power_demand_data)
        avg_power = np.mean(self.power_demand_data[self.power_demand_data > 0])
        total_energy = self.energy_consumption_data[-1]
        avg_efficiency = total_energy / (total_distance / 1000) if total_distance > 0 else 0
        
        initial_soc = self.battery_soc_data[0]
        final_soc = self.battery_soc_data[-1]
        soc_change = initial_soc - final_soc
        
        max_motor_speed = np.max(self.motor_speed_data)
        max_motor_torque = np.max(self.motor_torque_data)
        avg_motor_efficiency = np.mean(self.motor_efficiency_data)
        
        # Get battery and motor state
        battery_state = self.battery.get_state()
        motor_state = self.motor.get_state()
        
        # Create report
        report = f"""# Electric Vehicle Simulation Report

## Simulation Overview

- **Duration**: {duration_seconds:.1f} seconds ({duration_formatted})
- **Distance Traveled**: {total_distance:.2f} m ({total_distance/1000:.2f} km)
- **Energy Consumed**: {total_energy:.2f} kWh
- **Energy Efficiency**: {avg_efficiency:.2f} kWh/km

## Vehicle Performance

### Speed and Acceleration

- **Maximum Speed**: {max_speed:.2f} m/s ({max_speed*3.6:.2f} km/h)
- **Average Speed**: {avg_speed:.2f} m/s ({avg_speed*3.6:.2f} km/h)
- **Maximum Acceleration**: {max_acceleration:.2f} m/s²
- **Maximum Deceleration**: {max_deceleration:.2f} m/s²

### Power and Energy

- **Maximum Power Demand**: {max_power:.2f} kW
- **Average Power Demand**: {avg_power:.2f} kW

## Battery Status

### State of Charge

- **Initial SOC**: {initial_soc*100:.1f}%
- **Final SOC**: {final_soc*100:.1f}%
- **SOC Change**: {soc_change*100:.1f}%

### Battery Health

- **State of Health**: {battery_state["soh"]*100:.1f}%
- **Remaining Useful Life**: {battery_state["rul_cycles"]:.1f} cycles
- **Cell Configuration**: {battery_state["cell_config"]} ({battery_state["total_cells"]} cells)
- **Temperature Range**: {min(self.battery_temperature_data)-273.15:.1f}°C to {max(self.battery_temperature_data)-273.15:.1f}°C

## Motor Status

### Performance

- **Maximum Speed**: {max_motor_speed:.1f} rpm
- **Maximum Torque**: {max_motor_torque:.1f} Nm
- **Average Efficiency**: {avg_motor_efficiency*100:.1f}%

### Motor Health

- **Health Status**: {motor_state["health"]*100:.1f}%
- **Remaining Useful Life**: {motor_state["rul_hours"]:.1f} hours
- **Temperature Range**: {min(self.motor_temperature_data)-273.15:.1f}°C to {max(self.motor_temperature_data)-273.15:.1f}°C

## Vehicle Specifications

- **Vehicle Mass**: {self.vehicle_mass} kg
- **Wheel Radius**: {self.wheel_radius} m
- **Gear Ratio**: {self.gear_ratio}
- **Drag Coefficient**: {self.drag_coefficient}
- **Frontal Area**: {self.frontal_area} m²
- **Rolling Resistance**: {self.rolling_resistance}

## Battery Specifications

- **Capacity**: {battery_state["capacity"]} Ah
- **Nominal Voltage**: {self.battery.nominal_voltage} V
- **Cell Configuration**: {battery_state["cell_config"]}

## Motor Specifications

- **Type**: {motor_state["motor_type"]}
- **Nominal Power**: {motor_state["nominal_power"]} kW
- **Nominal Speed**: {motor_state["nominal_speed"]} rpm
- **Nominal Torque**: {motor_state["nominal_torque"]:.1f} Nm
- **Pole Pairs**: {motor_state["pole_pairs"]}

## Simulation Timestamp

- **Generated**: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        # Write report to file
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"Simulation report generated: {filename}")
        
        return report
    
    def plot_results(self):
        """
        Plot the simulation results.
        
        Returns:
            tuple: Matplotlib figure and axes objects
        """
        if len(self.time_data) == 0:
            raise ValueError("No simulation results to plot. Run a simulation first.")
        
        # Create figure with subplots
        fig, axes = plt.subplots(4, 2, figsize=(15, 20))
        
        # Plot vehicle speed
        axes[0, 0].plot(self.time_minutes_data, self.speed_data * 3.6)  # Convert to km/h
        axes[0, 0].set_xlabel("Time [min]")
        axes[0, 0].set_ylabel("Speed [km/h]")
        axes[0, 0].set_title("Vehicle Speed")
        axes[0, 0].grid(True)
        
        # Plot battery SOC
        axes[0, 1].plot(self.time_minutes_data, self.battery_soc_data * 100)  # Convert to percentage
        axes[0, 1].set_xlabel("Time [min]")
        axes[0, 1].set_ylabel("SOC [%]")
        axes[0, 1].set_title("Battery State of Charge")
        axes[0, 1].grid(True)
        
        # Plot power demand
        axes[1, 0].plot(self.time_minutes_data, self.power_demand_data)
        axes[1, 0].set_xlabel("Time [min]")
        axes[1, 0].set_ylabel("Power [kW]")
        axes[1, 0].set_title("Power Demand")
        axes[1, 0].grid(True)
        
        # Plot motor torque
        axes[1, 1].plot(self.time_minutes_data, self.motor_torque_data)
        axes[1, 1].set_xlabel("Time [min]")
        axes[1, 1].set_ylabel("Torque [Nm]")
        axes[1, 1].set_title("Motor Torque")
        axes[1, 1].grid(True)
        
        # Plot temperatures
        axes[2, 0].plot(self.time_minutes_data, self.battery_temperature_data - 273.15, label="Battery")
        axes[2, 0].plot(self.time_minutes_data, self.motor_temperature_data - 273.15, label="Motor")
        axes[2, 0].set_xlabel("Time [min]")
        axes[2, 0].set_ylabel("Temperature [°C]")
        axes[2, 0].set_title("Component Temperatures")
        axes[2, 0].legend()
        axes[2, 0].grid(True)
        
        # Plot energy consumption
        axes[2, 1].plot(self.time_minutes_data, self.energy_consumption_data)
        axes[2, 1].set_xlabel("Time [min]")
        axes[2, 1].set_ylabel("Energy [kWh]")
        axes[2, 1].set_title("Cumulative Energy Consumption")
        axes[2, 1].grid(True)
        
        # Plot component health
        axes[3, 0].plot(self.time_minutes_data, self.battery_soh_data * 100, label="Battery SOH")
        axes[3, 0].plot(self.time_minutes_data, self.motor_health_data * 100, label="Motor Health")
        axes[3, 0].set_xlabel("Time [min]")
        axes[3, 0].set_ylabel("Health [%]")
        axes[3, 0].set_title("Component Health")
        axes[3, 0].legend()
        axes[3, 0].grid(True)
        
        # Plot RUL
        ax1 = axes[3, 1]
        ax2 = ax1.twinx()
        
        ax1.plot(self.time_minutes_data, self.battery_rul_data, 'b-', label='Battery RUL (cycles)')
        ax1.set_xlabel("Time [min]")
        ax1.set_ylabel("Battery RUL [cycles]", color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        
        ax2.plot(self.time_minutes_data, self.motor_rul_data, 'r-', label='Motor RUL (hours)')
        ax2.set_ylabel("Motor RUL [hours]", color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        
        axes[3, 1].set_title("Remaining Useful Life")
        axes[3, 1].grid(True)
        
        # Add lines for both legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        axes[3, 1].legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        plt.tight_layout()
        return fig, axes


def test_enhanced_ev_digital_twin():
    """
    Test function to demonstrate the enhanced EV digital twin functionality.
    """
    # Create EV digital twin
    ev = EnhancedElectricVehicleDigitalTwin(
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
    
    # Create a speed profile
    def speed_profile(t):
        t_minutes = t / 60
        if t_minutes < 2:  # Acceleration
            return t_minutes * 15  # 0 to 30 m/s in 2 minutes
        elif t_minutes < 10:  # Cruising
            return 30.0  # Cruise at 30 m/s (108 km/h)
        elif t_minutes < 12:  # Deceleration
            return 30.0 - (t_minutes - 10) * 15  # 30 to 0 m/s in 2 minutes
        else:  # Stopped
            return 0.0
    
    # Run simulation
    print("Running enhanced EV simulation...")
    results = ev.simulate(speed_profile, duration=15*60, dt=1.0)  # 15 minutes
    
    # Export results to CSV
    ev.export_to_csv("enhanced_ev_simulation_results.csv")
    
    # Generate report
    ev.generate_report("enhanced_ev_simulation_report.md")
    
    # Plot results
    fig, axes = ev.plot_results()
    plt.savefig("enhanced_ev_simulation_results.png")
    plt.close(fig)
    
    # Print summary
    print(f"Simulation completed for {results['time'][-1]:.1f} seconds ({results['time_formatted'][-1]})")
    print(f"Final distance: {results['distance'][-1]/1000:.2f} km")
    print(f"Final battery SOC: {results['battery_soc'][-1]*100:.2f}%")
    print(f"Energy consumption: {results['energy_consumption'][-1]:.2f} kWh")
    print(f"Energy efficiency: {results['energy_efficiency'][-1]:.2f} kWh/km")
    print(f"Battery RUL: {results['battery_rul'][-1]:.1f} cycles")
    print(f"Motor RUL: {results['motor_rul'][-1]:.1f} hours")
    
    return ev


if __name__ == "__main__":
    test_enhanced_ev_digital_twin()

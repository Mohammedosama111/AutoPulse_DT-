"""
Electric Vehicle Digital Twin
----------------------------
This module integrates the battery and motor models to create a complete
electric vehicle digital twin that simulates the behavior of an electric vehicle.
"""

import numpy as np
import matplotlib.pyplot as plt
from battery_model.simplified_battery_model import SimplifiedBatteryModel
from motor_model.simplified_pmsm_motor_model import SimplifiedPMSMMotorModel


class ElectricVehicleDigitalTwin:
    """
    Electric Vehicle Digital Twin that integrates battery and motor models.
    
    This class provides methods to:
    - Initialize an EV digital twin with custom parameters
    - Simulate EV behavior under different driving conditions
    - Track battery and motor states
    - Export simulation data for analysis
    """
    
    def __init__(self, 
                 battery_capacity=50.0,
                 battery_nominal_voltage=400.0,
                 motor_power=100.0,
                 motor_nominal_speed=4000.0,
                 vehicle_mass=1500.0,
                 wheel_radius=0.3,
                 gear_ratio=10.0,
                 drag_coefficient=0.3,
                 frontal_area=2.0,
                 rolling_resistance=0.01):
        """
        Initialize the EV digital twin with parameters.
        
        Args:
            battery_capacity (float): Battery capacity in Ah
            battery_nominal_voltage (float): Battery nominal voltage in V
            motor_power (float): Motor nominal power in kW
            motor_nominal_speed (float): Motor nominal speed in rpm
            vehicle_mass (float): Vehicle mass in kg
            wheel_radius (float): Wheel radius in m
            gear_ratio (float): Gear ratio between motor and wheels
            drag_coefficient (float): Aerodynamic drag coefficient
            frontal_area (float): Vehicle frontal area in m²
            rolling_resistance (float): Rolling resistance coefficient
        """
        # Store vehicle parameters
        self.vehicle_mass = vehicle_mass  # kg
        self.wheel_radius = wheel_radius  # m
        self.gear_ratio = gear_ratio  # ratio
        self.drag_coefficient = drag_coefficient  # dimensionless
        self.frontal_area = frontal_area  # m²
        self.rolling_resistance = rolling_resistance  # dimensionless
        self.air_density = 1.225  # kg/m³
        self.gravity = 9.81  # m/s²
        
        # Initialize battery model
        self.battery = SimplifiedBatteryModel(
            initial_soc=0.9,
            capacity=battery_capacity,
            nominal_voltage=battery_nominal_voltage
        )
        
        # Initialize motor model
        self.motor = SimplifiedPMSMMotorModel(
            nominal_power=motor_power,
            nominal_speed=motor_nominal_speed,
            nominal_voltage=battery_nominal_voltage
        )
        
        # Initialize vehicle state
        self.current_speed = 0.0  # m/s
        self.current_acceleration = 0.0  # m/s²
        self.current_distance = 0.0  # m
        self.current_power_demand = 0.0  # kW
        
        # Store simulation data
        self.time_data = []
        self.speed_data = []
        self.acceleration_data = []
        self.distance_data = []
        self.power_demand_data = []
        self.battery_soc_data = []
        self.battery_voltage_data = []
        self.battery_current_data = []
        self.battery_temperature_data = []
        self.motor_speed_data = []
        self.motor_torque_data = []
        self.motor_efficiency_data = []
        
        print(f"Electric Vehicle Digital Twin initialized with {battery_capacity} Ah battery and {motor_power} kW motor")
    
    def _calculate_resistive_forces(self, speed):
        """
        Calculate resistive forces acting on the vehicle.
        
        Args:
            speed (float): Vehicle speed in m/s
        
        Returns:
            float: Total resistive force in N
        """
        # Rolling resistance
        f_rolling = self.rolling_resistance * self.vehicle_mass * self.gravity
        
        # Aerodynamic drag
        f_drag = 0.5 * self.air_density * self.drag_coefficient * self.frontal_area * speed**2
        
        # Total resistive force
        return f_rolling + f_drag
    
    def _speed_to_motor_rpm(self, speed):
        """
        Convert vehicle speed to motor rpm.
        
        Args:
            speed (float): Vehicle speed in m/s
        
        Returns:
            float: Motor speed in rpm
        """
        # wheel_rpm = speed / (2 * pi * wheel_radius) * 60
        # motor_rpm = wheel_rpm * gear_ratio
        return speed / (2 * np.pi * self.wheel_radius) * 60 * self.gear_ratio
    
    def _motor_rpm_to_speed(self, motor_rpm):
        """
        Convert motor rpm to vehicle speed.
        
        Args:
            motor_rpm (float): Motor speed in rpm
        
        Returns:
            float: Vehicle speed in m/s
        """
        # wheel_rpm = motor_rpm / gear_ratio
        # speed = wheel_rpm * 2 * pi * wheel_radius / 60
        return motor_rpm / self.gear_ratio * 2 * np.pi * self.wheel_radius / 60
    
    def _torque_to_force(self, torque):
        """
        Convert motor torque to tractive force at wheels.
        
        Args:
            torque (float): Motor torque in Nm
        
        Returns:
            float: Tractive force in N
        """
        # F = T * gear_ratio / wheel_radius
        return torque * self.gear_ratio / self.wheel_radius
    
    def _force_to_torque(self, force):
        """
        Convert tractive force to motor torque.
        
        Args:
            force (float): Tractive force in N
        
        Returns:
            float: Motor torque in Nm
        """
        # T = F * wheel_radius / gear_ratio
        return force * self.wheel_radius / self.gear_ratio
    
    def _calculate_power_demand(self, speed, acceleration):
        """
        Calculate power demand based on vehicle dynamics.
        
        Args:
            speed (float): Vehicle speed in m/s
            acceleration (float): Vehicle acceleration in m/s²
        
        Returns:
            float: Power demand in kW
        """
        # Calculate resistive forces
        f_resistive = self._calculate_resistive_forces(speed)
        
        # Calculate acceleration force
        f_acceleration = self.vehicle_mass * acceleration
        
        # Total force
        f_total = f_resistive + f_acceleration
        
        # Power = Force * Speed
        power = f_total * speed  # W
        
        # Convert to kW
        return power / 1000
    
    def _update_vehicle_state(self, speed, acceleration, time_step):
        """
        Update vehicle state based on speed and acceleration.
        
        Args:
            speed (float): Vehicle speed in m/s
            acceleration (float): Vehicle acceleration in m/s²
            time_step (float): Time step in seconds
        """
        # Update distance
        self.current_distance += speed * time_step
        
        # Update speed and acceleration
        self.current_speed = speed
        self.current_acceleration = acceleration
        
        # Calculate power demand
        self.current_power_demand = self._calculate_power_demand(speed, acceleration)
    
    def simulate(self, speed_profile, duration, dt=1.0):
        """
        Simulate the EV with a given speed profile.
        
        Args:
            speed_profile (callable): Function that returns target speed in m/s at time t
            duration (float): Simulation duration in seconds
            dt (float): Time step in seconds
        
        Returns:
            dict: Dictionary containing simulation results
        """
        # Reset simulation data
        self.time_data = []
        self.speed_data = []
        self.acceleration_data = []
        self.distance_data = []
        self.power_demand_data = []
        self.battery_soc_data = []
        self.battery_voltage_data = []
        self.battery_current_data = []
        self.battery_temperature_data = []
        self.motor_speed_data = []
        self.motor_torque_data = []
        self.motor_efficiency_data = []
        
        # Reset vehicle state
        self.current_speed = 0.0
        self.current_acceleration = 0.0
        self.current_distance = 0.0
        self.current_power_demand = 0.0
        
        # Create time points
        time_points = np.arange(0, duration, dt)
        
        # Previous speed for acceleration calculation
        prev_speed = 0.0
        
        # Run simulation
        for t in time_points:
            # Get target speed from profile
            target_speed = speed_profile(t)  # m/s
            
            # Calculate acceleration
            acceleration = (target_speed - prev_speed) / dt
            prev_speed = target_speed
            
            # Update vehicle state
            self._update_vehicle_state(target_speed, acceleration, dt)
            
            # Calculate motor speed and torque
            motor_speed_rpm = self._speed_to_motor_rpm(target_speed)
            
            # Calculate resistive forces
            resistive_force = self._calculate_resistive_forces(target_speed)
            
            # Calculate acceleration force
            acceleration_force = self.vehicle_mass * acceleration
            
            # Total force
            total_force = resistive_force + acceleration_force
            
            # Convert to motor torque
            motor_torque = self._force_to_torque(total_force)
            
            # Calculate power demand in kW
            power_demand = self.current_power_demand
            
            # Calculate battery current based on power demand and voltage
            battery_state = self.battery.get_state()
            battery_voltage = battery_state["voltage"]
            
            # P = V * I, so I = P / V
            # Convert power from kW to W
            if abs(battery_voltage) > 1e-6:
                battery_current = (power_demand * 1000) / battery_voltage
            else:
                battery_current = 0.0
            
            # Apply current to battery (positive current = discharge)
            battery_results = self.battery.apply_constant_current(battery_current, dt, dt)
            
            # Apply torque to motor
            def torque_profile(t_motor):
                return motor_torque
            
            motor_results = self.motor.simulate(torque_profile, dt, dt)
            
            # Store data
            self.time_data.append(t)
            self.speed_data.append(target_speed)
            self.acceleration_data.append(acceleration)
            self.distance_data.append(self.current_distance)
            self.power_demand_data.append(power_demand)
            
            # Battery data
            self.battery_soc_data.append(self.battery.current_soc)
            self.battery_voltage_data.append(self.battery.current_voltage)
            self.battery_current_data.append(battery_current)
            self.battery_temperature_data.append(self.battery.current_temperature)
            
            # Motor data
            self.motor_speed_data.append(self.motor.current_speed)
            self.motor_torque_data.append(self.motor.current_torque)
            self.motor_efficiency_data.append(self.motor.current_efficiency)
        
        # Return results
        return {
            "time": np.array(self.time_data),
            "speed": np.array(self.speed_data),
            "acceleration": np.array(self.acceleration_data),
            "distance": np.array(self.distance_data),
            "power_demand": np.array(self.power_demand_data),
            "battery_soc": np.array(self.battery_soc_data),
            "battery_voltage": np.array(self.battery_voltage_data),
            "battery_current": np.array(self.battery_current_data),
            "battery_temperature": np.array(self.battery_temperature_data),
            "motor_speed": np.array(self.motor_speed_data),
            "motor_torque": np.array(self.motor_torque_data),
            "motor_efficiency": np.array(self.motor_efficiency_data)
        }
    
    def export_to_csv(self, filename):
        """
        Export simulation results to CSV file.
        
        Args:
            filename (str): Output CSV filename
        """
        import pandas as pd
        
        # Create DataFrame
        data = {
            "Time (s)": self.time_data,
            "Speed (m/s)": self.speed_data,
            "Acceleration (m/s²)": self.acceleration_data,
            "Distance (m)": self.distance_data,
            "Power Demand (kW)": self.power_demand_data,
            "Battery SOC": self.battery_soc_data,
            "Battery Voltage (V)": self.battery_voltage_data,
            "Battery Current (A)": self.battery_current_data,
            "Battery Temperature (°C)": [t - 273.15 for t in self.battery_temperature_data],  # Convert K to °C
            "Motor Speed (rpm)": self.motor_speed_data,
            "Motor Torque (Nm)": self.motor_torque_data,
            "Motor Efficiency (%)": [e * 100 for e in self.motor_efficiency_data]
        }
        
        df = pd.DataFrame(data)
        
        # Save to CSV
        df.to_csv(filename, index=False)
        
        print(f"Simulation results exported to {filename}")
    
    def plot_results(self):
        """
        Plot the simulation results.
        
        Returns:
            tuple: Matplotlib figure and axes objects
        """
        if len(self.time_data) == 0:
            raise ValueError("No simulation results to plot. Run a simulation first.")
        
        fig, axes = plt.subplots(4, 2, figsize=(14, 16))
        
        # Plot vehicle speed
        axes[0, 0].plot(self.time_data, self.speed_data)
        axes[0, 0].set_xlabel("Time [s]")
        axes[0, 0].set_ylabel("Speed [m/s]")
        axes[0, 0].set_title("Vehicle Speed")
        axes[0, 0].grid(True)
        
        # Plot vehicle acceleration
        axes[0, 1].plot(self.time_data, self.acceleration_data)
        axes[0, 1].set_xlabel("Time [s]")
        axes[0, 1].set_ylabel("Acceleration [m/s²]")
        axes[0, 1].set_title("Vehicle Acceleration")
        axes[0, 1].grid(True)
        
        # Plot battery SOC
        axes[1, 0].plot(self.time_data, self.battery_soc_data)
        axes[1, 0].set_xlabel("Time [s]")
        axes[1, 0].set_ylabel("State of Charge")
        axes[1, 0].set_title("Battery SOC")
        axes[1, 0].grid(True)
        
        # Plot battery voltage and current
        ax1 = axes[1, 1]
        ax1.plot(self.time_data, self.battery_voltage_data, 'b-', label='Voltage [V]')
        ax1.set_xlabel("Time [s]")
        ax1.set_ylabel("Voltage [V]")
        ax1.set_title("Battery Voltage and Current")
        ax1.grid(True)
        
        ax2 = ax1.twinx()
        ax2.plot(self.time_data, self.battery_current_data, 'r-', label='Current [A]')
        ax2.set_ylabel("Current [A]")
        
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        # Plot motor speed
        axes[2, 0].plot(self.time_data, self.motor_speed_data)
        axes[2, 0].set_xlabel("Time [s]")
        axes[2, 0].set_ylabel("Speed [rpm]")
        axes[2, 0].set_title("Motor Speed")
        axes[2, 0].grid(True)
        
        # Plot motor torque
        axes[2, 1].plot(self.time_data, self.motor_torque_data)
        axes[2, 1].set_xlabel("Time [s]")
        axes[2, 1].set_ylabel("Torque [Nm]")
        axes[2, 1].set_title("Motor Torque")
        axes[2, 1].grid(True)
        
        # Plot power demand
        axes[3, 0].plot(self.time_data, self.power_demand_data)
        axes[3, 0].set_xlabel("Time [s]")
        axes[3, 0].set_ylabel("Power [kW]")
        axes[3, 0].set_title("Power Demand")
        axes[3, 0].grid(True)
        
        # Plot motor efficiency
        axes[3, 1].plot(self.time_data, [e * 100 for e in self.motor_efficiency_data])
        axes[3, 1].set_xlabel("Time [s]")
        axes[3, 1].set_ylabel("Efficiency [%]")
        axes[3, 1].set_title("Motor Efficiency")
        axes[3, 1].grid(True)
        
        plt.tight_layout()
        return fig, axes


def test_ev_digital_twin():
    """
    Test function to demonstrate the EV digital twin functionality.
    """
    # Create EV digital twin
    ev = ElectricVehicleDigitalTwin(
        battery_capacity=75.0,  # 75 kWh battery
        battery_nominal_voltage=400.0,  # 400V system
        motor_power=150.0,  # 150 kW motor
        motor_nominal_speed=8000.0,  # 8000 rpm
        vehicle_mass=2000.0,  # 2000 kg
        wheel_radius=0.33,  # 33 cm
        gear_ratio=9.0,  # 9:1 gear ratio
        drag_coefficient=0.28,  # Aerodynamic drag coefficient
        frontal_area=2.3,  # 2.3 m²
        rolling_resistance=0.01  # Rolling resistance coefficient
    )
    
    # Define a speed profile: acceleration, cruising, deceleration
    def speed_profile(t):
        if t < 10.0:
            return t * 3.0  # Accelerate to 30 m/s (108 km/h) in 10 seconds
        elif t < 50.0:
            return 30.0  # Cruise at 30 m/s for 40 seconds
        elif t < 60.0:
            return 30.0 - (t - 50.0) * 3.0  # Decelerate to 0 m/s in 10 seconds
        else:
            return 0.0  # Stop
    
    # Run simulation
    print("Running EV simulation...")
    results = ev.simulate(speed_profile, duration=70.0, dt=1.0)
    
    # Plot results
    fig, axes = ev.plot_results()
    plt.savefig("ev_simulation_results.png")
    plt.close(fig)
    
    # Export results to CSV
    ev.export_to_csv("ev_simulation_results.csv")
    
    # Print summary
    print(f"Simulation completed for {results['time'][-1]:.1f} seconds")
    print(f"Final distance: {results['distance'][-1]/1000:.2f} km")
    print(f"Final battery SOC: {results['battery_soc'][-1]*100:.2f}%")
    print(f"Average power consumption: {np.mean(results['power_demand']):.2f} kW")
    
    return ev


if __name__ == "__main__":
    test_ev_digital_twin()

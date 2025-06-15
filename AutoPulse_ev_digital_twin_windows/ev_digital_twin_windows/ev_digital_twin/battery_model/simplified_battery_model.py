"""
Simplified Battery Model for Electric Vehicle Digital Twin
---------------------------------------------------------
This module implements a simplified battery model that captures key parameters:
voltage, current, capacity, and temperature.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp


class SimplifiedBatteryModel:
    """
    Simplified battery model for electric vehicle simulation.
    
    This class provides methods to:
    - Initialize a battery model with custom parameters
    - Simulate battery behavior under different load conditions
    - Track voltage, current, capacity, and temperature
    - Provide battery state information to the EV digital twin
    """
    
    def __init__(self, initial_soc=1.0, capacity=3.4, nominal_voltage=3.7):
        """
        Initialize the battery model with parameters.
        
        Args:
            initial_soc (float): Initial state of charge (0.0 to 1.0)
            capacity (float): Battery capacity in Ah
            nominal_voltage (float): Nominal battery voltage in V
        """
        # Store battery parameters
        self.initial_soc = initial_soc
        self.capacity = capacity  # Ah
        self.nominal_voltage = nominal_voltage  # V
        
        # Battery characteristics
        self.r_internal = 0.05  # Internal resistance (ohms)
        self.thermal_mass = 1200.0  # Thermal mass (J/K)
        self.cooling_coefficient = 10.0  # Cooling coefficient (W/K)
        self.ambient_temp = 298.15  # Ambient temperature (K)
        self.max_temp = 333.15  # Maximum safe temperature (K)
        
        # Battery model parameters
        self.k_voltage = 0.1  # Voltage vs SOC curve steepness
        self.v_full = nominal_voltage + 0.5  # Voltage at full charge
        self.v_empty = nominal_voltage - 0.7  # Voltage at empty
        
        # Current state
        self.current_soc = initial_soc
        self.current_voltage = self._calculate_voltage(initial_soc)
        self.current_temperature = self.ambient_temp
        self.current_current = 0.0
        
        # Store simulation data
        self.time_data = []
        self.voltage_data = []
        self.current_data = []
        self.soc_data = []
        self.temperature_data = []
        
        print(f"Simplified battery model initialized with capacity {capacity} Ah and nominal voltage {nominal_voltage} V")
    
    def _calculate_voltage(self, soc):
        """
        Calculate battery voltage based on state of charge.
        
        Args:
            soc (float): State of charge (0.0 to 1.0)
        
        Returns:
            float: Battery voltage
        """
        # Nonlinear relationship between SOC and voltage
        if soc >= 0.9:
            # Exponential rise at high SOC
            return self.v_full - (self.v_full - self.nominal_voltage) * np.exp(-10 * (soc - 0.9))
        elif soc <= 0.1:
            # Exponential drop at low SOC
            return self.v_empty + (self.nominal_voltage - self.v_empty) * np.exp(10 * soc)
        else:
            # Linear region in the middle
            return self.nominal_voltage + (soc - 0.5) * self.k_voltage
    
    def _battery_dynamics(self, t, state, current):
        """
        Battery state dynamics for ODE solver.
        
        Args:
            t (float): Time
            state (array): [SOC, Temperature]
            current (float): Current in Amperes (positive for discharge)
        
        Returns:
            array: State derivatives [dSOC/dt, dTemp/dt]
        """
        soc, temp = state
        
        # SOC dynamics (coulomb counting)
        # dSOC/dt = -I / (capacity * 3600)
        dsoc_dt = -current / (self.capacity * 3600)  # Convert Ah to As
        
        # Temperature dynamics
        # Heat generated = I^2 * R (Joule heating)
        heat_generated = current**2 * self.r_internal
        # Cooling = cooling_coefficient * (T - T_ambient)
        cooling = self.cooling_coefficient * (temp - self.ambient_temp)
        # dTemp/dt = (heat_generated - cooling) / thermal_mass
        dtemp_dt = (heat_generated - cooling) / self.thermal_mass
        
        return [dsoc_dt, dtemp_dt]
    
    def simulate(self, current_profile, duration, dt=1.0):
        """
        Simulate battery behavior with a given current profile.
        
        Args:
            current_profile (callable): Function that returns current at time t
            duration (float): Simulation duration in seconds
            dt (float): Time step for results in seconds
        
        Returns:
            dict: Dictionary containing simulation results
        """
        # Initial state [SOC, Temperature]
        initial_state = [self.current_soc, self.current_temperature]
        
        # Time points for simulation
        t_span = (0, duration)
        t_eval = np.arange(0, duration, dt)
        
        # Solve ODE system
        solution = solve_ivp(
            lambda t, y: self._battery_dynamics(t, y, current_profile(t)),
            t_span,
            initial_state,
            t_eval=t_eval,
            method='RK45',
            rtol=1e-4,
            atol=1e-6
        )
        
        # Extract results
        self.time_data = solution.t / 3600.0  # Convert to hours
        self.soc_data = solution.y[0]
        self.temperature_data = solution.y[1]
        
        # Calculate voltage and current at each time point
        self.voltage_data = np.array([self._calculate_voltage(soc) for soc in self.soc_data])
        self.current_data = np.array([current_profile(t) for t in solution.t])
        
        # Update current state to final values
        self.current_soc = self.soc_data[-1]
        self.current_temperature = self.temperature_data[-1]
        self.current_voltage = self.voltage_data[-1]
        self.current_current = self.current_data[-1]
        
        # Return results dictionary
        return {
            "time": self.time_data,
            "voltage": self.voltage_data,
            "current": self.current_data,
            "soc": self.soc_data,
            "temperature": self.temperature_data
        }
    
    def apply_constant_current(self, current, duration, dt=1.0):
        """
        Apply a constant current to the battery for a specified duration.
        Positive current = discharge, negative current = charge.
        
        Args:
            current (float): Current in Amperes (positive for discharge)
            duration (float): Duration in seconds
            dt (float): Time step in seconds
        
        Returns:
            dict: Dictionary containing simulation results
        """
        # Create constant current profile
        current_profile = lambda t: current
        
        # Run simulation
        return self.simulate(current_profile, duration, dt)
    
    def apply_drive_cycle(self, power_profile, duration, dt=1.0):
        """
        Apply a power-based drive cycle to the battery.
        
        Args:
            power_profile (callable): Function that returns power demand at time t
            duration (float): Duration in seconds
            dt (float): Time step in seconds
        
        Returns:
            dict: Dictionary containing simulation results
        """
        # Create current profile based on power demand and battery voltage
        # This requires an iterative approach since voltage depends on SOC
        # which changes with current, but current depends on voltage
        def current_profile(t):
            power = power_profile(t)
            # Estimate voltage based on current SOC
            voltage = self._calculate_voltage(self.current_soc)
            # Calculate current from power: P = V * I
            # Positive power = discharge (positive current)
            if abs(power) < 1e-6:
                return 0.0
            current = power / voltage
            return current
        
        # Run simulation
        return self.simulate(current_profile, duration, dt)
    
    def get_state(self):
        """
        Get the current state of the battery.
        
        Returns:
            dict: Dictionary containing current battery state
        """
        return {
            "soc": self.current_soc,
            "voltage": self.current_voltage,
            "temperature": self.current_temperature,
            "capacity": self.capacity
        }
    
    def plot_results(self):
        """
        Plot the simulation results.
        
        Returns:
            tuple: Matplotlib figure and axes objects
        """
        if len(self.time_data) == 0:
            raise ValueError("No simulation results to plot. Run a simulation first.")
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # Plot voltage
        axes[0, 0].plot(self.time_data, self.voltage_data)
        axes[0, 0].set_xlabel("Time [h]")
        axes[0, 0].set_ylabel("Voltage [V]")
        axes[0, 0].set_title("Battery Voltage")
        axes[0, 0].grid(True)
        
        # Plot current
        axes[0, 1].plot(self.time_data, self.current_data)
        axes[0, 1].set_xlabel("Time [h]")
        axes[0, 1].set_ylabel("Current [A]")
        axes[0, 1].set_title("Battery Current")
        axes[0, 1].grid(True)
        
        # Plot SOC
        axes[1, 0].plot(self.time_data, self.soc_data)
        axes[1, 0].set_xlabel("Time [h]")
        axes[1, 0].set_ylabel("State of Charge")
        axes[1, 0].set_title("Battery SOC")
        axes[1, 0].grid(True)
        
        # Plot temperature
        axes[1, 1].plot(self.time_data, self.temperature_data - 273.15)  # Convert K to °C
        axes[1, 1].set_xlabel("Time [h]")
        axes[1, 1].set_ylabel("Temperature [°C]")
        axes[1, 1].set_title("Battery Temperature")
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        return fig, axes


def test_battery_model():
    """
    Test function to demonstrate the battery model functionality.
    """
    # Create battery model
    battery = SimplifiedBatteryModel(initial_soc=0.8, capacity=50.0, nominal_voltage=3.7)
    
    # Test discharge at 1C rate (50A for a 50Ah battery)
    print("Testing battery discharge at 1C...")
    results = battery.apply_constant_current(current=50.0, duration=3600)  # 1 hour
    
    # Plot results
    fig, axes = battery.plot_results()
    plt.savefig("battery_simulation_results.png")
    plt.close(fig)
    
    print(f"Final SOC: {battery.current_soc:.2f}")
    print(f"Final Voltage: {battery.current_voltage:.2f} V")
    print(f"Final Temperature: {battery.current_temperature - 273.15:.2f} °C")
    
    # Test variable load profile
    print("\nTesting battery with variable load profile...")
    
    # Create a simple drive cycle with acceleration, cruising, and regenerative braking
    def power_profile(t):
        t_minutes = t / 60
        if t_minutes < 5:  # Acceleration
            return 30000  # 30 kW
        elif t_minutes < 15:  # Cruising
            return 15000  # 15 kW
        elif t_minutes < 17:  # Regenerative braking
            return -10000  # -10 kW (charging)
        else:  # Stopped
            return 0
    
    # Reset battery to initial state
    battery = SimplifiedBatteryModel(initial_soc=0.8, capacity=50.0, nominal_voltage=3.7)
    
    # Run simulation with drive cycle
    results = battery.apply_drive_cycle(power_profile, duration=20*60, dt=10)  # 20 minutes
    
    # Plot results
    fig, axes = battery.plot_results()
    plt.savefig("battery_drive_cycle_results.png")
    plt.close(fig)
    
    print(f"Final SOC after drive cycle: {battery.current_soc:.2f}")
    print(f"Final Voltage after drive cycle: {battery.current_voltage:.2f} V")
    print(f"Final Temperature after drive cycle: {battery.current_temperature - 273.15:.2f} °C")
    
    return battery


if __name__ == "__main__":
    test_battery_model()

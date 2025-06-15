"""
Enhanced Battery Model for Electric Vehicle Digital Twin
-------------------------------------------------------
This module implements an enhanced battery model with cell-level details and RUL calculation.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp


class EnhancedBatteryModel:
    """
    Enhanced battery model for electric vehicle simulation.
    
    This class provides methods to:
    - Initialize a battery model with custom parameters and cell-level details
    - Simulate battery behavior under different load conditions
    - Track voltage, current, capacity, temperature at pack and cell levels
    - Calculate Remaining Useful Life (RUL) based on degradation models
    - Provide battery state information to the EV digital twin
    """
    
    def __init__(self, initial_soc=1.0, capacity=3.4, nominal_voltage=3.7, 
                 num_cells_series=96, num_cells_parallel=4, initial_soh=1.0):
        """
        Initialize the battery model with parameters.
        
        Args:
            initial_soc (float): Initial state of charge (0.0 to 1.0)
            capacity (float): Battery capacity in Ah
            nominal_voltage (float): Nominal battery voltage in V
            num_cells_series (int): Number of cells in series
            num_cells_parallel (int): Number of cells in parallel
            initial_soh (float): Initial state of health (0.0 to 1.0)
        """
        # Store battery parameters
        self.initial_soc = initial_soc
        self.capacity = capacity  # Ah
        self.nominal_voltage = nominal_voltage  # V
        
        # Cell configuration
        self.num_cells_series = num_cells_series
        self.num_cells_parallel = num_cells_parallel
        self.total_cells = num_cells_series * num_cells_parallel
        self.cell_capacity = capacity / num_cells_parallel  # Ah per cell
        self.cell_nominal_voltage = nominal_voltage / num_cells_series  # V per cell
        
        # Battery characteristics
        self.r_internal = 0.05  # Internal resistance (ohms)
        self.cell_r_internal = self.r_internal * num_cells_parallel / num_cells_series  # Internal resistance per cell
        self.thermal_mass = 1200.0  # Thermal mass (J/K)
        self.cell_thermal_mass = self.thermal_mass / self.total_cells  # Thermal mass per cell
        self.cooling_coefficient = 10.0  # Cooling coefficient (W/K)
        self.ambient_temp = 298.15  # Ambient temperature (K)
        self.max_temp = 333.15  # Maximum safe temperature (K)
        
        # Battery model parameters
        self.k_voltage = 0.1  # Voltage vs SOC curve steepness
        self.v_full = self.cell_nominal_voltage + 0.5  # Voltage at full charge per cell
        self.v_empty = self.cell_nominal_voltage - 0.7  # Voltage at empty per cell
        
        # Degradation model parameters
        self.initial_soh = initial_soh
        self.cycle_degradation_rate = 0.0002  # SOH loss per full cycle
        self.calendar_degradation_rate = 0.00005  # SOH loss per day
        self.temperature_factor = 0.005  # Additional degradation per degree above 25°C
        self.dod_factor = 1.5  # Depth of discharge impact factor
        
        # Current state
        self.current_soc = initial_soc
        self.current_soh = initial_soh
        self.current_voltage = self._calculate_voltage(initial_soc)
        self.current_temperature = self.ambient_temp
        self.current_current = 0.0
        
        # Cell-level state arrays
        self.cell_soc = np.ones(self.total_cells) * initial_soc
        self.cell_voltage = np.ones(self.total_cells) * self._calculate_cell_voltage(initial_soc)
        self.cell_temperature = np.ones(self.total_cells) * self.ambient_temp
        self.cell_current = np.zeros(self.total_cells)
        self.cell_soh = np.ones(self.total_cells) * initial_soh
        
        # Cycle counting for degradation
        self.cycle_count = 0
        self.energy_throughput = 0  # Ah
        self.last_soc = initial_soc
        self.min_soc_in_cycle = initial_soc
        self.max_soc_in_cycle = initial_soc
        self.cycle_depths = []  # Store depths of discharge for each cycle
        self.operation_days = 0  # Simulated operation time in days
        
        # RUL estimation
        self.rul_cycles = self._estimate_rul_cycles()
        self.rul_calendar = self._estimate_rul_calendar()
        self.rul_combined = min(self.rul_cycles, self.rul_calendar)
        
        # Store simulation data
        self.time_data = []
        self.voltage_data = []
        self.current_data = []
        self.soc_data = []
        self.temperature_data = []
        self.soh_data = []
        self.rul_data = []
        
        print(f"Enhanced battery model initialized with {self.total_cells} cells "
              f"({num_cells_series}S{num_cells_parallel}P), "
              f"{capacity} Ah capacity and {nominal_voltage} V nominal voltage")
    
    def _calculate_cell_voltage(self, soc):
        """
        Calculate cell voltage based on state of charge.
        
        Args:
            soc (float): State of charge (0.0 to 1.0)
        
        Returns:
            float: Cell voltage
        """
        # Nonlinear relationship between SOC and voltage
        if soc >= 0.9:
            # Exponential rise at high SOC
            return self.v_full - (self.v_full - self.cell_nominal_voltage) * np.exp(-10 * (soc - 0.9))
        elif soc <= 0.1:
            # Exponential drop at low SOC
            return self.v_empty + (self.cell_nominal_voltage - self.v_empty) * np.exp(10 * soc)
        else:
            # Linear region in the middle
            return self.cell_nominal_voltage + (soc - 0.5) * self.k_voltage
    
    def _calculate_voltage(self, soc):
        """
        Calculate pack voltage based on state of charge.
        
        Args:
            soc (float): State of charge (0.0 to 1.0)
        
        Returns:
            float: Pack voltage
        """
        return self._calculate_cell_voltage(soc) * self.num_cells_series
    
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
    
    def _update_cell_states(self, soc, temperature, current):
        """
        Update cell-level states based on pack-level values.
        
        Args:
            soc (float): Pack state of charge
            temperature (float): Pack temperature
            current (float): Pack current
        """
        # Calculate cell current (assuming equal distribution in parallel strings)
        cell_current = current / self.num_cells_parallel
        
        # Update cell states with small variations to simulate cell imbalance
        for i in range(self.total_cells):
            # Cell position: row (series position), col (parallel position)
            row = i // self.num_cells_parallel
            col = i % self.num_cells_parallel
            
            # Add small random variations to simulate cell imbalance
            soc_variation = np.random.normal(0, 0.01)  # 1% standard deviation
            temp_variation = np.random.normal(0, 1.0)  # 1K standard deviation
            
            # Ensure variations stay within reasonable bounds
            self.cell_soc[i] = np.clip(soc + soc_variation, 0.0, 1.0)
            self.cell_temperature[i] = max(self.ambient_temp, temperature + temp_variation)
            
            # Cell current is divided among parallel cells
            self.cell_current[i] = cell_current
            
            # Calculate cell voltage based on SOC
            self.cell_voltage[i] = self._calculate_cell_voltage(self.cell_soc[i])
    
    def _update_degradation(self, soc, temperature, current, time_step):
        """
        Update battery degradation based on usage.
        
        Args:
            soc (float): State of charge
            temperature (float): Temperature in K
            current (float): Current in A
            time_step (float): Time step in seconds
        """
        # Track SOC for cycle counting
        if soc < self.min_soc_in_cycle:
            self.min_soc_in_cycle = soc
        if soc > self.max_soc_in_cycle:
            self.max_soc_in_cycle = soc
        
        # Detect cycle completion (when SOC starts increasing after decreasing or vice versa)
        if (self.last_soc < soc and self.last_soc < self.min_soc_in_cycle) or \
           (self.last_soc > soc and self.last_soc > self.max_soc_in_cycle):
            # Calculate depth of discharge for the completed cycle
            dod = self.max_soc_in_cycle - self.min_soc_in_cycle
            self.cycle_depths.append(dod)
            
            # Increment cycle count (partial cycle based on depth)
            self.cycle_count += dod
            
            # Calculate cycle degradation with DOD factor
            # Deeper cycles cause more degradation
            cycle_degradation = self.cycle_degradation_rate * dod * self.dod_factor
            
            # Apply degradation to SOH
            self.current_soh -= cycle_degradation
            
            # Reset cycle tracking
            self.min_soc_in_cycle = soc
            self.max_soc_in_cycle = soc
        
        # Track energy throughput
        self.energy_throughput += abs(current) * time_step / 3600  # Convert to Ah
        
        # Calendar aging (time-based degradation)
        days_step = time_step / (24 * 3600)  # Convert seconds to days
        self.operation_days += days_step
        calendar_degradation = self.calendar_degradation_rate * days_step
        
        # Temperature effect on degradation
        # Higher temperatures accelerate degradation
        temp_celsius = temperature - 273.15
        if temp_celsius > 25:
            temp_degradation = self.temperature_factor * (temp_celsius - 25) * days_step
        else:
            temp_degradation = 0
        
        # Apply calendar and temperature degradation
        self.current_soh -= (calendar_degradation + temp_degradation)
        
        # Ensure SOH stays within bounds
        self.current_soh = max(0.0, min(1.0, self.current_soh))
        
        # Update cell-level SOH with small variations
        for i in range(self.total_cells):
            soh_variation = np.random.normal(0, 0.005)  # 0.5% standard deviation
            self.cell_soh[i] = max(0.0, min(1.0, self.current_soh + soh_variation))
        
        # Update RUL estimates
        self.rul_cycles = self._estimate_rul_cycles()
        self.rul_calendar = self._estimate_rul_calendar()
        self.rul_combined = min(self.rul_cycles, self.rul_calendar)
        
        # Update last SOC
        self.last_soc = soc
    
    def _estimate_rul_cycles(self):
        """
        Estimate remaining useful life based on cycle degradation.
        
        Returns:
            float: Estimated RUL in cycles
        """
        if self.current_soh <= 0.8:
            return 0  # End of life reached
        
        # Calculate average depth of discharge
        avg_dod = np.mean(self.cycle_depths) if self.cycle_depths else 0.8
        
        # Calculate degradation per cycle
        degradation_per_cycle = self.cycle_degradation_rate * avg_dod * self.dod_factor
        
        # Calculate remaining cycles until SOH reaches 0.8 (80% capacity)
        remaining_soh = self.current_soh - 0.8
        remaining_cycles = remaining_soh / degradation_per_cycle if degradation_per_cycle > 0 else 1000
        
        return max(0, remaining_cycles)
    
    def _estimate_rul_calendar(self):
        """
        Estimate remaining useful life based on calendar aging.
        
        Returns:
            float: Estimated RUL in days
        """
        if self.current_soh <= 0.8:
            return 0  # End of life reached
        
        # Calculate average temperature effect
        avg_temp = np.mean(self.temperature_data) if self.temperature_data else self.ambient_temp
        avg_temp_celsius = avg_temp - 273.15
        temp_factor = self.temperature_factor * max(0, avg_temp_celsius - 25)
        
        # Calculate degradation per day
        degradation_per_day = self.calendar_degradation_rate + temp_factor
        
        # Calculate remaining days until SOH reaches 0.8 (80% capacity)
        remaining_soh = self.current_soh - 0.8
        remaining_days = remaining_soh / degradation_per_day if degradation_per_day > 0 else 3650  # ~10 years
        
        return max(0, remaining_days)
    
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
        
        # Calculate SOH and RUL at each time point
        self.soh_data = []
        self.rul_data = []
        
        # Update cell states and degradation at each time point
        for i, t in enumerate(solution.t):
            # Update degradation
            if i > 0:
                time_step = solution.t[i] - solution.t[i-1]
                self._update_degradation(self.soc_data[i], self.temperature_data[i], 
                                        self.current_data[i], time_step)
            
            # Update cell states
            self._update_cell_states(self.soc_data[i], self.temperature_data[i], 
                                    self.current_data[i])
            
            # Store SOH and RUL
            self.soh_data.append(self.current_soh)
            self.rul_data.append(self.rul_combined)
        
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
            "temperature": self.temperature_data,
            "soh": np.array(self.soh_data),
            "rul": np.array(self.rul_data),
            "cell_soc": self.cell_soc,
            "cell_voltage": self.cell_voltage,
            "cell_temperature": self.cell_temperature,
            "cell_current": self.cell_current,
            "cell_soh": self.cell_soh
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
            "capacity": self.capacity * self.current_soh,  # Available capacity
            "soh": self.current_soh,
            "rul_cycles": self.rul_cycles,
            "rul_calendar_days": self.rul_calendar,
            "cycle_count": self.cycle_count,
            "energy_throughput": self.energy_throughput,
            "cell_config": f"{self.num_cells_series}S{self.num_cells_parallel}P",
            "total_cells": self.total_cells,
            "cell_soc_min": np.min(self.cell_soc),
            "cell_soc_max": np.max(self.cell_soc),
            "cell_voltage_min": np.min(self.cell_voltage),
            "cell_voltage_max": np.max(self.cell_voltage),
            "cell_temperature_min": np.min(self.cell_temperature),
            "cell_temperature_max": np.max(self.cell_temperature),
            "cell_soh_min": np.min(self.cell_soh),
            "cell_soh_max": np.max(self.cell_soh)
        }
    
    def plot_results(self):
        """
        Plot the simulation results.
        
        Returns:
            tuple: Matplotlib figure and axes objects
        """
        if len(self.time_data) == 0:
            raise ValueError("No simulation results to plot. Run a simulation first.")
        
        fig, axes = plt.subplots(3, 2, figsize=(14, 12))
        
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
        
        # Plot SOH
        axes[2, 0].plot(self.time_data, self.soh_data)
        axes[2, 0].set_xlabel("Time [h]")
        axes[2, 0].set_ylabel("State of Health")
        axes[2, 0].set_title("Battery SOH")
        axes[2, 0].grid(True)
        
        # Plot RUL
        axes[2, 1].plot(self.time_data, self.rul_data)
        axes[2, 1].set_xlabel("Time [h]")
        axes[2, 1].set_ylabel("Remaining Useful Life [cycles]")
        axes[2, 1].set_title("Battery RUL")
        axes[2, 1].grid(True)
        
        plt.tight_layout()
        return fig, axes
    
    def plot_cell_distribution(self):
        """
        Plot the distribution of cell-level parameters.
        
        Returns:
            tuple: Matplotlib figure and axes objects
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Reshape cell data to match physical layout
        soc_grid = self.cell_soc.reshape(self.num_cells_series, self.num_cells_parallel)
        voltage_grid = self.cell_voltage.reshape(self.num_cells_series, self.num_cells_parallel)
        temp_grid = self.cell_temperature.reshape(self.num_cells_series, self.num_cells_parallel) - 273.15  # K to °C
        soh_grid = self.cell_soh.reshape(self.num_cells_series, self.num_cells_parallel)
        
        # Plot SOC distribution
        im0 = axes[0, 0].imshow(soc_grid, cmap='viridis', aspect='auto')
        axes[0, 0].set_title('Cell SOC Distribution')
        axes[0, 0].set_xlabel('Parallel Position')
        axes[0, 0].set_ylabel('Series Position')
        fig.colorbar(im0, ax=axes[0, 0], label='SOC')
        
        # Plot voltage distribution
        im1 = axes[0, 1].imshow(voltage_grid, cmap='plasma', aspect='auto')
        axes[0, 1].set_title('Cell Voltage Distribution [V]')
        axes[0, 1].set_xlabel('Parallel Position')
        axes[0, 1].set_ylabel('Series Position')
        fig.colorbar(im1, ax=axes[0, 1], label='Voltage [V]')
        
        # Plot temperature distribution
        im2 = axes[1, 0].imshow(temp_grid, cmap='inferno', aspect='auto')
        axes[1, 0].set_title('Cell Temperature Distribution [°C]')
        axes[1, 0].set_xlabel('Parallel Position')
        axes[1, 0].set_ylabel('Series Position')
        fig.colorbar(im2, ax=axes[1, 0], label='Temperature [°C]')
        
        # Plot SOH distribution
        im3 = axes[1, 1].imshow(soh_grid, cmap='cividis', aspect='auto')
        axes[1, 1].set_title('Cell SOH Distribution')
        axes[1, 1].set_xlabel('Parallel Position')
        axes[1, 1].set_ylabel('Series Position')
        fig.colorbar(im3, ax=axes[1, 1], label='SOH')
        
        plt.tight_layout()
        return fig, axes


def test_enhanced_battery_model():
    """
    Test function to demonstrate the enhanced battery model functionality.
    """
    # Create battery model with cell-level details
    battery = EnhancedBatteryModel(
        initial_soc=0.8, 
        capacity=75.0, 
        nominal_voltage=400.0,
        num_cells_series=96,
        num_cells_parallel=4,
        initial_soh=0.95
    )
    
    # Test discharge at 1C rate
    print("Testing battery discharge at 1C...")
    results = battery.apply_constant_current(current=75.0, duration=3600)  # 1 hour
    
    # Plot results
    fig, axes = battery.plot_results()
    plt.savefig("enhanced_battery_simulation_results.png")
    plt.close(fig)
    
    # Plot cell distribution
    fig, axes = battery.plot_cell_distribution()
    plt.savefig("battery_cell_distribution.png")
    plt.close(fig)
    
    # Print battery state
    state = battery.get_state()
    print(f"Final SOC: {state['soc']:.2f}")
    print(f"Final Voltage: {state['voltage']:.2f} V")
    print(f"Final Temperature: {state['temperature'] - 273.15:.2f} °C")
    print(f"State of Health: {state['soh']:.4f}")
    print(f"Remaining Useful Life: {state['rul_cycles']:.1f} cycles")
    print(f"Cell Configuration: {state['cell_config']} ({state['total_cells']} cells)")
    print(f"Cell SOC Range: {state['cell_soc_min']:.4f} - {state['cell_soc_max']:.4f}")
    print(f"Cell Temperature Range: {state['cell_temperature_min'] - 273.15:.2f}°C - {state['cell_temperature_max'] - 273.15:.2f}°C")
    
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
    battery = EnhancedBatteryModel(
        initial_soc=0.8, 
        capacity=75.0, 
        nominal_voltage=400.0,
        num_cells_series=96,
        num_cells_parallel=4,
        initial_soh=0.95
    )
    
    # Run simulation with drive cycle
    results = battery.apply_drive_cycle(power_profile, duration=20*60, dt=10)  # 20 minutes
    
    # Plot results
    fig, axes = battery.plot_results()
    plt.savefig("enhanced_battery_drive_cycle_results.png")
    plt.close(fig)
    
    # Print battery state
    state = battery.get_state()
    print(f"Final SOC after drive cycle: {state['soc']:.2f}")
    print(f"Final Voltage after drive cycle: {state['voltage']:.2f} V")
    print(f"Final Temperature after drive cycle: {state['temperature'] - 273.15:.2f} °C")
    print(f"State of Health after drive cycle: {state['soh']:.4f}")
    print(f"Remaining Useful Life after drive cycle: {state['rul_cycles']:.1f} cycles")
    
    # Test accelerated aging simulation
    print("\nTesting accelerated aging simulation...")
    
    # Create a new battery with lower initial SOH
    battery = EnhancedBatteryModel(
        initial_soc=0.8, 
        capacity=75.0, 
        nominal_voltage=400.0,
        num_cells_series=96,
        num_cells_parallel=4,
        initial_soh=0.9
    )
    
    # Simulate 1000 cycles of 80% DOD
    total_duration = 0
    for i in range(1000):
        # Discharge 80%
        results = battery.apply_constant_current(current=75.0, duration=2880)  # 0.8 * 3600
        total_duration += 2880
        
        # Charge back to 80%
        results = battery.apply_constant_current(current=-75.0, duration=2880)
        total_duration += 2880
        
        # Print progress every 100 cycles
        if (i+1) % 100 == 0:
            state = battery.get_state()
            print(f"After {i+1} cycles: SOH = {state['soh']:.4f}, RUL = {state['rul_cycles']:.1f} cycles")
            
            # Stop if battery reaches end of life
            if state['soh'] < 0.8:
                print("Battery reached end of life (SOH < 80%)")
                break
    
    # Plot final results
    fig, axes = battery.plot_results()
    plt.savefig("battery_aging_simulation_results.png")
    plt.close(fig)
    
    # Plot cell distribution
    fig, axes = battery.plot_cell_distribution()
    plt.savefig("aged_battery_cell_distribution.png")
    plt.close(fig)
    
    return battery


if __name__ == "__main__":
    test_enhanced_battery_model()

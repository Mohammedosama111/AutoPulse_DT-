"""
Enhanced Motor Model for Electric Vehicle Digital Twin
-----------------------------------------------------
This module implements an enhanced PMSM motor model with detailed torque calculations and RUL estimation.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp


class EnhancedPMSMMotorModel:
    """
    Enhanced PMSM (Permanent Magnet Synchronous Motor) model for electric vehicle simulation.
    
    This class provides methods to:
    - Initialize a PMSM motor model with custom parameters
    - Simulate motor behavior under different load conditions
    - Track torque, speed, efficiency, temperature, and other parameters
    - Calculate Remaining Useful Life (RUL) based on wear models
    - Provide motor state information to the EV digital twin
    """
    
    def __init__(self, nominal_power=150.0, nominal_speed=8000.0, nominal_voltage=400.0, 
                 motor_type="PMSM", pole_pairs=4, initial_health=1.0):
        """
        Initialize the motor model with parameters.
        
        Args:
            nominal_power (float): Nominal motor power in kW
            nominal_speed (float): Nominal motor speed in rpm
            nominal_voltage (float): Nominal motor voltage in V
            motor_type (str): Motor type (PMSM, BLDC, etc.)
            pole_pairs (int): Number of pole pairs
            initial_health (float): Initial health factor (0.0 to 1.0)
        """
        # Store motor parameters
        self.nominal_power = nominal_power  # kW
        self.nominal_speed = nominal_speed  # rpm
        self.nominal_voltage = nominal_voltage  # V
        self.motor_type = motor_type
        self.pole_pairs = pole_pairs
        
        # Calculate derived parameters
        self.nominal_torque = (nominal_power * 1000) / (nominal_speed * 2 * np.pi / 60)  # Nm
        self.max_torque = self.nominal_torque * 2.0  # Peak torque
        self.max_speed = self.nominal_speed * 1.2  # Maximum speed
        
        # Motor electrical parameters
        self.r_stator = 0.05  # Stator resistance (ohms)
        self.l_d = 0.001  # d-axis inductance (H)
        self.l_q = 0.001  # q-axis inductance (H)
        self.flux_pm = 0.2  # Permanent magnet flux (Wb)
        self.j_rotor = 0.01  # Rotor inertia (kg*m²)
        self.b_friction = 0.001  # Friction coefficient (Nm*s/rad)
        
        # Thermal parameters
        self.thermal_resistance = 0.05  # K/W
        self.thermal_capacitance = 5000.0  # J/K
        self.ambient_temp = 298.15  # K (25°C)
        self.max_temp = 423.15  # K (150°C)
        self.current_temperature = self.ambient_temp
        
        # Efficiency map parameters
        self.base_efficiency = 0.92  # Base efficiency at nominal conditions
        self.copper_loss_factor = 0.6  # Proportion of losses from copper
        self.iron_loss_factor = 0.3  # Proportion of losses from iron
        self.mechanical_loss_factor = 0.1  # Proportion of losses from mechanical
        
        # Wear and degradation parameters
        self.initial_health = initial_health
        self.current_health = initial_health
        self.thermal_wear_factor = 0.0001  # Health degradation per hour at max temperature
        self.current_wear_factor = 0.0002  # Health degradation per hour at max current
        self.mechanical_wear_factor = 0.0001  # Health degradation per hour at max speed
        
        # Operation counters for RUL
        self.operation_hours = 0
        self.high_temp_hours = 0  # Hours above 100°C
        self.high_current_hours = 0  # Hours above nominal current
        self.high_speed_hours = 0  # Hours above nominal speed
        
        # Current state
        self.current_speed = 0.0  # rpm
        self.current_torque = 0.0  # Nm
        self.current_power = 0.0  # kW
        self.current_efficiency = 0.0
        self.current_i_d = 0.0  # d-axis current
        self.current_i_q = 0.0  # q-axis current
        self.current_v_d = 0.0  # d-axis voltage
        self.current_v_q = 0.0  # q-axis voltage
        
        # RUL estimation
        self.rul_hours = self._estimate_rul()
        
        # Store simulation data
        self.time_data = []
        self.speed_data = []
        self.torque_data = []
        self.power_data = []
        self.efficiency_data = []
        self.temperature_data = []
        self.health_data = []
        self.rul_data = []
        
        print(f"Enhanced {motor_type} motor model initialized with "
              f"{nominal_power} kW nominal power, {nominal_speed} rpm nominal speed, "
              f"and {nominal_voltage} V nominal voltage")
        print(f"Motor has {pole_pairs} pole pairs and {self.nominal_torque:.1f} Nm nominal torque")
    
    def _motor_dynamics(self, t, state, torque_load):
        """
        Motor state dynamics for ODE solver.
        
        Args:
            t (float): Time
            state (array): [Speed (rad/s), Temperature (K)]
            torque_load (float): Load torque in Nm
        
        Returns:
            array: State derivatives [dSpeed/dt, dTemp/dt]
        """
        speed_rad_s, temp = state
        
        # Calculate motor torque based on field-oriented control
        # In FOC, we typically control i_q for torque and keep i_d at 0 for PMSM
        # Torque = 1.5 * p * flux_pm * i_q
        
        # Calculate required i_q for the desired torque
        i_q_desired = torque_load / (1.5 * self.pole_pairs * self.flux_pm)
        i_d_desired = 0.0  # Typically kept at 0 for PMSM
        
        # Apply current limits
        i_q_max = (self.nominal_power * 1000) / (self.nominal_voltage * 0.9)  # Approximate max current
        i_q = np.clip(i_q_desired, -i_q_max, i_q_max)
        i_d = np.clip(i_d_desired, -i_q_max, i_q_max)
        
        # Calculate motor torque
        motor_torque = 1.5 * self.pole_pairs * (self.flux_pm * i_q + (self.l_d - self.l_q) * i_d * i_q)
        
        # Calculate friction torque
        friction_torque = self.b_friction * speed_rad_s
        
        # Calculate net torque
        net_torque = motor_torque - friction_torque - torque_load
        
        # Speed dynamics
        # dω/dt = T_net / J
        dspeed_dt = net_torque / self.j_rotor
        
        # Calculate losses
        # Copper losses = 1.5 * R * (i_d² + i_q²)
        copper_losses = 1.5 * self.r_stator * (i_d**2 + i_q**2)
        
        # Iron losses (simplified model, proportional to speed²)
        iron_losses = 0.01 * (speed_rad_s / (self.nominal_speed * 2 * np.pi / 60))**2 * self.nominal_power * 1000
        
        # Mechanical losses (simplified model, proportional to speed³)
        mechanical_losses = 0.005 * (speed_rad_s / (self.nominal_speed * 2 * np.pi / 60))**3 * self.nominal_power * 1000
        
        # Total losses
        total_losses = copper_losses + iron_losses + mechanical_losses
        
        # Temperature dynamics
        # dT/dt = (P_loss - (T - T_ambient) / R_th) / C_th
        cooling = (temp - self.ambient_temp) / self.thermal_resistance
        dtemp_dt = (total_losses - cooling) / self.thermal_capacitance
        
        # Update current state for external access
        self.current_i_d = i_d
        self.current_i_q = i_q
        self.current_torque = motor_torque
        
        # Calculate power and efficiency
        mechanical_power = motor_torque * speed_rad_s  # W
        electrical_power = mechanical_power + total_losses  # W
        
        if electrical_power > 0:
            self.current_efficiency = mechanical_power / electrical_power
        else:
            self.current_efficiency = 0.0
        
        self.current_power = mechanical_power / 1000  # kW
        
        return [dspeed_dt, dtemp_dt]
    
    def _update_degradation(self, speed, torque, temperature, time_step):
        """
        Update motor degradation based on usage.
        
        Args:
            speed (float): Motor speed in rpm
            torque (float): Motor torque in Nm
            temperature (float): Motor temperature in K
            time_step (float): Time step in seconds
        """
        # Convert time step to hours
        hours = time_step / 3600
        
        # Update operation hours
        self.operation_hours += hours
        
        # Calculate normalized parameters
        norm_speed = speed / self.nominal_speed
        norm_torque = torque / self.nominal_torque
        norm_temp = (temperature - self.ambient_temp) / (self.max_temp - self.ambient_temp)
        
        # Update high stress operation hours
        if temperature > 373.15:  # > 100°C
            self.high_temp_hours += hours
        
        if abs(torque) > self.nominal_torque:
            self.high_current_hours += hours
        
        if abs(speed) > self.nominal_speed:
            self.high_speed_hours += hours
        
        # Calculate wear factors
        thermal_wear = self.thermal_wear_factor * hours * max(0, norm_temp)**2
        current_wear = self.current_wear_factor * hours * max(0, norm_torque)**2
        mechanical_wear = self.mechanical_wear_factor * hours * max(0, norm_speed)**2
        
        # Apply degradation to health
        total_wear = thermal_wear + current_wear + mechanical_wear
        self.current_health = max(0.0, self.current_health - total_wear)
        
        # Update RUL estimate
        self.rul_hours = self._estimate_rul()
    
    def _estimate_rul(self):
        """
        Estimate remaining useful life based on current health and usage patterns.
        
        Returns:
            float: Estimated RUL in hours
        """
        if self.current_health <= 0.7:
            return 0  # End of life reached
        
        # Calculate average degradation rate based on operation history
        if self.operation_hours > 0:
            avg_degradation_rate = (self.initial_health - self.current_health) / self.operation_hours
        else:
            # Estimate based on nominal conditions
            avg_degradation_rate = (self.thermal_wear_factor + self.current_wear_factor + self.mechanical_wear_factor) * 0.5
        
        # Calculate remaining hours until health reaches 0.7 (70% health)
        remaining_health = self.current_health - 0.7
        
        if avg_degradation_rate > 0:
            remaining_hours = remaining_health / avg_degradation_rate
        else:
            remaining_hours = 10000  # Arbitrary large number
        
        return max(0, remaining_hours)
    
    def _calculate_efficiency(self, speed, torque):
        """
        Calculate motor efficiency based on speed and torque.
        
        Args:
            speed (float): Motor speed in rpm
            torque (float): Motor torque in Nm
        
        Returns:
            float: Efficiency (0.0 to 1.0)
        """
        # Normalize speed and torque
        norm_speed = speed / self.nominal_speed
        norm_torque = torque / self.nominal_torque
        
        # Base efficiency at nominal conditions
        efficiency = self.base_efficiency
        
        # Reduce efficiency at low speed/torque
        if norm_speed < 0.2 or abs(norm_torque) < 0.2:
            efficiency *= 0.7 + 0.3 * min(norm_speed, abs(norm_torque)) / 0.2
        
        # Reduce efficiency at very high speed
        if norm_speed > 1.0:
            efficiency *= 1.0 - 0.1 * (norm_speed - 1.0) / 0.2
        
        # Reduce efficiency at very high torque
        if abs(norm_torque) > 1.0:
            efficiency *= 1.0 - 0.05 * (abs(norm_torque) - 1.0) / 0.2
        
        # Reduce efficiency based on health
        efficiency *= 0.7 + 0.3 * self.current_health
        
        return max(0.1, min(0.98, efficiency))
    
    def simulate(self, torque_profile, duration, dt=1.0):
        """
        Simulate motor behavior with a given torque profile.
        
        Args:
            torque_profile (callable): Function that returns load torque at time t
            duration (float): Simulation duration in seconds
            dt (float): Time step for results in seconds
        
        Returns:
            dict: Dictionary containing simulation results
        """
        # Initial state [Speed (rad/s), Temperature (K)]
        initial_state = [self.current_speed * 2 * np.pi / 60, self.current_temperature]
        
        # Time points for simulation
        t_span = (0, duration)
        t_eval = np.arange(0, duration, dt)
        
        # Solve ODE system
        solution = solve_ivp(
            lambda t, y: self._motor_dynamics(t, y, torque_profile(t)),
            t_span,
            initial_state,
            t_eval=t_eval,
            method='RK45',
            rtol=1e-4,
            atol=1e-6
        )
        
        # Extract results
        self.time_data = solution.t
        speed_rad_s = solution.y[0]
        self.temperature_data = solution.y[1]
        
        # Convert rad/s to rpm
        self.speed_data = speed_rad_s * 60 / (2 * np.pi)
        
        # Calculate torque, power, and efficiency at each time point
        self.torque_data = np.array([torque_profile(t) for t in solution.t])
        self.power_data = np.array([s * t * 2 * np.pi / 60 / 1000 for s, t in zip(self.speed_data, self.torque_data)])
        self.efficiency_data = np.array([self._calculate_efficiency(s, t) for s, t in zip(self.speed_data, self.torque_data)])
        
        # Update degradation and store health and RUL data
        self.health_data = []
        self.rul_data = []
        
        for i, t in enumerate(solution.t):
            # Update degradation
            if i > 0:
                time_step = solution.t[i] - solution.t[i-1]
                self._update_degradation(self.speed_data[i], self.torque_data[i], 
                                        self.temperature_data[i], time_step)
            
            # Store health and RUL
            self.health_data.append(self.current_health)
            self.rul_data.append(self.rul_hours)
        
        # Update current state to final values
        self.current_speed = self.speed_data[-1]
        self.current_temperature = self.temperature_data[-1]
        self.current_torque = self.torque_data[-1]
        self.current_power = self.power_data[-1]
        self.current_efficiency = self.efficiency_data[-1]
        
        # Return results dictionary
        return {
            "time": self.time_data,
            "speed": self.speed_data,
            "torque": self.torque_data,
            "power": self.power_data,
            "efficiency": self.efficiency_data,
            "temperature": self.temperature_data,
            "health": np.array(self.health_data),
            "rul": np.array(self.rul_data)
        }
    
    def apply_constant_torque(self, torque, duration, dt=1.0):
        """
        Apply a constant torque to the motor for a specified duration.
        
        Args:
            torque (float): Torque in Nm
            duration (float): Duration in seconds
            dt (float): Time step in seconds
        
        Returns:
            dict: Dictionary containing simulation results
        """
        # Create constant torque profile
        torque_profile = lambda t: torque
        
        # Run simulation
        return self.simulate(torque_profile, duration, dt)
    
    def apply_speed_profile(self, speed_profile, duration, dt=1.0, controller_kp=10.0, controller_ki=1.0):
        """
        Apply a speed profile to the motor using a PI controller.
        
        Args:
            speed_profile (callable): Function that returns target speed at time t
            duration (float): Duration in seconds
            dt (float): Time step in seconds
            controller_kp (float): Proportional gain for PI controller
            controller_ki (float): Integral gain for PI controller
        
        Returns:
            dict: Dictionary containing simulation results
        """
        # PI controller state
        error_integral = 0.0
        
        # Create torque profile based on speed error
        def torque_profile(t):
            # Get target speed
            target_speed = speed_profile(t)
            
            # Calculate speed error
            error = target_speed - self.current_speed
            
            # Update integral term
            nonlocal error_integral
            error_integral += error * dt
            
            # Calculate control output (torque)
            torque = controller_kp * error + controller_ki * error_integral
            
            # Limit torque to motor capabilities
            torque = np.clip(torque, -self.max_torque, self.max_torque)
            
            return torque
        
        # Run simulation
        return self.simulate(torque_profile, duration, dt)
    
    def get_state(self):
        """
        Get the current state of the motor.
        
        Returns:
            dict: Dictionary containing current motor state
        """
        return {
            "speed": self.current_speed,
            "torque": self.current_torque,
            "power": self.current_power,
            "efficiency": self.current_efficiency,
            "temperature": self.current_temperature,
            "health": self.current_health,
            "rul_hours": self.rul_hours,
            "operation_hours": self.operation_hours,
            "high_temp_hours": self.high_temp_hours,
            "high_current_hours": self.high_current_hours,
            "high_speed_hours": self.high_speed_hours,
            "motor_type": self.motor_type,
            "pole_pairs": self.pole_pairs,
            "nominal_power": self.nominal_power,
            "nominal_speed": self.nominal_speed,
            "nominal_torque": self.nominal_torque,
            "max_torque": self.max_torque,
            "max_speed": self.max_speed
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
        
        # Plot speed
        axes[0, 0].plot(self.time_data, self.speed_data)
        axes[0, 0].set_xlabel("Time [s]")
        axes[0, 0].set_ylabel("Speed [rpm]")
        axes[0, 0].set_title("Motor Speed")
        axes[0, 0].grid(True)
        
        # Plot torque
        axes[0, 1].plot(self.time_data, self.torque_data)
        axes[0, 1].set_xlabel("Time [s]")
        axes[0, 1].set_ylabel("Torque [Nm]")
        axes[0, 1].set_title("Motor Torque")
        axes[0, 1].grid(True)
        
        # Plot power
        axes[1, 0].plot(self.time_data, self.power_data)
        axes[1, 0].set_xlabel("Time [s]")
        axes[1, 0].set_ylabel("Power [kW]")
        axes[1, 0].set_title("Motor Power")
        axes[1, 0].grid(True)
        
        # Plot efficiency
        axes[1, 1].plot(self.time_data, self.efficiency_data * 100)
        axes[1, 1].set_xlabel("Time [s]")
        axes[1, 1].set_ylabel("Efficiency [%]")
        axes[1, 1].set_title("Motor Efficiency")
        axes[1, 1].grid(True)
        
        # Plot temperature
        axes[2, 0].plot(self.time_data, self.temperature_data - 273.15)  # Convert K to °C
        axes[2, 0].set_xlabel("Time [s]")
        axes[2, 0].set_ylabel("Temperature [°C]")
        axes[2, 0].set_title("Motor Temperature")
        axes[2, 0].grid(True)
        
        # Plot health and RUL
        ax1 = axes[2, 1]
        ax2 = ax1.twinx()
        
        ax1.plot(self.time_data, np.array(self.health_data) * 100, 'b-', label='Health')
        ax1.set_xlabel("Time [s]")
        ax1.set_ylabel("Health [%]", color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        
        ax2.plot(self.time_data, np.array(self.rul_data), 'r-', label='RUL')
        ax2.set_ylabel("RUL [hours]", color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        
        axes[2, 1].set_title("Motor Health and RUL")
        axes[2, 1].grid(True)
        
        plt.tight_layout()
        return fig, axes
    
    def plot_efficiency_map(self, speed_range=None, torque_range=None):
        """
        Plot the motor efficiency map.
        
        Args:
            speed_range (tuple, optional): Speed range (min, max) in rpm
            torque_range (tuple, optional): Torque range (min, max) in Nm
        
        Returns:
            tuple: Matplotlib figure and axes objects
        """
        # Set default ranges if not provided
        if speed_range is None:
            speed_range = (0, self.max_speed)
        
        if torque_range is None:
            torque_range = (0, self.max_torque)
        
        # Create speed and torque grids
        speeds = np.linspace(speed_range[0], speed_range[1], 50)
        torques = np.linspace(torque_range[0], torque_range[1], 50)
        
        speed_grid, torque_grid = np.meshgrid(speeds, torques)
        efficiency_grid = np.zeros_like(speed_grid)
        
        # Calculate efficiency at each point
        for i in range(speed_grid.shape[0]):
            for j in range(speed_grid.shape[1]):
                efficiency_grid[i, j] = self._calculate_efficiency(speed_grid[i, j], torque_grid[i, j])
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Plot efficiency map
        contour = ax.contourf(speed_grid, torque_grid, efficiency_grid * 100, 
                             levels=np.linspace(70, 98, 15), cmap='viridis')
        
        # Add contour lines
        contour_lines = ax.contour(speed_grid, torque_grid, efficiency_grid * 100,
                                  levels=[80, 85, 90, 95], colors='k', linewidths=0.5)
        ax.clabel(contour_lines, fmt='%1.0f%%', fontsize=8)
        
        # Add colorbar
        cbar = fig.colorbar(contour, ax=ax)
        cbar.set_label('Efficiency [%]')
        
        # Plot nominal and maximum operating points
        ax.plot(self.nominal_speed, self.nominal_torque, 'ro', markersize=10, label='Nominal Point')
        ax.plot(self.nominal_speed, self.max_torque, 'r*', markersize=10, label='Peak Torque')
        ax.plot(self.max_speed, self.nominal_torque * self.nominal_speed / self.max_speed, 'r^', 
               markersize=10, label='Max Speed')
        
        # Add constant power curves
        powers = [self.nominal_power * 0.25, self.nominal_power * 0.5, self.nominal_power, 
                 self.nominal_power * 1.5]
        for p in powers:
            # P = T * ω, so T = P / ω
            # Convert power from kW to W and rpm to rad/s
            power_w = p * 1000
            speeds_rad_s = speeds * 2 * np.pi / 60
            torques_curve = np.array([power_w / s if s > 0 else self.max_torque for s in speeds_rad_s])
            
            # Clip torque to max torque
            torques_curve = np.minimum(torques_curve, self.max_torque)
            
            ax.plot(speeds, torques_curve, 'k--', linewidth=0.5)
            
            # Add power label at middle of curve
            middle_idx = len(speeds) // 2
            if speeds_rad_s[middle_idx] > 0:
                middle_torque = power_w / speeds_rad_s[middle_idx]
                if middle_torque <= self.max_torque:
                    ax.text(speeds[middle_idx], middle_torque, f"{p:.1f} kW", 
                           fontsize=8, ha='center', va='bottom')
        
        # Set labels and title
        ax.set_xlabel('Speed [rpm]')
        ax.set_ylabel('Torque [Nm]')
        ax.set_title(f'{self.motor_type} Motor Efficiency Map')
        
        # Add legend
        ax.legend(loc='upper right')
        
        # Set axis limits
        ax.set_xlim(speed_range)
        ax.set_ylim(torque_range)
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        return fig, ax


def test_enhanced_motor_model():
    """
    Test function to demonstrate the enhanced motor model functionality.
    """
    # Create motor model
    motor = EnhancedPMSMMotorModel(
        nominal_power=150.0,
        nominal_speed=8000.0,
        nominal_voltage=400.0,
        motor_type="PMSM",
        pole_pairs=4,
        initial_health=0.95
    )
    
    # Test constant torque
    print("Testing motor with constant torque...")
    results = motor.apply_constant_torque(torque=100.0, duration=60)  # 1 minute
    
    # Plot results
    fig, axes = motor.plot_results()
    plt.savefig("enhanced_motor_torque_profile_results.png")
    plt.close(fig)
    
    # Print motor state
    state = motor.get_state()
    print(f"Final Speed: {state['speed']:.2f} rpm")
    print(f"Final Torque: {state['torque']:.2f} Nm")
    print(f"Final Power: {state['power']:.2f} kW")
    print(f"Final Efficiency: {state['efficiency']*100:.2f}%")
    print(f"Final Temperature: {state['temperature'] - 273.15:.2f} °C")
    print(f"Motor Health: {state['health']*100:.2f}%")
    print(f"Remaining Useful Life: {state['rul_hours']:.1f} hours")
    
    # Test speed profile
    print("\nTesting motor with speed profile...")
    
    # Create a simple speed profile with acceleration, cruising, and deceleration
    def speed_profile(t):
        t_seconds = t
        if t_seconds < 10:  # Acceleration
            return t_seconds * 400  # 0 to 4000 rpm in 10 seconds
        elif t_seconds < 40:  # Cruising
            return 4000  # Cruise at 4000 rpm
        elif t_seconds < 50:  # Deceleration
            return 4000 - (t_seconds - 40) * 400  # 4000 to 0 rpm in 10 seconds
        else:  # Stopped
            return 0
    
    # Reset motor to initial state
    motor = EnhancedPMSMMotorModel(
        nominal_power=150.0,
        nominal_speed=8000.0,
        nominal_voltage=400.0,
        motor_type="PMSM",
        pole_pairs=4,
        initial_health=0.95
    )
    
    # Run simulation with speed profile
    results = motor.apply_speed_profile(speed_profile, duration=60, dt=0.1)
    
    # Plot results
    fig, axes = motor.plot_results()
    plt.savefig("enhanced_motor_speed_profile_results.png")
    plt.close(fig)
    
    # Plot efficiency map
    fig, ax = motor.plot_efficiency_map()
    plt.savefig("motor_efficiency_map.png")
    plt.close(fig)
    
    # Print motor state
    state = motor.get_state()
    print(f"Final Speed after profile: {state['speed']:.2f} rpm")
    print(f"Final Torque after profile: {state['torque']:.2f} Nm")
    print(f"Final Power after profile: {state['power']:.2f} kW")
    print(f"Final Efficiency after profile: {state['efficiency']*100:.2f}%")
    print(f"Final Temperature after profile: {state['temperature'] - 273.15:.2f} °C")
    print(f"Motor Health after profile: {state['health']*100:.2f}%")
    print(f"Remaining Useful Life after profile: {state['rul_hours']:.1f} hours")
    
    # Test accelerated aging simulation
    print("\nTesting accelerated aging simulation...")
    
    # Create a new motor with lower initial health
    motor = EnhancedPMSMMotorModel(
        nominal_power=150.0,
        nominal_speed=8000.0,
        nominal_voltage=400.0,
        motor_type="PMSM",
        pole_pairs=4,
        initial_health=0.9
    )
    
    # Simulate operation at high temperature and torque
    for i in range(100):
        # Run at high torque and speed
        results = motor.apply_constant_torque(torque=motor.nominal_torque * 1.5, duration=3600)  # 1 hour
        
        # Print progress every 10 iterations
        if (i+1) % 10 == 0:
            state = motor.get_state()
            print(f"After {i+1} hours: Health = {state['health']*100:.2f}%, "
                 f"RUL = {state['rul_hours']:.1f} hours, "
                 f"Temp = {state['temperature'] - 273.15:.1f}°C")
            
            # Stop if motor reaches end of life
            if state['health'] < 0.7:
                print("Motor reached end of life (Health < 70%)")
                break
    
    # Plot final results
    fig, axes = motor.plot_results()
    plt.savefig("motor_aging_simulation_results.png")
    plt.close(fig)
    
    return motor


if __name__ == "__main__":
    test_enhanced_motor_model()

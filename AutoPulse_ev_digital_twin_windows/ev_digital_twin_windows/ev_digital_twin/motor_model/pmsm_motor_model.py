"""
PMSM Motor Model for Electric Vehicle Digital Twin
-------------------------------------------------
This module implements a Permanent Magnet Synchronous Motor (PMSM) model using the GYM electric motor library.
The model simulates motor behavior with focus on torque, speed, and efficiency.
"""

import gym_electric_motor as gem
import numpy as np
import matplotlib.pyplot as plt
from gym_electric_motor.physical_systems.mechanical_loads import ConstantSpeedLoad, ExternalSpeedLoad
from gym_electric_motor.visualization import MotorDashboard


class PMSMMotorModel:
    """
    PMSM motor model using GYM electric motor library.
    
    This class provides methods to:
    - Initialize a PMSM motor model with custom parameters
    - Simulate motor behavior under different load conditions
    - Track torque, speed, currents, and voltages
    - Provide motor state information to the EV digital twin
    """
    
    def __init__(self, nominal_power=100.0, nominal_speed=4000.0, nominal_voltage=400.0):
        """
        Initialize the PMSM motor model with parameters.
        
        Args:
            nominal_power (float): Nominal motor power in kW
            nominal_speed (float): Nominal motor speed in rpm
            nominal_voltage (float): Nominal motor voltage in V
        """
        # Store motor parameters
        self.nominal_power = nominal_power  # kW
        self.nominal_speed = nominal_speed  # rpm
        self.nominal_voltage = nominal_voltage  # V
        
        # Calculate derived parameters
        self.nominal_torque = (nominal_power * 1000) / (nominal_speed * 2 * np.pi / 60)  # Nm
        
        # Initialize state variables
        self.current_speed = 0.0  # rpm
        self.current_torque = 0.0  # Nm
        self.current_currents = np.zeros(3)  # A (3-phase)
        self.current_voltages = np.zeros(3)  # V (3-phase)
        self.current_efficiency = 0.0  # %
        
        # Store simulation data
        self.time_data = []
        self.speed_data = []
        self.torque_data = []
        self.currents_data = []
        self.voltages_data = []
        self.efficiency_data = []
        
        # Create the PMSM environment
        self.env = self._create_pmsm_environment()
        
        print(f"PMSM motor model initialized with nominal power {nominal_power} kW, "
              f"nominal speed {nominal_speed} rpm, and nominal voltage {nominal_voltage} V")
    
    def _create_pmsm_environment(self):
        """
        Create a GYM electric motor environment for PMSM simulation.
        
        Returns:
            gym.Env: GYM environment for PMSM motor
        """
        # Define motor parameters
        motor_parameter = dict(
            p=3,  # Number of pole pairs
            l_d=0.0014,  # d-axis inductance in H
            l_q=0.0014,  # q-axis inductance in H
            psi_p=0.1,  # Permanent magnet flux in Vs
            r_s=0.05,  # Stator resistance in Ohm
            j_rotor=0.001,  # Rotor inertia in kg*m^2
        )
        
        # Define nominal values
        nominal_values = dict(
            i=150.0,  # Nominal current in A
            omega=self.nominal_speed * 2 * np.pi / 60,  # Nominal angular velocity in rad/s
            torque=self.nominal_torque,  # Nominal torque in Nm
            u=self.nominal_voltage,  # Nominal voltage in V
            epsilon=1.0,  # Nominal efficiency
        )
        
        # Define limits
        limit_values = dict(
            i=300.0,  # Maximum current in A
            omega=1.5 * self.nominal_speed * 2 * np.pi / 60,  # Maximum angular velocity in rad/s
            torque=2.0 * self.nominal_torque,  # Maximum torque in Nm
            u=1.5 * self.nominal_voltage,  # Maximum voltage in V
        )
        
        # Create the environment
        env = gem.make(
            "Cont-SC-PMSM-v0",  # Continuous action space, speed control, PMSM motor
            visualization=MotorDashboard(state_plots=['omega', 'torque', 'i_a', 'i_b', 'i_c', 'u_a', 'u_b', 'u_c']),
            motor_parameter=motor_parameter,
            nominal_values=nominal_values,
            limit_values=limit_values,
            load_parameter=dict(
                j_load=0.1,  # Load inertia in kg*m^2
                a=0.01,  # Friction coefficient
            ),
            reward_function=None,  # No reward function needed for simulation
            reference_generator=dict(
                reference_state='omega',
                sigma=1e-3,
            ),
        )
        
        return env
    
    def reset(self):
        """
        Reset the motor model to initial state.
        
        Returns:
            dict: Initial state of the motor
        """
        # Reset the environment
        state, _ = self.env.reset()
        
        # Reset state variables
        self.current_speed = 0.0
        self.current_torque = 0.0
        self.current_currents = np.zeros(3)
        self.current_voltages = np.zeros(3)
        self.current_efficiency = 0.0
        
        # Reset simulation data
        self.time_data = []
        self.speed_data = []
        self.torque_data = []
        self.currents_data = []
        self.voltages_data = []
        self.efficiency_data = []
        
        return self.get_state()
    
    def step(self, action):
        """
        Step the motor simulation with a given action.
        
        Args:
            action (float or array): Control action for the motor
                For speed control: target speed in rad/s
                For torque control: target torque in Nm
                For current control: target currents in A
        
        Returns:
            dict: New state of the motor
        """
        # Step the environment
        state, _, terminated, truncated, info = self.env.step(action)
        
        # Extract state variables
        omega = state[self.env.state_names.index('omega')]  # rad/s
        torque = state[self.env.state_names.index('torque')]  # Nm
        i_a = state[self.env.state_names.index('i_a')]  # A
        i_b = state[self.env.state_names.index('i_b')]  # A
        i_c = state[self.env.state_names.index('i_c')]  # A
        
        # Extract voltages from info if available
        if 'u_a' in info and 'u_b' in info and 'u_c' in info:
            u_a = info['u_a']
            u_b = info['u_b']
            u_c = info['u_c']
        else:
            u_a = u_b = u_c = 0.0
        
        # Update state variables
        self.current_speed = omega * 60 / (2 * np.pi)  # Convert rad/s to rpm
        self.current_torque = torque
        self.current_currents = np.array([i_a, i_b, i_c])
        self.current_voltages = np.array([u_a, u_b, u_c])
        
        # Calculate efficiency (simplified)
        mechanical_power = abs(omega * torque)  # W
        electrical_power = abs(i_a * u_a + i_b * u_b + i_c * u_c)  # W
        
        if electrical_power > 0:
            if mechanical_power > electrical_power:  # Regenerative braking
                self.current_efficiency = 0.9  # Assume 90% efficiency in regeneration
            else:
                self.current_efficiency = mechanical_power / electrical_power
        else:
            self.current_efficiency = 0.0
        
        # Store data
        self.time_data.append(len(self.time_data) * self.env.tau)  # Time in seconds
        self.speed_data.append(self.current_speed)
        self.torque_data.append(self.current_torque)
        self.currents_data.append(self.current_currents)
        self.voltages_data.append(self.current_voltages)
        self.efficiency_data.append(self.current_efficiency)
        
        return self.get_state()
    
    def run_speed_profile(self, speed_profile, duration, dt=0.001):
        """
        Run the motor with a given speed profile.
        
        Args:
            speed_profile (callable): Function that returns target speed in rpm at time t
            duration (float): Simulation duration in seconds
            dt (float): Time step in seconds
        
        Returns:
            dict: Dictionary containing simulation results
        """
        # Reset the motor
        self.reset()
        
        # Create time points
        time_points = np.arange(0, duration, dt)
        
        # Run simulation
        for t in time_points:
            # Get target speed in rpm and convert to rad/s
            target_speed_rpm = speed_profile(t)
            target_speed_rads = target_speed_rpm * 2 * np.pi / 60
            
            # Normalize action to [-1, 1] range for the environment
            normalized_action = target_speed_rads / (1.5 * self.nominal_speed * 2 * np.pi / 60)
            normalized_action = np.clip(normalized_action, -1.0, 1.0)
            
            # Step the simulation
            self.step([normalized_action])
        
        # Return results
        return {
            "time": np.array(self.time_data),
            "speed": np.array(self.speed_data),
            "torque": np.array(self.torque_data),
            "currents": np.array(self.currents_data),
            "voltages": np.array(self.voltages_data),
            "efficiency": np.array(self.efficiency_data)
        }
    
    def run_torque_profile(self, torque_profile, duration, dt=0.001):
        """
        Run the motor with a given torque profile.
        
        Args:
            torque_profile (callable): Function that returns target torque in Nm at time t
            duration (float): Simulation duration in seconds
            dt (float): Time step in seconds
        
        Returns:
            dict: Dictionary containing simulation results
        """
        # For torque control, we need to modify the environment
        # Save the current environment
        speed_control_env = self.env
        
        # Create a torque control environment
        torque_control_env = gem.make(
            "Cont-TC-PMSM-v0",  # Continuous action space, torque control, PMSM motor
            visualization=None,
            motor_parameter=speed_control_env.physical_system.electrical_motor.motor_parameter,
            nominal_values=speed_control_env.physical_system.limits.nominal_values,
            limit_values=speed_control_env.physical_system.limits.limits,
            load_parameter=speed_control_env.physical_system.mechanical_load.load_parameter,
            reward_function=None,
        )
        
        # Set the environment to torque control
        self.env = torque_control_env
        
        # Reset the motor
        self.reset()
        
        # Create time points
        time_points = np.arange(0, duration, dt)
        
        # Run simulation
        for t in time_points:
            # Get target torque in Nm
            target_torque = torque_profile(t)
            
            # Normalize action to [-1, 1] range for the environment
            normalized_action = target_torque / (2.0 * self.nominal_torque)
            normalized_action = np.clip(normalized_action, -1.0, 1.0)
            
            # Step the simulation
            self.step([normalized_action])
        
        # Restore the speed control environment
        self.env = speed_control_env
        
        # Return results
        return {
            "time": np.array(self.time_data),
            "speed": np.array(self.speed_data),
            "torque": np.array(self.torque_data),
            "currents": np.array(self.currents_data),
            "voltages": np.array(self.voltages_data),
            "efficiency": np.array(self.efficiency_data)
        }
    
    def get_state(self):
        """
        Get the current state of the motor.
        
        Returns:
            dict: Dictionary containing current motor state
        """
        return {
            "speed": self.current_speed,
            "torque": self.current_torque,
            "currents": self.current_currents,
            "voltages": self.current_voltages,
            "efficiency": self.current_efficiency,
            "power": self.current_torque * self.current_speed * 2 * np.pi / 60 / 1000  # kW
        }
    
    def plot_results(self):
        """
        Plot the simulation results.
        
        Returns:
            tuple: Matplotlib figure and axes objects
        """
        if len(self.time_data) == 0:
            raise ValueError("No simulation results to plot. Run a simulation first.")
        
        fig, axes = plt.subplots(3, 2, figsize=(14, 10))
        
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
        
        # Plot currents
        currents = np.array(self.currents_data)
        axes[1, 0].plot(self.time_data, currents[:, 0], label='i_a')
        axes[1, 0].plot(self.time_data, currents[:, 1], label='i_b')
        axes[1, 0].plot(self.time_data, currents[:, 2], label='i_c')
        axes[1, 0].set_xlabel("Time [s]")
        axes[1, 0].set_ylabel("Current [A]")
        axes[1, 0].set_title("Motor Currents")
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        
        # Plot voltages
        voltages = np.array(self.voltages_data)
        axes[1, 1].plot(self.time_data, voltages[:, 0], label='u_a')
        axes[1, 1].plot(self.time_data, voltages[:, 1], label='u_b')
        axes[1, 1].plot(self.time_data, voltages[:, 2], label='u_c')
        axes[1, 1].set_xlabel("Time [s]")
        axes[1, 1].set_ylabel("Voltage [V]")
        axes[1, 1].set_title("Motor Voltages")
        axes[1, 1].legend()
        axes[1, 1].grid(True)
        
        # Plot efficiency
        axes[2, 0].plot(self.time_data, np.array(self.efficiency_data) * 100)
        axes[2, 0].set_xlabel("Time [s]")
        axes[2, 0].set_ylabel("Efficiency [%]")
        axes[2, 0].set_title("Motor Efficiency")
        axes[2, 0].grid(True)
        
        # Plot power
        power_data = np.array(self.torque_data) * np.array(self.speed_data) * 2 * np.pi / 60 / 1000  # kW
        axes[2, 1].plot(self.time_data, power_data)
        axes[2, 1].set_xlabel("Time [s]")
        axes[2, 1].set_ylabel("Power [kW]")
        axes[2, 1].set_title("Motor Power")
        axes[2, 1].grid(True)
        
        plt.tight_layout()
        return fig, axes


def test_motor_model():
    """
    Test function to demonstrate the motor model functionality.
    """
    # Create motor model
    motor = PMSMMotorModel(nominal_power=100.0, nominal_speed=4000.0, nominal_voltage=400.0)
    
    # Define a speed profile: ramp up, constant speed, ramp down
    def speed_profile(t):
        if t < 1.0:
            return t * 2000  # Ramp up to 2000 rpm in 1 second
        elif t < 3.0:
            return 2000  # Constant speed for 2 seconds
        elif t < 4.0:
            return 2000 - (t - 3.0) * 2000  # Ramp down to 0 rpm in 1 second
        else:
            return 0  # Stop
    
    # Run simulation with speed profile
    print("Testing motor with speed profile...")
    results = motor.run_speed_profile(speed_profile, duration=5.0, dt=0.01)
    
    # Plot results
    fig, axes = motor.plot_results()
    plt.savefig("motor_speed_profile_results.png")
    plt.close(fig)
    
    # Print final state
    state = motor.get_state()
    print(f"Final Speed: {state['speed']:.2f} rpm")
    print(f"Final Torque: {state['torque']:.2f} Nm")
    print(f"Final Power: {state['power']:.2f} kW")
    print(f"Final Efficiency: {state['efficiency']*100:.2f}%")
    
    # Define a torque profile: constant torque, reverse torque
    def torque_profile(t):
        if t < 2.0:
            return 100  # Constant torque for 2 seconds
        elif t < 4.0:
            return -50  # Reverse torque (braking) for 2 seconds
        else:
            return 0  # No torque
    
    # Reset motor and run simulation with torque profile
    motor.reset()
    print("\nTesting motor with torque profile...")
    results = motor.run_torque_profile(torque_profile, duration=5.0, dt=0.01)
    
    # Plot results
    fig, axes = motor.plot_results()
    plt.savefig("motor_torque_profile_results.png")
    plt.close(fig)
    
    # Print final state
    state = motor.get_state()
    print(f"Final Speed: {state['speed']:.2f} rpm")
    print(f"Final Torque: {state['torque']:.2f} Nm")
    print(f"Final Power: {state['power']:.2f} kW")
    print(f"Final Efficiency: {state['efficiency']*100:.2f}%")
    
    return motor


if __name__ == "__main__":
    test_motor_model()

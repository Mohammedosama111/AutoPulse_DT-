"""
Simplified PMSM Motor Model for Electric Vehicle Digital Twin
-----------------------------------------------------------
This module implements a simplified Permanent Magnet Synchronous Motor (PMSM) model
that simulates motor behavior with focus on torque, speed, and efficiency.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp


class SimplifiedPMSMMotorModel:
    """
    Simplified PMSM motor model for electric vehicle simulation.
    
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
        
        # Motor characteristics
        self.r_stator = 0.05  # Stator resistance (ohms)
        self.l_d = 0.001  # d-axis inductance (H)
        self.l_q = 0.001  # q-axis inductance (H)
        self.psi_pm = 0.1  # Permanent magnet flux (Wb)
        self.pole_pairs = 3  # Number of pole pairs
        self.j_rotor = 0.01  # Rotor inertia (kg*m^2)
        self.b_friction = 0.001  # Friction coefficient (Nm*s/rad)
        self.max_current = 300.0  # Maximum current (A)
        
        # Initialize state variables
        self.current_speed = 0.0  # rpm
        self.current_torque = 0.0  # Nm
        self.current_currents = np.zeros(3)  # A (3-phase)
        self.current_voltages = np.zeros(3)  # V (3-phase)
        self.current_efficiency = 0.0  # %
        self.current_power = 0.0  # kW
        
        # Store simulation data
        self.time_data = []
        self.speed_data = []
        self.torque_data = []
        self.currents_data = []
        self.voltages_data = []
        self.efficiency_data = []
        self.power_data = []
        
        print(f"Simplified PMSM motor model initialized with nominal power {nominal_power} kW, "
              f"nominal speed {nominal_speed} rpm, and nominal voltage {nominal_voltage} V")
    
    def _motor_dynamics(self, t, state, torque_load):
        """
        Motor state dynamics for ODE solver.
        
        Args:
            t (float): Time
            state (array): [omega (rad/s), i_d, i_q]
            torque_load (float): Load torque in Nm
        
        Returns:
            array: State derivatives [domega/dt, di_d/dt, di_q/dt]
        """
        omega, i_d, i_q = state
        
        # Calculate electromagnetic torque
        # T_em = 3/2 * p * [(L_d - L_q) * i_d * i_q + psi_pm * i_q]
        torque_em = 1.5 * self.pole_pairs * ((self.l_d - self.l_q) * i_d * i_q + self.psi_pm * i_q)
        
        # Speed dynamics
        # domega/dt = (T_em - T_load - B*omega) / J
        domega_dt = (torque_em - torque_load - self.b_friction * omega) / self.j_rotor
        
        # Current dynamics (simplified FOC control)
        # Assume perfect current control with time constant tau_i
        tau_i = 0.001  # Current control time constant (s)
        
        # Target currents based on torque control
        if abs(torque_load) < 1e-6:
            i_d_ref = 0.0
            i_q_ref = 0.0
        else:
            # Field weakening if speed is above nominal
            omega_nominal = self.nominal_speed * 2 * np.pi / 60
            if abs(omega) > omega_nominal:
                # Apply field weakening
                i_d_ref = -0.2 * self.max_current * (abs(omega) - omega_nominal) / omega_nominal
                i_d_ref = max(i_d_ref, -0.5 * self.max_current)
            else:
                i_d_ref = 0.0  # No field weakening below nominal speed
            
            # Calculate i_q for desired torque
            if abs(self.psi_pm) > 1e-6:
                i_q_ref = (2.0 * torque_load) / (3.0 * self.pole_pairs * self.psi_pm)
            else:
                i_q_ref = 0.0
            
            # Limit current magnitude
            i_mag = np.sqrt(i_d_ref**2 + i_q_ref**2)
            if i_mag > self.max_current:
                scale = self.max_current / i_mag
                i_d_ref *= scale
                i_q_ref *= scale
        
        # Current dynamics
        di_d_dt = (i_d_ref - i_d) / tau_i
        di_q_dt = (i_q_ref - i_q) / tau_i
        
        return [domega_dt, di_d_dt, di_q_dt]
    
    def _calculate_voltages(self, omega, i_d, i_q):
        """
        Calculate d-q voltages based on current state.
        
        Args:
            omega (float): Angular velocity in rad/s
            i_d (float): d-axis current
            i_q (float): q-axis current
        
        Returns:
            tuple: (v_d, v_q) d-q voltages
        """
        # v_d = R*i_d - omega*L_q*i_q
        v_d = self.r_stator * i_d - omega * self.l_q * i_q
        
        # v_q = R*i_q + omega*L_d*i_d + omega*psi_pm
        v_q = self.r_stator * i_q + omega * self.l_d * i_d + omega * self.psi_pm
        
        return v_d, v_q
    
    def _dq_to_abc(self, theta, i_d, i_q):
        """
        Convert d-q currents to three-phase abc currents.
        
        Args:
            theta (float): Electrical angle in radians
            i_d (float): d-axis current
            i_q (float): q-axis current
        
        Returns:
            array: [i_a, i_b, i_c] three-phase currents
        """
        # Park transformation matrix
        cos_theta = np.cos(theta)
        cos_theta_120 = np.cos(theta - 2*np.pi/3)
        cos_theta_240 = np.cos(theta - 4*np.pi/3)
        
        sin_theta = np.sin(theta)
        sin_theta_120 = np.sin(theta - 2*np.pi/3)
        sin_theta_240 = np.sin(theta - 4*np.pi/3)
        
        i_a = i_d * cos_theta - i_q * sin_theta
        i_b = i_d * cos_theta_120 - i_q * sin_theta_120
        i_c = i_d * cos_theta_240 - i_q * sin_theta_240
        
        return np.array([i_a, i_b, i_c])
    
    def _calculate_efficiency(self, omega, torque, i_d, i_q):
        """
        Calculate motor efficiency.
        
        Args:
            omega (float): Angular velocity in rad/s
            torque (float): Torque in Nm
            i_d (float): d-axis current
            i_q (float): q-axis current
        
        Returns:
            float: Efficiency (0.0 to 1.0)
        """
        # Calculate mechanical power
        mechanical_power = abs(omega * torque)  # W
        
        # Calculate electrical losses
        copper_loss = self.r_stator * (i_d**2 + i_q**2)  # W
        iron_loss = 0.01 * omega**2  # Simplified iron loss model
        friction_loss = self.b_friction * omega**2  # Friction loss
        
        # Total losses
        total_loss = copper_loss + iron_loss + friction_loss
        
        # Calculate electrical power
        if omega > 0 and torque > 0:  # Motoring mode
            electrical_power = mechanical_power + total_loss
            return mechanical_power / electrical_power if electrical_power > 0 else 0.0
        elif omega > 0 and torque < 0:  # Regenerative braking
            electrical_power = mechanical_power - total_loss
            return 0.9  # Assume 90% efficiency in regeneration
        else:
            return 0.0
    
    def simulate(self, torque_profile, duration, dt=0.001):
        """
        Simulate motor behavior with a given torque profile.
        
        Args:
            torque_profile (callable): Function that returns load torque in Nm at time t
            duration (float): Simulation duration in seconds
            dt (float): Time step for results in seconds
        
        Returns:
            dict: Dictionary containing simulation results
        """
        # Initial state [omega (rad/s), i_d, i_q]
        initial_state = [0.0, 0.0, 0.0]
        
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
        omega_data = solution.y[0]
        i_d_data = solution.y[1]
        i_q_data = solution.y[2]
        
        # Convert rad/s to rpm
        self.speed_data = omega_data * 60 / (2 * np.pi)
        
        # Calculate torque at each time point
        self.torque_data = np.array([1.5 * self.pole_pairs * ((self.l_d - self.l_q) * i_d * i_q + self.psi_pm * i_q) 
                                    for i_d, i_q in zip(i_d_data, i_q_data)])
        
        # Calculate three-phase currents
        theta_data = np.array([self.pole_pairs * np.cumsum([omega * dt for omega in omega_data])])
        self.currents_data = np.array([self._dq_to_abc(theta, i_d, i_q) 
                                      for theta, i_d, i_q in zip(theta_data[0], i_d_data, i_q_data)])
        
        # Calculate voltages
        v_dq_data = np.array([self._calculate_voltages(omega, i_d, i_q) 
                             for omega, i_d, i_q in zip(omega_data, i_d_data, i_q_data)])
        v_d_data = v_dq_data[:, 0]
        v_q_data = v_dq_data[:, 1]
        
        # Convert to three-phase voltages (simplified)
        self.voltages_data = np.array([np.array([v_d, v_q, -(v_d + v_q)]) 
                                      for v_d, v_q in zip(v_d_data, v_q_data)])
        
        # Calculate efficiency
        self.efficiency_data = np.array([self._calculate_efficiency(omega, torque, i_d, i_q) 
                                        for omega, torque, i_d, i_q in zip(omega_data, self.torque_data, i_d_data, i_q_data)])
        
        # Calculate power in kW
        self.power_data = np.array([torque * omega / 1000 
                                   for torque, omega in zip(self.torque_data, omega_data)])
        
        # Update current state to final values
        self.current_speed = self.speed_data[-1]
        self.current_torque = self.torque_data[-1]
        self.current_currents = self.currents_data[-1]
        self.current_voltages = self.voltages_data[-1]
        self.current_efficiency = self.efficiency_data[-1]
        self.current_power = self.power_data[-1]
        
        # Return results dictionary
        return {
            "time": self.time_data,
            "speed": self.speed_data,
            "torque": self.torque_data,
            "currents": self.currents_data,
            "voltages": self.voltages_data,
            "efficiency": self.efficiency_data,
            "power": self.power_data
        }
    
    def run_speed_profile(self, speed_profile, duration, dt=0.001):
        """
        Run the motor with a given speed profile using a PI controller.
        
        Args:
            speed_profile (callable): Function that returns target speed in rpm at time t
            duration (float): Simulation duration in seconds
            dt (float): Time step in seconds
        
        Returns:
            dict: Dictionary containing simulation results
        """
        # PI controller parameters
        kp = 0.5  # Proportional gain
        ki = 0.1  # Integral gain
        
        # Create torque profile based on speed error
        def torque_controller(t):
            # Get target speed in rpm and convert to rad/s
            target_speed_rpm = speed_profile(t)
            target_speed_rads = target_speed_rpm * 2 * np.pi / 60
            
            # Get current speed (use last known speed or 0 if no data)
            current_speed_rads = self.current_speed * 2 * np.pi / 60 if len(self.speed_data) > 0 else 0
            
            # Calculate speed error
            error = target_speed_rads - current_speed_rads
            
            # Calculate integral term (simplified)
            if len(self.time_data) > 0:
                integral = sum([error * dt for _ in range(len(self.time_data))])
            else:
                integral = 0
            
            # Calculate control output (torque)
            torque = kp * error + ki * integral
            
            # Limit torque to motor capabilities
            max_torque = 2.0 * self.nominal_torque
            return np.clip(torque, -max_torque, max_torque)
        
        # Run simulation with torque controller
        return self.simulate(torque_controller, duration, dt)
    
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
            "power": self.current_power
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
        axes[1, 1].plot(self.time_data, voltages[:, 0], label='v_a')
        axes[1, 1].plot(self.time_data, voltages[:, 1], label='v_b')
        axes[1, 1].plot(self.time_data, voltages[:, 2], label='v_c')
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
        axes[2, 1].plot(self.time_data, self.power_data)
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
    motor = SimplifiedPMSMMotorModel(nominal_power=100.0, nominal_speed=4000.0, nominal_voltage=400.0)
    
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
    motor = SimplifiedPMSMMotorModel(nominal_power=100.0, nominal_speed=4000.0, nominal_voltage=400.0)
    print("\nTesting motor with torque profile...")
    results = motor.simulate(torque_profile, duration=5.0, dt=0.01)
    
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

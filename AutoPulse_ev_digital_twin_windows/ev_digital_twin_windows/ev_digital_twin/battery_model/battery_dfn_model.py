"""
Battery DFN Model for Electric Vehicle Digital Twin
---------------------------------------------------
This module implements a Doyle-Fuller-Newman (DFN) battery model using PyBaMM.
The model simulates battery behavior with focus on voltage, current, capacity, and temperature.
"""

import pybamm
import numpy as np
import matplotlib.pyplot as plt


class BatteryDFNModel:
    """
    Battery model using PyBaMM's DFN implementation.
    
    This class provides methods to:
    - Initialize a DFN battery model with custom parameters
    - Simulate battery behavior under different load conditions
    - Track voltage, current, capacity, and temperature
    - Provide battery state information to the EV digital twin
    """
    
    def __init__(self, initial_soc=1.0, capacity=3.4, nominal_voltage=3.7):
        """
        Initialize the battery model with DFN parameters.
        
        Args:
            initial_soc (float): Initial state of charge (0.0 to 1.0)
            capacity (float): Battery capacity in Ah
            nominal_voltage (float): Nominal battery voltage in V
        """
        # Store battery parameters
        self.initial_soc = initial_soc
        self.capacity = capacity  # Ah
        self.nominal_voltage = nominal_voltage  # V
        
        # Store simulation data
        self.time_data = []
        self.voltage_data = []
        self.current_data = []
        self.soc_data = []
        self.temperature_data = []
        
        # Initialize state variables
        self.current_soc = initial_soc
        self.current_voltage = nominal_voltage
        self.current_temperature = 298.15  # K
        
        # Initialize simulation
        self.simulation = None
        self.solution = None
        
        print(f"Battery DFN model initialized with capacity {capacity} Ah and nominal voltage {nominal_voltage} V")
    
    def create_simulation(self, experiment=None):
        """
        Create a PyBaMM simulation with the DFN model.
        
        Args:
            experiment (pybamm.Experiment, optional): PyBaMM experiment to run.
                If None, a default experiment will be created.
        
        Returns:
            pybamm.Simulation: The created simulation object
        """
        # Create a DFN model
        model = pybamm.lithium_ion.DFN()
        
        # Create parameter set with default parameters
        parameter_values = pybamm.ParameterValues("Marquis2019")
        
        # Modify capacity and other parameters
        parameter_values.update({
            "Nominal cell capacity [A.h]": self.capacity,
            "Initial concentration in negative electrode [mol.m-3]": 
                parameter_values["Maximum concentration in negative electrode [mol.m-3]"] * self.initial_soc,
            "Initial concentration in positive electrode [mol.m-3]": 
                parameter_values["Maximum concentration in positive electrode [mol.m-3]"] * (1 - self.initial_soc),
            "Initial temperature [K]": 298.15,  # 25°C
        })
        
        if experiment is None:
            # Default experiment: discharge at 1C rate with smaller time steps
            c_rate = 1
            experiment = pybamm.Experiment(
                [
                    "Discharge at {}C until 2.5V".format(c_rate),
                    "Rest for 30 minutes",
                ],
                period="10 seconds"  # Reduced from 30 seconds to improve convergence
            )
        
        # Create simulation using the Simulation class with solver options for better convergence
        solver = pybamm.CasadiSolver(mode="safe", dt_max=60.0)  # Reduced dt_max from default 600
        self.simulation = pybamm.Simulation(
            model, 
            experiment=experiment,
            parameter_values=parameter_values,
            solver=solver
        )
        
        return self.simulation
    
    def run_simulation(self, t_eval=None):
        """
        Run the battery simulation.
        
        Args:
            t_eval (array-like, optional): Times at which to evaluate the solution.
                If None, the simulation's default timesteps will be used.
        
        Returns:
            pybamm.Solution: Solution object containing simulation results
        """
        if self.simulation is None:
            self.create_simulation()
        
        try:
            # Try to solve with the DFN model
            self.solution = self.simulation.solve(t_eval=t_eval)
            
            # Extract and store key data
            self.time_data = self.solution["Time [h]"].entries
            self.voltage_data = self.solution["Terminal voltage [V]"].entries
            self.current_data = self.solution["Current [A]"].entries
            self.soc_data = self.solution["State of Charge"].entries
            self.temperature_data = self.solution["X-averaged cell temperature [K]"].entries
            
            # Update current state
            self.current_soc = self.soc_data[-1]
            self.current_voltage = self.voltage_data[-1]
            self.current_temperature = self.temperature_data[-1]
            
            return self.solution
            
        except pybamm.SolverError as e:
            print(f"Solver error: {e}")
            print("Trying with simplified SPM model instead...")
            
            # Fall back to simpler SPM model if DFN fails
            model = pybamm.lithium_ion.SPM()
            parameter_values = pybamm.ParameterValues("Marquis2019")
            parameter_values.update({
                "Nominal cell capacity [A.h]": self.capacity,
                "Initial concentration in negative electrode [mol.m-3]": 
                    parameter_values["Maximum concentration in negative electrode [mol.m-3]"] * self.initial_soc,
                "Initial concentration in positive electrode [mol.m-3]": 
                    parameter_values["Maximum concentration in positive electrode [mol.m-3]"] * (1 - self.initial_soc),
                "Initial temperature [K]": 298.15,  # 25°C
            })
            
            # Create a simpler experiment
            experiment = pybamm.Experiment(
                ["Discharge at 1C until 2.5V"],
                period="10 seconds"
            )
            
            # Use safer solver settings
            solver = pybamm.CasadiSolver(mode="safe", dt_max=30.0)
            self.simulation = pybamm.Simulation(
                model, 
                experiment=experiment,
                parameter_values=parameter_values,
                solver=solver
            )
            
            self.solution = self.simulation.solve(t_eval=t_eval)
            
            # Extract and store key data
            self.time_data = self.solution["Time [h]"].entries
            self.voltage_data = self.solution["Terminal voltage [V]"].entries
            self.current_data = self.solution["Current [A]"].entries
            self.soc_data = self.solution["State of Charge"].entries
            self.temperature_data = self.solution["X-averaged cell temperature [K]"].entries
            
            # Update current state
            self.current_soc = self.soc_data[-1]
            self.current_voltage = self.voltage_data[-1]
            self.current_temperature = self.temperature_data[-1]
            
            return self.solution
    
    def apply_current(self, current, duration, dt=1.0):
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
        # Create experiment with constant current
        experiment = pybamm.Experiment(
            [f"Discharge at {abs(current)/self.capacity}C for {duration} seconds"],
            period=f"{dt} seconds"
        ) if current > 0 else pybamm.Experiment(
            [f"Charge at {abs(current)/self.capacity}C for {duration} seconds"],
            period=f"{dt} seconds"
        )
        
        # Create and run simulation
        self.create_simulation(experiment)
        self.run_simulation()
        
        # Return key results
        return {
            "time": self.time_data,
            "voltage": self.voltage_data,
            "current": self.current_data,
            "soc": self.soc_data,
            "temperature": self.temperature_data
        }
    
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
        if self.solution is None:
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
    battery = BatteryDFNModel(initial_soc=0.8, capacity=50.0, nominal_voltage=3.7)
    
    # Create and run simulation
    battery.create_simulation()
    battery.run_simulation()
    
    # Plot results
    fig, axes = battery.plot_results()
    plt.savefig("battery_simulation_results.png")
    plt.close(fig)
    
    # Test applying current
    print("Testing battery discharge...")
    results = battery.apply_current(current=25.0, duration=1800)  # 25A for 30 minutes
    
    print(f"Final SOC: {battery.current_soc:.2f}")
    print(f"Final Voltage: {battery.current_voltage:.2f} V")
    print(f"Final Temperature: {battery.current_temperature - 273.15:.2f} °C")
    
    return battery


if __name__ == "__main__":
    test_battery_model()

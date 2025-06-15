"""
Real-time Simulation Interface for Electric Vehicle Digital Twin
---------------------------------------------------------------
This module provides a real-time simulation interface for the EV digital twin,
allowing interactive control and visualization of the simulation.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Slider, Button
import time
import threading
import pandas as pd
from integration.ev_digital_twin import ElectricVehicleDigitalTwin


class RealTimeEVSimulation:
    """
    Real-time simulation interface for the Electric Vehicle Digital Twin.
    
    This class provides methods to:
    - Run the EV simulation in real-time
    - Visualize simulation results with live updates
    - Control simulation parameters interactively
    - Export simulation data to CSV
    """
    
    def __init__(self, ev_model=None):
        """
        Initialize the real-time simulation interface.
        
        Args:
            ev_model (ElectricVehicleDigitalTwin, optional): EV digital twin model.
                If None, a default model will be created.
        """
        # Initialize EV model
        if ev_model is None:
            self.ev = ElectricVehicleDigitalTwin(
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
        else:
            self.ev = ev_model
        
        # Simulation parameters
        self.dt = 0.1  # Time step in seconds
        self.max_time = 300  # Maximum simulation time in seconds
        self.current_time = 0  # Current simulation time
        self.target_speed = 0  # Target speed in m/s
        self.max_speed = 40  # Maximum speed in m/s (144 km/h)
        self.acceleration_rate = 3.0  # Default acceleration rate in m/s²
        self.deceleration_rate = 5.0  # Default deceleration rate in m/s²
        
        # Simulation control
        self.running = False
        self.paused = False
        self.simulation_thread = None
        
        # Initialize data storage
        self.time_data = []
        self.speed_data = []
        self.battery_soc_data = []
        self.motor_power_data = []
        self.distance_data = []
        
        # Initialize plot
        self.fig = None
        self.axes = None
        self.lines = None
        self.animation = None
        
        print("Real-time EV simulation interface initialized")
    
    def _speed_profile(self, t):
        """
        Speed profile function for the simulation.
        
        Args:
            t (float): Current time in seconds
        
        Returns:
            float: Target speed in m/s
        """
        return self.target_speed
    
    def _simulation_loop(self):
        """
        Main simulation loop that runs in a separate thread.
        """
        self.current_time = 0
        self.time_data = []
        self.speed_data = []
        self.battery_soc_data = []
        self.motor_power_data = []
        self.distance_data = []
        
        # Reset EV model
        self.ev.current_speed = 0.0
        self.ev.current_acceleration = 0.0
        self.ev.current_distance = 0.0
        self.ev.current_power_demand = 0.0
        
        while self.running and self.current_time < self.max_time:
            if not self.paused:
                # Run one simulation step
                results = self.ev.simulate(self._speed_profile, duration=self.dt, dt=self.dt)
                
                # Update current time
                self.current_time += self.dt
                
                # Store data
                self.time_data.append(self.current_time)
                self.speed_data.append(results["speed"][-1])
                self.battery_soc_data.append(results["battery_soc"][-1])
                self.motor_power_data.append(results["power_demand"][-1])
                self.distance_data.append(results["distance"][-1])
            
            # Sleep to maintain real-time simulation
            time.sleep(self.dt * 0.5)  # Sleep for half the time step to allow for computation
    
    def start_simulation(self):
        """
        Start the real-time simulation in a separate thread.
        """
        if not self.running:
            self.running = True
            self.paused = False
            self.simulation_thread = threading.Thread(target=self._simulation_loop)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
            print("Simulation started")
    
    def pause_simulation(self):
        """
        Pause the simulation.
        """
        self.paused = True
        print("Simulation paused")
    
    def resume_simulation(self):
        """
        Resume the paused simulation.
        """
        self.paused = False
        print("Simulation resumed")
    
    def stop_simulation(self):
        """
        Stop the simulation.
        """
        self.running = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=1.0)
        print("Simulation stopped")
    
    def set_target_speed(self, speed):
        """
        Set the target speed for the simulation.
        
        Args:
            speed (float): Target speed in m/s
        """
        self.target_speed = min(max(0, speed), self.max_speed)
        print(f"Target speed set to {self.target_speed:.1f} m/s ({self.target_speed * 3.6:.1f} km/h)")
    
    def accelerate(self, amount=None):
        """
        Increase the target speed.
        
        Args:
            amount (float, optional): Amount to increase speed by in m/s.
                If None, use the default acceleration rate * dt.
        """
        if amount is None:
            amount = self.acceleration_rate * self.dt
        self.set_target_speed(self.target_speed + amount)
    
    def decelerate(self, amount=None):
        """
        Decrease the target speed.
        
        Args:
            amount (float, optional): Amount to decrease speed by in m/s.
                If None, use the default deceleration rate * dt.
        """
        if amount is None:
            amount = self.deceleration_rate * self.dt
        self.set_target_speed(self.target_speed - amount)
    
    def _init_animation(self):
        """
        Initialize the animation plot.
        """
        # Create empty data
        if len(self.time_data) == 0:
            self.time_data = [0]
            self.speed_data = [0]
            self.battery_soc_data = [1.0]
            self.motor_power_data = [0]
            self.distance_data = [0]
        
        # Create figure and axes
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.suptitle("Electric Vehicle Digital Twin - Real-time Simulation", fontsize=16)
        
        # Speed plot
        self.lines = {}
        self.lines["speed"], = self.axes[0, 0].plot(self.time_data, self.speed_data, 'b-')
        self.axes[0, 0].set_xlabel("Time [s]")
        self.axes[0, 0].set_ylabel("Speed [m/s]")
        self.axes[0, 0].set_title("Vehicle Speed")
        self.axes[0, 0].set_xlim(0, self.max_time)
        self.axes[0, 0].set_ylim(0, self.max_speed * 1.1)
        self.axes[0, 0].grid(True)
        
        # Battery SOC plot
        self.lines["soc"], = self.axes[0, 1].plot(self.time_data, self.battery_soc_data, 'g-')
        self.axes[0, 1].set_xlabel("Time [s]")
        self.axes[0, 1].set_ylabel("State of Charge")
        self.axes[0, 1].set_title("Battery SOC")
        self.axes[0, 1].set_xlim(0, self.max_time)
        self.axes[0, 1].set_ylim(0, 1.0)
        self.axes[0, 1].grid(True)
        
        # Power plot
        self.lines["power"], = self.axes[1, 0].plot(self.time_data, self.motor_power_data, 'r-')
        self.axes[1, 0].set_xlabel("Time [s]")
        self.axes[1, 0].set_ylabel("Power [kW]")
        self.axes[1, 0].set_title("Motor Power")
        self.axes[1, 0].set_xlim(0, self.max_time)
        self.axes[1, 0].set_ylim(-50, 200)
        self.axes[1, 0].grid(True)
        
        # Distance plot
        self.lines["distance"], = self.axes[1, 1].plot(self.time_data, self.distance_data, 'm-')
        self.axes[1, 1].set_xlabel("Time [s]")
        self.axes[1, 1].set_ylabel("Distance [km]")
        self.axes[1, 1].set_title("Distance Traveled")
        self.axes[1, 1].set_xlim(0, self.max_time)
        self.axes[1, 1].set_ylim(0, 10)
        self.axes[1, 1].grid(True)
        
        # Add sliders and buttons
        plt.subplots_adjust(bottom=0.25)
        
        # Speed slider
        ax_speed = plt.axes([0.25, 0.15, 0.65, 0.03])
        self.speed_slider = Slider(
            ax=ax_speed,
            label='Target Speed [m/s]',
            valmin=0,
            valmax=self.max_speed,
            valinit=self.target_speed,
        )
        self.speed_slider.on_changed(self._update_speed)
        
        # Buttons
        ax_start = plt.axes([0.25, 0.05, 0.15, 0.05])
        ax_pause = plt.axes([0.45, 0.05, 0.15, 0.05])
        ax_stop = plt.axes([0.65, 0.05, 0.15, 0.05])
        
        self.start_button = Button(ax_start, 'Start')
        self.pause_button = Button(ax_pause, 'Pause/Resume')
        self.stop_button = Button(ax_stop, 'Stop')
        
        self.start_button.on_clicked(self._on_start)
        self.pause_button.on_clicked(self._on_pause)
        self.stop_button.on_clicked(self._on_stop)
        
        plt.tight_layout(rect=[0, 0.25, 1, 1])
        
        return self.lines.values()
    
    def _update_animation(self, frame):
        """
        Update the animation plot.
        
        Args:
            frame (int): Animation frame number
        
        Returns:
            list: Updated line objects
        """
        if len(self.time_data) > 0:
            # Update line data
            self.lines["speed"].set_data(self.time_data, self.speed_data)
            self.lines["soc"].set_data(self.time_data, self.battery_soc_data)
            self.lines["power"].set_data(self.time_data, self.motor_power_data)
            
            # Convert distance to km
            distance_km = [d / 1000 for d in self.distance_data]
            self.lines["distance"].set_data(self.time_data, distance_km)
            
            # Update x-axis limits if needed
            if self.current_time > self.axes[0, 0].get_xlim()[1]:
                for ax in self.axes.flat:
                    ax.set_xlim(0, self.current_time * 1.5)
            
            # Update y-axis limits if needed
            max_power = max(self.motor_power_data) if self.motor_power_data else 0
            if max_power > self.axes[1, 0].get_ylim()[1]:
                self.axes[1, 0].set_ylim(-50, max_power * 1.2)
            
            max_distance = max(distance_km) if distance_km else 0
            if max_distance > self.axes[1, 1].get_ylim()[1]:
                self.axes[1, 1].set_ylim(0, max_distance * 1.2)
        
        return self.lines.values()
    
    def _update_speed(self, val):
        """
        Update the target speed from the slider.
        
        Args:
            val (float): New target speed value
        """
        self.set_target_speed(val)
    
    def _on_start(self, event):
        """
        Handle start button click.
        
        Args:
            event: Button click event
        """
        self.start_simulation()
    
    def _on_pause(self, event):
        """
        Handle pause/resume button click.
        
        Args:
            event: Button click event
        """
        if self.paused:
            self.resume_simulation()
        else:
            self.pause_simulation()
    
    def _on_stop(self, event):
        """
        Handle stop button click.
        
        Args:
            event: Button click event
        """
        self.stop_simulation()
    
    def run_interactive_simulation(self):
        """
        Run the interactive simulation with real-time visualization.
        """
        # Initialize animation
        self._init_animation()
        
        # Create animation
        self.animation = animation.FuncAnimation(
            self.fig,
            self._update_animation,
            interval=100,  # Update every 100 ms
            blit=True
        )
        
        # Show plot
        plt.show()
        
        # Clean up after plot is closed
        self.stop_simulation()
    
    def export_to_csv(self, filename="real_time_simulation_results.csv"):
        """
        Export simulation results to CSV file.
        
        Args:
            filename (str): Output CSV filename
        """
        if len(self.time_data) == 0:
            print("No simulation data to export")
            return
        
        # Create DataFrame
        data = {
            "Time (s)": self.time_data,
            "Speed (m/s)": self.speed_data,
            "Battery SOC": self.battery_soc_data,
            "Power (kW)": self.motor_power_data,
            "Distance (m)": self.distance_data
        }
        
        df = pd.DataFrame(data)
        
        # Save to CSV
        df.to_csv(filename, index=False)
        
        print(f"Simulation results exported to {filename}")


def run_real_time_simulation():
    """
    Run the real-time EV simulation interface.
    """
    # Create EV model
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
    
    # Create real-time simulation interface
    sim = RealTimeEVSimulation(ev)
    
    # Run interactive simulation
    print("Starting interactive EV simulation...")
    print("Use the slider to control the target speed")
    print("Use the buttons to start, pause/resume, and stop the simulation")
    
    sim.run_interactive_simulation()
    
    # Export results
    sim.export_to_csv()
    
    return sim


if __name__ == "__main__":
    run_real_time_simulation()

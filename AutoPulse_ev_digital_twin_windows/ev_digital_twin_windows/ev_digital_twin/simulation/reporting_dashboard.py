"""
Reporting Dashboard for Electric Vehicle Digital Twin
----------------------------------------------------
This module provides a reporting dashboard for the EV digital twin simulation results.
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import time
from datetime import datetime
import json
from matplotlib.gridspec import GridSpec


class EVReportingDashboard:
    """
    Reporting dashboard for Electric Vehicle Digital Twin simulation results.
    
    This class provides methods to:
    - Load simulation results from CSV files
    - Generate comprehensive reports and visualizations
    - Compare multiple simulation runs
    - Track vehicle and component performance over time
    - Visualize RUL predictions and health status
    """
    
    def __init__(self, data_dir="./data_export"):
        """
        Initialize the reporting dashboard.
        
        Args:
            data_dir (str): Directory containing simulation data files
        """
        self.data_dir = data_dir
        self.simulation_data = {}
        self.simulation_metadata = {}
        self.current_simulation_id = None
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing simulation data
        self._load_existing_simulations()
        
        print(f"EV Reporting Dashboard initialized. Found {len(self.simulation_data)} existing simulations.")
    
    def _load_existing_simulations(self):
        """
        Load existing simulation data from the data directory.
        """
        # Check for metadata file
        metadata_file = os.path.join(self.data_dir, "simulation_metadata.json")
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    self.simulation_metadata = json.load(f)
            except Exception as e:
                print(f"Error loading metadata: {e}")
                self.simulation_metadata = {}
        
        # Look for CSV files
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".csv") and "simulation_results" in filename:
                sim_id = filename.split("_results")[0]
                if sim_id not in self.simulation_data:
                    try:
                        file_path = os.path.join(self.data_dir, filename)
                        self.simulation_data[sim_id] = pd.read_csv(file_path)
                        
                        # Add metadata if not present
                        if sim_id not in self.simulation_metadata:
                            self.simulation_metadata[sim_id] = {
                                "timestamp": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M:%S"),
                                "description": f"Simulation {sim_id}",
                                "file": filename
                            }
                    except Exception as e:
                        print(f"Error loading {filename}: {e}")
    
    def _save_metadata(self):
        """
        Save simulation metadata to file.
        """
        metadata_file = os.path.join(self.data_dir, "simulation_metadata.json")
        try:
            with open(metadata_file, 'w') as f:
                json.dump(self.simulation_metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving metadata: {e}")
    
    def load_simulation(self, file_path, description=None):
        """
        Load simulation results from a CSV file.
        
        Args:
            file_path (str): Path to the CSV file
            description (str, optional): Description of the simulation
        
        Returns:
            str: Simulation ID
        """
        try:
            # Load data
            data = pd.read_csv(file_path)
            
            # Generate simulation ID
            sim_id = f"sim_{int(time.time())}"
            
            # Store data
            self.simulation_data[sim_id] = data
            
            # Store metadata
            self.simulation_metadata[sim_id] = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "description": description or f"Simulation {sim_id}",
                "file": os.path.basename(file_path)
            }
            
            # Save metadata
            self._save_metadata()
            
            # Set as current simulation
            self.current_simulation_id = sim_id
            
            print(f"Loaded simulation {sim_id}: {self.simulation_metadata[sim_id]['description']}")
            return sim_id
        
        except Exception as e:
            print(f"Error loading simulation: {e}")
            return None
    
    def add_simulation_result(self, data, description=None):
        """
        Add simulation results directly from data.
        
        Args:
            data (dict or DataFrame): Simulation results
            description (str, optional): Description of the simulation
        
        Returns:
            str: Simulation ID
        """
        try:
            # Convert dict to DataFrame if necessary
            if isinstance(data, dict):
                df = pd.DataFrame(data)
            else:
                df = data
            
            # Generate simulation ID
            sim_id = f"sim_{int(time.time())}"
            
            # Store data
            self.simulation_data[sim_id] = df
            
            # Store metadata
            self.simulation_metadata[sim_id] = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "description": description or f"Simulation {sim_id}",
                "file": f"{sim_id}_results.csv"
            }
            
            # Save data to file
            file_path = os.path.join(self.data_dir, f"{sim_id}_results.csv")
            df.to_csv(file_path, index=False)
            
            # Save metadata
            self._save_metadata()
            
            # Set as current simulation
            self.current_simulation_id = sim_id
            
            print(f"Added simulation {sim_id}: {self.simulation_metadata[sim_id]['description']}")
            return sim_id
        
        except Exception as e:
            print(f"Error adding simulation: {e}")
            return None
    
    def list_simulations(self):
        """
        List all available simulations.
        
        Returns:
            DataFrame: Table of simulations with metadata
        """
        data = []
        for sim_id, metadata in self.simulation_metadata.items():
            row = {
                "Simulation ID": sim_id,
                "Timestamp": metadata["timestamp"],
                "Description": metadata["description"],
                "File": metadata["file"]
            }
            
            # Add summary statistics if available
            if sim_id in self.simulation_data:
                df = self.simulation_data[sim_id]
                if "Distance (km)" in df.columns:
                    row["Distance (km)"] = df["Distance (km)"].iloc[-1]
                if "Energy Consumption (kWh)" in df.columns:
                    row["Energy (kWh)"] = df["Energy Consumption (kWh)"].iloc[-1]
                if "Battery SOC" in df.columns:
                    row["Final SOC"] = f"{df['Battery SOC'].iloc[-1]*100:.1f}%"
                if "Time (s)" in df.columns:
                    row["Duration (s)"] = df["Time (s)"].iloc[-1]
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    def set_current_simulation(self, sim_id):
        """
        Set the current simulation for reporting.
        
        Args:
            sim_id (str): Simulation ID
        
        Returns:
            bool: Success flag
        """
        if sim_id in self.simulation_data:
            self.current_simulation_id = sim_id
            print(f"Current simulation set to {sim_id}: {self.simulation_metadata[sim_id]['description']}")
            return True
        else:
            print(f"Simulation {sim_id} not found")
            return False
    
    def get_simulation_summary(self, sim_id=None):
        """
        Get a summary of the simulation results.
        
        Args:
            sim_id (str, optional): Simulation ID. If None, use current simulation.
        
        Returns:
            dict: Summary statistics
        """
        # Use current simulation if not specified
        if sim_id is None:
            sim_id = self.current_simulation_id
        
        if sim_id not in self.simulation_data:
            print(f"Simulation {sim_id} not found")
            return None
        
        df = self.simulation_data[sim_id]
        
        # Calculate summary statistics
        summary = {
            "simulation_id": sim_id,
            "description": self.simulation_metadata[sim_id]["description"],
            "timestamp": self.simulation_metadata[sim_id]["timestamp"]
        }
        
        # Time and distance
        if "Time (s)" in df.columns:
            summary["duration_seconds"] = df["Time (s)"].iloc[-1]
        if "Time (mm:ss)" in df.columns:
            summary["duration_formatted"] = df["Time (mm:ss)"].iloc[-1]
        if "Distance (m)" in df.columns:
            summary["distance_m"] = df["Distance (m)"].iloc[-1]
            summary["distance_km"] = df["Distance (m)"].iloc[-1] / 1000
        
        # Speed and acceleration
        if "Speed (m/s)" in df.columns:
            summary["max_speed_ms"] = df["Speed (m/s)"].max()
            summary["avg_speed_ms"] = df["Speed (m/s)"].mean()
        if "Speed (km/h)" in df.columns:
            summary["max_speed_kmh"] = df["Speed (km/h)"].max()
            summary["avg_speed_kmh"] = df["Speed (km/h)"].mean()
        if "Acceleration (m/s²)" in df.columns:
            summary["max_acceleration"] = df["Acceleration (m/s²)"].max()
            summary["max_deceleration"] = df["Acceleration (m/s²)"].min()
        
        # Power and energy
        if "Power Demand (kW)" in df.columns:
            summary["max_power_kw"] = df["Power Demand (kW)"].max()
            summary["avg_power_kw"] = df.loc[df["Power Demand (kW)"] > 0, "Power Demand (kW)"].mean()
        if "Energy Consumption (kWh)" in df.columns:
            summary["energy_consumption_kwh"] = df["Energy Consumption (kWh)"].iloc[-1]
        if "Energy Efficiency (kWh/km)" in df.columns:
            summary["energy_efficiency_kwh_km"] = df["Energy Efficiency (kWh/km)"].iloc[-1]
        
        # Battery
        if "Battery SOC" in df.columns:
            summary["initial_soc"] = df["Battery SOC"].iloc[0]
            summary["final_soc"] = df["Battery SOC"].iloc[-1]
            summary["soc_change"] = summary["initial_soc"] - summary["final_soc"]
        if "Battery Temperature (°C)" in df.columns:
            summary["min_battery_temp_c"] = df["Battery Temperature (°C)"].min()
            summary["max_battery_temp_c"] = df["Battery Temperature (°C)"].max()
            summary["avg_battery_temp_c"] = df["Battery Temperature (°C)"].mean()
        if "Battery SOH" in df.columns:
            summary["battery_soh"] = df["Battery SOH"].iloc[-1]
        if "Battery RUL (cycles)" in df.columns:
            summary["battery_rul_cycles"] = df["Battery RUL (cycles)"].iloc[-1]
        
        # Motor
        if "Motor Speed (rpm)" in df.columns:
            summary["max_motor_speed_rpm"] = df["Motor Speed (rpm)"].max()
        if "Motor Torque (Nm)" in df.columns:
            summary["max_motor_torque_nm"] = df["Motor Torque (Nm)"].max()
        if "Motor Efficiency" in df.columns:
            summary["avg_motor_efficiency"] = df["Motor Efficiency"].mean()
        if "Motor Temperature (°C)" in df.columns:
            summary["min_motor_temp_c"] = df["Motor Temperature (°C)"].min()
            summary["max_motor_temp_c"] = df["Motor Temperature (°C)"].max()
            summary["avg_motor_temp_c"] = df["Motor Temperature (°C)"].mean()
        if "Motor Health" in df.columns:
            summary["motor_health"] = df["Motor Health"].iloc[-1]
        if "Motor RUL (hours)" in df.columns:
            summary["motor_rul_hours"] = df["Motor RUL (hours)"].iloc[-1]
        
        return summary
    
    def generate_dashboard(self, sim_id=None, output_file="ev_dashboard.png"):
        """
        Generate a comprehensive dashboard visualization of the simulation results.
        
        Args:
            sim_id (str, optional): Simulation ID. If None, use current simulation.
            output_file (str): Output file path for the dashboard image
        
        Returns:
            tuple: Matplotlib figure and axes objects
        """
        # Use current simulation if not specified
        if sim_id is None:
            sim_id = self.current_simulation_id
        
        if sim_id not in self.simulation_data:
            print(f"Simulation {sim_id} not found")
            return None
        
        df = self.simulation_data[sim_id]
        summary = self.get_simulation_summary(sim_id)
        
        # Create figure
        fig = plt.figure(figsize=(20, 24))
        gs = GridSpec(12, 6, figure=fig)
        
        # Title and summary
        ax_title = fig.add_subplot(gs[0, :])
        ax_title.axis('off')
        title_text = f"Electric Vehicle Digital Twin - Simulation Dashboard\n"
        title_text += f"Simulation: {summary['description']} ({summary['timestamp']})"
        ax_title.text(0.5, 0.5, title_text, ha='center', va='center', fontsize=20, fontweight='bold')
        
        # Summary statistics
        ax_summary = fig.add_subplot(gs[1, :3])
        ax_summary.axis('off')
        
        summary_text = "Summary Statistics:\n\n"
        summary_text += f"Duration: {summary.get('duration_formatted', 'N/A')} ({summary.get('duration_seconds', 'N/A'):.1f} s)\n"
        summary_text += f"Distance: {summary.get('distance_km', 'N/A'):.2f} km\n"
        summary_text += f"Max Speed: {summary.get('max_speed_kmh', 'N/A'):.1f} km/h\n"
        summary_text += f"Avg Speed: {summary.get('avg_speed_kmh', 'N/A'):.1f} km/h\n"
        summary_text += f"Max Acceleration: {summary.get('max_acceleration', 'N/A'):.2f} m/s²\n"
        summary_text += f"Max Deceleration: {summary.get('max_deceleration', 'N/A'):.2f} m/s²\n"
        summary_text += f"Energy Consumption: {summary.get('energy_consumption_kwh', 'N/A'):.2f} kWh\n"
        summary_text += f"Energy Efficiency: {summary.get('energy_efficiency_kwh_km', 'N/A'):.2f} kWh/km\n"
        
        ax_summary.text(0.05, 0.95, summary_text, ha='left', va='top', fontsize=12, linespacing=1.5)
        
        # Battery and motor status
        ax_status = fig.add_subplot(gs[1, 3:])
        ax_status.axis('off')
        
        status_text = "Component Status:\n\n"
        status_text += f"Battery SOC: {summary.get('initial_soc', 'N/A')*100:.1f}% → {summary.get('final_soc', 'N/A')*100:.1f}% (Δ {summary.get('soc_change', 'N/A')*100:.1f}%)\n"
        status_text += f"Battery SOH: {summary.get('battery_soh', 'N/A')*100:.1f}%\n"
        status_text += f"Battery RUL: {summary.get('battery_rul_cycles', 'N/A'):.1f} cycles\n"
        status_text += f"Battery Temp: {summary.get('max_battery_temp_c', 'N/A'):.1f}°C max\n"
        status_text += f"Motor Health: {summary.get('motor_health', 'N/A')*100:.1f}%\n"
        status_text += f"Motor RUL: {summary.get('motor_rul_hours', 'N/A'):.1f} hours\n"
        status_text += f"Motor Temp: {summary.get('max_motor_temp_c', 'N/A'):.1f}°C max\n"
        status_text += f"Motor Efficiency: {summary.get('avg_motor_efficiency', 'N/A')*100:.1f}% avg\n"
        
        ax_status.text(0.05, 0.95, status_text, ha='left', va='top', fontsize=12, linespacing=1.5)
        
        # Speed and distance plot
        ax_speed = fig.add_subplot(gs[2:4, :3])
        if "Time (min)" in df.columns and "Speed (km/h)" in df.columns:
            ax_speed.plot(df["Time (min)"], df["Speed (km/h)"], 'b-', label='Speed')
            ax_speed.set_xlabel("Time [min]")
            ax_speed.set_ylabel("Speed [km/h]", color='b')
            ax_speed.tick_params(axis='y', labelcolor='b')
            
            ax_dist = ax_speed.twinx()
            if "Distance (km)" in df.columns:
                ax_dist.plot(df["Time (min)"], df["Distance (km)"], 'r-', label='Distance')
                ax_dist.set_ylabel("Distance [km]", color='r')
                ax_dist.tick_params(axis='y', labelcolor='r')
            
            ax_speed.set_title("Vehicle Speed and Distance")
            ax_speed.grid(True)
            
            # Add legend
            lines1, labels1 = ax_speed.get_legend_handles_labels()
            lines2, labels2 = ax_dist.get_legend_handles_labels()
            ax_speed.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Battery SOC and temperature plot
        ax_soc = fig.add_subplot(gs[2:4, 3:])
        if "Time (min)" in df.columns and "Battery SOC" in df.columns:
            ax_soc.plot(df["Time (min)"], df["Battery SOC"] * 100, 'g-', label='SOC')
            ax_soc.set_xlabel("Time [min]")
            ax_soc.set_ylabel("SOC [%]", color='g')
            ax_soc.tick_params(axis='y', labelcolor='g')
            
            ax_temp = ax_soc.twinx()
            if "Battery Temperature (°C)" in df.columns:
                ax_temp.plot(df["Time (min)"], df["Battery Temperature (°C)"], 'r-', label='Temperature')
                ax_temp.set_ylabel("Temperature [°C]", color='r')
                ax_temp.tick_params(axis='y', labelcolor='r')
            
            ax_soc.set_title("Battery State of Charge and Temperature")
            ax_soc.grid(True)
            
            # Add legend
            lines1, labels1 = ax_soc.get_legend_handles_labels()
            lines2, labels2 = ax_temp.get_legend_handles_labels()
            ax_soc.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        # Power and energy plot
        ax_power = fig.add_subplot(gs[4:6, :3])
        if "Time (min)" in df.columns and "Power Demand (kW)" in df.columns:
            ax_power.plot(df["Time (min)"], df["Power Demand (kW)"], 'b-', label='Power')
            ax_power.set_xlabel("Time [min]")
            ax_power.set_ylabel("Power [kW]", color='b')
            ax_power.tick_params(axis='y', labelcolor='b')
            
            ax_energy = ax_power.twinx()
            if "Energy Consumption (kWh)" in df.columns:
                ax_energy.plot(df["Time (min)"], df["Energy Consumption (kWh)"], 'g-', label='Energy')
                ax_energy.set_ylabel("Energy [kWh]", color='g')
                ax_energy.tick_params(axis='y', labelcolor='g')
            
            ax_power.set_title("Power Demand and Energy Consumption")
            ax_power.grid(True)
            
            # Add legend
            lines1, labels1 = ax_power.get_legend_handles_labels()
            lines2, labels2 = ax_energy.get_legend_handles_labels()
            ax_power.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # Motor torque and speed plot
        ax_torque = fig.add_subplot(gs[4:6, 3:])
        if "Time (min)" in df.columns and "Motor Torque (Nm)" in df.columns:
            ax_torque.plot(df["Time (min)"], df["Motor Torque (Nm)"], 'b-', label='Torque')
            ax_torque.set_xlabel("Time [min]")
            ax_torque.set_ylabel("Torque [Nm]", color='b')
            ax_torque.tick_params(axis='y', labelcolor='b')
            
            ax_motor_speed = ax_torque.twinx()
            if "Motor Speed (rpm)" in df.columns:
                ax_motor_speed.plot(df["Time (min)"], df["Motor Speed (rpm)"], 'r-', label='Speed')
                ax_motor_speed.set_ylabel("Speed [rpm]", color='r')
                ax_motor_speed.tick_params(axis='y', labelcolor='r')
            
            ax_torque.set_title("Motor Torque and Speed")
            ax_torque.grid(True)
            
            # Add legend
            lines1, labels1 = ax_torque.get_legend_handles_labels()
            lines2, labels2 = ax_motor_speed.get_legend_handles_labels()
            ax_torque.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        # Component temperatures plot
        ax_temps = fig.add_subplot(gs[6:8, :3])
        if "Time (min)" in df.columns:
            if "Battery Temperature (°C)" in df.columns:
                ax_temps.plot(df["Time (min)"], df["Battery Temperature (°C)"], 'r-', label='Battery')
            if "Motor Temperature (°C)" in df.columns:
                ax_temps.plot(df["Time (min)"], df["Motor Temperature (°C)"], 'b-', label='Motor')
            
            ax_temps.set_xlabel("Time [min]")
            ax_temps.set_ylabel("Temperature [°C]")
            ax_temps.set_title("Component Temperatures")
            ax_temps.legend()
            ax_temps.grid(True)
        
        # Component health plot
        ax_health = fig.add_subplot(gs[6:8, 3:])
        if "Time (min)" in df.columns:
            if "Battery SOH" in df.columns:
                ax_health.plot(df["Time (min)"], df["Battery SOH"] * 100, 'g-', label='Battery SOH')
            if "Motor Health" in df.columns:
                ax_health.plot(df["Time (min)"], df["Motor Health"] * 100, 'b-', label='Motor Health')
            
            ax_health.set_xlabel("Time [min]")
            ax_health.set_ylabel("Health [%]")
            ax_health.set_title("Component Health")
            ax_health.legend()
            ax_health.grid(True)
        
        # RUL plot
        ax_rul = fig.add_subplot(gs[8:10, :])
        if "Time (min)" in df.columns:
            if "Battery RUL (cycles)" in df.columns:
                ax_rul.plot(df["Time (min)"], df["Battery RUL (cycles)"], 'g-', label='Battery RUL (cycles)')
            
            ax_rul2 = ax_rul.twinx()
            if "Motor RUL (hours)" in df.columns:
                ax_rul2.plot(df["Time (min)"], df["Motor RUL (hours)"], 'b-', label='Motor RUL (hours)')
                ax_rul2.set_ylabel("Motor RUL [hours]", color='b')
                ax_rul2.tick_params(axis='y', labelcolor='b')
            
            ax_rul.set_xlabel("Time [min]")
            ax_rul.set_ylabel("Battery RUL [cycles]", color='g')
            ax_rul.tick_params(axis='y', labelcolor='g')
            ax_rul.set_title("Remaining Useful Life (RUL)")
            ax_rul.grid(True)
            
            # Add legend
            lines1, labels1 = ax_rul.get_legend_handles_labels()
            lines2, labels2 = ax_rul2.get_legend_handles_labels()
            ax_rul.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        # Speed vs. power scatter plot
        ax_scatter = fig.add_subplot(gs[10:12, :3])
        if "Speed (km/h)" in df.columns and "Power Demand (kW)" in df.columns:
            scatter = ax_scatter.scatter(df["Speed (km/h)"], df["Power Demand (kW)"], 
                                        c=df["Time (min)"], cmap='viridis', alpha=0.7)
            ax_scatter.set_xlabel("Speed [km/h]")
            ax_scatter.set_ylabel("Power [kW]")
            ax_scatter.set_title("Speed vs. Power Relationship")
            ax_scatter.grid(True)
            
            # Add colorbar
            cbar = plt.colorbar(scatter, ax=ax_scatter)
            cbar.set_label('Time [min]')
        
        # Energy efficiency plot
        ax_efficiency = fig.add_subplot(gs[10:12, 3:])
        if "Time (min)" in df.columns and "Energy Efficiency (kWh/km)" in df.columns:
            ax_efficiency.plot(df["Time (min)"], df["Energy Efficiency (kWh/km)"], 'g-')
            ax_efficiency.set_xlabel("Time [min]")
            ax_efficiency.set_ylabel("Energy Efficiency [kWh/km]")
            ax_efficiency.set_title("Energy Efficiency")
            ax_efficiency.grid(True)
            
            # Add horizontal line for average efficiency
            if "energy_efficiency_kwh_km" in summary:
                ax_efficiency.axhline(y=summary["energy_efficiency_kwh_km"], color='r', linestyle='--', 
                                     label=f'Avg: {summary["energy_efficiency_kwh_km"]:.2f} kWh/km')
                ax_efficiency.legend()
        
        # Adjust layout
        plt.tight_layout()
        
        # Save figure
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        
        print(f"Dashboard generated and saved to {output_file}")
        return fig
    
    def compare_simulations(self, sim_ids, output_file="ev_comparison.png"):
        """
        Compare multiple simulations and generate a comparison dashboard.
        
        Args:
            sim_ids (list): List of simulation IDs to compare
            output_file (str): Output file path for the comparison dashboard
        
        Returns:
            tuple: Matplotlib figure and axes objects
        """
        # Validate simulation IDs
        valid_sim_ids = [sim_id for sim_id in sim_ids if sim_id in self.simulation_data]
        if len(valid_sim_ids) < 2:
            print("Need at least two valid simulations to compare")
            return None
        
        # Get data and summaries
        data_frames = [self.simulation_data[sim_id] for sim_id in valid_sim_ids]
        summaries = [self.get_simulation_summary(sim_id) for sim_id in valid_sim_ids]
        
        # Create figure
        fig = plt.figure(figsize=(20, 24))
        gs = GridSpec(12, 6, figure=fig)
        
        # Title
        ax_title = fig.add_subplot(gs[0, :])
        ax_title.axis('off')
        title_text = f"Electric Vehicle Digital Twin - Simulation Comparison\n"
        title_text += f"Comparing {len(valid_sim_ids)} simulations"
        ax_title.text(0.5, 0.5, title_text, ha='center', va='center', fontsize=20, fontweight='bold')
        
        # Summary comparison table
        ax_summary = fig.add_subplot(gs[1:3, :])
        ax_summary.axis('off')
        
        # Create comparison table data
        table_data = []
        metrics = [
            ("Description", "description", ""),
            ("Duration", "duration_seconds", "s"),
            ("Distance", "distance_km", "km"),
            ("Max Speed", "max_speed_kmh", "km/h"),
            ("Avg Speed", "avg_speed_kmh", "km/h"),
            ("Energy Consumption", "energy_consumption_kwh", "kWh"),
            ("Energy Efficiency", "energy_efficiency_kwh_km", "kWh/km"),
            ("Initial SOC", "initial_soc", "%"),
            ("Final SOC", "final_soc", "%"),
            ("Battery SOH", "battery_soh", "%"),
            ("Battery RUL", "battery_rul_cycles", "cycles"),
            ("Motor Health", "motor_health", "%"),
            ("Motor RUL", "motor_rul_hours", "hours")
        ]
        
        # Create header row
        header = ["Metric"]
        for i, sim_id in enumerate(valid_sim_ids):
            header.append(f"Sim {i+1}")
        table_data.append(header)
        
        # Add data rows
        for metric_name, metric_key, unit in metrics:
            row = [metric_name]
            for summary in summaries:
                if metric_key in summary:
                    value = summary[metric_key]
                    if metric_key in ["initial_soc", "final_soc", "battery_soh", "motor_health"]:
                        value = value * 100  # Convert to percentage
                    if isinstance(value, (int, float)):
                        if unit == "%":
                            row.append(f"{value:.1f}{unit}")
                        else:
                            row.append(f"{value:.2f}{unit}")
                    else:
                        row.append(str(value))
                else:
                    row.append("N/A")
            table_data.append(row)
        
        # Create table
        table = ax_summary.table(cellText=table_data, loc='center', cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)
        
        # Speed comparison
        ax_speed = fig.add_subplot(gs[3:5, :3])
        for i, (df, sim_id) in enumerate(zip(data_frames, valid_sim_ids)):
            if "Time (min)" in df.columns and "Speed (km/h)" in df.columns:
                ax_speed.plot(df["Time (min)"], df["Speed (km/h)"], label=f"Sim {i+1}")
        
        ax_speed.set_xlabel("Time [min]")
        ax_speed.set_ylabel("Speed [km/h]")
        ax_speed.set_title("Speed Comparison")
        ax_speed.legend()
        ax_speed.grid(True)
        
        # Battery SOC comparison
        ax_soc = fig.add_subplot(gs[3:5, 3:])
        for i, (df, sim_id) in enumerate(zip(data_frames, valid_sim_ids)):
            if "Time (min)" in df.columns and "Battery SOC" in df.columns:
                ax_soc.plot(df["Time (min)"], df["Battery SOC"] * 100, label=f"Sim {i+1}")
        
        ax_soc.set_xlabel("Time [min]")
        ax_soc.set_ylabel("SOC [%]")
        ax_soc.set_title("Battery SOC Comparison")
        ax_soc.legend()
        ax_soc.grid(True)
        
        # Power comparison
        ax_power = fig.add_subplot(gs[5:7, :3])
        for i, (df, sim_id) in enumerate(zip(data_frames, valid_sim_ids)):
            if "Time (min)" in df.columns and "Power Demand (kW)" in df.columns:
                ax_power.plot(df["Time (min)"], df["Power Demand (kW)"], label=f"Sim {i+1}")
        
        ax_power.set_xlabel("Time [min]")
        ax_power.set_ylabel("Power [kW]")
        ax_power.set_title("Power Demand Comparison")
        ax_power.legend()
        ax_power.grid(True)
        
        # Energy comparison
        ax_energy = fig.add_subplot(gs[5:7, 3:])
        for i, (df, sim_id) in enumerate(zip(data_frames, valid_sim_ids)):
            if "Time (min)" in df.columns and "Energy Consumption (kWh)" in df.columns:
                ax_energy.plot(df["Time (min)"], df["Energy Consumption (kWh)"], label=f"Sim {i+1}")
        
        ax_energy.set_xlabel("Time [min]")
        ax_energy.set_ylabel("Energy [kWh]")
        ax_energy.set_title("Energy Consumption Comparison")
        ax_energy.legend()
        ax_energy.grid(True)
        
        # Temperature comparison
        ax_temp = fig.add_subplot(gs[7:9, :3])
        for i, (df, sim_id) in enumerate(zip(data_frames, valid_sim_ids)):
            if "Time (min)" in df.columns and "Battery Temperature (°C)" in df.columns:
                ax_temp.plot(df["Time (min)"], df["Battery Temperature (°C)"], 
                            linestyle='-', label=f"Sim {i+1} Battery")
            if "Time (min)" in df.columns and "Motor Temperature (°C)" in df.columns:
                ax_temp.plot(df["Time (min)"], df["Motor Temperature (°C)"], 
                            linestyle='--', label=f"Sim {i+1} Motor")
        
        ax_temp.set_xlabel("Time [min]")
        ax_temp.set_ylabel("Temperature [°C]")
        ax_temp.set_title("Component Temperature Comparison")
        ax_temp.legend()
        ax_temp.grid(True)
        
        # Health comparison
        ax_health = fig.add_subplot(gs[7:9, 3:])
        for i, (df, sim_id) in enumerate(zip(data_frames, valid_sim_ids)):
            if "Time (min)" in df.columns and "Battery SOH" in df.columns:
                ax_health.plot(df["Time (min)"], df["Battery SOH"] * 100, 
                              linestyle='-', label=f"Sim {i+1} Battery")
            if "Time (min)" in df.columns and "Motor Health" in df.columns:
                ax_health.plot(df["Time (min)"], df["Motor Health"] * 100, 
                              linestyle='--', label=f"Sim {i+1} Motor")
        
        ax_health.set_xlabel("Time [min]")
        ax_health.set_ylabel("Health [%]")
        ax_health.set_title("Component Health Comparison")
        ax_health.legend()
        ax_health.grid(True)
        
        # Energy efficiency comparison
        ax_efficiency = fig.add_subplot(gs[9:11, :])
        for i, (df, sim_id) in enumerate(zip(data_frames, valid_sim_ids)):
            if "Time (min)" in df.columns and "Energy Efficiency (kWh/km)" in df.columns:
                ax_efficiency.plot(df["Time (min)"], df["Energy Efficiency (kWh/km)"], label=f"Sim {i+1}")
        
        ax_efficiency.set_xlabel("Time [min]")
        ax_efficiency.set_ylabel("Energy Efficiency [kWh/km]")
        ax_efficiency.set_title("Energy Efficiency Comparison")
        ax_efficiency.legend()
        ax_efficiency.grid(True)
        
        # Bar chart comparison of key metrics
        ax_bar = fig.add_subplot(gs[11:, :])
        
        # Prepare bar chart data
        bar_metrics = [
            ("Distance (km)", "distance_km"),
            ("Energy (kWh)", "energy_consumption_kwh"),
            ("Efficiency (kWh/km)", "energy_efficiency_kwh_km"),
            ("Avg Speed (km/h)", "avg_speed_kmh"),
            ("Battery RUL (cycles)", "battery_rul_cycles"),
            ("Motor RUL (hours)", "motor_rul_hours")
        ]
        
        bar_data = {metric_name: [] for metric_name, _ in bar_metrics}
        for summary in summaries:
            for metric_name, metric_key in bar_metrics:
                if metric_key in summary:
                    bar_data[metric_name].append(summary[metric_key])
                else:
                    bar_data[metric_name].append(0)
        
        # Create bar chart
        x = np.arange(len(bar_metrics))
        width = 0.8 / len(valid_sim_ids)
        
        for i, sim_id in enumerate(valid_sim_ids):
            values = [bar_data[metric_name][i] for metric_name, _ in bar_metrics]
            ax_bar.bar(x + i*width - 0.4 + width/2, values, width, label=f"Sim {i+1}")
        
        ax_bar.set_xticks(x)
        ax_bar.set_xticklabels([metric_name for metric_name, _ in bar_metrics])
        ax_bar.set_title("Key Metrics Comparison")
        ax_bar.legend()
        
        # Adjust layout
        plt.tight_layout()
        
        # Save figure
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        
        print(f"Comparison dashboard generated and saved to {output_file}")
        return fig
    
    def generate_report(self, sim_id=None, output_file="ev_simulation_report.md"):
        """
        Generate a comprehensive report of the simulation results.
        
        Args:
            sim_id (str, optional): Simulation ID. If None, use current simulation.
            output_file (str): Output report filename
        
        Returns:
            str: Report content
        """
        # Use current simulation if not specified
        if sim_id is None:
            sim_id = self.current_simulation_id
        
        if sim_id not in self.simulation_data:
            print(f"Simulation {sim_id} not found")
            return None
        
        # Get summary
        summary = self.get_simulation_summary(sim_id)
        
        # Create report
        report = f"""# Electric Vehicle Simulation Report

## Simulation Overview

- **Simulation ID**: {sim_id}
- **Description**: {summary['description']}
- **Timestamp**: {summary['timestamp']}
- **Duration**: {summary.get('duration_seconds', 'N/A'):.1f} seconds ({summary.get('duration_formatted', 'N/A')})
- **Distance Traveled**: {summary.get('distance_m', 'N/A'):.2f} m ({summary.get('distance_km', 'N/A'):.2f} km)
- **Energy Consumed**: {summary.get('energy_consumption_kwh', 'N/A'):.2f} kWh
- **Energy Efficiency**: {summary.get('energy_efficiency_kwh_km', 'N/A'):.2f} kWh/km

## Vehicle Performance

### Speed and Acceleration

- **Maximum Speed**: {summary.get('max_speed_ms', 'N/A'):.2f} m/s ({summary.get('max_speed_kmh', 'N/A'):.2f} km/h)
- **Average Speed**: {summary.get('avg_speed_ms', 'N/A'):.2f} m/s ({summary.get('avg_speed_kmh', 'N/A'):.2f} km/h)
- **Maximum Acceleration**: {summary.get('max_acceleration', 'N/A'):.2f} m/s²
- **Maximum Deceleration**: {summary.get('max_deceleration', 'N/A'):.2f} m/s²

### Power and Energy

- **Maximum Power Demand**: {summary.get('max_power_kw', 'N/A'):.2f} kW
- **Average Power Demand**: {summary.get('avg_power_kw', 'N/A'):.2f} kW

## Battery Status

### State of Charge

- **Initial SOC**: {summary.get('initial_soc', 'N/A')*100:.1f}%
- **Final SOC**: {summary.get('final_soc', 'N/A')*100:.1f}%
- **SOC Change**: {summary.get('soc_change', 'N/A')*100:.1f}%

### Battery Health

- **State of Health**: {summary.get('battery_soh', 'N/A')*100:.1f}%
- **Remaining Useful Life**: {summary.get('battery_rul_cycles', 'N/A'):.1f} cycles
- **Temperature Range**: {summary.get('min_battery_temp_c', 'N/A'):.1f}°C to {summary.get('max_battery_temp_c', 'N/A'):.1f}°C
- **Average Temperature**: {summary.get('avg_battery_temp_c', 'N/A'):.1f}°C

## Motor Status

### Performance

- **Maximum Speed**: {summary.get('max_motor_speed_rpm', 'N/A'):.1f} rpm
- **Maximum Torque**: {summary.get('max_motor_torque_nm', 'N/A'):.1f} Nm
- **Average Efficiency**: {summary.get('avg_motor_efficiency', 'N/A')*100:.1f}%

### Motor Health

- **Health Status**: {summary.get('motor_health', 'N/A')*100:.1f}%
- **Remaining Useful Life**: {summary.get('motor_rul_hours', 'N/A'):.1f} hours
- **Temperature Range**: {summary.get('min_motor_temp_c', 'N/A'):.1f}°C to {summary.get('max_motor_temp_c', 'N/A'):.1f}°C
- **Average Temperature**: {summary.get('avg_motor_temp_c', 'N/A'):.1f}°C

## Simulation Timestamp

- **Generated**: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        # Write report to file
        with open(output_file, 'w') as f:
            f.write(report)
        
        print(f"Simulation report generated: {output_file}")
        
        return report
    
    def replay_simulation(self, sim_id=None, speed_factor=1.0, output_file=None):
        """
        Replay a simulation with visualization.
        
        Args:
            sim_id (str, optional): Simulation ID. If None, use current simulation.
            speed_factor (float): Replay speed factor (1.0 = real-time)
            output_file (str, optional): Output file for animation
        
        Returns:
            animation: Matplotlib animation object
        """
        # Use current simulation if not specified
        if sim_id is None:
            sim_id = self.current_simulation_id
        
        if sim_id not in self.simulation_data:
            print(f"Simulation {sim_id} not found")
            return None
        
        df = self.simulation_data[sim_id]
        
        # Check required columns
        required_columns = ["Time (s)", "Speed (km/h)", "Battery SOC", "Power Demand (kW)"]
        for col in required_columns:
            if col not in df.columns:
                print(f"Required column '{col}' not found in simulation data")
                return None
        
        # Create figure
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        plt.subplots_adjust(hspace=0.3)
        
        # Initialize plots
        speed_line, = axes[0, 0].plot([], [], 'b-')
        axes[0, 0].set_xlabel("Time [min]")
        axes[0, 0].set_ylabel("Speed [km/h]")
        axes[0, 0].set_title("Vehicle Speed")
        axes[0, 0].grid(True)
        
        soc_line, = axes[0, 1].plot([], [], 'g-')
        axes[0, 1].set_xlabel("Time [min]")
        axes[0, 1].set_ylabel("SOC [%]")
        axes[0, 1].set_title("Battery State of Charge")
        axes[0, 1].grid(True)
        
        power_line, = axes[1, 0].plot([], [], 'r-')
        axes[1, 0].set_xlabel("Time [min]")
        axes[1, 0].set_ylabel("Power [kW]")
        axes[1, 0].set_title("Power Demand")
        axes[1, 0].grid(True)
        
        # Dashboard in the bottom right
        dashboard_ax = axes[1, 1]
        dashboard_ax.axis('off')
        
        # Set axis limits
        time_max = df["Time (s)"].max() / 60  # Convert to minutes
        axes[0, 0].set_xlim(0, time_max)
        axes[0, 0].set_ylim(0, df["Speed (km/h)"].max() * 1.1)
        
        axes[0, 1].set_xlim(0, time_max)
        axes[0, 1].set_ylim(0, 100)
        
        axes[1, 0].set_xlim(0, time_max)
        power_max = max(df["Power Demand (kW)"].max(), 1) * 1.1
        power_min = min(df["Power Demand (kW)"].min(), 0) * 1.1
        axes[1, 0].set_ylim(power_min, power_max)
        
        # Prepare data
        time_data = df["Time (s)"].values / 60  # Convert to minutes
        speed_data = df["Speed (km/h)"].values
        soc_data = df["Battery SOC"].values * 100  # Convert to percentage
        power_data = df["Power Demand (kW)"].values
        
        # Animation update function
        def update(frame):
            # Update line data
            speed_line.set_data(time_data[:frame], speed_data[:frame])
            soc_line.set_data(time_data[:frame], soc_data[:frame])
            power_line.set_data(time_data[:frame], power_data[:frame])
            
            # Update dashboard
            dashboard_ax.clear()
            dashboard_ax.axis('off')
            
            # Current values
            current_time = df["Time (s)"].iloc[frame]
            current_time_min = current_time / 60
            current_time_formatted = f"{int(current_time // 60):02d}:{int(current_time % 60):02d}"
            current_speed = df["Speed (km/h)"].iloc[frame]
            current_soc = df["Battery SOC"].iloc[frame] * 100
            current_power = df["Power Demand (kW)"].iloc[frame]
            
            # Additional values if available
            dashboard_text = f"Time: {current_time_formatted}\n"
            dashboard_text += f"Speed: {current_speed:.1f} km/h\n"
            dashboard_text += f"Battery: {current_soc:.1f}%\n"
            dashboard_text += f"Power: {current_power:.1f} kW\n"
            
            if "Distance (km)" in df.columns:
                current_distance = df["Distance (km)"].iloc[frame]
                dashboard_text += f"Distance: {current_distance:.2f} km\n"
            
            if "Motor Torque (Nm)" in df.columns:
                current_torque = df["Motor Torque (Nm)"].iloc[frame]
                dashboard_text += f"Torque: {current_torque:.1f} Nm\n"
            
            if "Battery Temperature (°C)" in df.columns:
                current_temp = df["Battery Temperature (°C)"].iloc[frame]
                dashboard_text += f"Battery Temp: {current_temp:.1f}°C\n"
            
            if "Motor Temperature (°C)" in df.columns:
                current_motor_temp = df["Motor Temperature (°C)"].iloc[frame]
                dashboard_text += f"Motor Temp: {current_motor_temp:.1f}°C\n"
            
            dashboard_ax.text(0.5, 0.5, dashboard_text, ha='center', va='center', fontsize=12)
            
            return speed_line, soc_line, power_line
        
        # Create animation
        from matplotlib.animation import FuncAnimation
        
        frames = len(df)
        interval = 1000 / (30 * speed_factor)  # 30 fps adjusted by speed factor
        
        anim = FuncAnimation(fig, update, frames=frames, interval=interval, blit=True)
        
        # Save animation if output file specified
        if output_file:
            if output_file.endswith('.mp4'):
                anim.save(output_file, writer='ffmpeg', fps=30)
            elif output_file.endswith('.gif'):
                anim.save(output_file, writer='pillow', fps=15)
            else:
                print("Unsupported output format. Use .mp4 or .gif")
        
        plt.tight_layout()
        plt.show()
        
        return anim


def test_reporting_dashboard():
    """
    Test function to demonstrate the reporting dashboard functionality.
    """
    # Create dashboard
    dashboard = EVReportingDashboard()
    
    # Load sample data
    sample_data_file = "enhanced_ev_simulation_results.csv"
    if os.path.exists(sample_data_file):
        # Load existing simulation
        sim_id = dashboard.load_simulation(sample_data_file, "Sample EV Simulation")
        
        # Generate dashboard
        dashboard.generate_dashboard(sim_id, "ev_dashboard.png")
        
        # Generate report
        dashboard.generate_report(sim_id, "dashboard_report.md")
        
        print("Reporting dashboard test completed successfully")
        return dashboard
    else:
        print(f"Sample data file {sample_data_file} not found")
        return None


if __name__ == "__main__":
    test_reporting_dashboard()

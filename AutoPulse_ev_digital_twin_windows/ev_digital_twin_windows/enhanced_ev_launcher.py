"""
Enhanced Windows-compatible launcher for the Electric Vehicle Digital Twin
This script automatically starts both the simulation and web interface
"""

import os
import sys
import webbrowser
import http.server
import socketserver
import threading
import time
import subprocess
import importlib.util
import platform

def setup_paths():
    """Set up the Python path for Windows compatibility"""
    # Get the current script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the current directory to sys.path if not already there
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Add the ev_digital_twin directory to sys.path if it exists
    ev_twin_dir = os.path.join(current_dir, "ev_digital_twin")
    if os.path.exists(ev_twin_dir) and ev_twin_dir not in sys.path:
        sys.path.insert(0, ev_twin_dir)
    
    print(f"Added {current_dir} to Python path")
    if os.path.exists(ev_twin_dir):
        print(f"Added {ev_twin_dir} to Python path")
    
    return current_dir

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = ["numpy", "pandas", "matplotlib", "scipy"]
    missing_packages = []
    
    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required Python packages:")
        for package in missing_packages:
            print(f"  - {package}")
        
        print("\nPlease install the missing packages using:")
        print(f"pip install {' '.join(missing_packages)}")
        
        return False
    
    print("All required Python packages are installed.")
    return True

def start_web_server(directory, port=8000):
    """Start a local web server in the specified directory"""
    os.chdir(directory)
    
    # Create a custom handler that sets the correct MIME types
    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # Enable CORS
            self.send_header('Access-Control-Allow-Origin', '*')
            super().end_headers()
            
        def guess_type(self, path):
            """Guess the type of a file based on its extension"""
            if path.endswith('.js'):
                return 'application/javascript'
            elif path.endswith('.html'):
                return 'text/html'
            elif path.endswith('.css'):
                return 'text/css'
            elif path.endswith('.json'):
                return 'application/json'
            elif path.endswith('.pdf'):
                return 'application/pdf'
            return super().guess_type(path)
    
    # Create and start the server
    handler = CustomHTTPRequestHandler
    
    # Try to start the server, handling the case where the port is already in use
    try:
        httpd = socketserver.TCPServer(("", port), handler)
        print(f"Web server started at http://localhost:{port}")
        
        # Start the server in a separate thread
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        return httpd
    except OSError as e:
        if e.errno == 98 or e.errno == 10048:  # Port already in use (Linux/Windows)
            print(f"Port {port} is already in use. The web server may already be running.")
            return None
        else:
            raise

def open_web_interface(port=8000):
    """Open the web interface in the default browser"""
    url = f"http://localhost:{port}/index.html"
    print(f"Opening web interface at {url}")
    webbrowser.open(url)

def start_simulation_backend():
    """Start the simulation backend in a separate process"""
    print("Starting EV Digital Twin simulation backend...")
    
    # Get the current script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Determine the path to the simulation module
    if platform.system() == "Windows":
        # For Windows, use the windows_real_time_simulation.py if available
        sim_script = os.path.join(current_dir, "windows_real_time_simulation.py")
        if not os.path.exists(sim_script):
            sim_script = os.path.join(current_dir, "ev_digital_twin", "simulation", "real_time_simulation.py")
    else:
        # For Linux/Mac, use the original simulation script
        sim_script = os.path.join(current_dir, "ev_digital_twin", "simulation", "real_time_simulation.py")
    
    # Check if the simulation script exists
    if not os.path.exists(sim_script):
        print(f"Error: Simulation script not found at {sim_script}")
        return None
    
    # Start the simulation in a separate process
    try:
        if platform.system() == "Windows":
            # Hide console window on Windows
            startupinfo = None
            if hasattr(subprocess, 'STARTUPINFO'):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.Popen(
                [sys.executable, sim_script],
                cwd=current_dir,
                startupinfo=startupinfo
            )
        else:
            process = subprocess.Popen(
                [sys.executable, sim_script],
                cwd=current_dir
            )
        
        print(f"Simulation backend started (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"Error starting simulation backend: {e}")
        return None

def find_index_html():
    """Find the index.html file in the project directory"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check common locations for index.html
    possible_locations = [
        current_dir,
        os.path.join(current_dir, "web_interface"),
        os.path.join(current_dir, "ev_digital_twin", "web_interface"),
    ]
    
    for location in possible_locations:
        index_path = os.path.join(location, "index.html")
        if os.path.exists(index_path):
            return location
    
    # If not found in common locations, search recursively
    for root, dirs, files in os.walk(current_dir):
        if "index.html" in files:
            return root
    
    # Default to current directory if not found
    return current_dir

def main():
    """Main function to run the EV Digital Twin with web interface"""
    try:
        print("=" * 60)
        print("Starting Enhanced Electric Vehicle Digital Twin")
        print("=" * 60)
        
        # Setup paths
        project_dir = setup_paths()
        
        # Check dependencies
        if not check_dependencies():
            input("\nPress Enter to exit...")
            return
        
        # Find the directory containing index.html
        web_dir = find_index_html()
        print(f"Found web interface in: {web_dir}")
        
        # Start the web server
        port = 8000
        server = start_web_server(web_dir, port)
        
        if server is None:
            print("Using existing web server...")
        
        # Wait a moment for the server to start
        time.sleep(1)
        
        # Start the simulation backend
        sim_process = start_simulation_backend()
        
        # Open the web interface
        open_web_interface(port)
        
        print("\n" + "=" * 60)
        print("Electric Vehicle Digital Twin is now running")
        print("The web interface should open in your default browser")
        print("If it doesn't open automatically, go to: http://localhost:8000")
        print("=" * 60)
        print("\nPress Ctrl+C to stop all services and exit")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down services...")
        if 'server' in locals() and server is not None:
            server.shutdown()
        if 'sim_process' in locals() and sim_process is not None:
            sim_process.terminate()
        print("All services stopped. Goodbye!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()

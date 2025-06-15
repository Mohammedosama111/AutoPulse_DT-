"""
Web Interface Auto-Launcher for Electric Vehicle Digital Twin
This script automatically opens the web interface in the default browser
"""

import os
import sys
import webbrowser
import http.server
import socketserver
import threading
import time
import platform

def setup_paths():
    """Set up the Python path for Windows compatibility"""
    # Get the current script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the current directory to sys.path if not already there
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    return current_dir

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

def main():
    """Main function to run the web interface auto-launcher"""
    try:
        print("=" * 60)
        print("Starting Electric Vehicle Digital Twin Web Interface")
        print("=" * 60)
        
        # Setup paths
        project_dir = setup_paths()
        
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
        
        # Open the web interface
        open_web_interface(port)
        
        print("\n" + "=" * 60)
        print("Electric Vehicle Digital Twin Web Interface is now running")
        print("The web interface should be open in your default browser")
        print("If it doesn't open automatically, go to: http://localhost:8000")
        print("=" * 60)
        print("\nPress Ctrl+C to stop the server and exit")
        
        # Keep the script running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down web server...")
        if 'server' in locals() and server is not None:
            server.shutdown()
        print("Web server stopped. Goodbye!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()

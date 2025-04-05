#!/usr/bin/env python3
"""
SUMO Sci-Fi Dashboard - Launcher Script
---------------------------------------
This script checks for the required dependencies and launches the SUMO Sci-Fi Dashboard.
"""

import sys
import os
import subprocess
import importlib.util
import pkg_resources
from pathlib import Path

def check_dependency(package_name, min_version=None):
    """Check if a package is installed and meets the minimum version requirement."""
    try:
        if min_version:
            pkg_resources.require(f"{package_name}>={min_version}")
        else:
            pkg_resources.require(package_name)
        return True
    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
        return False

def check_sumo():
    """Check if SUMO is properly installed and configured."""
    # First check if SUMO is installed via pip
    try:
        import sumo
        print("Found SUMO Python package installed via pip.")
        
        # Set SUMO_HOME if not already set
        if "SUMO_HOME" not in os.environ:
            sumo_package_path = os.path.dirname(sumo.__file__)
            os.environ["SUMO_HOME"] = sumo_package_path
            print(f"Set SUMO_HOME to {sumo_package_path}")
        
        sumo_home = os.environ["SUMO_HOME"]
        
        # For pip installation, we need to ensure binaries are accessible
        # The binaries might be in a different location than standard SUMO
        if os.path.exists(os.path.join(sumo_home, "bin", "sumo")) or \
           os.path.exists(os.path.join(sumo_home, "bin", "sumo.exe")):
            return True
            
        # Try to find sumo in PATH
        from shutil import which
        sumo_binary = which("sumo")
        if sumo_binary:
            print(f"Found SUMO binary at {sumo_binary}")
            return True
            
        # If we can import traci, we're probably good to go
        try:
            import traci
            print("TraCI module found, assuming SUMO is properly installed.")
            return True
        except ImportError:
            pass
            
        print(f"WARNING: SUMO binaries not found in standard locations.")
        print(f"The application may still work if the binaries are in your PATH.")
        return True  # Return True anyway, we'll try to run
        
    except ImportError:
        # Traditional SUMO installation check
        if "SUMO_HOME" not in os.environ:
            print("ERROR: SUMO_HOME environment variable is not set.")
            print("Please set the SUMO_HOME environment variable to your SUMO installation directory.")
            return False
        
        sumo_home = os.environ["SUMO_HOME"]
        
        # Check if SUMO binaries exist
        sumo_bin = os.path.join(sumo_home, "bin", "sumo")
        sumo_gui_bin = os.path.join(sumo_home, "bin", "sumo-gui")
        
        if not (os.path.exists(sumo_bin) or os.path.exists(sumo_bin + ".exe")):
            print(f"ERROR: SUMO binary not found at {sumo_bin}")
            return False
        
        if not (os.path.exists(sumo_gui_bin) or os.path.exists(sumo_gui_bin + ".exe")):
            print(f"ERROR: SUMO-GUI binary not found at {sumo_gui_bin}")
            return False
        
        # Check if SUMO tools are available
        tools_path = os.path.join(sumo_home, "tools")
        if not os.path.exists(tools_path):
            print(f"ERROR: SUMO tools directory not found at {tools_path}")
            return False
        
        return True

def install_dependencies():
    """Install required Python dependencies."""
    dependencies = ["PyQt6>=6.0.0"]
    
    print("Installing required dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + dependencies)
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError:
        print("ERROR: Failed to install dependencies.")
        return False

def main():
    """Main function to check dependencies and launch the application."""
    print("SUMO Sci-Fi Dashboard - Setup")
    print("-----------------------------")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required.")
        return 1
    
    # Check PyQt6
    if not check_dependency("PyQt6", "6.0.0"):
        print("PyQt6 not found or version too old. Attempting to install...")
        if not install_dependencies():
            print("Please install PyQt6 manually: pip install PyQt6>=6.0.0")
            return 1
    
    # Check SUMO
    if not check_sumo():
        print("\nSUMO not properly configured. Please install SUMO and set the SUMO_HOME environment variable.")
        print("SUMO can be downloaded from: https://sumo.dlr.de/docs/Downloads.php")
        return 1
    
    # Try to import traci to make sure it's available
    try:
        # First try importing from sumo package (pip installation)
        try:
            from sumo import traci
            print("TraCI module found in sumo package.")
        except ImportError:
            # Then try traditional import
            import traci
            print("TraCI module found.")
    except ImportError:
        print("WARNING: TraCI module not found. Some simulation features may be limited.")
    
    print("\nAll dependencies satisfied. Launching SUMO Sci-Fi Dashboard...\n")
    
    # Import and run the main application
    try:
        from main_app import MainWindow
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        return app.exec()
    except ImportError as e:
        print(f"ERROR: Failed to import required modules: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        return 1
    
if __name__ == "__main__":
    sys.exit(main())
# SUMO Sci-Fi Dashboard

A modern, sci-fi themed interface for Eclipse SUMO (Simulation of Urban MObility) traffic simulator. This application provides a sleek, futuristic dashboard for creating, editing, and simulating traffic networks directly within a single, integrated application.

![SUMO Sci-Fi Dashboard](https://via.placeholder.com/800x450/101020/00FFFF?text=SUMO+Sci-Fi+Dashboard)

## Features

- **Modern Sci-Fi Interface**: Dark-themed UI with futuristic design elements
- **Advanced Network Editor**: Easily create and edit road networks with an intuitive drawing interface
- **Integrated Simulation**: Run traffic simulations directly within the application
  - No external SUMO GUI required
  - Real-time visualization and control
  - Seamless simulation management
- **Interactive Visualization**: 
  - Live vehicle tracking
  - Dynamic network rendering
  - Multiple visualization modes
- **Comprehensive Simulation Controls**: 
  - Detailed parameter configuration
  - Real-time speed and route adjustments
  - Instant statistical feedback

## Key Innovations

### Integrated Simulation Experience
Unlike traditional traffic simulation tools, the SUMO Sci-Fi Dashboard runs the entire simulation process within a single application:

- Direct SUMO integration via TraCI
- Real-time vehicle and network visualization
- Complete simulation control from one interface
- No need to launch external simulation windows
- Instant feedback and interactive exploration

### Sci-Fi Visualization
- Futuristic dark-themed interface
- Dynamic, color-coded vehicle representations
- Customizable visualization styles
- Interactive zoom and display options

## Requirements

- Python 3.8 or higher
- PyQt6
- Eclipse SUMO 1.8.0 or higher

## Installation

1. **Install SUMO**: 
   Download and install Eclipse SUMO from [the official website](https://sumo.dlr.de/docs/Downloads.php).

2. **Set SUMO_HOME Environment Variable**:
   - **Windows**: `set SUMO_HOME=C:\path\to\sumo`
   - **Linux/Mac**: `export SUMO_HOME=/path/to/sumo`

3. **Clone the Repository**:
   ```
   git clone https://github.com/yourusername/sumo-scifi-dashboard.git
   cd sumo-scifi-dashboard
   ```

4. **Install Python Dependencies**:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

You can start the application by running:

```
python run_app.py
```

The launcher script will check for dependencies and launch the application. If any dependencies are missing, it will attempt to install them automatically.

## Usage Guide

### Network Editor

1. **Create a New Network**:
   - Click on "New Network" in the sidebar or toolbar
   - Switch to "Network Editor" tab if not already there

2. **Draw Mode**:
   - Click "Draw Mode" button to enter drawing mode
   - Left-click to place nodes (intersections)
   - Continue left-clicking to create roads between nodes
   - Right-click to cancel the current road
   - Press Escape to exit drawing mode

3. **Edit Network Elements**:
   - Right-click on nodes or roads to access context menu
   - Edit properties such as speed limits, number of lanes, etc.
   - Delete unwanted elements

4. **Save Your Network**:
   - Click "Save Network" to save in SUMO format
   - Your network will be saved as a .net.xml file

### Simulation

1. **Configure Simulation Parameters**:
   - Set the number of vehicles
   - Choose distribution pattern
   - Adjust simulation speed
   - Configure route options

2. **Run Simulation**:
   - Click "Start Simulation" to begin
   - The application will switch to the Simulation tab automatically
   - Use the simulation controls to adjust parameters on-the-fly

3. **Explore Visualization**:
   - Watch vehicles move in real-time
   - Explore different visualization modes
   - Analyze traffic flow, speed, and density
   - View overall statistics

## Project Structure

- `main_app.py` - Main application entry point
- `network_editor.py` - Advanced network editing components
- `vehicle_simulator.py` - Integrated simulation control and visualization
- `sumo_utils.py` - Utilities for SUMO integration
- `run_app.py` - Launcher script that checks dependencies

## Customization

You can customize the appearance by modifying the style sheet definitions in the code. Look for `setStyleSheet` calls and adjust colors and other properties to match your preferences.

## Known Issues

- Large networks may cause performance slowdowns
- Some advanced SUMO features are not yet supported in the UI
- TraCI integration may be limited depending on your SUMO installation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Eclipse SUMO](https://www.eclipse.org/sumo/) for the excellent traffic simulation engine
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the UI framework
- All contributors who have helped with the project
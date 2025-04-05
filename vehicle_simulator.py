import os
import sys
import subprocess
import tempfile
import time
import threading
from PyQt6.QtWidgets import (QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsRectItem)
from PyQt6.QtCore import QLineF, QPointF
from PyQt6.QtGui import (QPen, QBrush, QColor, QFont, QPainter)
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QSlider, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
                            QGroupBox, QFormLayout, QFileDialog, QMessageBox,
                            QProgressBar, QTabWidget,QGraphicsView, QGraphicsScene)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QProcess
from PyQt6.QtGui import QFont, QColor, QPainter
import os
import sys
import subprocess
import tempfile
import time
import threading
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QSlider, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
                            QGroupBox, QFormLayout, QFileDialog, QMessageBox,
                            QProgressBar, QTabWidget, QGraphicsView, QGraphicsScene,
                            QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsRectItem)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QProcess, QPointF, QLineF
from PyQt6.QtGui import QFont, QColor, QPen, QBrush, QPainter, QTransform

# Try to import TraCI (Traffic Control Interface) for SUMO
try:
    # Add SUMO_HOME/tools to the Python path
    if 'SUMO_HOME' in os.environ:
        tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
        sys.path.append(tools)
    else:
        raise EnvironmentError("Please declare environment variable 'SUMO_HOME'")
    
    import traci
    TRACI_AVAILABLE = True
except ImportError:
    TRACI_AVAILABLE = False
    print("TraCI not available. Limited simulation functionality.")


class SimulationControlPanel(QWidget):
    """
    Control panel for simulation parameters and execution
    """
    simulation_started = pyqtSignal(str)  # Emits config file path
    simulation_stopped = pyqtSignal()
    simulation_data_updated = pyqtSignal(dict)  # Emits vehicle data for visualization
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sumo_process = None
        self.traci_controller = None
        self.setupUI()
    
    def setupUI(self):
        """Set up the control panel UI"""
        main_layout = QVBoxLayout(self)
        
        # Style constants
        title_style = "color: #00FFFF; font-weight: bold; font-size: 14px; margin-top: 10px;"
        group_style = """
            QGroupBox {
                border: 1px solid #4040bf;
                border-radius: 4px;
                margin-top: 10px;
                color: #00FFAA;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """
        slider_style = """
            QSlider::groove:horizontal {
                border: 1px solid #4040bf;
                height: 8px;
                background: #2a2a4a;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00FFFF;
                border: 1px solid #00FFFF;
                width: 18px;
                margin: -8px 0;
                border-radius: 9px;
            }
        """
        
        # Simulation parameters group
        param_group = QGroupBox("Simulation Parameters")
        param_group.setStyleSheet(group_style)
        param_layout = QFormLayout(param_group)
        
        # Vehicle count
        self.vehicle_count = QSpinBox()
        self.vehicle_count.setRange(1, 1000)
        self.vehicle_count.setValue(100)
        self.vehicle_count.setStyleSheet("color: #e6e6ff; background-color: #2a2a4a; border: 1px solid #4040bf;")
        param_layout.addRow("Vehicles:", self.vehicle_count)
        
        # Simulation speed
        self.speed_factor = QSlider(Qt.Orientation.Horizontal)
        self.speed_factor.setRange(10, 500)  # 0.1x to 5.0x
        self.speed_factor.setValue(100)  # 1.0x default
        self.speed_factor.setStyleSheet(slider_style)
        self.speed_label = QLabel("1.0x")
        self.speed_label.setStyleSheet("color: #e6e6ff;")
        self.speed_factor.valueChanged.connect(self.updateSpeedLabel)
        
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(self.speed_factor)
        speed_layout.addWidget(self.speed_label)
        param_layout.addRow("Speed:", speed_layout)
        
        # Visualization style
        self.viz_style = QComboBox()
        self.viz_style.addItems(["Classic", "Futuristic", "Minimal", "Neon"])
        self.viz_style.setStyleSheet("color: #e6e6ff; background-color: #2a2a4a; border: 1px solid #4040bf;")
        param_layout.addRow("Style:", self.viz_style)
        
        # Route generation options
        route_group = QGroupBox("Route Options")
        route_group.setStyleSheet(group_style)
        route_layout = QFormLayout(route_group)
        
        # Route type
        self.route_type = QComboBox()
        self.route_type.addItems(["Random", "Shortest Path", "Fastest Path", "Custom"])
        self.route_type.setStyleSheet("color: #e6e6ff; background-color: #2a2a4a; border: 1px solid #4040bf;")
        route_layout.addRow("Route Type:", self.route_type)
        
        # Vehicle distribution
        self.distribution = QComboBox()
        self.distribution.addItems(["Uniform", "Poisson", "Normal", "Rush Hour"])
        self.distribution.setStyleSheet("color: #e6e6ff; background-color: #2a2a4a; border: 1px solid #4040bf;")
        route_layout.addRow("Distribution:", self.distribution)
        
        # Simulation duration
        self.duration = QSpinBox()
        self.duration.setRange(10, 3600)  # 10s to 1h
        self.duration.setValue(600)  # 10 minutes default
        self.duration.setSuffix(" s")
        self.duration.setStyleSheet("color: #e6e6ff; background-color: #2a2a4a; border: 1px solid #4040bf;")
        route_layout.addRow("Duration:", self.duration)
        
        # Advanced options
        advanced_group = QGroupBox("Advanced Settings")
        advanced_group.setStyleSheet(group_style)
        advanced_layout = QFormLayout(advanced_group)
        
        # Step length
        self.step_length = QDoubleSpinBox()
        self.step_length.setRange(0.01, 1.0)
        self.step_length.setValue(0.1)
        self.step_length.setSingleStep(0.01)
        self.step_length.setSuffix(" s")
        self.step_length.setStyleSheet("color: #e6e6ff; background-color: #2a2a4a; border: 1px solid #4040bf;")
        advanced_layout.addRow("Step Length:", self.step_length)
        
        # Collect traffic data
        self.collect_data = QCheckBox("Collect Traffic Data")
        self.collect_data.setChecked(True)
        self.collect_data.setStyleSheet("color: #e6e6ff;")
        advanced_layout.addRow("", self.collect_data)
        
        # GUI option
        self.use_gui = QCheckBox("Show SUMO GUI")
        self.use_gui.setChecked(True)
        self.use_gui.setStyleSheet("color: #e6e6ff;")
        advanced_layout.addRow("", self.use_gui)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        btn_style = """
            QPushButton {
                background-color: #2a2a4a;
                color: #00FFFF;
                border: 1px solid #4040bf;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a6a;
            }
            QPushButton:pressed {
                background-color: #4a4a8a;
            }
            QPushButton:disabled {
                background-color: #1a1a2a;
                color: #555577;
                border: 1px solid #333355;
            }
        """
        
        self.start_btn = QPushButton("▶️ Start Simulation")
        self.start_btn.setStyleSheet(btn_style)
        self.start_btn.clicked.connect(self.startSimulation)
        
        self.stop_btn = QPushButton("⏹️ Stop Simulation")
        self.stop_btn.setStyleSheet(btn_style)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stopSimulation)
        
        self.reset_btn = QPushButton("🔄 Reset")
        self.reset_btn.setStyleSheet(btn_style)
        self.reset_btn.clicked.connect(self.resetSimulation)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.reset_btn)
        
        # Status indicator
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #00FF00; font-weight: bold;")
        status_layout.addWidget(QLabel("Status:"))
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #4040bf;
                border-radius: 4px;
                background-color: #2a2a4a;
                color: #e6e6ff;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #00AAFF;
                border-radius: 3px;
            }
        """)
        
        # Add everything to main layout
        main_layout.addWidget(param_group)
        main_layout.addWidget(route_group)
        main_layout.addWidget(advanced_group)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(status_layout)
        main_layout.addWidget(self.progress_bar)
        
        # Create a timer for updating the simulation
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.updateSimulation)
        
        # Set up the simulation process handler
        self.simulation_process = QProcess(self)
        self.simulation_process.finished.connect(self.processFinished)
    
    def updateSpeedLabel(self, value):
        """Update the speed factor label"""
        speed = value / 100.0
        self.speed_label.setText(f"{speed:.1f}x")
    
    def startSimulation(self):
        """Start the SUMO simulation"""
        if not TRACI_AVAILABLE:
            QMessageBox.warning(
                self, 
                "TraCI Not Available", 
                "The SUMO Traffic Control Interface (TraCI) is not available. "
                "Make sure SUMO is installed correctly and the SUMO_HOME environment variable is set."
            )
            return
        
        # Check if we have a network file
        if not hasattr(self, 'network_file') or not self.network_file:
            QMessageBox.warning(
                self, 
                "No Network", 
                "Please create or load a road network first."
            )
            return
        
        # Create a temporary directory for simulation files
        self.temp_dir = tempfile.mkdtemp()
        
        try:
            # Create route file
            self.createRouteFile()
            
            # Create configuration file
            config_file = self.createConfigFile()
            
            # Update UI
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Simulation Running")
            self.status_label.setStyleSheet("color: #FF9900; font-weight: bold;")
            
            # Start progress tracking
            self.progress_bar.setValue(0)
            self.simulation_start_time = time.time()
            self.update_timer.start(100)  # Update every 100ms
            
            # Initialize TraCI controller
            if not hasattr(self, 'traci_controller') or not self.traci_controller:
                self.traci_controller = TraciSimulationController()
            
            # Start simulation with TraCI instead of launching external GUI
            success = self.traci_controller.connect(config_file)
            
            if not success:
                raise Exception("Failed to connect to SUMO via TraCI")
            
            # Set up a timer to step the simulation
            if not hasattr(self, 'simulation_timer'):
                self.simulation_timer = QTimer(self)
                self.simulation_timer.timeout.connect(self.stepSimulation)
            
            # Set the timer interval based on the speed factor
            interval = max(10, int(100 / (self.speed_factor.value() / 100.0)))
            self.simulation_timer.start(interval)
            
            # Emit signal that simulation started
            self.simulation_started.emit(config_file)
            
        except Exception as e:
            QMessageBox.critical(self, "Simulation Error", f"Error starting simulation: {str(e)}")
            self.resetUI()
    
    def stepSimulation(self):
        """Perform a single simulation step"""
        if not hasattr(self, 'traci_controller') or not self.traci_controller or not self.traci_controller.connected:
            self.stopSimulation()
            return
        
        try:
            # Step the simulation
            success = self.traci_controller.step()
            
            if not success:
                self.stopSimulation()
                return
            
            # Update progress
            elapsed_time = time.time() - self.simulation_start_time
            total_time = self.duration.value()
            progress = min(int((elapsed_time / total_time) * 100), 100)
            self.progress_bar.setValue(progress)
            
            # Get simulation data to update visualization
            self.updateSimulationData()
            
            # Check if simulation is complete
            if progress >= 100:
                self.stopSimulation()
        
        except Exception as e:
            print(f"Error in simulation step: {e}")
            self.stopSimulation()
    
    def createRouteFile(self):
            """Create a route file for the simulation"""
            # This would normally use SUMO tools to generate routes
            # For now, we'll create a route file using actual network edges
            
            self.route_file = os.path.join(self.temp_dir, "routes.rou.xml")
            
            # First, try to parse the network file to get actual edges
            try:
                import xml.etree.ElementTree as ET
                
                # Read the network file
                network_file = self.network_file
                tree = ET.parse(network_file)
                root = tree.getroot()
                
                # Find all edge IDs
                edge_ids = [edge.get('id') for edge in root.findall('.//edge')]
                
                # If no edges found, use a default route
                if not edge_ids:
                    edge_ids = ['edge0']
            except Exception as e:
                print(f"Error parsing network file: {e}")
                edge_ids = ['edge0']
            
            # Validate edge_ids
            if not edge_ids:
                edge_ids = ['edge0']
            
            # Create route file
            with open(self.route_file, 'w') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<routes>\n')
                
                # Define a vehicle type
                f.write('    <vType id="car" accel="2.6" decel="4.5" sigma="0.5" length="5" maxSpeed="50"/>\n')
                
                # Define route using the first edge found
                f.write(f'    <route id="route0" edges="{" ".join(edge_ids)}"/>\n')
                
                # Add vehicles
                vehicle_count = self.vehicle_count.value()
                for i in range(vehicle_count):
                    # Calculate departure time and position based on distribution
                    if self.distribution.currentText() == "Uniform":
                        depart_time = i * (self.duration.value() / vehicle_count)
                        depart_pos = "random"  # Random position along the first edge
                    elif self.distribution.currentText() == "Poisson":
                        import numpy as np
                        # Poisson distribution for departure times
                        depart_time = np.random.poisson(self.duration.value() / vehicle_count) * 1.0
                        depart_pos = "random"
                    elif self.distribution.currentText() == "Normal":
                        import numpy as np
                        # Normal distribution for departure times
                        depart_time = max(0, np.random.normal(
                            loc=self.duration.value() / 2, 
                            scale=self.duration.value() / 6
                        ))
                        depart_pos = "random"
                    else:  # Rush Hour simulation
                        # Concentrate vehicles in the middle third of simulation time
                        rush_start = self.duration.value() * 0.3
                        rush_end = self.duration.value() * 0.7
                        depart_time = rush_start + (i * (rush_end - rush_start) / vehicle_count)
                        depart_pos = "random"
                    
                    # Ensure depart time is within simulation duration
                    depart_time = min(max(0, depart_time), self.duration.value() - 1)
                    
                    f.write(
                        f'    <vehicle id="veh{i}" type="car" route="route0" '
                        f'depart="{depart_time:.2f}" departPos="{depart_pos}"/>\n'
                    )
                
                f.write('</routes>\n')
            
            return self.route_file
    
    def createConfigFile(self):
        """Create a SUMO configuration file"""
        config_file = os.path.join(self.temp_dir, "sim.sumocfg")
        
        with open(config_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<configuration>\n')
            
            f.write('    <input>\n')
            f.write(f'        <net-file value="{os.path.basename(self.network_file)}"/>\n')
            f.write(f'        <route-files value="{os.path.basename(self.route_file)}"/>\n')
            f.write('    </input>\n')
            f.write('    <defaults>\n')
            f.write('        <randomize>\n')
            f.write('            <vehicle.depart-pos value="random"/>\n')
            f.write('            <vehicle.departspeed value="random"/>\n')
            f.write('        </randomize>\n')
            f.write('    </defaults>\n')
            
            f.write('    <time>\n')
            f.write('        <begin value="0"/>\n')
            f.write(f'        <end value="{self.duration.value()}"/>\n')
            f.write(f'        <step-length value="{self.step_length.value()}"/>\n')
            f.write('    </time>\n')
            
            if self.collect_data.isChecked():
                f.write('    <output>\n')
                f.write(f'        <summary-output value="{os.path.join(self.temp_dir, "summary.xml")}"/>\n')
                f.write(f'        <tripinfo-output value="{os.path.join(self.temp_dir, "tripinfo.xml")}"/>\n')
                f.write('    </output>\n')
            
            f.write('    <report>\n')
            f.write('        <verbose value="false"/>\n')
            f.write('        <no-step-log value="true"/>\n')
            f.write('    </report>\n')
            
            f.write('</configuration>\n')
        
        # Copy network file to temp dir if it's not already there
        if not os.path.exists(os.path.join(self.temp_dir, os.path.basename(self.network_file))):
            import shutil
            shutil.copy(self.network_file, self.temp_dir)
        
        return config_file
    
    def updateSimulationData(self):
        """Get current simulation data and update visualization"""
        if not hasattr(self, 'traci_controller') or not self.traci_controller:
            return
        
        # Get all vehicles
        vehicles = self.traci_controller.getVehicles()
        
        # Get vehicle data
        vehicle_data = {}
        for vehicle_id in vehicles:
            data = self.traci_controller.getVehicleData(vehicle_id)
            if data:
                vehicle_data[vehicle_id] = data
        
        # Emit signal with vehicle data for visualization
        self.simulation_data_updated.emit(vehicle_data)
    
    def stopSimulation(self):
        """Stop the running simulation"""
        # Stop the simulation timer
        if hasattr(self, 'simulation_timer') and self.simulation_timer.isActive():
            self.simulation_timer.stop()
        
        # Disconnect from TraCI
        if hasattr(self, 'traci_controller') and self.traci_controller:
            self.traci_controller.disconnect()
        
        self.resetUI()
        self.update_timer.stop()
        
        # Emit signal that simulation stopped
        self.simulation_stopped.emit()
    
    def processFinished(self, exit_code, exit_status):
        """Handle when the SUMO process finishes"""
        self.resetUI()
        self.update_timer.stop()
        
        # Show results if data collection was enabled
        if self.collect_data.isChecked():
            QMessageBox.information(
                self,
                "Simulation Complete",
                "The simulation has completed. Simulation data has been saved."
            )
        
        # Emit signal that simulation stopped
        self.simulation_stopped.emit()
    
    def resetUI(self):
        """Reset the UI controls after simulation stops"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("color: #00FF00; font-weight: bold;")
        self.progress_bar.setValue(0)
    
    def resetSimulation(self):
        """Reset all simulation settings to defaults"""
        # Stop any running simulation
        if self.stop_btn.isEnabled():
            self.stopSimulation()
        
        # Reset controls to defaults
        self.vehicle_count.setValue(100)
        self.speed_factor.setValue(100)
        self.route_type.setCurrentIndex(0)
        self.distribution.setCurrentIndex(0)
        self.duration.setValue(600)
        self.step_length.setValue(0.1)
        self.collect_data.setChecked(True)
        self.use_gui.setChecked(True)
        
        # Reset status
        self.resetUI()
    
    def updateSimulation(self):
        """Update simulation progress"""
        if not hasattr(self, 'simulation_start_time'):
            return
        
        elapsed_time = time.time() - self.simulation_start_time
        total_time = self.duration.value()
        
        # Calculate progress percentage
        progress = min(int((elapsed_time / total_time) * 100), 100)
        self.progress_bar.setValue(progress)
        
        # If finished
        if progress >= 100:
            self.update_timer.stop()
    
    def setNetworkFile(self, file_path):
        """Set the network file to use for simulation"""
        self.network_file = file_path
        
        # Log network details for debugging
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            edges = root.findall('.//edge')
            print(f"Network File: {file_path}")
            print(f"Total Edges: {len(edges)}")
            for edge in edges[:5]:  # Print first 5 edges
                print(f"Edge ID: {edge.get('id')}")
        except Exception as e:
            print(f"Error parsing network file: {e}")


class SimulationVisualization(QWidget):
    """
    Widget for displaying SUMO simulation results
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
    
    def setupUI(self):
        """Set up the visualization UI"""
        main_layout = QVBoxLayout(self)
        
        # Create tabs for different visualizations
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #4040bf;
                background-color: #1a1a2e;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #2a2a4a;
                color: #8080ff;
                border: 1px solid #4040bf;
                border-bottom-color: #4040bf;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
                padding: 5px;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background-color: #3a3a6a;
                color: #00FFFF;
            }
            QTabBar::tab:selected {
                border-bottom-color: #1a1a2e;
            }
        """)
        
        # Create tab widgets
        self.traffic_tab = QWidget()
        self.speed_tab = QWidget()
        self.density_tab = QWidget()
        self.stats_tab = QWidget()
        
        # Add tabs
        self.tabs.addTab(self.traffic_tab, "Traffic Flow")
        self.tabs.addTab(self.speed_tab, "Speed")
        self.tabs.addTab(self.density_tab, "Density")
        self.tabs.addTab(self.stats_tab, "Statistics")
        
        # Set up each tab
        self.setupTrafficTab()
        self.setupSpeedTab()
        self.setupDensityTab()
        self.setupStatsTab()
        
        main_layout.addWidget(self.tabs)
    
    def setupTrafficTab(self):
        """Set up the traffic flow visualization tab"""
        layout = QVBoxLayout(self.traffic_tab)
        
        # Placeholder for traffic visualization
        placeholder = QLabel("Traffic Flow Visualization")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #00FFFF; font-size: 18px; font-weight: bold;")
        
        # In a real application, this would be replaced with a proper
        # visualization widget, possibly using PyQtGraph or similar
        
        layout.addWidget(placeholder)
    
    def setupSpeedTab(self):
        """Set up the speed visualization tab"""
        layout = QVBoxLayout(self.speed_tab)
        
        # Placeholder for speed visualization
        placeholder = QLabel("Speed Visualization")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #00FFFF; font-size: 18px; font-weight: bold;")
        
        layout.addWidget(placeholder)
    
    def setupDensityTab(self):
        """Set up the density visualization tab"""
        layout = QVBoxLayout(self.density_tab)
        
        # Placeholder for density visualization
        placeholder = QLabel("Density Visualization")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #00FFFF; font-size: 18px; font-weight: bold;")
        
        layout.addWidget(placeholder)
    
    def setupStatsTab(self):
        """Set up the statistics tab"""
        layout = QVBoxLayout(self.stats_tab)
        
        # Placeholder for statistics
        placeholder = QLabel("Simulation Statistics")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #00FFFF; font-size: 18px; font-weight: bold;")
        
        layout.addWidget(placeholder)
    
    def updateVisualization(self, simulation_data):
        """Update visualization with new simulation data"""
        # This would be called periodically during simulation
        # to update the visualizations with new data
        pass

class TraciSimulationController:
    """
    Controller class for interacting with SUMO via TraCI
    """
    def __init__(self):
        self.connected = False
        self.simulation_running = False
        self.sumo_process = None
        self.port = 8813
    
    def connect(self, config_file=None, port=8813):
        """Connect to SUMO via TraCI"""
        if not TRACI_AVAILABLE:
            print("TraCI is not available")
            return False
        
        try:
            # Get SUMO_HOME
            if 'SUMO_HOME' not in os.environ:
                raise EnvironmentError("Please declare environment variable 'SUMO_HOME'")
            
            sumo_home = os.environ['SUMO_HOME']
            sumo_binary = os.path.join(sumo_home, 'bin', 'sumo')
            
            if not os.path.exists(sumo_binary) and not os.path.exists(sumo_binary + '.exe'):
                # Try with default path
                sumo_binary = 'sumo'
            
            self.port = port
            
            if config_file:
                # Start SUMO as a subprocess
                cmd = [
                    sumo_binary,
                    '-c', config_file,
                    '--remote-port', str(port),
                    '--start',  # Start immediately
                    '--no-warnings',  # Don't show warnings in console
                    '--no-step-log',  # Don't show step info in console
                ]
                
                # Start SUMO process
                self.sumo_process = subprocess.Popen(cmd, 
                                                    stdout=subprocess.PIPE, 
                                                    stderr=subprocess.PIPE)
                
                # Give it a moment to start
                time.sleep(1.0)
                
                # Connect to the running SUMO instance
                traci.connect(port=port)
            else:
                # Connect to an already running SUMO instance
                traci.connect(port=port)
            
            self.connected = True
            self.simulation_running = True
            return True
        
        except Exception as e:
            print(f"Error connecting to SUMO: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from SUMO"""
        if self.connected:
            try:
                traci.close()
                
                # Terminate the SUMO process if it's still running
                if self.sumo_process:
                    self.sumo_process.terminate()
                    self.sumo_process = None
                
                self.connected = False
                self.simulation_running = False
            except Exception as e:
                print(f"Error disconnecting from SUMO: {e}")
    
    def step(self):
        """Perform one simulation step"""
        if self.connected and self.simulation_running:
            try:
                traci.simulationStep()
                
                # Check if simulation has ended
                if traci.simulation.getMinExpectedNumber() <= 0:
                    # No more vehicles expected, we can end the simulation
                    self.simulation_running = False
                    return False
                
                return True
            except Exception as e:
                print(f"Error in simulation step: {e}")
                self.simulation_running = False
                return False
        return False
        
    def getVehicles(self):
        """Get all vehicles in the simulation"""
        if self.connected:
            try:
                vehicles = traci.vehicle.getIDList()
                print(f"Vehicles in simulation: {vehicles}")
                return vehicles
            except Exception as e:
                print(f"Error getting vehicles: {e}")
        return []
    
    def getVehicleData(self, vehicle_id):
        """Get data for a specific vehicle"""
        if self.connected:
            try:
                # Convert SUMO coordinates to scene coordinates
                # Note: This is a simplified conversion - you may need to adjust based on your network
                x, y = traci.vehicle.getPosition(vehicle_id)
                
                return {
                    'position': (x, y),  # Adjusted coordinates
                    'speed': traci.vehicle.getSpeed(vehicle_id),
                    'route': traci.vehicle.getRoute(vehicle_id),
                    'edge': traci.vehicle.getRoadID(vehicle_id),
                    'lane': traci.vehicle.getLaneID(vehicle_id),
                    'type': traci.vehicle.getTypeID(vehicle_id),
                    'angle': traci.vehicle.getAngle(vehicle_id)  # Useful for rotation
                }
            except Exception as e:
                print(f"Error getting vehicle data: {e}")
        return None
    
    def getSimulationTime(self):
        """Get current simulation time"""
        if self.connected:
            try:
                return traci.simulation.getTime()
            except Exception as e:
                print(f"Error getting simulation time: {e}")
        return 0
    
    def getTrafficLights(self):
        """Get all traffic lights in the simulation"""
        if self.connected:
            try:
                return traci.trafficlight.getIDList()
            except Exception as e:
                print(f"Error getting traffic lights: {e}")
        return []
    
    def getTrafficLightState(self, tl_id):
        """Get state of a specific traffic light"""
        if self.connected:
            try:
                return traci.trafficlight.getRedYellowGreenState(tl_id)
            except Exception as e:
                print(f"Error getting traffic light state: {e}")
        return None
    
    def setTrafficLightState(self, tl_id, state):
        """Set state of a specific traffic light"""
        if self.connected:
            try:
                traci.trafficlight.setRedYellowGreenState(tl_id, state)
                return True
            except Exception as e:
                print(f"Error setting traffic light state: {e}")
        return False
    
    def getNetworkBounds(self):
        """Get the boundaries of the network"""
        if self.connected:
            try:
                return traci.simulation.getNetBoundary()
            except Exception as e:
                print(f"Error getting network bounds: {e}")
        return [0, 0, 100, 100]  # Default bounds if not connectedclass TraciSimulationController:
    """
    Controller class for interacting with SUMO via TraCI
    """
    def __init__(self):
        self.connected = False
        self.simulation_running = False
        self.sumo_process = None
        self.port = 8813
    
    def connect(self, config_file=None, port=8813):
        """Connect to SUMO via TraCI"""
        if not TRACI_AVAILABLE:
            print("TraCI is not available")
            return False
        
        try:
            # Get SUMO_HOME
            if 'SUMO_HOME' not in os.environ:
                raise EnvironmentError("Please declare environment variable 'SUMO_HOME'")
            
            sumo_home = os.environ['SUMO_HOME']
            sumo_binary = os.path.join(sumo_home, 'bin', 'sumo')
            
            if not os.path.exists(sumo_binary) and not os.path.exists(sumo_binary + '.exe'):
                # Try with default path
                sumo_binary = 'sumo'
            
            self.port = port
            
            if config_file:
                # Start SUMO as a subprocess
                cmd = [
                    sumo_binary,
                    '-c', config_file,
                    '--remote-port', str(port),
                    '--start',  # Start immediately
                    '--no-warnings',  # Don't show warnings in console
                    '--no-step-log',  # Don't show step info in console
                ]
                
                # Start SUMO process
                self.sumo_process = subprocess.Popen(cmd, 
                                                    stdout=subprocess.PIPE, 
                                                    stderr=subprocess.PIPE)
                
                # Give it a moment to start
                time.sleep(1.0)
                
                # Connect to the running SUMO instance
                traci.connect(port=port)
            else:
                # Connect to an already running SUMO instance
                traci.connect(port=port)
            
            self.connected = True
            self.simulation_running = True
            return True
        
        except Exception as e:
            print(f"Error connecting to SUMO: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from SUMO"""
        if self.connected:
            try:
                traci.close()
                
                # Terminate the SUMO process if it's still running
                if self.sumo_process:
                    self.sumo_process.terminate()
                    self.sumo_process = None
                
                self.connected = False
                self.simulation_running = False
            except Exception as e:
                print(f"Error disconnecting from SUMO: {e}")
    
    def step(self):
        """Perform one simulation step"""
        if self.connected and self.simulation_running:
            try:
                traci.simulationStep()
                
                # Check if simulation has ended
                if traci.simulation.getMinExpectedNumber() <= 0:
                    # No more vehicles expected, we can end the simulation
                    self.simulation_running = False
                    return False
                
                return True
            except Exception as e:
                print(f"Error in simulation step: {e}")
                self.simulation_running = False
                return False
        return False
    
    def getVehicles(self):
        """Get all vehicles in the simulation"""
        if self.connected:
            try:
                return traci.vehicle.getIDList()
            except Exception as e:
                print(f"Error getting vehicles: {e}")
        return []
    
    def getVehicleData(self, vehicle_id):
        """Get data for a specific vehicle"""
        if self.connected:
            try:
                # Convert SUMO coordinates to scene coordinates
                # Note: This is a simplified conversion - you may need to adjust based on your network
                x, y = traci.vehicle.getPosition(vehicle_id)
                
                return {
                    'position': (x, y),  # Adjusted coordinates
                    'speed': traci.vehicle.getSpeed(vehicle_id),
                    'route': traci.vehicle.getRoute(vehicle_id),
                    'edge': traci.vehicle.getRoadID(vehicle_id),
                    'lane': traci.vehicle.getLaneID(vehicle_id),
                    'type': traci.vehicle.getTypeID(vehicle_id),
                    'angle': traci.vehicle.getAngle(vehicle_id)  # Useful for rotation
                }
            except Exception as e:
                print(f"Error getting vehicle data: {e}")
        return None
    
    def getSimulationTime(self):
        """Get current simulation time"""
        if self.connected:
            try:
                return traci.simulation.getTime()
            except Exception as e:
                print(f"Error getting simulation time: {e}")
        return 0
    
    def getTrafficLights(self):
        """Get all traffic lights in the simulation"""
        if self.connected:
            try:
                return traci.trafficlight.getIDList()
            except Exception as e:
                print(f"Error getting traffic lights: {e}")
        return []
    
    def getTrafficLightState(self, tl_id):
        """Get state of a specific traffic light"""
        if self.connected:
            try:
                return traci.trafficlight.getRedYellowGreenState(tl_id)
            except Exception as e:
                print(f"Error getting traffic light state: {e}")
        return None
    
    def setTrafficLightState(self, tl_id, state):
        """Set state of a specific traffic light"""
        if self.connected:
            try:
                traci.trafficlight.setRedYellowGreenState(tl_id, state)
                return True
            except Exception as e:
                print(f"Error setting traffic light state: {e}")
        return False
    
    def getNetworkBounds(self):
        """Get the boundaries of the network"""
        if self.connected:
            try:
                return traci.simulation.getNetBoundary()
            except Exception as e:
                print(f"Error getting network bounds: {e}")
        return [0, 0, 100, 100]  # Default bounds if not connected

class IntegratedSimulationVisualization(QWidget):
    """
    Widget for displaying SUMO simulation results directly in our application
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vehicle_objects = {}  # Store visual representations of vehicles
        self.network = None  # Will store reference to network data
        self.setupUI()
    
    def setupUI(self):
        """Set up the visualization UI"""
        main_layout = QVBoxLayout(self)
        
        # Create a graphics view for the simulation
        self.view = QGraphicsView(self)
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        
        # Set sci-fi look with dark background
        self.view.setStyleSheet("background-color: #101020;")
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        # Create tabs for different visualizations
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #4040bf;
                background-color: #1a1a2e;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #2a2a4a;
                color: #8080ff;
                border: 1px solid #4040bf;
                border-bottom-color: #4040bf;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
                padding: 5px;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background-color: #3a3a6a;
                color: #00FFFF;
            }
            QTabBar::tab:selected {
                border-bottom-color: #1a1a2e;
            }
        """)
        
        # Create visualization tab
        self.viz_tab = QWidget()
        viz_layout = QVBoxLayout(self.viz_tab)
        viz_layout.addWidget(self.view)
        
        # Create statistics tab
        self.stats_tab = QWidget()
        stats_layout = QVBoxLayout(self.stats_tab)
        
        # Add some statistics labels
        self.vehicles_label = QLabel("Vehicles: 0")
        self.vehicles_label.setStyleSheet("color: #00FFFF; font-size: 14px;")
        self.avg_speed_label = QLabel("Average Speed: 0 m/s")
        self.avg_speed_label.setStyleSheet("color: #00FFFF; font-size: 14px;")
        self.run_time_label = QLabel("Simulation Time: 0s")
        self.run_time_label.setStyleSheet("color: #00FFFF; font-size: 14px;")
        
        stats_layout.addWidget(self.vehicles_label)
        stats_layout.addWidget(self.avg_speed_label)
        stats_layout.addWidget(self.run_time_label)
        stats_layout.addStretch()
        
        # Add tabs
        self.tabs.addTab(self.viz_tab, "Visualization")
        self.tabs.addTab(self.stats_tab, "Statistics")
        
        main_layout.addWidget(self.tabs)
        
        # Add control panel below the visualization
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        
        # Add visualization controls
        self.show_vehicle_ids = QCheckBox("Show Vehicle IDs")
        self.show_vehicle_ids.setStyleSheet("color: #00FFAA;")
        self.show_vehicle_ids.setChecked(True)
        
        self.show_speed_colors = QCheckBox("Color by Speed")
        self.show_speed_colors.setStyleSheet("color: #00FFAA;")
        self.show_speed_colors.setChecked(True)
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(50, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #4040bf;
                height: 8px;
                background: #2a2a4a;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00FFFF;
                border: 1px solid #00FFFF;
                width: 18px;
                margin: -8px 0;
                border-radius: 9px;
            }
        """)
        self.zoom_slider.valueChanged.connect(self.updateZoom)
        
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet("color: #00FFAA;")
        
        control_layout.addWidget(self.show_vehicle_ids)
        control_layout.addWidget(self.show_speed_colors)
        control_layout.addStretch()
        control_layout.addWidget(zoom_label)
        control_layout.addWidget(self.zoom_slider)
        
        main_layout.addWidget(control_panel)
    
    def setNetworkData(self, network_edges, network_nodes):
        """Set the network data for visualization"""
        self.network = {
            'edges': network_edges,
            'nodes': network_nodes
        }
        
        # Clear the scene
        self.scene.clear()
        
        # Draw the network
        self.drawNetwork()
    
    def drawNetwork(self):
        """Draw the network in the visualization"""
        if not self.network:
            return
        
        # Draw nodes (junctions)
        for node_id, x, y in self.network['nodes']:
            # Create a node representation
            node = QGraphicsEllipseItem(x - 6, y - 6, 12, 12)
            node.setPen(QPen(QColor("#4040bf"), 1))
            node.setBrush(QBrush(QColor(64, 64, 191, 100)))
            self.scene.addItem(node)
        
        # Draw edges (roads)
        for edge_id, from_node, to_node, lanes, speed in self.network['edges']:
            # Find the nodes
            from_coords = None
            to_coords = None
            
            for node_id, x, y in self.network['nodes']:
                if node_id == from_node:
                    from_coords = (x, y)
                elif node_id == to_node:
                    to_coords = (x, y)
            
            if from_coords and to_coords:
                # Create an edge representation
                edge = QGraphicsLineItem(from_coords[0], from_coords[1], to_coords[0], to_coords[1])
                
                # Set color based on speed
                if speed > 27.78:  # > 100 km/h
                    color = QColor("#FF3300")  # Red for highways
                elif speed > 13.89:  # > 50 km/h
                    color = QColor("#FFAA00")  # Orange for main roads
                else:
                    color = QColor("#00FFAA")  # Cyan-green for local roads
                
                # Set width based on lanes
                width = 1 + lanes
                
                edge.setPen(QPen(color, width, Qt.PenStyle.SolidLine, 
                              Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                self.scene.addItem(edge)
        
        # Set the scene rect to fit the network
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def updateVehicles(self, vehicles_data):
        """Update vehicle visualizations based on TraCI data"""
        # vehicles_data is a dict with vehicle_id as key and position, speed, etc. as values
        
        # Remove vehicles that are no longer in the simulation
        for vehicle_id in list(self.vehicle_objects.keys()):
            if vehicle_id not in vehicles_data:
                # Remove the vehicle visualization
                for item in self.vehicle_objects[vehicle_id]:
                    self.scene.removeItem(item)
                del self.vehicle_objects[vehicle_id]
        
        # Add or update vehicles
        for vehicle_id, data in vehicles_data.items():
            if vehicle_id in self.vehicle_objects:
                # Update existing vehicle
                self.updateVehiclePosition(vehicle_id, data)
            else:
                # Create new vehicle visualization
                self.createVehicleVisualization(vehicle_id, data)
        
        # Update statistics
        self.updateStatistics(vehicles_data)
    
    def createVehicleVisualization(self, vehicle_id, data):
        """Create a new vehicle visualization"""
        x, y = data['position']
        speed = data['speed']
        
        # Create vehicle representation (a simple rectangle)
        vehicle = QGraphicsRectItem(x - 3, y - 2, 6, 4)
        
        # Color based on speed if enabled
        if self.show_speed_colors.isChecked():
            # Higher speed = more red
            speed_ratio = min(speed / 30.0, 1.0)  # Normalize to 0-1
            r = int(255 * speed_ratio)
            g = int(255 * (1 - speed_ratio))
            b = 100
            vehicle.setBrush(QBrush(QColor(r, g, b)))
        else:
            # Default color
            vehicle.setBrush(QBrush(QColor("#FFFF00")))
        
        vehicle.setPen(QPen(QColor("#FFFFFF")))
        self.scene.addItem(vehicle)
        
        # Create label if enabled
        label = None
        if self.show_vehicle_ids.isChecked():
            label = self.scene.addText(vehicle_id, QFont("Arial", 6))
            label.setDefaultTextColor(QColor("#FFFFFF"))
            label.setPos(x + 5, y - 10)
        
        # Store vehicle objects
        self.vehicle_objects[vehicle_id] = [vehicle, label]
    
    def updateVehiclePosition(self, vehicle_id, data):
        """Update the position of an existing vehicle"""
        if vehicle_id not in self.vehicle_objects:
            return
            
        x, y = data['position']
        speed = data['speed']
        
        vehicle, label = self.vehicle_objects[vehicle_id]
        
        # Update vehicle position
        vehicle.setRect(x - 3, y - 2, 6, 4)
        
        # Update color based on speed if enabled
        if self.show_speed_colors.isChecked():
            # Higher speed = more red
            speed_ratio = min(speed / 30.0, 1.0)  # Normalize to 0-1
            r = int(255 * speed_ratio)
            g = int(255 * (1 - speed_ratio))
            b = 100
            vehicle.setBrush(QBrush(QColor(r, g, b)))
        
        # Update label position if it exists
        if label:
            label.setPos(x + 5, y - 10)
            label.setVisible(self.show_vehicle_ids.isChecked())
    
    def updateStatistics(self, vehicles_data):
        """Update the statistics display"""
        num_vehicles = len(vehicles_data)
        self.vehicles_label.setText(f"Vehicles: {num_vehicles}")
        
        if num_vehicles > 0:
            # Calculate average speed
            total_speed = sum(data['speed'] for data in vehicles_data.values())
            avg_speed = total_speed / num_vehicles
            self.avg_speed_label.setText(f"Average Speed: {avg_speed:.2f} m/s")
        else:
            self.avg_speed_label.setText("Average Speed: 0 m/s")
    
    def updateSimulationTime(self, time):
        """Update the simulation time display"""
        self.run_time_label.setText(f"Simulation Time: {time:.1f}s")
    
    def updateZoom(self, value):
        """Update the zoom level"""
        scale = value / 100.0
        transform = QTransform()
        transform.scale(scale, scale)
        self.view.setTransform(transform)
    
    def resetView(self):
        """Reset the view to show the entire network"""
        self.zoom_slider.setValue(100)
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
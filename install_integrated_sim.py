#!/usr/bin/env python3
"""
SUMO Sci-Fi Dashboard - Integrated Simulation Installer
-------------------------------------------------------
This script updates the SUMO Sci-Fi Dashboard application to use integrated
simulation instead of launching the external SUMO GUI.
"""

import os
import sys
import shutil
import tempfile
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the specified file"""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return False
    
    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")
    return True

def create_visualization_settings():
    """Create visualization settings file for SUMO"""
    settings_file = "visualization.settings.xml"
    
    with open(settings_file, 'w') as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<viewsettings>
    <scheme name="sci-fi">
        <background backgroundColor="0.05,0.05,0.1" showGrid="1" gridXSize="100.00" gridYSize="100.00"/>
        <edges laneEdgeMode="0" laneShowBorders="1" showLinkDecals="1" showRails="1" hideConnectors="0"
               edgeName_show="0" edgeName_size="50.00" edgeName_color="1.00,0.50,0.00" 
               edgeValue_show="0" edgeValue_size="100.00" edgeValue_color="1.00,0.50,0.00">
            <colorScheme name="sci-fi">
                <entry color="0.00,1.00,0.67" name="slow"/>
                <entry color="1.00,0.67,0.00" name="medium"/>
                <entry color="1.00,0.33,0.00" name="fast"/>
            </colorScheme>
        </edges>
        <vehicles vehicleMode="8" vehicleQuality="2" vehicle_minSize="1.00" vehicle_exaggeration="1.00" 
                 vehicle_constantSize="0" showBlinker="1"
                 vehicleName_show="0" vehicleName_size="50.00" vehicleName_color="0.80,0.60,1.00">
            <colorScheme name="by speed" interpolated="1">
                <entry color="0.00,1.00,0.67" name="slow"/>
                <entry color="1.00,0.67,0.00" name="medium"/>
                <entry color="1.00,0.33,0.00" name="fast"/>
            </colorScheme>
        </vehicles>
        <junctions junctionMode="0" drawLinkTLIndex="0" drawLinkJunctionIndex="0"
                  junctionName_show="0" junctionName_size="50.00" junctionName_color="0.00,1.00,1.00">
            <colorScheme name="sci-fi">
                <entry color="0.00,1.00,1.00"/>
            </colorScheme>
        </junctions>
    </scheme>
</viewsettings>
""")
    
    print(f"Created {settings_file}")
    return True

def update_main_app():
    """Update main_app.py to integrate with the new visualization"""
    file_path = "main_app.py"
    
    if not backup_file(file_path):
        return False
    
    try:
        # Read the original file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Update imports - make sure we import IntegratedSimulationVisualization
        if "from vehicle_simulator import SimulationControlPanel, SimulationVisualization" in content:
            content = content.replace(
                "from vehicle_simulator import SimulationControlPanel, SimulationVisualization",
                "from vehicle_simulator import SimulationControlPanel, IntegratedSimulationVisualization"
            )
        
        # Update the setupMainContent method to use IntegratedSimulationVisualization
        if "self.simulation_viz = SimulationVisualization()" in content:
            content = content.replace(
                "self.simulation_viz = SimulationVisualization()",
                "self.simulation_viz = IntegratedSimulationVisualization()"
            )
        
        # Add updateSimulationVisualization method
        update_sim_method = """    def updateSimulationVisualization(self):
        \"\"\"Update the simulation visualization with current data\"\"\"
        # Get vehicle data from TraCI controller
        if hasattr(self.simulation_panel, 'traci_controller') and self.simulation_panel.traci_controller:
            traci_controller = self.simulation_panel.traci_controller
            
            # Get all vehicles
            vehicles = traci_controller.getVehicles()
            
            # Collect vehicle data
            vehicle_data = {}
            for vehicle_id in vehicles:
                data = traci_controller.getVehicleData(vehicle_id)
                if data:
                    vehicle_data[vehicle_id] = data
            
            # Update visualization with vehicle data
            self.simulation_viz.updateVehicles(vehicle_data)
            
            # Update simulation time
            simulation_time = traci_controller.getSimulationTime()
            self.simulation_viz.updateSimulationTime(simulation_time)
    """
        
        # Check if method already exists
        if "def updateSimulationVisualization" not in content:
            # Find a good place to insert the method - before onSimulationStarted
            if "def onSimulationStarted" in content:
                insert_pos = content.find("def onSimulationStarted")
                content = content[:insert_pos] + update_sim_method + content[insert_pos:]
        
        # Update onSimulationStarted method
        sim_started_method = """    def onSimulationStarted(self, config_file):
        \"\"\"Handle simulation start event\"\"\"
        # Switch to simulation tab
        self.content_tabs.setCurrentIndex(1)
        
        # Store config file
        self.current_config_file = config_file
        
        # Export network data for visualization
        nodes_data, edges_data = self.network_editor.exportToSumo()
        
        # Pass network data to visualization component
        self.simulation_viz.setNetworkData(edges_data, nodes_data)
        
        # Connect simulation update signal
        if hasattr(self.simulation_panel, 'simulation_timer'):
            self.simulation_panel.simulation_timer.timeout.connect(self.updateSimulationVisualization)
        
        self.statusBar.showMessage("Simulation started")
    """
        
        # Replace the existing method
        if "def onSimulationStarted" in content:
            start_idx = content.find("def onSimulationStarted")
            end_idx = content.find("def ", start_idx + 5)  # Find the next method
            if end_idx > start_idx:
                content = content[:start_idx] + sim_started_method + content[end_idx:]
        
        # Update onSimulationStopped method
        sim_stopped_method = """    def onSimulationStopped(self):
        \"\"\"Handle simulation stop event\"\"\"
        # Disconnect simulation update signal to prevent errors
        if hasattr(self.simulation_panel, 'simulation_timer'):
            try:
                self.simulation_panel.simulation_timer.timeout.disconnect(self.updateSimulationVisualization)
            except TypeError:
                # Signal was not connected
                pass
        
        self.statusBar.showMessage("Simulation stopped")
        
        # Reset visualization if needed
        self.simulation_viz.resetView()
    """
        
        # Replace the existing method
        if "def onSimulationStopped" in content:
            start_idx = content.find("def onSimulationStopped")
            end_idx = content.find("def ", start_idx + 5)  # Find the next method
            if end_idx > start_idx:
                content = content[:start_idx] + sim_stopped_method + content[end_idx:]
        
        # Write back the updated content
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"Successfully updated {file_path}")
        return True
    
    except Exception as e:
        print(f"Error updating {file_path}: {str(e)}")
        return False

def update_vehicle_simulator():
    """Update the vehicle_simulator.py file with integrated visualization"""
    file_path = "vehicle_simulator.py"
    
    if not backup_file(file_path):
        return False
    
    try:
        # Read the original file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Update the imports
        imports_update = """
import os
import sys
import subprocess
import tempfile
import time
import threading
import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QSlider, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
                            QGroupBox, QFormLayout, QFileDialog, QMessageBox,
                            QProgressBar, QTabWidget, QGraphicsView, QGraphicsScene, 
                            QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QProcess, QPointF, QLineF, QTransform
from PyQt6.QtGui import QFont, QColor, QPen, QBrush, QPainter
"""
        
        if "import os" in content:
            content = content.replace(content[:content.find("import os")], imports_update)
        
        # Update the SimulationControlPanel class
        control_panel_class = """class SimulationControlPanel(QWidget):
    \"\"\"
    Control panel for simulation parameters and execution
    \"\"\"
    simulation_started = pyqtSignal(str)  # Emits config file path
    simulation_stopped = pyqtSignal()
    simulation_data_updated = pyqtSignal(dict)  # Emits vehicle data for visualization
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sumo_process = None
        self.traci_controller = None
        self.setupUI()
"""
        if "class SimulationControlPanel" in content:
            start_idx = content.find("class SimulationControlPanel")
            end_idx = content.find("def setupUI", start_idx)
            if end_idx > start_idx:
                content = content[:start_idx] + control_panel_class + content[end_idx:]
        
        # Update the startSimulation method
        start_simulation_method = """    
    def startSimulation(self):
        \"\"\"Start the SUMO simulation\"\"\"
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
"""
        if "def startSimulation" in content:
            start_idx = content.find("def startSimulation")
            end_idx = content.find("def", start_idx + 10)  # Find the next method
            if end_idx > start_idx:
                content = content[:start_idx] + start_simulation_method + content[end_idx:]
        
        # Add step simulation method
        step_simulation_method = """    def stepSimulation(self):
        \"\"\"Perform a single simulation step\"\"\"
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
            
            # Calculate progress percentage
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
    
    def updateSimulationData(self):
        \"\"\"Get current simulation data and update visualization\"\"\"
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
"""
        
        # Find stopSimulation method and insert before it
        if "def stopSimulation" in content:
            start_idx = content.find("def stopSimulation")
            content = content[:start_idx] + step_simulation_method + content[start_idx:]
        
        # Update stopSimulation method
        stop_simulation_method = """    def stopSimulation(self):
        \"\"\"Stop the running simulation\"\"\"
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
"""
        if "def stopSimulation" in content:
            start_idx = content.find("def stopSimulation")
            end_idx = content.find("def", start_idx + 10)  # Find the next method
            if end_idx > start_idx:
                content = content[:start_idx] + stop_simulation_method + content[end_idx:]
        
        # Update createConfigFile method
        config_file_method = """    def createConfigFile(self):
        \"\"\"Create a SUMO configuration file for headless operation\"\"\"
        config_file = os.path.join(self.temp_dir, "sim.sumocfg")
        
        with open(config_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\\n')
            f.write('<configuration>\\n')
            
            f.write('    <input>\\n')
            f.write(f'        <net-file value="{os.path.basename(self.network_file)}"/>\\n')
            f.write(f'        <route-files value="{os.path.basename(self.route_file)}"/>\\n')
            f.write('    </input>\\n')
            
            f.write('    <time>\\n')
            f.write('        <begin value="0"/>\\n')
            f.write(f'        <end value="{self.duration.value()}"/>\\n')
            f.write(f'        <step-length value="{self.step_length.value()}"/>\\n')
            f.write('    </time>\\n')
            
            # Important: Add TraCI section to make sure TraCI server is started
            f.write('    <traci_server>\\n')
            f.write('        <remote-port value="8813"/>\\n')
            f.write('    </traci_server>\\n')
            
            # Important: Turn off GUI
            f.write('    <gui_only>\\n')
            f.write('        <quit-on-end value="true"/>\\n')
            f.write('        <start value="false"/>\\n')
            f.write('    </gui_only>\\n')
            
            if self.collect_data.isChecked():
                f.write('    <output>\\n')
                f.write(f'        <summary-output value="{os.path.join(self.temp_dir, "summary.xml")}"/>\\n')
                f.write(f'        <tripinfo-output value="{os.path.join(self.temp_dir, "tripinfo.xml")}"/>\\n')
                f.write('    </output>\\n')
            
            f.write('    <report>\\n')
            f.write('        <verbose value="false"/>\\n')
            f.write('        <no-step-log value="true"/>\\n')
            f.write('        <no-warnings value="true"/>\\n')
            f.write('    </report>\\n')
            
            f.write('</configuration>\\n')
        
        # Copy network file to temp dir if it's not already there
        if not os.path.exists(os.path.join(self.temp_dir, os.path.basename(self.network_file))):
            import shutil
            shutil.copy(self.network_file, self.temp_dir)
        
        return config_file
"""
        if "def createConfigFile" in content:
            start_idx = content.find("def createConfigFile")
            end_idx = content.find("def", start_idx + 10)  # Find the next method
            if end_idx > start_idx:
                content = content[:start_idx] + config_file_method + content[end_idx:]
        
        # Add the new IntegratedSimulationVisualization class
        integrated_viz_class = """
class IntegratedSimulationVisualization(QWidget):
    \"\"\"
    Widget for displaying SUMO simulation results directly in our application
    \"\"\"
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vehicle_objects = {}  # Store visual representations of vehicles
        self.network = None  # Will store reference to network data
        self.setupUI()
    
    def setupUI(self):
        \"\"\"Set up the visualization UI\"\"\"
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
        self.tabs.setStyleSheet(\"\"\"
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
        \"\"\")
        
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
        self.zoom_slider.setStyleSheet('''
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
        ''')
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
        self.network = {
            'edges': network_edges,
            'nodes': network_nodes
        }
        
        # Clear the scene
        self.scene.clear()
        
        # Draw the network
        self.drawNetwork()
    
    def drawNetwork(self):
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
        # vehicles_data is a dict with vehicle_id as key and position, speed, etc. as values
        
        # Remove vehicles that are no longer in the simulation
        for vehicle_id in list(self.vehicle_objects.keys()):
            if vehicle_id not in vehicles_data:
                # Remove the vehicle visualization
                for item in self.vehicle_objects[vehicle_id]:
                    if item is not None:
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
        self.run_time_label.setText(f"Simulation Time: {time:.1f}s")
    
    def updateZoom(self, value):
        scale = value / 100.0
        transform = QTransform()
        transform.scale(scale, scale)
        self.view.setTransform(transform)
    
    def resetView(self):
        self.zoom_slider.setValue(100)
        if hasattr(self, 'scene') and self.scene is not None:
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
"""

        # Update the TraciSimulationController class
        traci_controller_class = """
class TraciSimulationController:
    def __init__(self):
        self.connected = False
        self.simulation_running = False
        self.sumo_process = None
        self.port = 8813
    
    def connect(self, config_file=None, port=8813):
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
        if self.connected:
            try:
                return traci.vehicle.getIDList()
            except Exception as e:
                print(f"Error getting vehicles: {e}")
        return []
    
    def getVehicleData(self, vehicle_id):
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
        if self.connected:
            try:
                return traci.simulation.getTime()
            except Exception as e:
                print(f"Error getting simulation time: {e}")
        return 0
    
    def getTrafficLights(self):
        if self.connected:
            try:
                return traci.trafficlight.getIDList()
            except Exception as e:
                print(f"Error getting traffic lights: {e}")
        return []
    
    def getTrafficLightState(self, tl_id):
        if self.connected:
            try:
                return traci.trafficlight.getRedYellowGreenState(tl_id)
            except Exception as e:
                print(f"Error getting traffic light state: {e}")
        return None
    
    def setTrafficLightState(self, tl_id, state):
        if self.connected:
            try:
                traci.trafficlight.setRedYellowGreenState(tl_id, state)
                return True
            except Exception as e:
                print(f"Error setting traffic light state: {e}")
        return False
    
    def getNetworkBounds(self):
        if self.connected:
            try:
                return traci.simulation.getNetBoundary()
            except Exception as e:
                print(f"Error getting network bounds: {e}")
        return [0, 0, 100, 100]  # Default bounds if not connected
"""

        # Add the new classes to the end of the file
        content += "\n" + integrated_viz_class + "\n" + traci_controller_class

        # Write back the updated content
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"Successfully updated {file_path}")
        return True
    
    except Exception as e:
        print(f"Error updating {file_path}: {str(e)}")
        return False
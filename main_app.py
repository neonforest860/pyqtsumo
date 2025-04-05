import sys
import os
import tempfile
from PyQt6.QtCore import Qt, QSettings, QTimer, pyqtSlot
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette, QGuiApplication
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QSplitter, QMessageBox, QFileDialog,
                            QTabWidget, QToolBar, QStatusBar, QLabel,
                            QDialog,QGraphicsView, QLineEdit, QFormLayout, QPushButton, QComboBox, QDoubleSpinBox)
from PyQt6.QtGui import QAction

# Import our custom modules
from network_editor import AdvancedNetworkEditor
from vehicle_simulator import SimulationControlPanel, SimulationVisualization, TraciSimulationController, IntegratedSimulationVisualization
from sumo_utils import SumoUtils

class MainWindow(QMainWindow):
    """Main application window with sci-fi theme"""
    def __init__(self):
        super().__init__()
        
        # Set application properties
        self.setWindowTitle("SUMO Sci-Fi Dashboard")
        self.setMinimumSize(1200, 800)
        
        # Initialize SUMO utilities
        try:
            self.sumo_utils = SumoUtils()
        except Exception as e:
            QMessageBox.critical(
                self, 
                "SUMO Configuration Error", 
                f"Error initializing SUMO utilities: {str(e)}\n\n"
                "Please make sure SUMO is installed correctly and the SUMO_HOME environment variable is set."
            )
            # We'll continue anyway, but some functionality may be limited
        
        # Set up the central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Set up the main layout
        self.main_layout = QHBoxLayout(self.central_widget)
        
        # Create the sidebar
        self.setupSidebar()
        
        # Create the main content area
        self.setupMainContent()
        
        # Set up status bar
        self.setupStatusBar()
        
        # Set up menu bar and toolbar
        self.setupMenuBar()
        self.setupToolBar()
        
        # Initialize variables
        self.current_network_file = None
        self.current_config_file = None
        self.simulation_controller = TraciSimulationController()
        
        # Set up timer for periodic updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.updateApplication)
        self.update_timer.start(500)  # Update every 500ms
        
        # Apply sci-fi theme
        self.applySciFiTheme()
        
        # Load any saved settings
        self.loadSettings()
    
    def setupSidebar(self):
        """Set up the sidebar with menu options"""
        # Create sidebar container
        self.sidebar = QWidget()
        self.sidebar.setMaximumWidth(220)
        self.sidebar.setMinimumWidth(180)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Style the sidebar
        self.sidebar.setStyleSheet("""
            background-color: #1a1a2e;
            color: #e6e6ff;
            border-right: 1px solid #4040bf;
            padding: 0px;
        """)
        
        # Create tabs for different control groups
        sidebar_tabs = QTabWidget()
        sidebar_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #1a1a2e;
            }
            QTabBar::tab {
                background-color: #2a2a4a;
                color: #8080ff;
                border: 1px solid #4040bf;
                border-bottom-color: #4040bf;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 80px;
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
        
        # Network tab
        self.network_panel = QWidget()
        network_layout = QVBoxLayout(self.network_panel)
        network_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create network control buttons
        btn_style = """
            QPushButton {
                background-color: #2a2a4a;
                color: #00FFFF;
                border: 1px solid #4040bf;
                border-radius: 4px;
                padding: 8px;
                text-align: left;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                background-color: #3a3a6a;
            }
            QPushButton:pressed {
                background-color: #4a4a8a;
            }
        """
        
        self.new_network_btn = QPushButton("🆕 New Network")
        self.new_network_btn.setStyleSheet(btn_style)
        self.new_network_btn.clicked.connect(self.newNetwork)
        
        self.load_network_btn = QPushButton("📂 Load Network")
        self.load_network_btn.setStyleSheet(btn_style)
        self.load_network_btn.clicked.connect(self.loadNetwork)
        
        self.save_network_btn = QPushButton("💾 Save Network")
        self.save_network_btn.setStyleSheet(btn_style)
        self.save_network_btn.clicked.connect(self.saveNetwork)
        
        self.draw_mode_btn = QPushButton("✏️ Draw Mode")
        self.draw_mode_btn.setStyleSheet(btn_style)
        self.draw_mode_btn.clicked.connect(self.toggleDrawMode)
        self.draw_mode_active = False
        
        network_layout.addWidget(self.new_network_btn)
        network_layout.addWidget(self.load_network_btn)
        network_layout.addWidget(self.save_network_btn)
        network_layout.addWidget(self.draw_mode_btn)
        network_layout.addStretch()
        
        # Simulation tab
        self.simulation_panel = SimulationControlPanel()
        
        # Add tabs to sidebar
        sidebar_tabs.addTab(self.network_panel, "Network")
        sidebar_tabs.addTab(self.simulation_panel, "Simulation")
        
        # Add tabs to sidebar layout
        sidebar_layout.addWidget(sidebar_tabs)
        
        # Add status info at bottom of sidebar
        self.sidebar_status = QLabel("Ready")
        self.sidebar_status.setStyleSheet("""
            color: #00FF00;
            padding: 5px;
            border-top: 1px solid #4040bf;
            font-weight: bold;
        """)
        sidebar_layout.addWidget(self.sidebar_status)
        
        # Add sidebar to main layout
        self.main_layout.addWidget(self.sidebar)
        
        # Connect simulation signals
        self.simulation_panel.simulation_started.connect(self.onSimulationStarted)
        self.simulation_panel.simulation_stopped.connect(self.onSimulationStopped)
    
    def setupMainContent(self):
        """Set up the main content area with tabs"""
        # Create content tabs widget
        self.content_tabs = QTabWidget()
        self.content_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #4040bf;
                background-color: #101020;
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
                border-bottom-color: #101020;
            }
        """)
        
        # Network editor tab
        self.network_editor = AdvancedNetworkEditor()
        
        # Simulation visualization tab
        self.simulation_viz = IntegratedSimulationVisualization()
        
        # Add tabs
        self.content_tabs.addTab(self.network_editor, "Network Editor")
        self.content_tabs.addTab(self.simulation_viz, "Simulation")
        
        # Connect tab change signal
        self.content_tabs.currentChanged.connect(self.onTabChanged)
        
        # Add content tabs to main layout
        self.main_layout.addWidget(self.content_tabs)
    def setupStatusBar(self):
        """Set up the status bar"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Style the status bar
        self.statusBar.setStyleSheet("""
            background-color: #1a1a2e;
            color: #00FFFF;
        """)
        
        # Add permanent widgets
        self.status_network = QLabel("No Network Loaded")
        self.status_coords = QLabel("X: 0, Y: 0")
        self.status_simulation = QLabel("Simulation: Inactive")
        
        self.statusBar.addPermanentWidget(self.status_network)
        self.statusBar.addPermanentWidget(self.status_coords)
        self.statusBar.addPermanentWidget(self.status_simulation)
        
        # Set initial message
        self.statusBar.showMessage("Ready")
    
    def setupMenuBar(self):
        """Set up the application menu bar"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #1a1a2e;
                color: #e6e6ff;
            }
            QMenuBar::item:selected {
                background-color: #3a3a6a;
            }
            QMenu {
                background-color: #1a1a2e;
                color: #e6e6ff;
                border: 1px solid #4040bf;
            }
            QMenu::item:selected {
                background-color: #3a3a6a;
            }
        """)
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # File actions
        new_action = QAction("New Network", self)
        new_action.triggered.connect(self.newNetwork)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open Network", self)
        open_action.triggered.connect(self.loadNetwork)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save Network", self)
        save_action.triggered.connect(self.saveNetwork)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save Network As...", self)
        save_as_action.triggered.connect(self.saveNetworkAs)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        import_action = QAction("Import SUMO Network...", self)
        import_action.triggered.connect(self.importSumoNetwork)
        file_menu.addAction(import_action)
        
        export_action = QAction("Export to SUMO...", self)
        export_action.triggered.connect(self.exportToSumo)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        # Edit actions
        draw_action = QAction("Draw Mode", self)
        draw_action.setCheckable(True)
        draw_action.triggered.connect(self.toggleDrawMode)
        edit_menu.addAction(draw_action)
        
        edit_menu.addSeparator()
        
        clear_action = QAction("Clear Network", self)
        clear_action.triggered.connect(self.clearNetwork)
        edit_menu.addAction(clear_action)
        
        # Simulation menu
        sim_menu = menubar.addMenu("Simulation")
        
        # Simulation actions
        start_sim_action = QAction("Start Simulation", self)
        start_sim_action.triggered.connect(lambda: self.simulation_panel.startSimulation())
        sim_menu.addAction(start_sim_action)
        
        stop_sim_action = QAction("Stop Simulation", self)
        stop_sim_action.triggered.connect(lambda: self.simulation_panel.stopSimulation())
        sim_menu.addAction(stop_sim_action)
        
        reset_sim_action = QAction("Reset Simulation", self)
        reset_sim_action.triggered.connect(lambda: self.simulation_panel.resetSimulation())
        sim_menu.addAction(reset_sim_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # View actions
        network_view_action = QAction("Network Editor", self)
        network_view_action.triggered.connect(lambda: self.content_tabs.setCurrentIndex(0))
        view_menu.addAction(network_view_action)
        
        sim_view_action = QAction("Simulation View", self)
        sim_view_action.triggered.connect(lambda: self.content_tabs.setCurrentIndex(1))
        view_menu.addAction(sim_view_action)
        
        view_menu.addSeparator()
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        # Help actions
        about_action = QAction("About", self)
        about_action.triggered.connect(self.showAboutDialog)
        help_menu.addAction(about_action)
        
        help_action = QAction("Help", self)
        help_action.triggered.connect(self.showHelpDialog)
        help_menu.addAction(help_action)
    
    def setupToolBar(self):
        """Set up the application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #1a1a2e;
                border-bottom: 1px solid #4040bf;
                spacing: 5px;
            }
            QToolButton {
                background-color: #2a2a4a;
                color: #00FFFF;
                border: 1px solid #4040bf;
                border-radius: 4px;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #3a3a6a;
            }
            QToolButton:pressed {
                background-color: #4a4a8a;
            }
        """)
        
        # Add toolbar actions
        new_action = QAction("🆕 New", self)
        new_action.triggered.connect(self.newNetwork)
        toolbar.addAction(new_action)
        
        open_action = QAction("📂 Open", self)
        open_action.triggered.connect(self.loadNetwork)
        toolbar.addAction(open_action)
        
        save_action = QAction("💾 Save", self)
        save_action.triggered.connect(self.saveNetwork)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        draw_action = QAction("✏️ Draw", self)
        draw_action.setCheckable(True)
        draw_action.triggered.connect(self.toggleDrawMode)
        toolbar.addAction(draw_action)
        
        toolbar.addSeparator()
        
        start_sim_action = QAction("▶️ Start Sim", self)
        start_sim_action.triggered.connect(lambda: self.simulation_panel.startSimulation())
        toolbar.addAction(start_sim_action)
        
        stop_sim_action = QAction("⏹️ Stop Sim", self)
        stop_sim_action.triggered.connect(lambda: self.simulation_panel.stopSimulation())
        toolbar.addAction(stop_sim_action)
        
        self.addToolBar(toolbar)
    
    def applySciFiTheme(self):
        """Apply sci-fi styling to the application"""
        # Set application palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#101020"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#e6e6ff"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#1a1a2e"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#2a2a4a"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2a2a4a"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#00FFFF"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#e6e6ff"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#2a2a4a"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#00FFFF"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#4040bf"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#00FFFF"))
        
        QApplication.instance().setPalette(palette)
        
        # Set application style sheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #101020;
                color: #e6e6ff;
            }
            QToolTip { 
                color: #00FFFF;
                background-color: #2a2a4a;
                border: 1px solid #4040bf;
            }
            QSplitter::handle {
                background-color: #4040bf;
            }
            QSplitter::handle:horizontal {
                width: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
        """)
    
    def loadSettings(self):
        """Load application settings"""
        settings = QSettings("SumoSciFi", "Dashboard")
        
        # Load window geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Load window state
        state = settings.value("windowState")
        if state:
            self.restoreState(state)
        
        # Load recent files
        recent_files = settings.value("recentFiles", [])
        # We would populate a recent files menu here
    
    def saveSettings(self):
        """Save application settings"""
        settings = QSettings("SumoSciFi", "Dashboard")
        
        # Save window geometry
        settings.setValue("geometry", self.saveGeometry())
        
        # Save window state
        settings.setValue("windowState", self.saveState())
        
        # Save current network file
        if self.current_network_file:
            settings.setValue("lastNetworkFile", self.current_network_file)
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Check if there are unsaved changes
        # For now, we'll just ask for confirmation
        reply = QMessageBox.question(
            self,
            "Exit Application",
            "Are you sure you want to exit? Any unsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Save settings
            self.saveSettings()
            
            # Stop any running simulation
            if hasattr(self, 'simulation_panel'):
                self.simulation_panel.stopSimulation()
            
            # Accept the close event
            event.accept()
        else:
            # Ignore the close event
            event.ignore()
        
    def updateApplication(self):
        """Periodic update for application state"""
        # Update status bar with cursor coordinates if in network editor
        # Only attempt to check currentIndex if content_tabs exists
        if hasattr(self, 'content_tabs') and self.content_tabs.currentIndex() == 0:
            # This would be implemented to show cursor position in scene coordinates
            # For now, we'll just show a placeholder
            self.status_coords.setText("X: -, Y: -")
        
        # Update simulation status
        if hasattr(self, 'simulation_panel'):
            if self.simulation_panel.stop_btn.isEnabled():
                self.status_simulation.setText("Simulation: Active")
                self.status_simulation.setStyleSheet("color: #FF9900; font-weight: bold;")
            else:
                self.status_simulation.setText("Simulation: Inactive")
                self.status_simulation.setStyleSheet("color: #00FFFF;")
    
    def newNetwork(self):
        """Create a new network"""
        # Check for unsaved changes first
        reply = QMessageBox.question(
            self,
            "New Network",
            "Create a new network? Any unsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear the network editor
            self.network_editor.clear()
            
            # Reset current network file
            self.current_network_file = None
            
            # Update status
            self.status_network.setText("New Network")
            self.statusBar.showMessage("New network created", 3000)
    
    def loadNetwork(self):
        """Load a network from file"""
        # File dialog to select network file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Network",
            "",
            "SUMO Network Files (*.net.xml);;All Files (*)"
        )
        
        if file_path:
            try:
                # Extract network data
                nodes_data, edges_data = self.sumo_utils.extract_network_data(file_path)
                
                # Load into network editor
                self.network_editor.importFromSumo(nodes_data, edges_data)
                
                # Update current network file
                self.current_network_file = file_path
                
                # Set the network file for simulation
                self.simulation_panel.setNetworkFile(file_path)
                
                # Update status
                self.status_network.setText(f"Network: {os.path.basename(file_path)}")
                self.statusBar.showMessage(f"Loaded network from {file_path}", 3000)
            
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Loading Network",
                    f"Failed to load network: {str(e)}"
                )
    
    def saveNetwork(self):
        """Save network to file"""
        if not self.current_network_file:
            # If no file is currently set, use Save As
            self.saveNetworkAs()
        else:
            self.saveNetworkToFile(self.current_network_file)
    
    def saveNetworkAs(self):
        """Save network to a new file"""
        # File dialog to select save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Network",
            "",
            "SUMO Network Files (*.net.xml);;All Files (*)"
        )
        
        if file_path:
            # Ensure file has .net.xml extension
            if not file_path.endswith('.net.xml'):
                file_path += '.net.xml'
            
            self.saveNetworkToFile(file_path)
    
    def saveNetworkToFile(self, file_path):
        """Save network to the specified file"""
        try:
            # Get network data from editor
            nodes_data, edges_data = self.network_editor.exportToSumo()
            
            # Use SumoUtils to save the network
            self.sumo_utils.network_to_xml(nodes_data, edges_data, file_path)
            
            # Update current network file
            self.current_network_file = file_path
            
            # Set the network file for simulation
            self.simulation_panel.setNetworkFile(file_path)
            
            # Update status
            self.status_network.setText(f"Network: {os.path.basename(file_path)}")
            self.statusBar.showMessage(f"Saved network to {file_path}", 3000)
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Network",
                f"Failed to save network: {str(e)}"
            )
    
    def importSumoNetwork(self):
        """Import a SUMO network file"""
        # This is similar to loadNetwork, but we could add more options
        # For now, we'll just call loadNetwork
        self.loadNetwork()
    
    def exportToSumo(self):
        """Export the network to SUMO format"""
        # This is similar to saveNetwork, but we could add more options
        # For now, we'll just call saveNetworkAs
        self.saveNetworkAs()
    
    def clearNetwork(self):
        """Clear the current network"""
        reply = QMessageBox.question(
            self,
            "Clear Network",
            "Are you sure you want to clear the network? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear the network editor
            self.network_editor.clear()
            
            # Update status
            self.statusBar.showMessage("Network cleared", 3000)
    
    def toggleDrawMode(self):
        """Toggle drawing mode in the network editor"""
        self.draw_mode_active = not self.draw_mode_active
        
        # Add a safety check to ensure network_editor exists
        if hasattr(self, 'network_editor'):
            if self.draw_mode_active:
                # Enter drawing mode
                self.network_editor.enterDrawingMode()
                self.statusBar.showMessage("Drawing mode activated")
                self.draw_mode_btn.setText("🛑 Exit Draw Mode")
                self.sidebar_status.setText("Drawing Mode")
                self.sidebar_status.setStyleSheet("color: #FF00FF; padding: 5px; border-top: 1px solid #4040bf; font-weight: bold;")
            else:
                # Exit drawing mode
                self.network_editor.exitDrawingMode()
                self.statusBar.showMessage("Drawing mode deactivated")
                self.draw_mode_btn.setText("✏️ Draw Mode")
                self.sidebar_status.setText("Ready")
                self.sidebar_status.setStyleSheet("color: #00FF00; padding: 5px; border-top: 1px solid #4040bf; font-weight: bold;")
        else:
            # Fallback if network_editor is not available
            print("Network editor not initialized")
    def onTabChanged(self, index):
        """Handle tab change events"""
        if index == 0:
            # Network Editor tab
            self.network_panel.setEnabled(True)
            if self.draw_mode_active:
                self.statusBar.showMessage("Drawing mode active")
            else:
                self.statusBar.showMessage("Ready to edit network")
        
        elif index == 1:
            # Simulation tab
            self.network_panel.setEnabled(False)
            if self.draw_mode_active:
                # Exit drawing mode when switching to simulation tab
                self.toggleDrawMode()
            
            self.statusBar.showMessage("Simulation view")
    
    def onSimulationStarted(self, config_file):
        """Handle simulation start event"""
        self.content_tabs.setCurrentIndex(1)  # Switch to simulation tab
        self.current_config_file = config_file
        self.statusBar.showMessage("Simulation started")
    
    def onSimulationStopped(self):
        """Handle simulation stop event"""
        self.statusBar.showMessage("Simulation stopped")
    
    def showAboutDialog(self):
        """Show the about dialog"""
        QMessageBox.about(
            self,
            "About SUMO Sci-Fi Dashboard",
            """<h1>SUMO Sci-Fi Dashboard</h1>
            <p>Version 1.0</p>
            <p>A modern, sci-fi themed interface for the SUMO traffic simulator.</p>
            <p>Created with PyQt6 and Eclipse SUMO.</p>"""
        )
    
    def showHelpDialog(self):
        """Show the help dialog"""
        QMessageBox.information(
            self,
            "Help",
            """<h1>SUMO Sci-Fi Dashboard Help</h1>
            <h2>Network Editor</h2>
            <p>Use Draw Mode to create roads and intersections.</p>
            <ul>
                <li>Left-click to place nodes and create roads</li>
                <li>Right-click to cancel the current road</li>
                <li>Press Escape to exit drawing mode</li>
            </ul>
            
            <h2>Simulation</h2>
            <p>Configure and run traffic simulations on your network.</p>
            <ul>
                <li>Set vehicle count and distribution</li>
                <li>Adjust simulation speed</li>
                <li>View traffic statistics and visualizations</li>
            </ul>"""
        )
    # Add this to the MainWindow class in main_app.py

    def setupMainContent(self):
        """Set up the main content area with tabs"""
        # Create content tabs widget
        self.content_tabs = QTabWidget()
        self.content_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #4040bf;
                background-color: #101020;
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
                border-bottom-color: #101020;
            }
        """)
        
        # Network editor tab
        # Explicitly create network_editor as an instance attribute
        self.network_editor = AdvancedNetworkEditor()
        
        # Simulation visualization tab
        self.simulation_viz = IntegratedSimulationVisualization()
        
        # Add tabs
        self.content_tabs.addTab(self.network_editor, "Network Editor")
        self.content_tabs.addTab(self.simulation_viz, "Simulation")
        
        # Connect tab change signal
        self.content_tabs.currentChanged.connect(self.onTabChanged)
        
        # Add content tabs to main layout
        self.main_layout.addWidget(self.content_tabs)
            
    def updateSimulationVisualization(self):
        """Update the simulation visualization with current data"""
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

    def onSimulationStarted(self, config_file):
        """Handle simulation start event"""
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
        
    def onSimulationStopped(self):
        """Handle simulation stop event"""
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


# Application entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application name and organization
    app.setApplicationName("SUMO Sci-Fi Dashboard")
    app.setOrganizationName("SumoSciFi")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())
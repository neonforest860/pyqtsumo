from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsItem, 
                           QGraphicsLineItem, QGraphicsEllipseItem, QMenu,
                           QDialog, QVBoxLayout, QFormLayout, QSpinBox, 
                           QDoubleSpinBox, QDialogButtonBox, QLabel)
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont, QPolygonF, QPainter

class Node(QGraphicsEllipseItem):
    """
    Represents a junction in the network
    """
    def __init__(self, x, y, node_id=None, parent=None):
        super().__init__(x - 8, y - 8, 16, 16, parent)
        self.node_id = node_id or f"node_{id(self)}"
        self.x = x
        self.y = y
        
        # Set sci-fi style
        self.setPen(QPen(QColor("#00FFFF"), 2))
        self.setBrush(QBrush(QColor(0, 255, 255, 100)))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        
        # Store path for glow effect to be added after the node is added to the scene
        self.glow_path = QPainterPath()
        self.glow_path.addEllipse(x - 12, y - 12, 24, 24)
        self.glow = None
        self.label = None
        
        # Connected edges
        self.edges = []
    
    def center(self):
        """Get the center point of the node"""
        return QPointF(self.x, self.y)
    
    def addEdge(self, edge):
        """Connect an edge to this node"""
        self.edges.append(edge)
    
    def removeEdge(self, edge):
        """Remove a connected edge"""
        if edge in self.edges:
            self.edges.remove(edge)
    
    def itemChange(self, change, value):
        """Handle movement and selection changes"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update connected edges
            for edge in self.edges:
                edge.updatePosition()
            
            # Update center position
            self.x = self.x() + 8
            self.y = self.y() + 8
            
            # Update glow position if it exists
            if self.glow:
                glow_path = QPainterPath()
                glow_path.addEllipse(self.x - 12, self.y - 12, 24, 24)
                self.glow.setPath(glow_path)
            
            # Update label position if it exists
            if self.label:
                self.label.setPos(self.x + 10, self.y - 10)
            
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            # Highlight when selected
            if self.glow:
                if value:
                    self.setPen(QPen(QColor("#FF00FF"), 3))
                    self.glow.setPen(QPen(QColor(255, 0, 255, 100), 2))
                    self.glow.setBrush(QBrush(QColor(255, 0, 255, 70)))
                else:
                    self.setPen(QPen(QColor("#00FFFF"), 2))
                    self.glow.setPen(QPen(QColor(0, 255, 255, 0)))
                    self.glow.setBrush(QBrush(QColor(0, 255, 255, 50)))
                
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        """Show context menu on right-click"""
        menu = QMenu()
        delete_action = menu.addAction("Delete Node")
        edit_action = menu.addAction("Edit Properties")
        
        action = menu.exec(event.screenPos())
        
        if action == delete_action:
            # Remove edges first
            for edge in self.edges.copy():  # Copy because we'll modify during iteration
                self.scene().removeItem(edge)
                if edge.source_node:
                    edge.source_node.removeEdge(edge)
                if edge.target_node:
                    edge.target_node.removeEdge(edge)
            
            # Remove node elements if they exist
            if self.glow and self.glow in self.scene().items():
                self.scene().removeItem(self.glow)
            if self.label and self.label in self.scene().items():
                self.scene().removeItem(self.label)
            
            # Remove the node itself
            self.scene().removeItem(self)
        
        elif action == edit_action:
            # Show properties dialog
            dialog = QDialog()
            dialog.setWindowTitle("Edit Node Properties")
            layout = QFormLayout()
            
            id_label = QLabel(f"Node ID: {self.node_id}")
            layout.addRow(id_label)
            
            # Here you would add more node properties that are relevant for SUMO
            # For example, junction type, traffic light settings, etc.
            
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                      QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            
            main_layout = QVBoxLayout(dialog)
            main_layout.addLayout(layout)
            main_layout.addWidget(buttons)
            
            dialog.exec()


class Edge(QGraphicsLineItem):
    """
    Represents a road in the network
    """
    def __init__(self, source_node, target_node, edge_id=None, lanes=1, speed=13.89, parent=None):
        """
        Initialize a new edge between two nodes
        
        Args:
            source_node (Node): Starting node
            target_node (Node): Ending node
            edge_id (str): Edge identifier (optional)
            lanes (int): Number of lanes
            speed (float): Speed limit in m/s
        """
        super().__init__(parent)
        self.source_node = source_node
        self.target_node = target_node
        self.edge_id = edge_id or f"edge_{id(self)}"
        self.lanes = lanes
        self.speed = speed  # m/s (default ~50 km/h)
        self.label = None
        self.lane_indicators = []
        
        # Connect to nodes
        if source_node:
            source_node.addEdge(self)
        if target_node:
            target_node.addEdge(self)
        
        # Set sci-fi style based on properties
        self.updateStyle()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        # Update line position (without updating lane indicators)
        if self.source_node and self.target_node:
            self.setLine(QLineF(self.source_node.center(), self.target_node.center()))
    
    def updatePosition(self):
        """Update edge position based on connected nodes"""
        if self.source_node and self.target_node:
            self.setLine(QLineF(self.source_node.center(), self.target_node.center()))
            if hasattr(self, 'label') and self.label:
                self.updateLabelPosition()
            if hasattr(self, 'lane_indicators') and self.scene():
                self.updateLaneIndicators()
    
    def updateLabelPosition(self):
        """Update label position to middle of the edge"""
        if self.label and self.source_node and self.target_node:
            center = self.line().center()
            self.label.setPos(center.x() + 5, center.y() - 15)
    
    def updateStyle(self):
        """Update visual style based on edge properties"""
        # Color based on speed
        if self.speed > 27.78:  # > 100 km/h
            base_color = QColor("#FF3300")  # Red for highways
        elif self.speed > 13.89:  # > 50 km/h
            base_color = QColor("#FFAA00")  # Orange for main roads
        else:
            base_color = QColor("#00FFAA")  # Cyan-green for local roads
        
        # Line thickness based on lanes
        thickness = 1 + self.lanes
        
        self.setPen(QPen(base_color, thickness, Qt.PenStyle.SolidLine, 
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    
    def updateLaneIndicators(self):
        """Update visual indicators for lanes"""
        # Check if the edge is in a scene
        if not self.scene():
            return
            
        # Remove old indicators
        for indicator in self.lane_indicators:
            if indicator in self.scene().items():
                self.scene().removeItem(indicator)
        self.lane_indicators.clear()
        
        if not self.source_node or not self.target_node:
            return
        
        # Only show lane indicators for multi-lane roads
        if self.lanes <= 1:
            return
        
        # Get line direction
        line = self.line()
        length = line.length()
        
        # Skip if too short
        if length < 50:
            return
        
        # Direction vector
        dx = line.dx() / length
        dy = line.dy() / length
        
        # Perpendicular vector
        px = -dy
        py = dx
        
        # Create lane indicators as small line segments
        segments = min(int(length / 50), 5)  # Max 5 segments
        
        for i in range(segments):
            # Position along the line
            pos = (i + 1) / (segments + 1)
            centerX = line.x1() + dx * length * pos
            centerY = line.y1() + dy * length * pos
            
            # Create arrow showing direction
            arrow = QPolygonF()
            
            # Base point
            baseX = centerX - dx * 5
            baseY = centerY - dy * 5
            
            # Tip point
            tipX = centerX + dx * 5
            tipY = centerY + dy * 5
            
            # Wing points
            wingSize = 3
            wing1X = tipX - dx * wingSize + px * wingSize
            wing1Y = tipY - dy * wingSize + py * wingSize
            wing2X = tipX - dx * wingSize - px * wingSize
            wing2Y = tipY - dy * wingSize - py * wingSize
            
            arrow.append(QPointF(baseX, baseY))
            arrow.append(QPointF(tipX, tipY))
            arrow.append(QPointF(wing1X, wing1Y))
            arrow.append(QPointF(tipX, tipY))
            arrow.append(QPointF(wing2X, wing2Y))
            
            indicator = self.scene().addPolygon(
                arrow, 
                QPen(QColor("#FFFFFF"), 1),
                QBrush(QColor("#FFFFFF"))
            )
            self.lane_indicators.append(indicator)
    
    def contextMenuEvent(self, event):
        """Show context menu on right-click"""
        menu = QMenu()
        delete_action = menu.addAction("Delete Edge")
        edit_action = menu.addAction("Edit Properties")
        
        action = menu.exec(event.screenPos())
        
        if action == delete_action:
            # Disconnect from nodes
            if self.source_node:
                self.source_node.removeEdge(self)
            if self.target_node:
                self.target_node.removeEdge(self)
            
            # Remove lane indicators
            for indicator in self.lane_indicators:
                if indicator in self.scene().items():
                    self.scene().removeItem(indicator)
            
            # Remove label if it exists
            if self.label and self.label in self.scene().items():
                self.scene().removeItem(self.label)
            
            # Remove self
            self.scene().removeItem(self)
        
        elif action == edit_action:
            # Show properties dialog
            dialog = QDialog()
            dialog.setWindowTitle("Edit Edge Properties")
            layout = QFormLayout()
            
            # Edge ID
            id_label = QLabel(f"Edge ID: {self.edge_id}")
            layout.addRow(id_label)
            
            # Number of lanes
            lanes_spin = QSpinBox()
            lanes_spin.setRange(1, 6)
            lanes_spin.setValue(self.lanes)
            layout.addRow("Lanes:", lanes_spin)
            
            # Speed limit
            speed_spin = QDoubleSpinBox()
            speed_spin.setRange(5, 50)  # 5-50 m/s (18-180 km/h)
            speed_spin.setValue(self.speed)
            speed_spin.setSuffix(" m/s")
            layout.addRow("Speed Limit:", speed_spin)
            
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                      QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            
            main_layout = QVBoxLayout(dialog)
            main_layout.addLayout(layout)
            main_layout.addWidget(buttons)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.lanes = lanes_spin.value()
                self.speed = speed_spin.value()
                self.updateStyle()
                self.updateLaneIndicators()


class AdvancedNetworkEditor(QGraphicsView):
    """
    Enhanced network editor for SUMO with sci-fi styling and advanced features
    """
    network_changed = pyqtSignal()  # Signal when network is modified
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Set sci-fi look with dark background and grid
        self.setBackgroundBrush(QBrush(QColor("#101020")))
        self.drawGrid()
        
        # Set rendering options
        # Fix: Changed Qt.RenderHint to QPainter.RenderHint
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        # Initialize drawing attributes
        self.drawing_mode = False
        self.temp_start_node = None
        self.temp_line = None
        self.nodes = []
        self.edges = []
        
        # Set up viewport
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Add sci-fi overlay elements
        self.addOverlayElements()
    
    def drawGrid(self):
        """Draw a grid in the background"""
        grid_size = 50
        grid_color = QColor("#202040")
        
        # Get scene bounds
        width = 5000
        height = 5000
        
        # Draw horizontal lines
        for y in range(-height // 2, height // 2 + 1, grid_size):
            line = self.scene.addLine(-width // 2, y, width // 2, y, QPen(grid_color, 1))
            line.setZValue(-1)  # Behind other elements
        
        # Draw vertical lines
        for x in range(-width // 2, width // 2 + 1, grid_size):
            line = self.scene.addLine(x, -height // 2, x, height // 2, QPen(grid_color, 1))
            line.setZValue(-1)  # Behind other elements
            
        # Set scene rect
        self.scene.setSceneRect(-width // 2, -height // 2, width, height)
    
    def addOverlayElements(self):
        """Add sci-fi overlay elements for visual effect"""
        # Add corner decorations
        corner_size = 100
        corner_color = QColor("#00FFFF")
        corner_pen = QPen(corner_color, 2)
        
        # Top-left corner
        top_left = QPainterPath()
        top_left.moveTo(-2400, -1800)
        top_left.lineTo(-2400 + corner_size, -1800)
        top_left.moveTo(-2400, -1800)
        top_left.lineTo(-2400, -1800 + corner_size)
        self.scene.addPath(top_left, corner_pen)
        
        # Top-right corner
        top_right = QPainterPath()
        top_right.moveTo(2400, -1800)
        top_right.lineTo(2400 - corner_size, -1800)
        top_right.moveTo(2400, -1800)
        top_right.lineTo(2400, -1800 + corner_size)
        self.scene.addPath(top_right, corner_pen)
        
        # Bottom-left corner
        bottom_left = QPainterPath()
        bottom_left.moveTo(-2400, 1800)
        bottom_left.lineTo(-2400 + corner_size, 1800)
        bottom_left.moveTo(-2400, 1800)
        bottom_left.lineTo(-2400, 1800 - corner_size)
        self.scene.addPath(bottom_left, corner_pen)
        
        # Bottom-right corner
        bottom_right = QPainterPath()
        bottom_right.moveTo(2400, 1800)
        bottom_right.lineTo(2400 - corner_size, 1800)
        bottom_right.moveTo(2400, 1800)
        bottom_right.lineTo(2400, 1800 - corner_size)
        self.scene.addPath(bottom_right, corner_pen)
        
        # Add coordinate indicators
        label_color = QColor("#00FFAA")
        for x in range(-2000, 2001, 1000):
            if x != 0:  # Skip zero
                x_label = self.scene.addText(f"x: {x}", QFont("Arial", 8))
                x_label.setDefaultTextColor(label_color)
                x_label.setPos(x - 20, 10)
                x_label.setZValue(-0.5)  # Above grid, below network
        
        for y in range(-1500, 1501, 1000):
            if y != 0:  # Skip zero
                y_label = self.scene.addText(f"y: {y}", QFont("Arial", 8))
                y_label.setDefaultTextColor(label_color)
                y_label.setPos(10, y - 10)
                y_label.setZValue(-0.5)  # Above grid, below network
        
        # Add origin marker
        origin_marker = QPainterPath()
        origin_marker.addEllipse(-5, -5, 10, 10)
        origin_marker.moveTo(-20, 0)
        origin_marker.lineTo(20, 0)
        origin_marker.moveTo(0, -20)
        origin_marker.lineTo(0, 20)
        self.scene.addPath(origin_marker, QPen(QColor("#FFFF00"), 1))
        
        # Add compass
        compass = self.scene.addText("N", QFont("Arial", 14, QFont.Weight.Bold))
        compass.setDefaultTextColor(QColor("#00FFFF"))
        compass.setPos(-2350, -1850)
        
        compass_marker = QPainterPath()
        compass_marker.moveTo(-2320, -1835)
        compass_marker.lineTo(-2320, -1865)
        compass_marker.lineTo(-2330, -1850)
        compass_marker.closeSubpath()
        self.scene.addPath(compass_marker, QPen(QColor("#00FFFF"), 1), QBrush(QColor("#00FFFF")))
    
    def enterDrawingMode(self):
        """Enter road drawing mode"""
        self.drawing_mode = True
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        # Add mode indicator text
        if not hasattr(self, 'mode_indicator'):
            self.mode_indicator = self.scene.addText("DRAWING MODE", QFont("Arial", 12, QFont.Weight.Bold))
            self.mode_indicator.setDefaultTextColor(QColor("#FF00FF"))
            self.mode_indicator.setPos(-2350, 1830)
        else:
            self.mode_indicator.setVisible(True)
    
    def exitDrawingMode(self):
        """Exit road drawing mode"""
        self.drawing_mode = False
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
        # Clear any temporary drawing elements
        if self.temp_line:
            self.scene.removeItem(self.temp_line)
            self.temp_line = None
        self.temp_start_node = None
        
        # Hide mode indicator
        if hasattr(self, 'mode_indicator'):
            self.mode_indicator.setVisible(False)
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if not self.drawing_mode:
            super().mousePressEvent(event)
            return
        
        if event.button() == Qt.MouseButton.LeftButton:
            # Get position in scene coordinates
            pos = self.mapToScene(event.pos())
            
            # Check if clicked near an existing node
            existing_node = self.findNodeAt(pos)
            
            if existing_node:
                # Use existing node as start/end
                if not self.temp_start_node:
                    self.temp_start_node = existing_node
                    # Highlight selected node
                    existing_node.setPen(QPen(QColor("#FF00FF"), 3))
                else:
                    if self.temp_start_node != existing_node:
                        # Create an edge between nodes
                        self.createEdge(self.temp_start_node, existing_node)
                        
                        # Reset temp starting node to current to continue
                        self.temp_start_node.setPen(QPen(QColor("#00FFFF"), 2))
                        self.temp_start_node = existing_node
                        existing_node.setPen(QPen(QColor("#FF00FF"), 3))
                    else:
                        # Clicked on same node, cancel current edge
                        self.temp_start_node.setPen(QPen(QColor("#00FFFF"), 2))
                        self.temp_start_node = None
                
                # Remove temp line
                if self.temp_line:
                    self.scene.removeItem(self.temp_line)
                    self.temp_line = None
            else:
                # Create a new node
                node = self.createNode(pos.x(), pos.y())
                
                if not self.temp_start_node:
                    self.temp_start_node = node
                    # Highlight selected node
                    node.setPen(QPen(QColor("#FF00FF"), 3))
                else:
                    # Create an edge between nodes
                    self.createEdge(self.temp_start_node, node)
                    
                    # Reset temp starting node to current to continue
                    self.temp_start_node.setPen(QPen(QColor("#00FFFF"), 2))
                    self.temp_start_node = node
                    node.setPen(QPen(QColor("#FF00FF"), 3))
                
                # Remove temp line
                if self.temp_line:
                    self.scene.removeItem(self.temp_line)
                    self.temp_line = None
        
        elif event.button() == Qt.MouseButton.RightButton:
            # Cancel current operation
            if self.temp_start_node:
                self.temp_start_node.setPen(QPen(QColor("#00FFFF"), 2))
                self.temp_start_node = None
            
            if self.temp_line:
                self.scene.removeItem(self.temp_line)
                self.temp_line = None
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self.drawing_mode and self.temp_start_node:
            # Get position in scene coordinates
            pos = self.mapToScene(event.pos())
            
            # Update temp line
            if self.temp_line:
                self.scene.removeItem(self.temp_line)
            
            self.temp_line = self.scene.addLine(
                QLineF(self.temp_start_node.center(), pos),
                QPen(QColor("#FF00FF"), 2, Qt.PenStyle.DashLine)
            )
        
        super().mouseMoveEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            if self.drawing_mode:
                # Cancel current operation
                if self.temp_start_node:
                    self.temp_start_node.setPen(QPen(QColor("#00FFFF"), 2))
                    self.temp_start_node = None
                
                if self.temp_line:
                    self.scene.removeItem(self.temp_line)
                    self.temp_line = None
            
        elif event.key() == Qt.Key.Key_Delete:
            # Delete selected items
            for item in self.scene.selectedItems():
                if isinstance(item, Node):
                    # Remove connected edges first
                    for edge in item.edges.copy():
                        if edge.source_node:
                            edge.source_node.removeEdge(edge)
                        if edge.target_node:
                            edge.target_node.removeEdge(edge)
                        
                        # Remove lane indicators
                        for indicator in edge.lane_indicators:
                            if indicator in self.scene.items():
                                self.scene.removeItem(indicator)
                        
                        # Remove edge label
                        if hasattr(edge, 'label') and edge.label in self.scene.items():
                            self.scene.removeItem(edge.label)
                        
                        # Remove edge
                        if edge in self.scene.items():
                            self.scene.removeItem(edge)
                    
                    # Remove node elements
                    if hasattr(item, 'glow') and item.glow in self.scene.items():
                        self.scene.removeItem(item.glow)
                    if hasattr(item, 'label') and item.label in self.scene.items():
                        self.scene.removeItem(item.label)
                    
                    # Remove node
                    self.scene.removeItem(item)
                    if item in self.nodes:
                        self.nodes.remove(item)
                
                elif isinstance(item, Edge):
                    # Disconnect from nodes
                    if item.source_node:
                        item.source_node.removeEdge(item)
                    if item.target_node:
                        item.target_node.removeEdge(item)
                    
                    # Remove lane indicators
                    for indicator in item.lane_indicators:
                        if indicator in self.scene.items():
                            self.scene.removeItem(indicator)
                    
                    # Remove edge label
                    if hasattr(item, 'label') and item.label in self.scene.items():
                        self.scene.removeItem(item.label)
                    
                    # Remove edge
                    self.scene.removeItem(item)
                    if item in self.edges:
                        self.edges.remove(item)
            
            # Emit network changed signal
            self.network_changed.emit()
        
        # Allow zooming with + and -
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.scale(1.2, 1.2)
        elif event.key() == Qt.Key.Key_Minus:
            self.scale(0.8, 0.8)
        
        super().keyPressEvent(event)
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        zoom_factor = 1.2
        
        if event.angleDelta().y() > 0:
            # Zoom in
            self.scale(zoom_factor, zoom_factor)
        else:
            # Zoom out
            self.scale(1.0 / zoom_factor, 1.0 / zoom_factor)
    
    def findNodeAt(self, pos, threshold=20):
        """Find a node near the given position"""
        for item in self.scene.items(pos):
            if isinstance(item, Node):
                return item
        
        # If not found directly, search in a small radius
        for node in self.nodes:
            dist = ((node.x - pos.x()) ** 2 + (node.y - pos.y()) ** 2) ** 0.5
            if dist < threshold:
                return node
        
        return None
    
    def createNode(self, x, y, node_id=None):
        """Create a new node at the specified position"""
        # Generate node ID if not provided
        if not node_id:
            node_id = f"node_{len(self.nodes)}"
        
        # Create the node
        node = Node(x, y, node_id)
        self.scene.addItem(node)
        self.nodes.append(node)
        
        # Now that the node is added to the scene, add the glow effect and label
        node.glow = self.scene.addPath(node.glow_path, 
                                      QPen(QColor(0, 255, 255, 0)), 
                                      QBrush(QColor(0, 255, 255, 50)))
        
        # Add label with ID
        node.label = self.scene.addText(node.node_id, QFont("Arial", 8))
        node.label.setDefaultTextColor(QColor("#00FFFF"))
        node.label.setPos(x + 10, y - 10)
        
        # Emit network changed signal
        self.network_changed.emit()
        
        return node
    
    def createEdge(self, source_node, target_node, edge_id=None, lanes=1, speed=13.89):
        """Create a new edge between two nodes"""
        # Generate edge ID if not provided
        if not edge_id:
            edge_id = f"edge_{len(self.edges)}"
        
        # Create the edge
        edge = Edge(source_node, target_node, edge_id, lanes, speed)
        self.scene.addItem(edge)
        self.edges.append(edge)
        
        # Now that the edge is added to the scene, add the label
        edge.label = self.scene.addText(edge.edge_id, QFont("Arial", 8))
        edge.label.setDefaultTextColor(QColor("#00FFAA"))
        edge.updateLabelPosition()
        
        # Create lane indicators
        edge.updateLaneIndicators()
        
        # Emit network changed signal
        self.network_changed.emit()
        
        return edge
    
    def clear(self):
        """Clear the entire network"""
        # Remove all items
        self.scene.clear()
        
        # Re-add grid and overlays
        self.drawGrid()
        self.addOverlayElements()
        
        # Reset data
        self.nodes = []
        self.edges = []
        self.temp_start_node = None
        self.temp_line = None
        
        # Emit network changed signal
        self.network_changed.emit()
    
    def exportToSumo(self):
        """Export the network to SUMO XML format"""
        nodes_data = []
        edges_data = []
        
        # Convert nodes
        for node in self.nodes:
            nodes_data.append((
                node.node_id,
                node.x,
                node.y
            ))
        
        # Convert edges
        for edge in self.edges:
            if edge.source_node and edge.target_node:
                edges_data.append((
                    edge.edge_id,
                    edge.source_node.node_id,
                    edge.target_node.node_id,
                    edge.lanes,
                    edge.speed
                ))
        
        return nodes_data, edges_data
    
    def importFromSumo(self, nodes_data, edges_data):
        """Import network from SUMO data"""
        # Clear existing network
        self.clear()
        
        # Create nodes first
        node_map = {}  # Map node IDs to Node objects
        for node_id, x, y in nodes_data:
            node = self.createNode(x, y, node_id)
            node_map[node_id] = node
        
        # Create edges
        for edge_id, from_node, to_node, lanes, speed in edges_data:
            if from_node in node_map and to_node in node_map:
                self.createEdge(
                    node_map[from_node],
                    node_map[to_node],
                    edge_id,
                    lanes,
                    speed
                )
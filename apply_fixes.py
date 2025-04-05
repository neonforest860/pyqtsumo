#!/usr/bin/env python3
"""
Applies fixes to the network_editor.py file to resolve the issues
"""

def update_network_editor():
    import os
    
    # Check if the network_editor.py file exists
    if not os.path.exists('network_editor.py'):
        print("Error: network_editor.py file not found!")
        return False
        
    # Read the original file content
    with open('network_editor.py', 'r') as f:
        content = f.read()
    
    # Make a backup of the original file
    with open('network_editor.py.bak', 'w') as f:
        f.write(content)
    print("Created backup: network_editor.py.bak")
    
    print("Applying fixes to network_editor.py...")
    
    # First, add the QPainter import
    if 'from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont, QPolygonF' in content:
        content = content.replace(
            'from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont, QPolygonF',
            'from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont, QPolygonF, QPainter'
        )
    
    # Fix the RenderHint
    if 'self.setRenderHint(Qt.RenderHint' in content:
        content = content.replace(
            'self.setRenderHint(Qt.RenderHint',
            'self.setRenderHint(QPainter.RenderHint'
        )
    
    # Fix the Node class initialization
    node_init_old = """    def __init__(self, x, y, node_id=None, parent=None):
        super().__init__(x - 8, y - 8, 16, 16, parent)
        self.node_id = node_id or f"node_{id(self)}"
        self.x = x
        self.y = y
        
        # Set sci-fi style
        self.setPen(QPen(QColor("#00FFFF"), 2))
        self.setBrush(QBrush(QColor(0, 255, 255, 100)))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        
        # Add a glow effect
        glow_path = QPainterPath()
        glow_path.addEllipse(x - 12, y - 12, 24, 24)
        self.glow = self.scene().addPath(glow_path, 
                                         QPen(QColor(0, 255, 255, 0)), 
                                         QBrush(QColor(0, 255, 255, 50)))
        
        # Add label with ID
        self.label = self.scene().addText(self.node_id, QFont("Arial", 8))
        self.label.setDefaultTextColor(QColor("#00FFFF"))
        self.label.setPos(x + 10, y - 10)
        
        # Connected edges
        self.edges = []"""

    node_init_new = """    def __init__(self, x, y, node_id=None, parent=None):
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
        self.edges = []"""

    content = content.replace(node_init_old, node_init_new)

    # Fix the Edge class initialization
    edge_init_old = """    def __init__(self, source_node, target_node, edge_id=None, lanes=1, speed=13.89, parent=None):
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
        
        # Connect to nodes
        if source_node:
            source_node.addEdge(self)
        if target_node:
            target_node.addEdge(self)
        
        # Set sci-fi style based on properties
        self.updateStyle()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        # Update line position
        self.updatePosition()
        
        # Add label with ID
        self.label = self.scene().addText(self.edge_id, QFont("Arial", 8))
        self.label.setDefaultTextColor(QColor("#00FFAA"))
        self.updateLabelPosition()
        
        # Create lane indicators
        self.lane_indicators = []
        self.updateLaneIndicators()"""

    edge_init_new = """    def __init__(self, source_node, target_node, edge_id=None, lanes=1, speed=13.89, parent=None):
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
            self.setLine(QLineF(self.source_node.center(), self.target_node.center()))"""

    content = content.replace(edge_init_old, edge_init_new)

    # Fix the updatePosition method
    update_position_old = """    def updatePosition(self):
        """Update edge position based on connected nodes"""
        if self.source_node and self.target_node:
            self.setLine(QLineF(self.source_node.center(), self.target_node.center()))
            self.updateLabelPosition()
            self.updateLaneIndicators()"""

    update_position_new = """    def updatePosition(self):
        """Update edge position based on connected nodes"""
        if self.source_node and self.target_node:
            self.setLine(QLineF(self.source_node.center(), self.target_node.center()))
            if hasattr(self, 'label') and self.label:
                self.updateLabelPosition()
            if hasattr(self, 'lane_indicators') and self.scene():
                self.updateLaneIndicators()"""

    content = content.replace(update_position_old, update_position_new)

    # Fix the updateLabelPosition method
    update_label_position_old = """    def updateLabelPosition(self):
        """Update label position to middle of the edge"""
        if hasattr(self, 'label') and self.source_node and self.target_node:
            center = self.line().center()
            self.label.setPos(center.x() + 5, center.y() - 15)"""

    update_label_position_new = """    def updateLabelPosition(self):
        """Update label position to middle of the edge"""
        if self.label and self.source_node and self.target_node:
            center = self.line().center()
            self.label.setPos(center.x() + 5, center.y() - 15)"""

    content = content.replace(update_label_position_old, update_label_position_new)

    # Fix the updateLaneIndicators method
    update_lane_indicators_old = """    def updateLaneIndicators(self):
        """Update visual indicators for lanes"""
        # Remove old indicators
        for indicator in self.lane_indicators:
            if indicator in self.scene().items():
                self.scene().removeItem(indicator)
        self.lane_indicators.clear()"""

    update_lane_indicators_new = """    def updateLaneIndicators(self):
        """Update visual indicators for lanes"""
        # Check if the edge is in a scene
        if not self.scene():
            return
            
        # Remove old indicators
        for indicator in self.lane_indicators:
            if indicator in self.scene().items():
                self.scene().removeItem(indicator)
        self.lane_indicators.clear()"""

    content = content.replace(update_lane_indicators_old, update_lane_indicators_new)

    # Fix the createNode method
    create_node_old = """    def createNode(self, x, y, node_id=None):
        """Create a new node at the specified position"""
        # Generate node ID if not provided
        if not node_id:
            node_id = f"node_{len(self.nodes)}"
        
        # Create the node
        node = Node(x, y, node_id)
        self.scene.addItem(node)
        self.nodes.append(node)
        
        # Emit network changed signal
        self.network_changed.emit()
        
        return node"""

    create_node_new = """    def createNode(self, x, y, node_id=None):
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
        
        return node"""

    content = content.replace(create_node_old, create_node_new)

    # Fix the createEdge method
    create_edge_old = """    def createEdge(self, source_node, target_node, edge_id=None, lanes=1, speed=13.89):
        """Create a new edge between two nodes"""
        # Generate edge ID if not provided
        if not edge_id:
            edge_id = f"edge_{len(self.edges)}"
        
        # Create the edge
        edge = Edge(source_node, target_node, edge_id, lanes, speed)
        self.scene.addItem(edge)
        self.edges.append(edge)
        
        # Emit network changed signal
        self.network_changed.emit()
        
        return edge"""

    create_edge_new = """    def createEdge(self, source_node, target_node, edge_id=None, lanes=1, speed=13.89):
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
        
        return edge"""

    content = content.replace(create_edge_old, create_edge_new)

    # Fix the itemChange method for Node
    item_change_old = """    def itemChange(self, change, value):
        """Handle movement and selection changes"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update connected edges
            for edge in self.edges:
                edge.updatePosition()
            
            # Update center position
            self.x = self.x() + 8
            self.y = self.y() + 8
            
            # Update glow position
            glow_path = QPainterPath()
            glow_path.addEllipse(self.x - 12, self.y - 12, 24, 24)
            self.glow.setPath(glow_path)
            
            # Update label position
            self.label.setPos(self.x + 10, self.y - 10)
            
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            # Highlight when selected
            if value:
                self.setPen(QPen(QColor("#FF00FF"), 3))
                self.glow.setPen(QPen(QColor(255, 0, 255, 100), 2))
                self.glow.setBrush(QBrush(QColor(255, 0, 255, 70)))
            else:
                self.setPen(QPen(QColor("#00FFFF"), 2))
                self.glow.setPen(QPen(QColor(0, 255, 255, 0)))
                self.glow.setBrush(QBrush(QColor(0, 255, 255, 50)))
                
        return super().itemChange(change, value)"""

    item_change_new = """    def itemChange(self, change, value):
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
                
        return super().itemChange(change, value)"""

    content = content.replace(item_change_old, item_change_new)

    # Fix the Node contextMenuEvent method
    node_context_menu_old = """    def contextMenuEvent(self, event):
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
            
            # Remove node elements
            self.scene().removeItem(self.glow)
            self.scene().removeItem(self.label)
            self.scene().removeItem(self)"""

    node_context_menu_new = """    def contextMenuEvent(self, event):
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
            self.scene().removeItem(self)"""

    content = content.replace(node_context_menu_old, node_context_menu_new)

    # Fix the Edge contextMenuEvent method
    edge_context_menu_old = """    def contextMenuEvent(self, event):
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
            
            # Remove label
            if hasattr(self, 'label') and self.label in self.scene().items():
                self.scene().removeItem(self.label)"""

    edge_context_menu_new = """    def contextMenuEvent(self, event):
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
                self.scene().removeItem(self.label)"""

    content = content.replace(edge_context_menu_old, edge_context_menu_new)
    
    # Write the updated content back to the file
    with open('network_editor.py', 'w') as f:
        f.write(content)
    
    print("Successfully updated network_editor.py")
    return True

if __name__ == "__main__":
    update_network_editor()

    # Fix the enterDrawingMode method
    enter_drawing_mode_old = """    def enterDrawingMode(self):
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
            self.mode_indicator.setVisible(True)"""

    enter_drawing_mode_new = """    def enterDrawingMode(self):
        """Enter road drawing mode"""
        self.drawing_mode = True
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        # Add mode indicator text
        if not hasattr(self, 'mode_indicator') or not self.mode_indicator or not self.scene or self.mode_indicator not in self.scene.items():
            self.mode_indicator = self.scene.addText("DRAWING MODE", QFont("Arial", 12, QFont.Weight.Bold))
            self.mode_indicator.setDefaultTextColor(QColor("#FF00FF"))
            self.mode_indicator.setPos(-2350, 1830)
        else:
            try:
                self.mode_indicator.setVisible(True)
            except RuntimeError:
                # If the object was deleted, recreate it
                self.mode_indicator = self.scene.addText("DRAWING MODE", QFont("Arial", 12, QFont.Weight.Bold))
                self.mode_indicator.setDefaultTextColor(QColor("#FF00FF"))
                self.mode_indicator.setPos(-2350, 1830)"""

    content = content.replace(enter_drawing_mode_old, enter_drawing_mode_new)

    # Fix the exitDrawingMode method
    exit_drawing_mode_old = """    def exitDrawingMode(self):
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
            self.mode_indicator.setVisible(False)"""

    exit_drawing_mode_new = """    def exitDrawingMode(self):
        """Exit road drawing mode"""
        self.drawing_mode = False
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
        # Clear any temporary drawing elements
        if self.temp_line and self.scene and self.temp_line in self.scene.items():
            self.scene.removeItem(self.temp_line)
            self.temp_line = None
        self.temp_start_node = None
        
        # Hide mode indicator if it exists
        if hasattr(self, 'mode_indicator') and self.mode_indicator and self.scene and self.mode_indicator in self.scene.items():
            try:
                self.mode_indicator.setVisible(False)
            except RuntimeError:
                # If the object was deleted, recreate it for next time
                self.mode_indicator = None"""

    content = content.replace(exit_drawing_mode_old, exit_drawing_mode_new)

    # Fix the clear method
    clear_old = """    def clear(self):
        """Clear the entire network"""
        # Reset data before clearing the scene
        self.nodes = []
        self.edges = []
        self.temp_start_node = None
        self.temp_line = None
        
        # Remember if we had a mode indicator
        had_mode_indicator = hasattr(self, 'mode_indicator') and self.mode_indicator is not None
        
        # Remove all items
        self.scene.clear()
        
        # Re-add grid and overlays
        self.drawGrid()
        self.addOverlayElements()
        
        # Reset the mode indicator reference
        if had_mode_indicator and self.drawing_mode:
            self.mode_indicator = self.scene.addText("DRAWING MODE", QFont("Arial", 12, QFont.Weight.Bold))
            self.mode_indicator.setDefaultTextColor(QColor("#FF00FF"))
            self.mode_indicator.setPos(-2350, 1830)
        else:
            self.mode_indicator = None
        
        # Emit network changed signal
        self.network_changed.emit()"""
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
        self.network_changed.emit()"""

    clear_new = """    def clear(self):
        """Clear the entire network
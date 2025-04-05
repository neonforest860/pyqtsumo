import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from xml.dom import minidom

class SumoUtils:
    """Utility class for interacting with SUMO"""
    
    def __init__(self, sumo_home=None):
        """Initialize with path to SUMO installation"""
        self.sumo_home = sumo_home or os.environ.get('SUMO_HOME')
        if not self.sumo_home:
            raise EnvironmentError("SUMO_HOME environment variable is not set. Please set it to your SUMO installation directory.")
        
        # Set paths to SUMO executables
        self.sumo_bin = os.path.join(self.sumo_home, 'bin', 'sumo')
        self.sumo_gui_bin = os.path.join(self.sumo_home, 'bin', 'sumo-gui')
        self.netconvert_bin = os.path.join(self.sumo_home, 'bin', 'netconvert')
        
        # Check if binary files exist
        for bin_file in [self.sumo_bin, self.sumo_gui_bin, self.netconvert_bin]:
            if not os.path.exists(bin_file) and not os.path.exists(bin_file + '.exe'):
                raise FileNotFoundError(f"SUMO binary not found at {bin_file}")
    
    def network_to_xml(self, nodes, edges, output_file=None):
        """
        Convert network data to SUMO XML format
        
        Args:
            nodes (list): List of (id, x, y) tuples for nodes
            edges (list): List of (id, from_node, to_node, lanes, speed) tuples for edges
            output_file (str): Path to save the network file (optional)
            
        Returns:
            str: Path to the created network file
        """
        temp_dir = tempfile.mkdtemp()
        
        # Create nodes file
        nodes_file = os.path.join(temp_dir, "nodes.nod.xml")
        with open(nodes_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<nodes>\n')
            for node_id, x, y in nodes:
                f.write(f'    <node id="{node_id}" x="{x}" y="{y}" type="priority"/>\n')
            f.write('</nodes>\n')
        
        # Create edges file
        edges_file = os.path.join(temp_dir, "edges.edg.xml")
        with open(edges_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<edges>\n')
            for edge_id, from_node, to_node, lanes, speed in edges:
                f.write(f'    <edge id="{edge_id}" from="{from_node}" to="{to_node}" numLanes="{lanes}" speed="{speed}"/>\n')
            f.write('</edges>\n')
        
        # Use netconvert to create the network file
        if not output_file:
            output_file = os.path.join(temp_dir, "network.net.xml")
            
        cmd = [
            self.netconvert_bin,
            "-n", nodes_file,
            "-e", edges_file,
            "-o", output_file
        ]
        
        try:
            subprocess.run(cmd, check=True)
            return output_file
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to convert network: {e}")
    
    def create_route_file(self, edges, output_file, vehicle_count=100, start_time=0, end_time=3600, distribution='uniform'):
            """
            Create a route file for simulation
            
            Args:
                edges (list): List of edge IDs that form the route
                output_file (str): Path to save the route file
                vehicle_count (int): Number of vehicles to generate
                start_time (int): Simulation start time in seconds
                end_time (int): Simulation end time in seconds
                distribution (str): Distribution type for vehicles
                
            Returns:
                str: Path to the created route file
            """
            import numpy as np
            
            # Create the route XML
            root = ET.Element("routes")
            
            # Add vehicle type
            vtype = ET.SubElement(root, "vType")
            vtype.set("id", "car")
            vtype.set("accel", "2.6")
            vtype.set("decel", "4.5")
            vtype.set("sigma", "0.5")
            vtype.set("length", "5.0")
            vtype.set("maxSpeed", "50.0")
            
            # Add route
            route = ET.SubElement(root, "route")
            route.set("id", "main_route")
            route.set("edges", " ".join(edges))
            
            # Generate vehicles with different distributions
            for i in range(vehicle_count):
                # Calculate departure time based on distribution
                if distribution == 'uniform':
                    depart_time = start_time + (i * (end_time - start_time) / vehicle_count)
                elif distribution == 'poisson':
                    # Poisson distribution
                    depart_time = start_time + np.random.poisson(
                        (end_time - start_time) / vehicle_count
                    )
                elif distribution == 'normal':
                    # Normal distribution
                    depart_time = start_time + max(0, np.random.normal(
                        loc=(start_time + end_time) / 2, 
                        scale=(end_time - start_time) / 6
                    ))
                elif distribution == 'rush_hour':
                    # Concentrate vehicles in the middle third of simulation time
                    rush_start = start_time + (end_time - start_time) * 0.3
                    rush_end = start_time + (end_time - start_time) * 0.7
                    depart_time = rush_start + (i * (rush_end - rush_start) / vehicle_count)
                else:
                    # Fallback to uniform
                    depart_time = start_time + (i * (end_time - start_time) / vehicle_count)
                
                # Ensure depart time is within simulation duration
                depart_time = min(max(start_time, depart_time), end_time - 1)
                
                vehicle = ET.SubElement(root, "vehicle")
                vehicle.set("id", f"veh{i}")
                vehicle.set("type", "car")
                vehicle.set("route", "main_route")
                vehicle.set("depart", f"{depart_time:.2f}")
                vehicle.set("departPos", "random")
            
            # Write to file with pretty formatting
            rough_string = ET.tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            with open(output_file, 'w') as f:
                f.write(reparsed.toprettyxml(indent="    "))
                
            return output_file
    
    def create_config_file(self, network_file, route_file, output_file, gui=True, step_length=0.1, end_time=3600):
        """
        Create a SUMO configuration file
        
        Args:
            network_file (str): Path to the network file
            route_file (str): Path to the route file
            output_file (str): Path to save the configuration file
            gui (bool): Whether to use the GUI version
            step_length (float): Simulation step length in seconds
            end_time (int): Simulation end time in seconds
            
        Returns:
            str: Path to the created configuration file
        """
        # Create the configuration XML
        root = ET.Element("configuration")
        
        # Input section
        input_section = ET.SubElement(root, "input")
        net_file = ET.SubElement(input_section, "net-file")
        net_file.set("value", os.path.basename(network_file))
        route_files = ET.SubElement(input_section, "route-files")
        route_files.set("value", os.path.basename(route_file))
        
        # Time section
        time_section = ET.SubElement(root, "time")
        begin = ET.SubElement(time_section, "begin")
        begin.set("value", "0")
        end = ET.SubElement(time_section, "end")
        end.set("value", str(end_time))
        step_length_elem = ET.SubElement(time_section, "step-length")
        step_length_elem.set("value", str(step_length))
        
        # Write to file with pretty formatting
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        with open(output_file, 'w') as f:
            f.write(reparsed.toprettyxml(indent="    "))
            
        return output_file
    
    def run_simulation(self, config_file, gui=True, output_file=None):
        """
        Run a SUMO simulation
        
        Args:
            config_file (str): Path to the configuration file
            gui (bool): Whether to use the GUI version
            output_file (str): Path to save simulation results (optional)
            
        Returns:
            subprocess.CompletedProcess: Result of the simulation run
        """
        binary = self.sumo_gui_bin if gui else self.sumo_bin
        
        cmd = [binary, "-c", config_file]
        
        if output_file:
            cmd.extend(["--output-prefix", output_file])
        
        try:
            return subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to run simulation: {e}")
    
    def extract_network_data(self, network_file):
        """
        Extract node and edge data from an existing SUMO network file
        
        Args:
            network_file (str): Path to the network file
            
        Returns:
            tuple: (nodes, edges) where nodes and edges are lists of data
        """
        # This is a simplified version that would need to be expanded for a real application
        # SUMO network files are complex XML, so we'd need more sophisticated parsing
        
        try:
            tree = ET.parse(network_file)
            root = tree.getroot()
            
            nodes = []
            for junction in root.findall(".//junction"):
                node_id = junction.get("id")
                x = float(junction.get("x"))
                y = float(junction.get("y"))
                nodes.append((node_id, x, y))
            
            edges = []
            for edge in root.findall(".//edge"):
                edge_id = edge.get("id")
                from_node = edge.get("from")
                to_node = edge.get("to")
                
                # Get lane information
                lanes = len(edge.findall("lane"))
                
                # Get speed (from the first lane)
                first_lane = edge.find("lane")
                speed = 13.89  # Default 50 km/h
                if first_lane is not None:
                    speed = float(first_lane.get("speed", speed))
                
                edges.append((edge_id, from_node, to_node, lanes, speed))
            
            return nodes, edges
        except Exception as e:
            raise RuntimeError(f"Failed to extract network data: {e}")
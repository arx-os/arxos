"""
Topology Analyzer for Arxos
Understands spatial relationships and building structure topology
"""

from typing import List, Dict, Any, Set, Tuple, Optional
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
from collections import defaultdict

from models.arxobject import (
    ArxObject, ArxObjectType, Relationship, 
    RelationshipType, ConfidenceScore
)
from models.coordinate_system import Point3D, BoundingBox


class TopologyType(Enum):
    """Types of topological relationships"""
    STRUCTURAL = "structural"  # Load-bearing relationships
    SPATIAL = "spatial"        # Space containment and adjacency
    FUNCTIONAL = "functional"  # System connections (HVAC, electrical, etc.)
    CIRCULATION = "circulation"  # Movement paths


@dataclass
class TopologyNode:
    """Node in the topology graph"""
    arxobject: ArxObject
    connections: Set[str] = field(default_factory=set)
    properties: Dict[str, Any] = field(default_factory=dict)
    

@dataclass
class TopologyEdge:
    """Edge in the topology graph"""
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    confidence: float
    properties: Dict[str, Any] = field(default_factory=dict)


class SpatialIndex:
    """Spatial index for efficient proximity queries"""
    
    def __init__(self, objects: List[ArxObject]):
        self.objects = {obj.id: obj for obj in objects}
        self.bounds_index = self._build_bounds_index(objects)
        self.grid_index = self._build_grid_index(objects)
        
    def _build_bounds_index(self, objects: List[ArxObject]) -> Dict[str, BoundingBox]:
        """Build bounding box index"""
        index = {}
        for obj in objects:
            if obj.bounds:
                index[obj.id] = obj.bounds
            elif obj.position and obj.dimensions:
                # Create bounds from position and dimensions
                half_width = obj.dimensions.width // 2
                half_height = obj.dimensions.height // 2
                half_depth = obj.dimensions.depth // 2
                
                index[obj.id] = BoundingBox(
                    min_point=Point3D(
                        x=obj.position.x - half_width,
                        y=obj.position.y - half_height,
                        z=obj.position.z - half_depth
                    ),
                    max_point=Point3D(
                        x=obj.position.x + half_width,
                        y=obj.position.y + half_height,
                        z=obj.position.z + half_depth
                    )
                )
        return index
    
    def _build_grid_index(self, objects: List[ArxObject], cell_size: int = 10_000_000_000) -> Dict[Tuple[int, int], List[str]]:
        """Build grid-based spatial index (cell size in nanometers)"""
        grid = defaultdict(list)
        
        for obj_id, bounds in self.bounds_index.items():
            # Calculate grid cells this object occupies
            min_x_cell = bounds.min_point.x // cell_size
            max_x_cell = bounds.max_point.x // cell_size
            min_y_cell = bounds.min_point.y // cell_size
            max_y_cell = bounds.max_point.y // cell_size
            
            # Add to all occupied cells
            for x in range(min_x_cell, max_x_cell + 1):
                for y in range(min_y_cell, max_y_cell + 1):
                    grid[(x, y)].append(obj_id)
        
        return dict(grid)
    
    def find_nearby(self, obj_id: str, max_distance: int = 1_000_000_000) -> List[str]:
        """Find objects within max_distance (nanometers) of given object"""
        if obj_id not in self.bounds_index:
            return []
        
        bounds = self.bounds_index[obj_id]
        center = Point3D(
            x=(bounds.min_point.x + bounds.max_point.x) // 2,
            y=(bounds.min_point.y + bounds.max_point.y) // 2,
            z=(bounds.min_point.z + bounds.max_point.z) // 2
        )
        
        nearby = []
        for other_id, other_bounds in self.bounds_index.items():
            if other_id == obj_id:
                continue
            
            other_center = Point3D(
                x=(other_bounds.min_point.x + other_bounds.max_point.x) // 2,
                y=(other_bounds.min_point.y + other_bounds.max_point.y) // 2,
                z=(other_bounds.min_point.z + other_bounds.max_point.z) // 2
            )
            
            # Calculate distance between centers
            dist = np.sqrt(
                float((center.x - other_center.x) ** 2 +
                      (center.y - other_center.y) ** 2 +
                      (center.z - other_center.z) ** 2)
            )
            
            if dist <= max_distance:
                nearby.append(other_id)
        
        return nearby
    
    def find_intersecting(self, obj_id: str) -> List[str]:
        """Find objects that intersect with given object"""
        if obj_id not in self.bounds_index:
            return []
        
        bounds = self.bounds_index[obj_id]
        intersecting = []
        
        for other_id, other_bounds in self.bounds_index.items():
            if other_id == obj_id:
                continue
            
            if bounds.intersects(other_bounds):
                intersecting.append(other_id)
        
        return intersecting
    
    def find_contained(self, container_id: str) -> List[str]:
        """Find objects contained within given object"""
        if container_id not in self.bounds_index:
            return []
        
        container_bounds = self.bounds_index[container_id]
        contained = []
        
        for obj_id, bounds in self.bounds_index.items():
            if obj_id == container_id:
                continue
            
            # Check if bounds is fully contained
            if (container_bounds.min_point.x <= bounds.min_point.x and
                container_bounds.max_point.x >= bounds.max_point.x and
                container_bounds.min_point.y <= bounds.min_point.y and
                container_bounds.max_point.y >= bounds.max_point.y):
                contained.append(obj_id)
        
        return contained


class TopologyAnalyzer:
    """Analyzes and builds topological relationships between ArxObjects"""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.spatial_index: Optional[SpatialIndex] = None
        
    def analyze(self, objects: List[ArxObject]) -> Dict[str, List[Relationship]]:
        """
        Analyze topology and build relationships
        Returns updated relationships for each object
        """
        # Build spatial index
        self.spatial_index = SpatialIndex(objects)
        
        # Build initial graph
        self._build_graph(objects)
        
        # Analyze different relationship types
        relationships = {}
        
        # Spatial relationships (adjacency, containment)
        spatial_rels = self._analyze_spatial_relationships(objects)
        self._merge_relationships(relationships, spatial_rels)
        
        # Structural relationships (load paths, support)
        structural_rels = self._analyze_structural_relationships(objects)
        self._merge_relationships(relationships, structural_rels)
        
        # Functional relationships (systems, services)
        functional_rels = self._analyze_functional_relationships(objects)
        self._merge_relationships(relationships, functional_rels)
        
        # Circulation relationships (paths, connectivity)
        circulation_rels = self._analyze_circulation_relationships(objects)
        self._merge_relationships(relationships, circulation_rels)
        
        # Update confidence based on topology consistency
        self._update_confidence_from_topology(objects, relationships)
        
        return relationships
    
    def _build_graph(self, objects: List[ArxObject]):
        """Build initial graph from objects"""
        self.graph.clear()
        
        # Add nodes
        for obj in objects:
            self.graph.add_node(
                obj.id,
                arxobject=obj,
                type=obj.type.value,
                position=obj.position,
                bounds=obj.bounds
            )
        
        # Add existing relationships as edges
        for obj in objects:
            for rel in obj.relationships:
                self.graph.add_edge(
                    obj.id,
                    rel.target_id,
                    type=rel.type.value,
                    confidence=rel.confidence,
                    properties=rel.properties
                )
    
    def _analyze_spatial_relationships(self, objects: List[ArxObject]) -> Dict[str, List[Relationship]]:
        """Analyze spatial relationships (adjacency, containment)"""
        relationships = defaultdict(list)
        
        for obj in objects:
            # Find adjacent objects
            if obj.type == ArxObjectType.WALL:
                adjacent = self._find_adjacent_walls(obj)
                for adj_id, confidence in adjacent:
                    relationships[obj.id].append(Relationship(
                        type=RelationshipType.ADJACENT_TO,
                        target_id=adj_id,
                        confidence=confidence,
                        properties={"topology_type": "spatial"}
                    ))
            
            # Find containment relationships
            if obj.type == ArxObjectType.ROOM:
                # Rooms contain other elements
                contained = self.spatial_index.find_contained(obj.id)
                for contained_id in contained:
                    contained_obj = self.spatial_index.objects[contained_id]
                    
                    # Room contains doors, windows, etc.
                    if contained_obj.type in [ArxObjectType.DOOR, ArxObjectType.WINDOW]:
                        relationships[obj.id].append(Relationship(
                            type=RelationshipType.CONTAINS,
                            target_id=contained_id,
                            confidence=0.9,
                            properties={"topology_type": "spatial"}
                        ))
                        
                        relationships[contained_id].append(Relationship(
                            type=RelationshipType.CONTAINED_BY,
                            target_id=obj.id,
                            confidence=0.9,
                            properties={"topology_type": "spatial"}
                        ))
            
            # Find objects above/below (for multi-story buildings)
            if obj.bounds and obj.type in [ArxObjectType.FLOOR, ArxObjectType.SLAB]:
                above, below = self._find_vertical_relationships(obj)
                
                for above_id in above:
                    relationships[obj.id].append(Relationship(
                        type=RelationshipType.BELOW,
                        target_id=above_id,
                        confidence=0.8,
                        properties={"topology_type": "spatial"}
                    ))
                
                for below_id in below:
                    relationships[obj.id].append(Relationship(
                        type=RelationshipType.ABOVE,
                        target_id=below_id,
                        confidence=0.8,
                        properties={"topology_type": "spatial"}
                    ))
        
        return dict(relationships)
    
    def _analyze_structural_relationships(self, objects: List[ArxObject]) -> Dict[str, List[Relationship]]:
        """Analyze structural relationships (load paths, support)"""
        relationships = defaultdict(list)
        
        # Find load-bearing relationships
        for obj in objects:
            if obj.type == ArxObjectType.COLUMN:
                # Columns support beams and slabs
                supported = self._find_supported_elements(obj)
                for supp_id, confidence in supported:
                    relationships[obj.id].append(Relationship(
                        type=RelationshipType.PART_OF,
                        target_id=supp_id,
                        confidence=confidence,
                        properties={
                            "topology_type": "structural",
                            "load_path": True
                        }
                    ))
            
            elif obj.type == ArxObjectType.BEAM:
                # Beams connect to columns and support slabs
                connections = self._find_beam_connections(obj)
                for conn_id, conn_type, confidence in connections:
                    relationships[obj.id].append(Relationship(
                        type=RelationshipType.CONNECTED_TO,
                        target_id=conn_id,
                        confidence=confidence,
                        properties={
                            "topology_type": "structural",
                            "connection_type": conn_type
                        }
                    ))
            
            elif obj.type == ArxObjectType.WALL:
                # Check if wall is load-bearing
                if self._is_load_bearing_wall(obj):
                    relationships[obj.id].append(Relationship(
                        type=RelationshipType.PART_OF,
                        target_id="structural_system",
                        confidence=0.8,
                        properties={
                            "topology_type": "structural",
                            "load_bearing": True
                        }
                    ))
        
        return dict(relationships)
    
    def _analyze_functional_relationships(self, objects: List[ArxObject]) -> Dict[str, List[Relationship]]:
        """Analyze functional relationships (systems, services)"""
        relationships = defaultdict(list)
        
        # Group objects by system
        systems = self._identify_systems(objects)
        
        for system_name, system_objects in systems.items():
            # Create relationships within each system
            for obj in system_objects:
                # Find upstream/downstream relationships
                upstream, downstream = self._find_system_flow(obj, system_objects)
                
                for up_id in upstream:
                    relationships[obj.id].append(Relationship(
                        type=RelationshipType.DOWNSTREAM,
                        target_id=up_id,
                        confidence=0.7,
                        properties={
                            "topology_type": "functional",
                            "system": system_name
                        }
                    ))
                
                for down_id in downstream:
                    relationships[obj.id].append(Relationship(
                        type=RelationshipType.UPSTREAM,
                        target_id=down_id,
                        confidence=0.7,
                        properties={
                            "topology_type": "functional",
                            "system": system_name
                        }
                    ))
                
                # Control relationships
                if obj.type in [ArxObjectType.CONTROLLER, ArxObjectType.THERMOSTAT]:
                    controlled = self._find_controlled_elements(obj, system_objects)
                    for ctrl_id in controlled:
                        relationships[obj.id].append(Relationship(
                            type=RelationshipType.CONTROLS,
                            target_id=ctrl_id,
                            confidence=0.8,
                            properties={
                                "topology_type": "functional",
                                "control_type": "direct"
                            }
                        ))
        
        return dict(relationships)
    
    def _analyze_circulation_relationships(self, objects: List[ArxObject]) -> Dict[str, List[Relationship]]:
        """Analyze circulation relationships (paths, connectivity)"""
        relationships = defaultdict(list)
        
        # Build circulation graph
        circulation_graph = self._build_circulation_graph(objects)
        
        # Find main circulation paths
        paths = self._find_circulation_paths(circulation_graph)
        
        for path in paths:
            for i in range(len(path) - 1):
                from_id = path[i]
                to_id = path[i + 1]
                
                relationships[from_id].append(Relationship(
                    type=RelationshipType.CONNECTED_TO,
                    target_id=to_id,
                    confidence=0.8,
                    properties={
                        "topology_type": "circulation",
                        "path_type": "primary"
                    }
                ))
        
        # Identify circulation nodes (doors, corridors, stairs)
        circulation_nodes = [
            obj for obj in objects 
            if obj.type in [ArxObjectType.DOOR, ArxObjectType.CORRIDOR, 
                           ArxObjectType.STAIRWELL, ArxObjectType.ELEVATOR_SHAFT]
        ]
        
        # Connect rooms through doors
        for door in circulation_nodes:
            if door.type == ArxObjectType.DOOR:
                connected_rooms = self._find_rooms_connected_by_door(door)
                
                for room1_id, room2_id in connected_rooms:
                    relationships[room1_id].append(Relationship(
                        type=RelationshipType.CONNECTED_TO,
                        target_id=room2_id,
                        confidence=0.9,
                        properties={
                            "topology_type": "circulation",
                            "connection": door.id,
                            "connection_type": "door"
                        }
                    ))
        
        return dict(relationships)
    
    def _find_adjacent_walls(self, wall: ArxObject) -> List[Tuple[str, float]]:
        """Find walls adjacent to given wall"""
        adjacent = []
        
        if not wall.bounds:
            return adjacent
        
        # Use spatial index to find nearby walls
        nearby = self.spatial_index.find_nearby(wall.id, max_distance=500_000_000)  # 500mm
        
        for nearby_id in nearby:
            nearby_obj = self.spatial_index.objects[nearby_id]
            
            if nearby_obj.type != ArxObjectType.WALL:
                continue
            
            # Check if walls are connected (share an endpoint or are perpendicular)
            if self._walls_are_connected(wall, nearby_obj):
                confidence = self._calculate_connection_confidence(wall, nearby_obj)
                adjacent.append((nearby_id, confidence))
        
        return adjacent
    
    def _walls_are_connected(self, wall1: ArxObject, wall2: ArxObject) -> bool:
        """Check if two walls are connected"""
        if not (wall1.bounds and wall2.bounds):
            return False
        
        # Check if walls share an endpoint or edge
        tolerance = 100_000_000  # 100mm tolerance
        
        # Check corners
        corners1 = [
            (wall1.bounds.min_point.x, wall1.bounds.min_point.y),
            (wall1.bounds.max_point.x, wall1.bounds.min_point.y),
            (wall1.bounds.min_point.x, wall1.bounds.max_point.y),
            (wall1.bounds.max_point.x, wall1.bounds.max_point.y)
        ]
        
        corners2 = [
            (wall2.bounds.min_point.x, wall2.bounds.min_point.y),
            (wall2.bounds.max_point.x, wall2.bounds.min_point.y),
            (wall2.bounds.min_point.x, wall2.bounds.max_point.y),
            (wall2.bounds.max_point.x, wall2.bounds.max_point.y)
        ]
        
        # Check if any corners are close
        for c1 in corners1:
            for c2 in corners2:
                dist = np.sqrt(float((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2))
                if dist < tolerance:
                    return True
        
        return False
    
    def _calculate_connection_confidence(self, wall1: ArxObject, wall2: ArxObject) -> float:
        """Calculate confidence of wall connection"""
        base_confidence = 0.5
        
        # Check angle between walls
        if wall1.data and wall2.data:
            angle1 = wall1.data.get("angle", 0)
            angle2 = wall2.data.get("angle", 0)
            
            angle_diff = abs(angle1 - angle2)
            
            # Perpendicular walls (90 degrees)
            if abs(angle_diff - 90) < 5 or abs(angle_diff - 270) < 5:
                base_confidence += 0.3
            # Parallel walls (0 or 180 degrees)
            elif angle_diff < 5 or abs(angle_diff - 180) < 5:
                base_confidence += 0.2
        
        # Check wall thickness match
        if wall1.dimensions and wall2.dimensions:
            thickness1 = wall1.dimensions.height
            thickness2 = wall2.dimensions.height
            
            if abs(thickness1 - thickness2) < 10_000_000:  # Within 10mm
                base_confidence += 0.2
        
        return min(base_confidence, 1.0)
    
    def _find_vertical_relationships(self, obj: ArxObject) -> Tuple[List[str], List[str]]:
        """Find objects above and below given object"""
        above = []
        below = []
        
        if not obj.bounds:
            return above, below
        
        z_center = (obj.bounds.min_point.z + obj.bounds.max_point.z) // 2
        
        for other_id, other_bounds in self.spatial_index.bounds_index.items():
            if other_id == obj.id:
                continue
            
            other_z_center = (other_bounds.min_point.z + other_bounds.max_point.z) // 2
            
            # Check horizontal overlap
            x_overlap = not (
                obj.bounds.max_point.x < other_bounds.min_point.x or
                obj.bounds.min_point.x > other_bounds.max_point.x
            )
            
            y_overlap = not (
                obj.bounds.max_point.y < other_bounds.min_point.y or
                obj.bounds.min_point.y > other_bounds.max_point.y
            )
            
            if x_overlap and y_overlap:
                if other_z_center > z_center:
                    above.append(other_id)
                elif other_z_center < z_center:
                    below.append(other_id)
        
        return above, below
    
    def _is_load_bearing_wall(self, wall: ArxObject) -> bool:
        """Determine if wall is load-bearing"""
        # Check wall thickness - thicker walls more likely load-bearing
        if wall.dimensions and wall.dimensions.height > 200_000_000:  # > 200mm
            return True
        
        # Check if wall is exterior (simplified check)
        if wall.data and wall.data.get("is_exterior", False):
            return True
        
        # Check if wall supports other elements
        above, _ = self._find_vertical_relationships(wall)
        if above:
            return True
        
        return False
    
    def _find_supported_elements(self, column: ArxObject) -> List[Tuple[str, float]]:
        """Find elements supported by column"""
        supported = []
        
        # Find elements directly above column
        above, _ = self._find_vertical_relationships(column)
        
        for elem_id in above:
            elem = self.spatial_index.objects[elem_id]
            if elem.type in [ArxObjectType.BEAM, ArxObjectType.SLAB]:
                supported.append((elem_id, 0.9))
        
        return supported
    
    def _find_beam_connections(self, beam: ArxObject) -> List[Tuple[str, str, float]]:
        """Find beam connections to columns and other beams"""
        connections = []
        
        # Find intersecting columns
        intersecting = self.spatial_index.find_intersecting(beam.id)
        
        for elem_id in intersecting:
            elem = self.spatial_index.objects[elem_id]
            
            if elem.type == ArxObjectType.COLUMN:
                connections.append((elem_id, "column_support", 0.9))
            elif elem.type == ArxObjectType.BEAM:
                connections.append((elem_id, "beam_junction", 0.8))
        
        return connections
    
    def _identify_systems(self, objects: List[ArxObject]) -> Dict[str, List[ArxObject]]:
        """Identify building systems (HVAC, electrical, plumbing)"""
        systems = defaultdict(list)
        
        for obj in objects:
            if obj.type in [ArxObjectType.HVAC_DUCT, ArxObjectType.HVAC_VENT, 
                           ArxObjectType.HVAC_UNIT, ArxObjectType.THERMOSTAT]:
                systems["hvac"].append(obj)
            
            elif obj.type in [ArxObjectType.ELECTRICAL_OUTLET, ArxObjectType.ELECTRICAL_SWITCH,
                             ArxObjectType.ELECTRICAL_PANEL, ArxObjectType.ELECTRICAL_CONDUIT,
                             ArxObjectType.LIGHT_FIXTURE]:
                systems["electrical"].append(obj)
            
            elif obj.type in [ArxObjectType.PLUMBING_PIPE, ArxObjectType.PLUMBING_FIXTURE,
                             ArxObjectType.VALVE, ArxObjectType.PUMP]:
                systems["plumbing"].append(obj)
        
        return dict(systems)
    
    def _find_system_flow(self, obj: ArxObject, system_objects: List[ArxObject]) -> Tuple[List[str], List[str]]:
        """Find upstream and downstream objects in system"""
        upstream = []
        downstream = []
        
        # Simplified - use proximity for now
        nearby = self.spatial_index.find_nearby(obj.id, max_distance=5_000_000_000)  # 5m
        
        for nearby_id in nearby:
            if nearby_id in [o.id for o in system_objects]:
                # Simplified flow direction based on type
                nearby_obj = self.spatial_index.objects[nearby_id]
                
                if self._is_upstream(obj.type, nearby_obj.type):
                    upstream.append(nearby_id)
                elif self._is_downstream(obj.type, nearby_obj.type):
                    downstream.append(nearby_id)
        
        return upstream, downstream
    
    def _is_upstream(self, type1: ArxObjectType, type2: ArxObjectType) -> bool:
        """Check if type2 is upstream of type1"""
        # Simplified logic
        upstream_map = {
            ArxObjectType.HVAC_VENT: [ArxObjectType.HVAC_DUCT, ArxObjectType.HVAC_UNIT],
            ArxObjectType.ELECTRICAL_OUTLET: [ArxObjectType.ELECTRICAL_CONDUIT, ArxObjectType.ELECTRICAL_PANEL],
            ArxObjectType.PLUMBING_FIXTURE: [ArxObjectType.PLUMBING_PIPE, ArxObjectType.PUMP],
        }
        
        return type2 in upstream_map.get(type1, [])
    
    def _is_downstream(self, type1: ArxObjectType, type2: ArxObjectType) -> bool:
        """Check if type2 is downstream of type1"""
        return self._is_upstream(type2, type1)
    
    def _find_controlled_elements(self, controller: ArxObject, system_objects: List[ArxObject]) -> List[str]:
        """Find elements controlled by controller"""
        controlled = []
        
        # Find nearby system elements
        nearby = self.spatial_index.find_nearby(controller.id, max_distance=10_000_000_000)  # 10m
        
        for nearby_id in nearby:
            if nearby_id in [o.id for o in system_objects]:
                nearby_obj = self.spatial_index.objects[nearby_id]
                
                # Check if element can be controlled
                if nearby_obj.type in [ArxObjectType.HVAC_UNIT, ArxObjectType.LIGHT_FIXTURE,
                                       ArxObjectType.VALVE, ArxObjectType.PUMP]:
                    controlled.append(nearby_id)
        
        return controlled
    
    def _build_circulation_graph(self, objects: List[ArxObject]) -> nx.Graph:
        """Build graph of circulation paths"""
        circ_graph = nx.Graph()
        
        # Add rooms and circulation spaces as nodes
        for obj in objects:
            if obj.type in [ArxObjectType.ROOM, ArxObjectType.CORRIDOR, 
                           ArxObjectType.STAIRWELL, ArxObjectType.ELEVATOR_SHAFT]:
                circ_graph.add_node(obj.id, type=obj.type.value)
        
        # Add edges through doors and openings
        for obj in objects:
            if obj.type in [ArxObjectType.DOOR, ArxObjectType.OPENING]:
                # Find connected spaces
                connected = self._find_spaces_connected_by_opening(obj)
                
                for space1, space2 in connected:
                    circ_graph.add_edge(space1, space2, connector=obj.id)
        
        return circ_graph
    
    def _find_circulation_paths(self, circ_graph: nx.Graph) -> List[List[str]]:
        """Find main circulation paths in building"""
        paths = []
        
        # Find all shortest paths between key spaces
        if len(circ_graph) > 0:
            # Find entrance/exit nodes (simplified)
            entrance_nodes = [n for n in circ_graph.nodes() 
                            if self.spatial_index.objects[n].data.get("is_entrance", False)]
            
            if not entrance_nodes and len(circ_graph) > 0:
                # Use first room as entrance
                entrance_nodes = [list(circ_graph.nodes())[0]]
            
            # Find paths from entrance to all other spaces
            for entrance in entrance_nodes:
                for target in circ_graph.nodes():
                    if target != entrance:
                        try:
                            path = nx.shortest_path(circ_graph, entrance, target)
                            if len(path) > 1:
                                paths.append(path)
                        except nx.NetworkXNoPath:
                            pass
        
        return paths
    
    def _find_rooms_connected_by_door(self, door: ArxObject) -> List[Tuple[str, str]]:
        """Find rooms connected by a door"""
        connections = []
        
        # Find nearby rooms
        nearby = self.spatial_index.find_nearby(door.id, max_distance=1_000_000_000)  # 1m
        
        rooms = []
        for nearby_id in nearby:
            nearby_obj = self.spatial_index.objects[nearby_id]
            if nearby_obj.type == ArxObjectType.ROOM:
                rooms.append(nearby_id)
        
        # Create connections between all pairs of rooms
        for i in range(len(rooms)):
            for j in range(i + 1, len(rooms)):
                connections.append((rooms[i], rooms[j]))
        
        return connections
    
    def _find_spaces_connected_by_opening(self, opening: ArxObject) -> List[Tuple[str, str]]:
        """Find spaces connected by an opening"""
        # Similar to door logic
        return self._find_rooms_connected_by_door(opening)
    
    def _merge_relationships(self, target: Dict[str, List[Relationship]], 
                           source: Dict[str, List[Relationship]]):
        """Merge relationships from source into target"""
        for obj_id, rels in source.items():
            if obj_id not in target:
                target[obj_id] = []
            
            # Avoid duplicates
            existing = set((r.type, r.target_id) for r in target[obj_id])
            
            for rel in rels:
                if (rel.type, rel.target_id) not in existing:
                    target[obj_id].append(rel)
    
    def _update_confidence_from_topology(self, objects: List[ArxObject], 
                                        relationships: Dict[str, List[Relationship]]):
        """Update object confidence based on topology consistency"""
        for obj in objects:
            if obj.id in relationships:
                rels = relationships[obj.id]
                
                # More relationships generally means higher confidence
                relationship_count = len(rels)
                
                if relationship_count > 0:
                    # Boost relationship confidence
                    boost = min(0.1 * (relationship_count / 10), 0.3)
                    obj.confidence.relationships = min(
                        obj.confidence.relationships + boost, 1.0
                    )
                    
                    # Recalculate overall confidence
                    obj.confidence.overall = (
                        obj.confidence.classification * 0.35 +
                        obj.confidence.position * 0.25 +
                        obj.confidence.properties * 0.20 +
                        obj.confidence.relationships * 0.20
                    )
    
    def get_topology_metrics(self) -> Dict[str, Any]:
        """Get metrics about the topology"""
        if not self.graph:
            return {}
        
        metrics = {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "connected_components": nx.number_weakly_connected_components(self.graph),
            "average_degree": sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes() if self.graph.number_of_nodes() > 0 else 0,
        }
        
        # Find most connected nodes (hubs)
        if self.graph.number_of_nodes() > 0:
            degrees = dict(self.graph.degree())
            sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
            metrics["hubs"] = sorted_nodes[:5]  # Top 5 most connected
        
        return metrics
"""
Enhanced BIM Builder Service
Builds hierarchical BIM structures from extracted SVG elements with spatial organization and system classification.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from models.bim import (
    BIMModel, Room, Wall, Door, Window, HVACZone, AirHandler, VAVBox,
    ElectricalCircuit, ElectricalPanel, ElectricalOutlet,
    PlumbingSystem, PlumbingFixture, Valve,
    FireAlarmSystem, SmokeDetector, SecuritySystem, Camera,
    Device, Label, SystemType, RoomType, DeviceCategory
)
from models.bim_metadata import BIMObjectMetadata, PropertySet, ClassificationReference
from models.bim_relationships import BIMRelationship, BIMRelationshipSet, SpatialRelationshipType, SystemRelationshipType
from services.bim_object_integration import BIMObjectIntegrationService

logger = logging.getLogger(__name__)

class BIMBuilder:
    """Enhanced BIM builder for creating hierarchical BIM structures."""
    
    def __init__(self):
        self.bim_integration = BIMObjectIntegrationService()
        self.relationships = BIMRelationshipSet()
        
    def build_hierarchical_bim_model(self, extracted_data: Dict[str, Any]) -> BIMModel:
        """
        Build a hierarchical BIM model from extracted SVG data.
        
        Args:
            extracted_data: Data from BIM extraction service
            
        Returns:
            BIMModel: Complete hierarchical BIM model
        """
        try:
            # Create base BIM model
            bim_model = BIMModel(
                name=extracted_data.get('metadata', {}).get('building_id', 'Unknown Building'),
                description="BIM model built from SVG extraction"
            )
            
            # 1. Build spatial hierarchy (floors -> rooms -> zones)
            self._build_spatial_hierarchy(bim_model, extracted_data)
            
            # 2. Build system hierarchy (systems -> equipment -> devices)
            self._build_system_hierarchy(bim_model, extracted_data)
            
            # 3. Establish relationships between elements
            self._establish_relationships(bim_model, extracted_data)
            
            # 4. Add metadata and classifications
            self._add_metadata_and_classifications(bim_model, extracted_data)
            
            # 5. Validate the complete model
            validation_errors = bim_model.validate_model()
            if validation_errors:
                logger.warning(f"BIM model validation warnings: {validation_errors}")
            
            logger.info(f"Built hierarchical BIM model with {len(bim_model.rooms)} rooms, {len(bim_model.devices)} devices")
            return bim_model
            
        except Exception as e:
            logger.error(f"Failed to build BIM model: {e}")
            raise
    
    def _build_spatial_hierarchy(self, bim_model: BIMModel, extracted_data: Dict[str, Any]):
        """Build spatial hierarchy: floors -> rooms -> zones."""
        
        # Extract rooms from the data
        rooms_data = extracted_data.get('rooms', [])
        svg_elements = extracted_data.get('svg_elements', [])
        
        # Group rooms by floor (if floor information is available)
        floors = defaultdict(list)
        for room_data in rooms_data:
            floor_level = room_data.get('floor_level', 1)  # Default to floor 1
            floors[floor_level].append(room_data)
        
        # Create rooms for each floor
        for floor_level, floor_rooms in floors.items():
            for room_data in floor_rooms:
                # Create room geometry from SVG elements
                room_geometry = self._create_room_geometry(room_data, svg_elements)
                
                if room_geometry:
                    room = Room(
                        name=room_data.get('name', f'Room {len(bim_model.rooms) + 1}'),
                        geometry=room_geometry,
                        room_type=RoomType(room_data.get('type', 'general')),
                        room_number=room_data.get('number'),
                        floor_level=float(floor_level),
                        area=room_data.get('area'),
                        ceiling_height=room_data.get('ceiling_height'),
                        occupants=room_data.get('occupants')
                    )
                    bim_model.add_element(room)
        
        # Create walls, doors, windows from SVG elements
        self._create_spatial_elements(bim_model, svg_elements)
    
    def _create_room_geometry(self, room_data: Dict[str, Any], svg_elements: List[Dict[str, Any]]) -> Optional[Any]:
        """Create room geometry from SVG elements."""
        # Look for polygon elements that might represent room boundaries
        for element in svg_elements:
            if element.get('type') == 'polygon' and element.get('parent_group'):
                group_label = element['parent_group'].get('label', '').lower()
                room_name = room_data.get('name', '').lower()
                
                # Simple matching - in a real system, this would be more sophisticated
                if any(word in group_label for word in room_name.split()) or any(word in room_name for word in group_label.split()):
                    from models.bim import Geometry, GeometryType
                    return Geometry(
                        type=GeometryType.POLYGON,
                        coordinates=element.get('geometry', {}).get('points', [])
                    )
        
        # If no specific geometry found, create a default rectangle
        from models.bim import Geometry, GeometryType
        return Geometry(
            type=GeometryType.POLYGON,
            coordinates=[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]  # Default 10x10 room
        )
    
    def _create_spatial_elements(self, bim_model: BIMModel, svg_elements: List[Dict[str, Any]]):
        """Create walls, doors, windows from SVG elements."""
        for element in svg_elements:
            if element.get('type') == 'line':
                # Assume lines are walls unless specified otherwise
                from models.bim import Wall, Geometry, GeometryType
                wall_geometry = Geometry(
                    type=GeometryType.LINESTRING,
                    coordinates=element.get('geometry', {}).get('points', [])
                )
                
                wall = Wall(
                    name=f"Wall {len(bim_model.walls) + 1}",
                    geometry=wall_geometry,
                    wall_type="interior",  # Default, could be determined from context
                    thickness=0.2,  # Default thickness
                    height=3.0  # Default height
                )
                bim_model.add_element(wall)
    
    def _build_system_hierarchy(self, bim_model: BIMModel, extracted_data: Dict[str, Any]):
        """Build system hierarchy: systems -> equipment -> devices."""
        
        devices_data = extracted_data.get('devices', [])
        svg_elements = extracted_data.get('svg_elements', [])
        
        # Group devices by system
        systems = defaultdict(list)
        for device_data in devices_data:
            system = device_data.get('system', 'unknown')
            systems[system].append(device_data)
        
        # Create HVAC system elements
        self._create_hvac_system(bim_model, systems.get('hvac', []), svg_elements)
        
        # Create electrical system elements
        self._create_electrical_system(bim_model, systems.get('electrical', []), svg_elements)
        
        # Create plumbing system elements
        self._create_plumbing_system(bim_model, systems.get('plumbing', []), svg_elements)
        
        # Create fire alarm system elements
        self._create_fire_alarm_system(bim_model, systems.get('fire_alarm', []), svg_elements)
        
        # Create security system elements
        self._create_security_system(bim_model, systems.get('security', []), svg_elements)
    
    def _create_hvac_system(self, bim_model: BIMModel, hvac_devices: List[Dict[str, Any]], svg_elements: List[Dict[str, Any]]):
        """Create HVAC system elements."""
        for device_data in hvac_devices:
            device_type = device_data.get('category', '')
            
            if device_type == 'ahu':
                ahu = AirHandler(
                    name=device_data.get('name', f'AHU {len(bim_model.air_handlers) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    capacity=device_data.get('properties', {}).get('capacity'),
                    airflow=device_data.get('properties', {}).get('airflow'),
                    efficiency=device_data.get('properties', {}).get('efficiency'),
                    manufacturer=device_data.get('properties', {}).get('manufacturer'),
                    model=device_data.get('properties', {}).get('model')
                )
                bim_model.add_element(ahu)
            
            elif device_type == 'vav':
                vav = VAVBox(
                    name=device_data.get('name', f'VAV {len(bim_model.vav_boxes) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    max_airflow=device_data.get('properties', {}).get('max_airflow'),
                    min_airflow=device_data.get('properties', {}).get('min_airflow'),
                    reheat_capacity=device_data.get('properties', {}).get('reheat_capacity')
                )
                bim_model.add_element(vav)
            
            else:
                # Generic HVAC device
                device = Device(
                    name=device_data.get('name', f'HVAC Device {len(bim_model.devices) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    system_type=SystemType.HVAC,
                    category=DeviceCategory(device_type) if device_type else DeviceCategory.AHU,
                    manufacturer=device_data.get('properties', {}).get('manufacturer'),
                    model=device_data.get('properties', {}).get('model')
                )
                bim_model.add_element(device)
    
    def _create_electrical_system(self, bim_model: BIMModel, electrical_devices: List[Dict[str, Any]], svg_elements: List[Dict[str, Any]]):
        """Create electrical system elements."""
        for device_data in electrical_devices:
            device_type = device_data.get('category', '')
            
            if device_type == 'panel':
                panel = ElectricalPanel(
                    name=device_data.get('name', f'Panel {len(bim_model.electrical_panels) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    voltage=device_data.get('properties', {}).get('voltage'),
                    amperage=device_data.get('properties', {}).get('amperage'),
                    phase=device_data.get('properties', {}).get('phase'),
                    circuit_count=device_data.get('properties', {}).get('circuit_count')
                )
                bim_model.add_element(panel)
            
            elif device_type == 'outlet':
                outlet = ElectricalOutlet(
                    name=device_data.get('name', f'Outlet {len(bim_model.electrical_outlets) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    voltage=device_data.get('properties', {}).get('voltage'),
                    amperage=device_data.get('properties', {}).get('amperage'),
                    is_gfci=device_data.get('properties', {}).get('is_gfci', False)
                )
                bim_model.add_element(outlet)
            
            else:
                # Generic electrical device
                device = Device(
                    name=device_data.get('name', f'Electrical Device {len(bim_model.devices) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    system_type=SystemType.ELECTRICAL,
                    category=DeviceCategory(device_type) if device_type else DeviceCategory.OUTLET,
                    manufacturer=device_data.get('properties', {}).get('manufacturer'),
                    model=device_data.get('properties', {}).get('model')
                )
                bim_model.add_element(device)
    
    def _create_plumbing_system(self, bim_model: BIMModel, plumbing_devices: List[Dict[str, Any]], svg_elements: List[Dict[str, Any]]):
        """Create plumbing system elements."""
        for device_data in plumbing_devices:
            device_type = device_data.get('category', '')
            
            if device_type == 'fixture':
                fixture = PlumbingFixture(
                    name=device_data.get('name', f'Fixture {len(bim_model.plumbing_fixtures) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    fixture_type=device_data.get('properties', {}).get('fixture_type', 'sink'),
                    flow_rate=device_data.get('properties', {}).get('flow_rate'),
                    manufacturer=device_data.get('properties', {}).get('manufacturer'),
                    model=device_data.get('properties', {}).get('model')
                )
                bim_model.add_element(fixture)
            
            elif device_type == 'valve':
                valve = Valve(
                    name=device_data.get('name', f'Valve {len(bim_model.valves) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    valve_type=device_data.get('properties', {}).get('valve_type', 'ball'),
                    size=device_data.get('properties', {}).get('size'),
                    material=device_data.get('properties', {}).get('material'),
                    is_automatic=device_data.get('properties', {}).get('is_automatic', False)
                )
                bim_model.add_element(valve)
            
            else:
                # Generic plumbing device
                device = Device(
                    name=device_data.get('name', f'Plumbing Device {len(bim_model.devices) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    system_type=SystemType.PLUMBING,
                    category=DeviceCategory(device_type) if device_type else DeviceCategory.VALVE,
                    manufacturer=device_data.get('properties', {}).get('manufacturer'),
                    model=device_data.get('properties', {}).get('model')
                )
                bim_model.add_element(device)
    
    def _create_fire_alarm_system(self, bim_model: BIMModel, fire_alarm_devices: List[Dict[str, Any]], svg_elements: List[Dict[str, Any]]):
        """Create fire alarm system elements."""
        for device_data in fire_alarm_devices:
            device_type = device_data.get('category', '')
            
            if device_type == 'smoke_detector':
                detector = SmokeDetector(
                    name=device_data.get('name', f'Smoke Detector {len(bim_model.smoke_detectors) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    detector_type=device_data.get('properties', {}).get('detector_type', 'photoelectric'),
                    coverage_area=device_data.get('properties', {}).get('coverage_area'),
                    battery_type=device_data.get('properties', {}).get('battery_type')
                )
                bim_model.add_element(detector)
            
            else:
                # Generic fire alarm device
                device = Device(
                    name=device_data.get('name', f'Fire Alarm Device {len(bim_model.devices) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    system_type=SystemType.FIRE_ALARM,
                    category=DeviceCategory(device_type) if device_type else DeviceCategory.SMOKE_DETECTOR,
                    manufacturer=device_data.get('properties', {}).get('manufacturer'),
                    model=device_data.get('properties', {}).get('model')
                )
                bim_model.add_element(device)
    
    def _create_security_system(self, bim_model: BIMModel, security_devices: List[Dict[str, Any]], svg_elements: List[Dict[str, Any]]):
        """Create security system elements."""
        for device_data in security_devices:
            device_type = device_data.get('category', '')
            
            if device_type == 'camera':
                camera = Camera(
                    name=device_data.get('name', f'Camera {len(bim_model.cameras) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    camera_type=device_data.get('properties', {}).get('camera_type', 'dome'),
                    resolution=device_data.get('properties', {}).get('resolution'),
                    night_vision=device_data.get('properties', {}).get('night_vision', False),
                    ptz_capable=device_data.get('properties', {}).get('ptz_capable', False)
                )
                bim_model.add_element(camera)
            
            else:
                # Generic security device
                device = Device(
                    name=device_data.get('name', f'Security Device {len(bim_model.devices) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    system_type=SystemType.SECURITY,
                    category=DeviceCategory(device_type) if device_type else DeviceCategory.CAMERA,
                    manufacturer=device_data.get('properties', {}).get('manufacturer'),
                    model=device_data.get('properties', {}).get('model')
                )
                bim_model.add_element(device)
    
    def _create_device_geometry(self, device_data: Dict[str, Any], svg_elements: List[Dict[str, Any]]) -> Any:
        """Create device geometry from SVG elements."""
        # Look for point elements that might represent device positions
        for element in svg_elements:
            if element.get('type') == 'circle' and element.get('parent_group'):
                group_label = element['parent_group'].get('label', '').lower()
                device_name = device_data.get('name', '').lower()
                
                # Simple matching - in a real system, this would be more sophisticated
                if any(word in group_label for word in device_name.split()) or any(word in device_name for word in group_label.split()):
                    from models.bim import Geometry, GeometryType
                    return Geometry(
                        type=GeometryType.POINT,
                        coordinates=[element['geometry'].get('cx', 0), element['geometry'].get('cy', 0)]
                    )
        
        # If no specific geometry found, create a default point
        from models.bim import Geometry, GeometryType
        return Geometry(
            type=GeometryType.POINT,
            coordinates=[0, 0]  # Default position
        )
    
    def _establish_relationships(self, bim_model: BIMModel, extracted_data: Dict[str, Any]):
        """Establish relationships between BIM elements."""
        
        # Spatial relationships (rooms contain devices)
        for room in bim_model.rooms:
            for device in bim_model.devices:
                # Simple spatial relationship - in a real system, this would use proper spatial analysis
                if self._is_device_in_room(device, room):
                    room.add_child(device.id)
                    device.parent_id = room.id
        
        # System relationships (equipment connected to devices)
        for device in bim_model.devices:
            if device.system_type == SystemType.HVAC:
                # Connect HVAC devices to rooms
                for room in bim_model.rooms:
                    if self._is_device_in_room(device, room):
                        device.add_child(room.id)
        
        # Electrical relationships (panels supply outlets)
        panels = [elem for elem in bim_model.electrical_panels]
        outlets = [elem for elem in bim_model.electrical_outlets]
        
        for panel in panels:
            for outlet in outlets:
                # Simple proximity-based relationship
                if self._are_elements_nearby(panel, outlet):
                    panel.add_child(outlet.id)
                    outlet.parent_id = panel.id
    
    def _is_device_in_room(self, device: Device, room: Room) -> bool:
        """Check if device is in room (simplified spatial analysis)."""
        # This is a simplified check - real implementation would use proper spatial analysis
        device_pos = device.geometry.coordinates
        room_bounds = room.geometry.coordinates
        
        if len(device_pos) >= 2 and len(room_bounds) >= 4:
            x, y = device_pos[0], device_pos[1]
            # Simple point-in-polygon check
            return self._point_in_polygon(x, y, room_bounds)
        
        return False
    
    def _point_in_polygon(self, x: float, y: float, polygon: List[List[float]]) -> bool:
        """Simple point-in-polygon test."""
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _are_elements_nearby(self, elem1: Any, elem2: Any, threshold: float = 50.0) -> bool:
        """Check if two elements are nearby (simplified proximity check)."""
        pos1 = elem1.geometry.coordinates
        pos2 = elem2.geometry.coordinates
        
        if len(pos1) >= 2 and len(pos2) >= 2:
            distance = ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
            return distance < threshold
        
        return False
    
    def _add_metadata_and_classifications(self, bim_model: BIMModel, extracted_data: Dict[str, Any]):
        """Add metadata and classifications to BIM elements."""
        
        # Add metadata to the BIM model
        bim_model.model_metadata.update({
            'extraction_date': extracted_data.get('metadata', {}).get('extraction_date'),
            'building_id': extracted_data.get('metadata', {}).get('building_id'),
            'floor_label': extracted_data.get('metadata', {}).get('floor_label'),
            'total_rooms': len(bim_model.rooms),
            'total_devices': len(bim_model.devices),
            'systems_present': list(set(device.system_type.value for device in bim_model.devices))
        })
        
        # Add classifications to elements
        for element in bim_model.rooms + bim_model.devices + bim_model.walls:
            if hasattr(element, 'metadata'):
                element.symbol_metadata.update({
                    'classification': {
                        'system': getattr(element, 'system_type', 'unknown'),
                        'category': getattr(element, 'category', 'unknown'),
                        'extraction_method': 'svg_parser'
                    }
                })

def build_bim_model(classified_elements: List[Dict[str, Any]]) -> BIMModel:
    """
    Builds a BIMModel from classified elements.
    
    Args:
        classified_elements: List of classified element dicts.
        
    Returns:
        BIMModel: Assembled BIM model.
    """
    builder = BIMBuilder()
    
    # Convert classified elements to the format expected by the builder
    extracted_data = {
        'metadata': {
            'building_id': 'extracted_building',
            'extraction_date': datetime.now().isoformat()
        },
        'rooms': [elem for elem in classified_elements if elem.get('type') == 'room'],
        'devices': [elem for elem in classified_elements if elem.get('type') == 'device'],
        'svg_elements': [elem for elem in classified_elements if elem.get('type') in ['line', 'rect', 'circle', 'polygon']]
    }
    
    return builder.build_hierarchical_bim_model(extracted_data) 
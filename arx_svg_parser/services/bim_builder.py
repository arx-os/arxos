"""
Enhanced BIM Builder Service
Builds hierarchical BIM structures from extracted SVG elements with spatial organization and system classification.
"""

import structlog
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

logger = structlog.get_logger(__name__)

class BIMBuilder:
    """Enhanced BIM builder for creating hierarchical BIM structures."""
    
    def __init__(self):
        self.bim_integration = BIMObjectIntegrationService()
        self.relationships = BIMRelationshipSet()
        
        logger.info("bim_builder_initialized",
                   integration_service="BIMObjectIntegrationService",
                   relationships_set="BIMRelationshipSet")
        
    def build_hierarchical_bim_model(self, extracted_data: Dict[str, Any]) -> BIMModel:
        """
        Build a hierarchical BIM model from extracted SVG data.
        
        Args:
            extracted_data: Data from BIM extraction service
            
        Returns:
            BIMModel: Complete hierarchical BIM model
        """
        try:
            logger.info("bim_model_construction_started",
                       building_id=extracted_data.get('metadata', {}).get('building_id'),
                       rooms_count=len(extracted_data.get('rooms', [])),
                       devices_count=len(extracted_data.get('devices', [])),
                       svg_elements_count=len(extracted_data.get('svg_elements', [])))
            
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
                logger.warning("bim_model_validation_warnings",
                              building_id=bim_model.name,
                              validation_errors=validation_errors)
            
            logger.info("bim_model_construction_completed",
                       building_id=bim_model.name,
                       rooms_count=len(bim_model.rooms),
                       devices_count=len(bim_model.devices),
                       walls_count=len(bim_model.walls),
                       air_handlers_count=len(bim_model.air_handlers),
                       vav_boxes_count=len(bim_model.vav_boxes),
                       electrical_panels_count=len(bim_model.electrical_panels),
                       plumbing_fixtures_count=len(bim_model.plumbing_fixtures))
            
            return bim_model
            
        except Exception as e:
            logger.error("bim_model_construction_failed",
                        building_id=extracted_data.get('metadata', {}).get('building_id'),
                        error=str(e),
                        error_type=type(e).__name__)
            raise
    
    def _build_spatial_hierarchy(self, bim_model: BIMModel, extracted_data: Dict[str, Any]):
        """Build spatial hierarchy: floors -> rooms -> zones."""
        
        logger.debug("spatial_hierarchy_construction_started",
                    building_id=bim_model.name)
        
        # Extract rooms from the data
        rooms_data = extracted_data.get('rooms', [])
        svg_elements = extracted_data.get('svg_elements', [])
        
        # Group rooms by floor (if floor information is available)
        floors = defaultdict(list)
        for room_data in rooms_data:
            floor_level = room_data.get('floor_level', 1)  # Default to floor 1
            floors[floor_level].append(room_data)
        
        logger.debug("room_grouping_by_floor",
                    building_id=bim_model.name,
                    total_rooms=len(rooms_data),
                    floors_count=len(floors),
                    rooms_per_floor={floor: len(rooms) for floor, rooms in floors.items()})
        
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
                    
                    logger.debug("room_created",
                               building_id=bim_model.name,
                               room_name=room.name,
                               room_type=room.room_type.value,
                               floor_level=room.floor_level,
                               area=room.area)
        
        # Create walls, doors, windows from SVG elements
        self._create_spatial_elements(bim_model, svg_elements)
        
        logger.info("spatial_hierarchy_construction_completed",
                   building_id=bim_model.name,
                   rooms_created=len(bim_model.rooms),
                   walls_created=len(bim_model.walls))
    
    def _create_room_geometry(self, room_data: Dict[str, Any], svg_elements: List[Dict[str, Any]]) -> Optional[Any]:
        """Create room geometry from SVG elements."""
        room_name = room_data.get('name', '')
        
        # Look for polygon elements that might represent room boundaries
        for element in svg_elements:
            if element.get('type') == 'polygon' and element.get('parent_group'):
                group_label = element['parent_group'].get('label', '').lower()
                room_name_lower = room_name.lower()
                
                # Simple matching - in a real system, this would be more sophisticated
                if any(word in group_label for word in room_name_lower.split()) or any(word in room_name_lower for word in group_label.split()):
                    from models.bim import Geometry, GeometryType
                    geometry = Geometry(
                        type=GeometryType.POLYGON,
                        coordinates=element.get('geometry', {}).get('points', [])
                    )
                    
                    logger.debug("room_geometry_found",
                               room_name=room_name,
                               geometry_type="polygon",
                               coordinates_count=len(element.get('geometry', {}).get('points', [])))
                    
                    return geometry
        
        # If no specific geometry found, create a default rectangle
        from models.bim import Geometry, GeometryType
        default_geometry = Geometry(
            type=GeometryType.POLYGON,
            coordinates=[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]  # Default 10x10 room
        )
        
        logger.debug("room_geometry_default_created",
                    room_name=room_name,
                    geometry_type="default_polygon")
        
        return default_geometry
    
    def _create_spatial_elements(self, bim_model: BIMModel, svg_elements: List[Dict[str, Any]]):
        """Create walls, doors, windows from SVG elements."""
        walls_created = 0
        
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
                walls_created += 1
        
        logger.debug("spatial_elements_created",
                    building_id=bim_model.name,
                    walls_created=walls_created)
    
    def _build_system_hierarchy(self, bim_model: BIMModel, extracted_data: Dict[str, Any]):
        """Build system hierarchy: systems -> equipment -> devices."""
        
        logger.debug("system_hierarchy_construction_started",
                    building_id=bim_model.name)
        
        devices_data = extracted_data.get('devices', [])
        svg_elements = extracted_data.get('svg_elements', [])
        
        # Group devices by system
        systems = defaultdict(list)
        for device_data in devices_data:
            system = device_data.get('system', 'unknown')
            systems[system].append(device_data)
        
        logger.debug("devices_grouped_by_system",
                    building_id=bim_model.name,
                    total_devices=len(devices_data),
                    systems_count=len(systems),
                    devices_per_system={system: len(devices) for system, devices in systems.items()})
        
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
        
        logger.info("system_hierarchy_construction_completed",
                   building_id=bim_model.name,
                   hvac_devices=len(systems.get('hvac', [])),
                   electrical_devices=len(systems.get('electrical', [])),
                   plumbing_devices=len(systems.get('plumbing', [])),
                   fire_alarm_devices=len(systems.get('fire_alarm', [])),
                   security_devices=len(systems.get('security', [])))
    
    def _create_hvac_system(self, bim_model: BIMModel, hvac_devices: List[Dict[str, Any]], svg_elements: List[Dict[str, Any]]):
        """Create HVAC system elements."""
        ahu_count = 0
        vav_count = 0
        
        for device_data in hvac_devices:
            device_type = device_data.get('category', '')
            device_name = device_data.get('name', 'Unknown')
            
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
                ahu_count += 1
                
                logger.debug("hvac_ahu_created",
                           building_id=bim_model.name,
                           device_name=device_name,
                           capacity=ahu.capacity,
                           airflow=ahu.airflow)
            
            elif device_type == 'vav':
                vav = VAVBox(
                    name=device_data.get('name', f'VAV {len(bim_model.vav_boxes) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    max_airflow=device_data.get('properties', {}).get('max_airflow'),
                    min_airflow=device_data.get('properties', {}).get('min_airflow'),
                    reheat_capacity=device_data.get('properties', {}).get('reheat_capacity')
                )
                bim_model.add_element(vav)
                vav_count += 1
                
                logger.debug("hvac_vav_created",
                           building_id=bim_model.name,
                           device_name=device_name,
                           max_airflow=vav.max_airflow,
                           min_airflow=vav.min_airflow)
        
        logger.info("hvac_system_created",
                   building_id=bim_model.name,
                   ahu_count=ahu_count,
                   vav_count=vav_count,
                   total_hvac_devices=len(hvac_devices))
    
    def _create_electrical_system(self, bim_model: BIMModel, electrical_devices: List[Dict[str, Any]], svg_elements: List[Dict[str, Any]]):
        """Create electrical system elements."""
        panel_count = 0
        outlet_count = 0
        
        for device_data in electrical_devices:
            device_type = device_data.get('category', '')
            device_name = device_data.get('name', 'Unknown')
            
            if device_type == 'panel':
                panel = ElectricalPanel(
                    name=device_data.get('name', f'Panel {len(bim_model.electrical_panels) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    capacity=device_data.get('properties', {}).get('capacity'),
                    voltage=device_data.get('properties', {}).get('voltage'),
                    phases=device_data.get('properties', {}).get('phases'),
                    manufacturer=device_data.get('properties', {}).get('manufacturer')
                )
                bim_model.add_element(panel)
                panel_count += 1
                
                logger.debug("electrical_panel_created",
                           building_id=bim_model.name,
                           device_name=device_name,
                           capacity=panel.capacity,
                           voltage=panel.voltage)
            
            elif device_type == 'outlet':
                outlet = ElectricalOutlet(
                    name=device_data.get('name', f'Outlet {len(bim_model.electrical_outlets) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    voltage=device_data.get('properties', {}).get('voltage'),
                    amperage=device_data.get('properties', {}).get('amperage'),
                    outlet_type=device_data.get('properties', {}).get('outlet_type')
                )
                bim_model.add_element(outlet)
                outlet_count += 1
                
                logger.debug("electrical_outlet_created",
                           building_id=bim_model.name,
                           device_name=device_name,
                           voltage=outlet.voltage,
                           amperage=outlet.amperage)
        
        logger.info("electrical_system_created",
                   building_id=bim_model.name,
                   panel_count=panel_count,
                   outlet_count=outlet_count,
                   total_electrical_devices=len(electrical_devices))
    
    def _create_plumbing_system(self, bim_model: BIMModel, plumbing_devices: List[Dict[str, Any]], svg_elements: List[Dict[str, Any]]):
        """Create plumbing system elements."""
        fixture_count = 0
        valve_count = 0
        
        for device_data in plumbing_devices:
            device_type = device_data.get('category', '')
            device_name = device_data.get('name', 'Unknown')
            
            if device_type == 'fixture':
                fixture = PlumbingFixture(
                    name=device_data.get('name', f'Fixture {len(bim_model.plumbing_fixtures) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    fixture_type=device_data.get('properties', {}).get('fixture_type'),
                    flow_rate=device_data.get('properties', {}).get('flow_rate'),
                    manufacturer=device_data.get('properties', {}).get('manufacturer')
                )
                bim_model.add_element(fixture)
                fixture_count += 1
                
                logger.debug("plumbing_fixture_created",
                           building_id=bim_model.name,
                           device_name=device_name,
                           fixture_type=fixture.fixture_type,
                           flow_rate=fixture.flow_rate)
            
            elif device_type == 'valve':
                valve = Valve(
                    name=device_data.get('name', f'Valve {len(bim_model.valves) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    valve_type=device_data.get('properties', {}).get('valve_type'),
                    size=device_data.get('properties', {}).get('size'),
                    pressure_rating=device_data.get('properties', {}).get('pressure_rating')
                )
                bim_model.add_element(valve)
                valve_count += 1
                
                logger.debug("plumbing_valve_created",
                           building_id=bim_model.name,
                           device_name=device_name,
                           valve_type=valve.valve_type,
                           size=valve.size)
        
        logger.info("plumbing_system_created",
                   building_id=bim_model.name,
                   fixture_count=fixture_count,
                   valve_count=valve_count,
                   total_plumbing_devices=len(plumbing_devices))
    
    def _create_fire_alarm_system(self, bim_model: BIMModel, fire_alarm_devices: List[Dict[str, Any]], svg_elements: List[Dict[str, Any]]):
        """Create fire alarm system elements."""
        detector_count = 0
        
        for device_data in fire_alarm_devices:
            device_type = device_data.get('category', '')
            device_name = device_data.get('name', 'Unknown')
            
            if device_type == 'smoke_detector':
                detector = SmokeDetector(
                    name=device_data.get('name', f'Smoke Detector {len(bim_model.smoke_detectors) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    detector_type=device_data.get('properties', {}).get('detector_type'),
                    sensitivity=device_data.get('properties', {}).get('sensitivity'),
                    manufacturer=device_data.get('properties', {}).get('manufacturer')
                )
                bim_model.add_element(detector)
                detector_count += 1
                
                logger.debug("fire_alarm_detector_created",
                           building_id=bim_model.name,
                           device_name=device_name,
                           detector_type=detector.detector_type,
                           sensitivity=detector.sensitivity)
        
        logger.info("fire_alarm_system_created",
                   building_id=bim_model.name,
                   detector_count=detector_count,
                   total_fire_alarm_devices=len(fire_alarm_devices))
    
    def _create_security_system(self, bim_model: BIMModel, security_devices: List[Dict[str, Any]], svg_elements: List[Dict[str, Any]]):
        """Create security system elements."""
        camera_count = 0
        
        for device_data in security_devices:
            device_type = device_data.get('category', '')
            device_name = device_data.get('name', 'Unknown')
            
            if device_type == 'camera':
                camera = Camera(
                    name=device_data.get('name', f'Camera {len(bim_model.cameras) + 1}'),
                    geometry=self._create_device_geometry(device_data, svg_elements),
                    camera_type=device_data.get('properties', {}).get('camera_type'),
                    resolution=device_data.get('properties', {}).get('resolution'),
                    field_of_view=device_data.get('properties', {}).get('field_of_view'),
                    manufacturer=device_data.get('properties', {}).get('manufacturer')
                )
                bim_model.add_element(camera)
                camera_count += 1
                
                logger.debug("security_camera_created",
                           building_id=bim_model.name,
                           device_name=device_name,
                           camera_type=camera.camera_type,
                           resolution=camera.resolution)
        
        logger.info("security_system_created",
                   building_id=bim_model.name,
                   camera_count=camera_count,
                   total_security_devices=len(security_devices))
    
    def _create_device_geometry(self, device_data: Dict[str, Any], svg_elements: List[Dict[str, Any]]) -> Any:
        """Create device geometry from SVG elements."""
        device_name = device_data.get('name', 'Unknown')
        
        # Look for matching SVG element
        for element in svg_elements:
            if element.get('id') == device_data.get('svg_id'):
                from models.bim import Geometry, GeometryType
                
                element_type = element.get('type', 'point')
                if element_type == 'circle':
                    geometry = Geometry(
                        type=GeometryType.POINT,
                        coordinates=element.get('geometry', {}).get('center', [0, 0])
                    )
                elif element_type == 'rect':
                    geometry = Geometry(
                        type=GeometryType.POLYGON,
                        coordinates=element.get('geometry', {}).get('points', [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]])
                    )
                else:
                    geometry = Geometry(
                        type=GeometryType.POINT,
                        coordinates=element.get('geometry', {}).get('center', [0, 0])
                    )
                
                logger.debug("device_geometry_created",
                           device_name=device_name,
                           geometry_type=geometry.type.value,
                           coordinates=geometry.coordinates)
                
                return geometry
        
        # Default geometry if no match found
        from models.bim import Geometry, GeometryType
        default_geometry = Geometry(
            type=GeometryType.POINT,
            coordinates=[0, 0]
        )
        
        logger.debug("device_geometry_default_created",
                    device_name=device_name,
                    geometry_type="default_point")
        
        return default_geometry
    
    def _establish_relationships(self, bim_model: BIMModel, extracted_data: Dict[str, Any]):
        """Establish relationships between BIM elements."""
        
        logger.debug("relationships_establishment_started",
                    building_id=bim_model.name)
        
        relationships_created = 0
        
        # Establish spatial relationships (devices in rooms)
        for device in bim_model.devices:
            for room in bim_model.rooms:
                if self._is_device_in_room(device, room):
                    relationship = BIMRelationship(
                        source_id=device.id,
                        target_id=room.id,
                        relationship_type=SpatialRelationshipType.CONTAINED_IN,
                        properties={"confidence": 0.9}
                    )
                    self.relationships.add_relationship(relationship)
                    relationships_created += 1
                    
                    logger.debug("spatial_relationship_created",
                               building_id=bim_model.name,
                               device_name=device.name,
                               room_name=room.name,
                               relationship_type="contained_in")
        
        # Establish system relationships (devices connected to systems)
        for device in bim_model.devices:
            if hasattr(device, 'system_id') and device.system_id:
                relationship = BIMRelationship(
                    source_id=device.id,
                    target_id=device.system_id,
                    relationship_type=SystemRelationshipType.BELONGS_TO,
                    properties={"confidence": 0.8}
                )
                self.relationships.add_relationship(relationship)
                relationships_created += 1
                
                logger.debug("system_relationship_created",
                           building_id=bim_model.name,
                           device_name=device.name,
                           system_id=device.system_id,
                           relationship_type="belongs_to")
        
        logger.info("relationships_establishment_completed",
                   building_id=bim_model.name,
                   relationships_created=relationships_created,
                   total_relationships=len(self.relationships.relationships))
    
    def _is_device_in_room(self, device: Device, room: Room) -> bool:
        """Check if a device is located within a room."""
        if not device.geometry or not room.geometry:
            return False
        
        # Simple point-in-polygon check for device center
        device_center = device.geometry.coordinates
        if isinstance(device_center, list) and len(device_center) >= 2:
            x, y = device_center[0], device_center[1]
            return self._point_in_polygon(x, y, room.geometry.coordinates)
        
        return False
    
    def _point_in_polygon(self, x: float, y: float, polygon: List[List[float]]) -> bool:
        """Check if a point is inside a polygon using ray casting algorithm."""
        if len(polygon) < 3:
            return False
        
        inside = False
        j = len(polygon) - 1
        
        for i in range(len(polygon)):
            if ((polygon[i][1] > y) != (polygon[j][1] > y) and
                x < (polygon[j][0] - polygon[i][0]) * (y - polygon[i][1]) / (polygon[j][1] - polygon[i][1]) + polygon[i][0]):
                inside = not inside
            j = i
        
        return inside
    
    def _are_elements_nearby(self, elem1: Any, elem2: Any, threshold: float = 50.0) -> bool:
        """Check if two elements are spatially close to each other."""
        if not elem1.geometry or not elem2.geometry:
            return False
        
        # Simple distance calculation between element centers
        center1 = elem1.geometry.coordinates
        center2 = elem2.geometry.coordinates
        
        if isinstance(center1, list) and isinstance(center2, list) and len(center1) >= 2 and len(center2) >= 2:
            distance = ((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2) ** 0.5
            return distance <= threshold
        
        return False
    
    def _add_metadata_and_classifications(self, bim_model: BIMModel, extracted_data: Dict[str, Any]):
        """Add metadata and classifications to BIM elements."""
        
        logger.debug("metadata_and_classifications_started",
                    building_id=bim_model.name)
        
        # Add metadata to all elements
        for element in bim_model.all_elements():
            metadata = BIMObjectMetadata(
                created_by="BIM Builder",
                created_date=datetime.utcnow(),
                source="SVG Extraction",
                version="1.0"
            )
            element.metadata = metadata
        
        # Add classifications
        for element in bim_model.all_elements():
            if hasattr(element, 'category'):
                classification = ClassificationReference(
                    system="IFC",
                    identifier=element.category.value if hasattr(element.category, 'value') else str(element.category),
                    name=element.category.name if hasattr(element.category, 'name') else str(element.category)
                )
                element.classifications = [classification]
        
        logger.info("metadata_and_classifications_completed",
                   building_id=bim_model.name,
                   elements_processed=len(bim_model.all_elements()))

def build_bim_model(classified_elements: List[Dict[str, Any]]) -> BIMModel:
    """Convenience function to build a BIM model from classified elements."""
    builder = BIMBuilder()
    
    # Convert classified elements to extracted data format
    extracted_data = {
        'metadata': {'building_id': 'Generated Building'},
        'rooms': [elem for elem in classified_elements if elem.get('type') == 'room'],
        'devices': [elem for elem in classified_elements if elem.get('type') == 'device'],
        'svg_elements': [elem for elem in classified_elements if elem.get('type') == 'svg_element']
    }
    
    return builder.build_hierarchical_bim_model(extracted_data) 
from typing import List, Optional, Tuple, Any, Dict, Union, Literal
from pydantic import BaseModel, field_validator, Field, model_validator
from datetime import datetime, timezone
from enum import Enum
import uuid
import json

# Enums for type safety
class GeometryType(str, Enum):
    POLYGON = "Polygon"
    LINESTRING = "LineString"
    POINT = "Point"
    MULTIPOLYGON = "MultiPolygon"
    MULTILINESTRING = "MultiLineString"
    MULTIPOINT = "MultiPoint"

class SystemType(str, Enum):
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    FIRE_ALARM = "fire_alarm"
    SECURITY = "security"
    STRUCTURAL = "structural"
    HVAC = "hvac"
    LIGHTING = "lighting"
    VENTILATION = "ventilation"

class RoomType(str, Enum):
    OFFICE = "office"
    CONFERENCE = "conference"
    BREAK_ROOM = "break_room"
    LOBBY = "lobby"
    CIRCULATION = "circulation"
    BATHROOM = "bathroom"
    STORAGE = "storage"
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    GENERAL = "general"

class DeviceCategory(str, Enum):
    # HVAC Devices
    AHU = "ahu"
    VAV = "vav"
    FCU = "fcu"
    RTU = "rtu"
    CHILLER = "chiller"
    BOILER = "boiler"
    PUMP = "pump"
    FAN = "fan"
    DAMPER = "damper"
    THERMOSTAT = "thermostat"
    
    # Electrical Devices
    PANEL = "panel"
    OUTLET = "outlet"
    SWITCH = "switch"
    LIGHT = "light"
    TRANSFORMER = "transformer"
    UPS = "ups"
    CONTROLLER = "controller"
    
    # Plumbing Devices
    VALVE = "valve"
    FAUCET = "faucet"
    DRAIN = "drain"
    PIPE = "pipe"
    FIXTURE = "fixture"
    
    # Fire Alarm Devices
    SMOKE_DETECTOR = "smoke_detector"
    HEAT_DETECTOR = "heat_detector"
    HORN_STROBE = "horn_strobe"
    PULL_STATION = "pull_station"
    ANNUNCIATOR = "annunciator"
    
    # Security Devices
    CAMERA = "camera"
    CARD_READER = "card_reader"
    MOTION_DETECTOR = "motion_detector"
    DOOR_CONTACT = "door_contact"
    MAG_LOCK = "mag_lock"

# Base Geometry Model
class Geometry(BaseModel):
    type: GeometryType
    coordinates: Any
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator('coordinates')
    @classmethod
    def validate_coordinates(cls, v, info):
        geom_type = info.data.get('type')
        if geom_type == GeometryType.POLYGON and v:
            if v[0] != v[-1]:
                raise ValueError("Polygon coordinates must be closed")
        return v

    @model_validator(mode='after')
    def validate_geometry(self):
        geom_type = self.type
        coords = self.coordinates
        
        if geom_type == GeometryType.POINT:
            if not isinstance(coords, (list, tuple)) or len(coords) < 2:
                raise ValueError("Point coordinates must be [x, y] or [x, y, z]")
        elif geom_type == GeometryType.LINESTRING:
            if not isinstance(coords, list) or len(coords) < 2:
                raise ValueError("LineString must have at least 2 points")
        elif geom_type == GeometryType.POLYGON:
            if not isinstance(coords, list) or len(coords) < 1:
                raise ValueError("Polygon must have at least one ring")
        
        return self

# Base BIM Element
class BIMElementBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    description: Optional[str] = None
    geometry: Geometry
    parent_id: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0"
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("ID cannot be empty")
        return v
    
    def add_child(self, child_id: str):
        """Add a child element ID."""
        if child_id not in self.children:
            self.children.append(child_id)
            self.updated_at = datetime.now(timezone.utc)
    
    def remove_child(self, child_id: str):
        """Remove a child element ID."""
        if child_id in self.children:
            self.children.remove(child_id)
            self.updated_at = datetime.now(timezone.utc)
    
    def add_property(self, key: str, value: Any):
        """Add a property to the element."""
        self.properties[key] = value
        self.updated_at = datetime.now(timezone.utc)
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property from the element."""
        return self.properties.get(key, default)

# Spatial Elements
class Room(BIMElementBase):
    room_type: RoomType = RoomType.GENERAL
    room_number: Optional[str] = None
    floor_level: Optional[float] = None
    ceiling_height: Optional[float] = None
    area: Optional[float] = None
    volume: Optional[float] = None
    occupants: Optional[int] = None
    temperature_setpoint: Optional[float] = None
    humidity_setpoint: Optional[float] = None
    
    @field_validator('area')
    @classmethod
    def validate_area(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Area must be positive")
        return v
    
    @field_validator('volume')
    @classmethod
    def validate_volume(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Volume must be positive")
        return v

class Wall(BIMElementBase):
    wall_type: str = "interior"
    thickness: Optional[float] = None
    height: Optional[float] = None
    material: Optional[str] = None
    fire_rating: Optional[str] = None
    acoustic_rating: Optional[str] = None

class Door(BIMElementBase):
    door_type: str = "swing"
    width: Optional[float] = None
    height: Optional[float] = None
    material: Optional[str] = None
    fire_rating: Optional[str] = None
    is_automatic: bool = False
    is_emergency_exit: bool = False

class Window(BIMElementBase):
    window_type: str = "fixed"
    width: Optional[float] = None
    height: Optional[float] = None
    glazing_type: Optional[str] = None
    u_value: Optional[float] = None
    is_operable: bool = False

# HVAC System Elements
class HVACZone(BIMElementBase):
    zone_type: str = "thermal"
    temperature_setpoint: Optional[float] = None
    humidity_setpoint: Optional[float] = None
    airflow_requirement: Optional[float] = None
    heating_capacity: Optional[float] = None
    cooling_capacity: Optional[float] = None
    vav_boxes: List[str] = Field(default_factory=list)
    thermostats: List[str] = Field(default_factory=list)

class AirHandler(BIMElementBase):
    system_type: SystemType = SystemType.HVAC
    category: DeviceCategory = DeviceCategory.AHU
    capacity: Optional[float] = None
    airflow: Optional[float] = None
    efficiency: Optional[float] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[datetime] = None
    maintenance_schedule: Optional[str] = None

class VAVBox(BIMElementBase):
    system_type: SystemType = SystemType.HVAC
    category: DeviceCategory = DeviceCategory.VAV
    max_airflow: Optional[float] = None
    min_airflow: Optional[float] = None
    reheat_capacity: Optional[float] = None
    damper_type: Optional[str] = None
    controller_type: Optional[str] = None

# Electrical System Elements
class ElectricalCircuit(BIMElementBase):
    circuit_type: str = "power"
    voltage: Optional[float] = None
    amperage: Optional[float] = None
    phase: Optional[str] = None
    breaker_size: Optional[float] = None
    panel_id: Optional[str] = None
    connected_devices: List[str] = Field(default_factory=list)
    load_capacity: Optional[float] = None
    load_percentage: Optional[float] = None

class ElectricalPanel(BIMElementBase):
    system_type: SystemType = SystemType.ELECTRICAL
    category: DeviceCategory = DeviceCategory.PANEL
    panel_type: str = "distribution"
    voltage: Optional[float] = None
    amperage: Optional[float] = None
    phase: Optional[str] = None
    circuit_count: Optional[int] = None
    available_circuits: Optional[int] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None

class ElectricalOutlet(BIMElementBase):
    system_type: SystemType = SystemType.ELECTRICAL
    category: DeviceCategory = DeviceCategory.OUTLET
    outlet_type: str = "duplex"
    voltage: Optional[float] = None
    amperage: Optional[float] = None
    circuit_id: Optional[str] = None
    is_gfci: bool = False
    is_afci: bool = False
    is_emergency: bool = False

# Plumbing System Elements
class PlumbingSystem(BIMElementBase):
    system_type: SystemType = SystemType.PLUMBING
    pipe_material: Optional[str] = None
    pipe_size: Optional[str] = None
    flow_rate: Optional[float] = None
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    connected_fixtures: List[str] = Field(default_factory=list)
    valves: List[str] = Field(default_factory=list)

class PlumbingFixture(BIMElementBase):
    system_type: SystemType = SystemType.PLUMBING
    category: DeviceCategory = DeviceCategory.FIXTURE
    fixture_type: str = "sink"
    flow_rate: Optional[float] = None
    water_consumption: Optional[float] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    installation_date: Optional[datetime] = None

class Valve(BIMElementBase):
    system_type: SystemType = SystemType.PLUMBING
    category: DeviceCategory = DeviceCategory.VALVE
    valve_type: str = "ball"
    size: Optional[str] = None
    material: Optional[str] = None
    pressure_rating: Optional[float] = None
    is_automatic: bool = False
    actuator_type: Optional[str] = None

# Fire Alarm System Elements
class FireAlarmSystem(BIMElementBase):
    system_type: SystemType = SystemType.FIRE_ALARM
    panel_type: str = "conventional"
    zone_count: Optional[int] = None
    device_count: Optional[int] = None
    battery_backup: bool = True
    emergency_power: bool = True
    connected_devices: List[str] = Field(default_factory=list)

class SmokeDetector(BIMElementBase):
    system_type: SystemType = SystemType.FIRE_ALARM
    category: DeviceCategory = DeviceCategory.SMOKE_DETECTOR
    detector_type: str = "photoelectric"
    sensitivity: Optional[str] = None
    coverage_area: Optional[float] = None
    battery_type: Optional[str] = None
    last_test_date: Optional[datetime] = None
    next_test_date: Optional[datetime] = None

# Security System Elements
class SecuritySystem(BIMElementBase):
    system_type: SystemType = SystemType.SECURITY
    system_type_detail: str = "access_control"
    device_count: Optional[int] = None
    zone_count: Optional[int] = None
    recording_capacity: Optional[str] = None
    backup_power: bool = True
    connected_devices: List[str] = Field(default_factory=list)

class Camera(BIMElementBase):
    system_type: SystemType = SystemType.SECURITY
    category: DeviceCategory = DeviceCategory.CAMERA
    camera_type: str = "dome"
    resolution: Optional[str] = None
    field_of_view: Optional[float] = None
    night_vision: bool = False
    ptz_capable: bool = False
    recording_enabled: bool = True
    storage_location: Optional[str] = None

# Generic Device for other systems
class Device(BIMElementBase):
    system_type: SystemType
    category: DeviceCategory
    subtype: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    maintenance_schedule: Optional[str] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    status: str = "active"
    operational_hours: Optional[float] = None
    efficiency_rating: Optional[float] = None

# Label for annotations
class Label(BIMElementBase):
    text: str
    font_size: Optional[float] = None
    font_family: Optional[str] = None
    color: Optional[str] = None
    layer: Optional[str] = None
    rotation: Optional[float] = None
    alignment: Optional[str] = None

# Main BIM Model
class BIMModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    description: Optional[str] = None
    version: str = "1.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Spatial elements
    rooms: List[Room] = Field(default_factory=list)
    walls: List[Wall] = Field(default_factory=list)
    doors: List[Door] = Field(default_factory=list)
    windows: List[Window] = Field(default_factory=list)
    
    # System elements
    hvac_zones: List[HVACZone] = Field(default_factory=list)
    air_handlers: List[AirHandler] = Field(default_factory=list)
    vav_boxes: List[VAVBox] = Field(default_factory=list)
    
    electrical_circuits: List[ElectricalCircuit] = Field(default_factory=list)
    electrical_panels: List[ElectricalPanel] = Field(default_factory=list)
    electrical_outlets: List[ElectricalOutlet] = Field(default_factory=list)
    
    plumbing_systems: List[PlumbingSystem] = Field(default_factory=list)
    plumbing_fixtures: List[PlumbingFixture] = Field(default_factory=list)
    valves: List[Valve] = Field(default_factory=list)
    
    fire_alarm_systems: List[FireAlarmSystem] = Field(default_factory=list)
    smoke_detectors: List[SmokeDetector] = Field(default_factory=list)
    
    security_systems: List[SecuritySystem] = Field(default_factory=list)
    cameras: List[Camera] = Field(default_factory=list)
    
    # Generic devices
    devices: List[Device] = Field(default_factory=list)
    
    # Annotations
    labels: List[Label] = Field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_element(self, element: BIMElementBase):
        """Add an element to the appropriate collection based on its type."""
        if isinstance(element, Room):
            self.rooms.append(element)
        elif isinstance(element, Wall):
            self.walls.append(element)
        elif isinstance(element, Door):
            self.doors.append(element)
        elif isinstance(element, Window):
            self.windows.append(element)
        elif isinstance(element, HVACZone):
            self.hvac_zones.append(element)
        elif isinstance(element, AirHandler):
            self.air_handlers.append(element)
        elif isinstance(element, VAVBox):
            self.vav_boxes.append(element)
        elif isinstance(element, ElectricalCircuit):
            self.electrical_circuits.append(element)
        elif isinstance(element, ElectricalPanel):
            self.electrical_panels.append(element)
        elif isinstance(element, ElectricalOutlet):
            self.electrical_outlets.append(element)
        elif isinstance(element, PlumbingSystem):
            self.plumbing_systems.append(element)
        elif isinstance(element, PlumbingFixture):
            self.plumbing_fixtures.append(element)
        elif isinstance(element, Valve):
            self.valves.append(element)
        elif isinstance(element, FireAlarmSystem):
            self.fire_alarm_systems.append(element)
        elif isinstance(element, SmokeDetector):
            self.smoke_detectors.append(element)
        elif isinstance(element, SecuritySystem):
            self.security_systems.append(element)
        elif isinstance(element, Camera):
            self.cameras.append(element)
        elif isinstance(element, Device):
            self.devices.append(element)
        elif isinstance(element, Label):
            self.labels.append(element)
        
        self.updated_at = datetime.utcnow()
    
    def get_element_by_id(self, element_id: str) -> Optional[BIMElementBase]:
        """Get an element by its ID from any collection."""
        all_elements = (
            self.rooms + self.walls + self.doors + self.windows +
            self.hvac_zones + self.air_handlers + self.vav_boxes +
            self.electrical_circuits + self.electrical_panels + self.electrical_outlets +
            self.plumbing_systems + self.plumbing_fixtures + self.valves +
            self.fire_alarm_systems + self.smoke_detectors +
            self.security_systems + self.cameras +
            self.devices + self.labels
        )
        
        for element in all_elements:
            if element.id == element_id:
                return element
        return None
    
    def get_elements_by_system(self, system_type: SystemType) -> List[BIMElementBase]:
        """Get all elements of a specific system type."""
        elements = []
        
        if system_type == SystemType.HVAC:
            elements.extend(self.hvac_zones + self.air_handlers + self.vav_boxes)
        elif system_type == SystemType.ELECTRICAL:
            elements.extend(self.electrical_circuits + self.electrical_panels + self.electrical_outlets)
        elif system_type == SystemType.PLUMBING:
            elements.extend(self.plumbing_systems + self.plumbing_fixtures + self.valves)
        elif system_type == SystemType.FIRE_ALARM:
            elements.extend(self.fire_alarm_systems + self.smoke_detectors)
        elif system_type == SystemType.SECURITY:
            elements.extend(self.security_systems + self.cameras)
        
        # Also check generic devices
        for device in self.devices:
            if device.system_type == system_type:
                elements.append(device)
        
        return elements
    
    def validate_model(self) -> List[str]:
        """Validate the BIM model and return list of validation errors."""
        errors = []
        
        # Check for duplicate IDs
        all_ids = []
        all_elements = (
            self.rooms + self.walls + self.doors + self.windows +
            self.hvac_zones + self.air_handlers + self.vav_boxes +
            self.electrical_circuits + self.electrical_panels + self.electrical_outlets +
            self.plumbing_systems + self.plumbing_fixtures + self.valves +
            self.fire_alarm_systems + self.smoke_detectors +
            self.security_systems + self.cameras +
            self.devices + self.labels
        )
        
        for element in all_elements:
            if element.id in all_ids:
                errors.append(f"Duplicate ID found: {element.id}")
            all_ids.append(element.id)
        
        # Check for orphaned children
        for element in all_elements:
            for child_id in element.children:
                if not self.get_element_by_id(child_id):
                    errors.append(f"Orphaned child reference: {child_id} in {element.id}")
        
        # Check for invalid parent references
        for element in all_elements:
            if element.parent_id and not self.get_element_by_id(element.parent_id):
                errors.append(f"Invalid parent reference: {element.parent_id} in {element.id}")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the BIM model to a dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'rooms': [room.dict() for room in self.rooms],
            'walls': [wall.dict() for wall in self.walls],
            'doors': [door.dict() for door in self.doors],
            'windows': [window.dict() for window in self.windows],
            'hvac_zones': [zone.dict() for zone in self.hvac_zones],
            'air_handlers': [ahu.dict() for ahu in self.air_handlers],
            'vav_boxes': [vav.dict() for vav in self.vav_boxes],
            'electrical_circuits': [circuit.dict() for circuit in self.electrical_circuits],
            'electrical_panels': [panel.dict() for panel in self.electrical_panels],
            'electrical_outlets': [outlet.dict() for outlet in self.electrical_outlets],
            'plumbing_systems': [system.dict() for system in self.plumbing_systems],
            'plumbing_fixtures': [fixture.dict() for fixture in self.plumbing_fixtures],
            'valves': [valve.dict() for valve in self.valves],
            'fire_alarm_systems': [system.dict() for system in self.fire_alarm_systems],
            'smoke_detectors': [detector.dict() for detector in self.smoke_detectors],
            'security_systems': [system.dict() for system in self.security_systems],
            'cameras': [camera.dict() for camera in self.cameras],
            'devices': [device.dict() for device in self.devices],
            'labels': [label.dict() for label in self.labels],
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """Convert the BIM model to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BIMModel':
        """Create a BIM model from a dictionary."""
        # Handle datetime conversion
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BIMModel':
        """Create a BIM model from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

# Utility function for building BIM models
def build_bim_model(parsed_svg_elements: List[dict]) -> BIMModel:
    """
    Build a BIMModel from parsed SVG elements.
    
    Args:
        parsed_svg_elements: List of parsed SVG element dictionaries
        
    Returns:
        BIMModel: Assembled BIM model
    """
    bim_model = BIMModel()
    
    for element in parsed_svg_elements:
        # Create appropriate BIM element based on SVG element type
        if element.get('type') == 'room':
            room = Room(
                name=element.get('name'),
                geometry=Geometry(
                    type=GeometryType.POLYGON,
                    coordinates=element.get('coordinates', [])
                ),
                room_type=RoomType(element.get('room_type', 'general')),
                room_number=element.get('room_number'),
                area=element.get('area')
            )
            bim_model.add_element(room)
        
        elif element.get('type') == 'device':
            device = Device(
                name=element.get('name'),
                geometry=Geometry(
                    type=GeometryType.POINT,
                    coordinates=element.get('coordinates', [0, 0])
                ),
                system_type=SystemType(element.get('system', 'mechanical')),
                category=DeviceCategory(element.get('category', 'ahu')),
                manufacturer=element.get('manufacturer'),
                model=element.get('model')
            )
            bim_model.add_element(device)
        
        elif element.get('type') == 'wall':
            wall = Wall(
                name=element.get('name'),
                geometry=Geometry(
                    type=GeometryType.LINESTRING,
                    coordinates=element.get('coordinates', [])
                ),
                wall_type=element.get('wall_type', 'interior'),
                thickness=element.get('thickness'),
                height=element.get('height')
            )
            bim_model.add_element(wall)
    
    return bim_model 

# Generic BIM element alias for compatibility
BIMElement = BIMElementBase

# Generic BIM system container
class BIMSystem(BaseModel):
    system_id: str
    system_type: Optional[str] = None
    elements: List[str] = []
    properties: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

# Generic BIM space alias (Room is the spatial container)
BIMSpace = Room

# Generic BIM relationship model
class BIMRelationship(BaseModel):
    relationship_id: str
    relationship_type: str
    source_id: str
    target_id: str
    properties: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {} 
"""
SVGX Engine - BIM Models

This module defines the data models for Building Information Modeling (BIM)
elements and structures used in the SVGX Engine.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime

# --- Enums ---

class GeometryType(Enum):
    """Types of geometry supported in SVGX Engine."""
    POINT = "point"
    LINESTRING = "linestring"
    POLYGON = "polygon"
    MULTIPOINT = "multipoint"
    MULTILINESTRING = "multilinestring"
    MULTIPOLYGON = "multipolygon"
    GEOMETRYCOLLECTION = "geometrycollection"

class SystemType(Enum):
    """Types of BIM systems."""
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    PLUMBING = "plumbing"
    HVAC = "hvac"
    FIRE_PROTECTION = "fire_protection"
    FIRE_ALARM = "fire_alarm"
    SECURITY = "security"
    TELECOMMUNICATIONS = "telecommunications"
    STRUCTURAL = "structural"
    ARCHITECTURAL = "architectural"

class RoomType(Enum):
    """Types of rooms in BIM models."""
    OFFICE = "office"
    CONFERENCE = "conference"
    LOBBY = "lobby"
    RESTROOM = "restroom"
    KITCHEN = "kitchen"
    STORAGE = "storage"
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    CORRIDOR = "corridor"
    STAIRWELL = "stairwell"
    ELEVATOR = "elevator"
    EXIT = "exit"
    ENTRANCE = "entrance"
    OTHER = "other"

class DeviceCategory(Enum):
    """Categories of devices in BIM models."""
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    PLUMBING = "plumbing"
    HVAC = "hvac"
    FIRE_PROTECTION = "fire_protection"
    SECURITY = "security"
    TELECOMMUNICATIONS = "telecommunications"
    LIGHTING = "lighting"
    OTHER = "other"

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

class ElementCategory(Enum):
    """Categories of BIM elements."""
    HVAC = "hvac"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    FIRE_SAFETY = "fire_safety"
    SECURITY = "security"
    STRUCTURAL = "structural"
    LIGHTING = "lighting"
    OTHER = "other"

# --- Core Data Classes ---

@dataclass
class Geometry:
    """Geometry representation for BIM elements."""
    geometry_type: GeometryType
    coordinates: Union[List, List[List], List[List[List]]]
    properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        pass
    """
    Perform __post_init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __post_init__(param)
        print(result)
    """
        if not isinstance(self.coordinates, (list, tuple)):
            raise ValueError("Coordinates must be a list or tuple")
        if self.geometry_type == GeometryType.POINT:
            if len(self.coordinates) < 2:
                raise ValueError("Point geometry must have at least 2 coordinates")
        elif self.geometry_type == GeometryType.LINESTRING:
            if len(self.coordinates) < 2:
                raise ValueError("LineString geometry must have at least 2 points")
        elif self.geometry_type == GeometryType.POLYGON:
            if len(self.coordinates) < 3:
                raise ValueError("Polygon geometry must have at least 3 points")

@dataclass
class BIMElementBase:
    """Base class for all BIM elements."""
    id: str
    name: str
    geometry: Optional[Geometry] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            raise ValueError("Element ID cannot be empty")
        if not self.name:
            raise ValueError("Element name cannot be empty")

@dataclass
class BIMElement(BIMElementBase):
    """Generic BIM element."""
    element_type: str = "generic"
    system_type: Optional[SystemType] = None

    def __post_init__(self):
        super().__post_init__()
        if not self.element_type:
            raise ValueError("Element type cannot be empty")

@dataclass
class Room(BIMElementBase):
    """Room element in BIM model."""
    room_type: RoomType = RoomType.OTHER
    floor_number: Optional[int] = None
    area: Optional[float] = None
    height: Optional[float] = None
    occupancy: Optional[int] = None

    def __post_init__(self):
        super().__post_init__()
        if self.area is not None and self.area <= 0:
            raise ValueError("Room area must be positive")
        if self.height is not None and self.height <= 0:
            raise ValueError("Room height must be positive")
        if self.occupancy is not None and self.occupancy < 0:
            raise ValueError("Room occupancy cannot be negative")

@dataclass
class Wall(BIMElementBase):
    """Wall element in BIM model."""
    wall_type: str = "standard"
    thickness: Optional[float] = None
    height: Optional[float] = None
    material: Optional[str] = None
    fire_rating: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        if self.thickness is not None and self.thickness <= 0:
            raise ValueError("Wall thickness must be positive")
        if self.height is not None and self.height <= 0:
            raise ValueError("Wall height must be positive")

@dataclass
class Door(BIMElementBase):
    """Door element in BIM model."""
    door_type: str = "standard"
    width: Optional[float] = None
    height: Optional[float] = None
    material: Optional[str] = None
    fire_rating: Optional[str] = None
    swing_direction: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        if self.width is not None and self.width <= 0:
            raise ValueError("Door width must be positive")
        if self.height is not None and self.height <= 0:
            raise ValueError("Door height must be positive")

@dataclass
class Window(BIMElementBase):
    """Window element in BIM model."""
    window_type: str = "standard"
    width: Optional[float] = None
    height: Optional[float] = None
    material: Optional[str] = None
    glazing_type: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        if self.width is not None and self.width <= 0:
            raise ValueError("Window width must be positive")
        if self.height is not None and self.height <= 0:
            raise ValueError("Window height must be positive")

# --- HVACZone ---

@dataclass
class HVACZone(BIMElementBase):
    """HVAC Zone element in BIM model."

    Represents a thermal zone in an HVAC system with temperature and humidity
    setpoints, airflow requirements, and connected equipment.

    Attributes:
        temperature_setpoint: Target temperature in degrees Celsius
        humidity_setpoint: Target humidity percentage (0-100)
        airflow_requirement: Required airflow in cubic meters per second
        heating_capacity: Maximum heating capacity in watts
        cooling_capacity: Maximum cooling capacity in watts
        vav_boxes: List of VAV box IDs connected to this zone
        thermostats: List of thermostat IDs controlling this zone
        zone_type: Type of HVAC zone (e.g., "thermal", "comfort", "process")
    """
    zone_type: str = "thermal"
    temperature_setpoint: Optional[float] = None
    humidity_setpoint: Optional[float] = None
    airflow_requirement: Optional[float] = None
    heating_capacity: Optional[float] = None
    cooling_capacity: Optional[float] = None
    vav_boxes: List[str] = field(default_factory=list)
    thermostats: List[str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if self.temperature_setpoint is not None:
            if not (-50 <= self.temperature_setpoint <= 100):
                raise ValueError("Temperature setpoint must be between -50 and 100 degrees Celsius")
        if self.humidity_setpoint is not None:
            if not (0 <= self.humidity_setpoint <= 100):
                raise ValueError("Humidity setpoint must be between 0 and 100 percent")
        if self.airflow_requirement is not None:
            if self.airflow_requirement < 0:
                raise ValueError("Airflow requirement cannot be negative")
        if self.heating_capacity is not None:
            if self.heating_capacity < 0:
                raise ValueError("Heating capacity cannot be negative")
        if self.cooling_capacity is not None:
            if self.cooling_capacity < 0:
                raise ValueError("Cooling capacity cannot be negative")
def add_vav_box(self, vav_box_id: str):
        """Add a VAV box to this zone."""
        if vav_box_id not in self.vav_boxes:
            self.vav_boxes.append(vav_box_id)
            self.updated_at = datetime.now()
def remove_vav_box(self, vav_box_id: str):
        """Remove a VAV box from this zone."""
        if vav_box_id in self.vav_boxes:
            self.vav_boxes.remove(vav_box_id)
            self.updated_at = datetime.now()
def add_thermostat(self, thermostat_id: str):
        """Add a thermostat to this zone."""
        if thermostat_id not in self.thermostats:
            self.thermostats.append(thermostat_id)
            self.updated_at = datetime.now()
def remove_thermostat(self, thermostat_id: str):
        """Remove a thermostat from this zone."""
        if thermostat_id in self.thermostats:
            self.thermostats.remove(thermostat_id)
            self.updated_at = datetime.now()
def get_total_capacity(self) -> Optional[float]:
        """Get the total heating and cooling capacity."""
        total = 0.0
        if self.heating_capacity is not None:
            total += self.heating_capacity
        if self.cooling_capacity is not None:
            total += self.cooling_capacity
        return total if total > 0 else None
def is_comfort_zone(self) -> bool:
        """Check if this is a comfort zone (has temperature and humidity setpoints)."""
        return (self.temperature_setpoint is not None and self.humidity_setpoint is not None)
def get_zone_info(self) -> Dict[str, Any]:
        """Get comprehensive zone information."""
        return {
            'id': self.id,
            'name': self.name,
            'zone_type': self.zone_type,
            'temperature_setpoint': self.temperature_setpoint,
            'humidity_setpoint': self.humidity_setpoint,
            'airflow_requirement': self.airflow_requirement,
            'heating_capacity': self.heating_capacity,
            'cooling_capacity': self.cooling_capacity,
            'total_capacity': self.get_total_capacity(),
            'vav_box_count': len(self.vav_boxes),
            'thermostat_count': len(self.thermostats),
            'is_comfort_zone': self.is_comfort_zone(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# --- HVAC System Elements ---

@dataclass
class AirHandler(BIMElementBase):
    """Air Handler Unit (AHU) element in BIM model."""
    system_type: Optional[SystemType] = SystemType.HVAC
    category: Optional[DeviceCategory] = DeviceCategory.AHU
    capacity: Optional[float] = None
    airflow: Optional[float] = None
    efficiency: Optional[float] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[datetime] = None
    maintenance_schedule: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        if self.capacity is not None and self.capacity < 0:
            raise ValueError("Capacity cannot be negative")
        if self.airflow is not None and self.airflow < 0:
            raise ValueError("Airflow cannot be negative")
        if self.efficiency is not None and not (0 <= self.efficiency <= 100):
            raise ValueError("Efficiency must be between 0 and 100")

@dataclass
class VAVBox(BIMElementBase):
    """Variable Air Volume (VAV) box element in BIM model."""
    system_type: Optional[SystemType] = SystemType.HVAC
    category: Optional[DeviceCategory] = DeviceCategory.VAV
    max_airflow: Optional[float] = None
    min_airflow: Optional[float] = None
    reheat_capacity: Optional[float] = None
    damper_type: Optional[str] = None
    controller_type: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        if self.max_airflow is not None and self.max_airflow < 0:
            raise ValueError("Max airflow cannot be negative")
        if self.min_airflow is not None and self.min_airflow < 0:
            raise ValueError("Min airflow cannot be negative")
        if self.reheat_capacity is not None and self.reheat_capacity < 0:
            raise ValueError("Reheat capacity cannot be negative")

# --- Electrical System Elements ---

@dataclass
class ElectricalCircuit(BIMElementBase):
    """Electrical circuit element in BIM model."""
    circuit_type: Optional[str] = "power"
    voltage: Optional[float] = None
    amperage: Optional[float] = None
    phase: Optional[str] = None
    breaker_size: Optional[float] = None
    panel_id: Optional[str] = None
    connected_devices: List[str] = field(default_factory=list)
    load_capacity: Optional[float] = None
    load_percentage: Optional[float] = None

    def __post_init__(self):
        super().__post_init__()
        if self.voltage is not None and self.voltage <= 0:
            raise ValueError("Voltage must be positive")
        if self.amperage is not None and self.amperage <= 0:
            raise ValueError("Amperage must be positive")
        if self.breaker_size is not None and self.breaker_size <= 0:
            raise ValueError("Breaker size must be positive")
        if self.load_percentage is not None and not (0 <= self.load_percentage <= 100):
            raise ValueError("Load percentage must be between 0 and 100")

@dataclass
class ElectricalPanel(BIMElementBase):
    """Electrical panel element in BIM model."""
    system_type: Optional[SystemType] = SystemType.ELECTRICAL
    category: Optional[DeviceCategory] = DeviceCategory.PANEL
    panel_type: Optional[str] = "distribution"
    voltage: Optional[float] = None
    amperage: Optional[float] = None
    phase: Optional[str] = None
    circuit_count: Optional[int] = None
    available_circuits: Optional[int] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        if self.voltage is not None and self.voltage <= 0:
            raise ValueError("Voltage must be positive")
        if self.amperage is not None and self.amperage <= 0:
            raise ValueError("Amperage must be positive")
        if self.circuit_count is not None and self.circuit_count < 0:
            raise ValueError("Circuit count cannot be negative")
        if self.available_circuits is not None and self.available_circuits < 0:
            raise ValueError("Available circuits cannot be negative")

@dataclass
class ElectricalOutlet(BIMElementBase):
    """Electrical outlet element in BIM model."""
    system_type: Optional[SystemType] = SystemType.ELECTRICAL
    category: Optional[DeviceCategory] = DeviceCategory.OUTLET
    outlet_type: Optional[str] = "duplex"
    voltage: Optional[float] = None
    amperage: Optional[float] = None
    circuit_id: Optional[str] = None
    is_gfci: bool = False
    is_afci: bool = False
    is_emergency: bool = False

    def __post_init__(self):
        super().__post_init__()
        if self.voltage is not None and self.voltage <= 0:
            raise ValueError("Voltage must be positive")
        if self.amperage is not None and self.amperage <= 0:
            raise ValueError("Amperage must be positive")

# --- Plumbing System Elements ---

@dataclass
class PlumbingSystem(BIMElementBase):
    """Plumbing system element in BIM model."""
    system_type: Optional[SystemType] = SystemType.PLUMBING
    pipe_material: Optional[str] = None
    pipe_size: Optional[str] = None
    flow_rate: Optional[float] = None
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    connected_fixtures: List[str] = field(default_factory=list)
    valves: List[str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if self.flow_rate is not None and self.flow_rate < 0:
            raise ValueError("Flow rate cannot be negative")
        if self.pressure is not None and self.pressure < 0:
            raise ValueError("Pressure cannot be negative")

@dataclass
class PlumbingFixture(BIMElementBase):
    """Plumbing fixture element in BIM model."""
    system_type: Optional[SystemType] = SystemType.PLUMBING
    category: Optional[DeviceCategory] = DeviceCategory.FIXTURE
    fixture_type: Optional[str] = "sink"
    flow_rate: Optional[float] = None
    water_consumption: Optional[float] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    installation_date: Optional[datetime] = None

    def __post_init__(self):
        super().__post_init__()
        if self.flow_rate is not None and self.flow_rate < 0:
            raise ValueError("Flow rate cannot be negative")
        if self.water_consumption is not None and self.water_consumption < 0:
            raise ValueError("Water consumption cannot be negative")

@dataclass
class Valve(BIMElementBase):
    """Valve element in BIM model."""
    system_type: Optional[SystemType] = SystemType.PLUMBING
    category: Optional[DeviceCategory] = DeviceCategory.VALVE
    valve_type: Optional[str] = "ball"
    size: Optional[str] = None
    material: Optional[str] = None
    pressure_rating: Optional[float] = None
    is_automatic: bool = False
    actuator_type: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        if self.pressure_rating is not None and self.pressure_rating < 0:
            raise ValueError("Pressure rating cannot be negative")

# --- Fire Alarm System Elements ---

@dataclass
class FireAlarmSystem(BIMElementBase):
    """Fire alarm system element in BIM model."""
    system_type: Optional[SystemType] = SystemType.FIRE_ALARM
    panel_type: Optional[str] = "conventional"
    zone_count: Optional[int] = None
    device_count: Optional[int] = None
    battery_backup: bool = True
    emergency_power: bool = True
    connected_devices: List[str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if self.zone_count is not None and self.zone_count < 0:
            raise ValueError("Zone count cannot be negative")
        if self.device_count is not None and self.device_count < 0:
            raise ValueError("Device count cannot be negative")

@dataclass
class SmokeDetector(BIMElementBase):
    """Smoke detector element in BIM model."""
    system_type: Optional[SystemType] = SystemType.FIRE_ALARM
    category: Optional[DeviceCategory] = DeviceCategory.SMOKE_DETECTOR
    detector_type: Optional[str] = "photoelectric"
    sensitivity: Optional[str] = None
    coverage_area: Optional[float] = None
    battery_type: Optional[str] = None
    last_test_date: Optional[datetime] = None
    next_test_date: Optional[datetime] = None

    def __post_init__(self):
        super().__post_init__()
        if self.coverage_area is not None and self.coverage_area < 0:
            raise ValueError("Coverage area cannot be negative")

# --- Security System Elements ---

@dataclass
class SecuritySystem(BIMElementBase):
    """Security system element in BIM model."""
    system_type: Optional[SystemType] = SystemType.SECURITY
    system_type_detail: Optional[str] = "access_control"
    device_count: Optional[int] = None
    zone_count: Optional[int] = None
    recording_capacity: Optional[str] = None
    backup_power: bool = True
    connected_devices: List[str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        if self.device_count is not None and self.device_count < 0:
            raise ValueError("Device count cannot be negative")
        if self.zone_count is not None and self.zone_count < 0:
            raise ValueError("Zone count cannot be negative")

@dataclass
class Camera(BIMElementBase):
    """Camera element in BIM model."""
    system_type: Optional[SystemType] = SystemType.SECURITY
    category: Optional[DeviceCategory] = DeviceCategory.CAMERA
    camera_type: Optional[str] = "dome"
    resolution: Optional[str] = None
    field_of_view: Optional[float] = None
    night_vision: bool = False
    ptz_capable: bool = False
    recording_enabled: bool = True
    storage_location: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        if self.field_of_view is not None and not (0 <= self.field_of_view <= 360):
            raise ValueError("Field of view must be between 0 and 360 degrees")

# --- Generic Device for other systems ---

@dataclass
class Device(BIMElementBase):
    """Generic device element in BIM model."""
    system_type: Optional[SystemType] = None
    category: Optional[DeviceCategory] = None
    geometry: Optional[Geometry] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
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

    def __post_init__(self):
        super().__post_init__()
        if self.operational_hours is not None and self.operational_hours < 0:
            raise ValueError("Operational hours cannot be negative")
        if self.efficiency_rating is not None and not (0 <= self.efficiency_rating <= 100):
            raise ValueError("Efficiency rating must be between 0 and 100")

# --- Annotation Elements ---

@dataclass
class Label(BIMElementBase):
    """Label element for annotations in BIM model."""
    text: Optional[str] = None
    font_size: Optional[float] = None
    font_family: Optional[str] = None
    color: Optional[str] = None
    layer: Optional[str] = None
    rotation: Optional[float] = None
    alignment: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        if self.text is not None and not self.text:
            raise ValueError("Label text cannot be empty")
        if self.font_size is not None and self.font_size <= 0:
            raise ValueError("Font size must be positive")
        if self.rotation is not None and not (0 <= self.rotation <= 360):
            raise ValueError("Rotation must be between 0 and 360 degrees")

# --- BIM Model Classes ---

@dataclass
class BIMModel:
    """Main BIM model container."""
    id: str
    name: str
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    description: Optional[str] = None
    elements: List[BIMElementBase] = field(default_factory=list)
    systems: List['BIMSystem'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            raise ValueError("Model ID cannot be empty")
        if not self.name:
            raise ValueError("Model name cannot be empty")

    def add_element(self, element: BIMElementBase):
        """Add an element to the model."""
        self.elements.append(element)
        self.updated_at = datetime.now()

    def get_element_by_id(self, element_id: str) -> Optional[BIMElementBase]:
        """Get an element by its ID."""
        for element in self.elements:
            if element.id == element_id:
                return element
        return None

    def get_elements_by_type(self, element_type: str) -> List[BIMElementBase]:
        """Get all elements of a specific type."""
        return [element for element in self.elements if element.__class__.__name__ == element_type]

@dataclass
class BIMSystem:
    """BIM system container."""
    id: str
    name: str
    system_type: SystemType
    elements: List[str] = field(default_factory=list)  # List of element IDs
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            raise ValueError("System ID cannot be empty")
        if not self.name:
            raise ValueError("System name cannot be empty")

    def add_element(self, element_id: str):
        """Add an element to this system."""
        if element_id not in self.elements:
            self.elements.append(element_id)
            self.updated_at = datetime.now()

    def remove_element(self, element_id: str):
        """Remove an element from this system."""
        if element_id in self.elements:
            self.elements.remove(element_id)
            self.updated_at = datetime.now()

@dataclass
class BIMSpace:
    """BIM space container."""
    id: str
    name: str
    space_type: str = "general"
    elements: List[str] = field(default_factory=list)  # List of element IDs
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            raise ValueError("Space ID cannot be empty")
        if not self.name:
            raise ValueError("Space name cannot be empty")

    def add_element(self, element_id: str):
        """Add an element to this space."""
        if element_id not in self.elements:
            self.elements.append(element_id)
            self.updated_at = datetime.now()

    def remove_element(self, element_id: str):
        """Remove an element from this space."""
        if element_id in self.elements:
            self.elements.remove(element_id)
            self.updated_at = datetime.now()

@dataclass
class BIMRelationship:
    """BIM relationship between elements."""
    id: str
    relationship_type: str
    source_id: str
    target_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.id:
            raise ValueError("Relationship ID cannot be empty")
        if not self.relationship_type:
            raise ValueError("Relationship type cannot be empty")
        if not self.source_id:
            raise ValueError("Source ID cannot be empty")
        if not self.target_id:
            raise ValueError("Target ID cannot be empty")

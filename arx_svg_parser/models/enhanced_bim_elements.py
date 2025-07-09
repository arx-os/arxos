"""
Enhanced BIM Element Classes.

This module provides extended BIM element classes for various building systems:
- HVAC (Heating, Ventilation, Air Conditioning)
- Electrical systems
- Plumbing systems
- Fire safety systems
- Security systems
- Network/IT systems
- Structural elements
- Lighting systems
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
import uuid


class SystemType(Enum):
    """Building system types."""
    HVAC = "hvac"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    FIRE_SAFETY = "fire_safety"
    SECURITY = "security"
    NETWORK = "network"
    STRUCTURAL = "structural"
    LIGHTING = "lighting"
    MECHANICAL = "mechanical"
    CUSTOM = "custom"


class ElementCategory(Enum):
    """Element categories within systems."""
    # HVAC
    AIR_HANDLER = "air_handler"
    VAV_BOX = "vav_box"
    DUCT = "duct"
    DIFFUSER = "diffuser"
    THERMOSTAT = "thermostat"
    CHILLER = "chiller"
    BOILER = "boiler"
    COOLING_TOWER = "cooling_tower"
    HEAT_EXCHANGER = "heat_exchanger"
    
    # Electrical
    PANEL = "panel"
    CIRCUIT = "circuit"
    OUTLET = "outlet"
    SWITCH = "switch"
    LIGHTING_FIXTURE = "lighting_fixture"
    TRANSFORMER = "transformer"
    GENERATOR = "generator"
    UPS = "ups"
    
    # Plumbing
    PIPE = "pipe"
    VALVE = "valve"
    PUMP = "pump"
    TANK = "tank"
    FIXTURE = "fixture"
    DRAIN = "drain"
    VENT = "vent"
    
    # Fire Safety
    SPRINKLER = "sprinkler"
    SMOKE_DETECTOR = "smoke_detector"
    HEAT_DETECTOR = "heat_detector"
    PULL_STATION = "pull_station"
    HORN_STROBE = "horn_strobe"
    FIRE_DAMPER = "fire_damper"
    
    # Security
    CAMERA = "camera"
    ACCESS_CONTROL = "access_control"
    MOTION_DETECTOR = "motion_detector"
    DOOR_CONTACT = "door_contact"
    GLASS_BREAK = "glass_break"
    CARD_READER = "card_reader"
    
    # Network
    ROUTER = "router"
    NETWORK_SWITCH = "network_switch"
    SERVER = "server"
    ACCESS_POINT = "access_point"
    CABLE = "cable"
    PATCH_PANEL = "patch_panel"
    
    # Structural
    WALL = "wall"
    COLUMN = "column"
    BEAM = "beam"
    SLAB = "slab"
    FOUNDATION = "foundation"
    ROOF = "roof"
    
    # Lighting
    LIGHT = "light"
    EMERGENCY_LIGHT = "emergency_light"
    EXIT_SIGN = "exit_sign"
    DIMMER = "dimmer"
    SENSOR = "sensor"


class ConnectionType(Enum):
    """Types of connections between elements."""
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    HYDRAULIC = "hydraulic"
    PNEUMATIC = "pneumatic"
    DATA = "data"
    STRUCTURAL = "structural"
    SPATIAL = "spatial"


@dataclass
class Connection:
    """Connection between two elements."""
    id: str
    source_element_id: str
    target_element_id: str
    connection_type: ConnectionType
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class System:
    """Building system containing related elements."""
    id: str
    name: str
    system_type: SystemType
    description: Optional[str] = None
    elements: List[str] = field(default_factory=list)  # Element IDs
    connections: List[Connection] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class HVACElement(BaseModel):
    """HVAC system element."""
    id: str = Field(..., description="Element identifier")
    name: str = Field(..., description="Element name")
    category: ElementCategory = Field(..., description="Element category")
    system_id: str = Field(..., description="Parent system ID")
    
    # HVAC specific properties
    capacity: Optional[float] = Field(None, description="Capacity in appropriate units")
    flow_rate: Optional[float] = Field(None, description="Flow rate")
    temperature_setpoint: Optional[float] = Field(None, description="Temperature setpoint")
    pressure: Optional[float] = Field(None, description="Pressure")
    efficiency: Optional[float] = Field(None, description="Efficiency rating")
    
    # Location and geometry
    location: Dict[str, float] = Field(default_factory=dict, description="3D coordinates")
    dimensions: Dict[str, float] = Field(default_factory=dict, description="Dimensions")
    
    # Connections
    inlet_connections: List[str] = Field(default_factory=list, description="Inlet connection IDs")
    outlet_connections: List[str] = Field(default_factory=list, description="Outlet connection IDs")
    
    # Properties
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ElectricalElement(BaseModel):
    """Electrical system element."""
    id: str = Field(..., description="Element identifier")
    name: str = Field(..., description="Element name")
    category: ElementCategory = Field(..., description="Element category")
    system_id: str = Field(..., description="Parent system ID")
    
    # Electrical specific properties
    voltage: Optional[float] = Field(None, description="Voltage")
    current: Optional[float] = Field(None, description="Current")
    power: Optional[float] = Field(None, description="Power rating")
    phase: Optional[str] = Field(None, description="Phase (single, three, etc.)")
    circuit_number: Optional[str] = Field(None, description="Circuit number")
    
    # Location and geometry
    location: Dict[str, float] = Field(default_factory=dict, description="3D coordinates")
    dimensions: Dict[str, float] = Field(default_factory=dict, description="Dimensions")
    
    # Connections
    input_connections: List[str] = Field(default_factory=list, description="Input connection IDs")
    output_connections: List[str] = Field(default_factory=list, description="Output connection IDs")
    
    # Properties
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PlumbingElement(BaseModel):
    """Plumbing system element."""
    id: str = Field(..., description="Element identifier")
    name: str = Field(..., description="Element name")
    category: ElementCategory = Field(..., description="Element category")
    system_id: str = Field(..., description="Parent system ID")
    
    # Plumbing specific properties
    pipe_size: Optional[str] = Field(None, description="Pipe size")
    material: Optional[str] = Field(None, description="Material")
    flow_rate: Optional[float] = Field(None, description="Flow rate")
    pressure: Optional[float] = Field(None, description="Pressure")
    fluid_type: Optional[str] = Field(None, description="Fluid type")
    
    # Location and geometry
    location: Dict[str, float] = Field(default_factory=dict, description="3D coordinates")
    dimensions: Dict[str, float] = Field(default_factory=dict, description="Dimensions")
    
    # Connections
    inlet_connections: List[str] = Field(default_factory=list, description="Inlet connection IDs")
    outlet_connections: List[str] = Field(default_factory=list, description="Outlet connection IDs")
    
    # Properties
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class FireSafetyElement(BaseModel):
    """Fire safety system element."""
    id: str = Field(..., description="Element identifier")
    name: str = Field(..., description="Element name")
    category: ElementCategory = Field(..., description="Element category")
    system_id: str = Field(..., description="Parent system ID")
    
    # Fire safety specific properties
    coverage_area: Optional[float] = Field(None, description="Coverage area")
    activation_temperature: Optional[float] = Field(None, description="Activation temperature")
    response_time: Optional[float] = Field(None, description="Response time")
    zone: Optional[str] = Field(None, description="Fire zone")
    
    # Location and geometry
    location: Dict[str, float] = Field(default_factory=dict, description="3D coordinates")
    dimensions: Dict[str, float] = Field(default_factory=dict, description="Dimensions")
    
    # Connections
    connections: List[str] = Field(default_factory=list, description="Connection IDs")
    
    # Properties
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SecurityElement(BaseModel):
    """Security system element."""
    id: str = Field(..., description="Element identifier")
    name: str = Field(..., description="Element name")
    category: ElementCategory = Field(..., description="Element category")
    system_id: str = Field(..., description="Parent system ID")
    
    # Security specific properties
    coverage_area: Optional[float] = Field(None, description="Coverage area")
    resolution: Optional[str] = Field(None, description="Resolution (for cameras)")
    field_of_view: Optional[float] = Field(None, description="Field of view")
    access_level: Optional[str] = Field(None, description="Access level")
    
    # Location and geometry
    location: Dict[str, float] = Field(default_factory=dict, description="3D coordinates")
    dimensions: Dict[str, float] = Field(default_factory=dict, description="Dimensions")
    
    # Connections
    connections: List[str] = Field(default_factory=list, description="Connection IDs")
    
    # Properties
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class NetworkElement(BaseModel):
    """Network/IT system element."""
    id: str = Field(..., description="Element identifier")
    name: str = Field(..., description="Element name")
    category: ElementCategory = Field(..., description="Element category")
    system_id: str = Field(..., description="Parent system ID")
    
    # Network specific properties
    ip_address: Optional[str] = Field(None, description="IP address")
    mac_address: Optional[str] = Field(None, description="MAC address")
    port_count: Optional[int] = Field(None, description="Number of ports")
    bandwidth: Optional[str] = Field(None, description="Bandwidth")
    protocol: Optional[str] = Field(None, description="Network protocol")
    
    # Location and geometry
    location: Dict[str, float] = Field(default_factory=dict, description="3D coordinates")
    dimensions: Dict[str, float] = Field(default_factory=dict, description="Dimensions")
    
    # Connections
    connections: List[str] = Field(default_factory=list, description="Connection IDs")
    
    # Properties
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class StructuralElement(BaseModel):
    """Structural system element."""
    id: str = Field(..., description="Element identifier")
    name: str = Field(..., description="Element name")
    category: ElementCategory = Field(..., description="Element category")
    system_id: str = Field(..., description="Parent system ID")
    
    # Structural specific properties
    material: Optional[str] = Field(None, description="Material")
    load_capacity: Optional[float] = Field(None, description="Load capacity")
    fire_rating: Optional[str] = Field(None, description="Fire rating")
    seismic_rating: Optional[str] = Field(None, description="Seismic rating")
    
    # Location and geometry
    location: Dict[str, float] = Field(default_factory=dict, description="3D coordinates")
    dimensions: Dict[str, float] = Field(default_factory=dict, description="Dimensions")
    
    # Connections
    connections: List[str] = Field(default_factory=list, description="Connection IDs")
    
    # Properties
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class LightingElement(BaseModel):
    """Lighting system element."""
    id: str = Field(..., description="Element identifier")
    name: str = Field(..., description="Element name")
    category: ElementCategory = Field(..., description="Element category")
    system_id: str = Field(..., description="Parent system ID")
    
    # Lighting specific properties
    wattage: Optional[float] = Field(None, description="Wattage")
    lumens: Optional[float] = Field(None, description="Lumens")
    color_temperature: Optional[float] = Field(None, description="Color temperature")
    cri: Optional[float] = Field(None, description="Color rendering index")
    emergency_backup: Optional[bool] = Field(None, description="Emergency backup")
    
    # Location and geometry
    location: Dict[str, float] = Field(default_factory=dict, description="3D coordinates")
    dimensions: Dict[str, float] = Field(default_factory=dict, description="Dimensions")
    
    # Connections
    connections: List[str] = Field(default_factory=list, description="Connection IDs")
    
    # Properties
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class EnhancedBIMModel(BaseModel):
    """Enhanced BIM model with multiple building systems."""
    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Model name")
    description: Optional[str] = Field(None, description="Model description")
    
    # Systems
    hvac_systems: List[System] = Field(default_factory=list, description="HVAC systems")
    electrical_systems: List[System] = Field(default_factory=list, description="Electrical systems")
    plumbing_systems: List[System] = Field(default_factory=list, description="Plumbing systems")
    fire_safety_systems: List[System] = Field(default_factory=list, description="Fire safety systems")
    security_systems: List[System] = Field(default_factory=list, description="Security systems")
    network_systems: List[System] = Field(default_factory=list, description="Network systems")
    structural_systems: List[System] = Field(default_factory=list, description="Structural systems")
    lighting_systems: List[System] = Field(default_factory=list, description="Lighting systems")
    
    # Elements by type
    hvac_elements: List[HVACElement] = Field(default_factory=list, description="HVAC elements")
    electrical_elements: List[ElectricalElement] = Field(default_factory=list, description="Electrical elements")
    plumbing_elements: List[PlumbingElement] = Field(default_factory=list, description="Plumbing elements")
    fire_safety_elements: List[FireSafetyElement] = Field(default_factory=list, description="Fire safety elements")
    security_elements: List[SecurityElement] = Field(default_factory=list, description="Security elements")
    network_elements: List[NetworkElement] = Field(default_factory=list, description="Network elements")
    structural_elements: List[StructuralElement] = Field(default_factory=list, description="Structural elements")
    lighting_elements: List[LightingElement] = Field(default_factory=list, description="Lighting elements")
    
    # Connections
    connections: List[Connection] = Field(default_factory=list, description="All connections")
    
    # Properties
    properties: Dict[str, Any] = Field(default_factory=dict, description="Model properties")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Model metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def get_all_systems(self) -> List[System]:
        """Get all systems in the model."""
        all_systems = []
        all_systems.extend(self.hvac_systems)
        all_systems.extend(self.electrical_systems)
        all_systems.extend(self.plumbing_systems)
        all_systems.extend(self.fire_safety_systems)
        all_systems.extend(self.security_systems)
        all_systems.extend(self.network_systems)
        all_systems.extend(self.structural_systems)
        all_systems.extend(self.lighting_systems)
        return all_systems
    
    def get_system_by_id(self, system_id: str) -> Optional[System]:
        """Get a system by ID."""
        for system in self.get_all_systems():
            if system.id == system_id:
                return system
        return None
    
    def get_elements_by_system(self, system_id: str) -> List[Any]:
        """Get all elements belonging to a system."""
        elements = []
        
        # Check each element type
        for element in self.hvac_elements:
            if element.system_id == system_id:
                elements.append(element)
        
        for element in self.electrical_elements:
            if element.system_id == system_id:
                elements.append(element)
        
        for element in self.plumbing_elements:
            if element.system_id == system_id:
                elements.append(element)
        
        for element in self.fire_safety_elements:
            if element.system_id == system_id:
                elements.append(element)
        
        for element in self.security_elements:
            if element.system_id == system_id:
                elements.append(element)
        
        for element in self.network_elements:
            if element.system_id == system_id:
                elements.append(element)
        
        for element in self.structural_elements:
            if element.system_id == system_id:
                elements.append(element)
        
        for element in self.lighting_elements:
            if element.system_id == system_id:
                elements.append(element)
        
        return elements
    
    def get_element_by_id(self, element_id: str) -> Optional[Any]:
        """Get an element by ID."""
        # Check each element type
        for element in self.hvac_elements:
            if element.id == element_id:
                return element
        
        for element in self.electrical_elements:
            if element.id == element_id:
                return element
        
        for element in self.plumbing_elements:
            if element.id == element_id:
                return element
        
        for element in self.fire_safety_elements:
            if element.id == element_id:
                return element
        
        for element in self.security_elements:
            if element.id == element_id:
                return element
        
        for element in self.network_elements:
            if element.id == element_id:
                return element
        
        for element in self.structural_elements:
            if element.id == element_id:
                return element
        
        for element in self.lighting_elements:
            if element.id == element_id:
                return element
        
        return None
    
    def add_hvac_element(self, element: HVACElement) -> bool:
        """Add an HVAC element to the model."""
        try:
            self.hvac_elements.append(element)
            self.updated_at = datetime.now()
            return True
        except Exception:
            return False
    
    def add_electrical_element(self, element: ElectricalElement) -> bool:
        """Add an electrical element to the model."""
        try:
            self.electrical_elements.append(element)
            self.updated_at = datetime.now()
            return True
        except Exception:
            return False
    
    def add_plumbing_element(self, element: PlumbingElement) -> bool:
        """Add a plumbing element to the model."""
        try:
            self.plumbing_elements.append(element)
            self.updated_at = datetime.now()
            return True
        except Exception:
            return False
    
    def add_fire_safety_element(self, element: FireSafetyElement) -> bool:
        """Add a fire safety element to the model."""
        try:
            self.fire_safety_elements.append(element)
            self.updated_at = datetime.now()
            return True
        except Exception:
            return False
    
    def add_security_element(self, element: SecurityElement) -> bool:
        """Add a security element to the model."""
        try:
            self.security_elements.append(element)
            self.updated_at = datetime.now()
            return True
        except Exception:
            return False
    
    def add_network_element(self, element: NetworkElement) -> bool:
        """Add a network element to the model."""
        try:
            self.network_elements.append(element)
            self.updated_at = datetime.now()
            return True
        except Exception:
            return False
    
    def add_structural_element(self, element: StructuralElement) -> bool:
        """Add a structural element to the model."""
        try:
            self.structural_elements.append(element)
            self.updated_at = datetime.now()
            return True
        except Exception:
            return False
    
    def add_lighting_element(self, element: LightingElement) -> bool:
        """Add a lighting element to the model."""
        try:
            self.lighting_elements.append(element)
            self.updated_at = datetime.now()
            return True
        except Exception:
            return False
    
    def add_system(self, system: System) -> bool:
        """Add a system to the model."""
        try:
            if system.system_type == SystemType.HVAC:
                self.hvac_systems.append(system)
            elif system.system_type == SystemType.ELECTRICAL:
                self.electrical_systems.append(system)
            elif system.system_type == SystemType.PLUMBING:
                self.plumbing_systems.append(system)
            elif system.system_type == SystemType.FIRE_SAFETY:
                self.fire_safety_systems.append(system)
            elif system.system_type == SystemType.SECURITY:
                self.security_systems.append(system)
            elif system.system_type == SystemType.NETWORK:
                self.network_systems.append(system)
            elif system.system_type == SystemType.STRUCTURAL:
                self.structural_systems.append(system)
            elif system.system_type == SystemType.LIGHTING:
                self.lighting_systems.append(system)
            
            self.updated_at = datetime.now()
            return True
        except Exception:
            return False
    
    def add_connection(self, connection: Connection) -> bool:
        """Add a connection to the model."""
        try:
            self.connections.append(connection)
            self.updated_at = datetime.now()
            return True
        except Exception:
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get model statistics."""
        return {
            "total_systems": len(self.get_all_systems()),
            "total_elements": (
                len(self.hvac_elements) +
                len(self.electrical_elements) +
                len(self.plumbing_elements) +
                len(self.fire_safety_elements) +
                len(self.security_elements) +
                len(self.network_elements) +
                len(self.structural_elements) +
                len(self.lighting_elements)
            ),
            "total_connections": len(self.connections),
            "system_counts": {
                "hvac": len(self.hvac_systems),
                "electrical": len(self.electrical_systems),
                "plumbing": len(self.plumbing_systems),
                "fire_safety": len(self.fire_safety_systems),
                "security": len(self.security_systems),
                "network": len(self.network_systems),
                "structural": len(self.structural_systems),
                "lighting": len(self.lighting_systems)
            },
            "element_counts": {
                "hvac": len(self.hvac_elements),
                "electrical": len(self.electrical_elements),
                "plumbing": len(self.plumbing_elements),
                "fire_safety": len(self.fire_safety_elements),
                "security": len(self.security_elements),
                "network": len(self.network_elements),
                "structural": len(self.structural_elements),
                "lighting": len(self.lighting_elements)
            }
        }


def create_element_id() -> str:
    """Create a unique element ID."""
    return str(uuid.uuid4())


def create_system_id() -> str:
    """Create a unique system ID."""
    return str(uuid.uuid4())


def create_connection_id() -> str:
    """Create a unique connection ID."""
    return str(uuid.uuid4()) 
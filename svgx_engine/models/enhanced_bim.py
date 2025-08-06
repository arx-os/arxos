"""
SVGX Engine - Enhanced BIM Models

This module defines enhanced Building Information Modeling (BIM) data models
that transform SVGX elements into comprehensive building information systems.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union, Tuple
from enum import Enum
from datetime import datetime
import uuid
import json

# --- Enhanced BIM Enums ---


class BIMElementType(Enum):
    """Enhanced BIM element types for comprehensive building modeling."""

    # Spatial Elements
    BUILDING = "building"
    FLOOR = "floor"
    ROOM = "room"
    ZONE = "zone"
    SPACE = "space"
    CORRIDOR = "corridor"
    STAIRWELL = "stairwell"
    ELEVATOR_SHAFT = "elevator_shaft"

    # Enclosure Elements
    WALL = "wall"
    DOOR = "door"
    WINDOW = "window"
    ROOF = "roof"
    FLOOR_SLAB = "floor_slab"
    CEILING = "ceiling"
    PARTITION = "partition"

    # MEP Systems
    HVAC_ZONE = "hvac_zone"
    AIR_HANDLER = "air_handler"
    VAV_BOX = "vav_box"
    DUCT = "duct"
    DIFFUSER = "diffuser"
    THERMOSTAT = "thermostat"

    ELECTRICAL_PANEL = "electrical_panel"
    ELECTRICAL_CIRCUIT = "electrical_circuit"
    ELECTRICAL_OUTLET = "electrical_outlet"
    LIGHTING_FIXTURE = "lighting_fixture"
    SWITCH = "switch"

    PLUMBING_PIPE = "plumbing_pipe"
    PLUMBING_FIXTURE = "plumbing_fixture"
    VALVE = "valve"
    PUMP = "pump"
    WATER_HEATER = "water_heater"

    FIRE_ALARM_PANEL = "fire_alarm_panel"
    SMOKE_DETECTOR = "smoke_detector"
    FIRE_SPRINKLER = "fire_sprinkler"
    PULL_STATION = "pull_station"

    SECURITY_CAMERA = "security_camera"
    ACCESS_CONTROL = "access_control"
    CARD_READER = "card_reader"

    # Structural Elements
    COLUMN = "column"
    BEAM = "beam"
    TRUSS = "truss"
    FOUNDATION = "foundation"

    # Equipment
    EQUIPMENT = "equipment"
    FURNITURE = "furniture"
    FIXTURE = "fixture"


class BIMSystemType(Enum):
    """Enhanced BIM system types for comprehensive system modeling."""

    # Building Systems
    STRUCTURAL = "structural"
    ARCHITECTURAL = "architectural"
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    FIRE_PROTECTION = "fire_protection"
    SECURITY = "security"
    COMMUNICATIONS = "communications"

    # Specialized Systems
    HVAC = "hvac"
    LIGHTING = "lighting"
    POWER = "power"
    WATER = "water"
    SEWAGE = "sewage"
    GAS = "gas"
    VENTILATION = "ventilation"
    AIR_CONDITIONING = "air_conditioning"
    HEATING = "heating"
    COOLING = "cooling"

    # Industrial Systems
    PROCESS_CONTROL = "process_control"
    MATERIAL_HANDLING = "material_handling"
    QUALITY_CONTROL = "quality_control"
    SAFETY_SYSTEMS = "safety_systems"


class BIMPropertyType(Enum):
    """Enhanced BIM property types for comprehensive data modeling."""

    # Physical Properties
    DIMENSIONS = "dimensions"
    AREA = "area"
    VOLUME = "volume"
    WEIGHT = "weight"
    MATERIAL = "material"
    COLOR = "color"
    TEXTURE = "texture"

    # Performance Properties
    CAPACITY = "capacity"
    EFFICIENCY = "efficiency"
    POWER_CONSUMPTION = "power_consumption"
    FLOW_RATE = "flow_rate"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"

    # Operational Properties
    OPERATING_HOURS = "operating_hours"
    MAINTENANCE_SCHEDULE = "maintenance_schedule"
    LIFESPAN = "lifespan"
    WARRANTY = "warranty"
    MANUFACTURER = "manufacturer"
    MODEL_NUMBER = "model_number"
    SERIAL_NUMBER = "serial_number"

    # Financial Properties
    COST = "cost"
    REPLACEMENT_COST = "replacement_cost"
    DEPRECIATION = "depreciation"
    INSURANCE_VALUE = "insurance_value"

    # Compliance Properties
    CODE_COMPLIANCE = "code_compliance"
    CERTIFICATION = "certification"
    INSPECTION_DATE = "inspection_date"
    PERMIT_NUMBER = "permit_number"


class BIMRelationshipType(Enum):
    """Enhanced BIM relationship types for comprehensive relationship modeling."""

    # Spatial Relationships
    CONTAINS = "contains"
    IS_CONTAINED_BY = "is_contained_by"
    ADJACENT_TO = "adjacent_to"
    ABOVE = "above"
    BELOW = "below"
    NORTH_OF = "north_of"
    SOUTH_OF = "south_of"
    EAST_OF = "east_of"
    WEST_OF = "west_of"

    # System Relationships
    SUPPLIES = "supplies"
    IS_SUPPLIED_BY = "is_supplied_by"
    CONTROLS = "controls"
    IS_CONTROLLED_BY = "is_controlled_by"
    MONITORS = "monitors"
    IS_MONITORED_BY = "is_monitored_by"
    CONNECTS_TO = "connects_to"
    IS_CONNECTED_TO = "is_connected_to"

    # Functional Relationships
    DEPENDS_ON = "depends_on"
    IS_DEPENDENT_ON = "is_dependent_on"
    REPLACES = "replaces"
    IS_REPLACED_BY = "is_replaced_by"
    MAINTAINS = "maintains"
    IS_MAINTAINED_BY = "is_maintained_by"


# --- Enhanced BIM Data Classes ---


@dataclass
class BIMProperty:
    """Enhanced BIM property with comprehensive data modeling."""

    id: str
    name: str
    value: Any
    unit: Optional[str] = None
    data_type: str = "string"
    description: Optional[str] = None
    source: Optional[str] = None
    confidence: float = 1.0
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "data_type": self.data_type,
            "description": self.description,
            "source": self.source,
            "confidence": self.confidence,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class BIMPropertySet:
    """Enhanced BIM property set for comprehensive data organization."""

    id: str
    name: str
    description: Optional[str] = None
    properties: Dict[str, BIMProperty] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_property(self, property_obj: BIMProperty):
        """Add a property to the property set."""
        self.properties[property_obj.id] = property_obj
        self.updated_at = datetime.now()

    def get_property(self, property_id: str) -> Optional[BIMProperty]:
        """Get a property by ID."""
        return self.properties.get(property_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "properties": {k: v.to_dict() for k, v in self.properties.items()},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class BIMRelationship:
    """Enhanced BIM relationship with comprehensive relationship modeling."""

    id: str
    source_element_id: str
    target_element_id: str
    relationship_type: BIMRelationshipType
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "source_element_id": self.source_element_id,
            "target_element_id": self.target_element_id,
            "relationship_type": self.relationship_type.value,
            "properties": self.properties,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class EnhancedBIMElement:
    """Enhanced BIM element with comprehensive building information modeling."""

    id: str
    name: str
    element_type: BIMElementType
    system_type: BIMSystemType
    geometry: Optional[Dict[str, Any]] = None
    properties: Dict[str, BIMPropertySet] = field(default_factory=dict)
    relationships: List[BIMRelationship] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_property_set(self, property_set: BIMPropertySet):
        """Add a property set to the element."""
        self.properties[property_set.id] = property_set
        self.updated_at = datetime.now()

    def add_relationship(self, relationship: BIMRelationship):
        """Add a relationship to the element."""
        self.relationships.append(relationship)
        self.updated_at = datetime.now()

    def get_property_value(
        self, property_set_id: str, property_id: str
    ) -> Optional[Any]:
        """Get a property value by property set and property IDs."""
        property_set = self.properties.get(property_set_id)
        if property_set:
            property_obj = property_set.get_property(property_id)
            return property_obj.value if property_obj else None
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "element_type": self.element_type.value,
            "system_type": self.system_type.value,
            "geometry": self.geometry,
            "properties": {k: v.to_dict() for k, v in self.properties.items()},
            "relationships": [r.to_dict() for r in self.relationships],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class EnhancedBIMModel:
    """Enhanced BIM model with comprehensive building information modeling."""

    id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    elements: Dict[str, EnhancedBIMElement] = field(default_factory=dict)
    systems: Dict[str, Dict[str, EnhancedBIMElement]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_element(self, element: EnhancedBIMElement):
        """Add an element to the model."""
        self.elements[element.id] = element
        self.updated_at = datetime.now()

        # Add to system grouping
        system_type = element.system_type.value
        if system_type not in self.systems:
            self.systems[system_type] = {}
        self.systems[system_type][element.id] = element

    def get_element(self, element_id: str) -> Optional[EnhancedBIMElement]:
        """Get an element by ID."""
        return self.elements.get(element_id)

    def get_elements_by_type(
        self, element_type: BIMElementType
    ) -> List[EnhancedBIMElement]:
        """Get all elements of a specific type."""
        return [
            elem for elem in self.elements.values() if elem.element_type == element_type
        ]

    def get_elements_by_system(
        self, system_type: BIMSystemType
    ) -> List[EnhancedBIMElement]:
        """Get all elements of a specific system type."""
        return [
            elem for elem in self.elements.values() if elem.system_type == system_type
        ]

    def get_relationships(self, element_id: str) -> List[BIMRelationship]:
        """Get all relationships for a specific element."""
        element = self.get_element(element_id)
        return element.relationships if element else []

    def validate_model(self) -> List[str]:
        """Validate the BIM model and return any issues."""
        issues = []

        # Check for orphaned elements (no relationships)
        for element_id, element in self.elements.items():
            if not element.relationships:
                issues.append(f"Element {element_id} has no relationships")

        # Check for invalid relationships
        for element_id, element in self.elements.items():
            for relationship in element.relationships:
                if relationship.source_element_id not in self.elements:
                    issues.append(
                        f"Relationship {relationship.id} references non-existent source element {relationship.source_element_id}"
                    )
                if relationship.target_element_id not in self.elements:
                    issues.append(
                        f"Relationship {relationship.id} references non-existent target element {relationship.target_element_id}"
                    )

        return issues

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "elements": {k: v.to_dict() for k, v in self.elements.items()},
            "systems": {
                k: {ek: ev.to_dict() for ek, ev in v.items()}
                for k, v in self.systems.items()
            },
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# --- BIM Transformation Utilities ---


class BIMTransformer:
    """Utility class for transforming SVGX elements to enhanced BIM models."""

    @staticmethod
    def svgx_to_bim_element(svgx_element: Dict[str, Any]) -> EnhancedBIMElement:
        """Transform an SVGX element to an enhanced BIM element."""
        element_id = svgx_element.get("id", str(uuid.uuid4()))
        name = svgx_element.get("name", f"Element_{element_id}")

        # Determine element type from SVGX attributes
        element_type = BIMTransformer._determine_element_type(svgx_element)
        system_type = BIMTransformer._determine_system_type(svgx_element)

        # Extract geometry
        geometry = svgx_element.get("geometry", {})

        # Create property sets from SVGX attributes
        properties = BIMTransformer._extract_properties(svgx_element)

        # Create relationships from SVGX connections
        relationships = BIMTransformer._extract_relationships(svgx_element)

        return EnhancedBIMElement(
            id=element_id,
            name=name,
            element_type=element_type,
            system_type=system_type,
            geometry=geometry,
            properties=properties,
            relationships=relationships,
            metadata=svgx_element.get("metadata", {}),
        )

    @staticmethod
    def _determine_element_type(svgx_element: Dict[str, Any]) -> BIMElementType:
        """Determine BIM element type from SVGX element."""
        element_type = svgx_element.get("type", "unknown").lower()

        # Map SVGX types to BIM element types
        type_mapping = {
            "room": BIMElementType.ROOM,
            "wall": BIMElementType.WALL,
            "door": BIMElementType.DOOR,
            "window": BIMElementType.WINDOW,
            "hvac": BIMElementType.HVAC_ZONE,
            "electrical": BIMElementType.ELECTRICAL_PANEL,
            "plumbing": BIMElementType.PLUMBING_PIPE,
            "fire_alarm": BIMElementType.FIRE_ALARM_PANEL,
            "security": BIMElementType.SECURITY_CAMERA,
            "equipment": BIMElementType.EQUIPMENT,
            "furniture": BIMElementType.FURNITURE,
            "fixture": BIMElementType.FIXTURE,
        }

        return type_mapping.get(element_type, BIMElementType.EQUIPMENT)

    @staticmethod
    def _determine_system_type(svgx_element: Dict[str, Any]) -> BIMSystemType:
        """Determine BIM system type from SVGX element."""
        system = svgx_element.get("system", "unknown").lower()

        # Map SVGX systems to BIM system types
        system_mapping = {
            "hvac": BIMSystemType.HVAC,
            "electrical": BIMSystemType.ELECTRICAL,
            "plumbing": BIMSystemType.PLUMBING,
            "fire_protection": BIMSystemType.FIRE_PROTECTION,
            "security": BIMSystemType.SECURITY,
            "structural": BIMSystemType.STRUCTURAL,
            "architectural": BIMSystemType.ARCHITECTURAL,
            "mechanical": BIMSystemType.MECHANICAL,
        }

        return system_mapping.get(system, BIMSystemType.ARCHITECTURAL)

    @staticmethod
    def _extract_properties(svgx_element: Dict[str, Any]) -> Dict[str, BIMPropertySet]:
        """Extract properties from SVGX element."""
        properties = {}

        # Create physical properties
        physical_props = BIMPropertySet(
            id="physical_properties",
            name="Physical Properties",
            description="Physical characteristics of the element",
        )

        # Add dimensions if available
        if "width" in svgx_element:
            physical_props.add_property(
                BIMProperty(
                    id="width",
                    name="Width",
                    value=svgx_element["width"],
                    unit="mm",
                    data_type="float",
                )
            )

        if "height" in svgx_element:
            physical_props.add_property(
                BIMProperty(
                    id="height",
                    name="Height",
                    value=svgx_element["height"],
                    unit="mm",
                    data_type="float",
                )
            )

        if "depth" in svgx_element:
            physical_props.add_property(
                BIMProperty(
                    id="depth",
                    name="Depth",
                    value=svgx_element["depth"],
                    unit="mm",
                    data_type="float",
                )
            )

        if physical_props.properties:
            properties["physical_properties"] = physical_props

        # Create performance properties
        performance_props = BIMPropertySet(
            id="performance_properties",
            name="Performance Properties",
            description="Performance characteristics of the element",
        )

        # Add performance properties if available
        if "capacity" in svgx_element:
            performance_props.add_property(
                BIMProperty(
                    id="capacity",
                    name="Capacity",
                    value=svgx_element["capacity"],
                    unit=svgx_element.get("capacity_unit", ""),
                    data_type="float",
                )
            )

        if "efficiency" in svgx_element:
            performance_props.add_property(
                BIMProperty(
                    id="efficiency",
                    name="Efficiency",
                    value=svgx_element["efficiency"],
                    unit="%",
                    data_type="float",
                )
            )

        if performance_props.properties:
            properties["performance_properties"] = performance_props

        return properties

    @staticmethod
    def _extract_relationships(svgx_element: Dict[str, Any]) -> List[BIMRelationship]:
        """Extract relationships from SVGX element."""
        relationships = []
        element_id = svgx_element.get("id", "")

        # Extract connections
        connections = svgx_element.get("connections", [])
        for connection in connections:
            target_id = connection.get("target_id")
            if target_id:
                relationship = BIMRelationship(
                    id=f"rel_{element_id}_{target_id}",
                    source_element_id=element_id,
                    target_element_id=target_id,
                    relationship_type=BIMRelationshipType.CONNECTS_TO,
                    properties=connection.get("properties", {}),
                    confidence=connection.get("confidence", 1.0),
                )
                relationships.append(relationship)

        return relationships


# --- BIM Analysis Utilities ---


class BIMAnalyzer:
    """Utility class for analyzing enhanced BIM models."""

    @staticmethod
    def analyze_spatial_hierarchy(bim_model: EnhancedBIMModel) -> Dict[str, Any]:
        """Analyze the spatial hierarchy of the BIM model."""
        spatial_elements = {}

        # Group elements by spatial type
        for element in bim_model.elements.values():
            if element.element_type in [
                BIMElementType.BUILDING,
                BIMElementType.FLOOR,
                BIMElementType.ROOM,
                BIMElementType.ZONE,
                BIMElementType.SPACE,
            ]:
                spatial_elements[element.element_type.value] = spatial_elements.get(
                    element.element_type.value, []
                )
                spatial_elements[element.element_type.value].append(element)

        return {
            "spatial_hierarchy": spatial_elements,
            "total_spatial_elements": len(spatial_elements),
            "hierarchy_levels": list(spatial_elements.keys()),
        }

    @staticmethod
    def analyze_system_distribution(bim_model: EnhancedBIMModel) -> Dict[str, Any]:
        """Analyze the distribution of systems in the BIM model."""
        system_distribution = {}

        for element in bim_model.elements.values():
            system_type = element.system_type.value
            if system_type not in system_distribution:
                system_distribution[system_type] = []
            system_distribution[system_type].append(element)

        return {
            "system_distribution": system_distribution,
            "total_systems": len(system_distribution),
            "system_counts": {k: len(v) for k, v in system_distribution.items()},
        }

    @staticmethod
    def analyze_relationships(bim_model: EnhancedBIMModel) -> Dict[str, Any]:
        """Analyze the relationships in the BIM model."""
        relationship_types = {}
        total_relationships = 0

        for element in bim_model.elements.values():
            for relationship in element.relationships:
                rel_type = relationship.relationship_type.value
                if rel_type not in relationship_types:
                    relationship_types[rel_type] = 0
                relationship_types[rel_type] += 1
                total_relationships += 1

        return {
            "relationship_types": relationship_types,
            "total_relationships": total_relationships,
            "average_relationships_per_element": (
                total_relationships / len(bim_model.elements)
                if bim_model.elements
                else 0
            ),
        }

    @staticmethod
    def generate_bim_report(bim_model: EnhancedBIMModel) -> Dict[str, Any]:
        """Generate a comprehensive BIM analysis report."""
        spatial_analysis = BIMAnalyzer.analyze_spatial_hierarchy(bim_model)
        system_analysis = BIMAnalyzer.analyze_system_distribution(bim_model)
        relationship_analysis = BIMAnalyzer.analyze_relationships(bim_model)

        return {
            "model_info": {
                "id": bim_model.id,
                "name": bim_model.name,
                "version": bim_model.version,
                "total_elements": len(bim_model.elements),
                "total_systems": len(bim_model.systems),
            },
            "spatial_analysis": spatial_analysis,
            "system_analysis": system_analysis,
            "relationship_analysis": relationship_analysis,
            "validation_issues": bim_model.validate_model(),
            "report_generated": datetime.now().isoformat(),
        }

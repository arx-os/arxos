"""
SVGX Symbol Models

This module defines the data models for SVGX symbols, including metadata,
geometry, behavior, and validation components.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class SymbolType(Enum):
    """Enumeration of symbol types."""

    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    PLUMBING = "plumbing"
    HVAC = "hvac"
    STRUCTURAL = "structural"
    ARCHITECTURAL = "architectural"
    FURNITURE = "furniture"
    EQUIPMENT = "equipment"
    ANNOTATION = "annotation"
    CUSTOM = "custom"


class SymbolCategory(Enum):
    """Enumeration of symbol categories."""

    FIXTURE = "fixture"
    DEVICE = "device"
    EQUIPMENT = "equipment"
    CONNECTOR = "connector"
    TERMINAL = "terminal"
    SWITCH = "switch"
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    CONTROLLER = "controller"
    GENERATOR = "generator"
    STORAGE = "storage"
    DISTRIBUTION = "distribution"
    PROTECTION = "protection"
    MEASUREMENT = "measurement"
    INDICATOR = "indicator"
    CUSTOM = "custom"


@dataclass
class SVGXSymbolMetadata:
    """Metadata for SVGX symbols."""

    # Basic Information
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    author: Optional[str] = None
    created_date: datetime = field(default_factory=datetime.now)
    modified_date: datetime = field(default_factory=datetime.now)

    # Classification
    symbol_type: SymbolType = SymbolType.CUSTOM
    category: SymbolCategory = SymbolCategory.CUSTOM
    tags: List[str] = field(default_factory=list)

    # Technical Information
    precision: str = "1mm"
    units: str = "mm"
    scale_factor: float = 1.0

    # Validation
    validation_schema: Optional[str] = None
    required_attributes: List[str] = field(default_factory=list)
    optional_attributes: List[str] = field(default_factory=list)

    # Documentation
    documentation_url: Optional[str] = None
    examples: List[str] = field(default_factory=list)

    # Usage Statistics
    usage_count: int = 0
    rating: float = 0.0
    reviews: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "created_date": self.created_date.isoformat(),
            "modified_date": self.modified_date.isoformat(),
            "symbol_type": self.symbol_type.value,
            "category": self.category.value,
            "tags": self.tags,
            "precision": self.precision,
            "units": self.units,
            "scale_factor": self.scale_factor,
            "validation_schema": self.validation_schema,
            "required_attributes": self.required_attributes,
            "optional_attributes": self.optional_attributes,
            "documentation_url": self.documentation_url,
            "examples": self.examples,
            "usage_count": self.usage_count,
            "rating": self.rating,
            "reviews": self.reviews,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SVGXSymbolMetadata":
        """Create metadata from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description"),
            version=data.get("version", "1.0.0"),
            author=data.get("author"),
            created_date=datetime.fromisoformat(data["created_date"]),
            modified_date=datetime.fromisoformat(data["modified_date"]),
            symbol_type=SymbolType(data["symbol_type"]),
            category=SymbolCategory(data["category"]),
            tags=data.get("tags", []),
            precision=data.get("precision", "1mm"),
            units=data.get("units", "mm"),
            scale_factor=data.get("scale_factor", 1.0),
            validation_schema=data.get("validation_schema"),
            required_attributes=data.get("required_attributes", []),
            optional_attributes=data.get("optional_attributes", []),
            documentation_url=data.get("documentation_url"),
            examples=data.get("examples", []),
            usage_count=data.get("usage_count", 0),
            rating=data.get("rating", 0.0),
            reviews=data.get("reviews", []),
        )


@dataclass
class SVGXSymbolGeometry:
    """Geometry information for SVGX symbols."""

    # Basic Geometry
    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0

    # Position
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # Rotation
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0

    # Scale
    scale_x: float = 1.0
    scale_y: float = 1.0
    scale_z: float = 1.0

    # Path Data
    path_data: Optional[str] = None

    # Bounding Box
    min_x: float = 0.0
    min_y: float = 0.0
    min_z: float = 0.0
    max_x: float = 0.0
    max_y: float = 0.0
    max_z: float = 0.0

    # Connection Points
    connection_points: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert geometry to dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "depth": self.depth,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "rotation_x": self.rotation_x,
            "rotation_y": self.rotation_y,
            "rotation_z": self.rotation_z,
            "scale_x": self.scale_x,
            "scale_y": self.scale_y,
            "scale_z": self.scale_z,
            "path_data": self.path_data,
            "min_x": self.min_x,
            "min_y": self.min_y,
            "min_z": self.min_z,
            "max_x": self.max_x,
            "max_y": self.max_y,
            "max_z": self.max_z,
            "connection_points": self.connection_points,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SVGXSymbolGeometry":
        """Create geometry from dictionary."""
        return cls(
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            depth=data.get("depth", 0.0),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            z=data.get("z", 0.0),
            rotation_x=data.get("rotation_x", 0.0),
            rotation_y=data.get("rotation_y", 0.0),
            rotation_z=data.get("rotation_z", 0.0),
            scale_x=data.get("scale_x", 1.0),
            scale_y=data.get("scale_y", 1.0),
            scale_z=data.get("scale_z", 1.0),
            path_data=data.get("path_data"),
            min_x=data.get("min_x", 0.0),
            min_y=data.get("min_y", 0.0),
            min_z=data.get("min_z", 0.0),
            max_x=data.get("max_x", 0.0),
            max_y=data.get("max_y", 0.0),
            max_z=data.get("max_z", 0.0),
            connection_points=data.get("connection_points", []),
        )


@dataclass
class SVGXSymbolBehavior:
    """Behavior information for SVGX symbols."""

    # Variables
    variables: Dict[str, Any] = field(default_factory=dict)

    # Calculations
    calculations: Dict[str, str] = field(default_factory=dict)

    # Events
    events: Dict[str, str] = field(default_factory=dict)

    # Triggers
    triggers: List[Dict[str, Any]] = field(default_factory=list)

    # Actions
    actions: List[Dict[str, Any]] = field(default_factory=list)

    # Constraints
    constraints: List[Dict[str, Any]] = field(default_factory=list)

    # Physics
    physics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert behavior to dictionary."""
        return {
            "variables": self.variables,
            "calculations": self.calculations,
            "events": self.events,
            "triggers": self.triggers,
            "actions": self.actions,
            "constraints": self.constraints,
            "physics": self.physics,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SVGXSymbolBehavior":
        """Create behavior from dictionary."""
        return cls(
            variables=data.get("variables", {}),
            calculations=data.get("calculations", {}),
            events=data.get("events", {}),
            triggers=data.get("triggers", []),
            actions=data.get("actions", []),
            constraints=data.get("constraints", []),
            physics=data.get("physics", {}),
        )


@dataclass
class SVGXSymbol:
    """Complete SVGX symbol model."""

    # Unique Identifier
    id: str

    # Core Components
    metadata: SVGXSymbolMetadata
    geometry: SVGXSymbolGeometry
    behavior: SVGXSymbolBehavior

    # Content
    svgx_content: str = ""

    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    # Rendering
    style: Dict[str, Any] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)

    # Relationships
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    # Version Control
    version: str = "1.0.0"
    change_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert symbol to dictionary."""
        return {
            "id": self.id,
            "metadata": self.metadata.to_dict(),
            "geometry": self.geometry.to_dict(),
            "behavior": self.behavior.to_dict(),
            "svgx_content": self.svgx_content,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "style": self.style,
            "attributes": self.attributes,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "dependencies": self.dependencies,
            "version": self.version,
            "change_history": self.change_history,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SVGXSymbol":
        """Create symbol from dictionary."""
        return cls(
            id=data["id"],
            metadata=SVGXSymbolMetadata.from_dict(data["metadata"]),
            geometry=SVGXSymbolGeometry.from_dict(data["geometry"]),
            behavior=SVGXSymbolBehavior.from_dict(data["behavior"]),
            svgx_content=data.get("svgx_content", ""),
            is_valid=data.get("is_valid", True),
            validation_errors=data.get("validation_errors", []),
            style=data.get("style", {}),
            attributes=data.get("attributes", {}),
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            dependencies=data.get("dependencies", []),
            version=data.get("version", "1.0.0"),
            change_history=data.get("change_history", []),
        )

    def to_json(self) -> str:
        """Convert symbol to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "SVGXSymbol":
        """Create symbol from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> bool:
        """Validate the symbol."""
        self.validation_errors = []

        # Basic validation
        if not self.id:
            self.validation_errors.append("Symbol ID is required")

        if not self.metadata.name:
            self.validation_errors.append("Symbol name is required")

        if not self.svgx_content:
            self.validation_errors.append("SVGX content is required")

        # Geometry validation
        if self.geometry.width < 0 or self.geometry.height < 0:
            self.validation_errors.append("Invalid geometry dimensions")

        # Behavior validation
        for var_name, var_value in self.behavior.variables.items():
            if not isinstance(var_name, str):
                self.validation_errors.append(f"Invalid variable name: {var_name}")

        self.is_valid = len(self.validation_errors) == 0
        return self.is_valid

    def get_connection_points(self) -> List[Dict[str, Any]]:
        """Get all connection points for the symbol."""
        return self.geometry.connection_points

    def add_connection_point(self, point: Dict[str, Any]) -> None:
        """Add a connection point to the symbol."""
        self.geometry.connection_points.append(point)

    def update_usage_count(self) -> None:
        """Increment the usage count."""
        self.metadata.usage_count += 1
        self.metadata.modified_date = datetime.now()

    def add_review(self, rating: float, comment: str, user: str) -> None:
        """Add a review to the symbol."""
        review = {
            "rating": rating,
            "comment": comment,
            "user": user,
            "date": datetime.now().isoformat(),
        }
        self.metadata.reviews.append(review)

        # Update average rating
        if self.metadata.reviews:
            total_rating = sum(r["rating"] for r in self.metadata.reviews)
            self.metadata.rating = total_rating / len(self.metadata.reviews)

        self.metadata.modified_date = datetime.now()

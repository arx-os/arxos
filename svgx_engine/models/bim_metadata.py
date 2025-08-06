"""
SVGX Engine - BIM Metadata Models

This module defines the data models for BIM metadata including:
- Property sets
- Classification references
- Object metadata
- Version control
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid


class ClassificationSystem(Enum):
    IFC = "IFC"
    UNIFORMAT = "Uniformat"
    OMNICLASS = "Omniclass"
    CUSTOM = "Custom"


@dataclass
class ClassificationReference:
    system: ClassificationSystem = ClassificationSystem.IFC
    code: str = ""
    name: Optional[str] = None
    description: Optional[str] = None
    uri: Optional[str] = None


@dataclass
class PropertySet:
    name: str = ""
    description: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    version: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_property(self, key: str, value: Any):
        self.properties[key] = value
        self.updated_at = datetime.now()

    def get_property(self, key: str, default: Any = None) -> Any:
        return self.properties.get(key, default)


@dataclass
class VersionControlEntry:
    version: str = ""
    author: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    change_note: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None


@dataclass
class BIMObjectMetadata:
    guid: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    description: Optional[str] = None
    property_sets: List[PropertySet] = field(default_factory=list)
    classifications: List[ClassificationReference] = field(default_factory=list)
    version_history: List[VersionControlEntry] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    custom: Dict[str, Any] = field(default_factory=dict)

    def add_property_set(self, pset: PropertySet):
        self.property_sets.append(pset)
        self.updated_at = datetime.now()

    def add_classification(self, classification: ClassificationReference):
        self.classifications.append(classification)
        self.updated_at = datetime.now()

    def add_version_entry(self, entry: VersionControlEntry):
        self.version_history.append(entry)
        self.updated_at = datetime.now()

    def add_custom_metadata(self, key: str, value: Any):
        self.custom[key] = value
        self.updated_at = datetime.now()

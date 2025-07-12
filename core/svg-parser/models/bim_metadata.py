from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, timezone
from enum import Enum
import uuid

class ClassificationSystem(str, Enum):
    IFC = "IFC"
    UNIFORMAT = "Uniformat"
    OMNICLASS = "Omniclass"
    CUSTOM = "Custom"

class ClassificationReference(BaseModel):
    system: ClassificationSystem = ClassificationSystem.IFC
    code: str
    name: Optional[str] = None
    description: Optional[str] = None
    uri: Optional[str] = None

class PropertySet(BaseModel):
    name: str
    description: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    version: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def add_property(self, key: str, value: Any):
        self.properties[key] = value
        self.updated_at = datetime.now(timezone.utc)

    def get_property(self, key: str, default: Any = None) -> Any:
        return self.properties.get(key, default)

class VersionControlEntry(BaseModel):
    version: str
    author: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    change_note: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None

class BIMObjectMetadata(BaseModel):
    guid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    description: Optional[str] = None
    property_sets: List[PropertySet] = Field(default_factory=list)
    classifications: List[ClassificationReference] = Field(default_factory=list)
    version_history: List[VersionControlEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    custom: Dict[str, Any] = Field(default_factory=dict)

    def add_property_set(self, pset: PropertySet):
        self.property_sets.append(pset)
        self.updated_at = datetime.now(timezone.utc)

    def add_classification(self, classification: ClassificationReference):
        self.classifications.append(classification)
        self.updated_at = datetime.now(timezone.utc)

    def add_version_entry(self, entry: VersionControlEntry):
        self.version_history.append(entry)
        self.updated_at = datetime.now(timezone.utc)

    def add_custom_metadata(self, key: str, value: Any):
        self.custom[key] = value
        self.updated_at = datetime.now(timezone.utc) 
"""
Arxfile schema models for building repository configuration.

This module defines the data models for arxfile.yaml, which serves as the
configuration file for each building repository, defining permissions,
share distribution, contracts, and metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
import yaml
import json


class PermissionLevel(str, Enum):
    """Permission levels for building access."""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"


class ShareType(str, Enum):
    """Types of shares in building repositories."""
    EQUITY = "equity"
    REVENUE = "revenue"
    DATA = "data"
    ACCESS = "access"


class ContractType(str, Enum):
    """Types of contracts for building management."""
    OWNERSHIP = "ownership"
    MAINTENANCE = "maintenance"
    INSPECTION = "inspection"
    CONSTRUCTION = "construction"
    LICENSING = "licensing"


class LicenseStatus(str, Enum):
    """License status for building data."""
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    PENDING = "pending"


class ShareDistribution(BaseModel):
    """Share distribution configuration for building contributors."""
    
    contributor_id: str
    share_type: ShareType
    percentage: float = Field(ge=0.0, le=100.0)
    start_date: datetime
    end_date: Optional[datetime] = None
    conditions: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('percentage')
    def validate_percentage(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Percentage must be between 0 and 100')
        return v


class Contract(BaseModel):
    """Contract configuration for building management."""
    
    contract_id: str
    contract_type: ContractType
    parties: List[str]
    start_date: datetime
    end_date: Optional[datetime] = None
    terms: Dict[str, Any] = Field(default_factory=dict)
    obligations: List[str] = Field(default_factory=list)
    penalties: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Permission(BaseModel):
    """Permission configuration for building access."""
    
    user_id: str
    resource_type: str  # building, floor, system, etc.
    permission_level: PermissionLevel
    floor_id: Optional[str] = None
    system_code: Optional[str] = None  # E, LV, FA, N, M, P, S
    start_date: datetime
    end_date: Optional[datetime] = None
    conditions: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditConfig(BaseModel):
    """Audit configuration for building repository."""
    
    enabled: bool = True
    log_level: str = "INFO"
    retention_days: int = 365
    export_format: str = "json"
    include_metadata: bool = True
    real_time_alerts: bool = False
    alert_recipients: List[str] = Field(default_factory=list)


class SyncConfig(BaseModel):
    """Synchronization configuration for building repository."""
    
    auto_sync: bool = True
    sync_interval_minutes: int = 15
    conflict_resolution: str = "manual"  # manual, auto, merge
    backup_enabled: bool = True
    backup_retention_days: int = 30
    offline_support: bool = True
    mobile_sync: bool = True


class ArxfileSchema(BaseModel):
    """Main arxfile.yaml schema for building repository configuration."""
    
    # Repository metadata
    building_id: str = Field(..., description="Unique building identifier")
    building_name: str = Field(..., description="Human-readable building name")
    building_type: str = Field(..., description="Type of building (commercial, residential, etc.)")
    address: Dict[str, str] = Field(..., description="Building address information")
    
    # Version control
    version: str = Field(default="1.0.0", description="Schema version")
    created_at: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)
    
    # Ownership and licensing
    owner_id: str = Field(..., description="Primary building owner")
    license_status: LicenseStatus = Field(default=LicenseStatus.ACTIVE)
    license_expiry: Optional[datetime] = None
    license_terms: Dict[str, Any] = Field(default_factory=dict)
    
    # Share distribution
    shares: List[ShareDistribution] = Field(default_factory=list)
    
    # Contracts
    contracts: List[Contract] = Field(default_factory=list)
    
    # Permissions
    permissions: List[Permission] = Field(default_factory=list)
    
    # Access control
    default_permission_level: PermissionLevel = Field(default=PermissionLevel.READ)
    public_access: bool = Field(default=False)
    require_authentication: bool = Field(default=True)
    
    # Repository settings
    audit_config: AuditConfig = Field(default_factory=AuditConfig)
    sync_config: SyncConfig = Field(default_factory=SyncConfig)
    
    # Building-specific settings
    floor_count: int = Field(..., description="Number of floors in building")
    total_area_sqft: Optional[float] = None
    construction_year: Optional[int] = None
    last_renovation: Optional[datetime] = None
    
    # System configurations
    supported_systems: List[str] = Field(
        default=["E", "LV", "FA", "N", "M", "P", "S"],
        description="Supported MEP systems"
    )
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    notes: Optional[str] = None
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('shares')
    def validate_total_shares(cls, v):
        """Validate that total share percentage doesn't exceed 100%."""
        total = sum(share.percentage for share in v)
        if total > 100:
            raise ValueError(f'Total share percentage ({total}%) exceeds 100%')
        return v
    
    @validator('building_id')
    def validate_building_id(cls, v):
        """Validate building ID format."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Building ID cannot be empty')
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Building ID must be alphanumeric with optional hyphens and underscores')
        return v.strip()
    
    def to_yaml(self) -> str:
        """Convert schema to YAML string."""
        data = self.dict()
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    
    def to_json(self) -> str:
        """Convert schema to JSON string."""
        return self.json(indent=2)
    
    @classmethod
    def from_yaml(cls, yaml_content: str) -> 'ArxfileSchema':
        """Create schema from YAML content."""
        data = yaml.safe_load(yaml_content)
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_content: str) -> 'ArxfileSchema':
        """Create schema from JSON content."""
        data = json.loads(json_content)
        return cls(**data)
    
    def validate_permissions(self) -> List[str]:
        """Validate permissions and return list of issues."""
        issues = []
        
        for permission in self.permissions:
            # Check if user exists (would need user service integration)
            if not permission.user_id:
                issues.append(f"Permission {permission.user_id} has empty user_id")
            
            # Check if resource type is supported
            if permission.resource_type not in ['building', 'floor', 'system', 'asset']:
                issues.append(f"Permission {permission.user_id} has invalid resource_type: {permission.resource_type}")
            
            # Check date validity
            if permission.end_date and permission.start_date > permission.end_date:
                issues.append(f"Permission {permission.user_id} has invalid date range")
        
        return issues
    
    def get_user_permissions(self, user_id: str) -> List[Permission]:
        """Get all permissions for a specific user."""
        return [p for p in self.permissions if p.user_id == user_id]
    
    def get_floor_permissions(self, floor_id: str) -> List[Permission]:
        """Get all permissions for a specific floor."""
        return [p for p in self.permissions if p.floor_id == floor_id]
    
    def get_system_permissions(self, system_code: str) -> List[Permission]:
        """Get all permissions for a specific system."""
        return [p for p in self.permissions if p.system_code == system_code]
    
    def add_permission(self, permission: Permission) -> None:
        """Add a new permission to the schema."""
        self.permissions.append(permission)
        self.last_modified = datetime.now()
    
    def remove_permission(self, user_id: str, resource_type: str, floor_id: Optional[str] = None) -> bool:
        """Remove a permission from the schema."""
        initial_count = len(self.permissions)
        self.permissions = [
            p for p in self.permissions 
            if not (p.user_id == user_id and 
                   p.resource_type == resource_type and 
                   (floor_id is None or p.floor_id == floor_id))
        ]
        if len(self.permissions) < initial_count:
            self.last_modified = datetime.now()
            return True
        return False
    
    def add_share(self, share: ShareDistribution) -> None:
        """Add a new share distribution to the schema."""
        self.shares.append(share)
        self.last_modified = datetime.now()
    
    def add_contract(self, contract: Contract) -> None:
        """Add a new contract to the schema."""
        self.contracts.append(contract)
        self.last_modified = datetime.now()
    
    def get_total_shares(self) -> float:
        """Get total share percentage."""
        return sum(share.percentage for share in self.shares)
    
    def get_available_shares(self) -> float:
        """Get available share percentage."""
        return 100.0 - self.get_total_shares()


class ArxfileManager:
    """Manager for arxfile.yaml operations."""
    
    def __init__(self, file_path: str = "arxfile.yaml"):
        self.file_path = file_path
        self.schema: Optional[ArxfileSchema] = None
    
    def load(self) -> ArxfileSchema:
        """Load arxfile.yaml from disk."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
            
            self.schema = ArxfileSchema.from_yaml(yaml_content)
            return self.schema
        except FileNotFoundError:
            raise FileNotFoundError(f"Arxfile not found: {self.file_path}")
        except Exception as e:
            raise ValueError(f"Failed to load arxfile: {e}")
    
    def save(self, schema: Optional[ArxfileSchema] = None) -> None:
        """Save arxfile.yaml to disk."""
        if schema is None:
            schema = self.schema
        
        if schema is None:
            raise ValueError("No schema to save")
        
        try:
            yaml_content = schema.to_yaml()
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
        except Exception as e:
            raise ValueError(f"Failed to save arxfile: {e}")
    
    def create_new(self, building_id: str, building_name: str, building_type: str,
                   address: Dict[str, str], owner_id: str, floor_count: int) -> ArxfileSchema:
        """Create a new arxfile.yaml schema."""
        self.schema = ArxfileSchema(
            building_id=building_id,
            building_name=building_name,
            building_type=building_type,
            address=address,
            owner_id=owner_id,
            floor_count=floor_count
        )
        return self.schema
    
    def validate(self) -> List[str]:
        """Validate the current schema and return issues."""
        if self.schema is None:
            return ["No schema loaded"]
        
        issues = []
        
        # Validate schema structure
        try:
            self.schema.validate_permissions()
        except Exception as e:
            issues.append(f"Schema validation error: {e}")
        
        # Validate permissions
        issues.extend(self.schema.validate_permissions())
        
        # Validate shares
        if self.schema.get_total_shares() > 100:
            issues.append("Total share percentage exceeds 100%")
        
        # Validate required fields
        if not self.schema.building_id:
            issues.append("Building ID is required")
        
        if not self.schema.building_name:
            issues.append("Building name is required")
        
        return issues
    
    def get_user_access_level(self, user_id: str, resource_type: str = "building",
                             floor_id: Optional[str] = None) -> PermissionLevel:
        """Get the highest permission level for a user on a resource."""
        if self.schema is None:
            return PermissionLevel.NONE
        
        user_permissions = self.schema.get_user_permissions(user_id)
        
        # Filter by resource type and floor
        relevant_permissions = [
            p for p in user_permissions
            if p.resource_type == resource_type and
            (floor_id is None or p.floor_id == floor_id)
        ]
        
        if not relevant_permissions:
            return self.schema.default_permission_level
        
        # Return highest permission level
        levels = [PermissionLevel.NONE, PermissionLevel.READ, 
                 PermissionLevel.WRITE, PermissionLevel.ADMIN, PermissionLevel.OWNER]
        
        max_level = PermissionLevel.NONE
        for permission in relevant_permissions:
            if levels.index(permission.permission_level) > levels.index(max_level):
                max_level = permission.permission_level
        
        return max_level
    
    def can_user_access(self, user_id: str, action: str, resource_type: str = "building",
                       floor_id: Optional[str] = None) -> bool:
        """Check if user can perform action on resource."""
        access_level = self.get_user_access_level(user_id, resource_type, floor_id)
        
        # Define action requirements
        action_requirements = {
            "read": PermissionLevel.READ,
            "write": PermissionLevel.WRITE,
            "admin": PermissionLevel.ADMIN,
            "owner": PermissionLevel.OWNER
        }
        
        required_level = action_requirements.get(action, PermissionLevel.OWNER)
        levels = [PermissionLevel.NONE, PermissionLevel.READ, 
                 PermissionLevel.WRITE, PermissionLevel.ADMIN, PermissionLevel.OWNER]
        
        return levels.index(access_level) >= levels.index(required_level) 
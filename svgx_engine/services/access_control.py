"""
Access Control Service for SVGX Engine.

Provides comprehensive role-based access control (RBAC) with:
- Role management and inheritance
- Permission-based access control
- Audit logging
- Resource-level permissions
- User session management
- SVGX-specific resource types and actions
"""

import sqlite3
import json
import structlog
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

# Import SVGX-specific utilities
from ..utils.errors import AccessControlError, ValidationError
from ..utils import errors

logger = structlog.get_logger(__name__)

class UserRole(str, Enum):
    """User roles with hierarchical permissions."""
    VIEWER = "viewer"           # Read-only access
    EDITOR = "editor"           # Create and edit content
    ADMIN = "admin"             # System administration
    SUPERUSER = "superuser"     # Full system control
    MAINTENANCE = "maintenance" # Maintenance operations
    AUDITOR = "auditor"         # Audit and compliance
    CAD_USER = "cad_user"       # CAD-specific operations
    BIM_SPECIALIST = "bim_specialist"  # BIM-specific operations

class ResourceType(str, Enum):
    """Resource types for permission management with SVGX extensions."""
    # Core SVGX resources
    SVGX_FILE = "svgx_file"
    SVGX_ELEMENT = "svgx_element"
    SVGX_BEHAVIOR = "svgx_behavior"
    SVGX_PHYSICS = "svgx_physics"
    
    # CAD-specific resources
    DIMENSION = "dimension"
    CONSTRAINT = "constraint"
    ANNOTATION = "annotation"
    LAYER = "layer"
    SELECTION = "selection"
    TRANSFORM = "transform"
    
    # Legacy resources (maintained for compatibility)
    SYMBOL = "symbol"
    BUILDING = "building"
    FLOOR = "floor"
    USER = "user"
    PROJECT = "project"
    SYSTEM = "system"
    REPORT = "report"
    EXPORT = "export"
    AUDIT = "audit"

class ActionType(str, Enum):
    """Action types for permission management with SVGX extensions."""
    # Core actions
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    VALIDATE = "validate"
    MANAGE = "manage"
    AUDIT = "audit"
    
    # SVGX-specific actions
    EXECUTE = "execute"         # Execute behaviors
    SIMULATE = "simulate"       # Run physics simulations
    COMPILE = "compile"         # Compile SVGX to other formats
    RENDER = "render"           # Render SVGX content
    
    # CAD-specific actions
    DIMENSION = "dimension"     # Add/modify dimensions
    CONSTRAINT = "constraint"   # Add/modify constraints
    ANNOTATE = "annotate"       # Add/modify annotations
    TRANSFORM = "transform"     # Transform objects
    SELECT = "select"           # Select objects

class PermissionLevel(str, Enum):
    """Permission levels for granular access control."""
    NONE = "none"
    OWN = "own"      # Only own resources
    PROJECT = "project"  # Project-level access
    ORGANIZATION = "organization"  # Organization-level access
    GLOBAL = "global"    # Global access

@dataclass
class Permission:
    """Permission definition with SVGX extensions."""
    resource_type: ResourceType
    action: ActionType
    level: PermissionLevel
    conditions: Dict[str, Any] = field(default_factory=dict)
    svgx_namespace: Optional[str] = None  # SVGX namespace restriction

@dataclass
class Role:
    """Role definition with permissions and SVGX capabilities."""
    name: str
    description: str
    permissions: List[Permission] = field(default_factory=list)
    inherits_from: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    svgx_capabilities: List[str] = field(default_factory=list)  # SVGX-specific capabilities

@dataclass
class User:
    """User information with roles and permissions."""
    user_id: str
    username: str
    email: str
    primary_role: UserRole
    secondary_roles: List[UserRole] = field(default_factory=list)
    organization: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    svgx_preferences: Dict[str, Any] = field(default_factory=dict)  # SVGX user preferences

@dataclass
class AuditLog:
    """Audit log entry with SVGX context."""
    id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any]
    ip_address: str
    user_agent: str
    timestamp: datetime
    success: bool
    svgx_context: Dict[str, Any] = field(default_factory=dict)  # SVGX-specific context

class AccessControlService:
    """Comprehensive access control service with RBAC and SVGX support."""
    
    def __init__(self, db_path: str = "data/access_control.db"):
        self.db_path = db_path
        self.roles: Dict[str, Role] = {}
        self.permissions: Dict[str, Permission] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self._initialize_roles()
        self._initialize_database()
        
        logger.info("access_control_service_initialized",
                   db_path=db_path,
                   roles_count=len(self.roles))
    
    def _initialize_roles(self):
        """Initialize default roles with permissions including SVGX capabilities."""
        logger.debug("initializing_default_roles")
        
        # Viewer role - read-only access
        viewer_role = Role(
            name="viewer",
            description="Read-only access to SVGX files and basic features",
            permissions=[
                Permission(ResourceType.SVGX_FILE, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.SVGX_ELEMENT, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.SYMBOL, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.BUILDING, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.FLOOR, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.REPORT, ActionType.READ, PermissionLevel.OWN),
            ],
            svgx_capabilities=["view", "export_basic"]
        )
        
        # Editor role - create and edit content
        editor_role = Role(
            name="editor",
            description="Can create, update, and delete SVGX elements",
            inherits_from=["viewer"],
            permissions=[
                Permission(ResourceType.SVGX_FILE, ActionType.CREATE, PermissionLevel.PROJECT),
                Permission(ResourceType.SVGX_FILE, ActionType.UPDATE, PermissionLevel.PROJECT),
                Permission(ResourceType.SVGX_ELEMENT, ActionType.CREATE, PermissionLevel.PROJECT),
                Permission(ResourceType.SVGX_ELEMENT, ActionType.UPDATE, PermissionLevel.PROJECT),
                Permission(ResourceType.SVGX_ELEMENT, ActionType.DELETE, PermissionLevel.OWN),
                Permission(ResourceType.SYMBOL, ActionType.CREATE, PermissionLevel.PROJECT),
                Permission(ResourceType.SYMBOL, ActionType.UPDATE, PermissionLevel.PROJECT),
                Permission(ResourceType.SYMBOL, ActionType.DELETE, PermissionLevel.OWN),
                Permission(ResourceType.SYMBOL, ActionType.VALIDATE, PermissionLevel.PROJECT),
                Permission(ResourceType.BUILDING, ActionType.UPDATE, PermissionLevel.PROJECT),
                Permission(ResourceType.FLOOR, ActionType.UPDATE, PermissionLevel.PROJECT),
                Permission(ResourceType.EXPORT, ActionType.EXPORT, PermissionLevel.PROJECT),
            ],
            svgx_capabilities=["edit", "compile", "render_basic"]
        )
        
        # CAD User role - CAD-specific operations
        cad_user_role = Role(
            name="cad_user",
            description="CAD-specific operations and tools",
            inherits_from=["editor"],
            permissions=[
                Permission(ResourceType.DIMENSION, ActionType.DIMENSION, PermissionLevel.PROJECT),
                Permission(ResourceType.CONSTRAINT, ActionType.CONSTRAINT, PermissionLevel.PROJECT),
                Permission(ResourceType.ANNOTATION, ActionType.ANNOTATE, PermissionLevel.PROJECT),
                Permission(ResourceType.LAYER, ActionType.MANAGE, PermissionLevel.PROJECT),
                Permission(ResourceType.SELECTION, ActionType.SELECT, PermissionLevel.PROJECT),
                Permission(ResourceType.TRANSFORM, ActionType.TRANSFORM, PermissionLevel.PROJECT),
            ],
            svgx_capabilities=["cad_tools", "dimensioning", "constraints", "annotations"]
        )
        
        # BIM Specialist role - BIM-specific operations
        bim_specialist_role = Role(
            name="bim_specialist",
            description="BIM-specific operations and integration",
            inherits_from=["editor"],
            permissions=[
                Permission(ResourceType.SVGX_BEHAVIOR, ActionType.EXECUTE, PermissionLevel.PROJECT),
                Permission(ResourceType.SVGX_PHYSICS, ActionType.SIMULATE, PermissionLevel.PROJECT),
                Permission(ResourceType.BUILDING, ActionType.MANAGE, PermissionLevel.PROJECT),
                Permission(ResourceType.FLOOR, ActionType.MANAGE, PermissionLevel.PROJECT),
            ],
            svgx_capabilities=["bim_integration", "physics_simulation", "behavior_execution"]
        )
        
        # Admin role - system administration
        admin_role = Role(
            name="admin",
            description="Full system access including user management",
            inherits_from=["editor", "cad_user", "bim_specialist"],
            permissions=[
                Permission(ResourceType.USER, ActionType.MANAGE, PermissionLevel.GLOBAL),
                Permission(ResourceType.SYSTEM, ActionType.MANAGE, PermissionLevel.GLOBAL),
                Permission(ResourceType.REPORT, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.EXPORT, ActionType.EXPORT, PermissionLevel.GLOBAL),
                Permission(ResourceType.SYSTEM, ActionType.IMPORT, PermissionLevel.GLOBAL),
            ],
            svgx_capabilities=["admin", "system_config", "user_management"]
        )
        
        # Superuser role - complete system control
        superuser_role = Role(
            name="superuser",
            description="Complete system control and configuration",
            inherits_from=["admin"],
            permissions=[
                Permission(ResourceType.SYSTEM, ActionType.MANAGE, PermissionLevel.GLOBAL),
                Permission(ResourceType.USER, ActionType.MANAGE, PermissionLevel.GLOBAL),
                Permission(ResourceType.AUDIT, ActionType.AUDIT, PermissionLevel.GLOBAL),
            ],
            svgx_capabilities=["all"]
        )
        
        # Maintenance role - maintenance operations
        maintenance_role = Role(
            name="maintenance",
            description="Maintenance and operational tasks",
            permissions=[
                Permission(ResourceType.SYSTEM, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.REPORT, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.EXPORT, ActionType.EXPORT, PermissionLevel.GLOBAL),
            ],
            svgx_capabilities=["maintenance", "monitoring"]
        )
        
        # Auditor role - audit and compliance
        auditor_role = Role(
            name="auditor",
            description="Audit and compliance monitoring",
            permissions=[
                Permission(ResourceType.AUDIT, ActionType.AUDIT, PermissionLevel.GLOBAL),
                Permission(ResourceType.REPORT, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.SYSTEM, ActionType.READ, PermissionLevel.GLOBAL),
            ],
            svgx_capabilities=["audit", "compliance"]
        )
        
        # Store roles
        self.roles = {
            "viewer": viewer_role,
            "editor": editor_role,
            "cad_user": cad_user_role,
            "bim_specialist": bim_specialist_role,
            "admin": admin_role,
            "superuser": superuser_role,
            "maintenance": maintenance_role,
            "auditor": auditor_role,
        }
        
        logger.info("default_roles_initialized",
                   roles_count=len(self.roles),
                   role_names=list(self.roles.keys()))
    
    def _initialize_database(self):
        """Initialize the access control database with SVGX extensions."""
        try:
            import os
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table with SVGX extensions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    primary_role TEXT NOT NULL,
                    secondary_roles TEXT,
                    organization TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    metadata TEXT,
                    svgx_preferences TEXT
                )
            """)
            
            # Create audit_logs table with SVGX context
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT TRUE,
                    svgx_context TEXT
                )
            """)
            
            # Create sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Create SVGX-specific tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS svgx_permissions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    svgx_namespace TEXT,
                    resource_type TEXT NOT NULL,
                    action TEXT NOT NULL,
                    level TEXT NOT NULL,
                    conditions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("access_control_database_initialized",
                       db_path=self.db_path)
            
        except Exception as e:
            logger.error("database_initialization_failed",
                        db_path=self.db_path,
                        error=str(e),
                        error_type=type(e).__name__)
            raise errors.AccessControlError(f"Failed to initialize database: {str(e)}")
    
    def create_user(self, username: str, email: str, primary_role: UserRole,
                   secondary_roles: List[UserRole] = None, organization: str = "",
                   svgx_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new user with specified roles and SVGX preferences."""
        try:
            # Validate input parameters
            if not username or not email:
                raise errors.ValidationError("Username and email are required")
            
            if not isinstance(primary_role, UserRole):
                raise errors.ValidationError("Invalid primary role")
            
            user_id = str(uuid.uuid4())
            secondary_roles = secondary_roles or []
            svgx_preferences = svgx_preferences or {}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (user_id, username, email, primary_role, secondary_roles, 
                                 organization, svgx_preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                username,
                email,
                primary_role.value,
                json.dumps([role.value for role in secondary_roles]),
                organization,
                json.dumps(svgx_preferences)
            ))
            
            conn.commit()
            conn.close()
            
            logger.info("user_created",
                       user_id=user_id,
                       username=username,
                       email=email,
                       primary_role=primary_role.value,
                       secondary_roles=[role.value for role in secondary_roles],
                       organization=organization,
                       svgx_preferences=svgx_preferences)
            
            return {
                "user_id": user_id,
                "username": username,
                "email": email,
                "primary_role": primary_role.value,
                "secondary_roles": [role.value for role in secondary_roles],
                "organization": organization,
                "svgx_preferences": svgx_preferences,
                "created_at": datetime.utcnow().isoformat()
            }
            
        except sqlite3.IntegrityError as e:
            logger.warning("user_creation_failed_duplicate",
                          username=username,
                          email=email,
                          error=str(e))
            raise errors.ValidationError(f"User with username '{username}' or email '{email}' already exists")
        except Exception as e:
            logger.error("user_creation_failed",
                        username=username,
                        email=email,
                        error=str(e),
                        error_type=type(e).__name__)
            raise errors.AccessControlError(f"Failed to create user: {str(e)}")
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user information by user ID with SVGX preferences."""
        try:
            if not user_id:
                raise errors.ValidationError("User ID is required")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, username, email, primary_role, secondary_roles, 
                       organization, created_at, last_login, is_active, metadata, svgx_preferences
                FROM users WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                logger.warning("user_not_found", user_id=user_id)
                return None
            
            user_data = {
                "user_id": row[0],
                "username": row[1],
                "email": row[2],
                "primary_role": row[3],
                "secondary_roles": json.loads(row[4]) if row[4] else [],
                "organization": row[5],
                "created_at": row[6],
                "last_login": row[7],
                "is_active": bool(row[8]),
                "metadata": json.loads(row[9]) if row[9] else {},
                "svgx_preferences": json.loads(row[10]) if row[10] else {}
            }
            
            logger.debug("user_retrieved", user_id=user_id, username=user_data["username"])
            return user_data
            
        except Exception as e:
            logger.error("user_retrieval_failed",
                        user_id=user_id,
                        error=str(e),
                        error_type=type(e).__name__)
            raise errors.AccessControlError(f"Failed to retrieve user: {str(e)}")
    
    def _get_user_permissions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all permissions for a user including inherited roles and SVGX capabilities."""
        try:
            user = self.get_user(user_id)
            if not user:
                logger.warning("user_permissions_failed_user_not_found", user_id=user_id)
                return []
            
            all_roles = [user["primary_role"]] + user["secondary_roles"]
            all_permissions = []
            
            for role_name in all_roles:
                role_permissions = self._get_role_permissions(role_name)
                all_permissions.extend(role_permissions)
            
            # Add SVGX-specific permissions
            svgx_permissions = self._get_svgx_permissions(user_id)
            all_permissions.extend(svgx_permissions)
            
            logger.debug("user_permissions_retrieved",
                        user_id=user_id,
                        roles=all_roles,
                        permission_count=len(all_permissions))
            
            return all_permissions
            
        except Exception as e:
            logger.error("user_permissions_failed",
                        user_id=user_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return []
    
    def _get_role_permissions(self, role_name: str) -> List[Dict[str, Any]]:
        """Get permissions for a specific role including SVGX capabilities."""
        try:
            role = self.roles.get(role_name)
            if not role:
                logger.warning("role_not_found", role_name=role_name)
                return []
            
            permissions = []
            
            # Add direct permissions
            for permission in role.permissions:
                permissions.append({
                    "resource_type": permission.resource_type.value,
                    "action": permission.action.value,
                    "level": permission.level.value,
                    "conditions": permission.conditions,
                    "svgx_namespace": permission.svgx_namespace,
                    "source": "role",
                    "role_name": role_name
                })
            
            # Add inherited permissions
            for inherited_role_name in role.inherits_from:
                inherited_permissions = self._get_role_permissions(inherited_role_name)
                for perm in inherited_permissions:
                    perm["source"] = "inherited"
                    perm["inherited_from"] = inherited_role_name
                permissions.extend(inherited_permissions)
            
            # Add SVGX capabilities
            for capability in role.svgx_capabilities:
                permissions.append({
                    "resource_type": "svgx_capability",
                    "action": "execute",
                    "level": "project",
                    "conditions": {},
                    "svgx_namespace": None,
                    "source": "capability",
                    "role_name": role_name,
                    "capability": capability
                })
            
            logger.debug("role_permissions_retrieved",
                        role_name=role_name,
                        permission_count=len(permissions))
            
            return permissions
            
        except Exception as e:
            logger.error("role_permissions_failed",
                        role_name=role_name,
                        error=str(e),
                        error_type=type(e).__name__)
            return []
    
    def _get_svgx_permissions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get SVGX-specific permissions for a user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT svgx_namespace, resource_type, action, level, conditions
                FROM svgx_permissions WHERE user_id = ?
            """, (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            permissions = []
            for row in rows:
                permissions.append({
                    "resource_type": row[1],
                    "action": row[2],
                    "level": row[3],
                    "conditions": json.loads(row[4]) if row[4] else {},
                    "svgx_namespace": row[0],
                    "source": "svgx_specific"
                })
            
            return permissions
            
        except Exception as e:
            logger.error("svgx_permissions_failed",
                        user_id=user_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return []
    
    def check_permission(self, user_id: str, resource_type: str, action: str, 
                        resource_id: str = None, context: Dict[str, Any] = None) -> bool:
        """Check if user has permission for specific action with SVGX context."""
        try:
            if not user_id or not resource_type or not action:
                logger.warning("permission_check_invalid_params",
                             user_id=user_id,
                             resource_type=resource_type,
                             action=action)
                return False
            
            user_permissions = self._get_user_permissions(user_id)
            context = context or {}
            
            # Check for exact permission match
            for permission in user_permissions:
                if (permission["resource_type"] == resource_type and 
                    permission["action"] == action):
                    
                    # Check SVGX namespace restrictions
                    if permission.get("svgx_namespace"):
                        if context.get("svgx_namespace") != permission["svgx_namespace"]:
                            continue
                    
                    # Check permission level
                    if self._check_permission_level(user_id, permission, resource_id, context):
                        logger.debug("permission_granted",
                                   user_id=user_id,
                                   resource_type=resource_type,
                                   action=action,
                                   resource_id=resource_id)
                        return True
            
            logger.debug("permission_denied",
                        user_id=user_id,
                        resource_type=resource_type,
                        action=action,
                        resource_id=resource_id)
            return False
            
        except Exception as e:
            logger.error("permission_check_failed",
                        user_id=user_id,
                        resource_type=resource_type,
                        action=action,
                        error=str(e),
                        error_type=type(e).__name__)
            return False
    
    def _check_permission_level(self, user_id: str, permission: Dict[str, Any], 
                               resource_id: str, context: Dict[str, Any]) -> bool:
        """Check if permission level allows access."""
        level = permission["level"]
        
        if level == PermissionLevel.GLOBAL.value:
            return True
        elif level == PermissionLevel.ORGANIZATION.value:
            return self._user_has_organization_access(user_id, permission["resource_type"], resource_id)
        elif level == PermissionLevel.PROJECT.value:
            return self._user_has_project_access(user_id, permission["resource_type"], resource_id)
        elif level == PermissionLevel.OWN.value:
            return self._user_owns_resource(user_id, permission["resource_type"], resource_id)
        else:
            return False
    
    def _user_owns_resource(self, user_id: str, resource_type: str, resource_id: str) -> bool:
        """Check if user owns the resource."""
        # Implementation would check resource ownership
        # For now, return True for demonstration
        return True
    
    def _user_has_project_access(self, user_id: str, resource_type: str, resource_id: str) -> bool:
        """Check if user has project-level access to resource."""
        # Implementation would check project membership
        # For now, return True for demonstration
        return True
    
    def _user_has_organization_access(self, user_id: str, resource_type: str, resource_id: str) -> bool:
        """Check if user has organization-level access to resource."""
        # Implementation would check organization membership
        # For now, return True for demonstration
        return True
    
    def log_audit_event(self, user_id: str, action: str, resource_type: str, 
                       resource_id: str, details: Dict[str, Any], ip_address: str, 
                       user_agent: str, success: bool = True, svgx_context: Dict[str, Any] = None):
        """Log audit event with SVGX context."""
        try:
            audit_id = str(uuid.uuid4())
            svgx_context = svgx_context or {}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO audit_logs (id, user_id, action, resource_type, resource_id,
                                      details, ip_address, user_agent, success, svgx_context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                audit_id,
                user_id,
                action,
                resource_type,
                resource_id,
                json.dumps(details),
                ip_address,
                user_agent,
                success,
                json.dumps(svgx_context)
            ))
            
            conn.commit()
            conn.close()
            
            logger.info("audit_event_logged",
                       audit_id=audit_id,
                       user_id=user_id,
                       action=action,
                       resource_type=resource_type,
                       resource_id=resource_id,
                       success=success,
                       svgx_context=svgx_context)
            
        except Exception as e:
            logger.error("audit_logging_failed",
                        user_id=user_id,
                        action=action,
                        error=str(e),
                        error_type=type(e).__name__)
    
    def get_audit_logs(self, user_id: str = None, action: str = None, 
                      resource_type: str = None, start_date: datetime = None,
                      end_date: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs with SVGX context filtering."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query with filters
            query = """
                SELECT id, user_id, action, resource_type, resource_id, details,
                       ip_address, user_agent, timestamp, success, svgx_context
                FROM audit_logs WHERE 1=1
            """
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if action:
                query += " AND action = ?"
                params.append(action)
            
            if resource_type:
                query += " AND resource_type = ?"
                params.append(resource_type)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            audit_logs = []
            for row in rows:
                audit_logs.append({
                    "id": row[0],
                    "user_id": row[1],
                    "action": row[2],
                    "resource_type": row[3],
                    "resource_id": row[4],
                    "details": json.loads(row[5]) if row[5] else {},
                    "ip_address": row[6],
                    "user_agent": row[7],
                    "timestamp": row[8],
                    "success": bool(row[9]),
                    "svgx_context": json.loads(row[10]) if row[10] else {}
                })
            
            logger.debug("audit_logs_retrieved",
                        count=len(audit_logs),
                        filters={
                            "user_id": user_id,
                            "action": action,
                            "resource_type": resource_type,
                            "start_date": start_date,
                            "end_date": end_date,
                            "limit": limit
                        })
            
            return audit_logs
            
        except Exception as e:
            logger.error("audit_logs_retrieval_failed",
                        error=str(e),
                        error_type=type(e).__name__)
            return []
    
    def create_session(self, user_id: str, token: str, ip_address: str = None, 
                      user_agent: str = None) -> str:
        """Create user session with SVGX context."""
        try:
            session_id = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sessions (session_id, user_id, token, ip_address, user_agent, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, user_id, token, ip_address, user_agent, expires_at))
            
            conn.commit()
            conn.close()
            
            self.user_sessions[session_id] = {
                "user_id": user_id,
                "token": token,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at
            }
            
            logger.info("session_created",
                       session_id=session_id,
                       user_id=user_id,
                       ip_address=ip_address)
            
            return session_id
            
        except Exception as e:
            logger.error("session_creation_failed",
                        user_id=user_id,
                        error=str(e),
                        error_type=type(e).__name__)
            raise errors.AccessControlError(f"Failed to create session: {str(e)}")
    
    def validate_session(self, session_id: str) -> Dict[str, Any]:
        """Validate user session with SVGX context."""
        try:
            if not session_id:
                return None
            
            # Check in-memory sessions first
            if session_id in self.user_sessions:
                session = self.user_sessions[session_id]
                if session["expires_at"] > datetime.utcnow():
                    return session
                else:
                    del self.user_sessions[session_id]
                    return None
            
            # Check database sessions
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT session_id, user_id, token, ip_address, user_agent, 
                       created_at, expires_at
                FROM sessions WHERE session_id = ? AND is_active = TRUE
            """, (session_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            session_data = {
                "session_id": row[0],
                "user_id": row[1],
                "token": row[2],
                "ip_address": row[3],
                "user_agent": row[4],
                "created_at": row[5],
                "expires_at": row[6]
            }
            
            # Check if session is expired
            if session_data["expires_at"] < datetime.utcnow():
                self.revoke_session(session_id)
                return None
            
            # Cache in memory
            self.user_sessions[session_id] = session_data
            
            logger.debug("session_validated",
                        session_id=session_id,
                        user_id=session_data["user_id"])
            
            return session_data
            
        except Exception as e:
            logger.error("session_validation_failed",
                        session_id=session_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return None
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke user session."""
        try:
            # Remove from memory
            if session_id in self.user_sessions:
                del self.user_sessions[session_id]
            
            # Mark as inactive in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE sessions SET is_active = FALSE WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
            conn.close()
            
            logger.info("session_revoked", session_id=session_id)
            return True
            
        except Exception as e:
            logger.error("session_revocation_failed",
                        session_id=session_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return False
    
    def get_user_svgx_capabilities(self, user_id: str) -> List[str]:
        """Get SVGX capabilities for a user."""
        try:
            user = self.get_user(user_id)
            if not user:
                return []
            
            all_roles = [user["primary_role"]] + user["secondary_roles"]
            capabilities = set()
            
            for role_name in all_roles:
                role = self.roles.get(role_name)
                if role:
                    capabilities.update(role.svgx_capabilities)
            
            return list(capabilities)
            
        except Exception as e:
            logger.error("svgx_capabilities_failed",
                        user_id=user_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return []
    
    def check_svgx_permission(self, user_id: str, svgx_namespace: str, 
                             resource_type: str, action: str) -> bool:
        """Check SVGX-specific permission."""
        try:
            return self.check_permission(
                user_id, resource_type, action,
                context={"svgx_namespace": svgx_namespace}
            )
        except Exception as e:
            logger.error("svgx_permission_check_failed",
                        user_id=user_id,
                        svgx_namespace=svgx_namespace,
                        resource_type=resource_type,
                        action=action,
                        error=str(e))
            return False 
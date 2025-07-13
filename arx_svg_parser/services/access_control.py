"""
Access Control Service for Arxos SVG-BIM Integration System.

Provides comprehensive role-based access control (RBAC) with:
- Role management and inheritance
- Permission-based access control
- Audit logging
- Resource-level permissions
- User session management
"""

import sqlite3
import json
import structlog
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from utils.base_manager import BaseManager
from utils.base_service import BaseService

logger = structlog.get_logger(__name__)

class UserRole(str, Enum):
    """User roles with hierarchical permissions."""
    VIEWER = "viewer"           # Read-only access
    EDITOR = "editor"           # Create and edit content
    ADMIN = "admin"             # System administration
    SUPERUSER = "superuser"     # Full system control
    MAINTENANCE = "maintenance" # Maintenance operations
    AUDITOR = "auditor"         # Audit and compliance

class ResourceType(str, Enum):
    """Resource types for permission management."""
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
    """Action types for permission management."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    VALIDATE = "validate"
    MANAGE = "manage"
    AUDIT = "audit"

class PermissionLevel(str, Enum):
    """Permission levels for granular access control."""
    NONE = "none"
    OWN = "own"      # Only own resources
    PROJECT = "project"  # Project-level access
    ORGANIZATION = "organization"  # Organization-level access
    GLOBAL = "global"    # Global access

@dataclass
class Permission:
    """Permission definition."""
    resource_type: ResourceType
    action: ActionType
    level: PermissionLevel
    conditions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Role:
    """Role definition with permissions."""
    name: str
    description: str
    permissions: List[Permission] = field(default_factory=list)
    inherits_from: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

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

@dataclass
class AuditLog:
    """Audit log entry."""
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

class AccessControlService(BaseManager, BaseService):
    """Comprehensive access control service with RBAC."""
    
    def __init__(self, db_path: str = "data/access_control.db"):
        super().__init__()
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
        """Initialize default roles with permissions."""
        logger.debug("initializing_default_roles")
        
        # Viewer role - read-only access
        viewer_role = Role(
            name="viewer",
            description="Read-only access to symbols and basic features",
            permissions=[
                Permission(ResourceType.SYMBOL, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.BUILDING, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.FLOOR, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.REPORT, ActionType.READ, PermissionLevel.OWN),
            ]
        )
        
        # Editor role - create and edit content
        editor_role = Role(
            name="editor",
            description="Can create, update, and delete symbols",
            inherits_from=["viewer"],
            permissions=[
                Permission(ResourceType.SYMBOL, ActionType.CREATE, PermissionLevel.PROJECT),
                Permission(ResourceType.SYMBOL, ActionType.UPDATE, PermissionLevel.PROJECT),
                Permission(ResourceType.SYMBOL, ActionType.DELETE, PermissionLevel.OWN),
                Permission(ResourceType.SYMBOL, ActionType.VALIDATE, PermissionLevel.PROJECT),
                Permission(ResourceType.BUILDING, ActionType.UPDATE, PermissionLevel.PROJECT),
                Permission(ResourceType.FLOOR, ActionType.UPDATE, PermissionLevel.PROJECT),
                Permission(ResourceType.EXPORT, ActionType.EXPORT, PermissionLevel.PROJECT),
            ]
        )
        
        # Admin role - system administration
        admin_role = Role(
            name="admin",
            description="Full system access including user management",
            inherits_from=["editor"],
            permissions=[
                Permission(ResourceType.USER, ActionType.MANAGE, PermissionLevel.GLOBAL),
                Permission(ResourceType.SYSTEM, ActionType.MANAGE, PermissionLevel.GLOBAL),
                Permission(ResourceType.REPORT, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.EXPORT, ActionType.EXPORT, PermissionLevel.GLOBAL),
                Permission(ResourceType.SYSTEM, ActionType.IMPORT, PermissionLevel.GLOBAL),
            ]
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
            ]
        )
        
        # Maintenance role - maintenance operations
        maintenance_role = Role(
            name="maintenance",
            description="Maintenance and operational tasks",
            permissions=[
                Permission(ResourceType.SYSTEM, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.REPORT, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.EXPORT, ActionType.EXPORT, PermissionLevel.GLOBAL),
            ]
        )
        
        # Auditor role - audit and compliance
        auditor_role = Role(
            name="auditor",
            description="Audit and compliance monitoring",
            permissions=[
                Permission(ResourceType.AUDIT, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.REPORT, ActionType.READ, PermissionLevel.GLOBAL),
                Permission(ResourceType.SYSTEM, ActionType.READ, PermissionLevel.GLOBAL),
            ]
        )
        
        # Store roles
        self.roles = {
            "viewer": viewer_role,
            "editor": editor_role,
            "admin": admin_role,
            "superuser": superuser_role,
            "maintenance": maintenance_role,
            "auditor": auditor_role
        }
        
        logger.info("default_roles_initialized",
                   roles_count=len(self.roles),
                   role_names=list(self.roles.keys()))
    
    def _initialize_database(self):
        """Initialize the access control database."""
        try:
            import os
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table
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
                    metadata TEXT
                )
            """)
            
            # Create audit_logs table
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
                    success BOOLEAN DEFAULT TRUE
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
            
            conn.commit()
            conn.close()
            
            logger.info("access_control_database_initialized",
                       db_path=self.db_path)
            
        except Exception as e:
            logger.error("database_initialization_failed",
                        db_path=self.db_path,
                        error=str(e),
                        error_type=type(e).__name__)
            raise
    
    def create_user(self, username: str, email: str, primary_role: UserRole,
                   secondary_roles: List[UserRole] = None, organization: str = "") -> Dict[str, Any]:
        """Create a new user with specified roles."""
        try:
            user_id = str(uuid.uuid4())
            secondary_roles = secondary_roles or []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (user_id, username, email, primary_role, secondary_roles, organization)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                username,
                email,
                primary_role.value,
                json.dumps([role.value for role in secondary_roles]),
                organization
            ))
            
            conn.commit()
            conn.close()
            
            logger.info("user_created",
                       user_id=user_id,
                       username=username,
                       email=email,
                       primary_role=primary_role.value,
                       secondary_roles=[role.value for role in secondary_roles],
                       organization=organization)
            
            return {
                "user_id": user_id,
                "username": username,
                "email": email,
                "primary_role": primary_role.value,
                "secondary_roles": [role.value for role in secondary_roles],
                "organization": organization,
                "created_at": datetime.utcnow().isoformat()
            }
            
        except sqlite3.IntegrityError as e:
            logger.warning("user_creation_failed_duplicate",
                          username=username,
                          email=email,
                          error=str(e))
            raise ValueError(f"User with username '{username}' or email '{email}' already exists")
        except Exception as e:
            logger.error("user_creation_failed",
                        username=username,
                        email=email,
                        error=str(e),
                        error_type=type(e).__name__)
            raise
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user information by user ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, username, email, primary_role, secondary_roles, 
                       organization, created_at, last_login, is_active, metadata
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
                "metadata": json.loads(row[9]) if row[9] else {}
            }
            
            logger.debug("user_retrieved", user_id=user_id, username=user_data["username"])
            return user_data
            
        except Exception as e:
            logger.error("user_retrieval_failed",
                        user_id=user_id,
                        error=str(e),
                        error_type=type(e).__name__)
            raise
    
    def _get_user_permissions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all permissions for a user including inherited roles."""
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
            
            logger.debug("user_permissions_retrieved",
                        user_id=user_id,
                        roles=all_roles,
                        permissions_count=len(all_permissions))
            
            return all_permissions
            
        except Exception as e:
            logger.error("user_permissions_retrieval_failed",
                        user_id=user_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return []
    
    def _get_role_permissions(self, role_name: str) -> List[Dict[str, Any]]:
        """Get permissions for a specific role including inherited permissions."""
        try:
            if role_name not in self.roles:
                logger.warning("role_not_found", role_name=role_name)
                return []
            
            role = self.roles[role_name]
            permissions = []
            
            # Add direct permissions
            for permission in role.permissions:
                permissions.append({
                    "resource_type": permission.resource_type.value,
                    "action": permission.action.value,
                    "level": permission.level.value,
                    "conditions": permission.conditions
                })
            
            # Add inherited permissions
            for inherited_role_name in role.inherits_from:
                inherited_permissions = self._get_role_permissions(inherited_role_name)
                permissions.extend(inherited_permissions)
            
            logger.debug("role_permissions_retrieved",
                        role_name=role_name,
                        permissions_count=len(permissions))
            
            return permissions
            
        except Exception as e:
            logger.error("role_permissions_retrieval_failed",
                        role_name=role_name,
                        error=str(e),
                        error_type=type(e).__name__)
            return []
    
    def check_permission(self, user_id: str, resource_type: str, action: str, 
                        resource_id: str = None, context: Dict[str, Any] = None) -> bool:
        """Check if user has permission for specific action on resource."""
        try:
            permissions = self._get_user_permissions(user_id)
            context = context or {}
            
            for permission in permissions:
                if (permission["resource_type"] == resource_type and 
                    permission["action"] == action):
                    
                    # Check permission level
                    level = permission["level"]
                    
                    if level == PermissionLevel.GLOBAL.value:
                        logger.debug("permission_granted_global",
                                   user_id=user_id,
                                   resource_type=resource_type,
                                   action=action,
                                   level=level)
                        return True
                    
                    elif level == PermissionLevel.ORGANIZATION.value:
                        if self._user_has_organization_access(user_id, resource_type, resource_id):
                            logger.debug("permission_granted_organization",
                                       user_id=user_id,
                                       resource_type=resource_type,
                                       action=action,
                                       level=level)
                            return True
                    
                    elif level == PermissionLevel.PROJECT.value:
                        if self._user_has_project_access(user_id, resource_type, resource_id):
                            logger.debug("permission_granted_project",
                                       user_id=user_id,
                                       resource_type=resource_type,
                                       action=action,
                                       level=level)
                            return True
                    
                    elif level == PermissionLevel.OWN.value:
                        if self._user_owns_resource(user_id, resource_type, resource_id):
                            logger.debug("permission_granted_own",
                                       user_id=user_id,
                                       resource_type=resource_type,
                                       action=action,
                                       level=level)
                            return True
            
            logger.warning("permission_denied",
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
    
    def _user_owns_resource(self, user_id: str, resource_type: str, resource_id: str) -> bool:
        """Check if user owns the resource."""
        # Implementation would check ownership in database
        # For now, return False as placeholder
        return False
    
    def _user_has_project_access(self, user_id: str, resource_type: str, resource_id: str) -> bool:
        """Check if user has project-level access to resource."""
        # Implementation would check project membership
        # For now, return True as placeholder
        return True
    
    def _user_has_organization_access(self, user_id: str, resource_type: str, resource_id: str) -> bool:
        """Check if user has organization-level access to resource."""
        # Implementation would check organization membership
        # For now, return True as placeholder
        return True
    
    def log_audit_event(self, user_id: str, action: str, resource_type: str, 
                       resource_id: str, details: Dict[str, Any], ip_address: str, 
                       user_agent: str, success: bool = True):
        """Log an audit event."""
        try:
            audit_id = str(uuid.uuid4())
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO audit_logs (id, user_id, action, resource_type, resource_id, 
                                      details, ip_address, user_agent, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                audit_id,
                user_id,
                action,
                resource_type,
                resource_id,
                json.dumps(details),
                ip_address,
                user_agent,
                success
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
                       ip_address=ip_address)
            
        except Exception as e:
            logger.error("audit_event_logging_failed",
                        user_id=user_id,
                        action=action,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        error=str(e),
                        error_type=type(e).__name__)
    
    def get_audit_logs(self, user_id: str = None, action: str = None, 
                      resource_type: str = None, start_date: datetime = None,
                      end_date: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs with optional filtering."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM audit_logs WHERE 1=1"
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
                    "success": bool(row[9])
                })
            
            logger.info("audit_logs_retrieved",
                       filters={
                           "user_id": user_id,
                           "action": action,
                           "resource_type": resource_type,
                           "start_date": start_date.isoformat() if start_date else None,
                           "end_date": end_date.isoformat() if end_date else None
                       },
                       results_count=len(audit_logs))
            
            return audit_logs
            
        except Exception as e:
            logger.error("audit_logs_retrieval_failed",
                        error=str(e),
                        error_type=type(e).__name__)
            return []
    
    def create_session(self, user_id: str, token: str, ip_address: str = None, 
                      user_agent: str = None) -> str:
        """Create a new user session."""
        try:
            session_id = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sessions (session_id, user_id, token, ip_address, user_agent, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, user_id, token, ip_address, user_agent, expires_at.isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info("session_created",
                       session_id=session_id,
                       user_id=user_id,
                       ip_address=ip_address,
                       expires_at=expires_at.isoformat())
            
            return session_id
            
        except Exception as e:
            logger.error("session_creation_failed",
                        user_id=user_id,
                        error=str(e),
                        error_type=type(e).__name__)
            raise
    
    def validate_session(self, session_id: str) -> Dict[str, Any]:
        """Validate a user session."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT session_id, user_id, token, ip_address, user_agent, 
                       created_at, expires_at, is_active
                FROM sessions WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                logger.warning("session_not_found", session_id=session_id)
                return None
            
            session_data = {
                "session_id": row[0],
                "user_id": row[1],
                "token": row[2],
                "ip_address": row[3],
                "user_agent": row[4],
                "created_at": row[5],
                "expires_at": row[6],
                "is_active": bool(row[7])
            }
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if datetime.utcnow() > expires_at:
                logger.warning("session_expired",
                              session_id=session_id,
                              expires_at=expires_at.isoformat())
                return None
            
            # Check if session is active
            if not session_data["is_active"]:
                logger.warning("session_inactive", session_id=session_id)
                return None
            
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
        """Revoke a user session."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE sessions SET is_active = FALSE WHERE session_id = ?
            """, (session_id,))
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            if affected_rows > 0:
                logger.info("session_revoked", session_id=session_id)
                return True
            else:
                logger.warning("session_revoke_failed_not_found", session_id=session_id)
                return False
            
        except Exception as e:
            logger.error("session_revoke_failed",
                        session_id=session_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return False

# Global service instance
access_control_service = AccessControlService() 
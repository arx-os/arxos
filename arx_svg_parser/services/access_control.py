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
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from utils.base_manager import BaseManager
from utils.base_service import BaseService

logger = logging.getLogger(__name__)

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
    
    def _initialize_roles(self):
        """Initialize default roles with permissions."""
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
        
        self.roles = {
            "viewer": viewer_role,
            "editor": editor_role,
            "admin": admin_role,
            "superuser": superuser_role,
            "maintenance": maintenance_role,
            "auditor": auditor_role,
        }
    
    def _initialize_database(self):
        """Initialize database tables for access control."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                primary_role TEXT NOT NULL,
                secondary_roles TEXT,
                organization TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                metadata TEXT
            )
        ''')
        
        # Roles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                name TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                permissions TEXT NOT NULL,
                inherits_from TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Permissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                action TEXT NOT NULL,
                level TEXT NOT NULL,
                conditions TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Audit logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                details TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Insert default roles
        for role_name, role in self.roles.items():
            cursor.execute('''
                INSERT OR REPLACE INTO roles 
                (name, description, permissions, inherits_from, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                role.name,
                role.description,
                json.dumps([p.__dict__ for p in role.permissions]),
                json.dumps(role.inherits_from),
                role.created_at.isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def create_user(self, username: str, email: str, primary_role: UserRole,
                   secondary_roles: List[UserRole] = None, organization: str = "") -> Dict[str, Any]:
        """Create a new user with role assignment."""
        try:
            user_id = str(uuid.uuid4())
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                primary_role=primary_role,
                secondary_roles=secondary_roles or [],
                organization=organization
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (
                    user_id, username, email, primary_role, secondary_roles,
                    organization, created_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.user_id, user.username, user.email, user.primary_role.value,
                json.dumps([r.value for r in user.secondary_roles]),
                user.organization, user.created_at.isoformat(),
                json.dumps(user.metadata)
            ))
            
            conn.commit()
            conn.close()
            
            self.log_info(f"Created user {username} with role {primary_role.value}")
            
            # Record metrics
            self.metrics['user_creations'] += 1
            self.record_metric('user_creation', 1, {'role': primary_role.value})
            
            return {"success": True, "user_id": user_id}
            
        except Exception as e:
            self.log_error(f"Failed to create user: {e}")
            return {"success": False, "message": str(e)}
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user information with roles and permissions."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if not row:
                return {"success": False, "message": "User not found"}
            
            user = {
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
            
            # Get user permissions
            user["permissions"] = self._get_user_permissions(user_id)
            
            conn.close()
            return {"success": True, "user": user}
            
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return {"success": False, "message": str(e)}
    
    def _get_user_permissions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all permissions for a user including inherited ones."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user roles
            cursor.execute('SELECT primary_role, secondary_roles FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if not row:
                return []
            
            primary_role = row[0]
            secondary_roles = json.loads(row[1]) if row[1] else []
            
            # Get all roles including inherited ones
            all_roles = [primary_role] + secondary_roles
            all_permissions = []
            
            for role_name in all_roles:
                role_permissions = self._get_role_permissions(role_name)
                all_permissions.extend(role_permissions)
            
            # Remove duplicates
            unique_permissions = []
            seen = set()
            for perm in all_permissions:
                key = f"{perm['resource_type']}:{perm['action']}:{perm['level']}"
                if key not in seen:
                    seen.add(key)
                    unique_permissions.append(perm)
            
            conn.close()
            return unique_permissions
            
        except Exception as e:
            logger.error(f"Failed to get user permissions: {e}")
            return []
    
    def _get_role_permissions(self, role_name: str) -> List[Dict[str, Any]]:
        """Get permissions for a specific role including inherited ones."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT permissions, inherits_from FROM roles WHERE name = ?', (role_name,))
            row = cursor.fetchone()
            if not row:
                return []
            
            permissions = json.loads(row[0]) if row[0] else []
            inherits_from = json.loads(row[1]) if row[1] else []
            
            # Get inherited permissions
            inherited_permissions = []
            for inherited_role in inherits_from:
                inherited_perms = self._get_role_permissions(inherited_role)
                inherited_permissions.extend(inherited_perms)
            
            # Combine permissions
            all_permissions = permissions + inherited_permissions
            
            conn.close()
            return all_permissions
            
        except Exception as e:
            logger.error(f"Failed to get role permissions: {e}")
            return []
    
    def check_permission(self, user_id: str, resource_type: str, action: str, 
                        resource_id: str = None, context: Dict[str, Any] = None) -> bool:
        """Check if user has permission for specific action on resource."""
        try:
            user_permissions = self._get_user_permissions(user_id)
            
            for permission in user_permissions:
                if (permission['resource_type'] == resource_type and 
                    permission['action'] == action):
                    
                    # Check permission level
                    level = permission['level']
                    if level == PermissionLevel.GLOBAL:
                        return True
                    elif level == PermissionLevel.OWN:
                        # Check if user owns the resource
                        if self._user_owns_resource(user_id, resource_type, resource_id):
                            return True
                    elif level == PermissionLevel.PROJECT:
                        # Check if user has project access
                        if self._user_has_project_access(user_id, resource_type, resource_id):
                            return True
                    elif level == PermissionLevel.ORGANIZATION:
                        # Check if user has organization access
                        if self._user_has_organization_access(user_id, resource_type, resource_id):
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check permission: {e}")
            return False
    
    def _user_owns_resource(self, user_id: str, resource_type: str, resource_id: str) -> bool:
        """Check if user owns the resource."""
        # This would need to be implemented based on your data model
        # For now, return True as a placeholder
        return True
    
    def _user_has_project_access(self, user_id: str, resource_type: str, resource_id: str) -> bool:
        """Check if user has project-level access to resource."""
        # This would need to be implemented based on your data model
        # For now, return True as a placeholder
        return True
    
    def _user_has_organization_access(self, user_id: str, resource_type: str, resource_id: str) -> bool:
        """Check if user has organization-level access to resource."""
        # This would need to be implemented based on your data model
        # For now, return True as a placeholder
        return True
    
    def log_audit_event(self, user_id: str, action: str, resource_type: str, 
                       resource_id: str, details: Dict[str, Any], ip_address: str, 
                       user_agent: str, success: bool = True):
        """Log an audit event."""
        try:
            audit_id = str(uuid.uuid4())
            audit_log = AuditLog(
                id=audit_id,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                success=success
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audit_logs (
                    id, user_id, action, resource_type, resource_id,
                    details, ip_address, user_agent, timestamp, success
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                audit_log.id, audit_log.user_id, audit_log.action,
                audit_log.resource_type, audit_log.resource_id,
                json.dumps(audit_log.details), audit_log.ip_address,
                audit_log.user_agent, audit_log.timestamp.isoformat(),
                audit_log.success
            ))
            
            conn.commit()
            conn.close()
            
            self.log_info(f"Audit event logged: {action} on {resource_type}:{resource_id}")
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def get_audit_logs(self, user_id: str = None, action: str = None, 
                      resource_type: str = None, start_date: datetime = None,
                      end_date: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs with optional filters."""
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
            
            audit_logs = []
            for row in rows:
                audit_log = {
                    "id": row[0],
                    "user_id": row[1],
                    "action": row[2],
                    "resource_type": row[3],
                    "resource_id": row[4],
                    "details": json.loads(row[5]),
                    "ip_address": row[6],
                    "user_agent": row[7],
                    "timestamp": row[8],
                    "success": bool(row[9])
                }
                audit_logs.append(audit_log)
            
            conn.close()
            return audit_logs
            
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []
    
    def create_session(self, user_id: str, token: str, ip_address: str = None, 
                      user_agent: str = None) -> str:
        """Create a new user session."""
        try:
            session_id = str(uuid.uuid4())
            created_at = datetime.utcnow()
            expires_at = created_at + timedelta(hours=24)  # 24-hour session
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_sessions (
                    session_id, user_id, token, created_at, expires_at,
                    ip_address, user_agent, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id, user_id, token, created_at.isoformat(),
                expires_at.isoformat(), ip_address, user_agent, True
            ))
            
            conn.commit()
            conn.close()
            
            self.log_info(f"Created session for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None
    
    def validate_session(self, session_id: str) -> Dict[str, Any]:
        """Validate a user session."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM user_sessions 
                WHERE session_id = ? AND is_active = TRUE AND expires_at > ?
            ''', (session_id, datetime.utcnow().isoformat()))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return {"valid": False, "message": "Session not found or expired"}
            
            return {
                "valid": True,
                "user_id": row[1],
                "token": row[2],
                "created_at": row[3],
                "expires_at": row[4],
                "ip_address": row[5],
                "user_agent": row[6]
            }
            
        except Exception as e:
            logger.error(f"Failed to validate session: {e}")
            return {"valid": False, "message": "Session validation failed"}
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke a user session."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_sessions 
                SET is_active = FALSE 
                WHERE session_id = ?
            ''', (session_id,))
            
            conn.commit()
            conn.close()
            
            self.log_info(f"Revoked session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke session: {e}")
            return False

# Global access control service instance
access_control_service = AccessControlService() 
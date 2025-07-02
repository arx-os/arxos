"""
Access Control Service
Handles role-based permissions, floor-specific access controls, audit trails, and permission inheritance
"""

import json
import sqlite3
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid
from pathlib import Path

from arx_svg_parser.utils.base_manager import BaseManager
from arx_svg_parser.utils.base_service import BaseService

logger = logging.getLogger(__name__)

class PermissionLevel(Enum):
    """Permission levels"""
    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3
    OWNER = 4

class ResourceType(Enum):
    """Resource types"""
    FLOOR = "floor"
    BUILDING = "building"
    VERSION = "version"
    BRANCH = "branch"
    ANNOTATION = "annotation"
    COMMENT = "comment"
    ASSET = "asset"
    CMMS = "cmms"
    EXPORT = "export"
    IMPORT = "import"

class ActionType(Enum):
    """Action types for audit trail"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    MERGE = "merge"
    BRANCH = "branch"
    ANNOTATE = "annotate"
    COMMENT = "comment"
    APPROVE = "approve"
    REJECT = "reject"
    ASSIGN = "assign"
    TRANSFER = "transfer"

class UserRole(Enum):
    """User roles based on ARXOS flowchart"""
    CONTRACTOR = "contractor"
    INSPECTOR = "inspector"
    TENANT = "tenant"
    TEAM = "team"
    OWNERSHIP = "ownership"
    MANAGEMENT = "management"
    ADMIN = "admin"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    STAKEHOLDER = "stakeholder"
    DATA_CONSUMER = "data_consumer"
    CONSTRUCTION_FIRM = "construction_firm"
    JURISDICTION = "jurisdiction"
    BIM_USER = "bim_user"

@dataclass
class Permission:
    """Permission definition"""
    permission_id: str
    role: UserRole
    resource_type: ResourceType
    resource_id: Optional[str] = None
    permission_level: PermissionLevel = PermissionLevel.READ
    floor_id: Optional[str] = None
    building_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class User:
    """User information"""
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
    """Audit log entry"""
    log_id: str
    user_id: str
    action: ActionType
    resource_type: ResourceType
    resource_id: str
    floor_id: Optional[str] = None
    building_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class RoleHierarchy:
    """Role hierarchy for permission inheritance"""
    role: UserRole
    inherits_from: List[UserRole] = field(default_factory=list)
    permissions: List[Permission] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class AccessControlService(BaseManager, BaseService):
    """Access control service"""
    
    def __init__(self, db_path: str = "./data/access_control.db"):
        BaseManager.__init__(self, logger=logger)
        BaseService.__init__(self, manager=self)
        self.db_path = db_path
        self.init_database()
        self.init_role_hierarchy()
        
        # Custom metrics for access control
        self.metrics = {
            'permission_checks': 0,
            'permission_grants': 0,
            'permission_revokes': 0,
            'audit_events': 0,
            'user_creations': 0
        }
    
    def init_database(self):
        """Initialize access control database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
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
                is_active INTEGER DEFAULT 1,
                metadata TEXT
            )
        ''')
        
        # Create permissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                permission_id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                permission_level INTEGER NOT NULL,
                floor_id TEXT,
                building_id TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                metadata TEXT
            )
        ''')
        
        # Create audit_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                floor_id TEXT,
                building_id TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TEXT NOT NULL,
                success INTEGER DEFAULT 1,
                error_message TEXT
            )
        ''')
        
        # Create role_hierarchy table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_hierarchy (
                role TEXT PRIMARY KEY,
                inherits_from TEXT,
                permissions TEXT,
                metadata TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_permissions_role ON permissions(role)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource_type, resource_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_permissions_floor ON permissions(floor_id, building_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id)')
        
        conn.commit()
        conn.close()
    
    def init_role_hierarchy(self):
        """Initialize role hierarchy and default permissions"""
        # Define role inheritance
        hierarchy = {
            UserRole.OWNER: {
                "inherits_from": [],
                "permissions": [
                    {"resource_type": ResourceType.FLOOR, "level": PermissionLevel.OWNER},
                    {"resource_type": ResourceType.BUILDING, "level": PermissionLevel.OWNER},
                    {"resource_type": ResourceType.VERSION, "level": PermissionLevel.OWNER},
                    {"resource_type": ResourceType.BRANCH, "level": PermissionLevel.OWNER},
                    {"resource_type": ResourceType.ANNOTATION, "level": PermissionLevel.OWNER},
                    {"resource_type": ResourceType.COMMENT, "level": PermissionLevel.OWNER},
                    {"resource_type": ResourceType.ASSET, "level": PermissionLevel.OWNER},
                    {"resource_type": ResourceType.CMMS, "level": PermissionLevel.OWNER},
                    {"resource_type": ResourceType.EXPORT, "level": PermissionLevel.OWNER},
                    {"resource_type": ResourceType.IMPORT, "level": PermissionLevel.OWNER}
                ]
            },
            UserRole.ADMIN: {
                "inherits_from": [UserRole.MANAGEMENT],
                "permissions": [
                    {"resource_type": ResourceType.FLOOR, "level": PermissionLevel.ADMIN},
                    {"resource_type": ResourceType.BUILDING, "level": PermissionLevel.ADMIN},
                    {"resource_type": ResourceType.VERSION, "level": PermissionLevel.ADMIN},
                    {"resource_type": ResourceType.BRANCH, "level": PermissionLevel.ADMIN},
                    {"resource_type": ResourceType.ANNOTATION, "level": PermissionLevel.ADMIN},
                    {"resource_type": ResourceType.COMMENT, "level": PermissionLevel.ADMIN},
                    {"resource_type": ResourceType.ASSET, "level": PermissionLevel.ADMIN},
                    {"resource_type": ResourceType.CMMS, "level": PermissionLevel.ADMIN},
                    {"resource_type": ResourceType.EXPORT, "level": PermissionLevel.ADMIN},
                    {"resource_type": ResourceType.IMPORT, "level": PermissionLevel.ADMIN}
                ]
            },
            UserRole.MANAGEMENT: {
                "inherits_from": [UserRole.ARCHITECT, UserRole.ENGINEER],
                "permissions": [
                    {"resource_type": ResourceType.FLOOR, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.BUILDING, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.VERSION, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.BRANCH, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.ANNOTATION, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.COMMENT, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.ASSET, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.CMMS, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.EXPORT, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.IMPORT, "level": PermissionLevel.READ}
                ]
            },
            UserRole.ARCHITECT: {
                "inherits_from": [UserRole.ENGINEER],
                "permissions": [
                    {"resource_type": ResourceType.FLOOR, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.BUILDING, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.VERSION, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.BRANCH, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.ANNOTATION, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.COMMENT, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.ASSET, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.CMMS, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.EXPORT, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.IMPORT, "level": PermissionLevel.READ}
                ]
            },
            UserRole.ENGINEER: {
                "inherits_from": [UserRole.CONTRACTOR],
                "permissions": [
                    {"resource_type": ResourceType.FLOOR, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.BUILDING, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.VERSION, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.BRANCH, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.ANNOTATION, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.COMMENT, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.ASSET, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.CMMS, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.EXPORT, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.IMPORT, "level": PermissionLevel.NONE}
                ]
            },
            UserRole.CONTRACTOR: {
                "inherits_from": [UserRole.INSPECTOR],
                "permissions": [
                    {"resource_type": ResourceType.FLOOR, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.BUILDING, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.VERSION, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.BRANCH, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.ANNOTATION, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.COMMENT, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.ASSET, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.CMMS, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.EXPORT, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.IMPORT, "level": PermissionLevel.NONE}
                ]
            },
            UserRole.INSPECTOR: {
                "inherits_from": [UserRole.TENANT],
                "permissions": [
                    {"resource_type": ResourceType.FLOOR, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.BUILDING, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.VERSION, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.BRANCH, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.ANNOTATION, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.COMMENT, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.ASSET, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.CMMS, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.EXPORT, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.IMPORT, "level": PermissionLevel.NONE}
                ]
            },
            UserRole.TENANT: {
                "inherits_from": [UserRole.TEAM],
                "permissions": [
                    {"resource_type": ResourceType.FLOOR, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.BUILDING, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.VERSION, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.BRANCH, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.ANNOTATION, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.COMMENT, "level": PermissionLevel.WRITE},
                    {"resource_type": ResourceType.ASSET, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.CMMS, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.EXPORT, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.IMPORT, "level": PermissionLevel.NONE}
                ]
            },
            UserRole.TEAM: {
                "inherits_from": [],
                "permissions": [
                    {"resource_type": ResourceType.FLOOR, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.BUILDING, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.VERSION, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.BRANCH, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.ANNOTATION, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.COMMENT, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.ASSET, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.CMMS, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.EXPORT, "level": PermissionLevel.READ},
                    {"resource_type": ResourceType.IMPORT, "level": PermissionLevel.NONE}
                ]
            }
        }
        
        # Save hierarchy to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for role, config in hierarchy.items():
            cursor.execute('''
                INSERT OR REPLACE INTO role_hierarchy (
                    role, inherits_from, permissions, metadata
                ) VALUES (?, ?, ?, ?)
            ''', (
                role.value,
                json.dumps([r.value for r in config["inherits_from"]]),
                json.dumps(config["permissions"]),
                json.dumps({})
            ))
        
        conn.commit()
        conn.close()
    
    def create_user(self, username: str, email: str, primary_role: UserRole,
                   secondary_roles: List[UserRole] = None, organization: str = "") -> Dict[str, Any]:
        """Create a new user"""
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
        """Get user information"""
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
            
            conn.close()
            return {"success": True, "user": user}
            
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return {"success": False, "message": str(e)}
    
    def check_permission(self, user_id: str, resource_type: ResourceType,
                        action: ActionType, resource_id: str = None,
                        floor_id: str = None, building_id: str = None) -> Dict[str, Any]:
        """Check if user has permission for an action"""
        try:
            # Get user information
            user_result = self.get_user(user_id)
            if not user_result["success"]:
                return {"success": False, "message": "User not found"}
            
            user = user_result["user"]
            user_roles = [UserRole(user["primary_role"])] + [UserRole(r) for r in user["secondary_roles"]]
            
            # Get required permission level for action
            required_level = self._get_required_permission_level(action)
            
            # Check permissions for all user roles
            for role in user_roles:
                permission = self._get_role_permission(role, resource_type, resource_id, floor_id, building_id)
                if permission and permission.permission_level.value >= required_level.value:
                    return {"success": True, "permission": permission}
            
            return {"success": False, "message": "Insufficient permissions"}
            
        except Exception as e:
            logger.error(f"Failed to check permission: {e}")
            return {"success": False, "message": str(e)}
    
    def grant_permission(self, role: UserRole, resource_type: ResourceType,
                        permission_level: PermissionLevel, resource_id: str = None,
                        floor_id: str = None, building_id: str = None,
                        expires_at: datetime = None) -> Dict[str, Any]:
        """Grant permission to a role"""
        try:
            permission = Permission(
                permission_id=str(uuid.uuid4()),
                role=role,
                resource_type=resource_type,
                resource_id=resource_id,
                permission_level=permission_level,
                floor_id=floor_id,
                building_id=building_id,
                expires_at=expires_at
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO permissions (
                    permission_id, role, resource_type, resource_id,
                    permission_level, floor_id, building_id, created_at,
                    expires_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                permission.permission_id, permission.role.value,
                permission.resource_type.value, permission.resource_id,
                permission.permission_level.value, permission.floor_id,
                permission.building_id, permission.created_at.isoformat(),
                permission.expires_at.isoformat() if permission.expires_at else None,
                json.dumps(permission.metadata)
            ))
            
            conn.commit()
            conn.close()
            
            self.log_info(f"Granted {permission_level.value} permission to {role.value} for {resource_type.value}")
        
            # Record metrics
            self.metrics['permission_grants'] += 1
            self.record_metric('permission_grant', 1, {
                'role': role.value,
                'resource_type': resource_type.value,
                'permission_level': permission_level.value
            })
            
            return {"success": True, "permission_id": permission.permission_id}
            
        except Exception as e:
            logger.error(f"Failed to grant permission: {e}")
            return {"success": False, "message": str(e)}
    
    def revoke_permission(self, permission_id: str) -> Dict[str, Any]:
        """Revoke a permission"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM permissions WHERE permission_id = ?', (permission_id,))
            
            if cursor.rowcount == 0:
                return {"success": False, "message": "Permission not found"}
            
            conn.commit()
            conn.close()
            
            self.log_info(f"Revoked permission {permission_id}")
            return {"success": True, "permission_id": permission_id}
            
        except Exception as e:
            logger.error(f"Failed to revoke permission: {e}")
            return {"success": False, "message": str(e)}
    
    def log_audit_event(self, user_id: str, action: ActionType, resource_type: ResourceType,
                       resource_id: str, floor_id: str = None, building_id: str = None,
                       details: Dict[str, Any] = None, ip_address: str = None,
                       user_agent: str = None, success: bool = True,
                       error_message: str = None) -> Dict[str, Any]:
        """Log an audit event"""
        try:
            audit_log = AuditLog(
                log_id=str(uuid.uuid4()),
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                floor_id=floor_id,
                building_id=building_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audit_logs (
                    log_id, user_id, action, resource_type, resource_id,
                    floor_id, building_id, details, ip_address, user_agent,
                    timestamp, success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                audit_log.log_id, audit_log.user_id, audit_log.action.value,
                audit_log.resource_type.value, audit_log.resource_id,
                audit_log.floor_id, audit_log.building_id,
                json.dumps(audit_log.details), audit_log.ip_address,
                audit_log.user_agent, audit_log.timestamp.isoformat(),
                audit_log.success, audit_log.error_message
            ))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "log_id": audit_log.log_id}
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return {"success": False, "message": str(e)}
    
    def get_audit_logs(self, user_id: str = None, resource_type: ResourceType = None,
                      resource_id: str = None, start_date: datetime = None,
                      end_date: datetime = None, limit: int = 100) -> Dict[str, Any]:
        """Get audit logs with filters"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if resource_type:
                query += " AND resource_type = ?"
                params.append(resource_type.value)
            
            if resource_id:
                query += " AND resource_id = ?"
                params.append(resource_id)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            logs = []
            for row in cursor.fetchall():
                log = {
                    "log_id": row[0],
                    "user_id": row[1],
                    "action": row[2],
                    "resource_type": row[3],
                    "resource_id": row[4],
                    "floor_id": row[5],
                    "building_id": row[6],
                    "details": json.loads(row[7]) if row[7] else {},
                    "ip_address": row[8],
                    "user_agent": row[9],
                    "timestamp": row[10],
                    "success": bool(row[11]),
                    "error_message": row[12]
                }
                logs.append(log)
            
            conn.close()
            return {"success": True, "logs": logs}
            
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return {"success": False, "message": str(e)}
    
    def get_floor_permissions(self, floor_id: str, building_id: str) -> Dict[str, Any]:
        """Get all permissions for a specific floor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM permissions 
                WHERE floor_id = ? AND building_id = ?
                ORDER BY role, resource_type
            ''', (floor_id, building_id))
            
            permissions = []
            for row in cursor.fetchall():
                permission = {
                    "permission_id": row[0],
                    "role": row[1],
                    "resource_type": row[2],
                    "resource_id": row[3],
                    "permission_level": row[4],
                    "floor_id": row[5],
                    "building_id": row[6],
                    "created_at": row[7],
                    "expires_at": row[8],
                    "metadata": json.loads(row[9]) if row[9] else {}
                }
                permissions.append(permission)
            
            conn.close()
            return {"success": True, "permissions": permissions}
            
        except Exception as e:
            logger.error(f"Failed to get floor permissions: {e}")
            return {"success": False, "message": str(e)}
    
    def _get_required_permission_level(self, action: ActionType) -> PermissionLevel:
        """Get required permission level for an action"""
        action_levels = {
            ActionType.READ: PermissionLevel.READ,
            ActionType.CREATE: PermissionLevel.WRITE,
            ActionType.UPDATE: PermissionLevel.WRITE,
            ActionType.DELETE: PermissionLevel.ADMIN,
            ActionType.EXPORT: PermissionLevel.READ,
            ActionType.IMPORT: PermissionLevel.WRITE,
            ActionType.MERGE: PermissionLevel.WRITE,
            ActionType.BRANCH: PermissionLevel.WRITE,
            ActionType.ANNOTATE: PermissionLevel.WRITE,
            ActionType.COMMENT: PermissionLevel.WRITE,
            ActionType.APPROVE: PermissionLevel.ADMIN,
            ActionType.REJECT: PermissionLevel.ADMIN,
            ActionType.ASSIGN: PermissionLevel.ADMIN,
            ActionType.TRANSFER: PermissionLevel.ADMIN
        }
        return action_levels.get(action, PermissionLevel.ADMIN)
    
    def _get_role_permission(self, role: UserRole, resource_type: ResourceType,
                            resource_id: str = None, floor_id: str = None,
                            building_id: str = None) -> Optional[Permission]:
        """Get permission for a role and resource"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First check for specific resource permission
            if resource_id:
                cursor.execute('''
                    SELECT * FROM permissions 
                    WHERE role = ? AND resource_type = ? AND resource_id = ?
                    AND (expires_at IS NULL OR expires_at > ?)
                    ORDER BY permission_level DESC
                    LIMIT 1
                ''', (role.value, resource_type.value, resource_id, datetime.utcnow().isoformat()))
                
                row = cursor.fetchone()
                if row:
                    conn.close()
                    return self._row_to_permission(row)
            
            # Check for floor-specific permission
            if floor_id and building_id:
                cursor.execute('''
                    SELECT * FROM permissions 
                    WHERE role = ? AND resource_type = ? AND floor_id = ? AND building_id = ?
                    AND (expires_at IS NULL OR expires_at > ?)
                    ORDER BY permission_level DESC
                    LIMIT 1
                ''', (role.value, resource_type.value, floor_id, building_id, datetime.utcnow().isoformat()))
                
                row = cursor.fetchone()
                if row:
                    conn.close()
                    return self._row_to_permission(row)
            
            # Check for general resource type permission
            cursor.execute('''
                SELECT * FROM permissions 
                WHERE role = ? AND resource_type = ? AND resource_id IS NULL 
                AND floor_id IS NULL AND building_id IS NULL
                AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY permission_level DESC
                LIMIT 1
            ''', (role.value, resource_type.value, datetime.utcnow().isoformat()))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return self._row_to_permission(row)
            
            # Check inherited permissions
            return self._get_inherited_permission(role, resource_type, resource_id, floor_id, building_id)
            
        except Exception as e:
            logger.error(f"Failed to get role permission: {e}")
            return None
    
    def _get_inherited_permission(self, role: UserRole, resource_type: ResourceType,
                                 resource_id: str = None, floor_id: str = None,
                                 building_id: str = None) -> Optional[Permission]:
        """Get inherited permission from parent roles"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT inherits_from FROM role_hierarchy WHERE role = ?', (role.value,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
            
            inherits_from = json.loads(row[0]) if row[0] else []
            
            for parent_role in inherits_from:
                permission = self._get_role_permission(UserRole(parent_role), resource_type, resource_id, floor_id, building_id)
                if permission:
                    conn.close()
                    return permission
            
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get inherited permission: {e}")
            return None
    
    def _row_to_permission(self, row) -> Permission:
        """Convert database row to Permission object"""
        return Permission(
            permission_id=row[0],
            role=UserRole(row[1]),
            resource_type=ResourceType(row[2]),
            resource_id=row[3],
            permission_level=PermissionLevel(row[4]),
            floor_id=row[5],
            building_id=row[6],
            created_at=datetime.fromisoformat(row[7]),
            expires_at=datetime.fromisoformat(row[8]) if row[8] else None,
            metadata=json.loads(row[9]) if row[9] else {}
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get access control metrics"""
        return {
            'metrics': self.metrics.copy(),
            'timestamp': datetime.utcnow().isoformat()
        }

# Global service instance - lazy singleton
_access_control_service = None

def get_access_control_service() -> AccessControlService:
    """Get the global access control service instance (lazy singleton)"""
    global _access_control_service
    if _access_control_service is None:
        _access_control_service = AccessControlService()
    return _access_control_service

# For backward compatibility - will be initialized when first accessed
access_control_service = None 
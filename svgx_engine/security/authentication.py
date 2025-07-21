"""
Authentication and Authorization Services for Arxos.

This module implements enterprise-grade authentication and authorization
with support for RBAC (Role-Based Access Control) and ABAC (Attribute-Based Access Control).
"""

import jwt
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import bcrypt
from cryptography.fernet import Fernet


class UserRole(Enum):
    """User roles for RBAC implementation."""
    ADMIN = "admin"
    ENGINEER = "engineer"
    VIEWER = "viewer"
    CONTRACTOR = "contractor"
    GUEST = "guest"


class Permission(Enum):
    """Permissions for resource access control."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"
    VIEW_AUDIT_LOGS = "view_audit_logs"


@dataclass
class User:
    """User entity with attributes for ABAC."""
    id: str
    username: str
    email: str
    roles: List[UserRole]
    attributes: Dict[str, Any]
    is_active: bool = True
    created_at: datetime = None
    last_login: datetime = None


@dataclass
class Resource:
    """Resource entity for access control."""
    id: str
    type: str
    attributes: Dict[str, Any]
    owner_id: str
    created_at: datetime = None


class AuthService:
    """Main authentication service with JWT token management."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expiry = timedelta(hours=24)
        self.refresh_token_expiry = timedelta(days=7)
        
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def generate_token(self, user: User) -> str:
        """Generate JWT token for user."""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'roles': [role.value for role in user.roles],
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(32)
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    def refresh_token(self, refresh_token: str) -> str:
        """Generate new access token from refresh token."""
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            # Create new user object from payload
            user = User(
                id=payload['user_id'],
                username=payload['username'],
                email="",  # Not stored in token for security
                roles=[UserRole(role) for role in payload['roles']],
                attributes={}
            )
            return self.generate_token(user)
        except jwt.InvalidTokenError:
            raise ValueError("Invalid refresh token")


class RBACService:
    """Role-Based Access Control implementation."""
    
    def __init__(self):
        self.role_permissions = {
            UserRole.ADMIN: [
                Permission.READ, Permission.WRITE, Permission.DELETE,
                Permission.MANAGE_USERS, Permission.MANAGE_SYSTEM,
                Permission.EXPORT_DATA, Permission.IMPORT_DATA,
                Permission.VIEW_AUDIT_LOGS
            ],
            UserRole.ENGINEER: [
                Permission.READ, Permission.WRITE, Permission.EXPORT_DATA,
                Permission.IMPORT_DATA
            ],
            UserRole.VIEWER: [
                Permission.READ
            ],
            UserRole.CONTRACTOR: [
                Permission.READ, Permission.LIMITED_WRITE
            ],
            UserRole.GUEST: [
                Permission.READ
            ]
        }
    
    def check_permission(self, user: User, permission: Permission) -> bool:
        """Check if user has specific permission."""
        for role in user.roles:
            if permission in self.role_permissions.get(role, []):
                return True
        return False
    
    def get_user_permissions(self, user: User) -> List[Permission]:
        """Get all permissions for a user."""
        permissions = set()
        for role in user.roles:
            permissions.update(self.role_permissions.get(role, []))
        return list(permissions)
    
    def add_role_permission(self, role: UserRole, permission: Permission):
        """Add permission to a role."""
        if role not in self.role_permissions:
            self.role_permissions[role] = []
        if permission not in self.role_permissions[role]:
            self.role_permissions[role].append(permission)
    
    def remove_role_permission(self, role: UserRole, permission: Permission):
        """Remove permission from a role."""
        if role in self.role_permissions and permission in self.role_permissions[role]:
            self.role_permissions[role].remove(permission)


class ABACService:
    """Attribute-Based Access Control implementation."""
    
    def __init__(self):
        self.policies = []
    
    def add_policy(self, policy: Dict[str, Any]):
        """Add an ABAC policy."""
        self.policies.append(policy)
    
    def check_access(self, user: User, resource: Resource, action: str, context: Dict[str, Any] = None) -> bool:
        """Check access using ABAC policies."""
        context = context or {}
        
        for policy in self.policies:
            if self._evaluate_policy(policy, user, resource, action, context):
                return policy.get('effect', 'deny') == 'allow'
        
        return False  # Default deny
    
    def _evaluate_policy(self, policy: Dict[str, Any], user: User, resource: Resource, action: str, context: Dict[str, Any]) -> bool:
        """Evaluate a single ABAC policy."""
        conditions = policy.get('conditions', {})
        
        # Check user attributes
        for attr, value in conditions.get('user_attributes', {}).items():
            if user.attributes.get(attr) != value:
                return False
        
        # Check resource attributes
        for attr, value in conditions.get('resource_attributes', {}).items():
            if resource.attributes.get(attr) != value:
                return False
        
        # Check action
        if 'action' in conditions and action not in conditions['action']:
            return False
        
        # Check context
        for key, value in conditions.get('context', {}).items():
            if context.get(key) != value:
                return False
        
        return True
    
    def create_policy(self, name: str, effect: str, conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new ABAC policy."""
        return {
            'name': name,
            'effect': effect,
            'conditions': conditions
        }


class SessionManager:
    """Session management for security."""
    
    def __init__(self):
        self.active_sessions = {}
        self.session_timeout = timedelta(hours=8)
    
    def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """Create a new session."""
        session_id = secrets.token_urlsafe(32)
        session = {
            'user_id': user_id,
            'data': session_data,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow()
        }
        self.active_sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        # Check session timeout
        if datetime.utcnow() - session['last_activity'] > self.session_timeout:
            self.remove_session(session_id)
            return None
        
        # Update last activity
        session['last_activity'] = datetime.utcnow()
        return session
    
    def remove_session(self, session_id: str):
        """Remove a session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        current_time = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if current_time - session['last_activity'] > self.session_timeout
        ]
        for session_id in expired_sessions:
            self.remove_session(session_id)


class MultiFactorAuth:
    """Multi-factor authentication implementation."""
    
    def __init__(self):
        self.totp_secrets = {}
    
    def generate_totp_secret(self, user_id: str) -> str:
        """Generate TOTP secret for user."""
        secret = secrets.token_urlsafe(32)
        self.totp_secrets[user_id] = secret
        return secret
    
    def verify_totp(self, user_id: str, totp_code: str) -> bool:
        """Verify TOTP code."""
        secret = self.totp_secrets.get(user_id)
        if not secret:
            return False
        
        # Simple TOTP verification (in production, use proper TOTP library)
        expected_code = self._generate_totp_code(secret)
        return totp_code == expected_code
    
    def _generate_totp_code(self, secret: str) -> str:
        """Generate TOTP code (simplified implementation)."""
        # In production, use proper TOTP implementation
        import time
        timestamp = int(time.time() // 30)
        hash_input = f"{secret}{timestamp}".encode()
        hash_result = hashlib.sha256(hash_input).hexdigest()
        return hash_result[:6]  # 6-digit code 
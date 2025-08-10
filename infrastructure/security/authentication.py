"""
Enterprise Authentication and Authorization System.

Provides secure authentication, token management, and role-based access control
following security best practices and compliance requirements.
"""

import jwt
import bcrypt
import hashlib
import secrets
import time
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from enum import Enum
import re
from functools import wraps

from infrastructure.logging.structured_logging import get_logger, security_logger
from infrastructure.error_handling import SecurityError
from domain.value_objects import UserId, Email


logger = get_logger(__name__)


class UserRole(Enum):
    """User roles for authorization."""
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"
    GUEST = "guest"


class Permission(Enum):
    """System permissions for fine-grained access control."""
    # Building permissions
    CREATE_BUILDING = "create_building"
    READ_BUILDING = "read_building"
    UPDATE_BUILDING = "update_building"
    DELETE_BUILDING = "delete_building"
    
    # Floor permissions
    CREATE_FLOOR = "create_floor"
    READ_FLOOR = "read_floor"
    UPDATE_FLOOR = "update_floor"
    DELETE_FLOOR = "delete_floor"
    
    # Room permissions
    CREATE_ROOM = "create_room"
    READ_ROOM = "read_room"
    UPDATE_ROOM = "update_room"
    DELETE_ROOM = "delete_room"
    
    # Device permissions
    CREATE_DEVICE = "create_device"
    READ_DEVICE = "read_device"
    UPDATE_DEVICE = "update_device"
    DELETE_DEVICE = "delete_device"
    CONTROL_DEVICE = "control_device"
    
    # User management permissions
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    MANAGE_ROLES = "manage_roles"
    
    # System permissions
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_SYSTEM = "manage_system"
    EXPORT_DATA = "export_data"


@dataclass
class AuthenticationToken:
    """Secure authentication token with metadata."""
    user_id: str
    username: str
    email: str
    roles: List[UserRole]
    permissions: List[Permission]
    issued_at: datetime
    expires_at: datetime
    token_id: str
    session_id: str
    client_info: Dict[str, Any]
    
    def is_valid(self) -> bool:
        """Check if token is still valid."""
        return datetime.now(timezone.utc) < self.expires_at
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if token has specific permission."""
        return permission in self.permissions
    
    def has_role(self, role: UserRole) -> bool:
        """Check if token has specific role."""
        return role in self.roles


class PasswordPolicy:
    """Enterprise password policy enforcement."""
    
    MIN_LENGTH = 12
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    PREVENT_COMMON_PASSWORDS = True
    PREVENT_USER_INFO_IN_PASSWORD = True
    
    # Common passwords to reject
    COMMON_PASSWORDS = {
        "password", "password123", "admin", "administrator", 
        "root", "user", "guest", "default", "qwerty",
        "123456", "password1", "welcome", "login"
    }
    
    @classmethod
    def validate_password(cls, password: str, username: str = None, 
                         email: str = None) -> Tuple[bool, List[str]]:
        """Validate password against policy."""
        errors = []
        
        # Length checks
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")
        if len(password) > cls.MAX_LENGTH:
            errors.append(f"Password must be no more than {cls.MAX_LENGTH} characters long")
        
        # Character composition checks
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        if cls.REQUIRE_NUMBERS and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        if cls.REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*()_+=\-\[\]{}|;:,.<>?]', password):
            errors.append("Password must contain at least one special character")
        
        # Common password check
        if cls.PREVENT_COMMON_PASSWORDS and password.lower() in cls.COMMON_PASSWORDS:
            errors.append("Password is too common and easily guessable")
        
        # User information check
        if cls.PREVENT_USER_INFO_IN_PASSWORD:
            if username and username.lower() in password.lower():
                errors.append("Password must not contain username")
            if email and email.split('@')[0].lower() in password.lower():
                errors.append("Password must not contain email address")
        
        return len(errors) == 0, errors


class SecurePasswordManager:
    """Secure password hashing and verification."""
    
    # Use bcrypt with high cost factor for security
    BCRYPT_ROUNDS = 12
    
    @classmethod
    def hash_password(cls, password: str, salt: Optional[bytes] = None) -> str:
        """Hash password securely using bcrypt."""
        if salt is None:
            salt = bcrypt.gensalt(rounds=cls.BCRYPT_ROUNDS)
        
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @classmethod
    def generate_secure_password(cls, length: int = 16) -> str:
        """Generate cryptographically secure password."""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))


class JWTTokenManager:
    """JSON Web Token management with security features."""
    
    def __init__(self, secret_key: str, issuer: str = "arxos"):
        self.secret_key = secret_key
        self.issuer = issuer
        self.algorithm = "HS256"
        self.access_token_lifetime = timedelta(hours=1)
        self.refresh_token_lifetime = timedelta(days=7)
    
    def create_access_token(self, auth_token: AuthenticationToken) -> str:
        """Create JWT access token."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": auth_token.user_id,
            "username": auth_token.username,
            "email": auth_token.email,
            "roles": [role.value for role in auth_token.roles],
            "permissions": [perm.value for perm in auth_token.permissions],
            "iat": now.timestamp(),
            "exp": (now + self.access_token_lifetime).timestamp(),
            "iss": self.issuer,
            "jti": auth_token.token_id,
            "sid": auth_token.session_id,
            "typ": "access"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        security_logger.log_security_event(
            event_type="token_created",
            user_id=auth_token.user_id,
            details={
                "token_type": "access",
                "token_id": auth_token.token_id,
                "expires_at": payload["exp"]
            }
        )
        
        return token
    
    def create_refresh_token(self, auth_token: AuthenticationToken) -> str:
        """Create JWT refresh token."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": auth_token.user_id,
            "iat": now.timestamp(),
            "exp": (now + self.refresh_token_lifetime).timestamp(),
            "iss": self.issuer,
            "jti": f"{auth_token.token_id}_refresh",
            "sid": auth_token.session_id,
            "typ": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                issuer=self.issuer
            )
            
            # Check if token is expired
            if payload["exp"] < datetime.now(timezone.utc).timestamp():
                security_logger.log_security_event(
                    event_type="token_expired",
                    user_id=payload.get("sub"),
                    details={"token_type": payload.get("typ")}
                )
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            security_logger.log_security_event(
                event_type="token_expired",
                details={"error": "signature_expired"}
            )
            return None
        except jwt.InvalidTokenError as e:
            security_logger.log_security_event(
                event_type="token_invalid",
                details={"error": str(e)}
            )
            return None
    
    def revoke_token(self, token_id: str, user_id: str) -> None:
        """Revoke a token (implement with token blacklist)."""
        security_logger.log_security_event(
            event_type="token_revoked",
            user_id=user_id,
            details={"token_id": token_id}
        )
        # Implementation would add token_id to blacklist in Redis/database


class RoleBasedAccessControl:
    """Role-based access control system."""
    
    # Define role hierarchies and permissions
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: {
            # Full system access
            Permission.CREATE_BUILDING, Permission.READ_BUILDING, 
            Permission.UPDATE_BUILDING, Permission.DELETE_BUILDING,
            Permission.CREATE_FLOOR, Permission.READ_FLOOR,
            Permission.UPDATE_FLOOR, Permission.DELETE_FLOOR,
            Permission.CREATE_ROOM, Permission.READ_ROOM,
            Permission.UPDATE_ROOM, Permission.DELETE_ROOM,
            Permission.CREATE_DEVICE, Permission.READ_DEVICE,
            Permission.UPDATE_DEVICE, Permission.DELETE_DEVICE, Permission.CONTROL_DEVICE,
            Permission.CREATE_USER, Permission.READ_USER,
            Permission.UPDATE_USER, Permission.DELETE_USER, Permission.MANAGE_ROLES,
            Permission.VIEW_AUDIT_LOGS, Permission.MANAGE_SYSTEM, Permission.EXPORT_DATA
        },
        UserRole.MANAGER: {
            # Management operations
            Permission.CREATE_BUILDING, Permission.READ_BUILDING, Permission.UPDATE_BUILDING,
            Permission.CREATE_FLOOR, Permission.READ_FLOOR, Permission.UPDATE_FLOOR,
            Permission.CREATE_ROOM, Permission.READ_ROOM, Permission.UPDATE_ROOM,
            Permission.CREATE_DEVICE, Permission.READ_DEVICE, 
            Permission.UPDATE_DEVICE, Permission.CONTROL_DEVICE,
            Permission.CREATE_USER, Permission.READ_USER, Permission.UPDATE_USER,
            Permission.EXPORT_DATA
        },
        UserRole.OPERATOR: {
            # Operations and monitoring
            Permission.READ_BUILDING, Permission.UPDATE_BUILDING,
            Permission.READ_FLOOR, Permission.UPDATE_FLOOR,
            Permission.READ_ROOM, Permission.UPDATE_ROOM,
            Permission.READ_DEVICE, Permission.UPDATE_DEVICE, Permission.CONTROL_DEVICE,
            Permission.READ_USER
        },
        UserRole.VIEWER: {
            # Read-only access
            Permission.READ_BUILDING, Permission.READ_FLOOR,
            Permission.READ_ROOM, Permission.READ_DEVICE, Permission.READ_USER
        },
        UserRole.GUEST: {
            # Minimal access
            Permission.READ_BUILDING
        }
    }
    
    @classmethod
    def get_permissions_for_roles(cls, roles: List[UserRole]) -> Set[Permission]:
        """Get all permissions for given roles."""
        permissions = set()
        for role in roles:
            if role in cls.ROLE_PERMISSIONS:
                permissions.update(cls.ROLE_PERMISSIONS[role])
        return permissions
    
    @classmethod
    def can_access_resource(cls, user_roles: List[UserRole], 
                          required_permission: Permission) -> bool:
        """Check if user roles have required permission."""
        user_permissions = cls.get_permissions_for_roles(user_roles)
        return required_permission in user_permissions


class AuthenticationService:
    """Main authentication service."""
    
    def __init__(self, jwt_secret: str, session_manager=None):
        self.password_manager = SecurePasswordManager()
        self.token_manager = JWTTokenManager(jwt_secret)
        self.rbac = RoleBasedAccessControl()
        self.session_manager = session_manager
        
        # Rate limiting for authentication attempts
        self.failed_attempts = {}  # In production, use Redis
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
    
    def authenticate_user(self, username_or_email: str, password: str, 
                         client_info: Dict[str, Any] = None) -> Optional[Tuple[str, str]]:
        """Authenticate user and return access and refresh tokens."""
        # Check rate limiting
        if self._is_rate_limited(username_or_email):
            security_logger.log_security_event(
                event_type="authentication_rate_limited",
                details={"username": username_or_email}
            )
            raise SecurityError("Too many failed attempts. Please try again later.")
        
        try:
            # Get user from database (mock implementation)
            user = self._get_user_by_username_or_email(username_or_email)
            if not user:
                self._record_failed_attempt(username_or_email)
                security_logger.log_security_event(
                    event_type="authentication_failed",
                    details={"username": username_or_email, "reason": "user_not_found"}
                )
                return None
            
            # Verify password
            if not self.password_manager.verify_password(password, user["password_hash"]):
                self._record_failed_attempt(username_or_email)
                security_logger.log_security_event(
                    event_type="authentication_failed",
                    user_id=user["id"],
                    details={"username": username_or_email, "reason": "invalid_password"}
                )
                return None
            
            # Clear failed attempts on successful auth
            self._clear_failed_attempts(username_or_email)
            
            # Create authentication token
            session_id = secrets.token_urlsafe(32)
            token_id = secrets.token_urlsafe(16)
            
            auth_token = AuthenticationToken(
                user_id=user["id"],
                username=user["username"],
                email=user["email"],
                roles=[UserRole(role) for role in user["roles"]],
                permissions=list(self.rbac.get_permissions_for_roles([UserRole(role) for role in user["roles"]])),
                issued_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + self.token_manager.access_token_lifetime,
                token_id=token_id,
                session_id=session_id,
                client_info=client_info or {}
            )
            
            # Create JWT tokens
            access_token = self.token_manager.create_access_token(auth_token)
            refresh_token = self.token_manager.create_refresh_token(auth_token)
            
            # Store session
            if self.session_manager:
                self.session_manager.create_session(session_id, auth_token)
            
            security_logger.log_security_event(
                event_type="authentication_successful",
                user_id=user["id"],
                details={
                    "username": username_or_email,
                    "session_id": session_id,
                    "client_info": client_info
                }
            )
            
            return access_token, refresh_token
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            security_logger.log_security_event(
                event_type="authentication_error",
                details={"username": username_or_email, "error": str(e)}
            )
            raise SecurityError("Authentication failed")
    
    def create_user(self, username: str, email: str, password: str, 
                   roles: List[UserRole], created_by: str) -> str:
        """Create new user with secure password."""
        # Validate password policy
        is_valid, errors = PasswordPolicy.validate_password(password, username, email)
        if not is_valid:
            raise SecurityError(f"Password policy violation: {'; '.join(errors)}")
        
        # Hash password
        password_hash = self.password_manager.hash_password(password)
        
        # Generate user ID
        user_id = secrets.token_urlsafe(16)
        
        # Store user (mock implementation)
        user_data = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "roles": [role.value for role in roles],
            "created_at": datetime.now(timezone.utc),
            "created_by": created_by,
            "is_active": True
        }
        
        security_logger.log_security_event(
            event_type="user_created",
            user_id=user_id,
            details={
                "username": username,
                "email": email,
                "roles": [role.value for role in roles],
                "created_by": created_by
            }
        )
        
        return user_id
    
    def change_password(self, user_id: str, old_password: str, 
                       new_password: str) -> bool:
        """Change user password securely."""
        # Get user
        user = self._get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify old password
        if not self.password_manager.verify_password(old_password, user["password_hash"]):
            security_logger.log_security_event(
                event_type="password_change_failed",
                user_id=user_id,
                details={"reason": "invalid_old_password"}
            )
            return False
        
        # Validate new password
        is_valid, errors = PasswordPolicy.validate_password(
            new_password, user["username"], user["email"]
        )
        if not is_valid:
            raise SecurityError(f"Password policy violation: {'; '.join(errors)}")
        
        # Hash new password
        new_password_hash = self.password_manager.hash_password(new_password)
        
        # Update password (mock implementation)
        # In real implementation, update database
        
        security_logger.log_security_event(
            event_type="password_changed",
            user_id=user_id,
            details={"username": user["username"]}
        )
        
        return True
    
    def _is_rate_limited(self, identifier: str) -> bool:
        """Check if identifier is rate limited."""
        if identifier not in self.failed_attempts:
            return False
        
        attempts, last_attempt = self.failed_attempts[identifier]
        
        # Check if lockout period has passed
        if datetime.now(timezone.utc) - last_attempt > self.lockout_duration:
            del self.failed_attempts[identifier]
            return False
        
        return attempts >= self.max_attempts
    
    def _record_failed_attempt(self, identifier: str) -> None:
        """Record failed authentication attempt."""
        now = datetime.now(timezone.utc)
        if identifier in self.failed_attempts:
            attempts, _ = self.failed_attempts[identifier]
            self.failed_attempts[identifier] = (attempts + 1, now)
        else:
            self.failed_attempts[identifier] = (1, now)
    
    def _clear_failed_attempts(self, identifier: str) -> None:
        """Clear failed attempts for identifier."""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
    
    def _get_user_by_username_or_email(self, username_or_email: str) -> Optional[Dict[str, Any]]:
        """Get user by username or email (mock implementation)."""
        # In real implementation, query database
        # This is a mock for testing
        if username_or_email == "admin":
            return {
                "id": "admin_001",
                "username": "admin",
                "email": "admin@example.com",
                "password_hash": self.password_manager.hash_password("SecurePassword123!"),
                "roles": ["admin"],
                "is_active": True
            }
        return None
    
    def _get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID (mock implementation)."""
        # In real implementation, query database
        return None


def require_permission(permission: Permission):
    """Decorator to require specific permission for access."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get current user from context (implementation specific)
            current_user = kwargs.get('current_user') or getattr(func, 'current_user', None)
            
            if not current_user:
                security_logger.log_security_event(
                    event_type="authorization_failed",
                    details={"reason": "no_user_context", "permission": permission.value}
                )
                raise SecurityError("Authentication required")
            
            if not current_user.has_permission(permission):
                security_logger.log_security_event(
                    event_type="authorization_failed",
                    user_id=current_user.user_id,
                    details={
                        "reason": "insufficient_permissions",
                        "required_permission": permission.value,
                        "user_permissions": [p.value for p in current_user.permissions]
                    }
                )
                raise SecurityError(f"Permission {permission.value} required")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role: UserRole):
    """Decorator to require specific role for access."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user') or getattr(func, 'current_user', None)
            
            if not current_user:
                raise SecurityError("Authentication required")
            
            if not current_user.has_role(role):
                security_logger.log_security_event(
                    event_type="authorization_failed",
                    user_id=current_user.user_id,
                    details={
                        "reason": "insufficient_role",
                        "required_role": role.value,
                        "user_roles": [r.value for r in current_user.roles]
                    }
                )
                raise SecurityError(f"Role {role.value} required")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
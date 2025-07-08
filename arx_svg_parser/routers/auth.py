"""
Authentication router for Arxos SVG-BIM Integration System.

Provides endpoints for:
- User login/logout
- Token refresh
- User registration
- Password reset
- User profile management
- User administration (admin only)
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import re

from utils.auth import (
    create_access_token, create_refresh_token, get_current_user,
    get_user_from_refresh_token, hash_password, verify_password,
    TokenUser, TokenResponse, validate_password_strength, revoke_token
)
from models.database import User, get_db_manager
from services.database_service import DatabaseService
from services.access_control import access_control_service, UserRole
from utils.errors import AuthenticationError, ValidationError

router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models for request/response
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    roles: List[str] = ["viewer"]  # Default role
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', v):
            raise ValueError('Username must be 3-20 characters, alphanumeric and underscore only')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    roles: Optional[List[str]] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    roles: List[str]
    is_active: bool
    is_superuser: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    last_login: Optional[datetime]

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        is_valid, message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(message)
        return v

class UserSearch(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    organization: Optional[str] = None

# Database service instance
db_service = DatabaseService()

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return access/refresh tokens."""
    try:
        # Get user from database
        session = db_service.get_session()
        user = session.query(User).filter(User.username == form_data.username).first()
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            # Log failed login attempt
            access_control_service.log_audit_event(
                user_id="unknown",
                action="login_failed",
                resource_type="user",
                resource_id=form_data.username,
                details={"reason": "invalid_credentials"},
                ip_address="unknown",
                user_agent="unknown",
                success=False
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is temporarily locked"
            )
        
        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        session.commit()
        
        # Create token user object
        token_user = TokenUser(
            id=user.id,
            username=user.username,
            roles=user.roles or [],
            is_active=user.is_active
        )
        
        # Generate tokens
        access_token = create_access_token(token_user)
        refresh_token = create_refresh_token(token_user)
        
        # Log successful login
        access_control_service.log_audit_event(
            user_id=user.id,
            action="login_success",
            resource_type="user",
            resource_id=user.username,
            details={"login_method": "password"},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,  # 30 minutes
            refresh_expires_in=7 * 24 * 60 * 60  # 7 days
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )
    finally:
        session.close()

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token."""
    try:
        # Validate refresh token
        token_user = get_user_from_refresh_token(refresh_token)
        
        # Get user from database to ensure they still exist and are active
        session = db_service.get_session()
        user = session.query(User).filter(User.id == token_user.id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Generate new tokens
        access_token = create_access_token(token_user)
        new_refresh_token = create_refresh_token(token_user)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=30 * 60,  # 30 minutes
            refresh_expires_in=7 * 24 * 60 * 60  # 7 days
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )
    finally:
        session.close()

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user."""
    try:
        session = db_service.get_session()
        
        # Check if username or email already exists
        existing_user = session.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
        
        # Create new user
        user = User(
            id=str(uuid.uuid4()),
            username=user_data.username,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            roles=user_data.roles,
            is_active=True,
            is_superuser=False
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Log user creation
        access_control_service.log_audit_event(
            user_id=user.id,
            action="user_created",
            resource_type="user",
            resource_id=user.username,
            details={"roles": user_data.roles},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles or [],
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )
    finally:
        session.close()

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: TokenUser = Depends(get_current_user)):
    """Get current user's profile."""
    try:
        session = db_service.get_session()
        user = session.query(User).filter(User.id == current_user.id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles or [],
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )
    finally:
        session.close()

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: TokenUser = Depends(get_current_user)
):
    """Update current user's profile."""
    try:
        session = db_service.get_session()
        user = session.query(User).filter(User.id == current_user.id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update allowed fields
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.email is not None:
            # Check if email is already taken
            existing_user = session.query(User).filter(
                User.email == user_update.email,
                User.id != user.id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            user.email = user_update.email
        
        user.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(user)
        
        # Log profile update
        access_control_service.log_audit_event(
            user_id=user.id,
            action="profile_updated",
            resource_type="user",
            resource_id=user.username,
            details={"updated_fields": list(user_update.dict(exclude_unset=True).keys())},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles or [],
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    finally:
        session.close()

@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: TokenUser = Depends(get_current_user)
):
    """Change current user's password."""
    try:
        session = db_service.get_session()
        user = session.query(User).filter(User.id == current_user.id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not verify_password(password_change.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.hashed_password = hash_password(password_change.new_password)
        user.updated_at = datetime.utcnow()
        session.commit()
        
        # Log password change
        access_control_service.log_audit_event(
            user_id=user.id,
            action="password_changed",
            resource_type="user",
            resource_id=user.username,
            details={"password_changed": True},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )
    finally:
        session.close()

@router.post("/logout")
async def logout(current_user: TokenUser = Depends(get_current_user)):
    """Logout current user and revoke tokens."""
    try:
        # In a real implementation, you would add the token to a blacklist
        # For now, we'll just return success
        access_control_service.log_audit_event(
            user_id=current_user.id,
            action="logout",
            resource_type="user",
            resource_id=current_user.username,
            details={"logout_method": "api"},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

# Admin endpoints (require admin role)
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: TokenUser = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """List all users with pagination and filtering (admin only)."""
    if "admin" not in current_user.roles and "superuser" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        session = db_service.get_session()
        query = session.query(User)
        
        # Apply filters
        if search:
            query = query.filter(
                (User.username.contains(search)) |
                (User.email.contains(search)) |
                (User.full_name.contains(search))
            )
        
        if role:
            query = query.filter(User.roles.contains([role]))
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Apply pagination
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        
        return [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                roles=user.roles or [],
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login=user.last_login
            )
            for user in users
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )
    finally:
        session.close()

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: TokenUser = Depends(get_current_user)
):
    """Get specific user details (admin only)."""
    if "admin" not in current_user.roles and "superuser" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        session = db_service.get_session()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles or [],
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )
    finally:
        session.close()

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: TokenUser = Depends(get_current_user)
):
    """Update user (admin only)."""
    if "admin" not in current_user.roles and "superuser" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        session = db_service.get_session()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.email is not None:
            # Check if email is already taken
            existing_user = session.query(User).filter(
                User.email == user_update.email,
                User.id != user.id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            user.email = user_update.email
        if user_update.roles is not None:
            user.roles = user_update.roles
        if user_update.is_active is not None:
            user.is_active = user_update.is_active
        
        user.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(user)
        
        # Log user update
        access_control_service.log_audit_event(
            user_id=current_user.id,
            action="user_updated",
            resource_type="user",
            resource_id=user.username,
            details={"updated_fields": list(user_update.dict(exclude_unset=True).keys())},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles or [],
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )
    finally:
        session.close()

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: TokenUser = Depends(get_current_user)
):
    """Delete user (admin only)."""
    if "admin" not in current_user.roles and "superuser" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        session = db_service.get_session()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent self-deletion
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Soft delete by setting is_active to False
        user.is_active = False
        user.updated_at = datetime.utcnow()
        session.commit()
        
        # Log user deletion
        access_control_service.log_audit_event(
            user_id=current_user.id,
            action="user_deleted",
            resource_type="user",
            resource_id=user.username,
            details={"deleted_user_id": user_id},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
    finally:
        session.close()

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: TokenUser = Depends(get_current_user)
):
    """Activate a user account (admin only)."""
    if "admin" not in current_user.roles and "superuser" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        session = db_service.get_session()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        session.commit()
        
        # Log user activation
        access_control_service.log_audit_event(
            user_id=current_user.id,
            action="user_activated",
            resource_type="user",
            resource_id=user.username,
            details={"activated_user_id": user_id},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        return {"message": "User activated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )
    finally:
        session.close()

@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: TokenUser = Depends(get_current_user)
):
    """Deactivate a user account (admin only)."""
    if "admin" not in current_user.roles and "superuser" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        session = db_service.get_session()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent self-deactivation
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        session.commit()
        
        # Log user deactivation
        access_control_service.log_audit_event(
            user_id=current_user.id,
            action="user_deactivated",
            resource_type="user",
            resource_id=user.username,
            details={"deactivated_user_id": user_id},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        return {"message": "User deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )
    finally:
        session.close()

@router.get("/audit-logs")
async def get_audit_logs(
    current_user: TokenUser = Depends(get_current_user),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get audit logs (admin only)."""
    if "admin" not in current_user.roles and "superuser" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        logs = access_control_service.get_audit_logs(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {"audit_logs": logs, "total": len(logs)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit logs"
        ) 
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
import structlog

from utils.auth import (
    create_access_token, create_refresh_token, get_current_user,
    get_user_from_refresh_token, hash_password, verify_password,
    TokenUser, TokenResponse, validate_password_strength, revoke_token
)
from models.database import User, get_db_manager
from services.database_service import DatabaseService
from services.access_control import access_control_service, UserRole
from utils.errors import AuthenticationError, ValidationError

logger = structlog.get_logger(__name__)

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
        logger.info("user_login_attempt", username=form_data.username)
        
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
            
            logger.warning("user_login_failed_invalid_credentials",
                          username=form_data.username)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user.is_active:
            logger.warning("user_login_failed_account_disabled",
                          username=form_data.username,
                          user_id=user.id)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            logger.warning("user_login_failed_account_locked",
                          username=form_data.username,
                          user_id=user.id,
                          locked_until=user.locked_until.isoformat())
            
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
        
        logger.info("user_login_successful",
                   username=form_data.username,
                   user_id=user.id,
                   roles=user.roles)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,  # 30 minutes
            refresh_expires_in=7 * 24 * 60 * 60  # 7 days
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_login_exception",
                    username=form_data.username,
                    error=str(e),
                    error_type=type(e).__name__)
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
        logger.debug("token_refresh_attempt")
        
        # Validate refresh token
        token_user = get_user_from_refresh_token(refresh_token)
        
        if not token_user:
            logger.warning("token_refresh_failed_invalid_token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Generate new tokens
        new_access_token = create_access_token(token_user)
        new_refresh_token = create_refresh_token(token_user)
        
        # Revoke old refresh token
        revoke_token(refresh_token)
        
        logger.info("token_refresh_successful",
                   user_id=token_user.id,
                   username=token_user.username)
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=30 * 60,  # 30 minutes
            refresh_expires_in=7 * 24 * 60 * 60  # 7 days
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("token_refresh_exception",
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user."""
    try:
        logger.info("user_registration_attempt",
                   username=user_data.username,
                   email=user_data.email)
        
        # Check if username already exists
        session = db_service.get_session()
        existing_user = session.query(User).filter(User.username == user_data.username).first()
        
        if existing_user:
            logger.warning("user_registration_failed_username_exists",
                          username=user_data.username)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email already exists
        existing_email = session.query(User).filter(User.email == user_data.email).first()
        
        if existing_email:
            logger.warning("user_registration_failed_email_exists",
                          email=user_data.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create new user
        new_user = User(
            id=str(uuid.uuid4()),
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            roles=user_data.roles,
            is_active=True,
            is_superuser=False,
            created_at=datetime.utcnow()
        )
        
        session.add(new_user)
        session.commit()
        
        # Log user creation
        access_control_service.log_audit_event(
            user_id="system",
            action="user_created",
            resource_type="user",
            resource_id=new_user.username,
            details={"created_by": "registration"},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        logger.info("user_registration_successful",
                   username=user_data.username,
                   user_id=new_user.id,
                   email=user_data.email)
        
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            roles=new_user.roles or [],
            is_active=new_user.is_active,
            is_superuser=new_user.is_superuser,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
            last_login=new_user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_registration_exception",
                    username=user_data.username,
                    email=user_data.email,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )
    finally:
        session.close()

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: TokenUser = Depends(get_current_user)):
    """Get current user profile."""
    try:
        logger.debug("user_profile_request",
                    user_id=current_user.id,
                    username=current_user.username)
        
        session = db_service.get_session()
        user = session.query(User).filter(User.id == current_user.id).first()
        
        if not user:
            logger.warning("user_profile_not_found",
                          user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.debug("user_profile_retrieved",
                    user_id=current_user.id,
                    username=current_user.username)
        
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
        logger.error("user_profile_exception",
                    user_id=current_user.id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )
    finally:
        session.close()

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: TokenUser = Depends(get_current_user)
):
    """Update current user profile."""
    try:
        logger.info("user_profile_update_attempt",
                   user_id=current_user.id,
                   username=current_user.username,
                   update_fields=list(user_update.dict(exclude_unset=True).keys()))
        
        session = db_service.get_session()
        user = session.query(User).filter(User.id == current_user.id).first()
        
        if not user:
            logger.warning("user_profile_update_failed_not_found",
                          user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        session.commit()
        
        # Log profile update
        access_control_service.log_audit_event(
            user_id=current_user.id,
            action="profile_updated",
            resource_type="user",
            resource_id=user.username,
            details={"updated_fields": list(update_data.keys())},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        logger.info("user_profile_update_successful",
                   user_id=current_user.id,
                   username=current_user.username,
                   updated_fields=list(update_data.keys()))
        
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
        logger.error("user_profile_update_exception",
                    user_id=current_user.id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )
    finally:
        session.close()

@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: TokenUser = Depends(get_current_user)
):
    """Change current user password."""
    try:
        logger.info("password_change_attempt",
                   user_id=current_user.id,
                   username=current_user.username)
        
        session = db_service.get_session()
        user = session.query(User).filter(User.id == current_user.id).first()
        
        if not user:
            logger.warning("password_change_failed_user_not_found",
                          user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not verify_password(password_change.current_password, user.hashed_password):
            logger.warning("password_change_failed_current_password_incorrect",
                          user_id=current_user.id,
                          username=current_user.username)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = hash_password(password_change.new_password)
        user.hashed_password = new_hashed_password
        user.updated_at = datetime.utcnow()
        session.commit()
        
        # Log password change
        access_control_service.log_audit_event(
            user_id=current_user.id,
            action="password_changed",
            resource_type="user",
            resource_id=user.username,
            details={"changed_by": "user"},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        logger.info("password_change_successful",
                   user_id=current_user.id,
                   username=current_user.username)
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("password_change_exception",
                    user_id=current_user.id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )
    finally:
        session.close()

@router.post("/logout")
async def logout(current_user: TokenUser = Depends(get_current_user)):
    """Logout current user."""
    try:
        logger.info("user_logout_attempt",
                   user_id=current_user.id,
                   username=current_user.username)
        
        # Log logout event
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
        
        logger.info("user_logout_successful",
                   user_id=current_user.id,
                   username=current_user.username)
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error("user_logout_exception",
                    user_id=current_user.id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: TokenUser = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """List users (admin only)."""
    try:
        logger.info("user_list_request",
                   admin_user_id=current_user.id,
                   admin_username=current_user.username,
                   skip=skip,
                   limit=limit,
                   search=search,
                   role=role,
                   is_active=is_active)
        
        # Check admin permissions
        if "admin" not in current_user.roles and "superuser" not in current_user.roles:
            logger.warning("user_list_unauthorized",
                          user_id=current_user.id,
                          username=current_user.username,
                          roles=current_user.roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        session = db_service.get_session()
        query = session.query(User)
        
        # Apply filters
        if search:
            query = query.filter(
                User.username.contains(search) | User.email.contains(search)
            )
        
        if role:
            query = query.filter(User.roles.contains([role]))
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        users = query.offset(skip).limit(limit).all()
        
        logger.info("user_list_retrieved",
                   admin_user_id=current_user.id,
                   total_count=total_count,
                   returned_count=len(users),
                   skip=skip,
                   limit=limit)
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_list_exception",
                    admin_user_id=current_user.id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )
    finally:
        session.close()

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: TokenUser = Depends(get_current_user)
):
    """Get user by ID (admin only)."""
    try:
        logger.debug("user_retrieval_request",
                    admin_user_id=current_user.id,
                    target_user_id=user_id)
        
        # Check admin permissions
        if "admin" not in current_user.roles and "superuser" not in current_user.roles:
            logger.warning("user_retrieval_unauthorized",
                          user_id=current_user.id,
                          target_user_id=user_id,
                          roles=current_user.roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        session = db_service.get_session()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.warning("user_retrieval_failed_not_found",
                          admin_user_id=current_user.id,
                          target_user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.debug("user_retrieval_successful",
                    admin_user_id=current_user.id,
                    target_user_id=user_id,
                    target_username=user.username)
        
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
        logger.error("user_retrieval_exception",
                    admin_user_id=current_user.id,
                    target_user_id=user_id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )
    finally:
        session.close()

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: TokenUser = Depends(get_current_user)
):
    """Update user by ID (admin only)."""
    try:
        logger.info("user_update_attempt",
                   admin_user_id=current_user.id,
                   target_user_id=user_id,
                   update_fields=list(user_update.dict(exclude_unset=True).keys()))
        
        # Check admin permissions
        if "admin" not in current_user.roles and "superuser" not in current_user.roles:
            logger.warning("user_update_unauthorized",
                          user_id=current_user.id,
                          target_user_id=user_id,
                          roles=current_user.roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        session = db_service.get_session()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.warning("user_update_failed_not_found",
                          admin_user_id=current_user.id,
                          target_user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        session.commit()
        
        # Log user update
        access_control_service.log_audit_event(
            user_id=current_user.id,
            action="user_updated",
            resource_type="user",
            resource_id=user.username,
            details={"updated_by": current_user.username, "updated_fields": list(update_data.keys())},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        logger.info("user_update_successful",
                   admin_user_id=current_user.id,
                   target_user_id=user_id,
                   target_username=user.username,
                   updated_fields=list(update_data.keys()))
        
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
        logger.error("user_update_exception",
                    admin_user_id=current_user.id,
                    target_user_id=user_id,
                    error=str(e),
                    error_type=type(e).__name__)
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
    """Delete user by ID (admin only)."""
    try:
        logger.info("user_deletion_attempt",
                   admin_user_id=current_user.id,
                   target_user_id=user_id)
        
        # Check admin permissions
        if "admin" not in current_user.roles and "superuser" not in current_user.roles:
            logger.warning("user_deletion_unauthorized",
                          user_id=current_user.id,
                          target_user_id=user_id,
                          roles=current_user.roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Prevent self-deletion
        if user_id == current_user.id:
            logger.warning("user_deletion_failed_self_deletion",
                          user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        session = db_service.get_session()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.warning("user_deletion_failed_not_found",
                          admin_user_id=current_user.id,
                          target_user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Log user deletion
        access_control_service.log_audit_event(
            user_id=current_user.id,
            action="user_deleted",
            resource_type="user",
            resource_id=user.username,
            details={"deleted_by": current_user.username},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        session.delete(user)
        session.commit()
        
        logger.info("user_deletion_successful",
                   admin_user_id=current_user.id,
                   target_user_id=user_id,
                   target_username=user.username)
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_deletion_exception",
                    admin_user_id=current_user.id,
                    target_user_id=user_id,
                    error=str(e),
                    error_type=type(e).__name__)
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
    """Activate user account (admin only)."""
    try:
        logger.info("user_activation_attempt",
                   admin_user_id=current_user.id,
                   target_user_id=user_id)
        
        # Check admin permissions
        if "admin" not in current_user.roles and "superuser" not in current_user.roles:
            logger.warning("user_activation_unauthorized",
                          user_id=current_user.id,
                          target_user_id=user_id,
                          roles=current_user.roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        session = db_service.get_session()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.warning("user_activation_failed_not_found",
                          admin_user_id=current_user.id,
                          target_user_id=user_id)
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
            details={"activated_by": current_user.username},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        logger.info("user_activation_successful",
                   admin_user_id=current_user.id,
                   target_user_id=user_id,
                   target_username=user.username)
        
        return {"message": "User activated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_activation_exception",
                    admin_user_id=current_user.id,
                    target_user_id=user_id,
                    error=str(e),
                    error_type=type(e).__name__)
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
    """Deactivate user account (admin only)."""
    try:
        logger.info("user_deactivation_attempt",
                   admin_user_id=current_user.id,
                   target_user_id=user_id)
        
        # Check admin permissions
        if "admin" not in current_user.roles and "superuser" not in current_user.roles:
            logger.warning("user_deactivation_unauthorized",
                          user_id=current_user.id,
                          target_user_id=user_id,
                          roles=current_user.roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Prevent self-deactivation
        if user_id == current_user.id:
            logger.warning("user_deactivation_failed_self_deactivation",
                          user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
        
        session = db_service.get_session()
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            logger.warning("user_deactivation_failed_not_found",
                          admin_user_id=current_user.id,
                          target_user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
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
            details={"deactivated_by": current_user.username},
            ip_address="unknown",
            user_agent="unknown",
            success=True
        )
        
        logger.info("user_deactivation_successful",
                   admin_user_id=current_user.id,
                   target_user_id=user_id,
                   target_username=user.username)
        
        return {"message": "User deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("user_deactivation_exception",
                    admin_user_id=current_user.id,
                    target_user_id=user_id,
                    error=str(e),
                    error_type=type(e).__name__)
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
    try:
        logger.info("audit_logs_request",
                   admin_user_id=current_user.id,
                   admin_username=current_user.username,
                   filters={
                       "user_id": user_id,
                       "action": action,
                       "resource_type": resource_type,
                       "start_date": start_date.isoformat() if start_date else None,
                       "end_date": end_date.isoformat() if end_date else None,
                       "limit": limit
                   })
        
        # Check admin permissions
        if "admin" not in current_user.roles and "superuser" not in current_user.roles:
            logger.warning("audit_logs_unauthorized",
                          user_id=current_user.id,
                          roles=current_user.roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Get audit logs from access control service
        audit_logs = access_control_service.get_audit_logs(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        logger.info("audit_logs_retrieved",
                   admin_user_id=current_user.id,
                   log_count=len(audit_logs))
        
        return audit_logs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("audit_logs_exception",
                    admin_user_id=current_user.id,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        ) 
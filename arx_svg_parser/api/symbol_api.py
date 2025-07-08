from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from services.symbol_manager import SymbolManager
from utils.auth import (
    get_current_user, check_permission_dependency, require_role_dependency, Permission, UserRole, User,
    UserCreate, UserLogin, Token, login_user, create_user, list_users, update_user_role, deactivate_user
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

symbol_manager = SymbolManager()

class SymbolModel(BaseModel):
    name: str
    system: str
    svg: Dict[str, Any]
    description: Optional[str] = None
    category: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    connections: Optional[List[Any]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

class SymbolUpdateModel(BaseModel):
    id: str
    name: Optional[str] = None
    system: Optional[str] = None
    svg: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    category: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    connections: Optional[List[Any]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

# Authentication endpoints
@router.post("/auth/login", response_model=Token)
def login(user_data: UserLogin):
    """Login and get access token."""
    return login_user(user_data)

@router.post("/auth/register", response_model=User)
def register_user(
    user_data: UserCreate, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.MANAGE_USERS))
):
    """Register a new user (admin only)."""
    return create_user(user_data)

# Symbol endpoints with authentication and permissions
@router.post("/symbols/", response_model=Dict[str, Any])
def create_symbol(
    symbol: SymbolModel, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.CREATE_SYMBOL))
):
    """Create a new symbol."""
    try:
        created = symbol_manager.create_symbol(symbol.dict(exclude_unset=True))
        logger.info(f"User {current_user.username} created symbol: {created.get('id')}")
        return created
    except Exception as e:
        logger.error(f"Create symbol failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/symbols/{symbol_id}", response_model=Dict[str, Any])
def get_symbol(
    symbol_id: str, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.READ_SYMBOL))
):
    """Get a symbol by ID."""
    symbol = symbol_manager.get_symbol(symbol_id)
    if not symbol:
        raise HTTPException(status_code=404, detail="Symbol not found")
    return symbol

@router.put("/symbols/{symbol_id}", response_model=Dict[str, Any])
def update_symbol(
    symbol_id: str, 
    updates: SymbolUpdateModel, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.UPDATE_SYMBOL))
):
    """Update a symbol by ID."""
    try:
        updated = symbol_manager.update_symbol(symbol_id, updates.dict(exclude_unset=True))
        if not updated:
            raise HTTPException(status_code=404, detail="Symbol not found")
        logger.info(f"User {current_user.username} updated symbol: {symbol_id}")
        return updated
    except Exception as e:
        logger.error(f"Update symbol failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/symbols/{symbol_id}", response_model=Dict[str, Any])
def delete_symbol(
    symbol_id: str, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.DELETE_SYMBOL))
):
    """Delete a symbol by ID."""
    deleted = symbol_manager.delete_symbol(symbol_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Symbol not found")
    logger.info(f"User {current_user.username} deleted symbol: {symbol_id}")
    return {"deleted": True, "symbol_id": symbol_id}

@router.get("/symbols/", response_model=List[Dict[str, Any]])
def list_symbols(
    system: Optional[str] = Query(None), 
    query: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.LIST_SYMBOLS))
):
    """List or search symbols."""
    if query:
        return symbol_manager.search_symbols(query, system=system)
    return symbol_manager.list_symbols(system=system)

# Bulk operation endpoints
@router.post("/symbols/bulk_create", response_model=List[Dict[str, Any]])
def bulk_create_symbols(
    symbols: List[SymbolModel], 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.BULK_CREATE_SYMBOLS))
):
    """Bulk create symbols."""
    created = symbol_manager.bulk_create_symbols([s.dict(exclude_unset=True) for s in symbols])
    logger.info(f"User {current_user.username} bulk created {len(created)} symbols")
    return created

@router.post("/symbols/bulk_update", response_model=List[Dict[str, Any]])
def bulk_update_symbols(
    updates: List[SymbolUpdateModel], 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.BULK_UPDATE_SYMBOLS))
):
    """Bulk update symbols."""
    updated = symbol_manager.bulk_update_symbols([u.dict(exclude_unset=True) for u in updates])
    logger.info(f"User {current_user.username} bulk updated {len(updated)} symbols")
    return updated

@router.post("/symbols/bulk_delete", response_model=Dict[str, bool])
def bulk_delete_symbols(
    symbol_ids: List[str], 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.BULK_DELETE_SYMBOLS))
):
    """Bulk delete symbols by ID."""
    results = symbol_manager.bulk_delete_symbols(symbol_ids)
    deleted_count = sum(1 for success in results.values() if success)
    logger.info(f"User {current_user.username} bulk deleted {deleted_count} symbols")
    return results

# Statistics endpoint
@router.get("/symbols/statistics", response_model=Dict[str, Any])
def get_symbol_statistics(
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.VIEW_STATISTICS))
):
    """Get symbol statistics."""
    return symbol_manager.get_symbol_statistics()

# User management endpoints (admin only)
@router.get("/users/", response_model=List[User])
def get_users(
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: require_role_dependency(u, UserRole.ADMIN))
):
    """List all users (admin only)."""
    return list_users()

@router.put("/users/{user_id}/role", response_model=User)
def change_user_role(
    user_id: str, 
    new_role: UserRole, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: require_role_dependency(u, UserRole.ADMIN))
):
    """Change a user's role (admin only)."""
    return update_user_role(user_id, new_role)

@router.delete("/users/{user_id}", response_model=User)
def deactivate_user_account(
    user_id: str, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: require_role_dependency(u, UserRole.ADMIN))
):
    """Deactivate a user account (admin only)."""
    return deactivate_user(user_id)

# Health check endpoint (no authentication required)
@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "symbol-api"} 
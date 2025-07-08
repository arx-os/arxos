"""
Symbol Management Router

This module provides REST API endpoints for symbol management operations,
including CRUD operations, filtering, and search functionality.

Author: Arxos Development Team
Date: 2024
"""

from fastapi import APIRouter, HTTPException, Query, Depends, status, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from services.symbol_manager import SymbolManager
from services.schema_validation import SymbolSchemaValidator
from utils.auth import (
    get_current_user, check_permission, require_role, Permission, UserRole, User,
    UserCreate, UserLogin, Token, login_user, create_user, list_users, update_user_role, deactivate_user
)
import logging
import json
import csv
# Remove all YAML imports and logic
# Only allow JSON for symbol management
# Update docstrings and comments to reference JSON only
import io
import asyncio
from datetime import datetime
from enum import Enum

# Setup logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1", tags=["symbol-management"])

# Initialize symbol manager and validator
symbol_manager = SymbolManager()
schema_validator = SymbolSchemaValidator()

# Simple job tracking for bulk operations
class JobTracker:
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
    
    def create_job(self, job_type: str) -> str:
        job_id = f"{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self)}"
        self.jobs[job_id] = {
            "status": "pending",
            "progress": 0,
            "total_items": 0,
            "processed_items": 0,
            "errors": [],
            "result": None,
            "created_at": datetime.now().isoformat()
        }
        return job_id
    
    def update_job(self, job_id: str, **kwargs):
        if job_id in self.jobs:
            self.jobs[job_id].update(kwargs)
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)

job_tracker = JobTracker()

# Pydantic models for request/response validation
class SymbolCreateRequest(BaseModel):
    name: str = Field(..., description="Symbol name", min_length=1, max_length=100)
    system: str = Field(..., description="System category (e.g., mechanical, electrical)")
    svg: Dict[str, Any] = Field(..., description="SVG data including content")
    description: Optional[str] = Field(None, description="Symbol description", max_length=500)
    category: Optional[str] = Field(None, description="Symbol category")
    properties: Optional[Dict[str, Any]] = Field(None, description="Custom properties")
    connections: Optional[List[Any]] = Field(None, description="Connection points")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class SymbolUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Symbol name", min_length=1, max_length=100)
    system: Optional[str] = Field(None, description="System category")
    svg: Optional[Dict[str, Any]] = Field(None, description="SVG data")
    description: Optional[str] = Field(None, description="Symbol description", max_length=500)
    category: Optional[str] = Field(None, description="Symbol category")
    properties: Optional[Dict[str, Any]] = Field(None, description="Custom properties")
    connections: Optional[List[Any]] = Field(None, description="Connection points")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class SymbolResponse(BaseModel):
    id: str
    name: str
    system: str
    svg: Dict[str, Any]
    description: Optional[str] = None
    category: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    connections: Optional[List[Any]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: Optional[str] = None

class SymbolListResponse(BaseModel):
    symbols: List[SymbolResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool

class BulkCreateRequest(BaseModel):
    symbols: List[SymbolCreateRequest] = Field(..., description="List of symbols to create")

class BulkUpdateRequest(BaseModel):
    updates: List[Dict[str, Any]] = Field(..., description="List of symbol updates with IDs")

class BulkDeleteRequest(BaseModel):
    symbol_ids: List[str] = Field(..., description="List of symbol IDs to delete")

class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"

class BulkImportResponse(BaseModel):
    total_processed: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]]
    job_id: Optional[str] = None

class ExportResponse(BaseModel):
    format: ExportFormat
    total_symbols: int
    download_url: Optional[str] = None
    expires_at: Optional[str] = None

class ProgressResponse(BaseModel):
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: int  # 0-100
    total_items: int
    processed_items: int
    errors: List[Dict[str, Any]]
    result: Optional[Dict[str, Any]] = None

class StatisticsResponse(BaseModel):
    total_symbols: int
    systems: Dict[str, int]
    recent_symbols: List[SymbolResponse]
    symbol_sizes: Dict[str, int]

# Authentication endpoints
@router.post("/auth/login", response_model=Token, summary="Login user")
async def login(user_data: UserLogin):
    """
    Login and get access token.
    
    Returns a JWT token that can be used for authenticated requests.
    """
    return login_user(user_data)

@router.post("/auth/register", response_model=User, summary="Register new user")
async def register_user(
    user_data: UserCreate, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.MANAGE_USERS))
):
    """
    Register a new user (admin only).
    
    Only administrators can create new user accounts.
    """
    return create_user(user_data)

# Symbol CRUD endpoints
@router.post("/symbols", response_model=SymbolResponse, status_code=status.HTTP_201_CREATED, summary="Create symbol")
async def create_symbol(
    symbol_data: SymbolCreateRequest, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.CREATE_SYMBOL))
):
    """
    Create a new symbol.
    
    Requires CREATE_SYMBOL permission.
    """
    try:
        # Validate symbol data against schema
        symbol_dict = symbol_data.dict(exclude_unset=True)
        valid, errors = schema_validator.validate_symbol(symbol_dict)
        
        if not valid:
            error_details = {"validation_errors": errors}
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail=error_details
            )
        
        created_symbol = symbol_manager.create_symbol(symbol_dict)
        logger.info(f"User {current_user.username} created symbol: {created_symbol.get('id')}")
        return SymbolResponse(**created_symbol)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f"Create symbol failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/symbols/{symbol_id}", response_model=SymbolResponse, summary="Get symbol by ID")
async def get_symbol(
    symbol_id: str, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.READ_SYMBOL))
):
    """
    Get a symbol by ID.
    
    Requires READ_SYMBOL permission.
    """
    symbol = symbol_manager.get_symbol(symbol_id)
    if not symbol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Symbol with ID '{symbol_id}' not found"
        )
    return SymbolResponse(**symbol)

@router.put("/symbols/{symbol_id}", response_model=SymbolResponse, summary="Update symbol")
async def update_symbol(
    symbol_id: str, 
    updates: SymbolUpdateRequest, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.UPDATE_SYMBOL))
):
    """
    Update a symbol by ID.
    
    Requires UPDATE_SYMBOL permission.
    """
    try:
        # Get current symbol data
        current_symbol = symbol_manager.get_symbol(symbol_id)
        if not current_symbol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Symbol with ID '{symbol_id}' not found"
            )
        
        # Merge updates with current data for validation
        update_dict = updates.dict(exclude_unset=True)
        merged_data = {**current_symbol, **update_dict}
        
        # Validate merged data against schema
        valid, errors = schema_validator.validate_symbol(merged_data)
        
        if not valid:
            error_details = {"validation_errors": errors}
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail=error_details
            )
        
        updated_symbol = symbol_manager.update_symbol(symbol_id, update_dict)
        if not updated_symbol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Symbol with ID '{symbol_id}' not found"
            )
        logger.info(f"User {current_user.username} updated symbol: {symbol_id}")
        return SymbolResponse(**updated_symbol)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Update symbol failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/symbols/{symbol_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete symbol")
async def delete_symbol(
    symbol_id: str, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.DELETE_SYMBOL))
):
    """
    Delete a symbol by ID.
    
    Requires DELETE_SYMBOL permission.
    """
    deleted = symbol_manager.delete_symbol(symbol_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Symbol with ID '{symbol_id}' not found"
        )
    logger.info(f"User {current_user.username} deleted symbol: {symbol_id}")
    return None

@router.get("/symbols", response_model=SymbolListResponse, summary="List and search symbols")
async def list_symbols(
    system: Optional[str] = Query(None, description="Filter by system"),
    query: Optional[str] = Query(None, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.LIST_SYMBOLS))
):
    """
    List or search symbols with pagination and filtering.
    
    Requires LIST_SYMBOLS permission.
    """
    try:
        # Get symbols based on filters
        if query:
            symbols = symbol_manager.search_symbols(query, system=system)
        else:
            symbols = symbol_manager.list_symbols(system=system)
        
        # Apply pagination
        total_count = len(symbols)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_symbols = symbols[start_idx:end_idx]
        
        # Convert to response models
        symbol_responses = [SymbolResponse(**symbol) for symbol in paginated_symbols]
        
        return SymbolListResponse(
            symbols=symbol_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=end_idx < total_count,
            has_prev=page > 1
        )
    except Exception as e:
        logger.error(f"List symbols failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Bulk operation endpoints
@router.post("/symbols/bulk", response_model=List[SymbolResponse], status_code=status.HTTP_201_CREATED, summary="Bulk create symbols")
async def bulk_create_symbols(
    request: BulkCreateRequest, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.BULK_CREATE_SYMBOLS))
):
    """
    Bulk create symbols.
    
    Requires BULK_CREATE_SYMBOLS permission.
    """
    try:
        symbols_data = [symbol.dict(exclude_unset=True) for symbol in request.symbols]
        
        # Validate all symbols before creating
        validation_results = schema_validator.validate_symbols(symbols_data)
        invalid_symbols = [r for r in validation_results if not r['valid']]
        
        if invalid_symbols:
            error_details = {
                "validation_errors": invalid_symbols,
                "message": "Some symbols failed validation"
            }
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
                detail=error_details
            )
        
        created_symbols = symbol_manager.bulk_create_symbols(symbols_data)
        logger.info(f"User {current_user.username} bulk created {len(created_symbols)} symbols")
        return [SymbolResponse(**symbol) for symbol in created_symbols]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk create symbols failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put("/symbols/bulk", response_model=List[SymbolResponse], summary="Bulk update symbols")
async def bulk_update_symbols(
    request: BulkUpdateRequest, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.BULK_UPDATE_SYMBOLS))
):
    """
    Bulk update symbols.
    
    Requires BULK_UPDATE_SYMBOLS permission.
    """
    try:
        updated_symbols = symbol_manager.bulk_update_symbols(request.updates)
        logger.info(f"User {current_user.username} bulk updated {len(updated_symbols)} symbols")
        return [SymbolResponse(**symbol) for symbol in updated_symbols]
    except Exception as e:
        logger.error(f"Bulk update symbols failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/symbols/bulk", response_model=Dict[str, bool], summary="Bulk delete symbols")
async def bulk_delete_symbols(
    request: BulkDeleteRequest, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.BULK_DELETE_SYMBOLS))
):
    """
    Bulk delete symbols.
    
    Requires BULK_DELETE_SYMBOLS permission.
    """
    try:
        deleted_count = symbol_manager.bulk_delete_symbols(request.symbol_ids)
        logger.info(f"User {current_user.username} bulk deleted {deleted_count} symbols")
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        logger.error(f"Bulk delete symbols failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Bulk import/export endpoints
@router.post("/symbols/bulk-import", response_model=BulkImportResponse, summary="Bulk import symbols from file")
async def bulk_import_symbols(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="File to import (JSON)"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.BULK_CREATE_SYMBOLS))
):
    """
    Bulk import symbols from a JSON file.
    
    Requires BULK_CREATE_SYMBOLS permission.
    """
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JSON files are supported for import"
            )
        
        # Read and parse file content
        content = await file.read()
        try:
            symbols_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format"
            )
        
        # Validate that it's a list of symbols
        if not isinstance(symbols_data, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must contain a list of symbols"
            )
        
        # Create background job
        job_id = job_tracker.create_job("bulk_import")
        
        # Add background task
        background_tasks.add_task(process_bulk_import, job_id, symbols_data, current_user.username)
        
        return BulkImportResponse(
            total_processed=len(symbols_data),
            successful=0,
            failed=0,
            errors=[],
            job_id=job_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk import failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/symbols/export", response_model=ExportResponse, summary="Export symbols")
async def export_symbols(
    format: ExportFormat = Query(ExportFormat.JSON, description="Export format"),
    system: Optional[str] = Query(None, description="Filter by system"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.READ_SYMBOL))
):
    """
    Export symbols in various formats.
    
    Requires READ_SYMBOL permission.
    """
    try:
        # Get symbols to export
        symbols = symbol_manager.list_symbols(system=system)
        
        # Create background job
        job_id = job_tracker.create_job("bulk_export")
        
        # Add background task
        background_tasks.add_task(process_bulk_export, job_id, symbols, format, current_user.username)
        
        return ExportResponse(
            format=format,
            total_symbols=len(symbols),
            download_url=None,
            expires_at=None
        )
    except Exception as e:
        logger.error(f"Export symbols failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/symbols/export/download", summary="Download exported symbols")
async def download_export(
    job_id: str = Query(..., description="Export job ID"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.READ_SYMBOL))
):
    """
    Download exported symbols file.
    
    Requires READ_SYMBOL permission.
    """
    try:
        job = job_tracker.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export job not found"
            )
        
        if job['status'] != 'completed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Export job not completed"
            )
        
        # Return file for download
        # In a real implementation, you would serve the actual file
        return {"message": "Export file ready for download", "job_id": job_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download export failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/symbols/progress/{job_id}", response_model=ProgressResponse, summary="Get job progress")
async def get_job_progress(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get progress of a background job.
    """
    try:
        job = job_tracker.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return ProgressResponse(**job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job progress failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Statistics endpoint
@router.get("/symbols/statistics", response_model=StatisticsResponse, summary="Get symbol statistics")
async def get_symbol_statistics(
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.VIEW_STATISTICS))
):
    """
    Get symbol library statistics.
    
    Requires VIEW_STATISTICS permission.
    """
    try:
        symbols = symbol_manager.list_symbols()
        
        # Calculate statistics
        systems = {}
        for symbol in symbols:
            system = symbol.get('system', 'unknown')
            systems[system] = systems.get(system, 0) + 1
        
        # Get recent symbols (last 10)
        recent_symbols = sorted(symbols, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
        
        # Calculate symbol sizes
        symbol_sizes = {}
        for symbol in symbols:
            size = len(json.dumps(symbol))
            symbol_sizes[symbol['id']] = size
        
        return StatisticsResponse(
            total_symbols=len(symbols),
            systems=systems,
            recent_symbols=[SymbolResponse(**symbol) for symbol in recent_symbols],
            symbol_sizes=symbol_sizes
        )
    except Exception as e:
        logger.error(f"Get statistics failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Validation endpoints
@router.post("/symbols/validate", summary="Validate symbol data")
async def validate_symbols(
    symbols: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.READ_SYMBOL))
):
    """
    Validate symbol data against schema.
    
    Requires READ_SYMBOL permission.
    """
    try:
        validation_results = schema_validator.validate_symbols(symbols)
        return {
            "valid": all(r['valid'] for r in validation_results),
            "results": validation_results
        }
    except Exception as e:
        logger.error(f"Validate symbols failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/symbols/validate/detailed", summary="Validate symbol data with detailed results")
async def validate_symbols_detailed(
    symbols: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.READ_SYMBOL))
):
    """
    Validate symbol data with detailed error reporting.
    
    Requires READ_SYMBOL permission.
    """
    try:
        validation_results = schema_validator.validate_symbols(symbols)
        detailed_results = []
        
        for i, result in enumerate(validation_results):
            detailed_results.append({
                "index": i,
                "symbol_id": symbols[i].get('id', f"symbol_{i}"),
                "valid": result['valid'],
                "errors": result.get('errors', [])
            })
        
        return {
            "valid": all(r['valid'] for r in validation_results),
            "total_symbols": len(symbols),
            "valid_count": sum(1 for r in validation_results if r['valid']),
            "invalid_count": sum(1 for r in validation_results if not r['valid']),
            "detailed_results": detailed_results
        }
    except Exception as e:
        logger.error(f"Validate symbols detailed failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/symbols/validate/file", summary="Validate symbol file")
async def validate_symbol_file(
    file: UploadFile = File(..., description="Symbol file to validate (JSON)"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.READ_SYMBOL))
):
    """
    Validate a symbol file against schema.
    
    Requires READ_SYMBOL permission.
    """
    try:
        # Read and parse file content
        content = await file.read()
        try:
            symbols_data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON format"
            )
        
        # Validate symbols
        validation_results = schema_validator.validate_symbols(symbols_data)
        
        return {
            "filename": file.filename,
            "valid": all(r['valid'] for r in validation_results),
            "total_symbols": len(symbols_data),
            "valid_count": sum(1 for r in validation_results if r['valid']),
            "invalid_count": sum(1 for r in validation_results if not r['valid']),
            "results": validation_results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validate symbol file failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/symbols/validate/{symbol_id}", summary="Validate a single symbol by ID")
async def validate_symbol_by_id(
    symbol_id: str,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.READ_SYMBOL))
):
    """
    Validate a single symbol by ID.
    
    Requires READ_SYMBOL permission.
    """
    try:
        symbol = symbol_manager.get_symbol(symbol_id)
        if not symbol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Symbol with ID '{symbol_id}' not found"
            )
        
        valid, errors = schema_validator.validate_symbol(symbol)
        
        return {
            "symbol_id": symbol_id,
            "valid": valid,
            "errors": errors if not valid else []
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validate symbol by ID failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/symbols/validate-library", summary="Validate the entire symbol library")
async def validate_symbol_library(
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.READ_SYMBOL))
):
    """
    Validate the entire symbol library.
    
    Requires READ_SYMBOL permission.
    """
    try:
        symbols = symbol_manager.list_symbols()
        validation_results = schema_validator.validate_symbols(symbols)
        
        return {
            "valid": all(r['valid'] for r in validation_results),
            "total_symbols": len(symbols),
            "valid_count": sum(1 for r in validation_results if r['valid']),
            "invalid_count": sum(1 for r in validation_results if not r['valid']),
            "results": validation_results
        }
    except Exception as e:
        logger.error(f"Validate symbol library failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/symbols/validation-report", summary="Download validation report for the symbol library")
async def download_validation_report(
    system: Optional[str] = Query(None, description="Filter by system"),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.READ_SYMBOL))
):
    """
    Download a validation report for the symbol library.
    
    Requires READ_SYMBOL permission.
    """
    try:
        symbols = symbol_manager.list_symbols(system=system)
        validation_results = schema_validator.validate_symbols(symbols)
        
        # Generate report
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_symbols": len(symbols),
            "valid_count": sum(1 for r in validation_results if r['valid']),
            "invalid_count": sum(1 for r in validation_results if not r['valid']),
            "validation_results": validation_results
        }
        
        return report
    except Exception as e:
        logger.error(f"Download validation report failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/symbols/validation-status/{job_id}", summary="Get validation job status and results")
async def get_validation_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: check_permission_dependency(u, Permission.READ_SYMBOL))
):
    """
    Get validation job status and results.
    
    Requires READ_SYMBOL permission.
    """
    try:
        job = job_tracker.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Validation job not found"
            )
        
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get validation status failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# User management endpoints (admin only)
@router.get("/users", response_model=List[User], summary="List all users")
async def get_users(
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: require_role_dependency(u, UserRole.ADMIN))
):
    """
    List all users (admin only).
    
    Requires ADMIN role.
    """
    return list_users()

@router.put("/users/{user_id}/role", response_model=User, summary="Change user role")
async def change_user_role(
    user_id: str, 
    role_update: UserRole, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: require_role_dependency(u, UserRole.ADMIN))
):
    """
    Change a user's role (admin only).
    
    Requires ADMIN role.
    """
    return update_user_role(user_id, role_update)

@router.delete("/users/{user_id}", response_model=User, summary="Deactivate user")
async def deactivate_user_account(
    user_id: str, 
    current_user: User = Depends(get_current_user),
    _: bool = Depends(lambda u: require_role_dependency(u, UserRole.ADMIN))
):
    """
    Deactivate a user account (admin only).
    
    Requires ADMIN role.
    """
    return deactivate_user(user_id)

# Health check endpoint (no authentication required)
@router.get("/health", summary="Health check")
async def health_check():
    """
    Health check endpoint.
    
    No authentication required.
    """
    return {
        "status": "healthy", 
        "service": "symbol-management-api",
        "version": "1.0.0"
    }

# Background task functions
async def process_bulk_import(job_id: str, symbols_data: List[Dict[str, Any]], username: str):
    """
    Background task to process bulk import.
    """
    try:
        job_tracker.update_job(job_id, status="processing")
        
        successful = 0
        failed = 0
        errors = []
        
        for i, symbol_data in enumerate(symbols_data):
            try:
                # Validate symbol against schema
                valid, validation_errors = schema_validator.validate_symbol(symbol_data)
                if not valid:
                    failed += 1
                    errors.append({
                        "index": i,
                        "symbol_id": symbol_data.get("id", "unknown"),
                        "error": "Validation failed",
                        "validation_errors": validation_errors
                    })
                    continue
                
                # Create symbol if validation passes
                symbol_manager.create_symbol(symbol_data)
                successful += 1
                
            except Exception as e:
                failed += 1
                errors.append({
                    "index": i,
                    "symbol_id": symbol_data.get("id", "unknown"),
                    "error": str(e)
                })
            
            # Update progress
            progress = int((i + 1) / len(symbols_data) * 100)
            job_tracker.update_job(
                job_id,
                processed_items=i + 1,
                progress=progress,
                errors=errors
            )
            
            # Small delay to prevent overwhelming the system
            await asyncio.sleep(0.1)
        
        # Final update
        job_tracker.update_job(
            job_id,
            status="completed",
            processed_items=len(symbols_data),
            progress=100,
            result={
                "successful": successful,
                "failed": failed,
                "total": len(symbols_data)
            }
        )
        
        logger.info(f"Bulk import job {job_id} completed: {successful} successful, {failed} failed")
        
    except Exception as e:
        job_tracker.update_job(job_id, status="failed", result={"error": str(e)})
        logger.error(f"Bulk import job {job_id} failed: {e}")

async def process_bulk_export(job_id: str, symbols: List[Dict[str, Any]], format: ExportFormat, username: str):
    """
    Background task to process bulk export.
    """
    try:
        job_tracker.update_job(job_id, status="processing")
        
        # Convert symbols to export format
        if format == ExportFormat.JSON:
            content = json.dumps(symbols, indent=2, default=str)
            filename = f"symbols_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            content_type = "application/json"
            
        elif format == ExportFormat.CSV:
            # Convert to CSV format
            if symbols:
                fieldnames = list(symbols[0].keys())
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(symbols)
                content = output.getvalue()
            else:
                content = ""
            filename = f"symbols_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            content_type = "text/csv"
            
        # Update job with result
        job_tracker.update_job(
            job_id,
            status="completed",
            processed_items=len(symbols),
            progress=100,
            result={
                "content": content,
                "filename": filename,
                "content_type": content_type,
                "total_symbols": len(symbols)
            }
        )
        
        logger.info(f"Export job {job_id} completed: {len(symbols)} symbols exported to {format}")
        
    except Exception as e:
        job_tracker.update_job(job_id, status="failed", result={"error": str(e)})
        logger.error(f"Export job {job_id} failed: {e}") 
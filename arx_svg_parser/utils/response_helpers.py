"""
Centralized Response Helpers for Arxos Platform
Provides standardized API response formatting across all endpoints
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import status
import logging

logger = logging.getLogger(__name__)

class ResponseHelper:
    """Centralized response helper for consistent API responses"""
    
    @staticmethod
    def success_response(
        data: Any = None,
        message: str = "Operation completed successfully",
        status_code: int = status.HTTP_200_OK,
        metadata: Optional[Dict[str, Any]] = None,
        pagination: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """
        Create a standardized success response
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            metadata: Additional metadata
            pagination: Pagination information
            
        Returns:
            JSONResponse with standardized format
        """
        response_data = {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": status_code
        }
        
        if metadata:
            response_data["metadata"] = metadata
            
        if pagination:
            response_data["pagination"] = pagination
            
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @staticmethod
    def error_response(
        message: str,
        error_code: Optional[str] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
        validation_errors: Optional[List[str]] = None
    ) -> JSONResponse:
        """
        Create a standardized error response
        
        Args:
            message: Error message
            error_code: Application-specific error code
            status_code: HTTP status code
            details: Additional error details
            validation_errors: List of validation errors
            
        Returns:
            JSONResponse with standardized error format
        """
        response_data = {
            "success": False,
            "message": message,
            "error_code": error_code,
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": status_code
        }
        
        if details:
            response_data["details"] = details
            
        if validation_errors:
            response_data["validation_errors"] = validation_errors
            
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @staticmethod
    def list_response(
        items: List[Any],
        total_count: int,
        page: int = 1,
        page_size: int = 50,
        message: str = "Items retrieved successfully",
        filters: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """
        Create a standardized list response with pagination
        
        Args:
            items: List of items
            total_count: Total number of items
            page: Current page number
            page_size: Items per page
            message: Success message
            filters: Applied filters
            
        Returns:
            JSONResponse with list data and pagination
        """
        total_pages = (total_count + page_size - 1) // page_size
        
        pagination = {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
        
        metadata = {
            "item_count": len(items),
            "filters": filters or {}
        }
        
        return ResponseHelper.success_response(
            data=items,
            message=message,
            metadata=metadata,
            pagination=pagination
        )
    
    @staticmethod
    def created_response(
        data: Any = None,
        message: str = "Resource created successfully",
        resource_id: Optional[str] = None
    ) -> JSONResponse:
        """
        Create a standardized created response
        
        Args:
            data: Created resource data
            message: Success message
            resource_id: ID of created resource
            
        Returns:
            JSONResponse with 201 status
        """
        metadata = {"resource_id": resource_id} if resource_id else None
        
        return ResponseHelper.success_response(
            data=data,
            message=message,
            status_code=status.HTTP_201_CREATED,
            metadata=metadata
        )
    
    @staticmethod
    def updated_response(
        data: Any = None,
        message: str = "Resource updated successfully",
        changes: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """
        Create a standardized updated response
        
        Args:
            data: Updated resource data
            message: Success message
            changes: Summary of changes made
            
        Returns:
            JSONResponse with 200 status
        """
        metadata = {"changes": changes} if changes else None
        
        return ResponseHelper.success_response(
            data=data,
            message=message,
            metadata=metadata
        )
    
    @staticmethod
    def deleted_response(
        message: str = "Resource deleted successfully",
        resource_id: Optional[str] = None
    ) -> JSONResponse:
        """
        Create a standardized deleted response
        
        Args:
            message: Success message
            resource_id: ID of deleted resource
            
        Returns:
            JSONResponse with 200 status
        """
        metadata = {"resource_id": resource_id} if resource_id else None
        
        return ResponseHelper.success_response(
            data=None,
            message=message,
            metadata=metadata
        )
    
    @staticmethod
    def partial_response(
        data: Any = None,
        message: str = "Partial response",
        warnings: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """
        Create a standardized partial response (206)
        
        Args:
            data: Partial data
            message: Response message
            warnings: List of warnings
            metadata: Additional metadata
            
        Returns:
            JSONResponse with 206 status
        """
        response_data = {
            "success": True,
            "message": message,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": status.HTTP_206_PARTIAL_CONTENT
        }
        
        if warnings:
            response_data["warnings"] = warnings
            
        if metadata:
            response_data["metadata"] = metadata
            
        return JSONResponse(
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            content=response_data
        )

 
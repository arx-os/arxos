"""
Example Usage of Response Helpers
Demonstrates how to use the centralized response helpers in routers and services
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from datetime import datetime

from .response_helpers import (
    ResponseHelper, success_response, error_response, 
    validation_error_response, not_found_response,
    list_response, created_response, updated_response, deleted_response
)
from .error_handlers import handle_exception, log_error

# Example router using response helpers
router = APIRouter(prefix="/example", tags=["example"])

# Example 1: Basic success response
@router.get("/basic")
async def get_basic_data():
    """Example of basic success response"""
    try:
        data = {"message": "Hello World", "timestamp": datetime.utcnow().isoformat()}
        return success_response(
            data=data,
            message="Basic data retrieved successfully"
        )
    except Exception as e:
        return handle_exception(e)

# Example 2: List response with pagination
@router.get("/list")
async def get_list_data(
    page: int = 1,
    page_size: int = 10
):
    """Example of list response with pagination"""
    try:
        # Simulate data retrieval
        items = [{"id": i, "name": f"Item {i}"} for i in range(1, 101)]
        total_count = len(items)
        
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = items[start:end]
        
        return list_response(
            items=paginated_items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            filters={"page": page, "page_size": page_size}
        )
    except Exception as e:
        return handle_exception(e)

# Example 3: Created response
@router.post("/create")
async def create_resource(data: Dict[str, Any]):
    """Example of created response"""
    try:
        # Simulate resource creation
        resource_id = "resource_123"
        created_data = {**data, "id": resource_id, "created_at": datetime.utcnow().isoformat()}
        
        return created_response(
            data=created_data,
            message="Resource created successfully",
            resource_id=resource_id
        )
    except Exception as e:
        return handle_exception(e)

# Example 4: Updated response
@router.put("/update/{resource_id}")
async def update_resource(resource_id: str, data: Dict[str, Any]):
    """Example of updated response"""
    try:
        # Simulate resource update
        updated_data = {**data, "id": resource_id, "updated_at": datetime.utcnow().isoformat()}
        changes = {"fields_updated": list(data.keys())}
        
        return updated_response(
            data=updated_data,
            message="Resource updated successfully",
            changes=changes
        )
    except Exception as e:
        return handle_exception(e)

# Example 5: Deleted response
@router.delete("/delete/{resource_id}")
async def delete_resource(resource_id: str):
    """Example of deleted response"""
    try:
        # Simulate resource deletion
        return deleted_response(
            message="Resource deleted successfully",
            resource_id=resource_id
        )
    except Exception as e:
        return handle_exception(e)

# Example 6: Error handling with custom error codes
@router.get("/error-examples")
async def error_examples(error_type: str):
    """Example of different error responses"""
    try:
        if error_type == "validation":
            return validation_error_response(
                message="Input validation failed",
                validation_errors=["Field 'name' is required", "Field 'email' must be valid"]
            )
        elif error_type == "not_found":
            return not_found_response(
                message="User not found",
                resource_type="user",
                resource_id="user_123"
            )
        elif error_type == "unauthorized":
            return ResponseHelper.error_response(
                message="Authentication required",
                error_code="UNAUTHORIZED",
                status_code=401,
                details={"required_scopes": ["read:users"]}
            )
        elif error_type == "forbidden":
            return ResponseHelper.error_response(
                message="Insufficient permissions",
                error_code="FORBIDDEN",
                status_code=403,
                details={"required_role": "admin", "current_role": "user"}
            )
        else:
            return success_response(data={"error_type": error_type})
    except Exception as e:
        return handle_exception(e)

# Example 7: Using ResponseHelper class directly
@router.get("/custom")
async def custom_response():
    """Example of using ResponseHelper class directly"""
    try:
        data = {"custom": "data"}
        metadata = {"version": "1.0", "environment": "production"}
        
        return ResponseHelper.success_response(
            data=data,
            message="Custom response",
            metadata=metadata
        )
    except Exception as e:
        return handle_exception(e)

# Example 8: Partial response
@router.get("/partial")
async def partial_response():
    """Example of partial response (206)"""
    try:
        data = {"partial": "data"}
        warnings = ["Some data was truncated", "Rate limit approaching"]
        
        return ResponseHelper.partial_response(
            data=data,
            message="Partial data retrieved",
            warnings=warnings
        )
    except Exception as e:
        return handle_exception(e)

# Example 9: Error logging
@router.get("/logging-example")
async def logging_example():
    """Example of error logging"""
    try:
        # Simulate some operation that might fail
        raise ValueError("Example error for logging")
    except Exception as e:
        # Log the error with context
        log_error(
            message="Failed to process request",
            exc=e,
            context={"endpoint": "/logging-example", "user_id": "user_123"}
        )
        return handle_exception(e)

# Example 10: Service layer integration
class ExampleService:
    """Example service using response helpers"""
    
    @staticmethod
    def get_data_with_validation(data_id: str) -> Dict[str, Any]:
        """Example service method with validation"""
        if not data_id:
            raise ValueError("Data ID is required")
        
        if data_id == "invalid":
            raise ValueError("Invalid data ID format")
        
        # Simulate data retrieval
        return {
            "id": data_id,
            "name": f"Data {data_id}",
            "created_at": datetime.utcnow().isoformat()
        }

@router.get("/service-example/{data_id}")
async def service_example(data_id: str):
    """Example of using response helpers with service layer"""
    try:
        service = ExampleService()
        data = service.get_data_with_validation(data_id)
        
        return success_response(
            data=data,
            message="Data retrieved successfully"
        )
    except ValueError as e:
        return validation_error_response(
            message=str(e),
            validation_errors=[str(e)]
        )
    except Exception as e:
        return handle_exception(e) 
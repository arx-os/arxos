# Migration Guide: Using Centralized Response Helpers

This guide shows how to migrate existing routers and endpoints to use the new centralized response helpers.

## Before: Manual Response Formatting

```python
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}")
async def get_user(user_id: str):
    try:
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "data": user,
            "message": "User retrieved successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": 500
        }

@router.post("/")
async def create_user(user_data: Dict[str, Any]):
    try:
        if not user_data.get("email"):
            raise HTTPException(status_code=400, detail="Email is required")
        
        user = await user_service.create_user(user_data)
        return {
            "success": True,
            "data": user,
            "message": "User created successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": 500
        }
```

## After: Using Response Helpers

```python
from fastapi import APIRouter
from typing import Dict, Any
from utils.response_helpers import (
    success_response, not_found_response, 
    created_response, validation_error_response
)
from utils.error_handlers import handle_exception

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}")
async def get_user(user_id: str):
    try:
        user = await user_service.get_user(user_id)
        if not user:
            return not_found_response(
                message="User not found",
                resource_type="user",
                resource_id=user_id
            )
        
        return success_response(
            data=user,
            message="User retrieved successfully"
        )
    except Exception as e:
        return handle_exception(e)

@router.post("/")
async def create_user(user_data: Dict[str, Any]):
    try:
        if not user_data.get("email"):
            return validation_error_response(
                message="Email is required",
                validation_errors=["Email field is required"]
            )
        
        user = await user_service.create_user(user_data)
        return created_response(
            data=user,
            message="User created successfully",
            resource_id=user["id"]
        )
    except Exception as e:
        return handle_exception(e)
```

## Migration Steps

### 1. Import Response Helpers

Add imports to your router file:

```python
from utils.response_helpers import (
    success_response, error_response, created_response,
    updated_response, deleted_response, not_found_response,
    validation_error_response, list_response
)
from utils.error_handlers import handle_exception, log_error
```

### 2. Replace Manual Responses

#### Before:
```python
return {
    "success": True,
    "data": result,
    "message": "Success"
}
```

#### After:
```python
return success_response(
    data=result,
    message="Success"
)
```

### 3. Replace Error Responses

#### Before:
```python
raise HTTPException(status_code=404, detail="Not found")
```

#### After:
```python
return not_found_response(
    message="Resource not found",
    resource_type="user",
    resource_id=user_id
)
```

### 4. Add Exception Handling

#### Before:
```python
try:
    result = some_operation()
    return {"data": result}
except Exception as e:
    return {"error": str(e)}
```

#### After:
```python
try:
    result = some_operation()
    return success_response(data=result)
except Exception as e:
    return handle_exception(e)
```

## Common Migration Patterns

### List Endpoints

#### Before:
```python
@router.get("/")
async def list_users(page: int = 1, page_size: int = 20):
    users = await user_service.list_users(page, page_size)
    total = await user_service.count_users()
    
    return {
        "success": True,
        "data": users,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total
        }
    }
```

#### After:
```python
@router.get("/")
async def list_users(page: int = 1, page_size: int = 20):
    try:
        users = await user_service.list_users(page, page_size)
        total = await user_service.count_users()
        
        return list_response(
            items=users,
            total_count=total,
            page=page,
            page_size=page_size,
            filters={"page": page, "page_size": page_size}
        )
    except Exception as e:
        return handle_exception(e)
```

### CRUD Operations

#### Create:
```python
return created_response(
    data=new_resource,
    message="Resource created successfully",
    resource_id=new_resource["id"]
)
```

#### Update:
```python
return updated_response(
    data=updated_resource,
    message="Resource updated successfully",
    changes={"fields_updated": ["name", "email"]}
)
```

#### Delete:
```python
return deleted_response(
    message="Resource deleted successfully",
    resource_id=resource_id
)
```

### Validation Errors

#### Before:
```python
if not user_data.get("email"):
    raise HTTPException(status_code=400, detail="Email required")
```

#### After:
```python
if not user_data.get("email"):
    return validation_error_response(
        message="Validation failed",
        validation_errors=["Email is required"]
    )
```

## Benefits of Migration

1. **Consistency** - All responses follow the same format
2. **Maintainability** - Centralized response logic
3. **Error Handling** - Automatic logging and error tracking
4. **Type Safety** - Better IDE support and type checking
5. **Documentation** - Self-documenting response formats
6. **Testing** - Easier to test response formats

## Testing Migrated Endpoints

```python
def test_get_user_success():
    response = client.get("/users/123")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "data" in data
    assert "timestamp" in data

def test_get_user_not_found():
    response = client.get("/users/999")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] == False
    assert data["error_code"] == "NOT_FOUND"
```

## Gradual Migration

You can migrate endpoints gradually:

1. Start with new endpoints
2. Migrate simple GET endpoints
3. Migrate POST/PUT/DELETE endpoints
4. Update error handling last

This allows you to maintain functionality while improving response consistency. 
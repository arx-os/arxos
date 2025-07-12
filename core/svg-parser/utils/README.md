# Arxos SVG Parser - Utils Package

## Overview

The `utils` package provides centralized, reusable utilities for the Arxos SVG Parser service, including standardized response formatting, error handling, and common helper functions.

## 📁 Package Structure

```
utils/
├── __init__.py              # Package initialization and exports
├── response_helpers.py      # Standardized API response formatting
├── error_handlers.py        # Centralized error handling and logging
├── examples.py              # Usage examples and patterns
├── migration_guide.md       # Migration guide for existing code
└── README.md               # This file
```

## 🚀 Quick Start

```python
from utils.response_helpers import success_response, error_response
from utils.error_handlers import handle_exception

# Success response
return success_response(
    data={"user_id": "123", "name": "John Doe"},
    message="User created successfully"
)

# Error response
return error_response(
    message="User not found",
    error_code="USER_NOT_FOUND",
    status_code=404
)

# Exception handling
try:
    # Your code here
    pass
except Exception as e:
    return handle_exception(e)
```

## 📚 Core Modules

### Response Helpers (`response_helpers.py`)

Provides standardized API response formatting for consistent JSON structure across all endpoints.

**Key Features:**
- ✅ Standardized success and error response formats
- ✅ Specialized response types (list, created, updated, deleted)
- ✅ Pagination support for list responses
- ✅ Metadata and context support
- ✅ Convenience functions for common HTTP status codes

**Available Functions:**
- `success_response()` - Standard success responses
- `error_response()` - Standard error responses
- `list_response()` - Paginated list responses
- `created_response()` - Resource creation (201)
- `updated_response()` - Resource updates
- `deleted_response()` - Resource deletion
- `validation_error_response()` - Validation errors (422)
- `not_found_response()` - Not found errors (404)
- `unauthorized_response()` - Authentication errors (401)
- `forbidden_response()` - Permission errors (403)
- `server_error_response()` - Server errors (500)

### Error Handlers (`error_handlers.py`)

Provides centralized exception handling with automatic logging and standardized error responses.

**Key Features:**
- ✅ Automatic exception type detection and handling
- ✅ Structured error logging with context
- ✅ FastAPI exception handler integration
- ✅ Error ID generation for tracking
- ✅ Configurable error mappings

**Available Functions:**
- `handle_exception()` - Centralized exception handling
- `log_error()` - Manual error logging with context
- `http_exception_handler()` - FastAPI HTTPException handler
- `validation_exception_handler()` - FastAPI RequestValidationError handler
- `general_exception_handler()` - General exception handler

## 📖 Usage Examples

### Basic Response Patterns

```python
from utils.response_helpers import success_response, error_response

# Success response with data
return success_response(
    data={"result": "success"},
    message="Operation completed"
)

# Error response with details
return error_response(
    message="Invalid input",
    error_code="VALIDATION_ERROR",
    status_code=400,
    details={"field": "email", "issue": "Invalid format"}
)
```

### List Responses with Pagination

```python
from utils.response_helpers import list_response

return list_response(
    items=users,
    total_count=100,
    page=1,
    page_size=20,
    filters={"role": "admin"}
)
```

### CRUD Operation Responses

```python
from utils.response_helpers import created_response, updated_response, deleted_response

# Create
return created_response(
    data=new_user,
    message="User created successfully",
    resource_id=new_user["id"]
)

# Update
return updated_response(
    data=updated_user,
    message="User updated successfully",
    changes={"fields_updated": ["name", "email"]}
)

# Delete
return deleted_response(
    message="User deleted successfully",
    resource_id=user_id
)
```

### Error Handling

```python
from utils.error_handlers import handle_exception, log_error

# Automatic exception handling
try:
    result = some_operation()
    return success_response(data=result)
except Exception as e:
    return handle_exception(e)

# Manual error logging
try:
    # Your code here
    pass
except Exception as e:
    log_error(
        message="Failed to process user request",
        exc=e,
        context={"user_id": "123", "operation": "update_profile"}
    )
    return server_error_response()
```

## 🔧 Integration

### FastAPI Integration

The error handlers are automatically integrated into the main FastAPI app:

```python
# In app.py
from utils.error_handlers import (
    http_exception_handler, 
    validation_exception_handler, 
    general_exception_handler
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
```

### Router Integration

```python
from fastapi import APIRouter
from utils.response_helpers import success_response, not_found_response
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
```

## 📋 Response Format

### Success Response Format

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {...},
  "timestamp": "2024-01-15T10:30:00Z",
  "status_code": 200,
  "metadata": {...},
  "pagination": {...}
}
```

### Error Response Format

```json
{
  "success": false,
  "message": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z",
  "status_code": 400,
  "details": {...},
  "validation_errors": [...]
}
```

## 🧪 Testing

### Testing Response Helpers

```python
def test_success_response():
    response = success_response(data={"test": "data"})
    assert response.status_code == 200
    content = response.body.decode()
    assert "success" in content
    assert "test" in content

def test_error_response():
    response = error_response(message="Test error")
    assert response.status_code == 400
    content = response.body.decode()
    assert "success" in content
    assert "Test error" in content
```

### Testing Error Handlers

```python
def test_handle_exception():
    try:
        raise ValueError("Test error")
    except Exception as e:
        response = handle_exception(e)
        assert response.status_code == 400
        content = response.body.decode()
        assert "Test error" in content
```

## 🔄 Migration Guide

See `migration_guide.md` for detailed instructions on migrating existing code to use the response helpers.

## 📚 Additional Resources

- **Examples**: See `examples.py` for comprehensive usage examples
- **Migration**: See `migration_guide.md` for migration instructions
- **Main Documentation**: See `../README.md` for overall service documentation

## 🤝 Contributing

When adding new utilities to this package:

1. **Follow the existing patterns** for response formatting and error handling
2. **Add comprehensive docstrings** to all functions
3. **Include usage examples** in the docstrings
4. **Update this README** with new functionality
5. **Add tests** for new utilities

## 📄 License

This package is part of the Arxos platform and follows the same licensing terms. 
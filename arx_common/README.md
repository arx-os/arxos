# Arxos Common Utilities

A centralized shared library for common utility functions used across the Arxos Platform. This package provides standardized implementations for date/time handling, object manipulation, request processing, and other frequently used utilities.

## Overview

The `arx_common` package consolidates duplicate utility code from across the platform into a single, well-tested, and maintainable library. This reduces code duplication, ensures consistency, and improves maintainability.

## Modules

### `date_utils.py`
Date and time manipulation utilities.

**Key Functions:**
- `get_current_timestamp()` - Get current UTC timestamp
- `get_current_timestamp_iso()` - Get current UTC timestamp as ISO string
- `parse_timestamp()` - Parse timestamp from various formats
- `format_timestamp()` - Format datetime to string
- `add_timestamp_to_dict()` - Add current timestamp to dictionary
- `calculate_time_difference()` - Calculate time difference between timestamps
- `is_timestamp_recent()` - Check if timestamp is recent
- `get_relative_time_description()` - Get human-readable relative time
- `create_timestamp_range()` - Create timestamp range for queries
- `validate_date_range()` - Validate that start date is before end date
- `get_quarter_dates()` - Get start and end dates for a quarter
- `get_month_dates()` - Get start and end dates for a month
- `format_duration()` - Format duration in seconds to human-readable string
- `parse_duration()` - Parse duration string to timedelta

### `object_utils.py`
Object manipulation and data structure utilities.

**Key Functions:**
- `flatten_dict()` - Flatten nested dictionary
- `unflatten_dict()` - Unflatten flattened dictionary
- `deep_merge()` - Deep merge two dictionaries
- `remove_none_values()` - Remove None values from dictionary recursively
- `get_nested_value()` - Get nested value using dot notation
- `set_nested_value()` - Set nested value using dot notation
- `object_to_dict()` - Convert object to dictionary
- `dict_to_object()` - Convert dictionary to object
- `validate_required_fields()` - Validate that required fields are present
- `filter_dict()` - Filter dictionary to only include specified keys
- `exclude_dict()` - Filter dictionary to exclude specified keys
- `safe_get()` - Safely get value from dictionary
- `safe_set()` - Safely set value in dictionary
- `compare_objects()` - Compare two objects and return differences
- `serialize_object()` - Serialize object to JSON string
- `deserialize_object()` - Deserialize JSON string to object
- `create_object_id()` - Create unique object ID
- `validate_object_structure()` - Validate object structure against schema

### `request_utils.py`
HTTP request processing and validation utilities.

**Key Functions:**
- `get_client_ip()` - Get client IP address from request
- `get_user_agent()` - Get user agent from request
- `get_request_headers()` - Get request headers
- `get_request_params()` - Get all request parameters
- `validate_required_params()` - Validate that required parameters are present
- `extract_pagination_params()` - Extract pagination parameters
- `extract_sorting_params()` - Extract sorting parameters
- `extract_filter_params()` - Extract filter parameters
- `create_request_context()` - Create standardized request context
- `log_request()` - Log request details
- `validate_content_type()` - Validate request content type
- `extract_json_body()` - Extract JSON body from request
- `validate_request_size()` - Validate request size
- `create_rate_limit_key()` - Create rate limiting key for request
- `extract_api_version()` - Extract API version from request
- `create_correlation_id()` - Create or extract correlation ID
- `validate_request_permissions()` - Validate request permissions
- `sanitize_request_data()` - Sanitize request data by removing sensitive fields
- `create_request_summary()` - Create request summary for logging/monitoring

## Installation

The `arx_common` package is included in the main Arxos Platform repository and can be imported directly:

```python
from arx_common.date_utils import get_current_timestamp_iso
from arx_common.object_utils import flatten_dict
from arx_common.request_utils import get_client_ip
```

## Usage Examples

### Date Utilities

```python
from arx_common.date_utils import get_current_timestamp_iso, parse_timestamp

# Get current timestamp
timestamp = get_current_timestamp_iso()

# Parse timestamp from string
dt = parse_timestamp("2024-01-01T12:00:00")

# Add timestamp to dictionary
data = {"name": "John"}
data_with_timestamp = add_timestamp_to_dict(data)
```

### Object Utilities

```python
from arx_common.object_utils import flatten_dict, object_to_dict

# Flatten nested dictionary
nested = {"user": {"profile": {"name": "John"}}}
flattened = flatten_dict(nested)
# Result: {"user.profile.name": "John"}

# Convert object to dictionary
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

user = User("John", 30)
user_dict = object_to_dict(user)
```

### Request Utilities

```python
from arx_common.request_utils import get_client_ip, create_request_context

# Get client IP
client_ip = get_client_ip(request)

# Create request context
context = create_request_context(request)
```

## Migration Guide

### Before (Duplicate Code)

```python
# Multiple files with duplicate datetime handling
from datetime import datetime

def create_response():
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "data": "response"
    }

# Multiple files with duplicate object flattening
def flatten_data(data):
    # Custom implementation in each file
    pass
```

### After (Shared Utilities)

```python
# Use shared utilities
from arx_common.date_utils import get_current_timestamp_iso
from arx_common.object_utils import flatten_dict

def create_response():
    return {
        "timestamp": get_current_timestamp_iso(),
        "data": "response"
    }

# Use shared flattening
flattened = flatten_dict(data)
```

## Testing

Comprehensive tests are available in the `tests/arx_common/` directory:

- `test_date_utils.py` - Tests for date utilities
- `test_object_utils.py` - Tests for object utilities  
- `test_request_utils.py` - Tests for request utilities

Run tests with:

```bash
pytest tests/arx_common/
```

## Best Practices

### 1. Always Use Shared Utilities
Instead of implementing common functionality in multiple places, use the shared utilities:

```python
# ✅ Good
from arx_common.date_utils import get_current_timestamp_iso

# ❌ Bad
from datetime import datetime
timestamp = datetime.utcnow().isoformat()
```

### 2. Consistent Error Handling
Use the shared utilities for consistent error handling across the platform.

### 3. Structured Logging
All utilities use structured logging with semantic keys for better observability.

### 4. Type Hints
All functions include comprehensive type hints for better IDE support and code clarity.

## Contributing

When adding new utilities to `arx_common`:

1. **Check for existing functionality** - Don't duplicate existing utilities
2. **Add comprehensive tests** - All utilities must have full test coverage
3. **Include type hints** - All functions should have proper type annotations
4. **Add documentation** - Include docstrings and usage examples
5. **Follow naming conventions** - Use descriptive, consistent function names

## Dependencies

The `arx_common` package has minimal dependencies:

- `structlog` - For structured logging
- Standard library modules (`datetime`, `json`, `uuid`, etc.)

## Version History

- **1.0.0** - Initial release with date, object, and request utilities

## License

This package is part of the Arxos Platform and follows the same licensing terms. 
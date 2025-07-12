# Developer Documentation for Arxos Platform

## Overview

This document provides comprehensive developer documentation for the Arxos platform, including data models, handler logic, extension points, and performance optimization guides.

## Table of Contents

1. [Data Models and Relationships](#data-models-and-relationships)
2. [Handler Logic Explanations](#handler-logic-explanations)
3. [Extension Point Documentation](#extension-point-documentation)
4. [Performance Optimization Guides](#performance-optimization-guides)

---

## Data Models and Relationships

### Core Data Models

#### Version Control Models

```python
# Version Model
class Version:
    id: str                    # Unique version identifier
    floor_id: str             # Associated floor ID
    building_id: str          # Associated building ID
    branch: str               # Branch name
    version_number: int       # Sequential version number
    message: str              # Commit message
    version_type: str         # major, minor, patch
    created_by: str           # User who created version
    created_at: datetime      # Creation timestamp
    data_hash: str            # SHA256 hash of data
    object_count: int         # Number of objects in version

# Branch Model
class Branch:
    name: str                 # Branch name
    floor_id: str            # Associated floor ID
    building_id: str         # Associated building ID
    base_version_id: str     # Base version for branch
    description: str         # Branch description
    created_by: str          # User who created branch
    created_at: datetime     # Creation timestamp
    status: str              # active, inactive, merged

# Merge Request Model
class MergeRequest:
    id: str                   # Unique merge request ID
    source_version_id: str    # Source version to merge
    target_version_id: str    # Target version to merge into
    title: str               # Merge request title
    description: str         # Merge request description
    status: str              # open, approved, rejected, merged
    created_by: str          # User who created request
    created_at: datetime     # Creation timestamp
    reviewers: List[str]     # List of reviewer user IDs
    conflicts: List[Conflict] # List of conflicts
```

#### Route Management Models

```python
# Route Model
class Route:
    id: str                   # Unique route identifier
    floor_id: str            # Associated floor ID
    building_id: str         # Associated building ID
    name: str                # Route name
    route_type: str          # evacuation, access, maintenance
    waypoints: List[Waypoint] # List of route waypoints
    properties: RouteProperties # Route properties
    created_by: str          # User who created route
    created_at: datetime     # Creation timestamp
    status: str              # active, inactive, draft

# Waypoint Model
class Waypoint:
    x: float                 # X coordinate
    y: float                 # Y coordinate
    type: str                # start, waypoint, end
    properties: Dict         # Additional waypoint properties

# Route Properties Model
class RouteProperties:
    distance: float          # Total route distance
    estimated_time: int      # Estimated travel time (seconds)
    accessibility: bool      # Accessibility compliance
    capacity: int            # Maximum capacity
    constraints: Dict        # Route constraints
```

#### Floor Management Models

```python
# Floor Model
class Floor:
    id: str                  # Unique floor identifier
    building_id: str         # Associated building ID
    name: str                # Floor name
    level: int               # Floor level number
    area: float              # Floor area
    metadata: Dict           # Floor metadata
    objects: List[Object]    # Floor objects
    routes: List[Route]      # Floor routes
    created_by: str          # User who created floor
    created_at: datetime     # Creation timestamp
    status: str              # active, inactive, archived

# Object Model
class Object:
    id: str                  # Unique object identifier
    type: str                # Object type (room, device, etc.)
    x: float                 # X coordinate
    y: float                 # Y coordinate
    width: float             # Object width (optional)
    height: float            # Object height (optional)
    properties: Dict         # Object properties
    relationships: List[str] # Related object IDs
```

### Data Relationships

#### Entity Relationship Diagram

```
Building (1) ----< Floor (N)
Floor (1) ----< Version (N)
Floor (1) ----< Route (N)
Floor (1) ----< Object (N)
Version (1) ----< Branch (N)
Version (1) ----< MergeRequest (N)
Version (1) ----< Annotation (N)
Version (1) ----< Comment (N)
Route (1) ----< Waypoint (N)
Object (1) ----< Object (N) [relationships]
```

#### Relationship Types

1. **One-to-Many (1:N)**
   - Building → Floors
   - Floor → Versions
   - Floor → Routes
   - Floor → Objects

2. **Many-to-Many (M:N)**
   - Objects ↔ Objects (relationships)
   - Users ↔ MergeRequests (reviewers)

3. **Hierarchical**
   - Building → Floor → Object
   - Version → Branch → MergeRequest

### Data Validation Rules

#### Version Control Validation

```python
# Version validation rules
VERSION_VALIDATION_RULES = {
    "floor_id": {
        "required": True,
        "type": "string",
        "pattern": r"^[a-z0-9-]+$",
        "max_length": 50
    },
    "version_type": {
        "required": True,
        "enum": ["major", "minor", "patch"]
    },
    "message": {
        "required": True,
        "type": "string",
        "max_length": 500
    }
}

# Branch validation rules
BRANCH_VALIDATION_RULES = {
    "branch_name": {
        "required": True,
        "type": "string",
        "pattern": r"^[a-z0-9-_]+$",
        "max_length": 100
    },
    "base_version_id": {
        "required": True,
        "type": "string"
    }
}
```

#### Route Validation

```python
# Route validation rules
ROUTE_VALIDATION_RULES = {
    "name": {
        "required": True,
        "type": "string",
        "max_length": 200
    },
    "route_type": {
        "required": True,
        "enum": ["evacuation", "access", "maintenance"]
    },
    "waypoints": {
        "required": True,
        "type": "array",
        "min_items": 2,
        "max_items": 100
    }
}

# Waypoint validation rules
WAYPOINT_VALIDATION_RULES = {
    "x": {
        "required": True,
        "type": "number",
        "minimum": 0
    },
    "y": {
        "required": True,
        "type": "number",
        "minimum": 0
    },
    "type": {
        "required": True,
        "enum": ["start", "waypoint", "end"]
    }
}
```

---

## Handler Logic Explanations

### Version Control Handlers

#### Version Creation Handler

```python
class VersionControlHandler:
    def create_version(self, request_data):
        """
        Create a new version of floor data.
        
        Logic Flow:
        1. Validate input data
        2. Check user permissions
        3. Generate version ID and number
        4. Calculate data hash
        5. Store version data
        6. Update branch information
        7. Return version details
        """
        
        # Step 1: Validate input data
        validation_result = self.validate_version_data(request_data)
        if not validation_result["valid"]:
            return self.create_error_response(validation_result["errors"])
        
        # Step 2: Check user permissions
        permission_result = self.check_user_permissions(
            request_data["floor_id"], 
            request_data["building_id"], 
            "create_version"
        )
        if not permission_result["allowed"]:
            return self.create_error_response("Permission denied")
        
        # Step 3: Generate version ID and number
        version_id = self.generate_version_id()
        version_number = self.get_next_version_number(
            request_data["floor_id"], 
            request_data["building_id"], 
            request_data["branch"]
        )
        
        # Step 4: Calculate data hash
        data_hash = self.calculate_data_hash(request_data["data"])
        
        # Step 5: Store version data
        version_data = {
            "id": version_id,
            "floor_id": request_data["floor_id"],
            "building_id": request_data["building_id"],
            "branch": request_data["branch"],
            "version_number": version_number,
            "message": request_data["message"],
            "version_type": request_data["version_type"],
            "created_by": request_data["user_id"],
            "created_at": datetime.utcnow(),
            "data_hash": data_hash,
            "object_count": len(request_data["data"]["objects"])
        }
        
        self.store_version_data(version_data, request_data["data"])
        
        # Step 6: Update branch information
        self.update_branch_latest_version(
            request_data["floor_id"],
            request_data["building_id"],
            request_data["branch"],
            version_id
        )
        
        # Step 7: Return version details
        return self.create_success_response({
            "version_id": version_id,
            "version_number": version_number,
            "data_hash": data_hash,
            "version": version_data
        })
```

#### Branch Management Handler

```python
class BranchHandler:
    def create_branch(self, request_data):
        """
        Create a new branch from an existing version.
        
        Logic Flow:
        1. Validate branch data
        2. Check if branch already exists
        3. Verify base version exists
        4. Create branch record
        5. Set up branch tracking
        6. Return branch details
        """
        
        # Step 1: Validate branch data
        validation_result = self.validate_branch_data(request_data)
        if not validation_result["valid"]:
            return self.create_error_response(validation_result["errors"])
        
        # Step 2: Check if branch already exists
        existing_branch = self.get_branch(
            request_data["branch_name"],
            request_data["floor_id"],
            request_data["building_id"]
        )
        if existing_branch:
            return self.create_error_response("Branch already exists")
        
        # Step 3: Verify base version exists
        base_version = self.get_version(request_data["base_version_id"])
        if not base_version:
            return self.create_error_response("Base version not found")
        
        # Step 4: Create branch record
        branch_data = {
            "name": request_data["branch_name"],
            "floor_id": request_data["floor_id"],
            "building_id": request_data["building_id"],
            "base_version_id": request_data["base_version_id"],
            "description": request_data.get("description", ""),
            "created_by": request_data["user_id"],
            "created_at": datetime.utcnow(),
            "status": "active"
        }
        
        self.store_branch_data(branch_data)
        
        # Step 5: Set up branch tracking
        self.initialize_branch_tracking(branch_data)
        
        # Step 6: Return branch details
        return self.create_success_response({
            "branch_name": request_data["branch_name"],
            "branch": branch_data
        })
```

### Route Management Handlers

#### Route Creation Handler

```python
class RouteHandler:
    def create_route(self, request_data):
        """
        Create a new route with waypoints and properties.
        
        Logic Flow:
        1. Validate route data
        2. Check floor exists
        3. Validate waypoints
        4. Calculate route properties
        5. Store route data
        6. Return route details
        """
        
        # Step 1: Validate route data
        validation_result = self.validate_route_data(request_data)
        if not validation_result["valid"]:
            return self.create_error_response(validation_result["errors"])
        
        # Step 2: Check floor exists
        floor = self.get_floor(request_data["floor_id"])
        if not floor:
            return self.create_error_response("Floor not found")
        
        # Step 3: Validate waypoints
        waypoint_validation = self.validate_waypoints(
            request_data["waypoints"],
            request_data["floor_id"]
        )
        if not waypoint_validation["valid"]:
            return self.create_error_response(waypoint_validation["errors"])
        
        # Step 4: Calculate route properties
        route_properties = self.calculate_route_properties(
            request_data["waypoints"],
            request_data.get("properties", {})
        )
        
        # Step 5: Store route data
        route_data = {
            "id": self.generate_route_id(),
            "floor_id": request_data["floor_id"],
            "building_id": request_data["building_id"],
            "name": request_data["name"],
            "route_type": request_data["route_type"],
            "waypoints": request_data["waypoints"],
            "properties": route_properties,
            "created_by": request_data["user_id"],
            "created_at": datetime.utcnow(),
            "status": "active"
        }
        
        self.store_route_data(route_data)
        
        # Step 6: Return route details
        return self.create_success_response({
            "route_id": route_data["id"],
            "route": route_data
        })
```

#### Route Optimization Handler

```python
class RouteOptimizationHandler:
    def optimize_route(self, route_id, optimization_params):
        """
        Optimize an existing route based on specified criteria.
        
        Logic Flow:
        1. Retrieve current route
        2. Analyze optimization requirements
        3. Apply optimization algorithm
        4. Validate optimized route
        5. Update route data
        6. Return optimization results
        """
        
        # Step 1: Retrieve current route
        current_route = self.get_route(route_id)
        if not current_route:
            return self.create_error_response("Route not found")
        
        # Step 2: Analyze optimization requirements
        optimization_type = optimization_params.get("optimization_type", "shortest_path")
        constraints = optimization_params.get("constraints", {})
        
        # Step 3: Apply optimization algorithm
        if optimization_type == "shortest_path":
            optimized_waypoints = self.optimize_shortest_path(
                current_route["waypoints"],
                constraints
            )
        elif optimization_type == "accessibility":
            optimized_waypoints = self.optimize_accessibility(
                current_route["waypoints"],
                constraints
            )
        else:
            return self.create_error_response("Invalid optimization type")
        
        # Step 4: Validate optimized route
        validation_result = self.validate_optimized_route(
            optimized_waypoints,
            current_route["floor_id"]
        )
        if not validation_result["valid"]:
            return self.create_error_response("Optimized route validation failed")
        
        # Step 5: Update route data
        updated_properties = self.calculate_route_properties(optimized_waypoints)
        original_distance = current_route["properties"]["distance"]
        optimized_distance = updated_properties["distance"]
        
        savings_percentage = ((original_distance - optimized_distance) / original_distance) * 100
        
        route_data = {
            **current_route,
            "waypoints": optimized_waypoints,
            "properties": updated_properties,
            "optimization_metrics": {
                "original_distance": original_distance,
                "optimized_distance": optimized_distance,
                "savings_percentage": savings_percentage
            }
        }
        
        self.update_route_data(route_id, route_data)
        
        # Step 6: Return optimization results
        return self.create_success_response({
            "route": route_data,
            "optimization_results": {
                "type": optimization_type,
                "savings_percentage": savings_percentage,
                "constraints_applied": constraints
            }
        })
```

---

## Extension Point Documentation

### Plugin Architecture

The Arxos platform supports a plugin architecture that allows developers to extend functionality through various extension points.

#### Extension Point Types

1. **Data Processors**: Process and transform data
2. **Validation Rules**: Custom validation logic
3. **Optimization Algorithms**: Custom optimization strategies
4. **Export Formats**: Custom export formats
5. **Integration Hooks**: Integration with external systems

### Data Processor Extensions

#### Custom Data Processor

```python
from arxos.extensions import DataProcessor

class CustomDataProcessor(DataProcessor):
    """Custom data processor for specialized data transformation."""
    
    def __init__(self, config):
        super().__init__(config)
        self.processor_name = "custom_processor"
        self.version = "1.0.0"
    
    def process_floor_data(self, floor_data):
        """
        Process floor data with custom logic.
        
        Args:
            floor_data (dict): Floor data to process
            
        Returns:
            dict: Processed floor data
        """
        processed_data = floor_data.copy()
        
        # Apply custom processing logic
        for obj in processed_data.get("objects", []):
            if obj["type"] == "room":
                obj["processed_area"] = obj.get("width", 0) * obj.get("height", 0)
                obj["processing_timestamp"] = datetime.utcnow().isoformat()
        
        return processed_data
    
    def validate_config(self, config):
        """Validate processor configuration."""
        required_fields = ["custom_setting"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required config field: {field}")
        
        return True
```

#### Registering Data Processors

```python
# Register custom data processor
from arxos.registry import ExtensionRegistry

registry = ExtensionRegistry()

# Register processor
registry.register_data_processor(
    "custom_processor",
    CustomDataProcessor,
    {
        "custom_setting": "value",
        "enabled": True
    }
)

# Use processor in version control
version_handler = VersionControlHandler()
version_handler.add_data_processor("custom_processor")
```

### Validation Rule Extensions

#### Custom Validation Rule

```python
from arxos.extensions import ValidationRule

class CustomValidationRule(ValidationRule):
    """Custom validation rule for specialized validation logic."""
    
    def __init__(self, config):
        super().__init__(config)
        self.rule_name = "custom_validation"
        self.priority = 100
    
    def validate_floor_data(self, floor_data):
        """
        Validate floor data with custom rules.
        
        Args:
            floor_data (dict): Floor data to validate
            
        Returns:
            dict: Validation result
        """
        errors = []
        warnings = []
        
        # Custom validation logic
        for obj in floor_data.get("objects", []):
            if obj["type"] == "room":
                area = obj.get("width", 0) * obj.get("height", 0)
                if area < self.config.get("min_room_area", 10):
                    errors.append(f"Room {obj['id']} is too small: {area}")
                
                if area > self.config.get("max_room_area", 1000):
                    warnings.append(f"Room {obj['id']} is very large: {area}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
```

### Optimization Algorithm Extensions

#### Custom Optimization Algorithm

```python
from arxos.extensions import OptimizationAlgorithm

class CustomOptimizationAlgorithm(OptimizationAlgorithm):
    """Custom optimization algorithm for specialized route optimization."""
    
    def __init__(self, config):
        super().__init__(config)
        self.algorithm_name = "custom_optimization"
        self.version = "1.0.0"
    
    def optimize_route(self, waypoints, constraints):
        """
        Optimize route using custom algorithm.
        
        Args:
            waypoints (list): List of waypoints
            constraints (dict): Optimization constraints
            
        Returns:
            list: Optimized waypoints
        """
        optimized_waypoints = waypoints.copy()
        
        # Custom optimization logic
        if constraints.get("avoid_obstacles", False):
            optimized_waypoints = self.avoid_obstacles(optimized_waypoints)
        
        if constraints.get("minimize_distance", False):
            optimized_waypoints = self.minimize_distance(optimized_waypoints)
        
        if constraints.get("prefer_accessible", False):
            optimized_waypoints = self.prefer_accessible_routes(optimized_waypoints)
        
        return optimized_waypoints
    
    def avoid_obstacles(self, waypoints):
        """Avoid obstacles in route."""
        # Implementation for obstacle avoidance
        return waypoints
    
    def minimize_distance(self, waypoints):
        """Minimize total route distance."""
        # Implementation for distance minimization
        return waypoints
    
    def prefer_accessible_routes(self, waypoints):
        """Prefer accessible routes."""
        # Implementation for accessibility preference
        return waypoints
```

### Export Format Extensions

#### Custom Export Format

```python
from arxos.extensions import ExportFormat

class CustomExportFormat(ExportFormat):
    """Custom export format for specialized data export."""
    
    def __init__(self, config):
        super().__init__(config)
        self.format_name = "custom_format"
        self.file_extension = ".custom"
        self.mime_type = "application/custom"
    
    def export_floor_data(self, floor_data, export_options):
        """
        Export floor data in custom format.
        
        Args:
            floor_data (dict): Floor data to export
            export_options (dict): Export options
            
        Returns:
            bytes: Exported data
        """
        # Custom export logic
        export_data = {
            "format": self.format_name,
            "version": "1.0.0",
            "exported_at": datetime.utcnow().isoformat(),
            "floor_data": floor_data,
            "export_options": export_options
        }
        
        # Convert to custom format
        if export_options.get("format_type") == "json":
            return json.dumps(export_data, indent=2).encode()
        elif export_options.get("format_type") == "xml":
            return self.convert_to_xml(export_data)
        else:
            return self.convert_to_binary(export_data)
    
    def convert_to_xml(self, data):
        """Convert data to XML format."""
        # XML conversion implementation
        pass
    
    def convert_to_binary(self, data):
        """Convert data to binary format."""
        # Binary conversion implementation
        pass
```

### Integration Hook Extensions

#### Custom Integration Hook

```python
from arxos.extensions import IntegrationHook

class CustomIntegrationHook(IntegrationHook):
    """Custom integration hook for external system integration."""
    
    def __init__(self, config):
        super().__init__(config)
        self.hook_name = "custom_integration"
        self.events = ["version_created", "route_updated"]
    
    def on_version_created(self, version_data):
        """
        Handle version creation event.
        
        Args:
            version_data (dict): Version data
        """
        # Integration logic for version creation
        self.notify_external_system("version_created", version_data)
    
    def on_route_updated(self, route_data):
        """
        Handle route update event.
        
        Args:
            route_data (dict): Route data
        """
        # Integration logic for route updates
        self.notify_external_system("route_updated", route_data)
    
    def notify_external_system(self, event_type, data):
        """Notify external system of events."""
        # External system notification implementation
        pass
```

---

## Performance Optimization Guides

### Database Optimization

#### Indexing Strategies

```sql
-- Create indexes for frequently queried fields
CREATE INDEX idx_versions_floor_building ON versions(floor_id, building_id);
CREATE INDEX idx_versions_branch ON versions(branch);
CREATE INDEX idx_versions_created_at ON versions(created_at);
CREATE INDEX idx_routes_floor ON routes(floor_id);
CREATE INDEX idx_objects_floor ON objects(floor_id);

-- Composite indexes for complex queries
CREATE INDEX idx_versions_floor_branch_created ON versions(floor_id, branch, created_at);
CREATE INDEX idx_routes_floor_type ON routes(floor_id, route_type);
```

#### Query Optimization

```python
# Optimized version history query
def get_optimized_version_history(floor_id, building_id, limit=50, offset=0):
    """
    Optimized version history query with pagination.
    """
    query = """
        SELECT v.*, u.username as created_by_name
        FROM versions v
        LEFT JOIN users u ON v.created_by = u.id
        WHERE v.floor_id = ? AND v.building_id = ?
        ORDER BY v.created_at DESC
        LIMIT ? OFFSET ?
    """
    
    # Use prepared statements
    cursor = db.cursor()
    cursor.execute(query, (floor_id, building_id, limit, offset))
    
    return cursor.fetchall()

# Optimized route query with joins
def get_optimized_routes_with_objects(floor_id):
    """
    Optimized route query with related objects.
    """
    query = """
        SELECT r.*, 
               COUNT(o.id) as object_count,
               AVG(o.x) as avg_object_x,
               AVG(o.y) as avg_object_y
        FROM routes r
        LEFT JOIN objects o ON r.floor_id = o.floor_id
        WHERE r.floor_id = ?
        GROUP BY r.id
        ORDER BY r.created_at DESC
    """
    
    cursor = db.cursor()
    cursor.execute(query, (floor_id,))
    
    return cursor.fetchall()
```

### Caching Strategies

#### Redis Caching Implementation

```python
import redis
import json
from functools import wraps

class CacheManager:
    def __init__(self, redis_config):
        self.redis_client = redis.Redis(**redis_config)
        self.default_ttl = 3600  # 1 hour
    
    def cache_result(self, key, ttl=None):
        """Decorator for caching function results."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = f"{key}:{hash(str(args) + str(kwargs))}"
                
                # Try to get from cache
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    return json.loads(cached_result)
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.redis_client.setex(
                    cache_key,
                    ttl or self.default_ttl,
                    json.dumps(result)
                )
                
                return result
            return wrapper
        return decorator

# Usage example
cache_manager = CacheManager({
    "host": "localhost",
    "port": 6379,
    "db": 0
})

@cache_manager.cache_result("version_history", ttl=1800)
def get_version_history(floor_id, building_id):
    """Get version history with caching."""
    # Implementation
    pass
```

#### Memory Caching

```python
from functools import lru_cache
import time

class MemoryCache:
    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.cache = {}
        self.access_times = {}
    
    def get(self, key):
        """Get value from cache."""
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        return None
    
    def set(self, key, value, ttl=3600):
        """Set value in cache with TTL."""
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def _evict_oldest(self):
        """Evict oldest accessed item."""
        oldest_key = min(self.access_times, key=self.access_times.get)
        del self.cache[oldest_key]
        del self.access_times[oldest_key]

# Usage with LRU cache decorator
@lru_cache(maxsize=100)
def get_cached_floor_data(floor_id):
    """Get floor data with LRU caching."""
    # Implementation
    pass
```

### API Performance Optimization

#### Response Compression

```python
from flask import Flask, request, Response
import gzip
import json

app = Flask(__name__)

def compress_response(data):
    """Compress response data."""
    json_data = json.dumps(data)
    compressed_data = gzip.compress(json_data.encode('utf-8'))
    return compressed_data

@app.route('/api/floors/<floor_id>')
def get_floor(floor_id):
    """Get floor data with compression."""
    floor_data = get_floor_data(floor_id)
    
    # Check if client accepts gzip
    if 'gzip' in request.headers.get('Accept-Encoding', ''):
        compressed_data = compress_response(floor_data)
        response = Response(compressed_data)
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Type'] = 'application/json'
        return response
    
    return jsonify(floor_data)
```

#### Pagination Implementation

```python
def get_paginated_results(query, page=1, per_page=50):
    """
    Implement pagination for large result sets.
    """
    offset = (page - 1) * per_page
    
    # Get total count
    count_query = f"SELECT COUNT(*) FROM ({query}) as subquery"
    total_count = db.execute(count_query).scalar()
    
    # Get paginated results
    paginated_query = f"{query} LIMIT {per_page} OFFSET {offset}"
    results = db.execute(paginated_query).fetchall()
    
    return {
        "results": results,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
            "total_pages": (total_count + per_page - 1) // per_page,
            "has_next": page * per_page < total_count,
            "has_prev": page > 1
        }
    }
```

### Concurrency and Async Processing

#### Async Route Optimization

```python
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

class AsyncRouteOptimizer:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def optimize_routes_batch(self, routes):
        """
        Optimize multiple routes concurrently.
        """
        tasks = []
        for route in routes:
            task = asyncio.create_task(
                self.optimize_single_route(route)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def optimize_single_route(self, route):
        """
        Optimize a single route asynchronously.
        """
        loop = asyncio.get_event_loop()
        
        # Run CPU-intensive optimization in thread pool
        optimized_waypoints = await loop.run_in_executor(
            self.executor,
            self.cpu_intensive_optimization,
            route["waypoints"]
        )
        
        return {
            "route_id": route["id"],
            "optimized_waypoints": optimized_waypoints
        }
    
    def cpu_intensive_optimization(self, waypoints):
        """
        CPU-intensive optimization algorithm.
        """
        # Implementation of optimization algorithm
        pass
```

#### Background Task Processing

```python
from celery import Celery
import redis

# Configure Celery
celery_app = Celery('arxos_tasks')
celery_app.config_from_object('celeryconfig')

@celery_app.task
def optimize_route_background(route_id):
    """
    Background task for route optimization.
    """
    try:
        # Get route data
        route = get_route(route_id)
        if not route:
            return {"success": False, "error": "Route not found"}
        
        # Perform optimization
        optimized_waypoints = optimize_route_algorithm(route["waypoints"])
        
        # Update route
        update_route(route_id, {"waypoints": optimized_waypoints})
        
        return {"success": True, "route_id": route_id}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

@celery_app.task
def export_floor_data_background(floor_id, export_format):
    """
    Background task for floor data export.
    """
    try:
        # Get floor data
        floor_data = get_floor_data(floor_id)
        
        # Export data
        export_result = export_floor_data(floor_data, export_format)
        
        # Store export result
        store_export_result(floor_id, export_format, export_result)
        
        return {"success": True, "export_id": export_result["id"]}
    
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Monitoring and Profiling

#### Performance Monitoring

```python
import time
import logging
from functools import wraps

class PerformanceMonitor:
    def __init__(self):
        self.logger = logging.getLogger('performance')
    
    def monitor_performance(self, operation_name):
        """Decorator for monitoring operation performance."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = self.get_memory_usage()
                
                try:
                    result = func(*args, **kwargs)
                    success = True
                except Exception as e:
                    success = False
                    raise e
                finally:
                    end_time = time.time()
                    end_memory = self.get_memory_usage()
                    
                    duration = end_time - start_time
                    memory_used = end_memory - start_memory
                    
                    self.log_performance(
                        operation_name,
                        duration,
                        memory_used,
                        success
                    )
                
                return result
            return wrapper
        return decorator
    
    def get_memory_usage(self):
        """Get current memory usage."""
        import psutil
        return psutil.Process().memory_info().rss
    
    def log_performance(self, operation, duration, memory_used, success):
        """Log performance metrics."""
        self.logger.info(
            f"Performance: {operation} | "
            f"Duration: {duration:.3f}s | "
            f"Memory: {memory_used/1024/1024:.2f}MB | "
            f"Success: {success}"
        )

# Usage example
monitor = PerformanceMonitor()

@monitor.monitor_performance("get_version_history")
def get_version_history(floor_id, building_id):
    """Get version history with performance monitoring."""
    # Implementation
    pass
```

# Developer Documentation - Viewport Manager

## Overview

This document provides comprehensive technical documentation for developers integrating and extending the Arxos SVG-BIM viewport manager. It covers API reference, integration patterns, customization options, and best practices.

## Table of Contents

1. [API Reference](#api-reference)
2. [Integration Guide](#integration-guide)
3. [Customization](#customization)
4. [Event System](#event-system)
5. [Performance Optimization](#performance-optimization)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## API Reference

### ViewportManager Class

#### Constructor
```javascript
new ViewportManager(svgElement, options)
```

**Parameters:**
- `svgElement` (HTMLElement): The SVG element to manage
- `options` (Object): Configuration options

**Options:**
```javascript
{
    minZoom: 0.1,              // Minimum zoom level
    maxZoom: 5.0,              // Maximum zoom level
    zoomStep: 0.1,             // Zoom increment
    maxHistorySize: 50,        // Maximum history entries
    enableTouchGestures: true, // Enable touch support
    coordinateSystem: 'meters', // Coordinate system units
    performanceMode: 'auto',   // Performance optimization
    panBoundaries: {           // Pan boundary settings
        enabled: true,
        maxDistance: 2000
    }
}
```

#### Core Methods

##### Zoom Operations
```javascript
// Set zoom level
viewport.setZoom(zoomLevel)

// Get current zoom level
const zoom = viewport.getZoom()

// Zoom in by one step
viewport.zoomIn()

// Zoom out by one step
viewport.zoomOut()

// Zoom to fit all content
viewport.zoomToFit()

// Reset zoom to 100%
viewport.resetZoom()
```

##### Pan Operations
```javascript
// Set pan position
viewport.setPan(x, y)

// Get current pan position
const [x, y] = viewport.getPan()

// Pan by offset
viewport.panBy(deltaX, deltaY)

// Center view on coordinates
viewport.centerOn(x, y)
```

##### Coordinate Conversion
```javascript
// Convert screen coordinates to SVG coordinates
const [svgX, svgY] = viewport.screenToSVG(screenX, screenY)

// Convert SVG coordinates to screen coordinates
const [screenX, screenY] = viewport.svgToScreen(svgX, svgY)

// Get current viewport bounds
const bounds = viewport.getViewportBounds()
```

##### History Management
```javascript
// Undo last zoom operation
const success = viewport.undoZoom()

// Redo last zoom operation
const success = viewport.redoZoom()

// Clear zoom history
viewport.clearZoomHistory()

// Get history information
const history = viewport.getZoomHistory()
```

##### Event Management
```javascript
// Add event listener
viewport.addEventListener(eventType, handler)

// Remove event listener
viewport.removeEventListener(eventType, handler)

// Trigger custom event
viewport.triggerEvent(eventType, data)
```

#### Properties

```javascript
// Current zoom level
viewport.zoom

// Current pan position
viewport.panX
viewport.panY

// Zoom history
viewport.zoomHistory

// History index
viewport.historyIndex

// Configuration
viewport.config

// Touch state
viewport.touchState

// Performance metrics
viewport.performanceMetrics
```

## Integration Guide

### Basic Integration

#### 1. Include the Library
```html
<script src="viewport-manager.js"></script>
```

#### 2. Create SVG Element
```html
<svg id="building-model" width="800" height="600">
    <!-- Your building model content -->
</svg>
```

#### 3. Initialize Viewport Manager
```javascript
const svgElement = document.getElementById('building-model');
const viewport = new ViewportManager(svgElement, {
    minZoom: 0.1,
    maxZoom: 5.0,
    enableTouchGestures: true
});
```

#### 4. Add Event Listeners
```javascript
viewport.addEventListener('zoomChanged', (data) => {
    console.log('Zoom changed:', data.zoom);
    updateZoomDisplay(data.zoom);
});

viewport.addEventListener('panChanged', (data) => {
    console.log('Pan changed:', data.x, data.y);
    updatePanDisplay(data.x, data.y);
});
```

### Advanced Integration

#### Custom Controls
```javascript
// Custom zoom controls
document.getElementById('zoom-in').addEventListener('click', () => {
    viewport.zoomIn();
});

document.getElementById('zoom-out').addEventListener('click', () => {
    viewport.zoomOut();
});

document.getElementById('zoom-fit').addEventListener('click', () => {
    viewport.zoomToFit();
});

// Custom pan controls
document.getElementById('pan-left').addEventListener('click', () => {
    viewport.panBy(-100, 0);
});

document.getElementById('pan-right').addEventListener('click', () => {
    viewport.panBy(100, 0);
});
```

#### Coordinate Display
```javascript
// Update coordinate display
function updateCoordinateDisplay(event) {
    const [svgX, svgY] = viewport.screenToSVG(event.clientX, event.clientY);
    document.getElementById('coordinates').textContent = 
        `X: ${svgX.toFixed(3)} Y: ${svgY.toFixed(3)}`;
}

svgElement.addEventListener('mousemove', updateCoordinateDisplay);
```

#### Performance Monitoring
```javascript
// Monitor performance
setInterval(() => {
    const metrics = viewport.performanceMetrics;
    console.log('FPS:', metrics.fps);
    console.log('Memory Usage:', metrics.memoryUsage);
    console.log('Render Time:', metrics.renderTime);
}, 1000);
```

## Customization

### Custom Zoom Behavior
```javascript
class CustomViewportManager extends ViewportManager {
    constructor(svgElement, options) {
        super(svgElement, options);
        this.customZoomBehavior = true;
    }

    setZoom(zoom) {
        // Custom zoom logic
        const adjustedZoom = this.adjustZoomForCustomBehavior(zoom);
        super.setZoom(adjustedZoom);
    }

    adjustZoomForCustomBehavior(zoom) {
        // Implement custom zoom adjustment
        return zoom * 1.1; // Example: 10% boost
    }
}
```

### Custom Coordinate System
```javascript
class CustomCoordinateSystem {
    constructor(originX, originY, scale) {
        this.originX = originX;
        this.originY = originY;
        this.scale = scale;
    }

    convertToRealWorld(screenX, screenY) {
        return {
            x: (screenX - this.originX) * this.scale,
            y: (screenY - this.originY) * this.scale
        };
    }

    convertToScreen(realX, realY) {
        return {
            x: realX / this.scale + this.originX,
            y: realY / this.scale + this.originY
        };
    }
}
```

### Custom Event Handlers
```javascript
// Custom zoom handler with analytics
function customZoomHandler(data) {
    // Track zoom usage
    analytics.track('viewport_zoom', {
        zoomLevel: data.zoom,
        timestamp: Date.now()
    });

    // Update UI
    updateZoomIndicator(data.zoom);
    
    // Trigger custom logic
    if (data.zoom > 3.0) {
        showHighZoomWarning();
    }
}

viewport.addEventListener('zoomChanged', customZoomHandler);
```

## Event System

### Available Events

#### Navigation Events
```javascript
// Zoom events
viewport.addEventListener('zoomChanged', (data) => {
    // data.zoom: new zoom level
    // data.previousZoom: previous zoom level
    // data.source: 'mouse', 'keyboard', 'touch', 'programmatic'
});

// Pan events
viewport.addEventListener('panChanged', (data) => {
    // data.x: new x position
    // data.y: new y position
    // data.previousX: previous x position
    // data.previousY: previous y position
});

// Viewport events
viewport.addEventListener('viewportChanged', (data) => {
    // data.zoom: current zoom
    // data.x: current x position
    // data.y: current y position
    // data.bounds: viewport bounds
});
```

#### History Events
```javascript
// History events
viewport.addEventListener('historyChanged', (data) => {
    // data.canUndo: boolean
    // data.canRedo: boolean
    // data.historySize: number
});

// Undo/redo events
viewport.addEventListener('undoPerformed', (data) => {
    // data.zoom: restored zoom level
    // data.x: restored x position
    // data.y: restored y position
});

viewport.addEventListener('redoPerformed', (data) => {
    // data.zoom: restored zoom level
    // data.x: restored x position
    // data.y: restored y position
});
```

#### Performance Events
```javascript
// Performance events
viewport.addEventListener('performanceWarning', (data) => {
    // data.type: 'memory', 'cpu', 'fps'
    // data.value: current value
    // data.threshold: threshold value
});

viewport.addEventListener('constraintViolation', (data) => {
    // data.type: 'zoom', 'pan'
    // data.value: attempted value
    // data.limit: constraint limit
});
```

### Custom Events
```javascript
// Trigger custom events
viewport.triggerEvent('customAction', {
    action: 'symbolSelected',
    symbolId: 'door-001',
    coordinates: { x: 100, y: 200 }
});

// Listen for custom events
viewport.addEventListener('customAction', (data) => {
    console.log('Custom action:', data);
});
```

## Performance Optimization

### Configuration Optimization
```javascript
// Performance-focused configuration
const performanceConfig = {
    minZoom: 0.2,              // Higher minimum zoom
    maxZoom: 3.0,              // Lower maximum zoom
    maxHistorySize: 25,        // Smaller history
    performanceMode: 'high',   // High performance mode
    enableTouchGestures: false, // Disable if not needed
    throttleUpdates: true      // Enable throttling
};
```

### Memory Management
```javascript
// Monitor memory usage
function monitorMemory() {
    const metrics = viewport.performanceMetrics;
    if (metrics.memoryUsage > 100) { // 100MB threshold
        console.warn('High memory usage detected');
        viewport.clearZoomHistory();
    }
}

setInterval(monitorMemory, 5000);
```

### Rendering Optimization
```javascript
// Optimize rendering for large models
function optimizeRendering() {
    const zoom = viewport.getZoom();
    const symbolCount = getSymbolCount();
    
    if (symbolCount > 1000 && zoom < 0.5) {
        // Enable level of detail
        enableLOD();
    } else {
        disableLOD();
    }
}

viewport.addEventListener('zoomChanged', optimizeRendering);
```

## Testing

### Unit Testing
```javascript
// Example test using Jest
describe('ViewportManager', () => {
    let viewport;
    let svgElement;

    beforeEach(() => {
        svgElement = document.createElement('svg');
        viewport = new ViewportManager(svgElement);
    });

    test('should set zoom level correctly', () => {
        viewport.setZoom(2.0);
        expect(viewport.getZoom()).toBe(2.0);
    });

    test('should respect zoom constraints', () => {
        viewport.setZoom(10.0); // Beyond max
        expect(viewport.getZoom()).toBe(5.0); // Max zoom
    });

    test('should convert coordinates correctly', () => {
        viewport.setZoom(2.0);
        viewport.setPan(100, 200);
        
        const [svgX, svgY] = viewport.screenToSVG(200, 400);
        expect(svgX).toBe(50); // (200 - 100) / 2
        expect(svgY).toBe(100); // (400 - 200) / 2
    });
});
```

### Integration Testing
```javascript
// Example integration test
describe('Viewport Integration', () => {
    test('should integrate with symbol library', () => {
        const symbolLibrary = new SymbolLibrary();
        const viewport = new ViewportManager(svgElement);
        
        // Add symbol to viewport
        const symbol = symbolLibrary.createSymbol('door');
        viewport.addSymbol(symbol);
        
        // Test symbol interaction
        const symbols = viewport.getSymbolsAt(100, 200);
        expect(symbols).toContain(symbol);
    });
});
```

### Performance Testing
```javascript
// Performance test
describe('Viewport Performance', () => {
    test('should handle high-frequency zoom operations', () => {
        const startTime = performance.now();
        
        for (let i = 0; i < 1000; i++) {
            viewport.setZoom(Math.random() * 5);
        }
        
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        expect(duration).toBeLessThan(1000); // Should complete in <1 second
    });
});
```

## Troubleshooting

### Common Issues

#### Performance Problems
```javascript
// Check performance metrics
const metrics = viewport.performanceMetrics;
console.log('Performance metrics:', metrics);

// Common solutions
if (metrics.fps < 30) {
    // Reduce zoom level
    viewport.setZoom(Math.min(viewport.getZoom(), 2.0));
    
    // Clear history
    viewport.clearZoomHistory();
    
    // Enable performance mode
    viewport.setPerformanceMode('high');
}
```

#### Memory Leaks
```javascript
// Check for memory leaks
function checkMemoryLeaks() {
    const initialMemory = performance.memory.usedJSHeapSize;
    
    // Perform operations
    for (let i = 0; i < 100; i++) {
        viewport.setZoom(Math.random() * 5);
    }
    
    const finalMemory = performance.memory.usedJSHeapSize;
    const memoryIncrease = finalMemory - initialMemory;
    
    if (memoryIncrease > 10 * 1024 * 1024) { // 10MB threshold
        console.warn('Potential memory leak detected');
    }
}
```

#### Event Listener Issues
```javascript
// Debug event listeners
function debugEventListeners() {
    const events = viewport.getEventListeners();
    console.log('Active event listeners:', events);
    
    // Check for duplicate listeners
    const duplicates = findDuplicateListeners(events);
    if (duplicates.length > 0) {
        console.warn('Duplicate listeners found:', duplicates);
    }
}
```

### Debug Mode
```javascript
// Enable debug mode
const viewport = new ViewportManager(svgElement, {
    debug: true,
    logLevel: 'verbose'
});

// Debug information will be logged to console
```

## Best Practices

### Code Organization
```javascript
// Separate concerns
class ViewportController {
    constructor(svgElement) {
        this.viewport = new ViewportManager(svgElement);
        this.setupEventHandlers();
        this.setupUI();
    }
    
    setupEventHandlers() {
        this.viewport.addEventListener('zoomChanged', this.handleZoom.bind(this));
        this.viewport.addEventListener('panChanged', this.handlePan.bind(this));
    }
    
    setupUI() {
        // Setup UI controls
    }
    
    handleZoom(data) {
        // Handle zoom changes
    }
    
    handlePan(data) {
        // Handle pan changes
    }
}
```

### Error Handling
```javascript
// Robust error handling
class SafeViewportManager {
    constructor(svgElement, options) {
        try {
            this.viewport = new ViewportManager(svgElement, options);
            this.setupErrorHandling();
        } catch (error) {
            console.error('Failed to initialize viewport:', error);
            this.fallbackToBasicViewport();
        }
    }
    
    setupErrorHandling() {
        this.viewport.addEventListener('error', (error) => {
            console.error('Viewport error:', error);
            this.handleError(error);
        });
    }
    
    handleError(error) {
        // Implement error recovery
        switch (error.type) {
            case 'constraint_violation':
                this.handleConstraintViolation(error);
                break;
            case 'performance_warning':
                this.handlePerformanceWarning(error);
                break;
            default:
                this.handleGenericError(error);
        }
    }
}
```

### Performance Optimization
```javascript
// Performance optimization patterns
class OptimizedViewportManager {
    constructor(svgElement, options) {
        this.viewport = new ViewportManager(svgElement, {
            ...options,
            throttleUpdates: true,
            performanceMode: 'high'
        });
        
        this.setupPerformanceMonitoring();
    }
    
    setupPerformanceMonitoring() {
        // Monitor and optimize performance
        setInterval(() => {
            this.optimizePerformance();
        }, 1000);
    }
    
    optimizePerformance() {
        const metrics = this.viewport.performanceMetrics;
        
        if (metrics.fps < 30) {
            this.enablePerformanceMode();
        }
        
        if (metrics.memoryUsage > 100) {
            this.cleanupMemory();
        }
    }
}
```

### Testing Strategy
```javascript
// Comprehensive testing strategy
describe('ViewportManager Testing', () => {
    // Unit tests for individual methods
    describe('Unit Tests', () => {
        test('zoom operations');
        test('pan operations');
        test('coordinate conversion');
    });
    
    // Integration tests for component interaction
    describe('Integration Tests', () => {
        test('symbol library integration');
        test('event system integration');
        test('performance monitoring');
    });
    
    // Performance tests for optimization
    describe('Performance Tests', () => {
        test('high-frequency operations');
        test('memory usage');
        test('rendering performance');
    });
    
    // Browser compatibility tests
    describe('Browser Tests', () => {
        test('Chrome compatibility');
        test('Firefox compatibility');
        test('Safari compatibility');
        test('Edge compatibility');
    });
});
```

---

**Documentation Version**: 1.0.0
**Last Updated**: [Current Date]
**Target Audience**: Developers and Technical Users
**Compatibility**: Viewport Manager v1.0.0+ 
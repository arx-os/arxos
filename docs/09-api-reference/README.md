# API Reference

## Complete API Documentation for Arxos

This documentation covers all APIs for the Arxos system, including Rust core functions, WASM bindings, SQL queries, and REST endpoints. The API is designed for bidirectional translation between AR interfaces and compressed spatial data.

### 📖 Section Contents

1. **[Core API](core-api.md)** - Rust core library functions
2. **[WASM API](wasm-api.md)** - JavaScript bindings for web/mobile
3. **[SQL API](sql-api.md)** - Database queries and operations  
4. **[REST API](rest-api.md)** - HTTP endpoints for integration
5. **[AR Bridge API](ar-bridge-api.md)** - iOS/Android AR integration

## 🎯 API Design Principles

### Bidirectional by Design
Every operation supports both directions:
- **Forward**: Reality → AR → ArxObject → SQL → Query
- **Reverse**: Query → SQL → ArxObject → AR → Reality

### Type Safety First
```rust
// All APIs use strongly typed structures
pub struct ArxObject {
    pub id: Uuid,
    pub object_type: ObjectType, // Enum, not string
    pub position: Position3D,    // Validated coordinates
    pub properties: Properties,   // Typed property bag
}

// Not this:
// pub fn mark_object(data: HashMap<String, Any>) // Too loose!
```

### Offline-First Operations
```rust
// Every API works offline
pub trait OfflineCapable {
    fn execute_local(&self) -> Result<T>;
    fn sync_when_available(&self) -> SyncHandle;
    fn resolve_conflicts(&self) -> ConflictResolution;
}
```

## 🏗️ Core API Overview

### Spatial Compression

```rust
/// Compress point cloud to ArxObject with semantic understanding
pub fn compress_point_cloud(
    points: &[Point3D],
    options: CompressionOptions
) -> Result<ArxObject, CompressionError> {
    // Semantic recognition
    let structure = recognize_structure(points)?;
    
    // Geometric simplification
    let simplified = simplify_geometry(&structure)?;
    
    // Create ArxObject
    Ok(ArxObject::from_simplified(simplified))
}

/// Options for compression algorithm
pub struct CompressionOptions {
    pub target_ratio: f32,      // Default: 10000.0
    pub preserve_detail: bool,   // Keep fine details
    pub semantic_hints: Vec<ObjectType>, // Expected object types
}
```

### AR Markup Interface

```rust
/// Convert AR tap to world position
pub fn ar_tap_to_world(
    screen_point: CGPoint,
    ar_session: &ARSession
) -> Result<Position3D, ARError> {
    let ray = ar_session.raycast(screen_point)?;
    Ok(ray.intersection_point())
}

/// Create markup from AR interaction
pub fn create_ar_markup(
    position: Position3D,
    object_type: ObjectType,
    properties: Properties,
    user: &User
) -> Result<ARMarkup, ValidationError> {
    validate_position(&position)?;
    validate_properties(&object_type, &properties)?;
    
    Ok(ARMarkup {
        id: Uuid::new_v4(),
        position,
        object_type,
        properties,
        created_by: user.id,
        created_at: Utc::now(),
        bilt_earned: calculate_bilt(&object_type, &properties, user),
    })
}
```

### SQL Operations

```rust
/// Store ArxObject in SQLite database
pub fn store_arxobject(
    conn: &Connection,
    obj: &ArxObject
) -> Result<(), DatabaseError> {
    let sql = "
        INSERT INTO arxobjects (
            id, building_id, object_type, 
            position_x, position_y, position_z,
            properties, created_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ";
    
    conn.execute(sql, params![
        obj.id,
        obj.building_id,
        obj.object_type.to_string(),
        obj.position.x,
        obj.position.y,
        obj.position.z,
        serde_json::to_string(&obj.properties)?,
        obj.created_by,
        obj.created_at
    ])?;
    
    // Update spatial index
    update_spatial_index(conn, obj)?;
    
    Ok(())
}

/// Query objects near a point
pub fn query_nearby(
    conn: &Connection,
    center: Position3D,
    radius_meters: f32
) -> Result<Vec<ArxObject>, DatabaseError> {
    let sql = "
        SELECT a.* FROM arxobjects a
        JOIN arxobjects_spatial s ON a.id = s.id
        WHERE s.min_x <= ? AND s.max_x >= ?
          AND s.min_y <= ? AND s.max_y >= ?
          AND s.min_z <= ? AND s.max_z >= ?
    ";
    
    let radius_mm = (radius_meters * 1000.0) as i32;
    let results = conn.prepare(sql)?
        .query_map(params![
            center.x + radius_mm, center.x - radius_mm,
            center.y + radius_mm, center.y - radius_mm,
            center.z + radius_mm, center.z - radius_mm
        ], |row| ArxObject::from_row(row))?
        .collect::<Result<Vec<_>, _>>()?;
    
    Ok(results)
}
```

## 💻 WASM JavaScript API

### Initialization

```javascript
// Load WASM module
import init, { 
    ArxosEngine,
    compressPointCloud,
    createMarkup,
    queryNearby 
} from './arxos_wasm.js';

async function initialize() {
    await init();
    
    const engine = new ArxosEngine();
    await engine.loadDatabase('./building.db');
    
    return engine;
}
```

### Point Cloud Compression

```javascript
// Compress LiDAR scan to ArxObject
async function compressScan(pointCloud) {
    const compressed = await compressPointCloud(
        new Float32Array(pointCloud),
        {
            targetRatio: 10000,
            preserveDetail: false,
            semanticHints: ['wall', 'door', 'window']
        }
    );
    
    console.log(`Compressed ${pointCloud.length} points to ${compressed.size} bytes`);
    console.log(`Ratio: ${compressed.compressionRatio}:1`);
    
    return compressed;
}
```

### AR Markup Creation

```javascript
// Handle AR tap and create markup
async function handleARTap(screenX, screenY) {
    // Get 3D position from screen coordinates
    const position = await arSession.hitTest(screenX, screenY);
    
    // Show object selection menu
    const objectType = await showObjectMenu();
    
    // Get details from user
    const properties = await showDetailForm(objectType);
    
    // Create markup
    const markup = await createMarkup({
        position: position,
        objectType: objectType,
        properties: properties,
        userId: currentUser.id
    });
    
    // Display confirmation
    showSuccess(`+${markup.biltEarned} BILT earned!`);
    
    return markup;
}
```

## 🔍 SQL Query API

### Spatial Queries

```sql
-- Find all outlets on a specific circuit
CREATE PROCEDURE find_outlets_on_circuit(
    IN building_id TEXT,
    IN circuit_number TEXT
)
BEGIN
    SELECT 
        id,
        room_name,
        position_x,
        position_y,
        position_z,
        json_extract(properties, '$.voltage') as voltage,
        json_extract(properties, '$.amperage') as amperage
    FROM arxobjects
    WHERE building_id = building_id
      AND object_type = 'outlet'
      AND json_extract(properties, '$.circuit') = circuit_number
    ORDER BY room_name, position_x, position_y;
END;

-- Calculate emergency egress routes
CREATE PROCEDURE calculate_egress_routes(
    IN start_position_id TEXT,
    IN max_distance_meters REAL
)
BEGIN
    WITH RECURSIVE paths AS (
        -- Recursive CTE to find paths
        -- ... (see full implementation in sql-api.md)
    )
    SELECT * FROM paths
    WHERE destination_type = 'emergency_exit'
    ORDER BY total_distance
    LIMIT 3;
END;
```

### Aggregation Queries

```sql
-- Building completion statistics
CREATE VIEW building_completion AS
SELECT 
    b.id,
    b.name,
    COUNT(DISTINCT a.floor_number) as floors_mapped,
    COUNT(DISTINCT a.room_id) as rooms_mapped,
    COUNT(a.id) as total_objects,
    ROUND(AVG(CASE 
        WHEN a.verification_status = 'verified' THEN 100.0 
        ELSE 0.0 
    END), 1) as verification_percentage,
    SUM(a.bilt_awarded) as total_bilt_awarded
FROM buildings b
LEFT JOIN arxobjects a ON b.id = a.building_id
GROUP BY b.id;
```

## 🌐 REST API Endpoints

### BIM File Operations

```http
POST /api/v1/buildings/{id}/import
Content-Type: multipart/form-data
Authorization: Bearer {token}

{
    "file": <binary data>,
    "type": "pdf|ifc|dwg|rvt",
    "description": "Floor plan revision 3",
    "replaceExisting": true
}

Response: 202 Accepted
{
    "importId": "import-123",
    "status": "processing",
    "estimatedCompletion": "2024-01-15T14:30:00Z"
}

GET /api/v1/imports/{importId}/status
Response: 200 OK
{
    "status": "completed",
    "roomsExtracted": 28,
    "equipmentDetected": 157,
    "validationIssues": 3,
    "coordinateAlignment": "manual_review_needed"
}
```

### Validation Operations

```http
POST /api/v1/buildings/{id}/validate
Content-Type: application/json

{
    "validateAgainst": "reality|code|both",
    "components": ["rooms", "equipment", "egress"],
    "codeStandards": ["IBC2021", "NFPA101"]
}

Response: 200 OK
{
    "validationId": "val-456",
    "discrepancies": [
        {
            "type": "missing_in_reality",
            "component": "Fire extinguisher",
            "location": "Room 127",
            "severity": "high"
        },
        {
            "type": "code_violation", 
            "component": "Emergency exit",
            "issue": "Exit blocked by equipment",
            "codeSection": "IBC 1003.6"
        }
    ],
    "complianceScore": 0.87
}
```

### BIM Sync Operations

```http
PUT /api/v1/buildings/{id}/sync
Content-Type: application/json

{
    "direction": "reality_to_bim|bim_to_reality|bidirectional",
    "autoApprove": false,
    "notifyStakeholders": true
}

Response: 200 OK
{
    "syncId": "sync-789",
    "changesDetected": 15,
    "changesApplied": 12,
    "pendingApproval": 3,
    "bimFilesUpdated": [
        "/shared/BIM/jefferson_elementary.ifc",
        "/cad/electrical_plan.dwg"
    ]
}
```

### Object Management

```http
POST /api/v1/arxobjects
Content-Type: application/json
Authorization: Bearer {token}

{
    "buildingId": "jefferson-elementary",
    "objectType": "outlet",
    "position": {
        "x": 5420,
        "y": 3180,
        "z": 300
    },
    "properties": {
        "circuit": "A-12",
        "voltage": 120,
        "amperage": 15
    }
}

Response: 201 Created
{
    "id": "a4f7c891-23b4-4d89-b012-34567890abcd",
    "biltEarned": 20,
    "message": "Outlet marked successfully"
}
```

### Spatial Queries

```http
GET /api/v1/buildings/{id}/nearby?lat=27.9506&lon=-82.4572&radius=10

Response: 200 OK
{
    "objects": [
        {
            "id": "...",
            "type": "fire_extinguisher",
            "distance": 3.2,
            "properties": {...}
        }
    ],
    "count": 5
}
```

### BILT Operations

```http
GET /api/v1/users/{id}/bilt/balance

Response: 200 OK
{
    "balance": 3420,
    "lifetimeEarned": 12580,
    "lifetimeRedeemed": 9160,
    "pendingRedemptions": []
}

POST /api/v1/bilt/redeem
{
    "userId": "...",
    "itemId": "gift-card-home-depot-10",
    "quantity": 1
}

Response: 200 OK
{
    "redemptionId": "...",
    "code": "HD-XXXX-XXXX-XXXX",
    "newBalance": 2420
}
```

## 📱 AR Bridge API (iOS)

### Swift Integration

```swift
// ArxosARBridge - Swift to WASM bridge
public class ArxosARBridge {
    private let wasmEngine: ArxosWASMEngine
    private let arSession: ARSession
    
    /// Initialize AR bridge with WASM engine
    public init() {
        self.wasmEngine = ArxosWASMEngine()
        self.arSession = ARSession()
        configureARSession()
    }
    
    /// Process LiDAR point cloud
    public func processPointCloud(_ pointCloud: ARPointCloud) -> ArxObject {
        // Convert to format WASM expects
        let points = pointCloud.points.map { point in
            Float32Point(x: point.x, y: point.y, z: point.z)
        }
        
        // Call WASM compression
        return wasmEngine.compressPointCloud(points)
    }
    
    /// Handle AR tap for markup
    public func handleTap(at screenPoint: CGPoint) -> ARMarkup? {
        guard let query = arView.raycastQuery(
            from: screenPoint,
            allowing: .existingPlaneGeometry,
            alignment: .any
        ) else { return nil }
        
        let results = arSession.raycast(query)
        guard let first = results.first else { return nil }
        
        let position = Position3D(
            x: first.worldTransform.columns.3.x,
            y: first.worldTransform.columns.3.y,
            z: first.worldTransform.columns.3.z
        )
        
        return createMarkup(at: position)
    }
}
```

### Android Integration

```kotlin
// ArxosARBridge - Kotlin to WASM bridge
class ArxosARBridge(context: Context) {
    private val wasmEngine = ArxosWASMEngine(context)
    private lateinit var arSession: Session
    
    /**
     * Initialize AR session with ARCore
     */
    fun initialize() {
        arSession = Session(context)
        configureSession()
    }
    
    /**
     * Process depth map from ARCore
     */
    fun processDepthMap(depthImage: Image): ArxObject {
        val points = convertDepthToPoints(depthImage)
        return wasmEngine.compressPointCloud(points)
    }
    
    /**
     * Handle AR tap for markup
     */
    fun handleTap(x: Float, y: Float): ARMarkup? {
        val frame = arSession.update()
        val hitResults = frame.hitTest(x, y)
        
        if (hitResults.isNotEmpty()) {
            val hit = hitResults[0]
            val position = Position3D(
                hit.hitPose.tx(),
                hit.hitPose.ty(),
                hit.hitPose.tz()
            )
            
            return createMarkup(position)
        }
        
        return null
    }
}
```

## 🔧 Error Handling

### Standard Error Types

```rust
#[derive(Debug, Error)]
pub enum ArxosError {
    #[error("Compression failed: {0}")]
    CompressionError(String),
    
    #[error("Invalid position: {0}")]
    InvalidPosition(String),
    
    #[error("Database error: {0}")]
    DatabaseError(#[from] rusqlite::Error),
    
    #[error("AR tracking lost")]
    ARTrackingLost,
    
    #[error("Insufficient BILT balance")]
    InsufficientBilt,
    
    #[error("Network error: {0}")]
    NetworkError(String),
}

// All APIs return Result<T, ArxosError>
pub fn example_api() -> Result<ArxObject, ArxosError> {
    // Implementation
}
```

## 📊 Performance Guarantees

### API Performance SLAs

| Operation | Target | Maximum |
|-----------|--------|---------|
| Point cloud compression (1M points) | 300ms | 500ms |
| AR tap to markup | 50ms | 100ms |
| Spatial query (10K objects) | 20ms | 50ms |
| BILT calculation | 5ms | 10ms |
| Database insert | 10ms | 20ms |
| Sync operation | 1s | 5s |

### Resource Constraints

```rust
pub struct ResourceLimits {
    pub max_memory_mb: usize,        // 100 MB
    pub max_cpu_percent: f32,        // 50%
    pub max_battery_drain: f32,      // 5% per hour
    pub max_network_bandwidth: u32,  // 100 KB/s
}
```

---

*Complete API documentation with type safety, offline operation, and bidirectional translation*
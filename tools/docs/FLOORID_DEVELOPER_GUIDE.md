# FloorID Integration Developer Guide

## Overview

This guide provides comprehensive documentation for developers implementing and extending FloorID functionality in the Arxos connector system. It covers the technical architecture, implementation details, validation rules, and best practices for floor-based connector management.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Data Model](#data-model)
3. [API Implementation](#api-implementation)
4. [Validation Logic](#validation-logic)
5. [Database Schema](#database-schema)
6. [Frontend Integration](#frontend-integration)
7. [Testing Strategy](#testing-strategy)
8. [Migration Guide](#migration-guide)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Architecture Overview

### FloorID Integration Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │    │   API Layer     │    │   Database      │
│                 │    │                 │    │                 │
│ • Floor Filter  │◄──►│ • Validation    │◄──►│ • Connectors    │
│ • Floor Grouping│    │ • Consistency   │    │ • Floors        │
│ • Floor Badges  │    │ • Floor Checks  │    │ • Relationships │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Principles

1. **FloorID Required**: All connectors must have a valid floor_id
2. **Floor Consistency**: Connected objects must be on the same floor
3. **Floor Validation**: Geometry must be within floor boundaries
4. **Floor Organization**: UI groups and filters by floor

## Data Model

### Connector Model Structure

```go
type Connector struct {
    BIMObject
    ConnectorType     string   `json:"connector_type" gorm:"not null"`
    ConnectionType    string   `json:"connection_type" gorm:"not null"`
    ConnectionStatus  string   `json:"connection_status" gorm:"not null"`
    MaxCapacity       float64  `json:"max_capacity" gorm:"not null"`
    CurrentLoad       float64  `json:"current_load" gorm:"not null"`
    FloorID           uint     `json:"floor_id" gorm:"not null;index"`
    ConnectedTo       []string `json:"connected_to" gorm:"type:json"`
    Description       string   `json:"description"`
}
```

### Floor Model Reference

```go
type Floor struct {
    ID         uint      `json:"id" gorm:"primaryKey"`
    Name       string    `json:"name" gorm:"not null"`
    BuildingID uint      `json:"building_id" gorm:"not null;index"`
    Level      int       `json:"level"`
    CreatedAt  time.Time `json:"created_at"`
    UpdatedAt  time.Time `json:"updated_at"`
}
```

### Validation Rules

```go
func (c *Connector) ValidateConnector() error {
    if err := c.ValidateBIMObject(); err != nil {
        return err
    }
    
    // FloorID validation
    if c.FloorID == 0 {
        return fmt.Errorf("floor_id is required and must be > 0")
    }
    
    // Capacity validation
    if c.MaxCapacity < 0 {
        return fmt.Errorf("max_capacity cannot be negative")
    }
    
    if c.CurrentLoad < 0 {
        return fmt.Errorf("current_load cannot be negative")
    }
    
    if c.CurrentLoad > c.MaxCapacity {
        return fmt.Errorf("current_load cannot exceed max_capacity")
    }
    
    return nil
}
```

## API Implementation

### Endpoint Structure

#### Connector CRUD Endpoints

```go
// Create connector with FloorID
POST /api/connectors
{
    "object_id": "CONN_001",
    "name": "Electrical Connector A",
    "floor_id": 5,
    "connector_type": "electrical",
    // ... other fields
}

// Get connector with floor info
GET /api/connectors/{id}
Response: {
    "connector": {...},
    "floor": {
        "id": 5,
        "name": "5th Floor",
        "building_id": 1
    }
}

// Update connector with floor validation
PUT /api/connectors/{id}
{
    "floor_id": 5,
    "connected_to": ["DEVICE_001", "DEVICE_002"]
    // Floor consistency check performed
}

// List connectors with floor filtering
GET /api/connectors?floor_id=5&system=electrical

// Get connectors by floor
GET /api/connectors/floor/{floor_id}
```

#### BIM Model Endpoints

```go
// Get BIM model including connectors
GET /api/bim/floor/{id}
Response: {
    "floor": {...},
    "bim_model": {
        "rooms": [...],
        "devices": [...],
        "connectors": [...],  // FloorID included
        "panels": [...]
    }
}

// Save BIM model with FloorID validation
POST /api/bim/floor/{id}
{
    "bim_model": {
        "connectors": [
            {
                "object_id": "CONN_001",
                "floor_id": 5,  // Must match floor ID
                // ... other fields
            }
        ]
    }
}
```

### Handler Implementation

#### Create Connector Handler

```go
func CreateConnector(w http.ResponseWriter, r *http.Request) {
    // Parse request
    var connector models.Connector
    if err := json.NewDecoder(r.Body).Decode(&connector); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }
    
    // FloorID validation
    if connector.FloorID == 0 {
        http.Error(w, "floor_id is required", http.StatusBadRequest)
        return
    }
    
    // Verify floor exists
    var floor models.Floor
    if err := db.DB.First(&floor, connector.FloorID).Error; err != nil {
        http.Error(w, "Floor not found", http.StatusBadRequest)
        return
    }
    
    // Geometry bounds check
    if connector.Geometry.Points != nil {
        for _, pt := range connector.Geometry.Points {
            if pt.X < 0 || pt.Y < 0 || pt.X > 10000 || pt.Y > 10000 {
                http.Error(w, "Connector geometry points must be within floor bounds", http.StatusBadRequest)
                return
            }
        }
    }
    
    // Validate connector
    if err := connector.ValidateConnector(); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    
    // Create connector
    if err := db.DB.Create(&connector).Error; err != nil {
        http.Error(w, "Database error", http.StatusInternalServerError)
        return
    }
    
    // Return response with floor info
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]interface{}{
        "connector": connector,
        "floor": floor,
    })
}
```

#### Update Connector Handler

```go
func UpdateConnector(w http.ResponseWriter, r *http.Request) {
    // Get connector ID
    connectorID := chi.URLParam(r, "id")
    
    // Parse update data
    var updateData models.Connector
    if err := json.NewDecoder(r.Body).Decode(&updateData); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }
    
    // Get existing connector
    var connector models.Connector
    if err := db.DB.Where("object_id = ?", connectorID).First(&connector).Error; err != nil {
        http.Error(w, "Connector not found", http.StatusNotFound)
        return
    }
    
    // Floor consistency check for connected objects
    if updateData.ConnectedTo != nil {
        for _, objID := range updateData.ConnectedTo {
            var floorID uint
            
            // Check device
            var device models.Device
            if err := db.DB.Where("object_id = ?", objID).First(&device).Error; err == nil {
                floorID = device.FloorID
            } else {
                // Check room
                var room models.Room
                if err := db.DB.Where("object_id = ?", objID).First(&room).Error; err == nil {
                    floorID = room.FloorID
                } else {
                    http.Error(w, "Connected object not found: "+objID, http.StatusBadRequest)
                    return
                }
            }
            
            if floorID != connector.FloorID {
                http.Error(w, "Connected object must be on same floor", http.StatusBadRequest)
                return
            }
        }
    }
    
    // Update connector
    if err := db.DB.Model(&connector).Updates(updateData).Error; err != nil {
        http.Error(w, "Database error", http.StatusInternalServerError)
        return
    }
    
    // Return updated connector
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(connector)
}
```

## Validation Logic

### Floor Consistency Validation

```go
func validateFloorConsistency(connector *models.Connector, connectedObjects []string) error {
    for _, objID := range connectedObjects {
        var floorID uint
        
        // Try to find device
        var device models.Device
        if err := db.DB.Where("object_id = ?", objID).First(&device).Error; err == nil {
            floorID = device.FloorID
        } else {
            // Try to find room
            var room models.Room
            if err := db.DB.Where("object_id = ?", objID).First(&room).Error; err == nil {
                floorID = room.FloorID
            } else {
                return fmt.Errorf("connected object not found: %s", objID)
            }
        }
        
        if floorID != connector.FloorID {
            return fmt.Errorf("connected object %s must be on same floor as connector", objID)
        }
    }
    
    return nil
}
```

### Geometry Bounds Validation

```go
func validateGeometryBounds(geometry models.Geometry, floorID uint) error {
    if geometry.Points == nil {
        return nil
    }
    
    // Basic bounds check (0 <= x,y <= 10000)
    for _, pt := range geometry.Points {
        if pt.X < 0 || pt.Y < 0 || pt.X > 10000 || pt.Y > 10000 {
            return fmt.Errorf("geometry points must be within floor bounds (0 <= x,y <= 10000)")
        }
    }
    
    // TODO: Add floor-specific bounds validation using floor geometry
    return nil
}
```

## Database Schema

### Connectors Table

```sql
CREATE TABLE connectors (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    object_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    object_type VARCHAR(50) NOT NULL DEFAULT 'connector',
    type VARCHAR(50) NOT NULL,
    system VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    connector_type VARCHAR(50) NOT NULL,
    connection_type VARCHAR(50) NOT NULL,
    connection_status VARCHAR(50) NOT NULL,
    max_capacity DECIMAL(10,2) NOT NULL,
    current_load DECIMAL(10,2) NOT NULL,
    floor_id BIGINT NOT NULL,
    geometry JSON,
    connected_to JSON,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_floor_id (floor_id),
    INDEX idx_system (system),
    INDEX idx_connector_type (connector_type),
    INDEX idx_status (status),
    INDEX idx_created_by (created_by),
    
    FOREIGN KEY (floor_id) REFERENCES floors(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

### Migration Script

```sql
-- Add FloorID to existing connectors (if any)
UPDATE connectors SET floor_id = 1 WHERE floor_id IS NULL OR floor_id = 0;

-- Add NOT NULL constraint
ALTER TABLE connectors MODIFY COLUMN floor_id BIGINT NOT NULL;

-- Add index for performance
CREATE INDEX idx_connectors_floor_id ON connectors(floor_id);
```

## Frontend Integration

### JavaScript Connector Manager

```javascript
class ConnectorManager {
    constructor() {
        this.connectors = [];
        this.floors = [];
        this.currentFloorFilter = null;
    }
    
    // Load connectors with floor filtering
    async loadConnectors(floorId = null) {
        const params = new URLSearchParams();
        if (floorId) {
            params.append('floor_id', floorId);
        }
        
        const response = await fetch(`/api/connectors?${params}`);
        const data = await response.json();
        
        this.connectors = data.results;
        this.renderConnectorList();
    }
    
    // Group connectors by floor
    groupConnectorsByFloor() {
        const grouped = {};
        
        this.connectors.forEach(connector => {
            const floorId = connector.floor_id;
            if (!grouped[floorId]) {
                grouped[floorId] = [];
            }
            grouped[floorId].push(connector);
        });
        
        return grouped;
    }
    
    // Render connector list with floor grouping
    renderConnectorList() {
        const container = document.getElementById('connector-list');
        const grouped = this.groupConnectorsByFloor();
        
        let html = '';
        
        Object.keys(grouped).forEach(floorId => {
            const floor = this.getFloorInfo(floorId);
            const connectors = grouped[floorId];
            
            html += `
                <div class="floor-group">
                    <h3 class="floor-header">
                        ${floor ? floor.name : `Floor ${floorId}`}
                        <span class="connector-count">(${connectors.length})</span>
                    </h3>
                    <div class="connector-list">
                        ${connectors.map(connector => this.renderConnector(connector)).join('')}
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
    
    // Render individual connector with floor badge
    renderConnector(connector) {
        const floor = this.getFloorInfo(connector.floor_id);
        
        return `
            <div class="connector-item">
                <div class="connector-header">
                    <span class="connector-name">${connector.name}</span>
                    <span class="floor-badge">${floor ? floor.name : `Floor ${connector.floor_id}`}</span>
                </div>
                <div class="connector-details">
                    <span class="connector-type">${connector.connector_type}</span>
                    <span class="connection-status">${connector.connection_status}</span>
                </div>
            </div>
        `;
    }
}
```

### Context Panel Integration

```javascript
class ContextPanel {
    // Show connector details with floor information
    showConnectorDetails(connector) {
        const floorInfo = this.getFloorInfo(connector.floor_id);
        
        this.content.innerHTML = `
            <div class="connector-details">
                <div class="floor-indicator">
                    <span class="floor-badge">Floor: ${floorInfo ? floorInfo.name : connector.floor_id}</span>
                </div>
                
                <form class="connector-form">
                    <div class="form-group">
                        <label>Name</label>
                        <input type="text" name="name" value="${connector.name}">
                    </div>
                    
                    <div class="form-group">
                        <label>Floor</label>
                        <select name="floor_id" required>
                            ${this.floors.map(floor => 
                                `<option value="${floor.id}" ${floor.id === connector.floor_id ? 'selected' : ''}>
                                    ${floor.name}
                                </option>`
                            ).join('')}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Connector Type</label>
                        <select name="connector_type">
                            <option value="electrical" ${connector.connector_type === 'electrical' ? 'selected' : ''}>Electrical</option>
                            <option value="hvac" ${connector.connector_type === 'hvac' ? 'selected' : ''}>HVAC</option>
                            <option value="plumbing" ${connector.connector_type === 'plumbing' ? 'selected' : ''}>Plumbing</option>
                            <option value="data" ${connector.connector_type === 'data' ? 'selected' : ''}>Data</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Connection Type</label>
                        <select name="connection_type">
                            <option value="male" ${connector.connection_type === 'male' ? 'selected' : ''}>Male</option>
                            <option value="female" ${connector.connection_type === 'female' ? 'selected' : ''}>Female</option>
                            <option value="both" ${connector.connection_type === 'both' ? 'selected' : ''}>Both</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Connection Status</label>
                        <select name="connection_status">
                            <option value="connected" ${connector.connection_status === 'connected' ? 'selected' : ''}>Connected</option>
                            <option value="disconnected" ${connector.connection_status === 'disconnected' ? 'selected' : ''}>Disconnected</option>
                            <option value="pending" ${connector.connection_status === 'pending' ? 'selected' : ''}>Pending</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label>Max Capacity</label>
                        <input type="number" name="max_capacity" value="${connector.max_capacity}" step="0.01">
                    </div>
                    
                    <div class="form-group">
                        <label>Current Load</label>
                        <input type="number" name="current_load" value="${connector.current_load}" step="0.01">
                    </div>
                    
                    <button type="submit" class="btn btn-primary">Update Connector</button>
                </form>
            </div>
        `;
    }
}
```

## Testing Strategy

### Unit Tests

```go
func TestConnectorValidation(t *testing.T) {
    tests := []struct {
        name    string
        connector models.Connector
        wantErr bool
    }{
        {
            name: "valid connector",
            connector: models.Connector{
                BIMObject: models.BIMObject{
                    ObjectID: "CONN_001",
                    Name: "Test Connector",
                    FloorID: 1,
                },
                ConnectorType: "electrical",
                MaxCapacity: 100.0,
                CurrentLoad: 50.0,
            },
            wantErr: false,
        },
        {
            name: "missing floor_id",
            connector: models.Connector{
                BIMObject: models.BIMObject{
                    ObjectID: "CONN_002",
                    Name: "Test Connector",
                    FloorID: 0,
                },
                ConnectorType: "electrical",
                MaxCapacity: 100.0,
                CurrentLoad: 50.0,
            },
            wantErr: true,
        },
        {
            name: "capacity exceeded",
            connector: models.Connector{
                BIMObject: models.BIMObject{
                    ObjectID: "CONN_003",
                    Name: "Test Connector",
                    FloorID: 1,
                },
                ConnectorType: "electrical",
                MaxCapacity: 100.0,
                CurrentLoad: 150.0,
            },
            wantErr: true,
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := tt.connector.ValidateConnector()
            if (err != nil) != tt.wantErr {
                t.Errorf("ValidateConnector() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

### Integration Tests

```go
func TestConnectorCRUD(t *testing.T) {
    // Setup test database
    db := setupTestDB(t)
    defer cleanupTestDB(t, db)
    
    // Create test user and floor
    user := createTestUser(t, "test@example.com", "testuser", "admin")
    building := createTestBuilding(t, user.ID)
    floor := createTestFloor(t, building.ID, "Test Floor")
    
    // Test creating connector
    connectorData := models.Connector{
        BIMObject: models.BIMObject{
            ObjectID: "TEST_CONN_001",
            Name: "Test Electrical Connector",
            FloorID: floor.ID,
        },
        ConnectorType: "electrical",
        ConnectionType: "male",
        ConnectionStatus: "connected",
        MaxCapacity: 100.0,
        CurrentLoad: 75.0,
    }
    
    // Test API endpoint
    reqBody, _ := json.Marshal(connectorData)
    req := httptest.NewRequest("POST", "/api/connectors", bytes.NewBuffer(reqBody))
    req.Header.Set("Authorization", "Bearer "+user.Token)
    
    w := httptest.NewRecorder()
    handlers.CreateConnector(w, req)
    
    assert.Equal(t, http.StatusOK, w.Code)
    
    var response map[string]interface{}
    json.Unmarshal(w.Body.Bytes(), &response)
    
    assert.NotNil(t, response["connector"])
    assert.Equal(t, floor.ID, uint(response["connector"].(map[string]interface{})["floor_id"].(float64)))
}
```

## Migration Guide

### From Pre-FloorID to FloorID

1. **Database Migration**
   ```sql
   -- Add FloorID column
   ALTER TABLE connectors ADD COLUMN floor_id BIGINT;
   
   -- Set default floor for existing connectors
   UPDATE connectors SET floor_id = 1 WHERE floor_id IS NULL;
   
   -- Add NOT NULL constraint
   ALTER TABLE connectors MODIFY COLUMN floor_id BIGINT NOT NULL;
   
   -- Add index
   CREATE INDEX idx_connectors_floor_id ON connectors(floor_id);
   ```

2. **Code Updates**
   - Update connector model to include FloorID
   - Add validation logic
   - Update API handlers
   - Update frontend components

3. **Data Migration**
   - Assign appropriate floors to existing connectors
   - Validate floor consistency
   - Update connected object relationships

### Backward Compatibility

- API endpoints accept both old and new formats
- Default floor assignment for missing FloorID
- Graceful degradation for missing floor data

## Best Practices

### Code Organization

1. **Separation of Concerns**
   - Validation logic in models
   - Business logic in handlers
   - UI logic in frontend

2. **Error Handling**
   - Clear error messages
   - Proper HTTP status codes
   - Validation summaries

3. **Performance**
   - Database indexes on FloorID
   - Efficient queries with joins
   - Caching for floor data

### Data Integrity

1. **Validation**
   - FloorID required and valid
   - Floor consistency for connected objects
   - Geometry bounds validation

2. **Constraints**
   - Database foreign key constraints
   - Application-level validation
   - Transaction safety

3. **Audit Trail**
   - Track floor changes
   - Log validation failures
   - Monitor consistency issues

### User Experience

1. **UI Design**
   - Clear floor indicators
   - Intuitive floor selection
   - Helpful error messages

2. **Performance**
   - Fast floor filtering
   - Efficient bulk operations
   - Responsive UI updates

3. **Accessibility**
   - Screen reader support
   - Keyboard navigation
   - Clear visual hierarchy

## Troubleshooting

### Common Issues

#### FloorID Validation Failures
- **Cause**: Missing or invalid FloorID
- **Solution**: Ensure FloorID is set and references valid floor

#### Floor Consistency Errors
- **Cause**: Connected objects on different floors
- **Solution**: Move objects to same floor or update connections

#### Performance Issues
- **Cause**: Missing database indexes
- **Solution**: Add indexes on FloorID and related columns

#### UI Display Issues
- **Cause**: Missing floor data or incorrect grouping
- **Solution**: Verify floor data loading and grouping logic

### Debug Tools

1. **Database Queries**
   ```sql
   -- Check connector floor distribution
   SELECT floor_id, COUNT(*) as count 
   FROM connectors 
   GROUP BY floor_id;
   
   -- Find floor consistency issues
   SELECT c.object_id, c.floor_id, d.object_id as device_id, d.floor_id as device_floor
   FROM connectors c
   JOIN devices d ON JSON_CONTAINS(c.connected_to, d.object_id)
   WHERE c.floor_id != d.floor_id;
   ```

2. **API Testing**
   ```bash
   # Test connector creation with FloorID
   curl -X POST /api/connectors \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"object_id":"TEST_001","name":"Test","floor_id":1}'
   
   # Test floor filtering
   curl -X GET "/api/connectors?floor_id=1" \
     -H "Authorization: Bearer $TOKEN"
   ```

3. **Frontend Debugging**
   ```javascript
   // Check floor data loading
   console.log('Floors:', connectorManager.floors);
   console.log('Connectors:', connectorManager.connectors);
   
   // Check floor grouping
   console.log('Grouped:', connectorManager.groupConnectorsByFloor());
   ```

---

*Last updated: January 2024*
*Version: 1.0*

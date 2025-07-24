# CMMS Integration Documentation

## Overview

The CMMS (Computerized Maintenance Management System) Integration provides comprehensive maintenance management capabilities including data synchronization, work order processing, maintenance scheduling, and asset tracking. This system enables seamless integration with external CMMS systems and provides enterprise-grade maintenance management functionality.

## Architecture

### Components

1. **Data Synchronization Service** (`data_synchronization.py`)
   - Manages connections to external CMMS systems
   - Handles data transformation and mapping
   - Synchronizes work orders, maintenance schedules, and assets

2. **Work Order Processing Service** (`work_order_processing.py`)
   - Creates and manages work orders
   - Handles work order templates and steps
   - Tracks work order status and progress

3. **Maintenance Scheduling Service** (`maintenance_scheduling.py`)
   - Manages maintenance schedules and recurring tasks
   - Handles calendar and scheduling logic
   - Integrates with notification system

4. **Asset Tracking Service** (`asset_tracking.py`)
   - Tracks asset locations and conditions
   - Monitors performance metrics
   - Manages alerts and notifications

5. **API Layer** (`cmms_api.py`)
   - FastAPI application exposing CMMS functionality
   - RESTful endpoints for all CMMS operations
   - Request/response validation

6. **Go Integration** (`cmms_service.go`, `cmms_handlers.go`)
   - Go client service for Python CMMS services
   - HTTP handlers for CMMS API endpoints
   - Integration with Go backend

## Features

### Data Synchronization

#### CMMS Connections
- Support for multiple CMMS system types
- Secure API key and credential management
- Connection health monitoring

#### Field Mapping
- Configurable field mappings between systems
- Data transformation rules
- Required field validation

#### Synchronization Types
- **Work Orders**: Sync work orders from external CMMS
- **Maintenance Schedules**: Sync maintenance schedules
- **Assets**: Sync asset information
- **All Data**: Complete synchronization

### Work Order Processing

#### Work Order Creation
- Manual work order creation
- Template-based work order creation
- Asset assignment and scheduling

#### Work Order Management
- Status tracking (scheduled, in_progress, completed, cancelled)
- Step and part management
- Time and cost tracking

#### Work Order Templates
- Reusable work order templates
- Standardized procedures
- Estimated time and cost tracking

### Maintenance Scheduling

#### Maintenance Schedules
- **Types**: Preventive, Corrective, Predictive, Emergency, Inspection, Calibration, Cleaning, Lubrication
- **Priorities**: Critical, High, Medium, Low
- **Frequencies**: Daily, Weekly, Monthly, Quarterly, Semi-annual, Annual, Custom
- **Triggers**: Time-based, Usage-based, Condition-based, Manual, Event-based

#### Maintenance Tasks
- Automated task creation from schedules
- Resource allocation and assignment
- Progress tracking and completion

#### Calendar Management
- Working hours and days configuration
- Holiday management
- Timezone support

### Asset Tracking

#### Asset Management
- **Types**: Equipment, Machinery, Vehicle, Building, Infrastructure, Tool, Instrument, System, Component
- **Status**: Operational, Maintenance, Repair, Retired, Spare, Decommissioned, Testing, Standby
- **Conditions**: Excellent, Good, Fair, Poor, Critical

#### Location Tracking
- Building, floor, room tracking
- GPS coordinates support
- Department and zone assignment

#### Performance Monitoring
- Uptime percentage tracking
- Efficiency rating monitoring
- Temperature, vibration, pressure monitoring
- Error and warning tracking

#### Alert Management
- Automated alert generation
- Alert acknowledgment and resolution
- Notification integration

## API Reference

### Data Synchronization Endpoints

#### Add CMMS Connection
```http
POST /cmms/connections
Content-Type: application/json

{
  "cmms_type": "upkeep",
  "api_url": "https://api.upkeep.com",
  "api_key": "your_api_key",
  "connection_name": "Upkeep Production"
}
```

#### Sync Work Orders
```http
POST /cmms/sync/work-orders
Content-Type: application/json

{
  "cmms_connection_id": "uuid",
  "sync_type": "work_orders",
  "force_sync": false
}
```

#### Sync All Data
```http
POST /cmms/sync/all
Content-Type: application/json

{
  "cmms_connection_id": "uuid",
  "sync_type": "all",
  "force_sync": false
}
```

### Work Order Endpoints

#### Create Work Order
```http
POST /work-orders
Content-Type: application/json

{
  "asset_id": "asset_001",
  "title": "Equipment Maintenance",
  "description": "Monthly preventive maintenance",
  "priority": "high",
  "estimated_hours": 4.0,
  "assigned_to": "technician_001",
  "scheduled_start": "2024-01-15T09:00:00Z",
  "scheduled_end": "2024-01-15T13:00:00Z"
}
```

#### Get Work Orders
```http
GET /work-orders?status=scheduled&asset_id=asset_001&assigned_to=technician_001
```

#### Update Work Order Status
```http
PUT /work-orders/{work_order_id}/status
Content-Type: application/json

{
  "status": "in_progress"
}
```

### Maintenance Scheduling Endpoints

#### Create Maintenance Schedule
```http
POST /maintenance/schedules
Content-Type: application/json

{
  "name": "Monthly Equipment Check",
  "description": "Monthly preventive maintenance",
  "maintenance_type": "preventive",
  "priority": "medium",
  "frequency": "monthly",
  "trigger_type": "time_based",
  "trigger_value": 30,
  "estimated_duration": 120,
  "estimated_cost": 200.00,
  "required_skills": ["electrical", "mechanical"],
  "required_tools": ["multimeter", "wrenches"],
  "required_parts": ["filters", "lubricant"]
}
```

#### Create Maintenance Task
```http
POST /maintenance/tasks
Content-Type: application/json

{
  "schedule_id": "uuid",
  "asset_id": "asset_001",
  "scheduled_start": "2024-01-15T09:00:00Z",
  "priority": "high",
  "assigned_to": "technician_001",
  "location": "Building A, Floor 2"
}
```

#### Start Maintenance Task
```http
POST /maintenance/tasks/{task_id}/start?performer=technician_001
```

#### Complete Maintenance Task
```http
POST /maintenance/tasks/{task_id}/complete
Content-Type: application/json

{
  "actual_duration": 110,
  "actual_cost": 180.00,
  "notes": "Task completed successfully",
  "findings": "Equipment in good condition",
  "recommendations": "Continue with current schedule"
}
```

### Asset Tracking Endpoints

#### Register Asset
```http
POST /assets
Content-Type: application/json

{
  "asset_id": "asset_001",
  "name": "Production Machine",
  "asset_type": "equipment",
  "description": "Main production line equipment",
  "manufacturer": "Industrial Corp",
  "model": "PM-2000",
  "serial_number": "SN123456",
  "department": "Manufacturing",
  "responsible_person": "engineer_001",
  "tags": ["critical", "production"],
  "specifications": {
    "power_rating": "100kW",
    "voltage": "480V",
    "frequency": "60Hz"
  }
}
```

#### Update Asset Location
```http
POST /assets/{asset_id}/location
Content-Type: application/json

{
  "location_name": "Building A",
  "building": "Main Building",
  "floor": "2nd Floor",
  "room": "Room 201",
  "coordinates": [40.7128, -74.0060],
  "department": "Engineering"
}
```

#### Record Performance Data
```http
POST /assets/{asset_id}/performance
Content-Type: application/json

{
  "uptime_percentage": 95.5,
  "efficiency_rating": 92.3,
  "throughput": 150.0,
  "energy_consumption": 85.2,
  "temperature": 65.5,
  "vibration": 0.8,
  "pressure": 100.0,
  "speed": 1200.0,
  "load_percentage": 75.0,
  "error_count": 2,
  "warning_count": 1,
  "maintenance_hours": 4.5,
  "cost_per_hour": 25.0
}
```

#### Get Asset Statistics
```http
GET /assets/statistics?asset_id=asset_001&start_date=2024-01-01T00:00:00Z&end_date=2024-01-31T23:59:59Z
```

## Usage Examples

### Python Client

```python
from svgx_engine.services.cmms.data_synchronization import CMMSDataSynchronizationService
from svgx_engine.services.cmms.work_order_processing import WorkOrderProcessingService
from svgx_engine.services.cmms.maintenance_scheduling import MaintenanceSchedulingService
from svgx_engine.services.cmms.asset_tracking import AssetTrackingService

# Initialize services
data_sync_service = CMMSDataSynchronizationService()
work_order_service = WorkOrderProcessingService()
maintenance_service = MaintenanceSchedulingService()
asset_tracking_service = AssetTrackingService()

# Add CMMS connection
connection = await data_sync_service.add_cmms_connection(
    cmms_type="upkeep",
    api_url="https://api.upkeep.com",
    api_key="your_api_key",
    connection_name="Upkeep Production"
)

# Sync work orders
result = await data_sync_service.sync_work_orders(
    cmms_connection_id=connection.id,
    force_sync=False
)

# Create work order
work_order = await work_order_service.create_work_order(
    asset_id="asset_001",
    title="Equipment Maintenance",
    description="Monthly preventive maintenance",
    priority="high",
    estimated_hours=4.0,
    assigned_to="technician_001"
)

# Create maintenance schedule
schedule = await maintenance_service.create_maintenance_schedule(
    name="Monthly Equipment Check",
    description="Monthly preventive maintenance",
    maintenance_type="preventive",
    priority="medium",
    frequency="monthly",
    trigger_type="time_based",
    trigger_value=30,
    estimated_duration=120,
    estimated_cost=200.00
)

# Register asset
asset = await asset_tracking_service.register_asset(
    asset_id="asset_001",
    name="Production Machine",
    asset_type="equipment",
    department="Manufacturing"
)

# Record performance data
performance = await asset_tracking_service.record_performance_data(
    asset_id="asset_001",
    uptime_percentage=95.5,
    efficiency_rating=92.3,
    temperature=65.5,
    error_count=2
)
```

### Go Client

```go
package main

import (
    "log"
    "time"
    
    "arxos/arx-backend/services/cmms"
)

func main() {
    // Initialize CMMS service
    cmmsService := cmms.NewCMMSService("http://localhost:8003")
    
    // Add CMMS connection
    connection := cmms.CMMSConnection{
        CMMSType:       "upkeep",
        APIURL:         "https://api.upkeep.com",
        APIKey:         "your_api_key",
        ConnectionName: "Upkeep Production",
    }
    
    result, err := cmmsService.AddCMMSConnection(connection)
    if err != nil {
        log.Fatal(err)
    }
    
    // Sync work orders
    syncResult, err := cmmsService.SyncWorkOrders(result.ID, false)
    if err != nil {
        log.Fatal(err)
    }
    
    // Create work order
    workOrder := cmms.WorkOrder{
        AssetID:        "asset_001",
        Title:          "Equipment Maintenance",
        Description:    "Monthly preventive maintenance",
        Priority:       "high",
        EstimatedHours: 4.0,
        AssignedTo:     &[]string{"technician_001"}[0],
    }
    
    createdWorkOrder, err := cmmsService.CreateWorkOrder(workOrder)
    if err != nil {
        log.Fatal(err)
    }
    
    // Get work orders
    workOrders, err := cmmsService.GetWorkOrders(nil, nil, nil)
    if err != nil {
        log.Fatal(err)
    }
    
    // Register asset
    asset := cmms.Asset{
        ID:        "asset_001",
        Name:      "Production Machine",
        AssetType: "equipment",
    }
    
    registeredAsset, err := cmmsService.RegisterAsset(asset)
    if err != nil {
        log.Fatal(err)
    }
    
    // Record performance data
    performance := cmms.AssetPerformance{
        AssetID:          "asset_001",
        UptimePercentage: 95.5,
        EfficiencyRating: 92.3,
        Temperature:      &[]float64{65.5}[0],
        ErrorCount:       2,
    }
    
    err = cmmsService.RecordPerformanceData("asset_001", performance)
    if err != nil {
        log.Fatal(err)
    }
}
```

### JavaScript Client

```javascript
// CMMS API client
class CMMSClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }
    
    async addCMMSConnection(connection) {
        const response = await fetch(`${this.baseURL}/cmms/connections`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(connection),
        });
        return response.json();
    }
    
    async syncWorkOrders(connectionId, forceSync = false) {
        const response = await fetch(`${this.baseURL}/cmms/sync/work-orders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                cmms_connection_id: connectionId,
                sync_type: 'work_orders',
                force_sync: forceSync,
            }),
        });
        return response.json();
    }
    
    async createWorkOrder(workOrder) {
        const response = await fetch(`${this.baseURL}/work-orders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(workOrder),
        });
        return response.json();
    }
    
    async getWorkOrders(filters = {}) {
        const params = new URLSearchParams(filters);
        const response = await fetch(`${this.baseURL}/work-orders?${params}`);
        return response.json();
    }
    
    async registerAsset(asset) {
        const response = await fetch(`${this.baseURL}/assets`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(asset),
        });
        return response.json();
    }
    
    async recordPerformanceData(assetId, performance) {
        const response = await fetch(`${this.baseURL}/assets/${assetId}/performance`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(performance),
        });
        return response.json();
    }
}

// Usage
const cmmsClient = new CMMSClient('http://localhost:8003');

// Add CMMS connection
const connection = await cmmsClient.addCMMSConnection({
    cmms_type: 'upkeep',
    api_url: 'https://api.upkeep.com',
    api_key: 'your_api_key',
    connection_name: 'Upkeep Production',
});

// Sync work orders
const syncResult = await cmmsClient.syncWorkOrders(connection.connection_id);

// Create work order
const workOrder = await cmmsClient.createWorkOrder({
    asset_id: 'asset_001',
    title: 'Equipment Maintenance',
    description: 'Monthly preventive maintenance',
    priority: 'high',
    estimated_hours: 4.0,
    assigned_to: 'technician_001',
});

// Register asset
const asset = await cmmsClient.registerAsset({
    asset_id: 'asset_001',
    name: 'Production Machine',
    asset_type: 'equipment',
    department: 'Manufacturing',
});

// Record performance data
const performance = await cmmsClient.recordPerformanceData('asset_001', {
    uptime_percentage: 95.5,
    efficiency_rating: 92.3,
    temperature: 65.5,
    error_count: 2,
});
```

## Configuration

### Environment Variables

```bash
# CMMS API Configuration
CMMS_API_HOST=0.0.0.0
CMMS_API_PORT=8003
CMMS_API_DEBUG=true

# Database Configuration
CMMS_DB_HOST=localhost
CMMS_DB_PORT=5432
CMMS_DB_NAME=cmms_db
CMMS_DB_USER=cmms_user
CMMS_DB_PASSWORD=secure_password

# Notification Configuration
CMMS_NOTIFICATION_EMAIL_ENABLED=true
CMMS_NOTIFICATION_SLACK_ENABLED=true
CMMS_NOTIFICATION_SMS_ENABLED=false

# External CMMS API Keys
UPKEEP_API_KEY=your_upkeep_api_key
FIIX_API_KEY=your_fiix_api_key
MAXIMO_API_KEY=your_maximo_api_key
```

### Database Schema

The CMMS integration uses the following database tables:

- `cmms_connections`: CMMS system connections
- `cmms_field_mappings`: Field mapping configurations
- `work_orders`: Work order data
- `work_order_steps`: Work order procedure steps
- `work_order_parts`: Parts used in work orders
- `work_order_templates`: Reusable work order templates
- `maintenance_schedules`: Maintenance schedule configurations
- `maintenance_tasks`: Individual maintenance tasks
- `maintenance_history`: Maintenance completion history
- `maintenance_calendars`: Calendar configurations
- `assets`: Asset information
- `asset_locations`: Asset location history
- `asset_conditions`: Asset condition assessments
- `asset_performance`: Asset performance metrics
- `asset_alerts`: Asset alerts and notifications

## Testing

### Running Tests

```bash
# Run all CMMS integration tests
python -m pytest tests/test_cmms_integration_comprehensive.py -v

# Run specific test classes
python -m pytest tests/test_cmms_integration_comprehensive.py::TestCMMSDataSynchronization -v
python -m pytest tests/test_cmms_integration_comprehensive.py::TestWorkOrderProcessing -v
python -m pytest tests/test_cmms_integration_comprehensive.py::TestMaintenanceScheduling -v
python -m pytest tests/test_cmms_integration_comprehensive.py::TestAssetTracking -v
python -m pytest tests/test_cmms_integration_comprehensive.py::TestCMMSIntegration -v
```

### Test Coverage

The comprehensive test suite covers:

- **Data Synchronization**: Connection management, field mapping, data sync operations
- **Work Order Processing**: Creation, status updates, template management
- **Maintenance Scheduling**: Schedule creation, task management, calendar operations
- **Asset Tracking**: Registration, location updates, performance monitoring, alerts
- **Integration**: End-to-end workflow testing

## Monitoring and Alerting

### Performance Metrics

- **Data Sync Performance**: Sync duration, success rate, error count
- **Work Order Processing**: Creation rate, completion rate, average duration
- **Maintenance Scheduling**: Schedule adherence, task completion rate
- **Asset Tracking**: Alert response time, performance degradation detection

### Health Checks

```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "CMMS Integration API",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Security

### Authentication

- API key authentication for external CMMS systems
- JWT token authentication for internal API access
- Role-based access control (RBAC)

### Data Protection

- Encrypted storage of sensitive credentials
- Secure transmission of data over HTTPS
- Audit logging of all operations

### Compliance

- GDPR compliance for personal data
- SOC2 compliance for enterprise deployments
- Industry-specific compliance (FDA, ISO, etc.)

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8003

CMD ["python", "-m", "uvicorn", "svgx_engine.api.cmms_api:app", "--host", "0.0.0.0", "--port", "8003"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cmms-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cmms-api
  template:
    metadata:
      labels:
        app: cmms-api
    spec:
      containers:
      - name: cmms-api
        image: arxos/cmms-api:latest
        ports:
        - containerPort: 8003
        env:
        - name: CMMS_API_HOST
          value: "0.0.0.0"
        - name: CMMS_API_PORT
          value: "8003"
```

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Verify API credentials
   - Check network connectivity
   - Validate API endpoint URLs

2. **Data Sync Errors**
   - Review field mappings
   - Check data format compatibility
   - Verify required fields

3. **Performance Issues**
   - Monitor database performance
   - Check API response times
   - Review resource utilization

### Logs

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Support

For technical support and issues:

- **Documentation**: This documentation
- **Issues**: GitHub issue tracker
- **Email**: support@arxos.com

## Future Enhancements

### Planned Features

1. **Advanced Analytics**
   - Predictive maintenance algorithms
   - Performance trend analysis
   - Cost optimization recommendations

2. **Mobile Support**
   - Mobile app for field technicians
   - Offline capability
   - Photo and video capture

3. **IoT Integration**
   - Real-time sensor data integration
   - Automated condition monitoring
   - Predictive failure detection

4. **AI/ML Integration**
   - Automated work order generation
   - Intelligent scheduling optimization
   - Anomaly detection

### Roadmap

- **Q1 2024**: Advanced analytics and reporting
- **Q2 2024**: Mobile application development
- **Q3 2024**: IoT sensor integration
- **Q4 2024**: AI/ML capabilities

## Conclusion

The CMMS Integration provides a comprehensive, enterprise-grade maintenance management solution with seamless integration capabilities, robust API support, and extensive monitoring and alerting features. The system is designed for scalability, security, and ease of use across multiple deployment scenarios. 
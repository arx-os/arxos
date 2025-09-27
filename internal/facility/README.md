# ArxOS Facility Management System

The Facility Management System provides comprehensive CMMS/CAFM (Computerized Maintenance Management System / Computer-Aided Facility Management) capabilities for managing buildings, assets, work orders, maintenance schedules, inspections, and vendor relationships.

## Architecture

The system is built with a modular architecture that separates concerns and provides clear interfaces:

```
┌─────────────────────────────────────────────────────────────┐
│                    Facility Management                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Building  │  │    Space    │  │    Asset    │        │
│  │  Management │  │  Management │  │  Management │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Work      │  │ Maintenance │  │ Inspection  │        │
│  │   Order     │  │  Management │  │  Management │        │
│  │ Management  │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Vendor    │  │   Contract   │  │   Metrics   │        │
│  │ Management  │  │  Management  │  │   & Stats   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Building Management
- **Building**: Physical structures with location, type, and capacity information
- **Space**: Individual rooms, floors, or areas within buildings
- **Asset**: Equipment, fixtures, and systems within spaces

### 2. Work Order Management
- **Work Order**: Service requests, maintenance tasks, and repairs
- **Priority Levels**: Low, Medium, High, Urgent
- **Status Tracking**: Open → Assigned → In Progress → Completed/Cancelled
- **Assignment**: Automatic or manual assignment to technicians

### 3. Maintenance Management
- **Maintenance Schedule**: Recurring maintenance tasks
- **Frequency Types**: Daily, Weekly, Monthly, Yearly
- **Automated Execution**: Automatic work order creation for due tasks
- **Preventive Maintenance**: Scheduled maintenance to prevent failures

### 4. Inspection Management
- **Inspection**: Regular inspections of assets and spaces
- **Checklist Support**: Structured inspection procedures
- **Finding Management**: Issue identification and tracking
- **Compliance Tracking**: Regulatory and safety compliance

### 5. Vendor Management
- **Vendor**: External service providers and suppliers
- **Contract**: Service agreements and pricing
- **Performance Tracking**: Vendor performance metrics
- **Contract Management**: Renewal and expiration tracking

## Key Features

### Building Hierarchy
```
Building
├── Floor 1
│   ├── Space 101 (Office)
│   │   ├── Asset: HVAC Unit
│   │   ├── Asset: Lighting System
│   │   └── Asset: Security Camera
│   └── Space 102 (Conference Room)
│       ├── Asset: Projector
│       └── Asset: Audio System
└── Floor 2
    ├── Space 201 (Office)
    └── Space 202 (Storage)
```

### Work Order Lifecycle
1. **Creation**: Work order created from inspection findings, maintenance schedules, or manual requests
2. **Assignment**: Automatic or manual assignment to available technicians
3. **Execution**: Work order started, progress tracked, materials logged
4. **Completion**: Work order completed with notes, photos, and time tracking
5. **Closure**: Work order closed, follow-up scheduled if needed

### Maintenance Scheduling
- **Recurring Tasks**: HVAC filter changes, equipment inspections
- **Condition-Based**: Maintenance triggered by asset condition
- **Predictive**: Maintenance based on usage patterns and analytics
- **Emergency**: Immediate response to critical issues

### Inspection Workflow
1. **Scheduling**: Inspections scheduled based on frequency or triggers
2. **Execution**: Inspectors conduct inspections using checklists
3. **Finding Creation**: Issues identified and categorized by severity
4. **Work Order Generation**: Critical findings automatically create work orders
5. **Follow-up**: Findings tracked until resolution

## API Endpoints

### Building Management
- `GET /api/v1/facility/buildings` - List all buildings
- `POST /api/v1/facility/buildings` - Create new building
- `GET /api/v1/facility/buildings/{id}` - Get building details
- `PUT /api/v1/facility/buildings/{id}` - Update building
- `DELETE /api/v1/facility/buildings/{id}` - Delete building

### Space Management
- `GET /api/v1/facility/spaces` - List all spaces
- `POST /api/v1/facility/spaces` - Create new space
- `GET /api/v1/facility/buildings/{id}/spaces` - List spaces in building
- `GET /api/v1/facility/spaces/{id}` - Get space details
- `PUT /api/v1/facility/spaces/{id}` - Update space
- `DELETE /api/v1/facility/spaces/{id}` - Delete space

### Asset Management
- `GET /api/v1/facility/assets` - List all assets
- `POST /api/v1/facility/assets` - Create new asset
- `GET /api/v1/facility/buildings/{id}/assets` - List assets in building
- `GET /api/v1/facility/spaces/{id}/assets` - List assets in space
- `GET /api/v1/facility/assets/{id}` - Get asset details
- `PUT /api/v1/facility/assets/{id}` - Update asset
- `DELETE /api/v1/facility/assets/{id}` - Delete asset

### Work Order Management
- `GET /api/v1/facility/workorders` - List all work orders
- `POST /api/v1/facility/workorders` - Create new work order
- `GET /api/v1/facility/workorders/{id}` - Get work order details
- `PUT /api/v1/facility/workorders/{id}` - Update work order
- `POST /api/v1/facility/workorders/assign` - Assign work order
- `POST /api/v1/facility/workorders/start` - Start work order
- `POST /api/v1/facility/workorders/complete` - Complete work order
- `POST /api/v1/facility/workorders/cancel` - Cancel work order

### Maintenance Management
- `GET /api/v1/facility/maintenance` - List maintenance schedules
- `POST /api/v1/facility/maintenance` - Create maintenance schedule
- `GET /api/v1/facility/maintenance/{id}` - Get schedule details
- `PUT /api/v1/facility/maintenance/{id}` - Update schedule
- `POST /api/v1/facility/maintenance/execute` - Execute schedule
- `POST /api/v1/facility/maintenance/execute-all` - Execute all due schedules

### Inspection Management
- `GET /api/v1/facility/inspections` - List inspections
- `POST /api/v1/facility/inspections` - Create inspection
- `GET /api/v1/facility/inspections/{id}` - Get inspection details
- `PUT /api/v1/facility/inspections/{id}` - Update inspection
- `POST /api/v1/facility/inspections/start` - Start inspection
- `POST /api/v1/facility/inspections/complete` - Complete inspection
- `GET /api/v1/facility/inspections/findings` - List findings

### Vendor Management
- `GET /api/v1/facility/vendors` - List vendors
- `POST /api/v1/facility/vendors` - Create vendor
- `GET /api/v1/facility/vendors/{id}` - Get vendor details
- `PUT /api/v1/facility/vendors/{id}` - Update vendor
- `GET /api/v1/facility/contracts` - List contracts
- `POST /api/v1/facility/contracts` - Create contract
- `GET /api/v1/facility/contracts/{id}` - Get contract details
- `PUT /api/v1/facility/contracts/{id}` - Update contract

### Metrics and Statistics
- `GET /api/v1/facility/metrics` - Facility metrics
- `GET /api/v1/facility/workorders/metrics` - Work order metrics
- `GET /api/v1/facility/maintenance/metrics` - Maintenance metrics
- `GET /api/v1/facility/inspections/metrics` - Inspection metrics
- `GET /api/v1/facility/vendors/metrics` - Vendor metrics

## CLI Usage

The facility management system includes a comprehensive CLI for managing all aspects of facility operations:

### Building Management
```bash
# List all buildings
facility building list

# Create a new building
facility building create

# Get building details
facility building get <building-id>

# Update building
facility building update <building-id>

# Delete building
facility building delete <building-id>
```

### Space Management
```bash
# List all spaces
facility space list

# List spaces in a building
facility space list-by-building <building-id>

# Create a new space
facility space create

# Get space details
facility space get <space-id>
```

### Asset Management
```bash
# List all assets
facility asset list

# List assets in a building
facility asset list-by-building <building-id>

# List assets in a space
facility asset list-by-space <space-id>

# Create a new asset
facility asset create

# Get asset details
facility asset get <asset-id>
```

### Work Order Management
```bash
# List all work orders
facility workorder list

# Create a new work order
facility workorder create

# Assign work order
facility workorder assign <work-order-id> <technician-id>

# Start work order
facility workorder start <work-order-id>

# Complete work order
facility workorder complete <work-order-id>

# Cancel work order
facility workorder cancel <work-order-id>
```

### Maintenance Management
```bash
# List maintenance schedules
facility maintenance list

# Create maintenance schedule
facility maintenance create

# Execute maintenance schedule
facility maintenance execute <schedule-id>

# Execute all due maintenance
facility maintenance execute-all
```

### Inspection Management
```bash
# List inspections
facility inspection list

# Create inspection
facility inspection create

# Start inspection
facility inspection start <inspection-id>

# Complete inspection
facility inspection complete <inspection-id>
```

### Vendor Management
```bash
# List vendors
facility vendor list

# Create vendor
facility vendor create

# List contracts
facility vendor contracts

# Create contract
facility vendor create-contract
```

### Metrics and Statistics
```bash
# Show facility metrics
facility metrics facility

# Show work order metrics
facility metrics workorders

# Show maintenance metrics
facility metrics maintenance

# Show inspection metrics
facility metrics inspections

# Show vendor metrics
facility metrics vendors
```

## Data Models

### Building
```go
type Building struct {
    ID           string        `json:"id"`
    Name         string        `json:"name"`
    Address      string        `json:"address"`
    City         string        `json:"city"`
    State        string        `json:"state"`
    ZipCode      string        `json:"zip_code"`
    Country      string        `json:"country"`
    BuildingType string        `json:"building_type"`
    Floors       int           `json:"floors"`
    TotalArea    float64       `json:"total_area"`
    YearBuilt    int           `json:"year_built"`
    Status       BuildingStatus `json:"status"`
    CreatedAt    time.Time     `json:"created_at"`
    UpdatedAt    time.Time     `json:"updated_at"`
}
```

### Space
```go
type Space struct {
    ID         string      `json:"id"`
    BuildingID string      `json:"building_id"`
    Name       string      `json:"name"`
    SpaceType  string      `json:"space_type"`
    Floor      int         `json:"floor"`
    Area       float64     `json:"area"`
    Capacity   int         `json:"capacity"`
    Status     SpaceStatus `json:"status"`
    CreatedAt  time.Time   `json:"created_at"`
    UpdatedAt  time.Time   `json:"updated_at"`
}
```

### Asset
```go
type Asset struct {
    ID            string     `json:"id"`
    BuildingID    string     `json:"building_id"`
    SpaceID       string     `json:"space_id"`
    Name          string     `json:"name"`
    AssetType     string     `json:"asset_type"`
    Manufacturer  string     `json:"manufacturer"`
    Model         string     `json:"model"`
    SerialNumber  string     `json:"serial_number"`
    InstallDate   time.Time  `json:"install_date"`
    WarrantyExpiry time.Time `json:"warranty_expiry"`
    Status        AssetStatus `json:"status"`
    CreatedAt     time.Time  `json:"created_at"`
    UpdatedAt     time.Time  `json:"updated_at"`
}
```

### Work Order
```go
type WorkOrder struct {
    ID                  string           `json:"id"`
    Title               string           `json:"title"`
    Description         string           `json:"description"`
    Priority            WorkOrderPriority `json:"priority"`
    Status              WorkOrderStatus  `json:"status"`
    AssetID             string           `json:"asset_id"`
    SpaceID             string           `json:"space_id"`
    BuildingID          string           `json:"building_id"`
    AssignedTo          string           `json:"assigned_to"`
    CreatedBy           string           `json:"created_by"`
    CreatedAt           time.Time        `json:"created_at"`
    UpdatedAt           time.Time        `json:"updated_at"`
    StartedAt           time.Time        `json:"started_at"`
    CompletedAt         time.Time        `json:"completed_at"`
    CancelledAt         time.Time        `json:"cancelled_at"`
    CancellationReason  string           `json:"cancellation_reason"`
    Notes               []string         `json:"notes"`
}
```

### Maintenance Schedule
```go
type MaintenanceSchedule struct {
    ID          string             `json:"id"`
    Name        string             `json:"name"`
    Description string             `json:"description"`
    AssetID     string             `json:"asset_id"`
    Frequency   string             `json:"frequency"`
    Interval    int                `json:"interval"`
    NextDue     time.Time          `json:"next_due"`
    Status      MaintenanceStatus  `json:"status"`
    CreatedAt   time.Time          `json:"created_at"`
    UpdatedAt   time.Time          `json:"updated_at"`
}
```

### Inspection
```go
type Inspection struct {
    ID            string           `json:"id"`
    Name          string           `json:"name"`
    Type          string           `json:"type"`
    AssetID       string           `json:"asset_id"`
    SpaceID       string           `json:"space_id"`
    BuildingID    string           `json:"building_id"`
    ScheduledDate time.Time        `json:"scheduled_date"`
    Status        InspectionStatus `json:"status"`
    Score         float64          `json:"score"`
    Notes         string           `json:"notes"`
    CreatedAt     time.Time        `json:"created_at"`
    UpdatedAt     time.Time        `json:"updated_at"`
    StartedAt     time.Time        `json:"started_at"`
    CompletedAt   time.Time        `json:"completed_at"`
}
```

### Inspection Finding
```go
type InspectionFinding struct {
    ID           string           `json:"id"`
    InspectionID string           `json:"inspection_id"`
    Title        string           `json:"title"`
    Description  string           `json:"description"`
    Severity     FindingSeverity  `json:"severity"`
    Status       FindingStatus    `json:"status"`
    Category     string           `json:"category"`
    Resolution   string           `json:"resolution"`
    ResolvedAt   time.Time        `json:"resolved_at"`
    CreatedAt    time.Time        `json:"created_at"`
    UpdatedAt    time.Time        `json:"updated_at"`
}
```

### Vendor
```go
type Vendor struct {
    ID          string      `json:"id"`
    Name        string      `json:"name"`
    ContactName string      `json:"contact_name"`
    Email       string      `json:"email"`
    Phone       string      `json:"phone"`
    Address     string      `json:"address"`
    City        string      `json:"city"`
    State       string      `json:"state"`
    ZipCode     string      `json:"zip_code"`
    Country     string      `json:"country"`
    Status      VendorStatus `json:"status"`
    CreatedAt   time.Time   `json:"created_at"`
    UpdatedAt   time.Time   `json:"updated_at"`
}
```

### Contract
```go
type Contract struct {
    ID          string        `json:"id"`
    VendorID    string        `json:"vendor_id"`
    Name        string        `json:"name"`
    Description string        `json:"description"`
    StartDate   time.Time     `json:"start_date"`
    EndDate     time.Time     `json:"end_date"`
    Value       float64       `json:"value"`
    Status      ContractStatus `json:"status"`
    CreatedAt   time.Time     `json:"created_at"`
    UpdatedAt   time.Time     `json:"updated_at"`
}
```

## Status Enums

### Building Status
- `active` - Building is operational
- `inactive` - Building is not in use
- `maintenance` - Building under maintenance
- `closed` - Building permanently closed

### Space Status
- `active` - Space is available for use
- `inactive` - Space is not available
- `maintenance` - Space under maintenance
- `reserved` - Space is reserved

### Asset Status
- `active` - Asset is operational
- `inactive` - Asset is not in use
- `maintenance` - Asset under maintenance
- `retired` - Asset has been retired

### Work Order Status
- `open` - Work order created, not assigned
- `assigned` - Work order assigned to technician
- `in_progress` - Work order being executed
- `completed` - Work order completed
- `cancelled` - Work order cancelled

### Work Order Priority
- `low` - Low priority work order
- `medium` - Medium priority work order
- `high` - High priority work order
- `urgent` - Urgent work order

### Maintenance Status
- `active` - Maintenance schedule is active
- `inactive` - Maintenance schedule is inactive
- `paused` - Maintenance schedule is paused

### Inspection Status
- `scheduled` - Inspection is scheduled
- `in_progress` - Inspection is being conducted
- `completed` - Inspection is completed
- `cancelled` - Inspection is cancelled

### Finding Severity
- `low` - Low severity finding
- `medium` - Medium severity finding
- `high` - High severity finding
- `critical` - Critical finding requiring immediate attention

### Finding Status
- `open` - Finding is open
- `in_progress` - Finding is being addressed
- `resolved` - Finding has been resolved
- `closed` - Finding is closed

### Vendor Status
- `active` - Vendor is active
- `inactive` - Vendor is inactive
- `suspended` - Vendor is suspended

### Contract Status
- `active` - Contract is active
- `inactive` - Contract is inactive
- `expired` - Contract has expired
- `terminated` - Contract has been terminated

## Metrics and KPIs

### Facility Metrics
- Total buildings, spaces, and assets
- Active vs inactive counts
- Utilization rates
- Maintenance costs per square foot

### Work Order Metrics
- Total work orders by status
- Average resolution time
- Technician productivity
- Customer satisfaction scores

### Maintenance Metrics
- Preventive vs reactive maintenance ratio
- Schedule compliance rate
- Asset uptime
- Maintenance cost trends

### Inspection Metrics
- Inspection completion rate
- Average inspection scores
- Critical findings count
- Compliance rate

### Vendor Metrics
- Vendor performance scores
- Contract value and utilization
- Payment terms compliance
- Service level agreement adherence

## Integration Points

### Building Information Model (BIM)
- Import building data from IFC files
- Export facility data to BIM formats
- 3D visualization of assets and spaces

### IoT and Sensors
- Real-time asset monitoring
- Predictive maintenance triggers
- Environmental condition tracking

### Workflow Automation
- Automatic work order creation
- Escalation procedures
- Notification systems

### Financial Systems
- Cost tracking and budgeting
- Purchase order integration
- Invoice management

### Document Management
- Work order documentation
- Inspection reports
- Maintenance records
- Compliance certificates

## Security and Compliance

### Access Control
- Role-based permissions
- Building and space-level access
- Audit logging

### Data Protection
- Sensitive data encryption
- Secure API endpoints
- Data retention policies

### Compliance
- Regulatory compliance tracking
- Safety standards adherence
- Environmental regulations

## Performance Considerations

### Database Optimization
- Indexed queries for fast lookups
- Efficient spatial queries
- Caching for frequently accessed data

### Scalability
- Horizontal scaling support
- Load balancing
- Microservices architecture

### Monitoring
- Performance metrics
- Error tracking
- Resource utilization

## Future Enhancements

### AI and Machine Learning
- Predictive maintenance algorithms
- Anomaly detection
- Optimization recommendations

### Mobile Applications
- Field technician apps
- Inspection checklists
- Real-time updates

### Advanced Analytics
- Business intelligence dashboards
- Trend analysis
- Cost optimization

### Integration Expansion
- ERP system integration
- CAD software integration
- Third-party service providers

## Getting Started

1. **Installation**: The facility management system is part of the ArxOS core
2. **Configuration**: Set up database connections and API endpoints
3. **Initial Data**: Import building data or create manually
4. **User Setup**: Configure user roles and permissions
5. **Workflow Setup**: Define maintenance schedules and inspection procedures
6. **Integration**: Connect with existing systems and IoT devices

## Support and Documentation

- API documentation available at `/api/v1/facility/docs`
- CLI help available with `facility --help`
- Test suite for validation and regression testing
- Performance benchmarks and optimization guides

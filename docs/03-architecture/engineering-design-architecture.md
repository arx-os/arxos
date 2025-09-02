# Arxos Engineering Design & Architecture
**Project:** "Snapchat for Buildings" + Terminal Building Intelligence  
**Version:** 1.0  
**Date:** August 30, 2025

## Executive Summary

Arxos transforms building data capture from expensive professional surveys to crowd-sourced intelligence using iPhone LiDAR and mesh networking. The system provides real-time building intelligence accessible via multiple interfaces while maintaining complete offline operation through RF mesh networks.

**Key Innovation:** ArxObjects semantic compression converts 50MB LiDAR point clouds into 5KB queryable building data (10,000:1 compression ratio), enabling transmission over low-bandwidth packet radio while preserving building intelligence.

## Core Architecture

### Technology Stack
- **Rust:** Core processing engine (point cloud → ArxObjects → ASCII rendering)
- **SQLite:** Local data storage with R-Tree spatial indexing
- **Meshtastic LoRa:** Mesh networking (2km range, completely offline)

### System Requirements
- **Mesh Node:** Raspberry Pi 4 + LoRa module + Solar power
- **Total Node Cost:** $180-300 per deployment
- **Power Usage:** 1.5-6W (solar compatible)
- **Software Footprint:** 5-15MB Rust binary + SQLite database
- **Storage per Building:** 15KB-100MB depending on detail level

## Data Flow Architecture

```
iPhone LiDAR Scan → ArxObjects → ASCII Terminal → SQLite Storage → LoRa Mesh
       ↓                ↓              ↓              ↓              ↓
   20-second      Semantic      Terminal        Spatial      Mesh Network
     capture     compression    interface      indexing     propagation
       ↓                ↓              ↓              ↓              ↓
  Room layout    5KB building   Query/control   Local cache   Data sharing
```

### Bidirectional Intelligence Flow
```
AR Markup → ArxObjects → Terminal Interface → SQL Storage → Mesh Network
    ↑                                                             ↓
iPhone Camera ←←← Terminal Queries ←←← Local Interfaces ←←← Data Consumers
```

## User Interface Strategy

### Multi-Modal Access Design

**Problem Statement:** Different users need different interfaces - facilities managers want terminal power, contractors want visual simplicity, emergency responders need instant access.

**Solution:** Multiple interfaces to same backend infrastructure.

### Interface Types

#### 1. SSH Terminal Interface
**Target Users:** Facilities managers, IT administrators, power users  
**Access Method:** SSH to mesh node IP address on building network  
**Capabilities:**
- Complex building queries and automation
- System administration and configuration
- Bulk data operations and exports
- Integration with existing enterprise tools

**Example Usage:**
```bash
ssh admin@10.50.1.100  # School network IP
arxos> show outlets circuit B-7
arxos> find equipment type:HVAC floor:2
arxos> export room:205 format:CAD
```

#### 2. REST API Integration (Primary Interface)
**Target Users:** Existing CMMS, work order systems, mobile apps  
**Access Method:** HTTP API calls to mesh node on building network  
**Capabilities:**
- Seamless integration with existing workflows
- Real-time equipment data for work orders
- No user training or behavior change required
- Works with any existing facilities management software

**CMMS Integration Example:**
```javascript
// Work order app automatically enriches data
const equipment = await fetch('http://10.50.1.100:8080/api/equipment/room205/outlet3');
// Returns: {"circuit": "B-7", "panel": "2A", "last_service": "2024-03-15"}
```

#### 3. Web Interface (Secondary/Fallback)
**Target Users:** Buildings without CMMS integration, ad-hoc queries  
**Access Method:** Browse to mesh node IP on building network  
**Capabilities:**
- Interactive building floor plans
- Visual system overlays (electrical, HVAC, plumbing)
- Point-and-click equipment information
- Mobile-optimized interface

**Contractor Workflow (Fallback Only):**
1. Open browser on building WiFi
2. Navigate to http://10.50.1.100:8080
3. Browse interactive map with system toggles
4. Click on equipment for detailed information

#### 4. Voice Query Interface (Future)
**Target Users:** Hands-free scenarios, accessibility needs  
**Access Method:** Speak to mesh node microphone  
**Capabilities:**
- Natural language building queries
- Hands-free operation for ladder work
- Emergency evacuation assistance

## Network Architecture

### Hybrid Access Design

**Core Principle:** Complete internet isolation while integrating seamlessly with existing building networks and workflows.

#### Network Topology
```
Building A Mesh Node ←→ Building B Mesh Node ←→ Building C Mesh Node
        ↓                       ↓                       ↓
   Building Network        Building Network        Building Network
   (school WiFi)           (school WiFi)           (school WiFi)
        ↓                       ↓                       ↓
   CMMS Integration        CMMS Integration        CMMS Integration
   (seamless workflow)     (seamless workflow)     (seamless workflow)
```

#### Mesh Node Configuration
Each Raspberry Pi mesh node provides:
- **LoRa Radio:** Long-range mesh networking (2km urban, 10km rural)
- **Ethernet/WiFi Client:** Connects to building's existing network
- **REST API Server:** Serves building data to local network (port 8080)
- **SSH Access:** Terminal interface for power users
- **Processing Power:** Local ArxObject queries and spatial indexing

#### Network Integration Options

**Option 1: Ethernet Bridge (Preferred)**
- Mesh node connects via Ethernet to building network
- Appears as local device: `http://10.50.1.100:8080` 
- IT staff assigns static IP for reliability
- Works with existing network security policies

**Option 2: WiFi Client Mode**
- Mesh node connects to building WiFi as client device
- Serves Arxos API over existing network infrastructure
- Dynamic IP assignment (less reliable)
- Requires WiFi credentials for each building

**Option 3: Dedicated Network (Fallback)**
- Mesh node creates separate "Arxos-[Building]" network
- Used only when building network integration not possible
- Higher friction but maintains complete system functionality

### Security Model

**Network Isolation:**
- Mesh nodes connect to building networks but **never route to internet**
- LoRa mesh operates completely separately from building network
- No internet gateway or WAN routing on mesh nodes
- All external data exchange via LoRa mesh only

**Local Network Integration:**
- Mesh node acts as **read-only data service** on building network
- No bridging between building network and LoRa mesh
- Building network traffic never routes through mesh infrastructure
- API access restricted to building network clients only

**Access Control:**
- REST API serves building data to authorized local network clients
- SSH access uses standard key-based authentication
- CMMS integration requires network-level access controls
- All interfaces access same controlled dataset with appropriate permissions

## Data Architecture

### ArxObjects Format

**Semantic Compression Scheme:**
- **Input:** 50MB iPhone LiDAR point cloud
- **Processing:** Rust parser extracts building semantics
- **Output:** 5KB structured building data
- **Compression Ratio:** 10,000:1 (target for MVP: 1,000:1)

**ArxObject Structure:**
```rust
struct ArxObject {
    spatial_geometry: CompressedMesh,
    equipment_inventory: Vec<Equipment>,
    system_connections: NetworkGraph,
    markup_annotations: Vec<UserAnnotation>,
    metadata: BuildingMetadata,
}
```

### SQLite Schema Design

**Spatial Tables:**
```sql
-- Core building geometry
CREATE TABLE spaces (
    id INTEGER PRIMARY KEY,
    name TEXT,
    floor INTEGER,
    geometry BLOB -- R-Tree indexed polygons
);

-- Equipment and systems
CREATE TABLE equipment (
    id INTEGER PRIMARY KEY,
    space_id INTEGER,
    type TEXT, -- 'outlet', 'light', 'hvac_vent'
    system_id TEXT, -- 'circuit_B-7', 'hvac_zone_2'
    location_x REAL,
    location_y REAL,
    metadata JSON
);

-- System connections
CREATE TABLE systems (
    id TEXT PRIMARY KEY,
    type TEXT, -- 'electrical', 'hvac', 'plumbing'
    parent_system TEXT,
    specifications JSON
);
```

**Spatial Indexing:**
- R-Tree indexes for geometric queries
- Full-text search for equipment descriptions
- Graph traversal for system relationships

## Development Roadmap

### Phase 1: Core Infrastructure (Weeks 1-4)

**Week 1-2: ArxObject Foundation**
- Rust parser for basic building geometry
- SQLite schema with spatial indexing
- ASCII terminal renderer for floor plans
- Basic equipment markup structure

**Week 3-4: Data Pipeline**
- iPhone LiDAR → ArxObject conversion
- SQLite storage and retrieval
- Terminal query interface
- Manual data entry for testing

### Phase 2: Mesh Networking (Weeks 5-8)

**Week 5-6: Local Mesh**
- Meshtastic LoRa integration
- Multi-node data synchronization
- Basic mesh routing between Pi nodes
- Terminal access via SSH over mesh

**Week 7-8: Field Testing**
- Deploy 2-3 nodes at Jefferson Elementary
- Test mesh reliability and range
- Facilities manager training and feedback
- Data capture workflow validation

### Phase 3: User Integration (Weeks 9-12)

**Week 9-10: API Integration Development**
- REST API design and implementation
- CMMS system integration patterns
- Authentication and authorization framework
- API documentation and integration guides

**Week 11-12: Workflow Testing**
- Site technician workflow testing with existing tools
- CMMS integration validation
- Fallback web interface refinement
- Performance testing under realistic usage patterns

### Phase 4: Production Deployment (Months 4-6)

**Month 4: Pilot Expansion**
- Deploy across 5-10 Hillsborough County schools
- Train facilities and maintenance staff
- Establish data capture procedures
- Monitor system performance and reliability

**Month 5-6: District Integration**
- Present ROI analysis to district leadership
- Integrate with existing CMMS systems
- Establish maintenance and support procedures
- Plan for district-wide rollout

## Technical Implementation Details

### WiFi Hotspot Configuration

**Network Setup:**
```bash
# Raspberry Pi WiFi Access Point
hostapd configuration:
- SSID: "Arxos-[BuildingName]"
- Security: WPA2/WPA3 (optional password)
- IP Range: 192.168.100.1/24
- No internet gateway (critical requirement)
- DNS redirect to local web interface
```

**Captive Portal:**
- All HTTP requests redirect to building interface
- Works like hotel/airport WiFi but serves building data
- No internet access provided or available
- Immediate access to building information

### Web Interface Architecture

**Frontend Technology:**
- Static HTML/CSS/JavaScript (no external dependencies)
- SVG-based floor plan rendering
- Progressive Web App (PWA) for mobile optimization
- Works offline by design

**Backend API:**
```rust
// REST endpoints served by mesh node
GET /api/building/info          // Building metadata
GET /api/spaces                 // Floor plan geometry  
GET /api/equipment?type=outlet  // Filtered equipment queries
GET /api/systems/electrical     // System topology
POST /api/markup               // Add equipment annotations
```

**Data Synchronization:**
- Web interface queries local SQLite database
- Same data source as SSH terminal interface
- Real-time updates via mesh network propagation
- Consistent information across all interfaces

### Mesh Network Protocol

**LoRa Packet Structure:**
```
[Node_ID][Timestamp][Data_Type][Payload][Checksum]
     4B        4B        1B      Variable    2B
```

**Message Types:**
- **Building_Data:** ArxObject synchronization
- **Query_Request:** Cross-building equipment search
- **Status_Update:** Node health and connectivity
- **System_Control:** HVAC/lighting commands (future)

**Routing Algorithm:**
- Distance-vector routing with building-aware optimization
- Automatic failover for redundant paths
- Query caching to reduce mesh traffic
- Compression improves with network scale

## Security Architecture

### Network Isolation

**Hardline Requirements:**
- **No internet connectivity** on any mesh node
- **No cellular modules** except for SMS gateway (optional)
- **No ethernet uplinks** to building networks
- **No cloud dependencies** or external services

**Local Network Security:**
- WiFi networks use standard WPA2/WPA3 encryption
- SSH access requires key-based authentication
- Web interface serves from local Pi only
- All data stays within mesh network boundaries

### Data Protection

**Access Control:**
- Building-specific WiFi networks limit data access scope
- Terminal access restricted to authorized facilities staff
- Equipment markup requires authentication
- Audit trail for all data modifications

**Privacy Compliance:**
- No personal data collection or storage
- Building data anonymization for shared datasets
- Local data retention policies
- GDPR compliance through data minimization

## Business Model Integration

### Data Sharing Agreement (DSA)

**Private Sequester Tier:** $0.01/sqft/year
- Building data remains on local mesh only
- No data sharing with external parties
- Full control over access and distribution
- Premium security and privacy guarantees

**Shared Anonymous Tier:** FREE
- Anonymized building data contributes to research datasets
- Revenue sharing: 10-25% of data sales to contributors
- Aggregate market intelligence for real estate/insurance
- Individual building privacy maintained

### Token Economics

**BILT Tokens:** Reward building markup and data contribution
- Earned by scanning/marking building equipment
- Spent on premium features or cashed out
- Creates incentive for comprehensive building documentation

**NETWORK Tokens:** Reward mesh node deployment and traffic routing
- Earned by hosting mesh nodes and routing traffic
- Node operators can earn $2,000-20,000/year
- Self-funding network expansion mechanism

## Performance Specifications

### Query Performance
- **Local Queries:** <100ms (SQLite cache hits)
- **Mesh Queries:** 2-5 seconds (local area mesh routing)
- **Cross-Country:** 15-30 seconds (backbone mesh routing)
- **Compression Efficiency:** Improves with network scale

### Network Capacity
- **LoRa Bandwidth:** 5.5kbps per channel
- **ArxObject Size:** 5KB average per building
- **Mesh Throughput:** 50-100 buildings/minute propagation
- **Storage Scaling:** Linear with building count

### Reliability Targets
- **Mesh Uptime:** 99.9% (redundant routing)
- **Node Availability:** 99.5% (solar power + battery backup)
- **Data Consistency:** Eventually consistent across mesh
- **Query Success Rate:** 99%+ for local building data

## Risk Assessment & Mitigation

### Technical Risks

**LoRa Range/Penetration:**
- Risk: Building materials may limit 2km range claims
- Mitigation: Deploy test network, measure actual performance
- Fallback: Reduce range expectations, increase node density

**ArxObject Compression:**
- Risk: 10,000:1 compression may be overly optimistic
- Mitigation: Start with 1,000:1 target, optimize iteratively
- Fallback: Larger data packets, still viable at 100:1 ratio

**Mesh Network Reliability:**
- Risk: Complex routing protocols may introduce failures
- Mitigation: Use proven Meshtastic protocol, not custom routing
- Fallback: Star topology with central coordination nodes

### Business Risks

### Contractor Adoption:
- Risk: Users may resist new interfaces or require workflow changes
- Mitigation: API integration with existing tools eliminates workflow disruption
- Mitigation: Web interface fallback for buildings without CMMS integration
- Fallback: Terminal-only deployment for facilities managers

**Building Network Integration:**
- Risk: IT departments may resist connecting mesh nodes to building networks
- Mitigation: Read-only API access, no internet routing, standard network security
- Mitigation: Demonstrate value through improved work order efficiency
- Fallback: Dedicated WiFi networks where building integration not possible

**Building Owner Concerns:**
- Risk: Security fears about wireless networks in buildings
- Mitigation: "Never touches internet" positioning, local-only operation
- Fallback: Private sequester tier for security-sensitive clients

## Implementation Timeline

### MVP Development (3 months)

**Month 1: Core Infrastructure**
- Week 1-2: ArxObject parser and ASCII renderer
- Week 3-4: SQLite spatial database and terminal interface

**Month 2: Mesh Integration**
- Week 5-6: LoRa mesh networking between Pi nodes
- Week 7-8: Field testing at Jefferson Elementary School

**Month 3: User Interfaces**
- Week 9-10: WiFi hotspot and web interface development
- Week 11-12: Contractor workflow testing and refinement

### Pilot Deployment (Months 4-6)

**Month 4: Single Building Validation**
- Complete Jefferson Elementary deployment
- Facilities manager and contractor training
- Performance monitoring and optimization
- User feedback collection and analysis

**Month 5: Multi-Building Expansion**
- Deploy to 5-10 additional Hillsborough County schools
- Establish data capture and maintenance procedures
- Validate mesh networking across multiple buildings
- Refine business model and pricing

**Month 6: District Presentation**
- Compile ROI analysis and performance metrics
- Present to Hillsborough County leadership
- Negotiate district-wide deployment contract
- Plan scaling to 300+ school buildings

### Production Scaling (Year 1+)

**Months 7-12: District Deployment**
- Rollout across Hillsborough County (300 schools)
- Establish support and maintenance operations
- Train district facilities and IT staff
- Monitor system performance at scale

**Year 2: State Expansion**
- Expand to Florida school districts (3,000 schools)
- Develop commercial real estate partnerships
- Integrate with existing facilities management systems
- Launch data sharing marketplace

**Year 3+: National Network**
- Partner with CBRE for commercial buildings (13,000+ properties)
- Establish nationwide mesh infrastructure
- Launch emergency services integration
- Achieve profitability and consider exit strategies

## Interface Design Specifications

### SSH Terminal Interface

**Target Users:** Facilities managers, IT administrators, power users

**Command Structure:**
```bash
# Building queries
arxos> show building info
arxos> list equipment type:outlet floor:2
arxos> find circuit B-7
arxos> search "emergency lighting"

# System control (future)
arxos> hvac zone:3 temp:72
arxos> lights room:205 on

# Data management
arxos> export room:205 format:PDF
arxos> import markup file:room205.json
arxos> sync mesh full
```

**Features:**
- Auto-completion for building-specific terms
- Command history and favorites
- Bulk operations and scripting support
- Integration with existing facilities workflows

### WiFi Web Interface

**Target Users:** Contractors, maintenance staff, visitors

**Interface Design:**
- **Mobile-first responsive design**
- **High contrast for bright work environments**
- **Large touch targets for work gloves**
- **One-handed operation support**

**Core Features:**

#### Interactive Floor Plan
- SVG-based building layout generated from LiDAR data
- Zoom/pan navigation with touch gestures
- Layer toggles for different building systems
- Real-time equipment highlighting and information

#### System Layer Toggles
- **Electrical:** Outlets, lights, panels, circuits
- **HVAC:** Vents, ducts, thermostats, zones
- **Plumbing:** Fixtures, valves, pipes, shut-offs
- **Fire Safety:** Alarms, sprinklers, exits, extinguishers
- **Security:** Cameras, access points, sensors

#### Equipment Information Panel
- **Location:** Room number, coordinates, nearby landmarks
- **System Details:** Circuit numbers, zone assignments, specifications
- **Maintenance:** Last service date, warranty info, manuals
- **Photos:** Visual reference from initial markup
- **Instructions:** Step-by-step procedures for common tasks

#### Search and Navigation
- **Text Search:** "Find circuit B-7", "Show all HVAC in room 205"
- **Visual Search:** Tap equipment on map to see details
- **Breadcrumb Navigation:** Easy path back to overview
- **Related Items:** "Other equipment on this circuit"

### Network Access Implementation

#### Building Network Integration (Preferred)
```bash
# Raspberry Pi Network Configuration
# Connect to building network via Ethernet or WiFi client

# Ethernet configuration
auto eth0
iface eth0 inet static
address 10.50.1.100      # Assigned by building IT
netmask 255.255.255.0
gateway 10.50.1.1        # Building router (NO internet routing)

# API Server binding
bind_address = "10.50.1.100:8080"  # Building network accessible
internet_gateway = false           # Critical: no internet routing
```

#### CMMS Integration Example
```javascript
// Existing work order system integration
// Called when technician scans equipment barcode

async function enrichWorkOrder(roomNumber, equipmentId) {
    const response = await fetch(
        `http://10.50.1.100:8080/api/equipment/${roomNumber}/${equipmentId}`
    );
    const equipment = await response.json();
    
    // Auto-populate work order with Arxos data
    workOrder.circuit = equipment.circuit;
    workOrder.panel_location = equipment.panel;
    workOrder.last_service = equipment.maintenance_history;
    workOrder.equipment_specs = equipment.specifications;
}

// Zero workflow disruption - just better data
```

#### Dedicated Network Fallback
```bash
# Only used when building network integration not possible
# File: /etc/hostapd/hostapd.conf
interface=wlan1
ssid=Arxos-Jefferson-Elementary
hw_mode=g
channel=7
auth_algs=1
wpa=2
wpa_key_mgmt=WPA-PSK

# Still no internet gateway - local network only
# IP Range: 192.168.100.1/24
# DNS points to local web interface
```

## Data Capture Workflow

### Initial Building Documentation

**iPhone LiDAR Scanning:**
1. **Room Capture:** 20-second LiDAR scan per space
2. **Equipment Markup:** AR interface for marking equipment
3. **System Identification:** Link equipment to building systems
4. **Validation:** Review and verify captured data

**ArxObject Generation:**
1. **Point Cloud Processing:** Extract building geometry
2. **Semantic Analysis:** Identify rooms, equipment, connections
3. **Compression:** Convert to queryable ArxObject format
4. **Mesh Propagation:** Distribute to network nodes

### Ongoing Data Maintenance

**Crowd-Sourced Updates:**
- Contractors mark new equipment during installations
- Facilities staff update system changes
- Maintenance workers report equipment status
- Emergency responders add access notes

**Data Quality Assurance:**
- Markup validation through consensus
- Equipment lifecycle tracking
- System change approval workflows
- Regular data audits and cleanup

## Performance Monitoring

### Key Metrics

**Technical Performance:**
- Query response time by interface type
- Mesh network latency and packet loss
- ArxObject compression efficiency
- Node uptime and reliability

**User Adoption:**
- Interface usage patterns by user type
- Feature utilization rates
- User feedback and satisfaction scores
- Training completion and competency

**Business Metrics:**
- Cost savings vs traditional building surveys
- Contractor efficiency improvements
- Emergency response time reduction
- Data sharing revenue generation

### Monitoring Infrastructure

**Mesh Network Telemetry:**
- Node health and connectivity status
- Network topology and routing efficiency
- Data propagation delays and failures
- Bandwidth utilization and optimization

**User Interface Analytics:**
- Query patterns and frequency
- Feature usage and abandonment
- Error rates and user assistance needs
- Mobile vs terminal interface preferences

## Integration Strategy

### Existing Systems Integration

**CMMS Integration:**
- Export building data to existing maintenance systems
- Import work orders and equipment histories
- Sync with asset management databases
- Maintain data consistency across platforms

**Emergency Services:**
- Provide building layouts to fire departments
- Share access codes and utility shut-offs
- Emergency evacuation route optimization
- First responder training materials

**Insurance and Real Estate:**
- Anonymous aggregate data for risk assessment
- Building performance benchmarking
- Market intelligence for property valuation
- Maintenance cost prediction models

### API Design

**RESTful API Endpoints:**
```
GET /api/building                    # Building metadata
GET /api/spaces                      # Floor plan geometry
GET /api/equipment                   # Equipment inventory
GET /api/systems/{type}              # System-specific queries
POST /api/markup                     # Add new equipment markup
PUT /api/equipment/{id}              # Update equipment information
DELETE /api/equipment/{id}           # Remove equipment
```

**Terminal Command API:**
```bash
# Query building information
arxos query --type equipment --filter "circuit:B-7"
arxos export --format CAD --room 205
arxos import --file markup.json --validate

# System control (future)
arxos control --system hvac --zone 3 --temp 72
arxos monitor --system electrical --alerts on
```

## Success Metrics

### MVP Success Criteria

**Technical Milestones:**
- ArxObject compression achieves 1,000:1 ratio minimum
- Mesh network maintains <5 second query response times
- WiFi interface works reliably on contractor mobile devices
- Terminal interface supports all building query operations

**User Adoption Milestones:**
- 90%+ contractor adoption rate for WiFi interface
- 100% facilities manager competency with terminal interface
- <30 second average time to find equipment information
- Zero internet connectivity attempts or requests

**Business Validation:**
- 50%+ cost reduction vs traditional building surveys
- Positive ROI demonstration for Hillsborough County
- Commitment letter for district-wide deployment
- Interest from at least one commercial real estate partner

### Long-Term Success Indicators

**Network Growth:**
- 1,000+ mesh nodes deployed across Florida
- 10,000+ buildings documented and accessible
- 100,000+ equipment items marked and queryable
- $1M+ annual revenue from data sharing agreements

**Market Validation:**
- Partnership with major facilities management company
- Integration with leading CMMS platforms
- Emergency services adoption in multiple jurisdictions
- Insurance industry recognition and data purchase agreements

## Next Steps

### Immediate Actions (Next 30 Days)

1. **Technical Validation:**
   - Build basic ArxObject parser in Rust
   - Test iPhone LiDAR data capture workflow
   - Validate SQLite spatial indexing performance
   - Prototype ASCII terminal rendering

2. **Partnership Development:**
   - Schedule meeting with Jefferson Elementary facilities manager
   - Identify specific building documentation pain points
   - Establish pilot testing agreement
   - Define success criteria and feedback mechanisms

3. **Team Assembly:**
   - Finalize technical team roles and responsibilities
   - Establish development environment and tools
   - Create project management and communication workflows
   - Plan weekly progress reviews and milestone tracking

### Critical Decisions Required

1. **Network integration priority:** Focus on API integration vs web interface for MVP?
2. **CMMS partnership strategy:** Which work order systems to target first?
3. **Building network requirements:** Static IP allocation vs dynamic discovery?
4. **API authentication model:** Open local access or building-specific credentials?
5. **Mesh protocol:** Custom implementation or Meshtastic modification?

---

**Project Status:** Design phase complete, ready for technical implementation  
**Team Review Required:** Technical architecture validation, resource allocation, timeline approval  
**Next Milestone:** Working ArxObject parser and terminal interface (Week 2)
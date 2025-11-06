# ArxOS Integration Examples

This document provides complete, end-to-end examples for common ArxOS workflows and integrations.

---

## Table of Contents

1. [IFC Import Workflow](#ifc-import-workflow)
2. [AR Scan Integration Workflow](#ar-scan-integration-workflow)
3. [Sensor Data Processing Workflow](#sensor-data-processing-workflow)
4. [Equipment Management Workflow](#equipment-management-workflow)
5. [Building Data Export/Import](#building-data-exportimport)
6. [Git Workflow Examples](#git-workflow-examples)
7. [Mobile App Integration](#mobile-app-integration)
8. [CI/CD Integration](#cicd-integration)

---

## IFC Import Workflow

### Overview

Import an IFC building model file and extract hierarchy automatically.

### Step-by-Step Example

**1. Prepare IFC File**

Place your IFC file in an accessible location:
```bash
# Example: building.ifc in current directory
ls -lh building.ifc
```

**2. Import IFC File**

```bash
# Basic import
arx import building.ifc

# Dry run to preview changes
arx import building.ifc --dry-run

# Import to specific Git repository
arx import building.ifc --repo https://github.com/example/building.git
```

**3. Verify Import**

```bash
# Check building data
cat building.yaml

# List rooms
arx room list --building "Building Name"

# List equipment
arx equipment list --building "Building Name"
```

**4. Review Extracted Data**

The import process extracts:
- Building hierarchy (floors, wings, rooms)
- Equipment locations and types
- Spatial relationships
- Coordinate systems

**Example Output:**
```yaml
# building.yaml (auto-generated)
building:
  id: building-001
  name: Office Building
  floors:
    - id: floor-01
      name: First Floor
      level: 1
      rooms:
        - id: room-001
          name: Conference Room
          equipment:
            - id: equip-001
              name: VAV-301
              equipment_type: HVAC
```

### Troubleshooting

**Issue: IFC file not found**
```bash
# Ensure file exists and is accessible
ls -lh building.ifc
# Use absolute path if needed
arx import /absolute/path/to/building.ifc
```

**Issue: Import errors**
```bash
# Validate IFC file first
# Check file format
file building.ifc
# Should show: "IFC STEP"

# Use verbose mode for detailed errors
arx import building.ifc --dry-run 2>&1 | tee import.log
```

---

## AR Scan Integration Workflow

### Overview

Process AR scan data from mobile devices and integrate detected equipment into building data.

### Step-by-Step Example

**1. Capture AR Scan on Mobile Device**

Use the ArxOS mobile app (iOS/Android) to scan a room and detect equipment.

**2. Export AR Scan Data**

The mobile app saves scan data as JSON:
```json
{
  "detectedEquipment": [
    {
      "name": "VAV-301",
      "equipmentType": "HVAC",
      "position": {"x": 10.0, "y": 20.0, "z": 0.0},
      "confidence": 0.95
    }
  ],
  "roomName": "Conference Room",
  "floorLevel": 2
}
```

**3. Save Scan File**

Save scan data to a file:
```bash
# Save to .arxos/ar-scans/ directory
mkdir -p .arxos/ar-scans
# Copy scan file from mobile or receive via API
cp scan_20250103_143000.json .arxos/ar-scans/
```

**4. Integrate AR Scan**

```bash
# Integrate scan data
arx ar-integrate .arxos/ar-scans/scan_20250103_143000.json \
    --room "Conference Room" \
    --floor 2 \
    --building "Office Building" \
    --commit

# Custom commit message
arx ar-integrate scan.json \
    --room "Conference Room" \
    --floor 2 \
    --building "Office Building" \
    --commit \
    --message "Add equipment from AR scan - Conference Room"
```

**5. Review Pending Equipment**

```bash
# List pending equipment (requires confirmation)
arx ar pending list --building "Office Building"

# Confirm pending equipment
arx ar pending confirm --building "Office Building" --pending-id pending-001

# Reject pending equipment
arx ar pending reject --building "Office Building" --pending-id pending-002
```

**6. Verify Integration**

```bash
# List equipment in room
arx equipment list --room "Conference Room"

# Show equipment details
arx equipment show "VAV-301"
```

### Sample AR Scan Data File

See `examples/ar/scan_data.json` for a complete example.

---

## Sensor Data Processing Workflow

### Overview

Process sensor data from IoT devices (ESP32, RP2040, Arduino) and update equipment status.

### Step-by-Step Example

**1. Prepare Sensor Data**

Create sensor data files in YAML or JSON format:
```yaml
# sensor_data.yaml
sensor_id: esp32_temp_001
sensor_type: temperature
timestamp: 2025-01-03T14:30:00Z
values:
  temperature: 72.5
  humidity: 45.0
equipment_id: HVAC-301
building: Office Building
floor: 2
room: Conference Room
```

**2. Process Sensor Data**

```bash
# Process sensor data directory
arx process-sensors ./sensor-data --building "Office Building"

# Auto-commit changes
arx process-sensors ./sensor-data --building "Office Building" --commit

# Watch directory for new sensor files
arx process-sensors ./sensor-data --building "Office Building" --watch
```

**3. HTTP Server Mode**

Start HTTP server for real-time sensor data ingestion:
```bash
# Start HTTP server
arx sensors-http --building "Office Building" --host localhost --port 8080
```

**4. Send Sensor Data via HTTP**

```bash
# POST sensor data to server
curl -X POST http://localhost:8080/sensors \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "esp32_temp_001",
    "sensor_type": "temperature",
    "timestamp": "2025-01-03T14:30:00Z",
    "values": {
      "temperature": 72.5,
      "humidity": 45.0
    },
    "equipment_id": "HVAC-301",
    "building": "Office Building",
    "floor": 2,
    "room": "Conference Room"
  }'
```

**5. MQTT Subscriber Mode**

Start MQTT subscriber for real-time sensor data:
```bash
# Start MQTT subscriber
arx sensors-mqtt \
    --building "Office Building" \
    --broker mqtt.example.com \
    --port 1883 \
    --username sensor_user \
    --password sensor_pass \
    --topics "sensors/+/temperature" \
    --topics "sensors/+/humidity"
```

**6. Publish Sensor Data via MQTT**

```bash
# Publish to MQTT broker
mosquitto_pub -h mqtt.example.com -p 1883 \
    -u sensor_user -P sensor_pass \
    -t "sensors/esp32_temp_001/temperature" \
    -m '{"sensor_id":"esp32_temp_001","temperature":72.5,"timestamp":"2025-01-03T14:30:00Z"}'
```

### Sample Sensor Data Files

See `examples/sensors/temperature_readings.yaml` and `examples/sensors/air_quality.json` for complete examples.

---

## Equipment Management Workflow

### Overview

Add, update, and manage equipment in building data.

### Step-by-Step Example

**1. Add Equipment**

```bash
# Add equipment with auto-generated address
arx equipment add \
    --room "Conference Room" \
    --name "VAV-301" \
    --equipment-type "HVAC" \
    --position "10.0,20.0,0.0" \
    --commit

# Add equipment with custom address
arx equipment add \
    --room "Conference Room" \
    --name "VAV-301" \
    --equipment-type "HVAC" \
    --at "/usa/ny/brooklyn/office-building/floor-02/mech/vav-301" \
    --property "model=ABC123" \
    --property "serial=XYZ789" \
    --commit
```

**2. List Equipment**

```bash
# List all equipment
arx equipment list

# List equipment in room
arx equipment list --room "Conference Room"

# List equipment by type
arx equipment list --equipment-type "HVAC" --verbose

# Interactive browser
arx equipment list --interactive
```

**3. Update Equipment**

```bash
# Update equipment properties
arx equipment update "VAV-301" \
    --property "status=Maintenance" \
    --property "last_service=2025-01-03" \
    --commit

# Update equipment position
arx equipment update "VAV-301" \
    --position "10.5,20.3,0.0" \
    --commit
```

**4. Remove Equipment**

```bash
# Remove equipment
arx equipment remove "VAV-301" --confirm --commit
```

**5. Search Equipment**

```bash
# Search by name
arx search "VAV" --equipment

# Search with regex
arx search "HVAC.*301" --regex --equipment

# Query by address pattern
arx query "/usa/ny/*/floor-02/mech/*"
```

---

## Building Data Export/Import

### Overview

Export building data to various formats and import from other sources.

### Step-by-Step Example

**1. Export to IFC**

```bash
# Export to IFC format
arx export --format ifc --output building.ifc

# Export with delta (only changes)
arx export --format ifc --output building.ifc --delta
```

**2. Export to glTF (for AR)**

```bash
# Export to glTF for AR visualization
arx export --format gltf --output building.gltf

# Export to USDZ for iOS AR
arx export --format usdz --output building.usdz
```

**3. Export to Git Repository**

```bash
# Export to Git repository
arx export --format git --repo https://github.com/example/building.git

# Export with delta
arx export --format git --repo https://github.com/example/building.git --delta
```

**4. Sync to IFC File**

```bash
# One-time sync
arx sync --ifc building.ifc

# Continuous sync (watch mode)
arx sync --ifc building.ifc --watch

# Sync with delta
arx sync --ifc building.ifc --delta
```

**5. Import from Git Repository**

```bash
# Clone repository
git clone https://github.com/example/building.git

# Import building data
cd building
arx import building.yaml
```

---

## Git Workflow Examples

### Overview

ArxOS uses Git for version control. All building data changes are tracked via Git commits.

### Step-by-Step Example

**1. Initialize Building with Git**

```bash
# Initialize building with Git
arx init --name "Office Building" --git-init --commit
```

**2. Check Status**

```bash
# Show repository status
arx status

# Detailed status
arx status --verbose

# Interactive dashboard
arx status --interactive
```

**3. Stage Changes**

```bash
# Stage all changes
arx stage

# Stage specific file
arx stage building.yaml
```

**4. Commit Changes**

```bash
# Commit staged changes
arx commit "Add new HVAC equipment"

# Auto-commit with configuration
# Set in config: building.auto_commit = true
```

**5. View History**

```bash
# Show commit history
arx history

# Limit results
arx history --limit 10

# Show history for specific file
arx history --file building.yaml --verbose
```

**6. View Differences**

```bash
# Show diff
arx diff

# Compare with specific commit
arx diff --commit abc123

# Show diff for specific file
arx diff --file building.yaml

# Interactive diff viewer
arx diff --interactive
```

**7. Unstage Changes**

```bash
# Unstage all
arx unstage

# Unstage specific file
arx unstage building.yaml
```

---

## Mobile App Integration

### Overview

Integrate ArxOS with iOS and Android mobile apps using FFI bindings.

### iOS Integration (Swift)

**1. Link ArxOS Framework**

```swift
// Add to Xcode project
// Link libarxos.a or use XCFramework
```

**2. Call FFI Functions**

```swift
import ArxOSCore

// List rooms
let roomsJSON = arxos_list_rooms("Office Building")
let rooms = try JSONDecoder().decode([RoomInfo].self, from: roomsJSON.data(using: .utf8)!)

// Get room details
let roomJSON = arxos_get_room("Office Building", "Conference Room")
let room = try JSONDecoder().decode(RoomInfo.self, from: roomJSON.data(using: .utf8)!)

// Save AR scan
let scanData = ARScanData(...)
let scanJSON = try JSONEncoder().encode(scanData)
let result = arxos_save_ar_scan(
    String(data: scanJSON, encoding: .utf8)!,
    "Office Building",
    0.7  // confidence threshold
)

// Free string after use
arxos_free_string(result)
```

**3. Handle Errors**

```swift
// Check for errors
let errorCode = arxos_last_error()
if errorCode != 0 {
    let errorMessage = arxos_last_error_message()
    print("Error: \(String(cString: errorMessage))")
    arxos_free_string(errorMessage)
}
```

### Android Integration (Kotlin)

**1. Link Native Library**

```kotlin
// Add to build.gradle
android {
    ndk {
        abiFilters += listOf("arm64-v8a", "armeabi-v7a", "x86", "x86_64")
    }
}
```

**2. Call JNI Functions**

```kotlin
// Load native library
init {
    System.loadLibrary("arxos")
}

// List rooms
external fun listRooms(buildingName: String): String

// Get room details
external fun getRoom(buildingName: String, roomId: String): String

// Save AR scan
external fun saveARScan(
    jsonData: String,
    buildingName: String,
    confidenceThreshold: Double
): String

// Use in code
val roomsJSON = listRooms("Office Building")
val rooms = Gson().fromJson(roomsJSON, Array<RoomInfo>::class.java)
```

**3. Handle Errors**

```kotlin
// Check for errors
external fun getLastError(): Int
external fun getLastErrorMessage(): String

val errorCode = getLastError()
if (errorCode != 0) {
    val errorMessage = getLastErrorMessage()
    Log.e("ArxOS", "Error: $errorMessage")
}
```

### Complete Example

See `examples/mobile/` directory for complete iOS and Android integration examples.

---

## CI/CD Integration

### Overview

Integrate ArxOS into CI/CD pipelines for automated building data validation and processing.

### GitHub Actions Example

**`.github/workflows/arxos-ci.yml`:**

```yaml
name: ArxOS CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      
      - name: Install ArxOS
        run: cargo install arxos
      
      - name: Validate Building Data
        run: arx validate --path .
      
      - name: Check Git Status
        run: arx status --verbose
      
      - name: Export to IFC
        run: arx export --format ifc --output building.ifc
      
      - name: Upload IFC Artifact
        uses: actions/upload-artifact@v3
        with:
          name: building-ifc
          path: building.ifc
```

### GitLab CI Example

**`.gitlab-ci.yml`:**

```yaml
stages:
  - validate
  - export

validate:
  stage: validate
  image: rust:latest
  script:
    - cargo install arxos
    - arx validate --path .
    - arx status --verbose
  artifacts:
    paths:
      - building.yaml

export:
  stage: export
  image: rust:latest
  script:
    - cargo install arxos
    - arx export --format ifc --output building.ifc
  artifacts:
    paths:
      - building.ifc
```

### Jenkins Example

**`Jenkinsfile`:**

```groovy
pipeline {
    agent any
    
    stages {
        stage('Validate') {
            steps {
                sh 'cargo install arxos'
                sh 'arx validate --path .'
                sh 'arx status --verbose'
            }
        }
        
        stage('Export') {
            steps {
                sh 'arx export --format ifc --output building.ifc'
                archiveArtifacts 'building.ifc'
            }
        }
    }
}
```

---

## Additional Resources

- **API Reference:** See `docs/API_REFERENCE.md` for complete API documentation
- **User Guide:** See `docs/core/USER_GUIDE.md` for detailed usage instructions
- **Troubleshooting:** See `docs/TROUBLESHOOTING.md` for common issues and solutions

---

**Note:** All examples in this document assume ArxOS is installed and configured. See the [User Guide](docs/core/USER_GUIDE.md) for installation instructions.


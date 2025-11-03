<!-- d4d0e380-7a45-49c4-9417-4414059f67dd 1ef238d5-1fd9-4dd7-b3b9-dc7e228df3b7 -->
# ArxOS 0.1 Comprehensive Implementation Plan

## Overview

Implement all identified gaps to reach production-ready 0.1 release with three functional pillars: terminal workflow, mobile AR, and hardware integration.

## Phase 1: Configuration Management Overhaul (2-3 days)

### 1.1 Configuration Precedence & Validation

**Current State**: Config exists but lacks clear precedence hierarchy and comprehensive validation.

**Implementation**:

Update `src/config/manager.rs`:

- Implement strict precedence: ENV vars > project config > user config > global config > defaults
- Add comprehensive validation for all config fields
- Add schema documentation generation

Update `src/config/validation.rs`:

- Add `ConfigValidator::validate_all()` method
- Validate paths exist and are writable
- Validate numeric ranges (threads, memory limits)
- Validate email format, coordinate systems
- Return detailed validation errors with suggestions

Create `src/config/schema.rs`:

- Generate JSON schema for configuration
- Document all config options with examples
- Export schema for IDE autocomplete

**Files to modify**:

- `src/config/manager.rs` (lines 40-87, 176-220)
- `src/config/validation.rs` (new comprehensive validators)
- `src/config/schema.rs` (new file)
- `src/config/mod.rs` (re-export schema)

**Testing**:

- Add tests for precedence order
- Add tests for validation failures
- Add tests for environment variable overrides

## Phase 2: AR Export (USDZ/glTF) (1-2 weeks)

### 2.1 Create Export Infrastructure

**Implementation**:

Create `src/export/mod.rs`:

```rust
pub mod ar;
pub use ar::{ARExporter, ARFormat};
```

Create `src/export/ar/mod.rs`:

```rust
pub mod usdz;
pub mod gltf;
pub mod anchor;

pub enum ARFormat {
    USDZ,
    GLTF,
}

pub struct ARExporter {
    building_data: BuildingData,
}

impl ARExporter {
    pub fn export(&self, format: ARFormat, output: &Path) -> Result<()>
}
```

### 2.2 Implement glTF Export (Week 1)

Create `src/export/ar/gltf.rs`:

- Use `gltf` crate (already in dependencies)
- Convert BuildingData → glTF scene graph
- Export floors as separate nodes
- Export equipment as meshes with metadata
- Include materials and textures
- Preserve spatial coordinates

**Key Functions**:

```rust
pub fn export_building_to_gltf(building: &BuildingData, output: &Path) -> Result<()>
fn convert_floor_to_node(floor: &FloorData) -> gltf::Node
fn convert_equipment_to_mesh(equipment: &EquipmentData) -> gltf::Mesh
fn create_material_for_equipment(equipment_type: &str) -> gltf::Material
```

### 2.3 Implement USDZ Export (Week 2)

Create `src/export/ar/usdz.rs`:

- Research USD C++ library FFI bindings (or use `usd-rs` if available)
- Convert BuildingData → USD scene graph
- Package as USDZ (zip with USD + assets)
- Preserve ARKit-specific metadata

**Alternative**: If USD FFI is complex, export to glTF first, then convert using external tool (Reality Converter).

### 2.4 Spatial Anchor Management

Create `src/export/ar/anchor.rs`:

```rust
pub struct SpatialAnchor {
    pub id: String,
    pub position: Point3D,
    pub rotation: Quaternion,
    pub metadata: HashMap<String, String>,
}

pub fn export_anchors_to_json(anchors: &[SpatialAnchor], output: &Path) -> Result<()>
pub fn import_anchors_from_json(input: &Path) -> Result<Vec<SpatialAnchor>>
```

### 2.5 CLI Integration

Update `src/commands/export.rs`:

- Add `--format usdz|gltf` flag
- Add `--output <path>` flag
- Add `--include-anchors` flag
```rust
pub fn handle_export_ar(
    building: String,
    format: ARFormat,
    output: PathBuf,
    include_anchors: bool,
) -> Result<()>
```


Update `src/cli/mod.rs`:

- Add `ExportAR` command variant

**Dependencies to add**:

```toml
[dependencies]
gltf = "1.4"  # glTF support
gltf-json = "1.4"
```

**Testing**:

- Export sample building to glTF
- Validate glTF with online validators
- Load in Blender/Three.js viewer
- Test coordinate system accuracy

## Phase 3: Mobile AR Implementation (2-3 weeks)

### 3.1 iOS ARKit Integration (Week 1-1.5)

Update `ios/ArxOSMobile/ArxOSMobile/Views/ARViewContainer.swift`:

- Implement actual ARKit session
- Load USDZ/glTF models
- Place models at spatial anchors
- Implement tap-to-place equipment
- Save AR scan data to JSON

**Key Implementation**:

```swift
class ARViewContainer: UIViewRepresentable {
    func makeUIView(context: Context) -> ARView {
        let arView = ARView(frame: .zero)
        let config = ARWorldTrackingConfiguration()
        config.planeDetection = [.horizontal, .vertical]
        arView.session.run(config)
        return arView
    }
    
    func loadBuilding(from url: URL) {
        // Load USDZ model
        let entity = try? Entity.load(contentsOf: url)
        // Add to scene
    }
}
```

Update `ios/ArxOSMobile/ArxOSMobile/Services/ArxOSCoreFFI.swift`:

- Add `loadARModel(path: String)` FFI call
- Add `saveARScan(scanData: String)` FFI call
- Enable FFI calls (uncomment TODO sections)

Create `src/mobile_ffi/ar_ops.rs`:

```rust
#[no_mangle]
pub unsafe extern "C" fn arxos_load_ar_model(
    building_name: *const c_char,
    format: *const c_char,
    output_path: *const c_char,
) -> *mut c_char
```

### 3.2 Android ARCore Integration (Week 1.5-2)

Update `android/app/src/main/java/com/arxos/mobile/ui/components/ARViewContainer.kt`:

- Implement ARCore session
- Load glTF models using Sceneform or Filament
- Implement plane detection
- Implement tap-to-place
- Save AR scan data

**Key Implementation**:

```kotlin
class ARViewContainer : View {
    private lateinit var session: Session
    private lateinit var scene: Scene
    
    fun initializeARCore() {
        session = Session(context)
        val config = Config(session)
        config.planeFindingMode = Config.PlaneFindingMode.HORIZONTAL_AND_VERTICAL
        session.configure(config)
    }
    
    fun loadGLTFModel(uri: String) {
        // Use Filament to load glTF
    }
}
```

Update `android/app/src/main/java/com/arxos/mobile/service/ArxOSCoreJNI.kt`:

- Add JNI bindings for AR operations
- Mirror iOS FFI functions

Create `src/mobile_ffi/jni_ar.rs`:

```rust
#[no_mangle]
pub extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeLoadARModel(
    env: *mut JNIEnv,
    _class: JClass,
    building_name: JString,
    format: JString,
    output_path: JString,
) -> jstring
```

### 3.3 AR Scanning Workflow

Implement complete AR scanning workflow:

1. User opens AR view in mobile app
2. App calls FFI to export building to AR format
3. AR SDK loads model and displays in camera view
4. User scans room and taps to place equipment
5. App saves scan data (positions, types, confidence)
6. App calls FFI to process AR scan
7. Rust core validates and adds to pending equipment
8. User reviews pending equipment in app
9. User confirms/rejects equipment
10. Changes committed to Git

**Files to create**:

- `src/mobile_ffi/ar_ops.rs`
- `src/mobile_ffi/jni_ar.rs`
- `ios/ArxOSMobile/ArxOSMobile/Models/ARScanData.swift`
- `android/app/src/main/java/com/arxos/mobile/data/ARScanData.kt`

**Testing**:

- Test AR model loading on physical devices
- Test spatial alignment accuracy
- Test equipment placement workflow
- Test AR scan → pending → confirmation flow

## Phase 4: Hardware Sensor Pipeline (1-2 weeks)

### 4.1 Complete Sensor Ingestion Service

**Current State**: Basic file reading exists, needs real-time processing.

Update `src/hardware/ingestion.rs`:

- Add HTTP endpoint listener (using `axum` or `warp`)
- Add MQTT subscriber (using `rumqttc`)
- Add WebSocket support for real-time updates
- Implement automatic sensor data processing

**Implementation**:

```rust
pub struct RealtimeSensorIngestion {
    http_server: Option<HttpServer>,
    mqtt_client: Option<MqttClient>,
    ws_server: Option<WebSocketServer>,
    processor: SensorProcessor,
}

impl RealtimeSensorIngestion {
    pub async fn start_http_listener(&mut self, port: u16) -> Result<()>
    pub async fn start_mqtt_subscriber(&mut self, broker: &str) -> Result<()>
    pub async fn start_websocket_server(&mut self, port: u16) -> Result<()>
}
```

### 4.2 Equipment Status Updater Enhancement

Update `src/hardware/status_updater.rs`:

- Add real-time equipment status updates
- Implement threshold-based alerting
- Add equipment health scoring
- Implement predictive maintenance flags

**Implementation**:

```rust
impl EquipmentStatusUpdater {
    pub fn process_realtime_sensor_data(&mut self, data: &SensorData) -> Result<UpdateResult>
    pub fn check_alert_thresholds(&self, data: &SensorData) -> Vec<Alert>
    pub fn calculate_health_score(&self, equipment_id: &str) -> f64
    pub fn predict_maintenance_needs(&self, equipment_id: &str) -> Vec<MaintenanceTask>
}
```

### 4.3 Sensor-Equipment Mapping

Create `src/hardware/mapping.rs`:

```rust
pub struct SensorEquipmentMapper {
    mappings: HashMap<String, String>, // sensor_id -> equipment_id
}

impl SensorEquipmentMapper {
    pub fn load_from_building_data(building: &BuildingData) -> Self
    pub fn map_sensor_to_equipment(&self, sensor_id: &str) -> Option<String>
    pub fn add_mapping(&mut self, sensor_id: String, equipment_id: String)
    pub fn save_to_building_data(&self, building: &mut BuildingData)
}
```

### 4.4 CLI Integration

Update `src/commands/sensors.rs`:

- Add `arx sensor listen --http 8080` command
- Add `arx sensor listen --mqtt broker.example.com` command
- Add `arx sensor status` command
- Add `arx sensor map <sensor_id> <equipment_id>` command

**Implementation**:

```rust
pub fn handle_sensor_listen(
    protocol: SensorProtocol,
    address: String,
    building: String,
    auto_commit: bool,
) -> Result<()>

pub fn handle_sensor_status(building: String) -> Result<()>

pub fn handle_sensor_map(
    sensor_id: String,
    equipment_id: String,
    building: String,
) -> Result<()>
```

### 4.5 Hardware Examples Integration

Update `hardware/examples/esp32-temperature/`:

- Add HTTP POST to ArxOS endpoint
- Add MQTT publish example
- Add WebSocket example

**Dependencies to add**:

```toml
[dependencies]
# HTTP server
axum = "0.7"
tokio = { version = "1.0", features = ["full"] }

# MQTT client
rumqttc = "0.24"

# WebSocket
tokio-tungstenite = "0.21"
```

**Testing**:

- Test HTTP sensor data ingestion
- Test MQTT sensor data ingestion
- Test equipment status updates
- Test threshold alerts
- Test Git commit automation

## Phase 5: Integration & Testing (1 week)

### 5.1 End-to-End Workflow Tests

Create `tests/e2e_workflow_tests.rs`:

- Test complete IFC import → 3D render → AR export workflow
- Test AR scan → pending → confirmation → Git commit workflow
- Test sensor data → equipment update → Git commit workflow
- Test game review → AR export → mobile visualization workflow

### 5.2 Mobile Integration Tests

Create `tests/mobile_ar_integration_tests.rs`:

- Test FFI AR export functions
- Test AR scan processing
- Test spatial coordinate transformations
- Test model loading on simulators

### 5.3 Hardware Integration Tests

Create `tests/hardware_realtime_tests.rs`:

- Test HTTP sensor ingestion
- Test MQTT sensor ingestion
- Test equipment status updates
- Test threshold alerting

### 5.4 Performance Testing

Create `benches/ar_export_benchmarks.rs`:

- Benchmark glTF export performance
- Benchmark USDZ export performance
- Benchmark sensor data processing throughput

### 5.5 Fix Build Warnings

Fix all compiler warnings:

- Remove unused variables (prefix with `_`)
- Remove unused imports
- Fix unused `mut` declarations
- Address clippy warnings

**Files to fix**:

- `src/commands/game.rs` (lines 56, 123)
- `src/game/learning.rs` (line 217)
- Other files with warnings

## Phase 6: Documentation Updates (Deferred)

Per user request, documentation is deferred. However, inline code documentation (rustdoc) should be added as features are implemented.

## Dependencies to Add

Update `Cargo.toml`:

```toml
[dependencies]
# AR export
gltf = "1.4"
gltf-json = "1.4"

# Real-time sensor ingestion
axum = "0.7"
tokio = { version = "1.0", features = ["full"] }
rumqttc = "0.24"
tokio-tungstenite = "0.21"

# Async runtime
async-trait = "0.1"
futures = "0.3"
```

## Success Criteria

### Terminal Workflow

- IFC import → YAML → 3D render → Git commit works end-to-end
- Search, filter, and game commands functional
- Configuration system with validation and precedence

### Mobile AR

- iOS app loads USDZ models in AR
- Android app loads glTF models in AR
- AR scanning workflow saves to Git
- Spatial alignment accurate within ±10cm

### Hardware Integration

- HTTP/MQTT sensor ingestion working
- Equipment status updates automatically
- Threshold alerts trigger correctly
- Git commits automated for sensor updates

### Quality

- All tests pass (150+ tests)
- No compiler warnings
- Build time < 2 minutes
- Memory usage < 500MB for typical workflows

## Timeline

- Week 1: Configuration overhaul + glTF export
- Week 2: USDZ export + iOS ARKit integration
- Week 3: Android ARCore + hardware HTTP/MQTT
- Week 4: Integration testing + bug fixes + 0.1 release

## Risks & Mitigations

**Risk**: USDZ export complexity (no stable Rust crates)

**Mitigation**: Use glTF → Reality Converter workflow initially, add native USDZ later

**Risk**: ARCore/ARKit platform differences

**Mitigation**: Abstract AR operations behind common FFI interface

**Risk**: Real-time sensor processing performance

**Mitigation**: Use async Rust with tokio, implement backpressure

**Risk**: Scope creep (all three pillars in parallel)

**Mitigation**: Strict feature freeze after Phase 5, defer nice-to-haves to 0.2

### To-dos

- [ ] Implement strict configuration precedence hierarchy (ENV > project > user > global > defaults)
- [ ] Add comprehensive configuration validation with detailed error messages
- [ ] Create configuration schema documentation and JSON schema export
- [ ] Create src/export/ module structure with AR export foundation
- [ ] Implement glTF export from BuildingData with materials and spatial coordinates
- [ ] Implement USDZ export (native or via glTF conversion)
- [ ] Implement spatial anchor management and JSON serialization
- [ ] Add CLI commands for AR export (arx export --format usdz|gltf)
- [ ] Implement ARKit integration in iOS app with model loading and placement
- [ ] Create AR-specific FFI functions for iOS (load model, save scan)
- [ ] Implement ARCore integration in Android app with glTF loading
- [ ] Create JNI bindings for AR operations in Android
- [ ] Implement complete AR scanning workflow (scan → pending → confirm → Git)
- [ ] Add HTTP endpoint listener for real-time sensor data ingestion
- [ ] Add MQTT subscriber for sensor data ingestion
- [ ] Add WebSocket server for real-time sensor updates
- [ ] Enhance equipment status updater with real-time processing and alerting
- [ ] Create sensor-equipment mapping system with persistence
- [ ] Add CLI commands for sensor operations (listen, status, map)
- [ ] Update hardware examples with HTTP/MQTT/WebSocket integration
- [ ] Create end-to-end workflow tests for all three pillars
- [ ] Create mobile AR integration tests
- [ ] Create hardware real-time integration tests
- [ ] Add benchmarks for AR export and sensor processing
- [ ] Fix all compiler warnings and clippy issues
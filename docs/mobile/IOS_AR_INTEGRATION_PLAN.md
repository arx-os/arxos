# iOS AR Integration Plan

**Date:** November 2025  
**Status:** Planning  
**Priority:** High - Critical Path to 0.1 Release

---

## Overview

Complete iOS ARKit integration for ArxOS, enabling users to:
1. **Load building models** in AR (USDZ/glTF)
2. **Scan rooms** and detect equipment using ARKit
3. **Save scan data** to Rust backend for processing
4. **Review pending equipment** and confirm/reject
5. **Commit confirmed equipment** to Git

---

## Current State Analysis

### ✅ What's Already Implemented

1. **ARKit Infrastructure** ✅
   - `ARViewContainer.swift` - Basic ARKit session setup
   - `ARScanView.swift` - UI for AR scanning
   - ARCoordinator with session delegate
   - Plane detection configured
   - USDZ model loading (hardcoded to Bundle.main)

2. **Rust Backend** ✅
   - `arxos_export_for_ar()` - Exports building to AR format (glTF/USDZ)
   - `arxos_process_ar_scan_to_pending()` - Processes AR scan data
   - `arxos_parse_ar_scan()` - Parses AR scan JSON
   - Pending equipment management system
   - AR scan processing pipeline

3. **Swift FFI Wrappers** ✅
   - `ArxOSCoreFFI.swift` - FFI wrapper class
   - `exportForAR()` - Wrapped export function
   - `processARScanToPending()` - Wrapped scan processing
   - Memory management with `arxos_free_string()`

4. **Data Models** ✅
   - `ARScanData` - AR scan data structure
   - `DetectedEquipment` - Equipment detection model
   - `PendingARScanResult` - Processing result model
   - `ARExportResult` - Export result model

### ❌ What's Missing

1. **FFI Functions**
   - `arxos_load_ar_model()` - Load/export building model on demand
   - `arxos_save_ar_scan()` - Save AR scan data to file/backend

2. **Model Loading Integration**
   - Dynamic model loading from FFI (currently hardcoded to Bundle.main)
   - Temporary file management for exported models
   - Error handling for model loading failures

3. **Scan Saving Integration**
   - Wire up `saveScan()` in ARScanView to FFI
   - Convert Swift `ARScanData` to JSON
   - Handle scan processing results

4. **Tap-to-Place Equipment**
   - ARKit tap gesture handling
   - Equipment placement at tap locations
   - Visual feedback for placed equipment

5. **Complete Workflow**
   - Scan → Save → Process → Pending → Review → Confirm → Commit

---

## Implementation Plan

### Phase 1: Add Missing FFI Functions (2-3 hours)

#### 1.1 Add `arxos_load_ar_model()` FFI Function

**File:** `crates/arxos/crates/arxos/src/mobile_ffi/ffi.rs`

```rust
/// Load/export building model for AR
///
/// # Arguments
/// * `building_name` - Name of building to export
/// * `format` - Export format: "usdz" or "gltf"
/// * `output_path` - Path where model should be saved (or null for temp)
///
/// Returns JSON with model path and metadata
#[no_mangle]
pub unsafe extern "C" fn arxos_load_ar_model(
    building_name: *const c_char,
    format: *const c_char,
    output_path: *const c_char,
) -> *mut c_char {
    use crate::export::ar::{ARExporter, ARFormat};
    use std::path::Path;
    use tempfile::NamedTempFile;
    
    // Parse inputs
    let building_str = CStr::from_ptr(building_name).to_str()?;
    let format_str = CStr::from_ptr(format).to_str()?;
    
    // Determine output path
    let output = if output_path.is_null() {
        // Create temp file
        let temp_file = NamedTempFile::new()?;
        temp_file.path().to_path_buf()
    } else {
        PathBuf::from(CStr::from_ptr(output_path).to_str()?)
    };
    
    // Load building data
    let building_data = load_building_data(building_str)?;
    
    // Export to AR format
    let ar_format = format_str.parse::<ARFormat>()?;
    let exporter = ARExporter::new(building_data);
    exporter.export(ar_format, &output)?;
    
    // Return result with file path
    let result = ARModelLoadResult {
        success: true,
        building: building_str.to_string(),
        format: format_str.to_string(),
        file_path: output.to_string_lossy().to_string(),
        file_size: std::fs::metadata(&output)?.len(),
    };
    
    create_json_response(Ok(result))
}
```

**Swift Wrapper:** `ArxOSCoreFFI.swift`

```swift
/// Load AR model for building
func loadARModel(
    buildingName: String,
    format: String,
    outputPath: String? = nil,
    completion: @escaping (Result<ARModelLoadResult, Error>) -> Void
) {
    DispatchQueue.global().async {
        // FFI call implementation
        // Handle temp file management
        // Return file path for loading
    }
}
```

#### 1.2 Add `arxos_save_ar_scan()` FFI Function

**File:** `crates/arxos/crates/arxos/src/mobile_ffi/ffi.rs`

```rust
/// Save AR scan data and process to pending equipment
///
/// # Arguments
/// * `json_data` - JSON string of AR scan data
/// * `building_name` - Building name
/// * `confidence_threshold` - Minimum confidence (0.0-1.0)
///
/// Returns JSON with saved scan info and pending equipment IDs
#[no_mangle]
pub unsafe extern "C" fn arxos_save_ar_scan(
    json_data: *const c_char,
    building_name: *const c_char,
    confidence_threshold: f64,
) -> *mut c_char {
    // Parse AR scan data
    let json_str = CStr::from_ptr(json_data).to_str()?;
    let building_str = CStr::from_ptr(building_name).to_str()?;
    
    // Process scan to pending equipment
    let pending_ids = process_ar_scan_to_pending(
        &parse_ar_scan(json_str)?,
        building_str,
        confidence_threshold,
    )?;
    
    // Optionally save raw scan data to file for debugging
    // Save to: {building_name}_scans/{timestamp}.json
    
    // Return result
    let result = ARScanSaveResult {
        success: true,
        building: building_str.to_string(),
        pending_count: pending_ids.len(),
        pending_ids,
        scan_timestamp: Utc::now().to_rfc3339(),
    };
    
    create_json_response(Ok(result))
}
```

**Swift Wrapper:** `ArxOSCoreFFI.swift`

```swift
/// Save AR scan data
func saveARScan(
    scanData: ARScanData,
    buildingName: String,
    confidenceThreshold: Double = 0.7,
    completion: @escaping (Result<ARScanSaveResult, Error>) -> Void
) {
    // Convert ARScanData to JSON
    // Call FFI function
    // Handle result
}
```

---

### Phase 2: Wire Up Model Loading (2-3 hours)

#### 2.1 Update ARViewContainer to Use FFI

**File:** `ios/ArxOSMobile/ArxOSMobile/Views/ARViewContainer.swift`

**Changes:**
1. Replace Bundle.main model loading with FFI call
2. Handle temporary file management
3. Load model from returned file path
4. Add error handling and loading states

```swift
struct ARViewContainer: UIViewRepresentable {
    @Binding var detectedEquipment: [DetectedEquipment]
    @Binding var isScanning: Bool
    var buildingName: String? = nil
    @State private var modelLoadingState: ModelLoadingState = .idle
    
    enum ModelLoadingState {
        case idle
        case loading
        case loaded(String) // File path
        case error(String)
    }
    
    func makeUIView(context: Context) -> ARView {
        let arView = ARView(frame: .zero)
        
        // Configure AR session
        let configuration = ARWorldTrackingConfiguration()
        configuration.planeDetection = [.horizontal, .vertical]
        configuration.environmentTexturing = .automatic
        
        if ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth) {
            configuration.frameSemantics = .sceneDepth
        }
        
        arView.session.run(configuration)
        arView.session.delegate = context.coordinator
        
        // Load model via FFI if building specified
        if let building = buildingName {
            loadModelViaFFI(arView: arView, buildingName: building)
        }
        
        return arView
    }
    
    private func loadModelViaFFI(arView: ARView, buildingName: String) {
        modelLoadingState = .loading
        
        let ffi = ArxOSCoreFFI()
        ffi.loadARModel(
            buildingName: buildingName,
            format: "usdz" // Prefer USDZ for ARKit
        ) { result in
            switch result {
            case .success(let modelResult):
                // Load model from returned file path
                self.loadModelFromPath(arView: arView, filePath: modelResult.filePath)
                self.modelLoadingState = .loaded(modelResult.filePath)
            case .failure(let error):
                print("Failed to load AR model: \(error)")
                self.modelLoadingState = .error(error.localizedDescription)
            }
        }
    }
    
    private func loadModelFromPath(arView: ARView, filePath: String) {
        let url = URL(fileURLWithPath: filePath)
        
        // Create anchor
        let anchor = AnchorEntity(world: simd_float3(x: 0, y: 0, z: 0))
        anchor.name = "building_model"
        
        // Load entity
        Entity.loadAsync(contentsOf: url).sink(
            receiveCompletion: { completion in
                if case .failure(let error) = completion {
                    print("Failed to load model: \(error)")
                }
            },
            receiveValue: { entity in
                anchor.addChild(entity)
                arView.scene.addAnchor(anchor)
                print("✅ Successfully loaded AR model")
            }
        )
    }
}
```

---

### Phase 3: Wire Up Scan Saving (2-3 hours)

#### 3.1 Update ARScanView to Save Scans

**File:** `ios/ArxOSMobile/ArxOSMobile/Views/ARScanView.swift`

**Changes:**
1. Implement `saveScan()` to call FFI
2. Convert detected equipment to ARScanData
3. Handle scan processing results
4. Show pending equipment confirmation UI

```swift
struct ARScanView: View {
    @State private var isScanning = false
    @State private var detectedEquipment: [DetectedEquipment] = []
    @State private var currentRoom = "Room 301"
    @State private var buildingName = "Default Building"
    @State private var showPendingConfirmation = false
    @State private var pendingEquipmentIds: [String] = []
    
    private func saveScan() {
        // Convert detected equipment to ARScanData
        let scanData = ARScanData(
            detectedEquipment: detectedEquipment,
            roomBoundaries: RoomBoundaries(walls: [], openings: []),
            roomName: currentRoom,
            floorLevel: 0 // TODO: Get from building data
        )
        
        // Encode to JSON
        guard let jsonData = try? JSONEncoder().encode(scanData),
              let jsonString = String(data: jsonData, encoding: .utf8) else {
            print("Failed to encode scan data")
            return
        }
        
        // Call FFI to save and process
        let ffi = ArxOSCoreFFI()
        ffi.saveARScan(
            scanData: scanData,
            buildingName: buildingName,
            confidenceThreshold: 0.7
        ) { result in
            switch result {
            case .success(let saveResult):
                print("✅ Scan saved: \(saveResult.pendingCount) pending items")
                DispatchQueue.main.async {
                    self.pendingEquipmentIds = saveResult.pendingIds
                    self.showPendingConfirmation = true
                    self.isScanning = false
                }
            case .failure(let error):
                print("❌ Failed to save scan: \(error)")
            }
        }
    }
    
    // Add sheet for pending equipment confirmation
    .sheet(isPresented: $showPendingConfirmation) {
        PendingEquipmentConfirmationView(
            pendingIds: pendingEquipmentIds,
            buildingName: buildingName
        )
    }
}
```

---

### Phase 4: Implement Tap-to-Place Equipment (3-4 hours)

#### 4.1 Add Tap Gesture Handling

**File:** `ios/ArxOSMobile/ArxOSMobile/Views/ARViewContainer.swift`

```swift
class ARCoordinator: NSObject, ARSessionDelegate {
    var parent: ARViewContainer
    var arView: ARView?
    
    func setupTapGesture(on arView: ARView) {
        let tapGesture = UITapGestureRecognizer(
            target: self,
            action: #selector(handleTap(_:))
        )
        arView.addGestureRecognizer(tapGesture)
        self.arView = arView
    }
    
    @objc func handleTap(_ gesture: UITapGestureRecognizer) {
        guard let arView = arView else { return }
        
        let location = gesture.location(in: arView)
        
        // Perform hit test
        let hitTestResults = arView.raycast(
            from: location,
            allowing: .estimatedPlane,
            alignment: .any
        )
        
        guard let firstResult = hitTestResults.first else { return }
        
        // Create equipment at tap location
        let position = Position3D(
            x: Double(firstResult.worldTransform.columns.3.x),
            y: Double(firstResult.worldTransform.columns.3.y),
            z: Double(firstResult.worldTransform.columns.3.z)
        )
        
        // Show equipment placement UI
        showEquipmentPlacementDialog(at: position)
    }
    
    private func showEquipmentPlacementDialog(at position: Position3D) {
        // Present equipment type selection
        // Create DetectedEquipment with position
        // Add to detectedEquipment array
    }
}
```

---

### Phase 5: Complete Workflow Integration (2-3 hours)

#### 5.1 Create Pending Equipment Review View

**New File:** `ios/ArxOSMobile/ArxOSMobile/Views/PendingEquipmentConfirmationView.swift`

```swift
struct PendingEquipmentConfirmationView: View {
    let pendingIds: [String]
    let buildingName: String
    @State private var pendingEquipment: [PendingEquipment] = []
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationView {
            List {
                ForEach(pendingEquipment) { equipment in
                    PendingEquipmentRow(
                        equipment: equipment,
                        onConfirm: { confirmEquipment(equipment.id) },
                        onReject: { rejectEquipment(equipment.id) }
                    )
                }
            }
            .navigationTitle("Pending Equipment")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
        .onAppear {
            loadPendingEquipment()
        }
    }
    
    private func loadPendingEquipment() {
        // Load pending equipment from FFI
        // Call arxos_list_pending_equipment or similar
    }
    
    private func confirmEquipment(_ id: String) {
        // Call FFI to confirm pending equipment
        // Remove from list
    }
    
    private func rejectEquipment(_ id: String) {
        // Call FFI to reject pending equipment
        // Remove from list
    }
}
```

---

## Testing Plan

### Unit Tests
- [ ] FFI function parameter validation
- [ ] JSON serialization/deserialization
- [ ] Error handling for invalid inputs

### Integration Tests
- [ ] Model export and loading workflow
- [ ] AR scan data processing
- [ ] Pending equipment creation and confirmation

### Manual Testing
- [ ] Load building model in AR
- [ ] Scan room and detect equipment
- [ ] Save scan and verify pending equipment
- [ ] Confirm/reject pending equipment
- [ ] Verify Git commit after confirmation

---

## File Changes Summary

### Rust Files (crates/arxos/crates/arxos/src/mobile_ffi/)
- `ffi.rs` - Add `arxos_load_ar_model()` and `arxos_save_ar_scan()`

### Swift Files (ios/ArxOSMobile/ArxOSMobile/)
- `Services/ArxOSCoreFFI.swift` - Add `loadARModel()` and `saveARScan()` wrappers
- `Views/ARViewContainer.swift` - Wire up FFI model loading
- `Views/ARScanView.swift` - Wire up FFI scan saving
- `Views/PendingEquipmentConfirmationView.swift` - **NEW** - Review pending equipment

### Data Models
- `Models/ArxOSModels.swift` - Add `ARModelLoadResult` and `ARScanSaveResult`

---

## Timeline Estimate

- **Phase 1 (FFI Functions):** 2-3 hours
- **Phase 2 (Model Loading):** 2-3 hours
- **Phase 3 (Scan Saving):** 2-3 hours
- **Phase 4 (Tap-to-Place):** 3-4 hours
- **Phase 5 (Workflow):** 2-3 hours

**Total:** 11-16 hours (~1.5-2 days)

---

## Dependencies

- ✅ ARKit and RealityKit frameworks
- ✅ Existing FFI infrastructure
- ✅ AR export functionality (glTF/USDZ)
- ✅ Pending equipment management system

---

## Success Criteria

1. ✅ Building models load in AR from exported files
2. ✅ AR scans can be saved and processed
3. ✅ Equipment can be placed via tap gestures
4. ✅ Pending equipment workflow complete
5. ✅ Confirmed equipment commits to Git

---

## Risk Mitigation

**Risk:** Model loading performance on mobile devices  
**Mitigation:** Use async loading, cache models, provide loading indicators

**Risk:** ARKit compatibility across iOS versions  
**Mitigation:** Check ARWorldTrackingConfiguration support, provide fallbacks

**Risk:** File path management between Rust and Swift  
**Mitigation:** Use temp files with clear lifecycle management, document paths

---

## Next Steps

1. Start with Phase 1 (FFI functions) - most critical
2. Test model loading on physical device
3. Implement scan saving with validation
4. Add tap-to-place for better UX
5. Complete workflow with pending equipment review

---

**Status:** Ready for implementation  
**Priority:** High - Critical path to 0.1 release  
**Estimated Completion:** 1.5-2 days of focused work


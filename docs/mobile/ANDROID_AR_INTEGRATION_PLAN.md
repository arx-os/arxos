# Android AR Integration Plan

**Date:** November 2025  
**Status:** Planning  
**Priority:** High - Critical Path to 0.1 Release

---

## Overview

Complete Android ARCore integration for ArxOS, enabling users to:
1. **Load building models** in AR (glTF format - Android prefers glTF over USDZ)
2. **Scan rooms** and detect equipment using ARCore
3. **Save scan data** to Rust backend for processing
4. **Review pending equipment** and confirm/reject
5. **Commit confirmed equipment** to Git

---

## Current State Analysis

### ✅ What's Already Implemented

1. **ARCore Infrastructure** ✅
   - `ARViewContainer.kt` - ARCore session setup with GLSurfaceView
   - `ARRenderer` - OpenGL rendering pipeline
   - Plane detection (horizontal & vertical)
   - Camera background rendering
   - Session lifecycle management

2. **Rust Backend** ✅
   - `arxos_load_ar_model()` - Exports building to AR format (glTF/USDZ)
   - `arxos_save_ar_scan()` - Processes and saves AR scan data
   - `arxos_list_pending_equipment()` - Lists pending equipment
   - `arxos_confirm_pending_equipment()` - Confirms pending equipment
   - `arxos_reject_pending_equipment()` - Rejects pending equipment
   - Pending equipment management system
   - AR scan processing pipeline

3. **JNI Bindings (Partial)** ✅
   - `nativeListRooms()` - List rooms
   - `nativeGetRoom()` - Get specific room
   - `nativeListEquipment()` - List equipment
   - `nativeGetEquipment()` - Get specific equipment
   - `nativeParseARScan()` - Parse AR scan JSON
   - `nativeExtractEquipment()` - Extract equipment from scan
   - `nativeExportForAR()` - Export building to AR format

4. **Kotlin Service Layer** ✅
   - `ArxOSCoreJNI.kt` - JNI wrapper class
   - `ArxOSCoreJNIWrapper.kt` - High-level wrapper with error handling
   - `ArxOSCoreService.kt` - Service layer with coroutines

5. **Data Models** ✅
   - `DetectedEquipment` - Equipment detection model
   - `ARScanData` - AR scan data structure
   - `Vector3` - 3D position vector

### ❌ What's Missing

1. **JNI Functions for New AR Integration**
   - `nativeLoadARModel()` - Load/export building model on demand
   - `nativeSaveARScan()` - Save AR scan data to backend
   - `nativeListPendingEquipment()` - List pending equipment
   - `nativeConfirmPendingEquipment()` - Confirm pending equipment
   - `nativeRejectPendingEquipment()` - Reject pending equipment

2. **Model Loading Integration**
   - Dynamic glTF model loading from FFI (currently no model loading)
   - Temporary file management for exported models
   - Error handling for model loading failures
   - Integration with Sceneform or native glTF loader

3. **Scan Saving Integration**
   - Wire up `saveARScan()` in ARScreen to JNI
   - Convert Kotlin `ARScanData` to JSON
   - Handle scan processing results
   - Show pending equipment confirmation UI

4. **Tap-to-Place Equipment**
   - ARCore tap gesture handling
   - Equipment placement at tap locations (HitResult)
   - Visual feedback for placed equipment (Anchor + Entity)
   - Integration with ARCore Sceneform or native rendering

5. **Complete Workflow**
   - Scan → Save → Process → Pending → Review → Confirm → Commit

---

## Implementation Plan

### Phase 1: Add Missing JNI Functions (2-3 hours)

#### 1.1 Add JNI Functions in Rust

**File:** `crates/arxos/crates/arxos/src/mobile_ffi/jni.rs`

Add these JNI functions mirroring the C FFI functions:

```rust
/// Load/export building model for AR - JNI implementation
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeLoadARModel(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString,
    format: JString,
    output_path: JString
) -> jstring {
    // Extract parameters
    // Call arxos_load_ar_model equivalent logic
    // Return JSON with file path
}

/// Save AR scan data - JNI implementation
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeSaveARScan(
    mut env: JNIEnv,
    _class: JClass,
    json_data: JString,
    building_name: JString,
    confidence_threshold: jdouble
) -> jstring {
    // Extract parameters
    // Call arxos_save_ar_scan equivalent logic
    // Return JSON with pending IDs
}

/// List pending equipment - JNI implementation
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeListPendingEquipment(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString
) -> jstring {
    // Call arxos_list_pending_equipment equivalent logic
    // Return JSON with pending items
}

/// Confirm pending equipment - JNI implementation
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeConfirmPendingEquipment(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString,
    pending_id: JString,
    commit_to_git: jboolean
) -> jstring {
    // Call arxos_confirm_pending_equipment equivalent logic
    // Return JSON with equipment ID
}

/// Reject pending equipment - JNI implementation
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeRejectPendingEquipment(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString,
    pending_id: JString
) -> jstring {
    // Call arxos_reject_pending_equipment equivalent logic
    // Return JSON with success status
}
```

**Key Considerations:**
- Use `java_string_to_rust()` helper for string extraction
- Use `rust_string_to_java()` helper for string return
- Handle JNI exceptions properly
- Return JSON responses matching iOS FFI format

#### 1.2 Add Kotlin Declarations

**File:** `android/app/src/main/java/com/arxos/mobile/service/ArxOSCoreJNI.kt`

```kotlin
/**
 * Load/export building model for AR viewing
 */
external fun nativeLoadARModel(
    buildingName: String,
    format: String,
    outputPath: String?
): String

/**
 * Save AR scan data and process to pending equipment
 */
external fun nativeSaveARScan(
    jsonData: String,
    buildingName: String,
    confidenceThreshold: Double
): String

/**
 * List all pending equipment for a building
 */
external fun nativeListPendingEquipment(buildingName: String): String

/**
 * Confirm a pending equipment item
 */
external fun nativeConfirmPendingEquipment(
    buildingName: String,
    pendingId: String,
    commitToGit: Boolean
): String

/**
 * Reject a pending equipment item
 */
external fun nativeRejectPendingEquipment(
    buildingName: String,
    pendingId: String
): String
```

#### 1.3 Add Wrapper Methods

**File:** `android/app/src/main/java/com/arxos/mobile/service/ArxOSCoreJNIWrapper.kt`

Add wrapper methods with error handling and JSON parsing:

```kotlin
suspend fun loadARModel(
    buildingName: String,
    format: String = "gltf",
    outputPath: String? = null
): ARModelLoadResult {
    // Call nativeLoadARModel
    // Parse JSON response
    // Return typed result
}

suspend fun saveARScan(
    scanData: ARScanData,
    buildingName: String,
    confidenceThreshold: Double = 0.7
): ARScanSaveResult {
    // Serialize scanData to JSON
    // Call nativeSaveARScan
    // Parse JSON response
    // Return typed result
}

suspend fun listPendingEquipment(buildingName: String): PendingEquipmentListResult {
    // Call nativeListPendingEquipment
    // Parse JSON response
    // Return typed result
}

suspend fun confirmPendingEquipment(
    buildingName: String,
    pendingId: String,
    commitToGit: Boolean = true
): PendingEquipmentConfirmResult {
    // Call nativeConfirmPendingEquipment
    // Parse JSON response
    // Return typed result
}

suspend fun rejectPendingEquipment(
    buildingName: String,
    pendingId: String
): PendingEquipmentRejectResult {
    // Call nativeRejectPendingEquipment
    // Parse JSON response
    // Return typed result
}
```

**Time Estimate:** 2-3 hours

---

### Phase 2: Model Loading Integration (3-4 hours)

#### 2.1 Update ARViewContainer for Model Loading

**File:** `android/app/src/main/java/com/arxos/mobile/ui/components/ARViewContainer.kt`

Add model loading capability:

```kotlin
@Composable
fun ARViewContainer(
    modifier: Modifier = Modifier,
    onEquipmentDetected: (DetectedEquipment) -> Unit,
    isScanning: Boolean,
    loadedModel: String? = null, // Building name to load model for
    onEquipmentPlaced: ((DetectedEquipment) -> Unit)? = null
) {
    val context = LocalContext.current
    val viewModel = remember { ARViewModel(context) }
    
    // Load model when building name changes
    LaunchedEffect(loadedModel) {
        loadedModel?.let { buildingName ->
            viewModel.loadARModel(buildingName, "gltf")
        }
    }
    
    AndroidView(
        factory = { ctx ->
            createARView(ctx, onEquipmentDetected, viewModel, onEquipmentPlaced)
        },
        modifier = modifier.fillMaxSize(),
        update = { view ->
            // Handle model loading state
            viewModel.modelPath?.let { path ->
                loadModelIntoARView(view, path)
            }
        }
    )
}
```

#### 2.2 Add glTF Model Loading

**Options:**
1. **Sceneform (Recommended for simplicity)**
   - Use Sceneform's glTF loader
   - Easy integration with ARCore
   - Deprecated but still functional

2. **Native glTF Loader**
   - Use `gltf` crate or manual parsing
   - More control but more complex
   - Better for future customizations

3. **babylon.js Android (Alternative)**
   - Full-featured 3D engine
   - Overkill for current needs

**Recommended Approach:**
- Start with Sceneform for MVP
- Plan migration to native loader if needed

**Implementation:**
- Load glTF file from temp directory
- Parse glTF structure
- Create ARCore Anchor at building origin
- Render model as ARCore Entity
- Handle model scaling and positioning

#### 2.3 Update ARViewModel

**File:** `android/app/src/main/java/com/arxos/mobile/ui/viewmodel/ARViewModel.kt`

```kotlin
class ARViewModel(context: Context) : AndroidViewModel(context.applicationContext as Application) {
    private val service = ArxOSCoreServiceFactory.getInstance(context)
    
    var modelPath by mutableStateOf<String?>(null)
        private set
    
    var isLoadingModel by mutableStateOf(false)
        private set
    
    var modelLoadError by mutableStateOf<String?>(null)
        private set
    
    suspend fun loadARModel(buildingName: String, format: String = "gltf") {
        isLoadingModel = true
        modelLoadError = null
        
        try {
            val result = service.loadARModel(buildingName, format)
            if (result.success) {
                modelPath = result.filePath
            } else {
                modelLoadError = result.error ?: "Failed to load model"
            }
        } catch (e: Exception) {
            modelLoadError = e.message
        } finally {
            isLoadingModel = false
        }
    }
}
```

**Time Estimate:** 3-4 hours

---

### Phase 3: Scan Saving Integration (2-3 hours)

#### 3.1 Update ARScreen for Scan Saving

**File:** `android/app/src/main/java/com/arxos/mobile/ui/screens/ARScreen.kt`

Replace placeholder `saveARScan()` with real implementation:

```kotlin
@Composable
fun ARScreen() {
    val viewModel: ARViewModel = viewModel()
    var isSavingScan by remember { mutableStateOf(false) }
    var showSaveSuccess by remember { mutableStateOf(false) }
    var saveErrorMessage by remember { mutableStateOf<String?>(null) }
    var pendingEquipmentIds by remember { mutableStateOf<List<String>>(emptyList()) }
    var showPendingConfirmation by remember { mutableStateOf(false) }
    
    // Save scan function
    fun saveScan() {
        isSavingScan = true
        saveErrorMessage = null
        
        viewModelScope.launch {
            try {
                val scanData = ARScanData(
                    detectedEquipment = detectedEquipment.map { eq ->
                        DetectedEquipmentData(
                            name = eq.name,
                            type = eq.type,
                            position = Point3D(eq.position.x.toDouble(), eq.position.y.toDouble(), eq.position.z.toDouble()),
                            confidence = 0.9, // Default confidence
                            detectionMethod = "ARCore"
                        )
                    },
                    roomBoundaries = RoomBoundaries(emptyList(), emptyList()),
                    roomName = currentRoom,
                    floorLevel = floorLevel
                )
                
                val result = viewModel.saveARScan(scanData, buildingName, 0.7)
                
                if (result.success) {
                    pendingEquipmentIds = result.pendingIds
                    if (pendingEquipmentIds.isNotEmpty()) {
                        showPendingConfirmation = true
                    } else {
                        showSaveSuccess = true
                    }
                } else {
                    saveErrorMessage = result.error
                }
            } catch (e: Exception) {
                saveErrorMessage = e.message
            } finally {
                isSavingScan = false
            }
        }
    }
    
    // Show pending confirmation dialog
    if (showPendingConfirmation && pendingEquipmentIds.isNotEmpty()) {
        PendingEquipmentConfirmationDialog(
            pendingIds = pendingEquipmentIds,
            buildingName = buildingName,
            onDismiss = { showPendingConfirmation = false },
            onConfirm = { id -> /* Handle confirm */ },
            onReject = { id -> /* Handle reject */ }
        )
    }
}
```

#### 3.2 Add Scan Duration Tracking

```kotlin
var scanStartTime by remember { mutableStateOf<Long?>(null) }

fun startScanning() {
    isScanning = true
    scanStartTime = System.currentTimeMillis()
}

fun stopScanning() {
    isScanning = false
    val duration = scanStartTime?.let { System.currentTimeMillis() - it }
    // Include duration in scan data
}
```

#### 3.3 Add Floor Level Input

```kotlin
var floorLevel by remember { mutableStateOf(0) }

// In UI
OutlinedTextField(
    value = floorLevel.toString(),
    onValueChange = { floorLevel = it.toIntOrNull() ?: 0 },
    label = { Text("Floor Level") },
    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
)
```

**Time Estimate:** 2-3 hours

---

### Phase 4: Tap-to-Place Equipment (3-4 hours)

#### 4.1 Add Tap Gesture Handling

**File:** `android/app/src/main/java/com/arxos/mobile/ui/components/ARViewContainer.kt`

Add tap gesture detection to GLSurfaceView:

```kotlin
private fun createARView(
    context: Context,
    onEquipmentDetected: (DetectedEquipment) -> Unit,
    viewModel: ARViewModel,
    onEquipmentPlaced: ((DetectedEquipment) -> Unit)?
): GLSurfaceView {
    val glSurfaceView = GLSurfaceView(context).apply {
        setEGLContextClientVersion(2)
        preserveEGLContextOnPause = true
        setRenderer(ARRenderer(context, onEquipmentDetected, onEquipmentPlaced))
        
        // Add tap gesture listener
        setOnTouchListener { _, event ->
            if (event.action == MotionEvent.ACTION_DOWN) {
                val x = event.x
                val y = event.y
                handleTap(x, y, onEquipmentPlaced)
                true
            } else {
                false
            }
        }
    }
    
    return glSurfaceView
}

private fun handleTap(
    x: Float,
    y: Float,
    onEquipmentPlaced: ((DetectedEquipment) -> Unit)?
) {
    // Get ARCore frame
    val frame = session?.update()
    if (frame == null) return
    
    // Perform hit test
    val hits = frame.hitTest(x, y)
    
    // Filter hits by plane type
    val planeHits = hits.filter { hit ->
        hit.trackable is Plane && hit.trackable.trackingState == TrackingState.TRACKING
    }
    
    // Use first valid hit
    planeHits.firstOrNull()?.let { hit ->
        val pose = hit.hitPose
        val translation = FloatArray(3)
        pose.getTranslation(translation, 0)
        
        // Show equipment placement dialog
        showEquipmentPlacementDialog(
            position = Vector3(translation[0], translation[1], translation[2]),
            onConfirm = { name, type ->
                val equipment = DetectedEquipment(
                    id = UUID.randomUUID().toString(),
                    name = name,
                    type = type,
                    position = Vector3(translation[0], translation[1], translation[2]),
                    status = "Placed",
                    icon = getIconForType(type)
                )
                onEquipmentPlaced?.invoke(equipment)
                
                // Add visual marker at tap location
                addPlacementMarker(pose, equipment)
            }
        )
    }
}
```

#### 4.2 Add Visual Markers

```kotlin
private fun addPlacementMarker(pose: Pose, equipment: DetectedEquipment) {
    // Create ARCore Anchor at tap location
    val anchor = session?.createAnchor(pose)
    
    // Create visual entity (simplified - would use Sceneform or custom rendering)
    // For now, add to detected equipment list for UI display
    onEquipmentDetected(equipment)
}
```

#### 4.3 Equipment Placement Dialog

**File:** `android/app/src/main/java/com/arxos/mobile/ui/components/EquipmentPlacementDialog.kt`

```kotlin
@Composable
fun EquipmentPlacementDialog(
    position: Vector3,
    onConfirm: (String, String) -> Unit,
    onCancel: () -> Unit
) {
    var equipmentName by remember { mutableStateOf("") }
    var equipmentType by remember { mutableStateOf("Unknown") }
    
    val equipmentTypes = listOf("Unknown", "HVAC", "Electrical", "Plumbing", "Lighting", "Safety", "Other")
    
    AlertDialog(
        onDismissRequest = onCancel,
        title = { Text("Place Equipment") },
        text = {
            Column {
                OutlinedTextField(
                    value = equipmentName,
                    onValueChange = { equipmentName = it },
                    label = { Text("Equipment Name") }
                )
                Spacer(Modifier.height(16.dp))
                DropdownMenu(
                    expanded = false, // Simplified
                    onDismissRequest = {}
                ) {
                    // Equipment type selector
                }
            }
        },
        confirmButton = {
            Button(onClick = { onConfirm(equipmentName, equipmentType) }) {
                Text("Place")
            }
        },
        dismissButton = {
            TextButton(onClick = onCancel) {
                Text("Cancel")
            }
        }
    )
}
```

**Time Estimate:** 3-4 hours

---

### Phase 5: Complete Workflow Integration (2-3 hours)

#### 5.1 Pending Equipment Confirmation UI

**File:** `android/app/src/main/java/com/arxos/mobile/ui/components/PendingEquipmentConfirmationDialog.kt`

```kotlin
@Composable
fun PendingEquipmentConfirmationDialog(
    pendingIds: List<String>,
    buildingName: String,
    onDismiss: () -> Unit,
    onConfirm: (String) -> Unit,
    onReject: (String) -> Unit
) {
    val viewModel: ARViewModel = viewModel()
    var pendingEquipment by remember { mutableStateOf<List<PendingEquipmentItem>>(emptyList()) }
    var isLoading by remember { mutableStateOf(false) }
    
    LaunchedEffect(pendingIds) {
        isLoading = true
        pendingEquipment = viewModel.listPendingEquipment(buildingName)
        isLoading = false
    }
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Review Pending Equipment") },
        text = {
            if (isLoading) {
                CircularProgressIndicator()
            } else {
                LazyColumn {
                    items(pendingEquipment) { item ->
                        PendingEquipmentRow(
                            item = item,
                            onConfirm = { onConfirm(item.id) },
                            onReject = { onReject(item.id) }
                        )
                    }
                }
            }
        },
        confirmButton = {
            Button(onClick = onDismiss) {
                Text("Done")
            }
        }
    )
}
```

#### 5.2 Confirm/Reject Workflow

```kotlin
fun confirmEquipment(pendingId: String) {
    viewModelScope.launch {
        val result = viewModel.confirmPendingEquipment(buildingName, pendingId, commitToGit = true)
        if (result.success) {
            // Show success message
            // Remove from pending list
        }
    }
}

fun rejectEquipment(pendingId: String) {
    viewModelScope.launch {
        val result = viewModel.rejectPendingEquipment(buildingName, pendingId)
        if (result.success) {
            // Remove from pending list
        }
    }
}
```

#### 5.3 Update ARViewModel

```kotlin
suspend fun saveARScan(
    scanData: ARScanData,
    buildingName: String,
    confidenceThreshold: Double = 0.7
): ARScanSaveResult {
    val wrapper = ArxOSCoreJNIWrapper(jni)
    return wrapper.saveARScan(scanData, buildingName, confidenceThreshold)
}

suspend fun listPendingEquipment(buildingName: String): List<PendingEquipmentItem> {
    val wrapper = ArxOSCoreJNIWrapper(jni)
    return wrapper.listPendingEquipment(buildingName).items
}

suspend fun confirmPendingEquipment(
    buildingName: String,
    pendingId: String,
    commitToGit: Boolean = true
): PendingEquipmentConfirmResult {
    val wrapper = ArxOSCoreJNIWrapper(jni)
    return wrapper.confirmPendingEquipment(buildingName, pendingId, commitToGit)
}

suspend fun rejectPendingEquipment(
    buildingName: String,
    pendingId: String
): PendingEquipmentRejectResult {
    val wrapper = ArxOSCoreJNIWrapper(jni)
    return wrapper.rejectPendingEquipment(buildingName, pendingId)
}
```

**Time Estimate:** 2-3 hours

---

## Differences from iOS Implementation

### Platform Differences

| Aspect | iOS | Android |
|--------|-----|---------|
| **AR Framework** | ARKit | ARCore |
| **View System** | ARView (Metal) | GLSurfaceView (OpenGL ES) |
| **3D Format** | USDZ (preferred) | glTF (preferred) |
| **FFI** | C FFI | JNI |
| **Language** | Swift | Kotlin |
| **UI Framework** | SwiftUI | Jetpack Compose |
| **Rendering** | Metal | OpenGL ES 2.0 |
| **Model Loading** | RealityKit | Sceneform/Native |

### Key Implementation Differences

1. **JNI vs C FFI**
   - JNI requires Java string conversion helpers
   - JNI exceptions vs C error codes
   - Different function naming conventions

2. **glTF vs USDZ**
   - Android prefers glTF (more universal)
   - iOS can use both but prefers USDZ
   - Different loading libraries needed

3. **ARCore vs ARKit**
   - ARCore uses HitResult for tap detection
   - ARKit uses ARHitTestResult
   - Different anchor creation APIs
   - Different plane detection callbacks

4. **Compose vs SwiftUI**
   - Different state management
   - Different lifecycle handling
   - Different composable patterns

---

## Testing Strategy

### Unit Tests
- JNI function tests (Rust side)
- Kotlin wrapper tests
- ViewModel tests

### Integration Tests
- End-to-end AR workflow
- Model loading tests
- Scan saving tests
- Pending equipment workflow

### Device Tests
- ARCore functionality (requires physical device)
- glTF model rendering
- Tap-to-place accuracy
- Performance testing

---

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: JNI Functions | 2-3 hours | Rust backend complete |
| Phase 2: Model Loading | 3-4 hours | Phase 1 |
| Phase 3: Scan Saving | 2-3 hours | Phase 1 |
| Phase 4: Tap-to-Place | 3-4 hours | Phase 2 |
| Phase 5: Complete Workflow | 2-3 hours | Phases 1-4 |

**Total Estimated Time:** 12-17 hours

---

## Success Criteria

✅ All 5 new JNI functions implemented and tested  
✅ glTF models load and display in ARCore  
✅ AR scans save and process to pending equipment  
✅ Tap-to-place equipment works with visual feedback  
✅ Complete workflow: Scan → Save → Review → Confirm → Commit  
✅ Parity with iOS implementation (adjusted for platform differences)  
✅ Comprehensive test coverage  

---

## Next Steps

1. Review and approve plan
2. Start Phase 1: JNI Functions
3. Test each phase before proceeding
4. Document any deviations from plan
5. Create integration tests for complete workflow

---

**Status:** Ready for Implementation  
**Last Updated:** November 2025


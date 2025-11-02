# AR Integration Loop Roadmap

## Current State ✅

```
iPhone/iPad LiDAR Scan
    ↓
3D Scanner App → scan directory
    ↓
convert_3d_scanner_scan.rs
    ↓
YAML (building.yaml)
    ↓
ASCII art in terminal ✅
    ↓
CLI commands (arxos import, search, room, etc.) ✅
    ↓
YAML (updated building.yaml) ✅
    ↓
Git version control ✅
```

**Status**: Terminal rendering and data management are working correctly!

## The Missing Loop: Back to AR

Currently, the loop closes at Git. To complete the cycle back to AR visualization, we need:

```
YAML (building.yaml) ✅
    ↓
❌ **MISSING**: Export to AR format
    ↓
AR SDK (iOS ARKit / Android ARCore)
    ↓
iOS/Android App renders in AR
```

## Required Work Items

### 1. Export to AR Format 🔴 **HIGH PRIORITY**

**Status**: Not started  
**Priority**: High  
**Estimated Effort**: 2-3 weeks

**Tasks**:
- [ ] Create export format for AR SDKs
  - Option A: Export to USDZ (Universal Scene Description Zip) - Apple's preferred format
  - Option B: Export to glTF 2.0 - Standard 3D format supported by most AR frameworks
  - Option C: Export to proprietary JSON format with spatial anchors
- [ ] Implement coordinate system mapping
  - Convert from ArxOS world/local coordinate systems to AR native coordinates
  - Handle coordinate system transformations
  - Preserve spatial relationships
- [ ] Add material/texture information
  - Export wall materials, floor types, equipment appearances
  - Include metadata for AR occlusion, shadows, lighting
- [ ] Create `src/export/` module
  - `src/export/ar/mod.rs` - Main export module
  - `src/export/ar/usdz.rs` - USDZ export implementation
  - `src/export/ar/gltf.rs` - glTF export implementation
  - `src/export/ar/anchor.rs` - Spatial anchor handling

**Command**:
```bash
arxos export --building "Scan Name" --format usdz --output scan_ar.usdz
arxos export --building "Scan Name" --format gltf --output scan_ar.gltf
```

**Technical Considerations**:
- USDZ: Best for iOS/ARKit, single file distribution, custom shaders
- glTF: Universal, open standard, good browser support, requires additional files
- Spatial anchors: ARKit's anchor system, ARCore's Cloud Anchors

**Files to create**:
- `src/export/mod.rs`
- `src/export/ar/mod.rs`
- `src/export/ar/usdz.rs`
- `src/export/ar/gltf.rs`
- `src/export/ar/anchor.rs`
- `src/commands/export.rs` (update if exists)

---

### 2. AR Anchor Management 🟡 **MEDIUM PRIORITY**

**Status**: Not started  
**Priority**: Medium  
**Estimated Effort**: 1-2 weeks

**Tasks**:
- [ ] Implement spatial anchor tracking
  - Store and manage ARKit/ARCore anchor identifiers
  - Track anchor persistence across sessions
  - Handle anchor relocalization
- [ ] Create anchor synchronization
  - Sync anchors between devices
  - Handle multi-user AR experiences
  - Implement conflict resolution
- [ ] Add anchor metadata storage
  - Store anchor positions in YAML
  - Track anchor relationships
  - Export anchor data with building data

**Use Cases**:
- Place virtual furniture at saved locations
- Restore previous AR session state
- Multi-user collaborative AR editing

**Files to create**:
- `src/ar_anchor/mod.rs`
- `src/ar_anchor/storage.rs`
- `src/ar_anchor/sync.rs`

---

### 3. Mobile App Integration 🟢 **FUTURE**

**Status**: Architecture planned, not implemented  
**Priority**: Future  
**Estimated Effort**: 4-6 weeks

**Tasks**:
- [ ] Create iOS Swift app
  - ARKit integration
  - USDZ file loading
  - Spatial anchor management
  - FFI bridge to ArxOS Core
- [ ] Create Android Kotlin app
  - ARCore integration
  - glTF file loading
  - Cloud Anchor support
  - JNI bridge to ArxOS Core
- [ ] Implement real-time synchronization
  - WebSocket/WebRTC for live updates
  - Delta sync for efficiency
  - Conflict resolution strategies
- [ ] Add mobile-specific features
  - Touch-based editing
  - Gesture recognition
  - Voice commands
  - Hand tracking (when available)

**Architecture**:
```
iOS App (Swift)          Android App (Kotlin)
       ↓                           ↓
ArxOS FFI Bridge           ArxOS JNI Bridge
       ↓                           ↓
       └──────────┬────────────────┘
                  ↓
        ArxOS Core (Rust)
                  ↓
         YAML + Git Storage
```

**Files to create**:
- `ios/ArxOSMobile/` - iOS app (exists, needs AR features)
- `android/app/src/main/java/com/arxos/` - Android app
- `src/mobile_ffi/ar_ops.rs` - AR-specific FFI operations

---

### 4. Real-Time Collaboration 🟢 **FUTURE**

**Status**: Research phase  
**Priority**: Future  
**Estimated Effort**: 3-4 weeks

**Tasks**:
- [ ] Implement multi-user support
  - WebSocket server for real-time sync
  - User presence indicators
  - Conflict resolution
  - Permission management
- [ ] Add live editing features
  - Real-time position updates
  - Cursor/tool indicators
  - Change notifications
  - Undo/redo in collaborative mode
- [ ] Security and privacy
  - Authentication/authorization
  - Room-based access control
  - Encrypted data transmission

**Files to create**:
- `src/server/mod.rs` - WebSocket server
- `src/server/sync.rs` - Synchronization logic
- `src/server/auth.rs` - Authentication

---

## Recommended Implementation Order

1. **USDZ Export** (2-3 weeks)
   - Closes the immediate loop
   - Works with existing iOS infrastructure
   - Enables AR visualization testing

2. **glTF Export** (1 week)
   - Universal format support
   - Enables Android testing
   - Good for web-based AR

3. **AR Anchor Management** (1-2 weeks)
   - Makes AR sessions persistent
   - Enables more advanced use cases
   - Critical for production

4. **Mobile App Integration** (4-6 weeks)
   - Full-featured AR experience
   - Real-time collaboration
   - Production-ready apps

5. **Real-Time Collaboration** (3-4 weeks)
   - Multi-user features
   - Enterprise features
   - Advanced use cases

---

## Technical Dependencies

### External Libraries (Rust)

```toml
[dependencies]
# USD/USDZ support
# Note: No stable Rust crates exist yet
# May need to bind to USD C++ API via FFI

# glTF support
gltf = "0.17"           # glTF loader/writer
nalgebra = "0.32"       # Linear algebra (already added)
serde = { version = "1.0", features = ["derive"] }  # JSON (already added)

# FFI/Serialization (already added)
uniffi = "0.25"         # Cross-platform FFI
serde_json = "1.0"      # JSON
serde_yaml = "0.9"      # YAML
```

### Platform-Specific Requirements

**iOS (ARKit)**:
- iOS 12.0+
- ARWorldTrackingConfiguration
- RealityKit or SceneKit for rendering

**Android (ARCore)**:
- Android 7.0+ (API 24+)
- ARCore SDK
- Sceneform or OpenGL for rendering

**Web**:
- WebXR API
- Three.js or Babylon.js for rendering
- glTF 2.0 format

---

## Testing Strategy

### Unit Tests
- [ ] Test coordinate system transformations
- [ ] Test USDZ file generation
- [ ] Test glTF file generation
- [ ] Test spatial anchor serialization

### Integration Tests
- [ ] Test full export workflow (YAML → AR format)
- [ ] Test file loading in AR apps
- [ ] Test round-trip conversion (AR → YAML → AR)

### Manual Testing
- [ ] Load exported USDZ in iOS Reality Composer
- [ ] Load exported glTF in online viewers
- [ ] Test AR visualization in physical spaces
- [ ] Verify spatial alignment accuracy

---

## Success Criteria

✅ **Minimum Viable Loop**:
- Can export YAML to AR format
- Can load AR file in mobile app
- Spatial alignment is accurate (±10cm)

✅ **Production Ready**:
- Supports both USDZ and glTF
- AR anchors work consistently
- Round-trip conversion preserves data
- Multi-user collaboration works
- Production apps available

---

## Known Challenges

1. **USDZ Complexity**: Apple's USDZ is a complex format. May need FFI to USD C++ library.

2. **Spatial Alignment**: Matching virtual objects to real-world locations requires careful calibration.

3. **Platform Differences**: ARKit and ARCore have different APIs and capabilities.

4. **Real-time Sync**: Multi-user collaboration requires robust networking and conflict resolution.

5. **Storage**: AR files can be large. Need efficient caching and delta sync strategies.

---

## References

- [USD Documentation](https://graphics.pixar.com/usd/docs/index.html)
- [glTF Specification](https://www.khronos.org/gltf/)
- [ARKit Documentation](https://developer.apple.com/documentation/arkit)
- [ARCore Documentation](https://developers.google.com/ar)
- [WebXR API](https://www.w3.org/TR/webxr/)

---

## Notes

- Terminal rendering is working correctly! ✅
- Scan quality (removing furniture) improves accuracy ✅
- Current focus is on 2D floor plans ✅
- AR loop can be implemented incrementally
- Each phase builds on the previous

**Last Updated**: December 2024  
**Status**: Active planning phase


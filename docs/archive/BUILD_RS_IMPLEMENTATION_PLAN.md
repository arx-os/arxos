# Build.rs Implementation Plan

**Date:** January 2025  
**Status:** Phase 1 Complete ✅  
**Priority:** Medium

---

## Implementation Status

### ✅ Phase 1: Foundation - COMPLETE

**Implemented:**
- ✅ Platform detection (IOS, Android, MacOS, Linux, Windows, Unknown)
- ✅ FFI header validation (warning only, non-breaking)
- ✅ Build script rerun triggers (build.rs, Cargo.toml, header)
- ✅ Conservative approach (no linker config yet)

**Files Modified:**
- `build.rs` - Complete rewrite with platform detection and validation

**Testing:**
- ✅ macOS desktop build works
- ✅ Header validation works (warns when missing)
- ✅ Build script reruns when dependencies change
- ⚠️ iOS/Android builds need proper SDK setup (handled by build scripts)

---

## Discussion: Approach & Trade-offs

### Current Situation Analysis

**What works:**
- ✅ Basic builds work without build.rs functionality
- ✅ Manual mobile build scripts handle platform-specific logic
- ✅ FFI headers are manually maintained and working

**What's missing:**
- ❌ No automated platform detection in build.rs
- ❌ No linker configuration automation
- ❌ No validation of FFI header/implementation sync
- ❌ No build-time feature validation
- ❌ No version info injection

### Key Questions to Resolve

#### 1. **How critical is automated linker configuration?**

**Current State:** Build scripts manually handle this:
- iOS builds via `scripts/build-mobile-ios.sh`
- Android builds via `scripts/build-android-mac.sh`
- Desktop builds work without special configuration

**Considerations:**
- ✅ **Pro:** Automated linker config would catch issues earlier
- ✅ **Pro:** Consistent configuration across all builds
- ⚠️ **Con:** May conflict with existing build scripts
- ⚠️ **Con:** Some libraries already link correctly (git2 with vendored-openssl)

**Decision:** **Medium Priority** - Implement but make it optional/non-breaking

---

#### 2. **Should we validate FFI headers or auto-generate them?**

**Option A: Validation Only (Low Risk)**
- ✅ Check header exists
- ✅ Warn on changes
- ❌ Still requires manual maintenance
- ⚠️ Can have header/implementation drift

**Option B: Auto-generation with cbindgen (Higher Risk, Better Long-term)**
- ✅ Single source of truth (Rust code)
- ✅ No manual header maintenance
- ✅ Prevents drift automatically
- ⚠️ Requires cbindgen tool in CI/CD
- ⚠️ More complex setup
- ⚠️ May need header customization

**Decision:** **Start with Option A, migrate to Option B in Phase 3**

**Rationale:** 
- Lower risk for immediate implementation
- Allows validation without breaking existing workflow
- Can add auto-generation later without removing validation

---

#### 3. **How strict should feature validation be?**

**Option A: Warnings Only**
- ✅ Non-breaking
- ✅ Helps developers without blocking builds
- ⚠️ Easy to ignore

**Option B: Errors for Critical Cases**
- ✅ Prevents incorrect builds
- ⚠️ Can be annoying during development
- ⚠️ May need escape hatches

**Decision:** **Option A (Warnings) with option to promote to errors**

---

#### 4. **Build info injection: essential or nice-to-have?**

**Current State:** Version available via `env!("CARGO_PKG_VERSION")` in code

**Considerations:**
- ✅ Useful for debugging/telemetry
- ✅ Can help with support issues
- ⚠️ Build time adds dependency (chrono in build-deps)
- ⚠️ May not be used anywhere yet

**Decision:** **Nice-to-have, Phase 2** - Only add if there's a use case

---

## Implementation Strategy

### Phase 1: Foundation (Low Risk, High Value)

**Goal:** Add essential functionality without breaking existing builds

**Tasks:**
1. ✅ Platform detection
2. ✅ Basic linker configuration (iOS Foundation framework)
3. ✅ FFI header existence validation (warning only)
4. ✅ Build script rerun triggers

**Risk Level:** 🟢 **Low** - All additions are additive

**Testing:**
- Test on macOS (desktop)
- Test iOS build (simulator)
- Test Android build
- Verify desktop builds still work

**Estimated Effort:** 1-2 hours

---

### Phase 2: Enhanced Validation (Medium Priority)

**Goal:** Add helpful warnings and feature validation

**Tasks:**
1. ✅ Android feature flag validation (warning)
2. ✅ Build info injection (if needed)
3. ✅ More comprehensive header validation

**Risk Level:** 🟡 **Low-Medium** - Warnings should be safe

**Dependencies:** Phase 1 complete

**Estimated Effort:** 1 hour

---

### Phase 3: Header Auto-generation (Higher Risk, Future)

**Goal:** Eliminate manual header maintenance

**Tasks:**
1. Evaluate cbindgen vs manual approach
2. Set up cbindgen configuration
3. Implement auto-generation in build.rs
4. Update CI/CD
5. Remove manual header (or keep as fallback)

**Risk Level:** 🟡 **Medium** - Breaking change if not done carefully

**Dependencies:** 
- Phases 1 & 2 stable
- CI/CD infrastructure ready
- Team buy-in on approach

**Estimated Effort:** 4-6 hours

---

## Detailed Implementation Plan

### Phase 1: Foundation Implementation

#### Step 1.1: Update Cargo.toml

**File:** `Cargo.toml`

**Changes:**
```toml
[build-dependencies]
# Note: Only add if we need build-time date/time
# chrono = { version = "0.4", features = ["clock"] }
```

**Decision:** Skip chrono for Phase 1 (no build info injection yet)

---

#### Step 1.2: Implement Platform Detection

**File:** `build.rs`

**Implementation:**
```rust
#[derive(Debug, Clone, Copy)]
enum Platform {
    IOS,
    Android,
    MacOS,
    Linux,
    Windows,
    Unknown,
}

fn detect_platform() -> Platform {
    let target = env::var("TARGET").unwrap();
    
    if target.contains("apple-ios") {
        Platform::IOS
    } else if target.contains("android") {
        Platform::Android
    } else if target.contains("apple-darwin") {
        Platform::MacOS
    } else if target.contains("linux") {
        Platform::Linux
    } else if target.contains("windows") {
        Platform::Windows
    } else {
        Platform::Unknown
    }
}
```

**Testing:**
```bash
# Test each platform detection
TARGET=aarch64-apple-ios cargo build --lib
TARGET=aarch64-linux-android cargo build --lib --features android
TARGET=x86_64-apple-darwin cargo build
```

---

#### Step 1.3: Implement Linker Configuration

**File:** `build.rs`

**Implementation:**
```rust
fn configure_linker(platform: Platform) {
    match platform {
        Platform::IOS | Platform::MacOS => {
            // Link Foundation framework for NSString/CString conversion
            // This helps with CString <-> NSString interop in iOS
            println!("cargo:rustc-link-lib=framework=Foundation");
        }
        Platform::Android => {
            // Link Android log library for android_log_print
            // Only needed if using Android-specific logging
            println!("cargo:rustc-link-lib=log");
        }
        Platform::Linux => {
            // Link libc for C FFI (standard on Linux)
            println!("cargo:rustc-link-lib=c");
        }
        Platform::Windows => {
            // Windows MSVC automatically links C runtime
            // Additional libraries can be added here if needed
        }
        Platform::Unknown => {
            // Don't configure anything for unknown platforms
        }
    }
}
```

**Critical Question:** Do we actually need Foundation framework linking?

**Investigation Needed:**
- Check if iOS/macOS builds fail without it
- Check if JNI/FFI code uses Foundation APIs
- Verify existing builds work with/without it

**Approach:** Start conservative - only add if needed or if it's standard practice

---

#### Step 1.4: Implement FFI Header Validation

**File:** `build.rs`

**Implementation:**
```rust
fn validate_ffi_header() -> Result<(), Box<dyn std::error::Error>> {
    let header_path = "include/arxos_mobile.h";
    
    if !std::path::Path::new(header_path).exists() {
        return Err(format!("FFI header file not found: {}", header_path).into());
    }
    
    // Tell Cargo to rerun if header changes
    println!("cargo:rerun-if-changed={}", header_path);
    
    Ok(())
}
```

**Error Handling Strategy:**
- **Warning only** - Don't fail builds
- Log warning but continue
- Reason: Header might not be needed for all build types

**Implementation:**
```rust
if let Err(e) = validate_ffi_header() {
    eprintln!("⚠️  Warning: {}", e);
    eprintln!("   This may cause issues with mobile FFI builds.");
    // Don't fail build, just warn
}
```

---

#### Step 1.5: Add Rerun Triggers

**File:** `build.rs`

**Implementation:**
```rust
fn main() {
    // ... other logic ...
    
    // Tell Cargo when to rerun this build script
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=include/arxos_mobile.h");
}
```

**Purpose:** Ensure build script reruns when dependencies change

---

### Phase 1 Testing Plan

#### Test Matrix

| Platform | Build Command | Expected Result |
|----------|--------------|-----------------|
| macOS Desktop | `cargo build` | ✅ Links Foundation, validates header |
| iOS Device | `cargo build -p arxos --target aarch64-apple-ios --lib` | ✅ Links Foundation, validates header |
| iOS Simulator | `cargo build -p arxos --target x86_64-apple-ios --lib` | ✅ Links Foundation, validates header |
| Android ARM64 | `cargo build -p arxos --target aarch64-linux-android --lib --features android` | ✅ Links log, validates header |
| Linux Desktop | `cargo build -p arxos --target x86_64-unknown-linux-gnu` | ✅ Links libc, validates header |
| Windows | `cargo build -p arxos --target x86_64-pc-windows-msvc` | ✅ No special links, validates header |

#### Validation Checklist

- [ ] All platforms build successfully
- [ ] No new warnings appear (except intentional ones)
- [ ] FFI header validation works (test by temporarily renaming header)
- [ ] Linker configuration doesn't break existing builds
- [ ] Build script reruns when header changes

---

### Phase 2: Enhanced Validation

#### Step 2.1: Android Feature Validation

**Implementation:**
```rust
fn validate_features() {
    let target = env::var("TARGET").unwrap_or_default();
    let features = env::var("CARGO_CFG_FEATURES").unwrap_or_default();
    
    // Warn if building for Android without android feature
    if target.contains("android") && !features.contains("android") {
        eprintln!("⚠️  Warning: Building for Android but 'android' feature not enabled");
        eprintln!("   Some JNI functionality may not be available.");
        eprintln!("   Consider: cargo build --features android");
    }
}
```

**Why Warning Only:**
- Some builds might intentionally skip JNI
- Don't block development workflows
- Helpful reminder without being strict

---

#### Step 2.2: Build Info Injection (Optional)

**Decision Point:** Do we need this now?

**Use Cases:**
- Runtime version reporting (`arx --version`)
- Debug information
- Support/debugging

**If Needed:**
```rust
fn inject_build_info() {
    let version = env!("CARGO_PKG_VERSION");
    // Build time would require chrono dependency
    // Consider if this is actually needed
    
    println!("cargo:rustc-env=ARXOS_VERSION={}", version);
    println!("cargo:rerun-if-changed=Cargo.toml");
}
```

**Recommendation:** Skip for now unless there's a specific need

---

### Phase 3: Header Auto-generation (Future)

#### Evaluation: cbindgen vs Manual

**cbindgen Pros:**
- ✅ Automatic generation from Rust code
- ✅ No manual maintenance
- ✅ Type-safe

**cbindgen Cons:**
- ⚠️ Adds build-time dependency
- ⚠️ May need customization
- ⚠️ Requires tool in CI/CD
- ⚠️ Generated headers might be less readable

**Manual Pros:**
- ✅ Full control over header format
- ✅ Can add documentation/comments
- ✅ No additional tooling

**Manual Cons:**
- ❌ Risk of drift
- ❌ Manual maintenance

**Hybrid Approach:**
1. Use cbindgen to generate base header
2. Allow manual annotations/customizations
3. Validate generated matches manual in CI

**Decision:** Evaluate after Phases 1 & 2 are stable

---

## Risk Mitigation

### Risk 1: Breaking Existing Builds

**Mitigation:**
- Make all additions non-breaking
- Warnings only, no hard errors
- Test on all platforms before merging
- Keep old behavior as fallback

### Risk 2: Linker Conflicts

**Mitigation:**
- Only add linker flags if needed
- Test that existing builds still work
- Make linker config optional via feature flag if needed

### Risk 3: Build Time Impact

**Mitigation:**
- Keep build.rs simple and fast
- Only add dependencies if essential
- Use `rerun-if-changed` judiciously

### Risk 4: Maintenance Overhead

**Mitigation:**
- Document all decisions
- Keep code simple and readable
- Add comments explaining why each step exists

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Update `build.rs` with platform detection
- [ ] Add linker configuration (conservative approach)
- [ ] Add FFI header validation (warning only)
- [ ] Add rerun triggers
- [ ] Test on macOS desktop
- [ ] Test iOS build
- [ ] Test Android build
- [ ] Test Linux build
- [ ] Test Windows build (if possible)
- [ ] Document changes

### Phase 2: Enhanced Validation
- [ ] Add Android feature validation
- [ ] Consider build info injection (if needed)
- [ ] Test warnings appear correctly
- [ ] Document validation behavior

### Phase 3: Auto-generation (Future)
- [ ] Evaluate cbindgen
- [ ] Set up cbindgen config
- [ ] Implement in build.rs
- [ ] Update CI/CD
- [ ] Migrate to auto-generated headers
- [ ] Remove manual header (or keep as fallback)

---

## Open Questions

1. **Do we need Foundation framework linking?**
   - Action: Test iOS build with/without it
   - Investigate if JNI/FFI code uses Foundation APIs

2. **Should linker config be feature-gated?**
   - Consider: `[features] link-foundation = []`
   - Allows opt-out if needed

3. **How strict should header validation be?**
   - Current plan: Warning only
   - Future: Could add signature validation

4. **Build info injection - needed now?**
   - Check if `arx --version` or other code uses it
   - If not needed, skip to reduce dependencies

---

## Next Steps

1. **Review this plan** with team
2. **Resolve open questions** (especially Foundation linking)
3. **Implement Phase 1** (foundation)
4. **Test thoroughly** on all platforms
5. **Merge and document**
6. **Proceed to Phase 2** if Phase 1 is stable

---

## References

- [Cargo Build Scripts Documentation](https://doc.rust-lang.org/cargo/reference/build-scripts.html)
- [cbindgen Documentation](https://github.com/mozilla/cbindgen)
- [Rust FFI Best Practices](https://michael-f-bryan.github.io/rust-ffi-guide/)
- Review Document: `docs/BUILD_RS_REVIEW.md`

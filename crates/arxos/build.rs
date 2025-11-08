//! Build script for ArxOS
//!
//! Handles:
//! - Platform detection
//! - FFI header validation (warnings only)
//! - FFI header auto-generation (optional, via cbindgen)
//! - Build-time feature validation
//! - Build info injection (version)
//! - Build script rerun triggers
//!
//! This build script ensures that FFI headers are present for mobile builds,
//! validates feature flags for platform builds, and provides platform detection
//! for future enhancements.

use std::env;
use std::path::Path;
use std::process::Command;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Platform {
    Ios,
    Android,
    MacOS,
    Linux,
    Windows,
    Unknown,
}

/// Detect the target platform from the TARGET environment variable
fn detect_platform() -> Platform {
    let target = env::var("TARGET").unwrap_or_default();

    if target.contains("apple-ios") {
        Platform::Ios
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

/// Check if cbindgen is available on the system
fn cbindgen_available() -> bool {
    Command::new("cbindgen").arg("--version").output().is_ok()
}

/// Generate FFI header using cbindgen
///
/// Returns Ok(()) if generation succeeded, Err with message if failed.
fn generate_ffi_header() -> Result<(), String> {
    let config_path = Path::new("../cbindgen.toml");
    let output_path = Path::new("../include/arxos_mobile.h");

    if !config_path.exists() {
        return Err(format!(
            "cbindgen.toml not found at {}",
            config_path.display()
        ));
    }

    // Run cbindgen to generate header
    let output = Command::new("cbindgen")
        .arg("--config")
        .arg(config_path)
        .arg("--crate")
        .arg("arxos")
        .arg("--output")
        .arg(output_path)
        .output()
        .map_err(|e| format!("Failed to run cbindgen: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("cbindgen failed: {}", stderr));
    }

    Ok(())
}

/// Validate that the FFI header file exists
///
/// Returns Ok(()) if header exists, Err with message if missing.
/// This is a warning-only check - builds will not fail if header is missing.
fn validate_ffi_header() -> Result<(), String> {
    let header_path = Path::new("../include/arxos_mobile.h");

    if !header_path.exists() {
        return Err(format!(
            "FFI header file not found: {}",
            header_path.display()
        ));
    }

    // Tell Cargo to rerun this build script if the header changes
    println!("cargo:rerun-if-changed={}", header_path.display());

    Ok(())
}

/// Validate feature flags for the target platform
///
/// Warns if building for Android without the `android` feature enabled,
/// which may cause JNI functionality to be unavailable.
fn validate_features(platform: Platform) {
    if platform != Platform::Android {
        // Only validate Android feature flag for Android targets
        return;
    }

    let features = env::var("CARGO_CFG_FEATURES").unwrap_or_default();

    if !features.contains("android") {
        eprintln!("⚠️  Warning: Building for Android but 'android' feature not enabled");
        eprintln!("   Some JNI functionality may not be available.");
        eprintln!("   Consider: cargo build -p arxos --target <android-target> --features android");
        eprintln!("   Or add to Cargo.toml: [features] default = [\"android\"]");
    }
}

/// Inject build-time information as environment variables
///
/// Makes version information available at compile-time via env!() macro.
/// Can be accessed in code with: env!("ARXOS_VERSION")
fn inject_build_info() {
    let version = env!("CARGO_PKG_VERSION");

    // Make version available at compile-time
    println!("cargo:rustc-env=ARXOS_VERSION={}", version);

    // Rerun if Cargo.toml changes (version might change)
    println!("cargo:rerun-if-changed=Cargo.toml");
}

fn main() {
    // Detect target platform (for future use and debugging)
    let platform = detect_platform();

    // Phase 3: Try to auto-generate FFI header using cbindgen
    // If cbindgen is available and cbindgen.toml exists, generate the header
    // Otherwise, fall back to validation-only mode
    let header_generated = if cbindgen_available() {
        match generate_ffi_header() {
            Ok(()) => {
                if platform == Platform::Ios || platform == Platform::Android {
                    // Mobile builds benefit from auto-generated headers
                }
                true
            }
            Err(e) => {
                // Generation failed - warn but continue with validation
                eprintln!("⚠️  Warning: Failed to auto-generate FFI header: {}", e);
                eprintln!("   Falling back to header validation mode.");
                eprintln!(
                    "   To enable auto-generation, ensure cbindgen.toml is configured correctly."
                );
                false
            }
        }
    } else {
        false
    };

    // Validate FFI header exists (regardless of generation attempt)
    // Warning only - don't fail builds as header might not be needed for all build types
    match validate_ffi_header() {
        Ok(()) => {
            // Header exists - good to go
            if header_generated {
                // Tell Cargo to rerun if FFI source changes
                println!("cargo:rerun-if-changed=src/mobile_ffi/ffi.rs");
                println!("cargo:rerun-if-changed=../cbindgen.toml");
            }
            if platform == Platform::Ios || platform == Platform::Android {
                // Mobile builds typically need the header, so we're all set
            }
        }
        Err(e) => {
            // Header missing - warn but don't fail
            eprintln!("⚠️  Warning: {}", e);
            eprintln!("   This may cause issues with mobile FFI builds.");
            eprintln!("   Desktop builds may work without this header.");

            if !header_generated && cbindgen_available() {
                eprintln!("   💡 Tip: Install cbindgen and configure cbindgen.toml to auto-generate headers.");
            }
        }
    }

    // Validate feature flags for platform-specific builds
    validate_features(platform);

    // Inject build-time information (version)
    inject_build_info();

    // Tell Cargo when to rerun this build script
    println!("cargo:rerun-if-changed=build.rs");

    // Platform-specific rerun triggers (for future linker configuration)
    // Currently commented out as we're not doing linker config yet
    // Uncomment when adding platform-specific build logic:
    // match platform {
    //     Platform::Ios | Platform::MacOS => {
    //         // Could add Foundation framework linking here if needed
    //     }
    //     Platform::Android => {
    //         // Could add Android log library linking here if needed
    //     }
    //     Platform::Linux => {
    //         // Could add libc linking here if needed
    //     }
    //     _ => {}
    // }
}

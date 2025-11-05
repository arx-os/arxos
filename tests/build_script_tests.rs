//! Integration tests for build.rs functionality
//!
//! These tests verify that build script features work correctly,
//! including version injection and platform detection.

#[test]
fn test_build_version_available() {
    // Verify that ARXOS_VERSION is available at compile time
    let version = env!("ARXOS_VERSION");
    
    // Version should not be empty
    assert!(!version.is_empty(), "ARXOS_VERSION should not be empty");
    
    // Version should match Cargo.toml version format (semver)
    // Basic check: should contain at least one dot
    assert!(
        version.contains('.'),
        "ARXOS_VERSION should be in semver format (e.g., 0.1.0), got: {}",
        version
    );
    
    // Version should start with a digit
    assert!(
        version.chars().next().map_or(false, |c| c.is_ascii_digit()),
        "ARXOS_VERSION should start with a digit, got: {}",
        version
    );
}

#[test]
fn test_build_version_format() {
    let version = env!("ARXOS_VERSION");
    
    // Should be valid semver (major.minor.patch or similar)
    let parts: Vec<&str> = version.split('.').collect();
    assert!(
        parts.len() >= 2,
        "ARXOS_VERSION should have at least major.minor format, got: {}",
        version
    );
    
    // Each part should be numeric or alphanumeric with pre-release/build metadata
    for part in &parts {
        assert!(
            !part.is_empty(),
            "ARXOS_VERSION parts should not be empty"
        );
    }
}

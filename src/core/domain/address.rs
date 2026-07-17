//! ArxOS Address System
//!
//! Provides hierarchical addressing for building components using a 7-part path format:
//! /country/state/city/building/floor/room/fixture
//!
//! Supports both standardized engineering systems (14 reserved) and custom items.

use crate::error::ArxError;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fmt;

/// Reserved system names for standardized engineering components
pub const RESERVED_SYSTEMS: [&str; 14] = [
    "hvac",       // boilers, AHUs
    "plumbing",   // valves, pumps
    "electrical", // panels, breakers
    "fire",       // sprinklers, alarms
    "lighting",   // fixtures, controls
    "security",   // cameras, access
    "elevators",  // cars, controls
    "roof",       // units, drains
    "windows",    // frames, glass
    "doors",      // hinges, locks
    "structure",  // columns, beams
    "envelope",   // walls, insulation
    "it",         // switches, APs
    "furniture",  // desks, chairs
];

/// ArxOS Address - hierarchical path for building components
///
/// Format: /country/state/city/building/floor/room/fixture
///
/// Example (Standardized): /usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01
/// Example (Custom): /usa/ny/brooklyn/ps-118/floor-02/kitchen/fridge/pbj-sandwich
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(transparent)]
pub struct ArxAddress {
    pub path: String,
}

impl ArxAddress {
    /// Build address from parts (all lower-case, sanitized)
    ///
    /// # Arguments
    /// * `country` - Country code (e.g., "usa")
    /// * `state` - State/province code (e.g., "ny")
    /// * `city` - City name (e.g., "brooklyn")
    /// * `building` - Building identifier (e.g., "ps-118")
    /// * `floor` - Floor identifier (e.g., "floor-02")
    /// * `room` - Room/system name (e.g., "mech" or "kitchen")
    /// * `fixture` - Fixture/equipment name (e.g., "boiler-01" or "pbj-sandwich")
    pub fn new(
        country: &str,
        state: &str,
        city: &str,
        building: &str,
        floor: &str,
        room: &str,
        fixture: &str,
    ) -> Self {
        let parts = vec![
            Self::sanitize_part(country),
            Self::sanitize_part(state),
            Self::sanitize_part(city),
            Self::sanitize_part(building),
            Self::sanitize_part(floor),
            Self::sanitize_part(room),
            Self::sanitize_part(fixture),
        ];
        let non_empty: Vec<String> = parts.into_iter().filter(|s| !s.is_empty()).collect();
        let path = format!("/{}", non_empty.join("/"));
        Self { path }
    }

    /// Parse a full path string into an ArxAddress
    ///
    /// # Arguments
    /// * `path` - Full path string (e.g., "/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01")
    ///
    /// # Returns
    /// * `Result<ArxAddress>` - Parsed address or error if format is invalid
    pub fn from_path(path: &str) -> Result<Self> {
        if !path.starts_with('/') {
            return Err(ArxError::path_invalid(
                path,
                "Path must start with '/'",
            )
            .into());
        }
        let clean = path.trim_start_matches('/');
        if clean.is_empty() {
            return Err(ArxError::path_invalid(
                path,
                "Path cannot be empty",
            )
            .into());
        }
        let parts: Vec<&str> = clean.split('/').filter(|s| !s.is_empty()).collect();
        if parts.is_empty() {
            return Err(ArxError::path_invalid(
                path,
                "Path cannot be empty",
            )
            .into());
        }
        // Check for invalid characters in any segment (traversal safety)
        for part in &parts {
            if part.is_empty() || !part.chars().all(|c| c.is_alphanumeric() || c == '-' || c == '_') {
                return Err(ArxError::path_invalid(
                    path,
                    "Path segments must be alphanumeric, hyphen, or underscore",
                )
                .into());
            }
        }
        Ok(Self {
            path: format!("/{}", parts.join("/")),
        })
    }

    /// Validate address format and reserved system rules
    ///
    /// For reserved systems, validates that fixture names follow expected patterns.
    /// For custom systems, any fixture name is allowed.
    ///
    /// # Returns
    /// * `Ok(())` if valid, or `Err(AddressValidationError)`
    pub fn validate(&self) -> Result<(), AddressValidationError> {
        let parts: Vec<&str> = self.path.trim_start_matches('/').split('/').filter(|s| !s.is_empty()).collect();
        if parts.is_empty() {
            return Err(AddressValidationError::MissingSegments);
        }

        // Validate each part contains only lowercase/valid characters
        for part in &parts {
            if part.to_lowercase() != *part {
                return Err(AddressValidationError::NotLowercase { part: part.to_string() });
            }
            if !part.chars().all(|c| c.is_alphanumeric() || c == '-' || c == '_') {
                return Err(AddressValidationError::InvalidCharacters { part: part.to_string() });
            }
        }

        // If there's a reserved system segment, validate the following segment (if any)
        for (i, part) in parts.iter().enumerate() {
            if RESERVED_SYSTEMS.contains(part) && i + 1 < parts.len() {
                let fixture = parts[i + 1];
                match *part {
                    "hvac" => {
                        if !fixture.starts_with("boiler-") && !fixture.starts_with("ahu-") && !fixture.starts_with("vav-") {
                            return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                                system: part.to_string(),
                                message: "HVAC fixture must start with boiler-, ahu-, or vav-".to_string(),
                            });
                        }
                    }
                    "plumbing" => {
                        if !fixture.starts_with("valve-") && !fixture.starts_with("pump-") {
                            return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                                system: part.to_string(),
                                message: "Plumbing fixture must start with valve- or pump-".to_string(),
                            });
                        }
                    }
                    "electrical" => {
                        if !fixture.starts_with("panel-") && !fixture.starts_with("breaker-") {
                            return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                                system: part.to_string(),
                                message: "Electrical fixture must start with panel- or breaker-".to_string(),
                            });
                        }
                    }
                    "fire" => {
                        if !fixture.starts_with("sprinkler-") && !fixture.starts_with("alarm-") {
                            return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                                system: part.to_string(),
                                message: "Fire fixture must start with sprinkler- or alarm-".to_string(),
                            });
                        }
                    }
                    "lighting" => {
                        if !fixture.starts_with("fixture-") && !fixture.starts_with("control-") {
                            return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                                system: part.to_string(),
                                message: "Lighting fixture must start with fixture- or control-".to_string(),
                            });
                        }
                    }
                    "security" => {
                        if !fixture.starts_with("camera-") && !fixture.starts_with("access-") {
                            return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                                system: part.to_string(),
                                message: "Security fixture must start with camera- or access-".to_string(),
                            });
                        }
                    }
                    "elevators" => {
                        if !fixture.starts_with("car-") && !fixture.starts_with("control-") {
                            return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                                system: part.to_string(),
                                message: "Elevator fixture must start with car- or control-".to_string(),
                            });
                        }
                    }
                    "roof" => {
                        if !fixture.starts_with("unit-") && !fixture.starts_with("drain-") {
                            return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                                system: part.to_string(),
                                message: "Roof fixture must start with unit- or drain-".to_string(),
                            });
                        }
                    }
                    "windows" => {
                        if !fixture.starts_with("frame-") && !fixture.starts_with("glass-") {
                            return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                                system: part.to_string(),
                                message: "Window fixture must start with frame- or glass-".to_string(),
                            });
                        }
                    }
                    "doors" => {
                        if !fixture.starts_with("hinge-") && !fixture.starts_with("lock-") {
                            return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                                system: part.to_string(),
                                message: "Door fixture must start with hinge- or lock-".to_string(),
                            });
                        }
                    }
                    "structure" => {
                        if !fixture.starts_with("column-") && !fixture.starts_with("beam-") {
                            return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                                system: part.to_string(),
                                message: "Structure fixture must start with column- or beam-".to_string(),
                            });
                        }
                    }
                    "envelope" => {
                        if !fixture.starts_with("wall-") && !fixture.starts_with("insulation-") {
                            return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                                system: part.to_string(),
                                message: "Envelope fixture must start with wall- or insulation-".to_string(),
                            });
                        }
                    }
                    "it" => {
                        if !fixture.starts_with("switch-") && !fixture.starts_with("ap-") {
                            return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                                system: part.to_string(),
                                message: "IT fixture must start with switch- or ap-".to_string(),
                            });
                        }
                    }
                    "furniture" if !fixture.starts_with("desk-") && !fixture.starts_with("chair-") => {
                        return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                            system: part.to_string(),
                            message: "Furniture fixture must start with desk- or chair-".to_string(),
                        });
                    }
                    _ => {}
                }
            }
        }
        Ok(())
    }

    /// Get parent path (up to room, excluding fixture)
    ///
    /// # Returns
    /// * Parent path string (e.g., "/usa/ny/brooklyn/ps-118/floor-02/mech")
    pub fn parent(&self) -> String {
        let parts: Vec<&str> = self.path.trim_start_matches('/').split('/').filter(|s| !s.is_empty()).collect();
        if parts.len() > 1 {
            format!("/{}", parts[..parts.len() - 1].join("/"))
        } else {
            self.path.clone()
        }
    }

    /// Stable hex token derived from the address path (SHA-256).
    ///
    /// **Not** the IFC product GlobalId. Product GlobalIds come from
    /// `ifc_global_id` / `resolve_product_global_id` / `ifc_global_id_from_uuid`
    /// (see `docs/identity.md`). This helper is for address-keyed fixtures only.
    pub fn guid(&self) -> String {
        let mut hasher = Sha256::new();
        hasher.update(self.path.as_bytes());
        format!("{:x}", hasher.finalize())
    }

    /// Get parts of the address
    ///
    /// # Returns
    /// * Tuple of (country, state, city, building, floor, room, fixture)
    pub fn parts(&self) -> Result<(String, String, String, String, String, String, String)> {
        let segs: Vec<&str> = self.path.trim_start_matches('/').split('/').filter(|s| !s.is_empty()).collect();
        let mut parts = vec!["".to_string(); 7];
        for (i, seg) in segs.iter().enumerate() {
            if i < 6 {
                parts[i] = seg.to_string();
            } else {
                if parts[6].is_empty() {
                    parts[6] = seg.to_string();
                } else {
                    parts[6] = format!("{}/{}", parts[6], seg);
                }
            }
        }
        Ok((
            parts[0].clone(),
            parts[1].clone(),
            parts[2].clone(),
            parts[3].clone(),
            parts[4].clone(),
            parts[5].clone(),
            parts[6].clone(),
        ))
    }

    /// Get all individual segments of the path as a list of strings
    pub fn segments(&self) -> Vec<String> {
        self.path.trim_start_matches('/').split('/').filter(|s| !s.is_empty()).map(|s| s.to_string()).collect()
    }

    /// Promote address from one branch prefix to another.
    /// E.g. /building/hq/floor-1/... -> /main/hq/floor-1/...
    pub fn promote_to_branch(&self, from_branch: &str, to_branch: &str) -> Self {
        let from_prefix = format!("/{}", Self::sanitize_part(from_branch));
        let to_prefix = format!("/{}", Self::sanitize_part(to_branch));
        if self.path.starts_with(&from_prefix) {
            let suffix = &self.path[from_prefix.len()..];
            Self {
                path: format!("{}{}", to_prefix, suffix),
            }
        } else {
            self.clone()
        }
    }

    /// Whether this address matches a glob pattern against the full path.
    ///
    /// Patterns use standard glob wildcards (`*`, `?`) on the full path string,
    /// e.g. `/usa/ny/*/floor-*/mech/boiler-*`.
    pub fn matches_glob(&self, pattern: &str) -> bool {
        let pat = if pattern.starts_with('/') {
            pattern.to_string()
        } else {
            format!("/{}", pattern)
        };
        match glob::Pattern::new(&pat) {
            Ok(p) => p.matches(&self.path),
            Err(_) => false,
        }
    }

    /// Sanitize a path part for use in addresses
    /// Converts to lowercase, replaces invalid characters with hyphens
    fn sanitize_part(part: &str) -> String {
        part.to_lowercase()
            .chars()
            .map(|c| {
                if c.is_alphanumeric() || c == '-' || c == '_' {
                    c
                } else {
                    '-'
                }
            })
            .collect::<String>()
            .split('-')
            .filter(|s| !s.is_empty())
            .collect::<Vec<_>>()
            .join("-")
    }
}

/// Detailed validation errors and warnings that can occur when checking the syntax 
/// and semantic rules of an [`ArxAddress`].
#[derive(Debug, Clone, thiserror::Error, PartialEq, Eq)]
pub enum AddressValidationError {
    /// A segment contains uppercase characters, violating lowercase-only naming.
    #[error("Segment '{part}' must be lowercase")]
    NotLowercase { part: String },
    /// A segment contains non-alphanumeric, non-hyphen, non-underscore characters.
    #[error("Segment '{part}' contains invalid characters")]
    InvalidCharacters { part: String },
    /// The address path does not start with a leading slash.
    #[error("Path must start with '/'")]
    MissingLeadingSlash,
    /// The address path is an empty string.
    #[error("Path cannot be empty")]
    EmptyPath,
    /// The address path has no segments.
    #[error("Path must contain at least one segment")]
    MissingSegments,
    /// A fixture name inside a reserved system (e.g. `hvac`) does not follow standard naming prefixes.
    #[error("Address validation failed for system '{system}': {message}")]
    ReservedSystemPrefixMismatch { system: String, message: String },
}

impl fmt::Display for ArxAddress {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.path)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_matches_glob() {
        let addr = ArxAddress::new(
            "usa",
            "ny",
            "brooklyn",
            "ps-118",
            "floor-02",
            "mech",
            "boiler-01",
        );
        assert!(addr.matches_glob("/usa/ny/*/floor-*/mech/boiler-*"));
        assert!(addr.matches_glob("/usa/ny/brooklyn/ps-118/floor-02/mech/*"));
        assert!(!addr.matches_glob("/usa/ny/brooklyn/ps-118/floor-02/kitchen/*"));
        assert!(!addr.matches_glob("/usa/ca/*/floor-*/mech/*"));
    }

    #[test]
    fn test_new_address() {
        let addr = ArxAddress::new(
            "usa",
            "ny",
            "brooklyn",
            "ps-118",
            "floor-02",
            "mech",
            "boiler-01",
        );
        assert_eq!(addr.path, "/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01");
    }

    #[test]
    fn test_from_path() {
        let addr =
            ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        assert_eq!(addr.path, "/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01");
    }

    #[test]
    fn test_from_path_invalid() {
        assert!(ArxAddress::from_path("usa/ny").is_err());
        assert!(ArxAddress::from_path("/usa/ny/../invalid").is_err());
    }

    #[test]
    fn test_validate_hvac() {
        let addr =
            ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/hvac/boiler-01").unwrap();
        assert!(addr.validate().is_ok());

        let addr =
            ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/hvac/invalid-01").unwrap();
        assert!(addr.validate().is_err());
    }

    #[test]
    fn test_validate_custom() {
        let addr =
            ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/kitchen/fridge-01").unwrap();
        assert!(addr.validate().is_ok());
    }

    #[test]
    fn test_validate_pragmatic() {
        // Pragmatic names inside reserved systems should return a PrefixMismatch error
        let addr = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/plumbing/faucet-01").unwrap();
        let res = addr.validate();
        assert!(res.is_err());
        assert!(matches!(res.unwrap_err(), AddressValidationError::ReservedSystemPrefixMismatch { .. }));

        // Non-prefixed custom items under non-reserved categories are Ok
        let addr = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/classroom/projector-01").unwrap();
        assert!(addr.validate().is_ok());
    }

    #[test]
    fn test_parent() {
        let addr =
            ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        assert_eq!(addr.parent(), "/usa/ny/brooklyn/ps-118/floor-02/mech");
    }

    #[test]
    fn test_guid() {
        let addr =
            ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        let guid1 = addr.guid();
        let guid2 = addr.guid();
        assert_eq!(guid1, guid2); // Deterministic
        assert_eq!(guid1.len(), 64); // SHA-256 produces 256-bit (64 hex chars) hash
    }

    #[test]
    fn test_parts() {
        let addr =
            ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        let (country, state, city, building, floor, room, fixture) = addr.parts().unwrap();
        assert_eq!(country, "usa");
        assert_eq!(state, "ny");
        assert_eq!(city, "brooklyn");
        assert_eq!(building, "ps-118");
        assert_eq!(floor, "floor-02");
        assert_eq!(room, "mech");
        assert_eq!(fixture, "boiler-01");
    }

    #[test]
    fn test_sanitize_part() {
        // Sanitization is private, but we can test it through new()
        let addr = ArxAddress::new(
            "USA",
            "NY",
            "New York",
            "PS 118",
            "Floor 02",
            "Mech Room",
            "Boiler 01",
        );
        assert_eq!(
            addr.path,
            "/usa/ny/new-york/ps-118/floor-02/mech-room/boiler-01"
        );
    }

    #[test]
    fn test_validate_all_reserved_systems() {
        // Test all 14 reserved systems with valid prefixes
        let valid_cases = vec![
            ("hvac", "boiler-01"),
            ("hvac", "ahu-02"),
            ("plumbing", "valve-01"),
            ("plumbing", "pump-02"),
            ("electrical", "panel-01"),
            ("electrical", "breaker-02"),
            ("fire", "sprinkler-01"),
            ("fire", "alarm-02"),
            ("lighting", "fixture-01"),
            ("lighting", "control-02"),
            ("security", "camera-01"),
            ("security", "access-02"),
            ("elevators", "car-01"),
            ("elevators", "control-02"),
            ("roof", "unit-01"),
            ("roof", "drain-02"),
            ("windows", "frame-01"),
            ("windows", "glass-02"),
            ("doors", "hinge-01"),
            ("doors", "lock-02"),
            ("structure", "column-01"),
            ("structure", "beam-02"),
            ("envelope", "wall-01"),
            ("envelope", "insulation-02"),
            ("it", "switch-01"),
            ("it", "ap-02"),
            ("furniture", "desk-01"),
            ("furniture", "chair-02"),
        ];

        for (system, fixture) in valid_cases {
            let addr = ArxAddress::from_path(&format!(
                "/usa/ny/brooklyn/ps-118/floor-02/{}/{}",
                system, fixture
            ))
            .unwrap();
            assert!(
                addr.validate().is_ok(),
                "Failed validation for {}/{}",
                system,
                fixture
            );
        }
    }

    #[test]
    fn test_validate_invalid_prefixes() {
        // Test invalid prefixes for reserved systems
        let invalid_cases = vec![
            ("hvac", "invalid-01"),
            ("plumbing", "wrong-01"),
            ("electrical", "bad-01"),
        ];

        for (system, fixture) in invalid_cases {
            let addr = ArxAddress::from_path(&format!(
                "/usa/ny/brooklyn/ps-118/floor-02/{}/{}",
                system, fixture
            ))
            .unwrap();
            assert!(
                addr.validate().is_err(),
                "Should fail validation for {}/{}",
                system,
                fixture
            );
        }
    }

    #[test]
    fn test_guid_stability() {
        // Test that same path produces same GUID
        let addr1 =
            ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        let addr2 =
            ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        assert_eq!(addr1.guid(), addr2.guid());
    }

    #[test]
    fn test_guid_uniqueness() {
        // Test that different paths produce different GUIDs
        let addr1 =
            ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        let addr2 =
            ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-02").unwrap();
        assert_ne!(addr1.guid(), addr2.guid());
    }

    #[test]
    fn test_guid_collision_guard() {
        // Verify that GUID generation is deterministic and unique per path
        // SHA-256 has extremely low collision probability, but we verify determinism
        let paths = vec![
            "/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01",
            "/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-02",
            "/usa/ny/brooklyn/ps-118/floor-02/kitchen/fridge-01",
            "/usa/ca/san-francisco/office-building/floor-01/hvac/ahu-01",
        ];

        let mut guids = std::collections::HashSet::new();
        for path in &paths {
            let addr = ArxAddress::from_path(path).unwrap();
            let guid = addr.guid();

            // Verify determinism - same path should produce same GUID
            let addr2 = ArxAddress::from_path(path).unwrap();
            assert_eq!(
                addr.guid(),
                addr2.guid(),
                "GUID should be deterministic for path: {}",
                path
            );

            // Verify uniqueness - different paths should produce different GUIDs
            assert!(
                guids.insert(guid.clone()),
                "GUID collision detected for path: {}",
                path
            );
        }
    }

    #[test]
    fn test_invalid_path_rejected() {
        // Test that invalid paths are rejected
        assert!(ArxAddress::from_path("").is_err());
        assert!(ArxAddress::from_path("/").is_err());
        assert!(ArxAddress::from_path("/usa/ny/special@char").is_err());
    }
}

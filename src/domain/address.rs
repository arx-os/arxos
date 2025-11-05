//! ArxOS Address System
//!
//! Provides hierarchical addressing for building components using a 7-part path format:
//! /country/state/city/building/floor/room/fixture
//!
//! Supports both standardized engineering systems (14 reserved) and custom items.

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::fmt;
use sha2::{Sha256, Digest};
use crate::error::ArxError;

/// Reserved system names for standardized engineering components
pub const RESERVED_SYSTEMS: [&str; 14] = [
    "hvac",         // boilers, AHUs
    "plumbing",     // valves, pumps
    "electrical",   // panels, breakers
    "fire",         // sprinklers, alarms
    "lighting",     // fixtures, controls
    "security",     // cameras, access
    "elevators",    // cars, controls
    "roof",         // units, drains
    "windows",      // frames, glass
    "doors",        // hinges, locks
    "structure",    // columns, beams
    "envelope",     // walls, insulation
    "it",           // switches, APs
    "furniture",    // desks, chairs
];

/// ArxOS Address - hierarchical path for building components
///
/// Format: /country/state/city/building/floor/room/fixture
///
/// Example (Standardized): /usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01
/// Example (Custom): /usa/ny/brooklyn/ps-118/floor-02/kitchen/fridge/pbj-sandwich
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Eq, Hash)]
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
        let path = format!(
            "/{}/{}/{}/{}/{}/{}/{}",
            Self::sanitize_part(country),
            Self::sanitize_part(state),
            Self::sanitize_part(city),
            Self::sanitize_part(building),
            Self::sanitize_part(floor),
            Self::sanitize_part(room),
            Self::sanitize_part(fixture)
        );
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
        let clean = path.trim_start_matches('/');
        let parts: Vec<&str> = clean.split('/').collect();
        if parts.len() != 7 {
            return Err(ArxError::path_invalid(
                path,
                "/country/state/city/building/floor/room/fixture"
            ).into());
        }
        Ok(Self {
            path: format!("/{}", clean),
        })
    }

    /// Validate address format and reserved system rules
    ///
    /// For reserved systems, validates that fixture names follow expected patterns.
    /// For custom systems, any fixture name is allowed.
    ///
    /// # Returns
    /// * `Result<()>` - Ok if valid, error if validation fails
    pub fn validate(&self) -> Result<()> {
        let parts: Vec<&str> = self.path.trim_start_matches('/').split('/').collect();
        if parts.len() != 7 {
            return Err(ArxError::path_invalid(
                self.path.clone(),
                "/country/state/city/building/floor/room/fixture"
            ).into());
        }

        let system = parts[5]; // room / system (6th part, 0-indexed)

        if RESERVED_SYSTEMS.contains(&system) {
            let fixture = parts[6];
            // Validate fixture naming patterns for reserved systems
            match system {
                "hvac" => {
                    if !fixture.starts_with("boiler-") && !fixture.starts_with("ahu-") {
                        return Err(ArxError::address_validation(
                            self.path.clone(),
                            "HVAC fixture must start with boiler- or ahu-"
                        ).into());
                    }
                }
                "plumbing" => {
                    if !fixture.starts_with("valve-") && !fixture.starts_with("pump-") {
                        return Err(ArxError::address_validation(
                            self.path.clone(),
                            "Plumbing fixture must start with valve- or pump-"
                        ).into());
                    }
                }
                "electrical" => {
                    if !fixture.starts_with("panel-") && !fixture.starts_with("breaker-") {
                        return Err(ArxError::address_validation(
                            self.path.clone(),
                            "Electrical fixture must start with panel- or breaker-"
                        ).into());
                    }
                }
                "fire" => {
                    if !fixture.starts_with("sprinkler-") && !fixture.starts_with("alarm-") {
                        return Err(ArxError::address_validation(
                            self.path.clone(),
                            "Fire fixture must start with sprinkler- or alarm-"
                        ).into());
                    }
                }
                "lighting" => {
                    if !fixture.starts_with("fixture-") && !fixture.starts_with("control-") {
                        return Err(ArxError::address_validation(
                            self.path.clone(),
                            "Lighting fixture must start with fixture- or control-"
                        ).into());
                    }
                }
                "security" => {
                    if !fixture.starts_with("camera-") && !fixture.starts_with("access-") {
                        return Err(ArxError::address_validation(
                            self.path.clone(),
                            "Security fixture must start with camera- or access-"
                        ).into());
                    }
                }
                "elevators" => {
                    if !fixture.starts_with("car-") && !fixture.starts_with("control-") {
                        return Err(ArxError::address_validation(
                            self.path.clone(),
                            "Elevator fixture must start with car- or control-"
                        ).into());
                    }
                }
                "roof" => {
                    if !fixture.starts_with("unit-") && !fixture.starts_with("drain-") {
                        return Err(ArxError::address_validation(
                            self.path.clone(),
                            "Roof fixture must start with unit- or drain-"
                        ).into());
                    }
                }
                "windows" => {
                    if !fixture.starts_with("frame-") && !fixture.starts_with("glass-") {
                        return Err(ArxError::address_validation(
                            self.path.clone(),
                            "Window fixture must start with frame- or glass-"
                        ).into());
                    }
                }
                "doors" => {
                    if !fixture.starts_with("hinge-") && !fixture.starts_with("lock-") {
                        return Err(ArxError::address_validation(
                            self.path.clone(),
                            "Door fixture must start with hinge- or lock-"
                        ).into());
                    }
                }
                "structure" => {
                    if !fixture.starts_with("column-") && !fixture.starts_with("beam-") {
                        return Err(ArxError::address_validation(
                            self.path.clone(),
                            "Structure fixture must start with column- or beam-"
                        ).into());
                    }
                }
                "envelope" => {
                    if !fixture.starts_with("wall-") && !fixture.starts_with("insulation-") {
                        return Err(ArxError::address_validation(
                            self.path.clone(),
                            "Envelope fixture must start with wall- or insulation-"
                        ).into());
                    }
                }
                "it" => {
                    if !fixture.starts_with("switch-") && !fixture.starts_with("ap-") {
                        return Err(ArxError::address_validation(
                            self.path.clone(),
                            "IT fixture must start with switch- or ap-"
                        ).into());
                    }
                }
                "furniture" => {
                    if !fixture.starts_with("desk-") && !fixture.starts_with("chair-") {
                        return Err(ArxError::address_validation(
                            self.path.clone(),
                            "Furniture fixture must start with desk- or chair-"
                        ).into());
                    }
                }
                _ => {}
            }
        }
        // Open systems: anything goes
        Ok(())
    }

    /// Get parent path (up to room, excluding fixture)
    ///
    /// # Returns
    /// * Parent path string (e.g., "/usa/ny/brooklyn/ps-118/floor-02/mech")
    pub fn parent(&self) -> String {
        let parts: Vec<&str> = self.path.trim_start_matches('/').split('/').collect();
        if parts.len() >= 6 {
            format!("/{}", parts[..6].join("/"))
        } else {
            self.path.clone()
        }
    }

    /// Generate stable GUID for IFC export using SHA-256 hash
    ///
    /// # Returns
    /// * Hexadecimal string representation of the hash
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
        let parts: Vec<&str> = self.path.trim_start_matches('/').split('/').collect();
        if parts.len() != 7 {
            return Err(ArxError::path_invalid(
                self.path.clone(),
                "/country/state/city/building/floor/room/fixture"
            ).into());
        }
        Ok((
            parts[0].to_string(),
            parts[1].to_string(),
            parts[2].to_string(),
            parts[3].to_string(),
            parts[4].to_string(),
            parts[5].to_string(),
            parts[6].to_string(),
        ))
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

impl fmt::Display for ArxAddress {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.path)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_address() {
        let addr = ArxAddress::new(
            "usa", "ny", "brooklyn", "ps-118", "floor-02", "mech", "boiler-01"
        );
        assert_eq!(addr.path, "/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01");
    }

    #[test]
    fn test_from_path() {
        let addr = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        assert_eq!(addr.path, "/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01");
    }

    #[test]
    fn test_from_path_invalid() {
        assert!(ArxAddress::from_path("/usa/ny").is_err());
        assert!(ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech").is_err());
    }

    #[test]
    fn test_validate_hvac() {
        let addr = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/hvac/boiler-01").unwrap();
        assert!(addr.validate().is_ok());

        let addr = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/hvac/invalid-01").unwrap();
        assert!(addr.validate().is_err());
    }

    #[test]
    fn test_validate_custom() {
        let addr = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/kitchen/fridge/pbj-sandwich").unwrap();
        assert!(addr.validate().is_ok());
    }

    #[test]
    fn test_parent() {
        let addr = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        assert_eq!(addr.parent(), "/usa/ny/brooklyn/ps-118/floor-02/mech");
    }

    #[test]
    fn test_guid() {
        let addr = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        let guid1 = addr.guid();
        let guid2 = addr.guid();
        assert_eq!(guid1, guid2); // Deterministic
        assert_eq!(guid1.len(), 64); // SHA-256 produces 256-bit (64 hex chars) hash
    }

    #[test]
    fn test_parts() {
        let addr = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
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
        let addr = ArxAddress::new("USA", "NY", "New York", "PS 118", "Floor 02", "Mech Room", "Boiler 01");
        assert_eq!(addr.path, "/usa/ny/new-york/ps-118/floor-02/mech-room/boiler-01");
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
            )).unwrap();
            assert!(addr.validate().is_ok(), "Failed validation for {}/{}", system, fixture);
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
            )).unwrap();
            assert!(addr.validate().is_err(), "Should fail validation for {}/{}", system, fixture);
        }
    }

    #[test]
    fn test_guid_stability() {
        // Test that same path produces same GUID
        let addr1 = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        let addr2 = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        assert_eq!(addr1.guid(), addr2.guid());
    }

    #[test]
    fn test_guid_uniqueness() {
        // Test that different paths produce different GUIDs
        let addr1 = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        let addr2 = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-02").unwrap();
        assert_ne!(addr1.guid(), addr2.guid());
    }

    #[test]
    fn test_guid_collision_guard() {
        // Verify that GUID generation is deterministic and unique per path
        // SHA-256 has extremely low collision probability, but we verify determinism
        let paths = vec![
            "/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01",
            "/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-02",
            "/usa/ny/brooklyn/ps-118/floor-02/kitchen/fridge/pbj-sandwich",
            "/usa/ca/san-francisco/office-building/floor-01/hvac/ahu-01",
        ];

        let mut guids = std::collections::HashSet::new();
        for path in &paths {
            let addr = ArxAddress::from_path(path).unwrap();
            let guid = addr.guid();
            
            // Verify determinism - same path should produce same GUID
            let addr2 = ArxAddress::from_path(path).unwrap();
            assert_eq!(addr.guid(), addr2.guid(), "GUID should be deterministic for path: {}", path);
            
            // Verify uniqueness - different paths should produce different GUIDs
            assert!(guids.insert(guid.clone()), "GUID collision detected for path: {}", path);
        }
    }

    #[test]
    fn test_invalid_path_rejected() {
        // Test that invalid paths are rejected
        assert!(ArxAddress::from_path("").is_err());
        assert!(ArxAddress::from_path("/usa").is_err());
        assert!(ArxAddress::from_path("/usa/ny").is_err());
        assert!(ArxAddress::from_path("/usa/ny/brooklyn").is_err());
        assert!(ArxAddress::from_path("/usa/ny/brooklyn/ps-118").is_err());
        assert!(ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02").is_err());
        assert!(ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech").is_err());
    }
}


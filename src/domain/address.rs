//! ArxOS Address System
//!
//! Provides hierarchical addressing for building components using a 7-part path format:
//! /country/state/city/building/floor/room/fixture
//!
//! Supports both standardized engineering systems (14 reserved) and custom items.

use anyhow::{bail, Result};
use serde::{Deserialize, Serialize};
use std::fmt;
use sha2::{Sha256, Digest};

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
            bail!("ArxAddress must have exactly 7 segments, got {}", parts.len());
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
            bail!("ArxAddress must have exactly 7 segments");
        }

        let system = parts[5]; // room / system (6th part, 0-indexed)

        if RESERVED_SYSTEMS.contains(&system) {
            let fixture = parts[6];
            // Validate fixture naming patterns for reserved systems
            match system {
                "hvac" => {
                    if !fixture.starts_with("boiler-") && !fixture.starts_with("ahu-") {
                        bail!("HVAC fixture must start with boiler- or ahu-");
                    }
                }
                "plumbing" => {
                    if !fixture.starts_with("valve-") && !fixture.starts_with("pump-") {
                        bail!("Plumbing fixture must start with valve- or pump-");
                    }
                }
                "electrical" => {
                    if !fixture.starts_with("panel-") && !fixture.starts_with("breaker-") {
                        bail!("Electrical fixture must start with panel- or breaker-");
                    }
                }
                "fire" => {
                    if !fixture.starts_with("sprinkler-") && !fixture.starts_with("alarm-") {
                        bail!("Fire fixture must start with sprinkler- or alarm-");
                    }
                }
                "lighting" => {
                    if !fixture.starts_with("fixture-") && !fixture.starts_with("control-") {
                        bail!("Lighting fixture must start with fixture- or control-");
                    }
                }
                "security" => {
                    if !fixture.starts_with("camera-") && !fixture.starts_with("access-") {
                        bail!("Security fixture must start with camera- or access-");
                    }
                }
                "elevators" => {
                    if !fixture.starts_with("car-") && !fixture.starts_with("control-") {
                        bail!("Elevator fixture must start with car- or control-");
                    }
                }
                "roof" => {
                    if !fixture.starts_with("unit-") && !fixture.starts_with("drain-") {
                        bail!("Roof fixture must start with unit- or drain-");
                    }
                }
                "windows" => {
                    if !fixture.starts_with("frame-") && !fixture.starts_with("glass-") {
                        bail!("Window fixture must start with frame- or glass-");
                    }
                }
                "doors" => {
                    if !fixture.starts_with("hinge-") && !fixture.starts_with("lock-") {
                        bail!("Door fixture must start with hinge- or lock-");
                    }
                }
                "structure" => {
                    if !fixture.starts_with("column-") && !fixture.starts_with("beam-") {
                        bail!("Structure fixture must start with column- or beam-");
                    }
                }
                "envelope" => {
                    if !fixture.starts_with("wall-") && !fixture.starts_with("insulation-") {
                        bail!("Envelope fixture must start with wall- or insulation-");
                    }
                }
                "it" => {
                    if !fixture.starts_with("switch-") && !fixture.starts_with("ap-") {
                        bail!("IT fixture must start with switch- or ap-");
                    }
                }
                "furniture" => {
                    if !fixture.starts_with("desk-") && !fixture.starts_with("chair-") {
                        bail!("Furniture fixture must start with desk- or chair-");
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
            bail!("ArxAddress must have exactly 7 segments");
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
}


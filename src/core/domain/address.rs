//! ArxOS Address System (ADR 0001)
//!
//! Hierarchical operational identity. Canonical form examples:
//! - `bldg.us.fl.tampa.dale-mabry.143677.s2/fl.2/rm.215`
//! - `bldg.lab.local.sample.duplex/fl.1/rm.a101`
//!
//! Dots are legal inside segments (`fl.2`, `panel.L1`). Paths are stored with a
//! leading `/` for historical compatibility; `from_path` accepts both forms.
//!
//! Legacy geo-style paths (`/usa/ny/brooklyn/...`) still parse for existing YAML.

use crate::error::ArxError;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fmt;

/// Reserved system names for standardized engineering components.
/// Includes ADR short roots (`elec`, `plumb`, `vert`) and legacy long names.
pub const RESERVED_SYSTEMS: [&str; 18] = [
    "hvac",       // boilers, AHUs
    "plumbing",   // valves, pumps (legacy)
    "plumb",      // ADR short root
    "electrical", // panels, breakers (legacy)
    "elec",       // ADR short root
    "fire",       // sprinklers, alarms
    "lighting",   // fixtures, controls
    "security",   // cameras, access
    "elevators",  // cars, controls (legacy)
    "vert",       // ADR vertical transport
    "roof",       // units, drains
    "windows",    // frames, glass
    "doors",      // hinges, locks
    "structure",  // columns, beams
    "struct",     // ADR short root
    "envelope",   // walls, insulation
    "it",         // switches, APs
    "furniture",  // desks, chairs
];

/// ArxOS Address — hierarchical operational identity (ADR 0001).
///
/// Stored path always has a leading `/` (e.g. `/bldg.lab.local.sample.x/fl.1`).
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(transparent)]
pub struct ArxAddress {
    pub path: String,
}

impl ArxAddress {
    /// Legacy geo-style constructor (7 optional segments). Prefer [`Self::from_segments`]
    /// or [`Self::lab_building_root`] for new ADR-shaped addresses.
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
        Self {
            path: format!("/{}", non_empty.join("/")),
        }
    }

    /// Build an address from ordered path segments (already semantic, will be sanitized).
    pub fn from_segments(segments: &[&str]) -> Result<Self> {
        let mut parts = Vec::with_capacity(segments.len());
        for seg in segments {
            let s = Self::sanitize_part(seg);
            if s.is_empty() {
                continue;
            }
            if !Self::is_valid_segment(&s) {
                return Err(ArxError::path_invalid(
                    &segments.join("/"),
                    &format!("Invalid address segment '{}'", seg),
                )
                .into());
            }
            parts.push(s);
        }
        if parts.is_empty() {
            return Err(ArxError::path_invalid("", "Path cannot be empty").into());
        }
        Ok(Self {
            path: format!("/{}", parts.join("/")),
        })
    }

    /// Deterministic lab/sample building root when no postal address is available (ADR 0001).
    ///
    /// Form: `bldg.lab.local.sample.<slug>`
    pub fn lab_building_root(sample_key: &str) -> Self {
        let slug = Self::stable_slug(sample_key);
        // Root is a single multi-dot segment.
        Self {
            path: format!("/bldg.lab.local.sample.{}", slug),
        }
    }

    /// Fully-qualified postal-derived building root (ADR 0001 §4).
    ///
    /// Prefer [`super::postal::postal_building_root_fields`] for full street simplification.
    /// This constructor applies basic sanitize only (no directional/suffix stripping).
    pub fn postal_building_root(
        country: &str,
        region: &str,
        city: &str,
        street: &str,
        number: &str,
        unit: Option<&str>,
    ) -> Self {
        let mut core = format!(
            "bldg.{}.{}.{}.{}-{}",
            Self::sanitize_part(country),
            Self::sanitize_part(region),
            Self::sanitize_part(city),
            Self::sanitize_part(street),
            Self::sanitize_part(number),
        );
        if let Some(u) = unit {
            let u = Self::sanitize_part(u);
            if !u.is_empty() {
                core.push('.');
                core.push_str(&u);
            }
        }
        Self {
            path: format!("/{}", core),
        }
    }

    /// Append one child segment (sanitized). Returns error if the child is invalid.
    pub fn join(&self, child: &str) -> Result<Self> {
        let seg = Self::sanitize_part(child);
        if !Self::is_valid_segment(&seg) {
            return Err(ArxError::path_invalid(
                child,
                "Invalid child address segment",
            )
            .into());
        }
        Ok(Self {
            path: format!("{}/{}", self.path.trim_end_matches('/'), seg),
        })
    }

    /// True if `self` is equal to `prefix` or is a strict descendant path.
    pub fn starts_with_address(&self, prefix: &ArxAddress) -> bool {
        let p = prefix.path.trim_end_matches('/');
        self.path == p || self.path.starts_with(&format!("{}/", p))
    }

    /// Parse a full path string into an ArxAddress.
    ///
    /// Accepts with or without a leading `/`. Rejects empty, `.`, `..`, and illegal chars.
    /// Dots are allowed inside segments (ADR 0001 §3).
    pub fn from_path(path: &str) -> Result<Self> {
        let clean = path.trim().trim_start_matches('/');
        if clean.is_empty() {
            return Err(ArxError::path_invalid(path, "Path cannot be empty").into());
        }
        let parts: Vec<&str> = clean.split('/').filter(|s| !s.is_empty()).collect();
        if parts.is_empty() {
            return Err(ArxError::path_invalid(path, "Path cannot be empty").into());
        }
        for part in &parts {
            if !Self::is_valid_segment(part) {
                return Err(ArxError::path_invalid(
                    path,
                    "Path segments must be lowercase alphanumeric with '-', '_', or '.' (no '..')",
                )
                .into());
            }
            // from_path accepts already-cased input but validate() enforces lowercase;
            // normalize: reject uppercase here for consistency with sanitize on write paths
            if part.chars().any(|c| c.is_ascii_uppercase()) {
                return Err(ArxError::path_invalid(
                    path,
                    "Path segments must be lowercase",
                )
                .into());
            }
        }
        Ok(Self {
            path: format!("/{}", parts.join("/")),
        })
    }

    /// Validate address format and reserved system rules.
    pub fn validate(&self) -> Result<(), AddressValidationError> {
        let parts: Vec<&str> = self
            .path
            .trim_start_matches('/')
            .split('/')
            .filter(|s| !s.is_empty())
            .collect();
        if parts.is_empty() {
            return Err(AddressValidationError::MissingSegments);
        }

        for part in &parts {
            if part.to_lowercase() != *part {
                return Err(AddressValidationError::NotLowercase {
                    part: part.to_string(),
                });
            }
            if !Self::is_valid_segment(part) {
                return Err(AddressValidationError::InvalidCharacters {
                    part: part.to_string(),
                });
            }
        }

        // Reserved system child naming (legacy prefixes + ADR dotted mnemonics)
        for (i, part) in parts.iter().enumerate() {
            if RESERVED_SYSTEMS.contains(part) && i + 1 < parts.len() {
                let fixture = parts[i + 1];
                if !Self::reserved_child_ok(part, fixture) {
                    return Err(AddressValidationError::ReservedSystemPrefixMismatch {
                        system: part.to_string(),
                        message: format!(
                            "Child '{}' under system '{}' does not match allowed prefixes",
                            fixture, part
                        ),
                    });
                }
            }
        }
        Ok(())
    }

    /// Whether a reserved-system child segment is acceptable (legacy or ADR form).
    fn reserved_child_ok(system: &str, fixture: &str) -> bool {
        // ADR dotted mnemonics: panel.l1, ahu.1, ckt.14, rec.7
        if let Some((head, _rest)) = fixture.split_once('.') {
            return match system {
                "hvac" => matches!(
                    head,
                    "boiler"
                        | "ahu"
                        | "vav"
                        | "chiller"
                        | "fan"
                        | "coil"
                        | "diff"
                        | "pump"
                        | "exhaust"
                ),
                "electrical" | "elec" => matches!(
                    head,
                    "panel" | "breaker" | "ckt" | "jbox" | "rec" | "ltg" | "sw" | "xfmr" | "mdp"
                ),
                "plumbing" | "plumb" => matches!(
                    head,
                    "valve" | "pump" | "fixture" | "sink" | "wc" | "urinal" | "main" | "ris" | "branch"
                ),
                "fire" => matches!(head, "sprinkler" | "alarm" | "riser" | "head" | "panel" | "zone" | "device"),
                "lighting" => matches!(head, "fixture" | "control" | "ltg"),
                "security" => matches!(head, "camera" | "access" | "panel"),
                "elevators" | "vert" => matches!(head, "car" | "control" | "elev" | "escalator" | "stair"),
                "roof" => matches!(head, "unit" | "drain"),
                "windows" => matches!(head, "frame" | "glass" | "win"),
                "doors" => matches!(head, "hinge" | "lock" | "door"),
                "structure" | "struct" => matches!(head, "column" | "beam" | "col" | "slab"),
                "envelope" => matches!(head, "wall" | "insulation" | "win" | "door" | "roof"),
                "it" => matches!(head, "switch" | "ap" | "rack" | "controller"),
                "furniture" => matches!(head, "desk" | "chair"),
                _ => true,
            };
        }

        // Legacy hyphen prefixes
        match system {
            "hvac" => {
                fixture.starts_with("boiler-")
                    || fixture.starts_with("ahu-")
                    || fixture.starts_with("vav-")
            }
            "plumbing" | "plumb" => {
                fixture.starts_with("valve-") || fixture.starts_with("pump-")
            }
            "electrical" | "elec" => {
                fixture.starts_with("panel-") || fixture.starts_with("breaker-")
            }
            "fire" => fixture.starts_with("sprinkler-") || fixture.starts_with("alarm-"),
            "lighting" => fixture.starts_with("fixture-") || fixture.starts_with("control-"),
            "security" => fixture.starts_with("camera-") || fixture.starts_with("access-"),
            "elevators" | "vert" => fixture.starts_with("car-") || fixture.starts_with("control-"),
            "roof" => fixture.starts_with("unit-") || fixture.starts_with("drain-"),
            "windows" => fixture.starts_with("frame-") || fixture.starts_with("glass-"),
            "doors" => fixture.starts_with("hinge-") || fixture.starts_with("lock-"),
            "structure" | "struct" => {
                fixture.starts_with("column-") || fixture.starts_with("beam-")
            }
            "envelope" => fixture.starts_with("wall-") || fixture.starts_with("insulation-"),
            "it" => fixture.starts_with("switch-") || fixture.starts_with("ap-"),
            "furniture" => fixture.starts_with("desk-") || fixture.starts_with("chair-"),
            _ => true,
        }
    }

    /// Segment charset + traversal safety (ADR 0001: dots allowed).
    pub fn is_valid_segment(part: &str) -> bool {
        if part.is_empty() || part == "." || part == ".." {
            return false;
        }
        if part.starts_with('.') || part.ends_with('.') {
            return false;
        }
        if part.contains("..") {
            return false;
        }
        part.chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_' || c == '.')
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
    /// (see `docs/reference/identity.md`). This helper is for address-keyed fixtures only.
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

    /// Sanitize a path part for use in addresses.
    /// Lowercase; keep alphanumerics, `-`, `_`, `.`; other chars become `-`.
    pub fn sanitize_part(part: &str) -> String {
        let mapped: String = part
            .to_lowercase()
            .chars()
            .map(|c| {
                if c.is_ascii_alphanumeric() || c == '-' || c == '_' || c == '.' {
                    c
                } else {
                    '-'
                }
            })
            .collect();
        // Collapse consecutive hyphens; strip leading/trailing hyphens (not dots mid-token).
        let collapsed = mapped
            .split('-')
            .filter(|s| !s.is_empty())
            .collect::<Vec<_>>()
            .join("-");
        // Reject pure-dot garbage after collapse
        if collapsed == "." || collapsed == ".." || collapsed.is_empty() {
            return String::new();
        }
        collapsed
            .trim_matches('.')
            .trim_matches('-')
            .to_string()
    }

    /// Stable lowercase slug for lab roots and equipment leaves.
    pub fn stable_slug(input: &str) -> String {
        let s = Self::sanitize_part(input);
        if s.is_empty() {
            // Fallback: short hash of raw input for GlobalId-like opaque names
            let mut hasher = Sha256::new();
            hasher.update(input.as_bytes());
            let hex = format!("{:x}", hasher.finalize());
            return hex[..12].to_string();
        }
        // Prefer short slug; if still very long (e.g. IFC-ish), hash
        if s.len() > 48 || s.chars().filter(|c| c.is_ascii_uppercase()).count() > 0 {
            // already lowercased by sanitize
        }
        if s.len() > 48 {
            let mut hasher = Sha256::new();
            hasher.update(s.as_bytes());
            let hex = format!("{:x}", hasher.finalize());
            return hex[..12].to_string();
        }
        s
    }

    /// Floor segment `fl.<n>` from storey name + index.
    pub fn floor_segment(name: &str, index: usize) -> String {
        // Prefer last contiguous digit group (e.g. "Level 2" → 2, "Floor 12" → 12)
        let mut last_group = String::new();
        let mut cur = String::new();
        for c in name.chars() {
            if c.is_ascii_digit() {
                cur.push(c);
            } else if !cur.is_empty() {
                last_group = cur.clone();
                cur.clear();
            }
        }
        if !cur.is_empty() {
            last_group = cur;
        }
        if !last_group.is_empty() && last_group.len() <= 3 {
            if let Ok(n) = last_group.parse::<u32>() {
                return format!("fl.{}", n);
            }
        }
        format!("fl.{}", index)
    }

    /// Room segment `rm.<slug>`.
    pub fn room_segment(name: &str) -> String {
        format!("rm.{}", Self::stable_slug(name))
    }

    /// Equipment / fixture leaf segment from name.
    pub fn equipment_segment(name: &str) -> String {
        Self::stable_slug(name)
    }
}

/// Detailed validation errors and warnings that can occur when checking the syntax 
/// and semantic rules of an [`ArxAddress`].
#[derive(Debug, Clone, thiserror::Error, PartialEq, Eq)]
pub enum AddressValidationError {
    /// A segment contains uppercase characters, violating lowercase-only naming.
    #[error("Segment '{part}' must be lowercase")]
    NotLowercase { part: String },
    /// A segment contains characters outside the allowed set (alnum, `-`, `_`, `.`).
    #[error("Segment '{part}' contains invalid characters")]
    InvalidCharacters { part: String },
    /// Legacy: path did not start with `/` (no longer raised — both forms accepted).
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
        // Leading slash optional — bare segments are valid
        assert!(ArxAddress::from_path("usa/ny").is_ok());
        assert!(ArxAddress::from_path("/usa/ny/../invalid").is_err());
        assert!(ArxAddress::from_path("/usa/ny/special@char").is_err());
    }

    #[test]
    fn test_adr_dots_and_bldg_root() {
        let root = "bldg.us.fl.tampa.dale-mabry.143677.s2";
        let addr = ArxAddress::from_path(&format!("{}/fl.2/rm.215/panel.l1", root)).unwrap();
        assert!(addr.validate().is_ok());
        assert_eq!(
            addr.path,
            "/bldg.us.fl.tampa.dale-mabry.143677.s2/fl.2/rm.215/panel.l1"
        );

        let lab = ArxAddress::lab_building_root("Duplex A");
        assert!(lab.path.starts_with("/bldg.lab.local.sample."));
        let floor = lab.join("fl.1").unwrap();
        let room = floor.join("rm.a101").unwrap();
        assert!(room.starts_with_address(&lab));
        assert!(room.validate().is_ok());
    }

    #[test]
    fn test_elec_dotted_mnemonic() {
        let addr = ArxAddress::from_path(
            "bldg.lab.local.sample.hq/elec/panel.l1/ckt.14/rec.7",
        )
        .unwrap();
        assert!(addr.validate().is_ok());
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
        assert!(ArxAddress::from_path("").is_err());
        assert!(ArxAddress::from_path("/").is_err());
        assert!(ArxAddress::from_path("/usa/ny/special@char").is_err());
        assert!(ArxAddress::from_path("/usa/ny/foo..bar").is_err());
    }

    #[test]
    fn test_floor_room_segments() {
        assert_eq!(ArxAddress::floor_segment("Level 2", 0), "fl.2");
        assert_eq!(ArxAddress::floor_segment("Roof", 3), "fl.3");
        assert_eq!(ArxAddress::room_segment("A101"), "rm.a101");
    }
}

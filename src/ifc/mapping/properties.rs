//! Free-form property bag normalization for IFC import/export (Phase 3).
//!
//! Native IFC import stores Pset values as `PsetName:PropertyName`. Domain
//! models should hold **clean** keys for Arx free-form Psets so YAML is stable
//! and re-export does not double-prefix.

use std::collections::HashMap;

use super::{
    pset_prop_key, PROP_ARX_ID, PROP_ENTITY_KIND, PSET_ARX_BUILDING, PSET_ARX_EQUIPMENT,
    PSET_ARX_FLOOR, PSET_ARX_IDENTITY, PSET_ARX_LIDAR, PSET_ARX_ROOM,
};

/// Arx free-form Psets whose properties become clean domain keys on import.
pub const ARX_FREEFORM_PSETS: &[&str] = &[
    PSET_ARX_ROOM,
    PSET_ARX_EQUIPMENT,
    PSET_ARX_FLOOR,
    PSET_ARX_BUILDING,
];

/// Psets fully consumed into typed fields (must not remain in free-form bags).
pub const ARX_CONSUMED_PSETS: &[&str] = &[PSET_ARX_IDENTITY, PSET_ARX_LIDAR];

/// Structural key written into room/equipment free-form bags for wing grouping.
pub const PROP_ARX_WING: &str = "ArxWing";

/// Alternate wing key sometimes used in older data.
pub const PROP_WING: &str = "Wing";

/// Normalize an imported property bag for domain / YAML storage.
///
/// - Strips prefixes for known Arx free-form Psets (`max_occupancy`, not
///   `Pset_ArxRoomProperties:max_occupancy`).
/// - Removes leftovers from consumed Psets (identity, LiDAR).
/// - Leaves third-party `Pset_*:…` keys prefixed so foreign metadata is not lost.
/// - Collapses accidental double-prefixes from older re-exports.
///
/// Call **after** `apply_identity_on_import` and `apply_lidar_on_import`, which
/// still expect the raw `PsetName:Property` keys produced by the resolver.
pub fn normalize_imported_properties(properties: &mut HashMap<String, String>) {
    let old = std::mem::take(properties);
    let mut next = HashMap::with_capacity(old.len());

    for (key, value) in old {
        if is_consumed_pset_key(&key) {
            continue;
        }

        if let Some(clean) = strip_arx_freeform_prefix(&key) {
            // Prefer first occurrence; later duplicates are ignored
            next.entry(clean).or_insert(value);
            continue;
        }

        next.insert(key, value);
    }

    *properties = next;
}

/// Prepare free-form properties for export into a named Arx Pset.
///
/// - Uses clean property names (strips target / any free-form Arx prefix).
/// - Drops keys that belong to identity / LiDAR (exported via dedicated Psets).
/// - Drops empty keys.
pub fn properties_for_export(
    properties: &HashMap<String, String>,
    _target_pset: &str,
) -> HashMap<String, String> {
    let mut out = HashMap::new();

    for (key, value) in properties {
        if key.is_empty() {
            continue;
        }
        if is_consumed_pset_key(key) || is_consumed_clean_key(key) {
            continue;
        }

        let clean = strip_arx_freeform_prefix(key).unwrap_or_else(|| key.clone());
        if clean.is_empty() || is_consumed_clean_key(&clean) {
            continue;
        }

        out.entry(clean).or_insert_with(|| value.clone());
    }

    out
}

/// Look up wing name from a (possibly mixed) property bag.
///
/// Accepts clean keys and legacy prefixed keys for robustness.
pub fn wing_name_from_properties(properties: &HashMap<String, String>) -> Option<String> {
    properties
        .get(PROP_ARX_WING)
        .or_else(|| properties.get(PROP_WING))
        .or_else(|| properties.get(&pset_prop_key(PSET_ARX_ROOM, PROP_ARX_WING)))
        .or_else(|| properties.get(&pset_prop_key(PSET_ARX_ROOM, PROP_WING)))
        .or_else(|| properties.get(&pset_prop_key(PSET_ARX_EQUIPMENT, PROP_ARX_WING)))
        .or_else(|| properties.get(&pset_prop_key(PSET_ARX_EQUIPMENT, PROP_WING)))
        .cloned()
}

fn is_consumed_pset_key(key: &str) -> bool {
    for pset in ARX_CONSUMED_PSETS {
        let prefix = format!("{}:", pset);
        if key == *pset || key.starts_with(&prefix) {
            return true;
        }
    }
    false
}

fn is_consumed_clean_key(key: &str) -> bool {
    // Identity / LiDAR property names if they leaked into free-form bags
    matches!(
        key,
        PROP_ARX_ID
            | PROP_ENTITY_KIND
            | "PointCount"
            | "ConfidenceScore"
            | "LastScanTimestamp"
            | "ClassificationHeuristic"
    )
}

/// Strip known Arx free-form Pset prefixes (including stacked prefixes).
fn strip_arx_freeform_prefix(key: &str) -> Option<String> {
    let mut current = key;
    let mut stripped = false;

    loop {
        let mut matched = false;
        for pset in ARX_FREEFORM_PSETS {
            let prefix = format!("{}:", pset);
            if let Some(rest) = current.strip_prefix(&prefix) {
                current = rest;
                stripped = true;
                matched = true;
                break;
            }
        }
        if !matched {
            break;
        }
    }

    if stripped {
        Some(current.to_string())
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn normalize_strips_arx_freeform_prefixes() {
        let mut bag = HashMap::new();
        bag.insert(
            pset_prop_key(PSET_ARX_ROOM, "max_occupancy"),
            "20".to_string(),
        );
        bag.insert(
            pset_prop_key(PSET_ARX_ROOM, PROP_ARX_WING),
            "East".to_string(),
        );
        bag.insert(
            pset_prop_key(PSET_ARX_IDENTITY, PROP_ARX_ID),
            "uuid-here".to_string(),
        );
        bag.insert("Pset_Other:Foo".to_string(), "bar".to_string());

        normalize_imported_properties(&mut bag);

        assert_eq!(bag.get("max_occupancy").map(String::as_str), Some("20"));
        assert_eq!(bag.get(PROP_ARX_WING).map(String::as_str), Some("East"));
        assert!(!bag.keys().any(|k| k.starts_with(PSET_ARX_IDENTITY)));
        assert_eq!(
            bag.get("Pset_Other:Foo").map(String::as_str),
            Some("bar"),
            "third-party psets stay prefixed"
        );
    }

    #[test]
    fn normalize_collapses_double_prefix() {
        let mut bag = HashMap::new();
        bag.insert(
            format!("{}:{}:brand", PSET_ARX_EQUIPMENT, PSET_ARX_EQUIPMENT),
            "Epson".to_string(),
        );
        normalize_imported_properties(&mut bag);
        assert_eq!(bag.get("brand").map(String::as_str), Some("Epson"));
    }

    #[test]
    fn export_uses_clean_keys_and_drops_consumed() {
        let mut bag = HashMap::new();
        bag.insert("brand".to_string(), "Epson".to_string());
        bag.insert(pset_prop_key(PSET_ARX_EQUIPMENT, "model"), "X1".to_string());
        bag.insert(
            pset_prop_key(PSET_ARX_IDENTITY, PROP_ARX_ID),
            "uuid".to_string(),
        );
        bag.insert(PROP_ARX_ID.to_string(), "uuid2".to_string());

        let out = properties_for_export(&bag, PSET_ARX_EQUIPMENT);
        assert_eq!(out.get("brand").map(String::as_str), Some("Epson"));
        assert_eq!(out.get("model").map(String::as_str), Some("X1"));
        assert!(!out.contains_key(PROP_ARX_ID));
        assert!(!out.keys().any(|k| k.contains(PSET_ARX_IDENTITY)));
    }

    #[test]
    fn wing_lookup_accepts_clean_and_legacy() {
        let mut clean = HashMap::new();
        clean.insert(PROP_ARX_WING.to_string(), "Main".to_string());
        assert_eq!(wing_name_from_properties(&clean).as_deref(), Some("Main"));

        let mut legacy = HashMap::new();
        legacy.insert(
            pset_prop_key(PSET_ARX_ROOM, PROP_ARX_WING),
            "East".to_string(),
        );
        assert_eq!(wing_name_from_properties(&legacy).as_deref(), Some("East"));
    }
}

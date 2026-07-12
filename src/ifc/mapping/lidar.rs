//! LiDAR enrichment ↔ `Pset_ArxLidarEnrichment` mapping (L1).

use std::collections::HashMap;

use chrono::{DateTime, Utc};

use crate::core::LidarEnrichment;

use super::{pset_prop_key, PSET_ARX_LIDAR};

/// Number of LiDAR points associated with the entity.
pub const PROP_POINT_COUNT: &str = "PointCount";
/// Classification confidence in \[0.0, 1.0\].
pub const PROP_CONFIDENCE_SCORE: &str = "ConfidenceScore";
/// ISO-8601 timestamp of last scan (optional).
pub const PROP_LAST_SCAN_TIMESTAMP: &str = "LastScanTimestamp";
/// Heuristic / algorithm label (optional).
pub const PROP_CLASSIFICATION_HEURISTIC: &str = "ClassificationHeuristic";

const LIDAR_PROPS: &[&str] = &[
    PROP_POINT_COUNT,
    PROP_CONFIDENCE_SCORE,
    PROP_LAST_SCAN_TIMESTAMP,
    PROP_CLASSIFICATION_HEURISTIC,
];

/// Convert typed enrichment into a property map for IFC export.
///
/// All values are strings (IFC single-value labels); optional fields are omitted
/// when `None`.
pub fn lidar_enrichment_to_pset(enrichment: &LidarEnrichment) -> HashMap<String, String> {
    let mut map = HashMap::new();
    map.insert(
        PROP_POINT_COUNT.to_string(),
        enrichment.point_count.to_string(),
    );
    map.insert(
        PROP_CONFIDENCE_SCORE.to_string(),
        format_f64(enrichment.confidence_score),
    );
    if let Some(ts) = enrichment.last_scan_timestamp {
        map.insert(
            PROP_LAST_SCAN_TIMESTAMP.to_string(),
            ts.to_rfc3339(),
        );
    }
    if let Some(ref heuristic) = enrichment.classification_heuristic {
        if !heuristic.is_empty() {
            map.insert(
                PROP_CLASSIFICATION_HEURISTIC.to_string(),
                heuristic.clone(),
            );
        }
    }
    map
}

/// Extract typed enrichment from a properties bag (import path).
///
/// Looks for keys `Pset_ArxLidarEnrichment:PropertyName`. When any LiDAR key is
/// present, builds `LidarEnrichment` and **removes** those keys from `properties`
/// so they are not double-stored as free-form metadata.
///
/// Returns `None` if no LiDAR Pset keys are found.
pub fn take_lidar_enrichment_from_properties(
    properties: &mut HashMap<String, String>,
) -> Option<LidarEnrichment> {
    let has_any = LIDAR_PROPS
        .iter()
        .any(|p| properties.contains_key(&pset_prop_key(PSET_ARX_LIDAR, p)));
    if !has_any {
        return None;
    }

    let point_count = take_prop(properties, PROP_POINT_COUNT)
        .and_then(|s| s.parse::<usize>().ok())
        .unwrap_or(0);

    let confidence_score = take_prop(properties, PROP_CONFIDENCE_SCORE)
        .and_then(|s| s.parse::<f64>().ok())
        .unwrap_or(0.0);

    let last_scan_timestamp = take_prop(properties, PROP_LAST_SCAN_TIMESTAMP)
        .and_then(|s| parse_timestamp(&s));

    let classification_heuristic = take_prop(properties, PROP_CLASSIFICATION_HEURISTIC)
        .filter(|s| !s.is_empty());

    // Drop any leftover keys with the LiDAR pset prefix (forward compatibility)
    let prefix = format!("{}:", PSET_ARX_LIDAR);
    properties.retain(|k, _| !k.starts_with(&prefix));

    Some(LidarEnrichment {
        point_count,
        confidence_score,
        last_scan_timestamp,
        classification_heuristic,
    })
}

/// Apply LiDAR enrichment on import when the Pset is present.
pub fn apply_lidar_on_import(
    lidar_enrichment: &mut Option<LidarEnrichment>,
    properties: &mut HashMap<String, String>,
) {
    if let Some(enrichment) = take_lidar_enrichment_from_properties(properties) {
        *lidar_enrichment = Some(enrichment);
    }
}

/// Prefer existing enrichment when incoming is `None` (re-import merge helper).
pub fn prefer_existing_lidar(
    existing: &Option<LidarEnrichment>,
    incoming: &Option<LidarEnrichment>,
) -> Option<LidarEnrichment> {
    match (existing, incoming) {
        (_, Some(inc)) => Some(inc.clone()),
        (Some(ex), None) => Some(ex.clone()),
        (None, None) => None,
    }
}

fn take_prop(properties: &mut HashMap<String, String>, prop: &str) -> Option<String> {
    properties.remove(&pset_prop_key(PSET_ARX_LIDAR, prop))
}

fn format_f64(v: f64) -> String {
    // Stable, parseable representation without excessive trailing zeros noise
    if v.fract() == 0.0 && v.abs() < 1e15 {
        format!("{:.1}", v)
    } else {
        // Use enough precision for confidence scores
        let s = format!("{:.6}", v);
        s.trim_end_matches('0').trim_end_matches('.').to_string()
    }
}

fn parse_timestamp(s: &str) -> Option<DateTime<Utc>> {
    DateTime::parse_from_rfc3339(s)
        .map(|dt| dt.with_timezone(&Utc))
        .ok()
        .or_else(|| DateTime::parse_from_str(s, "%Y-%m-%dT%H:%M:%S%.f%z")
            .map(|dt| dt.with_timezone(&Utc))
            .ok())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_enrichment() -> LidarEnrichment {
        LidarEnrichment {
            point_count: 4200,
            confidence_score: 0.9,
            last_scan_timestamp: Some(
                DateTime::parse_from_rfc3339("2026-03-15T12:00:00Z")
                    .unwrap()
                    .with_timezone(&Utc),
            ),
            classification_heuristic: Some("occupancy_component_v1".to_string()),
        }
    }

    #[test]
    fn roundtrip_via_property_bag() {
        let original = sample_enrichment();
        let pset = lidar_enrichment_to_pset(&original);

        // Simulate native import key prefixing
        let mut bag = HashMap::new();
        for (k, v) in pset {
            bag.insert(pset_prop_key(PSET_ARX_LIDAR, &k), v);
        }
        bag.insert("other".to_string(), "keep".to_string());

        let restored = take_lidar_enrichment_from_properties(&mut bag).expect("enrichment");
        assert_eq!(restored.point_count, 4200);
        assert!((restored.confidence_score - 0.9).abs() < 1e-6);
        assert_eq!(
            restored.classification_heuristic.as_deref(),
            Some("occupancy_component_v1")
        );
        assert!(restored.last_scan_timestamp.is_some());
        assert_eq!(bag.get("other").map(String::as_str), Some("keep"));
        assert!(!bag.keys().any(|k| k.starts_with(PSET_ARX_LIDAR)));
    }

    #[test]
    fn missing_pset_returns_none() {
        let mut bag = HashMap::new();
        bag.insert("foo".to_string(), "bar".to_string());
        assert!(take_lidar_enrichment_from_properties(&mut bag).is_none());
        assert_eq!(bag.len(), 1);
    }

    #[test]
    fn prefer_existing_when_incoming_none() {
        let existing = Some(sample_enrichment());
        let merged = prefer_existing_lidar(&existing, &None);
        assert_eq!(merged.as_ref().map(|e| e.point_count), Some(4200));

        let incoming = Some(LidarEnrichment {
            point_count: 10,
            confidence_score: 0.5,
            last_scan_timestamp: None,
            classification_heuristic: None,
        });
        let merged = prefer_existing_lidar(&existing, &incoming);
        assert_eq!(merged.as_ref().map(|e| e.point_count), Some(10));
    }
}

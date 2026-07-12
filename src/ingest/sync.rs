//! Portable Building sync envelope for PWA / agent / CLI interchange.
//!
//! Single JSON shape used by WASM localStorage, future agent push/pull, and tests:
//!
//! ```json
//! {
//!   "schema_version": 1,
//!   "source": "ifc",
//!   "updated_at": "2026-07-12T00:00:00Z",
//!   "building": { ... },
//!   "report": ["Fidelity: L2", ...]
//! }
//! ```

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

use crate::core::Building;
use crate::ifc::mapping::{merge_building_with_policy, MergePolicy};
use crate::ingest::import::{finalize_ingest, IngestOptions, IngestResult, IngestSource};
use crate::validation::validate_building;

/// Current envelope schema version (bump on breaking JSON changes).
pub const SYNC_SCHEMA_VERSION: u32 = 1;

/// localStorage key for the last imported / active building envelope.
pub const STORAGE_KEY_ACTIVE_BUILDING: &str = "arxos_active_building_v1";

/// Legacy key used by earlier PWA builds (still readable).
pub const STORAGE_KEY_LEGACY_BUILDING: &str = "last_imported_building";

/// Source label inside the sync envelope.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(rename_all = "lowercase")]
pub enum SyncSource {
    #[default]
    Unknown,
    Ifc,
    Lidar,
    Text,
    Merge,
    Wasm,
}

impl From<IngestSource> for SyncSource {
    fn from(s: IngestSource) -> Self {
        match s {
            IngestSource::Ifc => SyncSource::Ifc,
            IngestSource::Lidar => SyncSource::Lidar,
            IngestSource::Text => SyncSource::Text,
        }
    }
}

/// Versioned portable building document.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingSyncEnvelope {
    pub schema_version: u32,
    pub source: SyncSource,
    pub updated_at: DateTime<Utc>,
    pub building: Building,
    /// Human-readable report lines (merge, validation, fidelity).
    #[serde(default)]
    pub report: Vec<String>,
}

impl BuildingSyncEnvelope {
    pub fn new(building: Building, source: SyncSource, report: Vec<String>) -> Self {
        Self {
            schema_version: SYNC_SCHEMA_VERSION,
            source,
            updated_at: Utc::now(),
            building,
            report,
        }
    }

    pub fn from_ingest(result: IngestResult) -> Self {
        let source = SyncSource::from(result.source);
        let report = result.summary_lines();
        Self::new(result.building, source, report)
    }

    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string(self)
    }

    pub fn to_json_pretty(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(self)
    }

    pub fn from_json(json: &str) -> Result<Self, String> {
        // Prefer full envelope; fall back to bare Building for legacy PWA storage
        if let Ok(env) = serde_json::from_str::<BuildingSyncEnvelope>(json) {
            return Ok(env);
        }
        let building: Building = serde_json::from_str(json)
            .map_err(|e| format!("invalid building/sync JSON: {}", e))?;
        Ok(Self::new(
            building,
            SyncSource::Unknown,
            vec!["legacy bare Building JSON".into()],
        ))
    }
}

/// Wrap a building after validation into a sync envelope.
pub fn building_to_envelope(building: Building, source: SyncSource) -> BuildingSyncEnvelope {
    let validation = validate_building(&building);
    let mut report = validation.summary_lines();
    report.insert(0, format!("source={:?}", source));
    BuildingSyncEnvelope::new(building, source, report)
}

/// Merge two envelope JSON strings (incoming into existing) with IFC-style policy.
///
/// Returns a new envelope JSON. Used by PWA multi-device sync and agent reconcile.
pub fn merge_sync_json(existing_json: &str, incoming_json: &str) -> Result<String, String> {
    let existing = BuildingSyncEnvelope::from_json(existing_json)?;
    let incoming = BuildingSyncEnvelope::from_json(incoming_json)?;
    let merge = merge_building_with_policy(
        &existing.building,
        incoming.building,
        &MergePolicy::ifc(),
    );
    let mut report = vec![
        "sync merge (IFC policy)".to_string(),
        format!(
            "rooms {} matched / {} added",
            merge.stats.rooms_matched, merge.stats.rooms_added
        ),
    ];
    for w in &merge.warnings {
        report.push(format!("[{}] {}", w.code, w.message));
    }
    let validation = validate_building(&merge.building);
    report.extend(validation.summary_lines());
    let env = BuildingSyncEnvelope::new(merge.building, SyncSource::Merge, report);
    env.to_json().map_err(|e| e.to_string())
}

/// Apply text script to envelope JSON; returns updated envelope JSON.
pub fn apply_text_to_sync_json(envelope_json: &str, script: &str) -> Result<String, String> {
    let mut env = BuildingSyncEnvelope::from_json(envelope_json)?;
    let edit_report = crate::ingest::text::apply_text_script(&mut env.building, script)
        .map_err(|e| e.to_string())?;
    let result = finalize_ingest(
        env.building,
        IngestSource::Text,
        IngestOptions {
            validate: true,
            existing: None,
            policy: None,
        },
    );
    let mut report = edit_report.messages;
    report.extend(result.summary_lines());
    let out = BuildingSyncEnvelope::new(result.building, SyncSource::Text, report);
    out.to_json().map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{Building, Floor, Room, RoomType, Wing};

    #[test]
    fn envelope_roundtrip_and_text_edit() {
        let mut b = Building::new("HQ".into(), "/hq".into());
        let mut floor = Floor::new("F0".into(), 0);
        let mut wing = Wing::new("Main".into());
        wing.add_room(Room::new("R1".into(), RoomType::Office));
        floor.add_wing(wing);
        b.add_floor(floor);

        let env = building_to_envelope(b, SyncSource::Text);
        let json = env.to_json().unwrap();
        let parsed = BuildingSyncEnvelope::from_json(&json).unwrap();
        assert_eq!(parsed.building.name, "HQ");

        let updated = apply_text_to_sync_json(
            &json,
            r#"add room Lab floor=0 type=laboratory
               set room Lab finish=epoxy"#,
        )
        .unwrap();
        let env2 = BuildingSyncEnvelope::from_json(&updated).unwrap();
        let lab = env2
            .building
            .floors[0]
            .wings[0]
            .rooms
            .iter()
            .find(|r| r.name == "Lab")
            .expect("Lab");
        assert_eq!(lab.properties.get("finish").map(String::as_str), Some("epoxy"));
    }

    #[test]
    fn legacy_bare_building_json() {
        let b = Building::new("Legacy".into(), "/l".into());
        let bare = serde_json::to_string(&b).unwrap();
        let env = BuildingSyncEnvelope::from_json(&bare).unwrap();
        assert_eq!(env.building.name, "Legacy");
        assert_eq!(env.schema_version, SYNC_SCHEMA_VERSION);
    }
}

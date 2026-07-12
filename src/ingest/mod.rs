//! Shared multi-source ingest: merge, validate, import orchestration.
//!
//! All adapters (IFC, LiDAR, text/AR) should finish through this module
//! so merge policy and validation stay consistent.

mod import;
mod sync;
pub mod text;

pub use import::{
    finalize_ingest, import_ifc_path, import_lidar_path, IngestOptions, IngestResult, IngestSource,
};
pub use sync::{
    apply_text_to_sync_json, building_to_envelope, merge_sync_json, BuildingSyncEnvelope,
    SyncSource, STORAGE_KEY_ACTIVE_BUILDING, STORAGE_KEY_LEGACY_BUILDING, SYNC_SCHEMA_VERSION,
};
pub use text::{
    apply_text_edits, apply_text_script, parse_text_line, parse_text_script, TextEdit,
    TextEditReport,
};

// Re-export merge / report types for a single ingest entry surface
pub use crate::ifc::mapping::{
    merge_building, merge_building_with_policy, MergePolicy, MergeResult, MergeSource, MergeStats,
    FidelityLevel, LossReport,
};
pub use crate::validation::{validate_building, BuildingValidationReport};

/// Apply a text/AR script to a building and run the standard finalize path.
pub fn ingest_text_script(
    mut building: Building,
    script: &str,
    validate: bool,
) -> anyhow::Result<IngestResult> {
    let edit_report = text::apply_text_script(&mut building, script)?;
    let mut result = finalize_ingest(
        building,
        IngestSource::Text,
        IngestOptions {
            validate,
            existing: None,
            policy: None,
        },
    );
    for msg in edit_report.messages {
        result.report.warn("text_edit", msg);
    }
    Ok(result)
}

// Need Building in scope for ingest_text_script signature
use crate::core::Building;

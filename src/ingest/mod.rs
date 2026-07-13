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
    merge_building, merge_building_with_policy, FidelityLevel, LossReport, MergePolicy,
    MergeResult, MergeSource, MergeStats,
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

/// Finalize an in-memory Building mutation and write durable SSOT.
///
/// Pipeline: `finalize_ingest(Text, validate)` → hard-fail on validation errors
/// → `PersistenceManager` save (optional Git commit).
///
/// All interactive/CRUD mutators should use this instead of writing YAML directly.
pub fn persist_building(
    building: Building,
    commit: bool,
    message: Option<&str>,
) -> Result<Building, Box<dyn std::error::Error>> {
    let result = finalize_ingest(
        building,
        IngestSource::Text,
        IngestOptions {
            validate: true,
            existing: None,
            policy: None,
        },
    );

    if result.validation.has_errors() {
        let details: Vec<String> = result
            .validation
            .errors()
            .map(|e| match &e.field {
                Some(f) => format!("{}: {}", f, e.message),
                None => e.message.clone(),
            })
            .collect();
        return Err(format!(
            "Building validation failed ({} error(s)): {}",
            details.len(),
            details.join("; ")
        )
        .into());
    }

    let pm = crate::persistence::PersistenceManager::from_cwd()?;
    if commit {
        pm.save_and_commit(&result.building, message)?;
    } else {
        // Already hard-gated above; skip second validate.
        pm.save_building_unchecked(&result.building)?;
    }

    Ok(result.building)
}

/// Like [`persist_building`], but writes under an explicit project root (no process cwd mutation).
pub fn persist_building_at(
    base: impl AsRef<std::path::Path>,
    building: Building,
    commit: bool,
    message: Option<&str>,
) -> Result<Building, Box<dyn std::error::Error>> {
    let result = finalize_ingest(
        building,
        IngestSource::Text,
        IngestOptions {
            validate: true,
            existing: None,
            policy: None,
        },
    );

    if result.validation.has_errors() {
        let details: Vec<String> = result
            .validation
            .errors()
            .map(|e| match &e.field {
                Some(f) => format!("{}: {}", f, e.message),
                None => e.message.clone(),
            })
            .collect();
        return Err(format!(
            "Building validation failed ({} error(s)): {}",
            details.len(),
            details.join("; ")
        )
        .into());
    }

    let pm = crate::persistence::PersistenceManager::at(base.as_ref());
    if commit {
        pm.save_and_commit(&result.building, message)?;
    } else {
        pm.save_building_unchecked(&result.building)?;
    }

    Ok(result.building)
}

// Need Building in scope for ingest helpers
use crate::core::Building;

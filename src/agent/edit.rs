//! Text/AR script apply via the ingest spine (Batch B4: `edit.apply`).
//!
//! Thin wrapper: load YAML → `apply_text_script` → `finalize_ingest` → hard-gate → save.
//! No second mutation path.

use std::path::Path;

use anyhow::{anyhow, Result};
use serde::Serialize;

use crate::ingest::{
    apply_text_script, finalize_ingest, IngestOptions, IngestSource,
};
use crate::persistence::{load_building_at, save_building_at, BUILDING_YAML};

/// JSON result for `edit.apply`.
#[derive(Debug, Serialize)]
pub struct EditApplyResult {
    pub building_name: String,
    pub yaml_path: String,
    pub applied: usize,
    pub floors: usize,
    pub rooms: usize,
    pub equipment: usize,
    /// Edit messages + finalize LossReport / validation summary lines.
    pub report_summary: Vec<String>,
    pub validation_ok: bool,
}

/// Apply a multi-line text/AR DSL script to durable `building.yaml`.
pub fn apply_edit(repo_root: &Path, script: &str) -> Result<EditApplyResult> {
    if script.trim().is_empty() {
        return Err(anyhow!("edit.apply requires non-empty 'script'"));
    }

    let mut building = load_building_at(repo_root)
        .map_err(|e| anyhow!("Failed to load {}: {}", BUILDING_YAML, e))?;

    let edit_report = apply_text_script(&mut building, script)
        .map_err(|e| anyhow!("Text script failed: {}", e))?;

    let mut result = finalize_ingest(
        building,
        IngestSource::Text,
        IngestOptions {
            validate: true,
            existing: None,
            policy: None,
        },
    );

    for msg in &edit_report.messages {
        result.report.warn("text_edit", msg.clone());
    }

    if result.validation.has_errors() {
        return Err(anyhow!(
            "edit.apply validation failed; refusing to write {}: {}",
            BUILDING_YAML,
            result.summary_lines().join("; ")
        ));
    }

    let report_summary = result.summary_lines();
    let building = result.building;
    let floors = building.floors.len();
    let rooms = building.get_all_rooms().len();
    let equipment = building.get_all_equipment().len();
    let name = building.name.clone();

    save_building_at(repo_root, &building)
        .map_err(|e| anyhow!("Failed to write {}: {}", BUILDING_YAML, e))?;

    Ok(EditApplyResult {
        building_name: name,
        yaml_path: BUILDING_YAML.to_string(),
        applied: edit_report.applied,
        floors,
        rooms,
        equipment,
        report_summary,
        validation_ok: true,
    })
}

/// Validate current `building.yaml` without mutating it.
#[derive(Debug, Serialize)]
pub struct ValidateResult {
    pub building_name: String,
    pub ok: bool,
    pub error_count: usize,
    pub warning_count: usize,
    pub summary_lines: Vec<String>,
    pub review_warnings: Vec<String>,
}

pub fn validate_building_rpc(repo_root: &Path) -> Result<ValidateResult> {
    let building = load_building_at(repo_root)
        .map_err(|e| anyhow!("Failed to load {}: {}", BUILDING_YAML, e))?;
    let report = crate::validation::validate_building(&building);
    let review = crate::core::summarize_review(&building);
    let ok = !report.has_errors();
    let error_count = report.errors().count();
    let warning_count = report.warnings().count();
    Ok(ValidateResult {
        building_name: building.name,
        ok,
        error_count,
        warning_count,
        summary_lines: report.summary_lines(),
        review_warnings: review.warning_lines(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{Building, Floor};
    use crate::persistence::save_building_at;
    use tempfile::tempdir;

    #[test]
    fn apply_edit_adds_equipment() {
        let dir = tempdir().unwrap();
        let mut b = Building::new("Bedroom Pilot".into(), "/pilot".into());
        b.add_floor(Floor::new("Ground Floor".into(), 0));
        save_building_at(dir.path(), &b).unwrap();

        let script = r#"
add room Bedroom floor="Ground Floor" type=bedroom
add equipment "Ceiling Fan" room=Bedroom type=electrical
set equipment "Ceiling Fan" review_status=proposed
add equipment "Light Switch" room=Bedroom type=electrical
set equipment "Light Switch" review_status=proposed
"#;
        let got = apply_edit(dir.path(), script).unwrap();
        assert_eq!(got.applied, 5);
        assert_eq!(got.rooms, 1);
        assert_eq!(got.equipment, 2);

        let v = validate_building_rpc(dir.path()).unwrap();
        assert!(v.ok);
    }
}

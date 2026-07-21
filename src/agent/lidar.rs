//! LiDAR file import via the ingest spine (`lidar.import` RPC).
//!
//! Mirrors `ifc.import`: base64 payload → imports/ → `import_lidar_path` → YAML.

use std::fs;
use std::path::Path;

use anyhow::{anyhow, bail, Result};
use base64::{engine::general_purpose, Engine as _};
use serde::Serialize;

use crate::ingest::import_lidar_path;
use crate::persistence::{save_building_at, BUILDING_YAML};
use crate::utils::path_safety::PathSafety;

#[derive(Debug, Serialize)]
pub struct LidarImportResult {
    pub building_name: String,
    pub yaml_path: String,
    pub floors: usize,
    pub rooms: usize,
    pub equipment: usize,
    pub report_summary: Vec<String>,
    pub proposed_rooms: usize,
    pub proposed_equipment: usize,
}

/// Decode base64 LiDAR payload, write under `imports/`, run LiDAR ingest spine.
pub fn import_lidar(
    repo_root: &Path,
    filename: &str,
    data_base64: &str,
    merge: bool,
    light_mode: bool,
    voxel_size: f64,
) -> Result<LidarImportResult> {
    let bytes = general_purpose::STANDARD
        .decode(data_base64)
        .map_err(|e| anyhow!("Base64 decode failed: {}", e))?;

    let max_lidar = crate::resource_limits::max_lidar_bytes() as usize;
    if bytes.len() > max_lidar {
        bail!(
            "LiDAR payload exceeds {} bytes (ARX_MAX_LIDAR_BYTES / pilot default). See docs/resource-limits.md.",
            max_lidar
        );
    }

    let ext = guess_ext(filename);
    let sanitized_name = ensure_extension(&sanitize_filename(filename, "scan.ply"), &ext);
    let imports_dir = repo_root.join("imports");
    fs::create_dir_all(&imports_dir)?;

    let import_path = imports_dir.join(&sanitized_name);
    PathSafety::validate_path_for_write(&import_path).map_err(|e| anyhow!(e))?;
    fs::write(&import_path, &bytes).map_err(|e| {
        anyhow!(
            "Failed to write LiDAR upload to {}: {}",
            import_path.display(),
            e
        )
    })?;

    finish_lidar_import(repo_root, &import_path, merge, light_mode, voxel_size)
}

fn finish_lidar_import(
    repo_root: &Path,
    lidar_path: &Path,
    merge: bool,
    light_mode: bool,
    voxel_size: f64,
) -> Result<LidarImportResult> {
    let building_yaml = repo_root.join(BUILDING_YAML);
    let existing = if merge && building_yaml.exists() {
        Some(building_yaml.as_path())
    } else if building_yaml.exists() {
        // Default for field: merge into existing pilot model when present
        Some(building_yaml.as_path())
    } else {
        None
    };

    let result = import_lidar_path(lidar_path, existing, voxel_size, light_mode, true)
        .map_err(|e| anyhow!("LiDAR import failed: {}", e))?;

    if result.validation.has_errors() {
        return Err(anyhow!(
            "LiDAR import validation failed; refusing to write {}: {}",
            BUILDING_YAML,
            result.summary_lines().join("; ")
        ));
    }

    let report_summary = result.summary_lines();
    let building = result.building;
    let floors = building.floors.len();
    let rooms = building.get_all_rooms().len();
    let equipment = building.get_all_equipment().len();
    use crate::core::review::{equipment_review_status, room_review_status, ReviewStatus};
    let proposed_rooms = building
        .get_all_rooms()
        .iter()
        .filter(|r| room_review_status(r) == Some(ReviewStatus::Proposed))
        .count();
    let proposed_equipment = building
        .get_all_equipment()
        .iter()
        .filter(|e| equipment_review_status(e) == Some(ReviewStatus::Proposed))
        .count();
    let name = building.name.clone();

    save_building_at(repo_root, &building)
        .map_err(|e| anyhow!("Failed to write {}: {}", BUILDING_YAML, e))?;

    Ok(LidarImportResult {
        building_name: name,
        yaml_path: BUILDING_YAML.to_string(),
        floors,
        rooms,
        equipment,
        report_summary,
        proposed_rooms,
        proposed_equipment,
    })
}

fn guess_ext(filename: &str) -> String {
    let lower = filename.to_ascii_lowercase();
    if lower.ends_with(".las") {
        ".las".into()
    } else if lower.ends_with(".laz") {
        ".laz".into()
    } else if lower.ends_with(".xyz") || lower.ends_with(".csv") {
        ".xyz".into()
    } else {
        ".ply".into()
    }
}

fn sanitize_filename(input: &str, fallback: &str) -> String {
    let candidate = Path::new(input)
        .file_name()
        .and_then(|s| s.to_str())
        .filter(|s| !s.trim().is_empty())
        .unwrap_or(fallback);

    let sanitized: String = candidate
        .chars()
        .map(|c| {
            if c.is_ascii_alphanumeric() || matches!(c, '-' | '_' | '.') {
                c
            } else {
                '_'
            }
        })
        .collect();

    let trimmed = sanitized.trim_matches('_');
    if trimmed.is_empty() {
        fallback.to_string()
    } else {
        sanitized
    }
}

fn ensure_extension(name: &str, ext: &str) -> String {
    if name.to_lowercase().ends_with(&ext.to_lowercase()) {
        name.to_string()
    } else {
        format!("{}{}", name, ext)
    }
}

//! LiDAR file import via the ingest spine (`lidar.import` RPC).
//!
//! Decision 11 v1 hand-off: client (CLI tooling or future native iOS) supplies
//! cloud file bytes → `imports/` → `import_lidar_path` → validate → `building.yaml`.
//! Optional provenance is stamped on the building; clients never write YAML.

use std::fs;
use std::path::Path;

use anyhow::{anyhow, bail, Result};
use base64::{engine::general_purpose, Engine as _};
use serde::{Deserialize, Serialize};

use crate::core::Building;
use crate::ingest::import_lidar_path;
use crate::persistence::{save_building_at, BUILDING_YAML};
use crate::utils::path_safety::PathSafety;

/// Optional client provenance (Decision 11 §3.1).
#[derive(Debug, Clone, Default, Deserialize, Serialize)]
pub struct CaptureProvenance {
    /// e.g. `ios_native`, `cli`, `airdrop_inbox`
    #[serde(default)]
    pub client: Option<String>,
    #[serde(default)]
    pub client_version: Option<String>,
    /// ISO-8601 capture time when known
    #[serde(default)]
    pub captured_at: Option<String>,
    #[serde(default)]
    pub device_model: Option<String>,
    #[serde(default)]
    pub note: Option<String>,
}

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
    /// Echo of applied client provenance (if any).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub provenance: Option<CaptureProvenance>,
}

/// Decode base64 LiDAR payload, write under `imports/`, run LiDAR ingest spine.
pub fn import_lidar(
    repo_root: &Path,
    filename: &str,
    data_base64: &str,
    merge: bool,
    light_mode: bool,
    voxel_size: f64,
    provenance: Option<CaptureProvenance>,
) -> Result<LidarImportResult> {
    let bytes = general_purpose::STANDARD
        .decode(data_base64)
        .map_err(|e| anyhow!("Base64 decode failed: {}", e))?;

    let max_lidar = crate::resource_limits::max_lidar_bytes() as usize;
    if bytes.is_empty() {
        bail!("LiDAR payload is empty after base64 decode");
    }
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

    finish_lidar_import(
        repo_root,
        &import_path,
        merge,
        light_mode,
        voxel_size,
        provenance,
    )
}

fn finish_lidar_import(
    repo_root: &Path,
    lidar_path: &Path,
    merge: bool,
    light_mode: bool,
    voxel_size: f64,
    provenance: Option<CaptureProvenance>,
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

    let mut result = import_lidar_path(lidar_path, existing, voxel_size, light_mode, true)
        .map_err(|e| anyhow!("LiDAR import failed: {}", e))?;

    if result.validation.has_errors() {
        return Err(anyhow!(
            "LiDAR import validation failed; refusing to write {}: {}",
            BUILDING_YAML,
            result.summary_lines().join("; ")
        ));
    }

    if let Some(ref prov) = provenance {
        apply_provenance(&mut result.building, prov);
        result.report.warn(
            "lidar_client_provenance",
            format!(
                "client={} version={} device={}",
                prov.client.as_deref().unwrap_or("unspecified"),
                prov.client_version.as_deref().unwrap_or("-"),
                prov.device_model.as_deref().unwrap_or("-")
            ),
        );
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
        provenance,
    })
}

/// Stamp Decision 11 provenance onto building metadata and proposed rooms.
fn apply_provenance(building: &mut Building, p: &CaptureProvenance) {
    if let Some(meta) = building.metadata.as_mut() {
        if let Some(c) = p.client.as_ref().filter(|s| !s.is_empty()) {
            meta.properties
                .insert("capture_client".to_string(), c.clone());
            if !meta.tags.iter().any(|t| t == c) {
                meta.tags.push(c.clone());
            }
        }
        if let Some(v) = p.client_version.as_ref().filter(|s| !s.is_empty()) {
            meta.properties
                .insert("capture_client_version".to_string(), v.clone());
        }
        if let Some(t) = p.captured_at.as_ref().filter(|s| !s.is_empty()) {
            meta.properties
                .insert("client_captured_at".to_string(), t.clone());
        }
        if let Some(d) = p.device_model.as_ref().filter(|s| !s.is_empty()) {
            meta.properties
                .insert("capture_device_model".to_string(), d.clone());
        }
        if let Some(n) = p.note.as_ref().filter(|s| !s.is_empty()) {
            meta.properties
                .insert("capture_client_note".to_string(), n.clone());
        }
        // Keep pipeline capture_source=lidar_file; client is additive provenance.
        if !meta.properties.contains_key("capture_source") {
            meta.properties
                .insert("capture_source".to_string(), "lidar_file".to_string());
        }
    }

    let client = p.client.clone().unwrap_or_default();
    if client.is_empty() {
        return;
    }
    for floor in &mut building.floors {
        for wing in &mut floor.wings {
            for room in &mut wing.rooms {
                room.properties
                    .insert("capture_client".to_string(), client.clone());
                for eq in &mut room.equipment {
                    eq.properties
                        .insert("capture_client".to_string(), client.clone());
                }
            }
        }
    }
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::PROP_REVIEW_STATUS;
    use crate::persistence::load_building_at;
    use tempfile::tempdir;

    fn tiny_xyz_cloud() -> Vec<u8> {
        let mut s = String::new();
        for i in 0..15 {
            for j in 0..15 {
                s.push_str(&format!("{} {} 1.0\n", i as f64 * 0.4, j as f64 * 0.4));
            }
        }
        s.into_bytes()
    }

    #[test]
    fn import_lidar_stamps_ios_provenance_and_proposed() {
        let dir = tempdir().unwrap();
        // Seed minimal building so merge path works cleanly
        let mut seed = crate::core::Building::new("Pilot".into(), "/pilot".into());
        seed.add_floor(crate::core::Floor::new("Ground Floor".into(), 0));
        save_building_at(dir.path(), &seed).unwrap();

        let b64 = general_purpose::STANDARD.encode(tiny_xyz_cloud());
        let prov = CaptureProvenance {
            client: Some("ios_native".into()),
            client_version: Some("0.0.1-dev".into()),
            captured_at: Some("2026-07-24T12:00:00Z".into()),
            device_model: Some("iPhone15,2".into()),
            note: Some("RoomPlan mesh exported to XYZ".into()),
        };
        let got = import_lidar(
            dir.path(),
            "room-scan.xyz",
            &b64,
            true,
            true,
            0.25,
            Some(prov),
        )
        .unwrap();

        assert!(got.rooms >= 1);
        assert!(got.proposed_rooms >= 1);
        assert_eq!(
            got.provenance.as_ref().and_then(|p| p.client.as_deref()),
            Some("ios_native")
        );

        let loaded = load_building_at(dir.path()).unwrap();
        let meta = loaded.metadata.as_ref().unwrap();
        assert_eq!(
            meta.properties.get("capture_client").map(String::as_str),
            Some("ios_native")
        );
        assert_eq!(
            meta.properties
                .get("capture_device_model")
                .map(String::as_str),
            Some("iPhone15,2")
        );
        let room = &loaded.get_all_rooms()[0];
        assert_eq!(
            room.properties.get(PROP_REVIEW_STATUS).map(String::as_str),
            Some("proposed")
        );
        assert_eq!(
            room.properties.get("capture_client").map(String::as_str),
            Some("ios_native")
        );
        assert!(dir.path().join("imports").join("room-scan.xyz").exists()
            || dir
                .path()
                .join("imports")
                .read_dir()
                .unwrap()
                .any(|e| e.unwrap().path().extension().is_some()));
    }

    #[test]
    fn import_lidar_rejects_empty_payload() {
        let dir = tempdir().unwrap();
        let b64 = general_purpose::STANDARD.encode([]);
        let err = import_lidar(dir.path(), "empty.xyz", &b64, true, true, 0.25, None)
            .unwrap_err();
        assert!(err.to_string().contains("empty"));
    }
}

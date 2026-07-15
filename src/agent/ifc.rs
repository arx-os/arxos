use std::fs;
use std::path::Path;

use crate::agent::git::SyncState;
use crate::export::ifc::IFCExporter;
use crate::ingest::import_ifc_path;
use crate::persistence::{load_building_at, save_building_at, BUILDING_YAML};
use crate::utils::path_safety::PathSafety;
use anyhow::{anyhow, bail, Result};
use base64::{engine::general_purpose, Engine as _};

#[derive(Debug, serde::Serialize)]
pub struct IfcImportResult {
    pub building_name: String,
    pub yaml_path: String,
    pub floors: usize,
    pub rooms: usize,
    pub equipment: usize,
    /// Human-readable loss / merge summary lines (Phase 5).
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub report_summary: Vec<String>,
}

#[derive(Debug, serde::Serialize)]
pub struct IfcExportResult {
    pub filename: String,
    pub data: String,
    pub size_bytes: usize,
}

pub fn import_ifc(repo_root: &Path, filename: &str, data_base64: &str) -> Result<IfcImportResult> {
    let bytes = decode_base64(data_base64)?;
    let max_ifc = crate::resource_limits::max_ifc_bytes() as usize;
    if bytes.len() > max_ifc {
        bail!(
            "IFC payload exceeds {} bytes (ARX_MAX_IFC_BYTES / pilot default). See docs/resource-limits.md.",
            max_ifc
        );
    }

    let sanitized_name = ensure_extension(&sanitize_filename(filename, "upload.ifc"), ".ifc");
    let imports_dir = repo_root.join("imports");
    fs::create_dir_all(&imports_dir)?;

    let import_path = imports_dir.join(&sanitized_name);
    PathSafety::validate_path_for_write(&import_path).map_err(|e| anyhow!(e))?;
    fs::write(&import_path, &bytes).map_err(|e| {
        anyhow!(
            "Failed to write IFC upload to {}: {}",
            import_path.display(),
            e
        )
    })?;

    finish_import(repo_root, &import_path)
}

pub fn import_ifc_local(repo_root: &Path, ifc_path: &Path) -> Result<IfcImportResult> {
    finish_import(repo_root, ifc_path)
}

/// Shared import pipeline via `ingest` (parse → merge → validate → write YAML).
fn finish_import(repo_root: &Path, ifc_path: &Path) -> Result<IfcImportResult> {
    // Prefer merging with an existing YAML named after the eventual building, if present
    let building_yaml = repo_root.join("building.yaml");
    let existing = if building_yaml.exists() {
        Some(building_yaml.as_path())
    } else {
        None
    };

    let result = import_ifc_path(ifc_path, existing, false, true)
        .map_err(|e| anyhow!("IFC import failed: {}", e))?;

    if result.validation.has_errors() {
        return Err(anyhow!(
            "IFC import validation failed; refusing to write {}: {}",
            BUILDING_YAML,
            result.summary_lines().join("; ")
        ));
    }

    let report_summary = result.summary_lines();
    let building = result.building;
    let floors = building.floors.len();
    let rooms = building
        .floors
        .iter()
        .map(|f| f.wings.iter().map(|w| w.rooms.len()).sum::<usize>())
        .sum();
    let equipment = building.get_all_equipment().len();

    save_building_at(repo_root, &building)
        .map_err(|e| anyhow!("Failed to write {}: {}", BUILDING_YAML, e))?;

    Ok(IfcImportResult {
        building_name: building.name,
        yaml_path: BUILDING_YAML.to_string(),
        floors,
        rooms,
        equipment,
        report_summary,
    })
}

/// Export IFC via the **same** compiler spine as `arx export --format ifc`
/// (`export::ifc::IFCExporter`).
///
/// Agent/daemon is edge bridging only: it must not invent alternate STEP writers
/// or delta semantics. Official L1 pilot handoffs use the CLI.
///
/// * `delta` — always rejected (matches CLI: not implemented).
/// * `approved_only` — same filter as CLI `--approved-only` (drop proposed/rejected LiDAR autos).
pub fn export_ifc(
    repo_root: &Path,
    filename: Option<String>,
    delta: bool,
) -> Result<IfcExportResult> {
    export_ifc_with_options(repo_root, filename, delta, false)
}

/// See [`export_ifc`]. Prefer this when the RPC client can pass review flags.
pub fn export_ifc_with_options(
    repo_root: &Path,
    filename: Option<String>,
    delta: bool,
    approved_only: bool,
) -> Result<IfcExportResult> {
    if delta {
        bail!(
            "agent ifc.export delta is not supported (same as `arx export --delta`). \
             Use full export via export::ifc. Official pilot handoffs: `arx export --format ifc`."
        );
    }

    let mut building = load_building_at(repo_root)
        .map_err(|e| anyhow!("Failed to load {}: {}", BUILDING_YAML, e))?;

    // Stabilize product GlobalIds before write (same contract as identity docs).
    crate::ifc::mapping::assign_missing_global_ids(&mut building);

    let review = crate::core::summarize_review(&building);
    for line in review.warning_lines() {
        eprintln!("  {}", line);
    }
    if approved_only {
        eprintln!("  approved_only: excluding proposed/rejected LiDAR auto entities");
    }
    let export_building = crate::core::filter_building_for_export(&building, approved_only);

    let exporter = IFCExporter::new(export_building);

    let exports_dir = repo_root.join("exports");
    fs::create_dir_all(&exports_dir)?;

    let default_name = format!("{}.ifc", sanitize_filename(&building.name, "building"));
    let export_filename = ensure_extension(
        &sanitize_filename(filename.as_deref().unwrap_or(&default_name), &default_name),
        ".ifc",
    );

    let ifc_path = exports_dir.join(&export_filename);
    PathSafety::validate_path_for_write(&ifc_path).map_err(|e| anyhow!(e))?;

    // Full export only — single IFCExporter path (no delta theater).
    exporter.export(&ifc_path)?;

    let sync_state_path = repo_root.join(SyncState::default_path());
    let mut sync_state = SyncState::load(&sync_state_path).unwrap_or_else(|| {
        SyncState::new(
            ifc_path
                .strip_prefix(repo_root)
                .unwrap_or(&ifc_path)
                .to_path_buf(),
        )
    });
    sync_state.ifc_file_path = ifc_path
        .strip_prefix(repo_root)
        .unwrap_or(&ifc_path)
        .to_path_buf();

    let (equipment_paths, rooms_paths) = exporter.collect_universal_paths();
    sync_state.update_after_export(equipment_paths, rooms_paths);
    sync_state
        .save(&sync_state_path)
        .map_err(|e| anyhow!("Failed to save IFC sync state: {}", e))?;

    let bytes = fs::read(&ifc_path)?;
    let encoded = general_purpose::STANDARD.encode(&bytes);

    Ok(IfcExportResult {
        filename: relative_display_path(repo_root, &ifc_path),
        data: encoded,
        size_bytes: bytes.len(),
    })
}

fn decode_base64(data: &str) -> Result<Vec<u8>> {
    general_purpose::STANDARD
        .decode(data)
        .map_err(|e| anyhow!("Base64 decode failed: {}", e))
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

fn relative_display_path(root: &Path, target: &Path) -> String {
    target
        .strip_prefix(root)
        .unwrap_or(target)
        .display()
        .to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{Building, Floor, Room, RoomType, SpatialProperties, Wing};
    use crate::yaml::BuildingYamlSerializer;
    use tempfile::TempDir;

    fn sample_ifc_bytes() -> Vec<u8> {
        let path = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("test_data")
            .join("sample_building.ifc");
        fs::read(path).expect("sample IFC should exist")
    }

    #[test]
    fn import_generates_yaml() {
        let temp = TempDir::new().unwrap();
        let repo_root = temp.path();
        let ifc_data = sample_ifc_bytes();
        let encoded = general_purpose::STANDARD.encode(&ifc_data);

        let result = import_ifc(repo_root, "Sample Building.ifc", &encoded).unwrap();
        assert!(repo_root.join(&result.yaml_path).exists());
        assert!(result.floors > 0);
    }

    #[test]
    fn export_round_trip() {
        let temp = TempDir::new().unwrap();
        let repo_root = temp.path();

        // Create minimal building data YAML
        let mut building = Building::new("Test Facility".into(), "/test".into());
        let mut floor = Floor::new("Level 1".into(), 1);
        let mut wing = Wing::new("North".into());
        let room = Room {
            id: uuid::Uuid::new_v4().to_string(),
            name: "Room 101".to_string(),
            room_type: RoomType::Office,
            equipment: Vec::new(),
            spatial_properties: SpatialProperties::default(),
            properties: Default::default(),
            created_at: None,
            updated_at: None,
            pending_equipment_ids: Vec::new(),
            lidar_enrichment: None,
            ifc_global_id: None,
            address: None,
            anchors: Vec::new(),
            pending_anchor_ids: Vec::new(),
        };
        wing.rooms.push(room);
        floor.wings.push(wing);
        building.floors.push(floor);

        save_building_at(repo_root, &building).unwrap();

        let export = export_ifc(repo_root, None, false).unwrap();
        assert!(export.size_bytes > 0);
        assert!(!export.data.is_empty());
    }
}

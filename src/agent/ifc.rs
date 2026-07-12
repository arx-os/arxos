use std::fs;
use std::path::{Path, PathBuf};

use anyhow::{anyhow, bail, Result};
use crate::utils::path_safety::PathSafety;
use crate::export::ifc::IFCExporter;
use crate::agent::git::SyncState;
use crate::ifc::IFCProcessor;
use crate::yaml::{BuildingData, BuildingYamlSerializer};
use crate::core::{Building, BuildingMetadata};
use base64::{engine::general_purpose, Engine as _};
use chrono::{DateTime, Utc};

const MAX_IFC_BYTES: usize = 50 * 1024 * 1024; // 50 MB ceiling for uploads

#[derive(Debug, serde::Serialize)]
pub struct IfcImportResult {
    pub building_name: String,
    pub yaml_path: String,
    pub floors: usize,
    pub rooms: usize,
    pub equipment: usize,
}

#[derive(Debug, serde::Serialize)]
pub struct IfcExportResult {
    pub filename: String,
    pub data: String,
    pub size_bytes: usize,
}

pub fn import_ifc(repo_root: &Path, filename: &str, data_base64: &str) -> Result<IfcImportResult> {
    let bytes = decode_base64(data_base64)?;
    if bytes.len() > MAX_IFC_BYTES {
        bail!("IFC payload exceeds {} bytes", MAX_IFC_BYTES);
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

    let import_path_str = import_path.to_str().ok_or_else(|| anyhow!("Invalid path utf-8"))?;
    let processor = IFCProcessor::new();
    let mut building = processor.extract_hierarchy(import_path_str)?;

    let floors = building.floors.len();
    let rooms = building
        .floors
        .iter()
        .map(|f| f.wings.iter().map(|w| w.rooms.len()).sum::<usize>())
        .sum();
    let equipment = building.get_all_equipment().len();

    let yaml_filename = format!("{}.yaml", sanitize_filename(&building.name, "building"));
    let yaml_path = repo_root.join(&yaml_filename);

    // Check if we have old data to merge
    if yaml_path.exists() {
        if let Ok(old_content) = fs::read_to_string(&yaml_path) {
            if let Ok(old_building) = BuildingYamlSerializer::deserialize_building(&old_content) {
                merge_buildings(&mut building, &old_building);
            }
        }
    }

    let relative_yaml = relative_display_path(repo_root, &yaml_path);
    
    // Save YAML
    let yaml_string = BuildingYamlSerializer::serialize_building(&building)
        .map_err(|e| anyhow!("Failed to serialize YAML: {}", e))?;
    fs::write(&yaml_path, yaml_string)?;

    Ok(IfcImportResult {
        building_name: building.name,
        yaml_path: relative_yaml,
        floors,
        rooms,
        equipment,
    })
}

pub fn import_ifc_local(repo_root: &Path, ifc_path: &Path) -> Result<IfcImportResult> {
    let import_path_str = ifc_path.to_str().ok_or_else(|| anyhow!("Invalid path utf-8"))?;
    let processor = IFCProcessor::new();
    let mut building = processor.extract_hierarchy(import_path_str)?;

    let floors = building.floors.len();
    let rooms = building
        .floors
        .iter()
        .map(|f| f.wings.iter().map(|w| w.rooms.len()).sum::<usize>())
        .sum();
    let equipment = building.get_all_equipment().len();

    let yaml_filename = format!("{}.yaml", sanitize_filename(&building.name, "building"));
    let yaml_path = repo_root.join(&yaml_filename);
    
    // Check if we have old data to merge
    if yaml_path.exists() {
        if let Ok(old_content) = fs::read_to_string(&yaml_path) {
            if let Ok(old_building) = BuildingYamlSerializer::deserialize_building(&old_content) {
                merge_buildings(&mut building, &old_building);
            }
        }
    }

    let relative_yaml = relative_display_path(repo_root, &yaml_path);
    
    let yaml_string = BuildingYamlSerializer::serialize_building(&building)
        .map_err(|e| anyhow!("Failed to serialize YAML: {}", e))?;
    fs::write(&yaml_path, yaml_string)?;

    Ok(IfcImportResult {
        building_name: building.name,
        yaml_path: relative_yaml,
        floors,
        rooms,
        equipment,
    })
}

fn merge_buildings(new_building: &mut Building, old_building: &Building) {
    // 1. Merge Building metadata
    if new_building.name == old_building.name {
        new_building.created_at = old_building.created_at;
        if let Some(old_meta) = &old_building.metadata {
            if let Some(new_meta) = &mut new_building.metadata {
                for tag in &old_meta.tags {
                    if !new_meta.tags.contains(tag) {
                        new_meta.tags.push(tag.clone());
                    }
                }
            } else {
                new_building.metadata = Some(old_meta.clone());
            }
        }
    }

    // 2. Index old components
    let mut old_rooms = std::collections::HashMap::new();
    let mut old_equipment = std::collections::HashMap::new();

    for floor in &old_building.floors {
        for wing in &floor.wings {
            for room in &wing.rooms {
                let path = format!("{}/{}", floor.name, room.name);
                old_rooms.insert(path, room);
            }
        }
    }

    // Index old equipment by their hierarchical paths
    for floor in &old_building.floors {
        for eq in &floor.equipment {
            let path = format!("{}/{}", floor.name, eq.name);
            old_equipment.insert(path, eq.clone());
        }
        for wing in &floor.wings {
            for eq in &wing.equipment {
                let path = format!("{}/{}/{}", floor.name, wing.name, eq.name);
                old_equipment.insert(path, eq.clone());
            }
            for room in &wing.rooms {
                for eq in &room.equipment {
                    let path = format!("{}/{}/{}/{}", floor.name, wing.name, room.name, eq.name);
                    old_equipment.insert(path, eq.clone());
                }
            }
        }
    }

    // 3. Merge Rooms
    for floor in &mut new_building.floors {
        for wing in &mut floor.wings {
            for room in &mut wing.rooms {
                let path = format!("{}/{}", floor.name, room.name);
                if let Some(old_room) = old_rooms.get(&path) {
                    room.created_at = old_room.created_at;
                    for (k, v) in &old_room.properties {
                        room.properties.entry(k.clone()).or_insert_with(|| v.clone());
                    }
                }
            }
        }
    }

    // 4. Merge Equipment
    for floor in &mut new_building.floors {
        let floor_name = &floor.name;
        for eq in &mut floor.equipment {
            let path = format!("{}/{}", floor_name, eq.name);
            if let Some(old_eq) = old_equipment.get(&path) {
                eq.status = old_eq.status;
                eq.health_status = old_eq.health_status.clone();
                for (k, v) in &old_eq.properties {
                    eq.properties.entry(k.clone()).or_insert_with(|| v.clone());
                }
            }
        }
        for wing in &mut floor.wings {
            let wing_name = &wing.name;
            for eq in &mut wing.equipment {
                let path = format!("{}/{}/{}", floor_name, wing_name, eq.name);
                if let Some(old_eq) = old_equipment.get(&path) {
                    eq.status = old_eq.status;
                    eq.health_status = old_eq.health_status.clone();
                    for (k, v) in &old_eq.properties {
                        eq.properties.entry(k.clone()).or_insert_with(|| v.clone());
                    }
                }
            }
            for room in &mut wing.rooms {
                let room_name = &room.name;
                for eq in &mut room.equipment {
                    let path = format!("{}/{}/{}/{}", floor_name, wing_name, room_name, eq.name);
                    if let Some(old_eq) = old_equipment.get(&path) {
                        eq.status = old_eq.status;
                        eq.health_status = old_eq.health_status.clone();
                        for (k, v) in &old_eq.properties {
                            eq.properties.entry(k.clone()).or_insert_with(|| v.clone());
                        }
                    }
                }
            }
        }
    }
}

pub fn export_ifc(
    repo_root: &Path,
    filename: Option<String>,
    delta: bool,
) -> Result<IfcExportResult> {
    let building_data = load_building_data(repo_root)?;
    let building = building_data.into_building();
    let exporter = IFCExporter::new(building.clone());

    let exports_dir = repo_root.join("exports");
    fs::create_dir_all(&exports_dir)?;

    let default_name = format!(
        "{}.ifc",
        sanitize_filename(&building.name, "building")
    );
    let export_filename = ensure_extension(
        &sanitize_filename(filename.as_deref().unwrap_or(&default_name), &default_name),
        ".ifc",
    );

    let ifc_path = exports_dir.join(&export_filename);
    PathSafety::validate_path_for_write(&ifc_path).map_err(|e| anyhow!(e))?;

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

    let has_previous_export = sync_state.last_export_timestamp > DateTime::<Utc>::UNIX_EPOCH;
    if delta && has_previous_export {
        exporter.export_delta(Some(&sync_state), &ifc_path)?;
    } else {
        exporter.export(&ifc_path)?;
    }

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

fn load_building_data(repo_root: &Path) -> Result<BuildingData> {
    let mut yaml_candidates = Vec::new();
    // Safe directory reading with path validation
    PathSafety::validate_path(repo_root)
        .map_err(|e| anyhow!("Invalid path: {}", e))?;
        
    for entry in fs::read_dir(repo_root)? {
        let entry = entry?;
        let path = entry.path();
        if let Some(ext) = path.extension().and_then(|s| s.to_str()) {
            if ext.eq_ignore_ascii_case("yaml") || ext.eq_ignore_ascii_case("yml") {
                yaml_candidates.push(path);
            }
        }
    }

    let yaml_path = yaml_candidates
        .first()
        .ok_or_else(|| anyhow!("No YAML building data found in repository"))?;

    // Safe file reading
    let content = PathSafety::read_file_safely(yaml_path, repo_root)
        .map_err(|e| anyhow::anyhow!("Failed to read safe file: {}", e))?;
    let data: BuildingData = serde_yaml::from_str(&content)
        .map_err(|e| anyhow!("Failed to parse YAML file {}: {}", yaml_path.display(), e))?;
    Ok(data)
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
        };
        wing.rooms.push(room);
        floor.wings.push(wing);
        building.floors.push(floor);

        let data = BuildingYamlSerializer::serialize_building(&building).unwrap();
        let yaml_path = repo_root.join("test_facility.yaml");
        std::fs::write(&yaml_path, data).unwrap();

        let export = export_ifc(repo_root, None, false).unwrap();
        assert!(export.size_bytes > 0);
        assert!(!export.data.is_empty());
    }
}

struct DirGuard {
    original: PathBuf,
}

impl DirGuard {
    fn change_to(path: &Path) -> Result<Self> {
        let original = std::env::current_dir()?;
        std::env::set_current_dir(path)?;
        Ok(Self { original })
    }
}

impl Drop for DirGuard {
    fn drop(&mut self) {
        let _ = std::env::set_current_dir(&self.original);
    }
}

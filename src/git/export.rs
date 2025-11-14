//! Export operations for building data to Git repository

use super::commit::commit_changes_with_metadata;
use super::{CommitMetadata, GitConfig, GitError, GitOperationResult};
use crate::utils::path_safety::PathSafety;
use crate::yaml::{BuildingData, BuildingYamlSerializer};
use git2::Repository;
use log::info;
use std::collections::HashMap;
use std::path::Path;

/// Export building data to Git repository
pub fn export_building(
    repo: &mut Repository,
    serializer: &BuildingYamlSerializer,
    building_data: &BuildingData,
    config: &GitConfig,
    metadata: &CommitMetadata,
) -> Result<GitOperationResult, GitError> {
    info!("Exporting building data to Git repository");

    // Check total size before exporting
    let total_size_mb = estimate_building_size(serializer, building_data)?;
    const WARNING_SIZE_MB: usize = 50;

    if total_size_mb > WARNING_SIZE_MB {
        info!(
            "Warning: Large building dataset ({}MB). Git operations may be slow.",
            total_size_mb
        );
    }

    // Create directory structure
    let file_structure = create_file_structure(serializer, building_data)?;

    // Write files to repository
    let files_changed = write_building_files(repo, &file_structure)?;
    let file_paths: Vec<String> = file_structure.keys().cloned().collect();

    // Commit changes with metadata
    let commit_id = commit_changes_with_metadata(repo, config, metadata, &file_paths)?;

    info!(
        "Successfully exported building data: {} files changed",
        files_changed
    );

    Ok(GitOperationResult {
        commit_id,
        files_changed,
        message: metadata.message.clone(),
    })
}

/// Estimate building data size in megabytes
fn estimate_building_size(
    serializer: &BuildingYamlSerializer,
    building_data: &BuildingData,
) -> Result<usize, GitError> {
    let main_yaml = serializer
        .to_yaml(building_data)
        .map_err(|e| GitError::Generic(e.to_string()))?;
    let mut size = main_yaml.len();

    // Estimate size of all floor/room/equipment files
    for floor in &building_data.building.floors {
        let floor_yaml = serializer
            .to_yaml(floor)
            .map_err(|e| GitError::Generic(e.to_string()))?;
        size += floor_yaml.len();
        // Rooms are in wings
        for wing in &floor.wings {
            for room in &wing.rooms {
                let room_yaml = serializer
                    .to_yaml(room)
                    .map_err(|e| GitError::Generic(e.to_string()))?;
                size += room_yaml.len();
            }
        }
        for equipment in &floor.equipment {
            let equipment_yaml = serializer
                .to_yaml(equipment)
                .map_err(|e| GitError::Generic(e.to_string()))?;
            size += equipment_yaml.len();
        }
    }

    Ok(size / (1024 * 1024)) // Convert to MB
}

/// Write building files to repository with path validation
fn write_building_files(
    repo: &Repository,
    file_structure: &HashMap<String, String>,
) -> Result<usize, GitError> {
    let repo_workdir = repo
        .workdir()
        .ok_or_else(|| GitError::OperationFailed {
            operation: "access repository workdir".to_string(),
            reason: "Git repository has no working directory".to_string(),
        })?
        .to_path_buf();

    let mut files_changed = 0;

    for (file_path, content) in file_structure {
        let file_path_buf = Path::new(file_path);
        let full_path = repo_workdir.join(file_path_buf);

        // Create parent directories first
        if let Some(parent) = full_path.parent() {
            std::fs::create_dir_all(parent).map_err(|e| GitError::OperationFailed {
                operation: format!("create directory: {}", parent.display()),
                reason: format!("Failed to create directory structure: {}", e),
            })?;
        }

        // Validate the path
        PathSafety::validate_path_for_write(&full_path)
            .map_err(|e| GitError::OperationFailed {
                operation: format!("validate file path: {}", file_path),
                reason: format!("Path validation failed: {}", e),
            })?;

        std::fs::write(&full_path, content)?;
        files_changed += 1;
    }

    Ok(files_changed)
}

/// Create file structure for building data
pub fn create_file_structure(
    serializer: &BuildingYamlSerializer,
    building_data: &BuildingData,
) -> Result<HashMap<String, String>, GitError> {
    let mut files = HashMap::new();

    // Main building file
    let building_yaml = serializer
        .to_yaml(building_data)
        .map_err(|e| GitError::Generic(e.to_string()))?;
    files.insert("building.yml".to_string(), building_yaml);

    // Floor files
    for floor in &building_data.building.floors {
        let floor_path = format!("floors/floor-{}.yml", floor.level);
        let floor_yaml = serializer
            .to_yaml(floor)
            .map_err(|e| GitError::Generic(e.to_string()))?;
        files.insert(floor_path, floor_yaml);

        // Room files (rooms are in wings)
        for wing in &floor.wings {
            for room in &wing.rooms {
                let room_path = format!(
                    "floors/floor-{}/rooms/{}.yml",
                    floor.level,
                    room.name.to_lowercase().replace(" ", "-")
                );
                let room_yaml = serializer
                    .to_yaml(room)
                    .map_err(|e| GitError::Generic(e.to_string()))?;
                files.insert(room_path, room_yaml);
            }
        }

        // Equipment files
        for equipment in &floor.equipment {
            // Use ArxAddress path for directory structure if available
            let equipment_path = if let Some(ref addr) = equipment.address {
                let path_parts: Vec<&str> = addr.path.trim_start_matches('/').split('/').collect();
                if path_parts.len() == 7 {
                    format!(
                        "{}/{}/{}/{}/{}/{}/{}.yml",
                        path_parts[0], // country
                        path_parts[1], // state
                        path_parts[2], // city
                        path_parts[3], // building
                        path_parts[4], // floor
                        path_parts[5], // room
                        path_parts[6]  // fixture
                    )
                } else {
                    // Fallback to old format
                    format!(
                        "floors/floor-{}/equipment/{}/{}.yml",
                        floor.level,
                        equipment.system_type().to_lowercase(),
                        equipment.name.to_lowercase().replace(" ", "-")
                    )
                }
            } else {
                // Fallback to old format if no address
                format!(
                    "floors/floor-{}/equipment/{}/{}.yml",
                    floor.level,
                    equipment.system_type().to_lowercase(),
                    equipment.name.to_lowercase().replace(" ", "-")
                )
            };
            let equipment_yaml = serializer
                .to_yaml(equipment)
                .map_err(|e| GitError::Generic(e.to_string()))?;
            files.insert(equipment_path, equipment_yaml);
        }
    }

    // Create index file for easy navigation
    let index_content = create_index_file(serializer, building_data)?;
    files.insert("index.yml".to_string(), index_content);

    Ok(files)
}

/// Create index file for building navigation
fn create_index_file(
    _serializer: &BuildingYamlSerializer,
    building_data: &BuildingData,
) -> Result<String, GitError> {
    use serde_yaml::{Mapping, Value};

    let mut index_map = Mapping::new();

    // Add building metadata
    let mut building_map = Mapping::new();
    building_map.insert(
        Value::String("id".to_string()),
        Value::String(building_data.building.id.clone()),
    );
    building_map.insert(
        Value::String("name".to_string()),
        Value::String(building_data.building.name.clone()),
    );
    index_map.insert(
        Value::String("building".to_string()),
        Value::Mapping(building_map),
    );

    // Add floors index
    let mut floors_list = Vec::new();
    for floor in &building_data.building.floors {
        let mut floor_map = Mapping::new();
        floor_map.insert(
            Value::String("level".to_string()),
            Value::Number(floor.level.into()),
        );
        floor_map.insert(
            Value::String("name".to_string()),
            Value::String(floor.name.clone()),
        );
        floors_list.push(Value::Mapping(floor_map));
    }
    index_map.insert(
        Value::String("floors".to_string()),
        Value::Sequence(floors_list),
    );

    // Serialize to YAML string
    let yaml_string = serde_yaml::to_string(&index_map)
        .map_err(|e| GitError::SerializationError(e.to_string()))?;

    Ok(yaml_string)
}

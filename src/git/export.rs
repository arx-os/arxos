//! Export canonical Building to the Git working tree as a single YAML SSOT.

use super::commit::commit_changes_with_metadata;
use super::{CommitMetadata, GitConfig, GitError, GitOperationResult};
use crate::persistence::BUILDING_YAML;
use crate::utils::path_safety::PathSafety;
use crate::yaml::BuildingYamlSerializer;
use git2::Repository;
use log::info;

/// Write `building.yaml` and commit it with metadata.
pub fn export_building(
    repo: &mut Repository,
    _serializer: &BuildingYamlSerializer,
    building: &crate::core::Building,
    config: &GitConfig,
    metadata: &CommitMetadata,
) -> Result<GitOperationResult, GitError> {
    info!(
        "Exporting building data to Git repository ({})",
        BUILDING_YAML
    );

    let yaml = BuildingYamlSerializer::serialize_building(building)
        .map_err(|e| GitError::Generic(e.to_string()))?;

    let size_mb = yaml.len() / (1024 * 1024);
    if size_mb > 50 {
        info!(
            "Warning: Large building dataset ({}MB). Git operations may be slow.",
            size_mb
        );
    }

    let files_changed = write_building_yaml(repo, &yaml)?;
    let file_paths = vec![BUILDING_YAML.to_string()];

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

fn write_building_yaml(repo: &Repository, content: &str) -> Result<usize, GitError> {
    let repo_workdir = repo
        .workdir()
        .ok_or_else(|| GitError::OperationFailed {
            operation: "access repository workdir".to_string(),
            reason: "Git repository has no working directory".to_string(),
        })?
        .to_path_buf();

    let full_path = repo_workdir.join(BUILDING_YAML);

    PathSafety::validate_path_for_write(&full_path).map_err(|e| GitError::OperationFailed {
        operation: format!("validate file path: {}", BUILDING_YAML),
        reason: format!("Path validation failed: {}", e),
    })?;

    std::fs::write(&full_path, content)?;
    Ok(1)
}

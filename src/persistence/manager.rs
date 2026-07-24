//! Persistence for the canonical `core::Building` durable store.
//!
//! Single layout: `{base_path}/building.yaml` via `BuildingYamlSerializer`.

use super::{PersistenceError, PersistenceResult};
use crate::core::Building;
use crate::yaml::BuildingYamlSerializer;
use std::path::{Path, PathBuf};

/// Canonical durable filename for a building model.
pub const BUILDING_YAML: &str = "building.yaml";

/// Manager for loading and saving the Building SSOT on disk.
///
/// Does not own Git versioning — use `BuildingGitManager` for commits.
pub struct PersistenceManager {
    base_path: PathBuf,
}

impl PersistenceManager {
    /// Open persistence at the current working directory.
    ///
    /// The `building_name` argument is accepted for call-site compatibility but
    /// no longer selects a subdirectory. SSOT is always `building.yaml` under
    /// the base path.
    pub fn new(_building_name: &str) -> PersistenceResult<Self> {
        Self::from_cwd()
    }

    /// Open persistence at the current working directory.
    pub fn from_cwd() -> PersistenceResult<Self> {
        let base_path = std::env::current_dir().map_err(PersistenceError::IoError)?;
        Ok(Self { base_path })
    }

    /// Open persistence at an explicit repository / project root.
    pub fn with_path<P: AsRef<Path>>(base_path: P, _building_name: &str) -> Self {
        Self {
            base_path: base_path.as_ref().to_path_buf(),
        }
    }

    /// Open persistence at an explicit base path (preferred constructor).
    pub fn at(base_path: impl AsRef<Path>) -> Self {
        Self {
            base_path: base_path.as_ref().to_path_buf(),
        }
    }

    /// Project / repo root used for `building.yaml`.
    pub fn base_path(&self) -> &Path {
        &self.base_path
    }

    /// Absolute path to the durable Building YAML.
    pub fn building_yaml_path(&self) -> PathBuf {
        self.base_path.join(BUILDING_YAML)
    }

    /// Alias for older call sites (`{name}/building.yaml` layout removed).
    pub fn building_path(&self) -> PathBuf {
        self.base_path.clone()
    }

    /// Path to the working Building file.
    pub fn working_file(&self) -> PathBuf {
        self.building_yaml_path()
    }

    /// Save `building` to `{base}/building.yaml` after validation hard-gate.
    ///
    /// Refuses to write when `validate_building` reports errors. Prefer this
    /// (or `ingest::persist_building`) for all production writers.
    pub fn save_building_data(&self, building: &Building) -> PersistenceResult<()> {
        self.save_building_validated(building)
    }

    /// Serialize-only save **without** validation.
    ///
    /// Intended for tests and internal use after an upstream validate gate
    /// (e.g. `persist_building` / import already checked `has_errors()`).
    /// Do not call from CLI/agent entry points for untrusted models.
    pub fn save_building_unchecked(&self, building: &Building) -> PersistenceResult<()> {
        use std::fs;

        if !self.base_path.exists() {
            fs::create_dir_all(&self.base_path)?;
        }

        let yaml_content = BuildingYamlSerializer::serialize_building(building)
            .map_err(|e| PersistenceError::SerializationError(e.to_string()))?;

        let file_path = self.building_yaml_path();
        fs::write(&file_path, yaml_content)?;

        Ok(())
    }

    /// Validate then save; hard-fail on validation errors.
    pub fn save_building_validated(&self, building: &Building) -> PersistenceResult<()> {
        let report = crate::validation::validate_building(building);
        if report.has_errors() {
            let details: Vec<String> = report
                .errors()
                .map(|e| match &e.field {
                    Some(f) => format!("{}: {}", f, e.message),
                    None => e.message.clone(),
                })
                .collect();
            return Err(PersistenceError::ValidationError(format!(
                "Building validation failed ({} error(s)): {}",
                details.len(),
                details.join("; ")
            )));
        }
        self.save_building_unchecked(building)
    }

    /// Load `Building` from `{base}/building.yaml` only (no multi-file discovery).
    pub fn load_building_data(&self) -> PersistenceResult<Building> {
        use std::fs;

        let file_path = self.building_yaml_path();
        if !file_path.exists() {
            return Err(PersistenceError::ValidationError(format!(
                "No building SSOT found at {}",
                file_path.display()
            )));
        }

        let yaml_content = fs::read_to_string(&file_path)?;
        BuildingYamlSerializer::deserialize_building(&yaml_content)
            .map_err(|e| PersistenceError::SerializationError(e.to_string()))
    }

    /// Save Building, then commit with `BuildingGitManager` when a repo exists.
    pub fn save_and_commit(
        &self,
        building: &Building,
        message: Option<&str>,
    ) -> PersistenceResult<()> {
        // Caller (persist_building) already validated; avoid double work but keep gate if used alone.
        self.save_building_validated(building)?;

        if !self.has_git_repo() {
            return Ok(());
        }

        use crate::git::manager::{BuildingGitManager, GitConfigManager};

        let config = GitConfigManager::load_from_arx_config_or_env();
        let base = self.base_path.to_str().ok_or_else(|| {
            PersistenceError::SerializationError("base path is not valid UTF-8".into())
        })?;

        let mut git = BuildingGitManager::new(base, "building", config)
            .map_err(|e| PersistenceError::SerializationError(format!("Git open failed: {}", e)))?;

        git.stage_file(BUILDING_YAML).map_err(|e| {
            PersistenceError::SerializationError(format!("Git stage failed: {}", e))
        })?;

        let msg = message.unwrap_or("Update building data");
        git.commit_staged(msg).map_err(|e| {
            PersistenceError::SerializationError(format!("Git commit failed: {}", e))
        })?;

        Ok(())
    }

    /// Whether `base_path` contains a Git repository.
    pub fn has_git_repo(&self) -> bool {
        self.base_path.join(".git").exists()
    }
}

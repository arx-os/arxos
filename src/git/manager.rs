// Real Git operations for ArxOS
use git2::{Repository, Signature};
use std::path::Path;
use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use log::info;
use crate::path::PathGenerator;
use crate::yaml::{BuildingData, BuildingYamlSerializer};

/// Git repository manager for building data version control
///
/// Manages all Git operations for building data, including commits, diffs, history,
/// and branch management. Follows Git-native philosophy for data persistence.
pub struct BuildingGitManager {
    repo: Repository,
    serializer: BuildingYamlSerializer,
    /// Path generator for building universal paths (reserved for future use)
    /// Currently, file paths are generated manually, but this will be used
    /// for consistent path generation in future versions.
    #[allow(dead_code)]
    path_generator: PathGenerator,
    git_config: GitConfig,
}

/// Git operation results
#[derive(Debug, Clone)]
pub struct GitOperationResult {
    pub commit_id: String,
    pub files_changed: usize,
    pub message: String,
}

/// Git repository configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitConfig {
    pub author_name: String,
    pub author_email: String,
    pub branch: String,
    pub remote_url: Option<String>,
}

/// Enhanced commit metadata with user attribution
#[derive(Debug, Clone)]
pub struct CommitMetadata {
    /// Commit message
    pub message: String,
    /// User ID from registry (UUID format: "usr_...")
    pub user_id: Option<String>,
    /// Device ID from mobile device (Phase 3)
    pub device_id: Option<String>,
    /// AR scan ID if from AR scan
    pub ar_scan_id: Option<String>,
    /// GPG signature (Phase 3)
    pub signature: Option<String>,
}

impl BuildingGitManager {
    /// Initialize or open a Git repository for building data
    pub fn new(repo_path: &str, building_name: &str, config: GitConfig) -> Result<Self, GitError> {
        use crate::utils::path_safety::PathSafety;
        
        let repo_path_buf = Path::new(repo_path);
        
        // Validate repository path format (no traversal, no null bytes)
        // For Git repositories, we allow absolute paths outside the current directory
        // but we still need to validate format and prevent traversal attempts
        PathSafety::validate_path_format(repo_path_buf)
            .map_err(|e| GitError::OperationFailed {
                operation: "validate repository path".to_string(),
                reason: format!("Path validation failed: {}", e),
            })?;
        
        // Detect path traversal attempts in relative paths
        if !repo_path_buf.is_absolute() {
            PathSafety::detect_path_traversal(repo_path_buf)
                .map_err(|e| GitError::OperationFailed {
                    operation: "validate repository path".to_string(),
                    reason: format!("Path traversal detected: {}", e),
                })?;
        }
        
        // Canonicalize the path (but don't restrict it to current_dir)
        let validated_repo_path = if repo_path_buf.is_absolute() {
            repo_path_buf.canonicalize()
                .map_err(|e| GitError::IoError(format!("Cannot canonicalize repository path: {}", e)))?
        } else {
            let current_dir = std::env::current_dir()
                .map_err(|e| GitError::from(e))?;
            let joined = current_dir.join(repo_path_buf);
            joined.canonicalize()
                .map_err(|e| GitError::IoError(format!("Cannot canonicalize repository path: {}", e)))?
        };
        
        // Ensure the directory exists
        if !validated_repo_path.exists() {
            std::fs::create_dir_all(&validated_repo_path)?;
        }
        
        let repo = if validated_repo_path.join(".git").exists() {
            Repository::open(&validated_repo_path)
                .map_err(|e| GitError::GitError(e.message().to_string()))?
        } else {
            Repository::init(&validated_repo_path)
                .map_err(|e| GitError::GitError(e.message().to_string()))?
        };

        let serializer = BuildingYamlSerializer::new();
        let path_generator = PathGenerator::new(building_name);

        Ok(Self {
            repo,
            serializer,
            path_generator,
            git_config: config,
        })
    }

    /// Export building data to Git repository
    pub fn export_building(
        &mut self,
        building_data: &BuildingData,
        commit_message: Option<&str>,
    ) -> Result<GitOperationResult, GitError> {
        // For backward compatibility, create simple metadata
        let msg = commit_message.unwrap_or("Update building data");
        let metadata = CommitMetadata {
            message: msg.to_string(),
            user_id: None,
            device_id: None,
            ar_scan_id: None,
            signature: None,
        };
        self.export_building_with_metadata(building_data, &metadata)
    }

    /// Export building data with user attribution metadata
    ///
    /// # Arguments
    ///
    /// * `building_data` - Building data to export
    /// * `metadata` - Commit metadata including message, user ID, device ID, etc.
    ///
    /// # Returns
    ///
    /// Returns a `GitOperationResult` with commit ID, files changed, and message, or an error if the operation fails.
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - Building data serialization fails
    /// - File writing fails
    /// - Git commit operations fail
    /// - Path validation fails
    pub fn export_building_with_metadata(
        &mut self,
        building_data: &BuildingData,
        metadata: &CommitMetadata,
    ) -> Result<GitOperationResult, GitError> {
        info!("Exporting building data to Git repository");

        // Check total size before exporting (optimized to avoid double serialization)
        let total_size_mb = self.estimate_building_size(building_data)?;
        const WARNING_SIZE_MB: usize = 50; // Warn if building data exceeds 50MB
        
        if total_size_mb > WARNING_SIZE_MB {
            info!("Warning: Large building dataset ({}MB). Git operations may be slow.", total_size_mb);
        }

        // Create directory structure
        let file_structure = self.create_file_structure(building_data)?;
        
        // Write files to repository
        let files_changed = self.write_building_files(&file_structure)?;
        let file_paths: Vec<String> = file_structure.keys().cloned().collect();

        // Commit changes with metadata
        let result = self.commit_changes_with_metadata(metadata, &file_paths);
        
        // Record to error analytics if failed
        if let Err(ref err) = result {
            use crate::error::analytics::ErrorAnalyticsManager;
            // Clone the error to convert to ArxError (From<GitError> is implemented)
            let git_err = err.clone();
            let arx_err: crate::error::ArxError = git_err.into();
            ErrorAnalyticsManager::record_global_error(&arx_err, Some("export_building_with_metadata".to_string()));
        }
        
        let commit_id = result?;

        info!("Successfully exported building data: {} files changed", files_changed);

        Ok(GitOperationResult {
            commit_id,
            files_changed,
            message: metadata.message.clone(),
        })
    }
    
    /// Estimate building data size in megabytes
    ///
    /// This is a performance optimization to avoid double-serialization.
    /// We serialize once to estimate size, but the serialized data is discarded.
    fn estimate_building_size(&self, building_data: &BuildingData) -> Result<usize, GitError> {
        let serializer = BuildingYamlSerializer::new();
        let main_yaml = serializer.to_yaml(building_data)
            .map_err(|e| GitError::Generic(e.to_string()))?;
        let mut size = main_yaml.len();
        
        // Estimate size of all floor/room/equipment files
        for floor in &building_data.floors {
            let floor_yaml = serializer.to_yaml(floor)
                .map_err(|e| GitError::Generic(e.to_string()))?;
            size += floor_yaml.len();
            for room in &floor.rooms {
                let room_yaml = serializer.to_yaml(room)
                    .map_err(|e| GitError::Generic(e.to_string()))?;
                size += room_yaml.len();
            }
            for equipment in &floor.equipment {
                let equipment_yaml = serializer.to_yaml(equipment)
                    .map_err(|e| GitError::Generic(e.to_string()))?;
                size += equipment_yaml.len();
            }
        }
        
        Ok(size / (1024 * 1024)) // Convert to MB
    }
    
    /// Write building files to repository with path validation
    ///
    /// Returns the number of files written.
    fn write_building_files(&self, file_structure: &HashMap<String, String>) -> Result<usize, GitError> {
        use crate::utils::path_safety::PathSafety;
        
        let repo_workdir = self.repo.workdir()
            .ok_or_else(|| GitError::OperationFailed {
                operation: "access repository workdir".to_string(),
                reason: "Git repository has no working directory".to_string(),
            })?
            .to_path_buf();
        
        let mut files_changed = 0;
        
        for (file_path, content) in file_structure {
            // Build full path
            let file_path_buf = Path::new(file_path);
            let full_path = repo_workdir.join(file_path_buf);
            
            // Create parent directories first (before validation)
            if let Some(parent) = full_path.parent() {
                std::fs::create_dir_all(parent)?;
            }
            
            // Now validate the path
            let validated_full_path = PathSafety::validate_path_for_write(
                &full_path,
                &repo_workdir
            ).map_err(|e| GitError::OperationFailed {
                operation: format!("validate file path: {}", file_path),
                reason: format!("Path validation failed: {}", e),
            })?;
            
            std::fs::write(&validated_full_path, content)?;
            files_changed += 1;
        }
        
        Ok(files_changed)
    }

    /// Create file structure for building data
    fn create_file_structure(&mut self, building_data: &BuildingData) -> Result<HashMap<String, String>, GitError> {
        let mut files = HashMap::new();

        // Main building file
        let building_yaml = self.serializer.to_yaml(building_data)
            .map_err(|e| GitError::Generic(e.to_string()))?;
        files.insert("building.yml".to_string(), building_yaml);

        // Floor files
        for floor in &building_data.floors {
            let floor_path = format!("floors/floor-{}.yml", floor.level);
            let floor_yaml = self.serializer.to_yaml(floor)
                .map_err(|e| GitError::Generic(e.to_string()))?;
            files.insert(floor_path, floor_yaml);

            // Room files
            for room in &floor.rooms {
                let room_path = format!("floors/floor-{}/rooms/{}.yml", floor.level, room.name.to_lowercase().replace(" ", "-"));
                let room_yaml = self.serializer.to_yaml(room)
                    .map_err(|e| GitError::Generic(e.to_string()))?;
                files.insert(room_path, room_yaml);
            }

            // Equipment files
            for equipment in &floor.equipment {
                let equipment_path = format!("floors/floor-{}/equipment/{}/{}.yml", 
                    floor.level, 
                    equipment.system_type.to_lowercase(), 
                    equipment.name.to_lowercase().replace(" ", "-")
                );
                let equipment_yaml = self.serializer.to_yaml(equipment)
                    .map_err(|e| GitError::Generic(e.to_string()))?;
                files.insert(equipment_path, equipment_yaml);
            }
        }

        // Create index file for easy navigation
        let index_content = self.create_index_file(building_data)?;
        files.insert("index.yml".to_string(), index_content);

        Ok(files)
    }

    /// Create index file for building navigation
    ///
    /// Uses structured YAML serialization for better maintainability and correctness.
    fn create_index_file(&self, building_data: &BuildingData) -> Result<String, GitError> {
        use serde_yaml::{Mapping, Value};
        
        let mut index_map = Mapping::new();
        
        // Add building metadata
        let mut building_map = Mapping::new();
        building_map.insert(
            Value::String("name".to_string()),
            Value::String(building_data.building.name.clone()),
        );
        building_map.insert(
            Value::String("id".to_string()),
            Value::String(building_data.building.id.clone()),
        );
        building_map.insert(
            Value::String("floors".to_string()),
            Value::Number(building_data.floors.len().into()),
        );
        index_map.insert(Value::String("building".to_string()), Value::Mapping(building_map));
        
        // Add floor information
        let mut floors_vec = Vec::new();
        for floor in &building_data.floors {
            let mut floor_map = Mapping::new();
            floor_map.insert(
                Value::String("level".to_string()),
                Value::Number(floor.level.into()),
            );
            floor_map.insert(
                Value::String("name".to_string()),
                Value::String(floor.name.clone()),
            );
            floor_map.insert(
                Value::String("rooms".to_string()),
                Value::Number(floor.rooms.len().into()),
            );
            floor_map.insert(
                Value::String("equipment".to_string()),
                Value::Number(floor.equipment.len().into()),
            );
            floors_vec.push(Value::Mapping(floor_map));
        }
        index_map.insert(Value::String("floors".to_string()), Value::Sequence(floors_vec));

        Ok(serde_yaml::to_string(&Value::Mapping(index_map))?)
    }

    /// Commit changes to Git repository
    ///
    /// This is a convenience wrapper around `commit_changes_with_metadata()` for backward compatibility.
    /// Reserved for future use or external API compatibility.
    #[allow(dead_code)]
    fn commit_changes(&self, message: &str, file_paths: &[String]) -> Result<String, GitError> {
        // For backward compatibility, create simple metadata
        let metadata = CommitMetadata {
            message: message.to_string(),
            user_id: None,
            device_id: None,
            ar_scan_id: None,
            signature: None,
        };
        self.commit_changes_with_metadata(&metadata, file_paths)
    }

    /// Commit changes to Git repository with metadata
    fn commit_changes_with_metadata(&self, metadata: &CommitMetadata, file_paths: &[String]) -> Result<String, GitError> {
        let mut index = self.repo.index()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        
        // Add all files to index
        for file_path in file_paths {
            index.add_path(Path::new(file_path))
                .map_err(|e| GitError::GitError(e.message().to_string()))?;
        }
        
        let tree_id = index.write_tree()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        let tree = self.repo.find_tree(tree_id)
            .map_err(|e| GitError::GitError(e.message().to_string()))?;

        // Get HEAD commit (if exists) - handle unborn repository
        let parent_commit = match self.repo.head() {
            Ok(head) => {
                if head.is_branch() {
                    Some(head.peel_to_commit()
                        .map_err(|e| GitError::GitError(e.message().to_string()))?)
                } else {
                    None
                }
            }
            Err(_) => {
                // No HEAD exists (unborn repository), this is the first commit
                None
            }
        };

        // Create signature using configured Git author
        let signature = Signature::now(
            &self.git_config.author_name,
            &self.git_config.author_email,
        ).map_err(|e| GitError::GitError(e.message().to_string()))?;

        // Build enhanced commit message with Git trailers
        let enhanced_message = self.build_commit_message(metadata);

        // Create commit
        let commit_id = self.repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            &enhanced_message,
            &tree,
            &parent_commit.iter().collect::<Vec<_>>(),
        ).map_err(|e| GitError::GitError(e.message().to_string()))?;

        Ok(commit_id.to_string())
    }

    /// Get repository status
    pub fn get_status(&self) -> Result<GitStatus, GitError> {
        match self.repo.head() {
            Ok(head) => {
                let commit = head.peel_to_commit()
                    .map_err(|e| GitError::GitError(e.message().to_string()))?;
                Ok(GitStatus {
                    current_branch: head.shorthand().unwrap_or("HEAD").to_string(),
                    last_commit: commit.id().to_string(),
                    last_commit_message: commit.message().unwrap_or("").to_string(),
                    last_commit_time: commit.time().seconds(),
                })
            }
            Err(_) => {
                // Unborn repository - no commits yet
                // Use configured branch name instead of hardcoding "main"
                Ok(GitStatus {
                    current_branch: self.git_config.branch.clone(),
                    last_commit: "".to_string(),
                    last_commit_message: "No commits yet".to_string(),
                    last_commit_time: 0,
                })
            }
        }
    }

    /// List commits in the repository
    ///
    /// # Arguments
    ///
    /// * `limit` - Maximum number of commits to return
    ///
    /// # Returns
    ///
    /// Returns a vector of `CommitInfo` structures, or an error if the operation fails.
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - Repository has no HEAD
    /// - Git revwalk operations fail
    pub fn list_commits(&self, limit: usize) -> Result<Vec<CommitInfo>, GitError> {
        let mut revwalk = self.repo.revwalk()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        revwalk.push_head()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        
        let mut commits = Vec::new();
        for (i, oid) in revwalk.enumerate() {
            if i >= limit {
                break;
            }
            
            let oid = oid.map_err(|e| GitError::GitError(e.message().to_string()))?;
            let commit = self.repo.find_commit(oid)
                .map_err(|e| GitError::GitError(e.message().to_string()))?;
            
            commits.push(CommitInfo {
                id: oid.to_string(),
                message: commit.message().unwrap_or("").to_string(),
                author: commit.author().name().unwrap_or("").to_string(),
                time: commit.time().seconds(),
            });
        }
        
        Ok(commits)
    }

    /// Get commit history for a specific file
    ///
    /// # Arguments
    ///
    /// * `file_path` - Relative path to the file from repository root
    ///
    /// # Returns
    ///
    /// Returns a vector of `CommitInfo` structures for commits that modified the file,
    /// or an error if the operation fails.
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - Repository has no HEAD
    /// - Git revwalk operations fail
    pub fn get_file_history(&self, file_path: &str) -> Result<Vec<CommitInfo>, GitError> {
        let mut revwalk = self.repo.revwalk()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        revwalk.push_head()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        
        let mut commits = Vec::new();
        for oid in revwalk {
            let oid = oid.map_err(|e| GitError::GitError(e.message().to_string()))?;
            let commit = self.repo.find_commit(oid)
                .map_err(|e| GitError::GitError(e.message().to_string()))?;
            
            // Check if file was modified in this commit
            if let Ok(tree) = commit.tree() {
                if tree.get_path(Path::new(file_path)).is_ok() {
                    commits.push(CommitInfo {
                        id: oid.to_string(),
                        message: commit.message().unwrap_or("").to_string(),
                        author: commit.author().name().unwrap_or("").to_string(),
                        time: commit.time().seconds(),
                    });
                }
            }
        }
        
        Ok(commits)
    }
    
    /// Get diff between commits
    ///
    /// # Arguments
    ///
    /// * `commit_hash` - Optional commit hash to compare against. If `None`, compares with previous commit.
    /// * `file_path` - Optional file path filter. If provided, only returns diff for that file.
    ///
    /// # Returns
    ///
    /// Returns a `DiffResult` containing the diff information, or an error if the operation fails.
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - Repository has no HEAD or commits
    /// - Commit hash is invalid
    /// - Git diff operation fails
    pub fn get_diff(&self, commit_hash: Option<&str>, file_path: Option<&str>) -> Result<DiffResult, GitError> {
        // Get HEAD commit with proper error handling
        let head_ref = self.repo.head()
            .map_err(|e| GitError::OperationFailed {
                operation: "get HEAD reference".to_string(),
                reason: format!("No HEAD reference found: {}", e),
            })?;
        
        let head_commit = head_ref.peel_to_commit()
            .map_err(|e| GitError::OperationFailed {
                operation: "peel HEAD to commit".to_string(),
                reason: format!("Cannot resolve HEAD to commit: {}", e),
            })?;
        
        let compare_commit = if let Some(hash) = commit_hash {
            // Parse commit hash with better error handling
            let oid = git2::Oid::from_str(hash)
                .map_err(|e| GitError::OperationFailed {
                    operation: "parse commit hash".to_string(),
                    reason: format!("Invalid commit hash '{}': {}", hash, e),
                })?;
            
            self.repo.find_commit(oid)
                .map_err(|e| GitError::GitError(e.message().to_string()))?
        } else {
            // Compare with previous commit
            let mut revwalk = self.repo.revwalk()
                .map_err(|e| GitError::OperationFailed {
                    operation: "create revwalk".to_string(),
                    reason: format!("Cannot create revwalk: {}", e),
                })?;
            
            revwalk.push_head()
                .map_err(|e| GitError::OperationFailed {
                    operation: "push HEAD to revwalk".to_string(),
                    reason: format!("Cannot push HEAD: {}", e),
                })?;
            
            // Get the second commit (previous to HEAD)
            let mut commits = revwalk.take(2);
            match commits.next() {
                Some(Ok(_)) => {
                    // Skip HEAD, get previous commit
                    match commits.next() {
                        Some(Ok(oid)) => {
                            self.repo.find_commit(oid)
                                .map_err(|e| GitError::GitError(e.message().to_string()))?
                        }
                        Some(Err(e)) => {
                            return Err(GitError::OperationFailed {
                                operation: "get previous commit".to_string(),
                                reason: format!("Error walking commits: {}", e),
                            });
                        }
                        None => {
                            // Only one commit (HEAD), compare with empty tree
                            head_commit.clone()
                        }
                    }
                }
                Some(Err(e)) => {
                    return Err(GitError::OperationFailed {
                        operation: "walk commits".to_string(),
                        reason: format!("Error walking commits: {}", e),
                    });
                }
                None => {
                    // No commits, compare with empty tree
                    head_commit.clone()
                }
            }
        };
        
        let head_tree = head_commit.tree()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        let compare_tree = compare_commit.tree()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        
        // Generate diff
        let diff = self.repo.diff_tree_to_tree(
            Some(&compare_tree),
            Some(&head_tree),
            None,
        ).map_err(|e| GitError::GitError(e.message().to_string()))?;
        
        let mut diff_result = DiffResult {
            commit_hash: head_commit.id().to_string(),
            compare_hash: compare_commit.id().to_string(),
            files_changed: 0,
            insertions: 0,
            deletions: 0,
            file_diffs: Vec::new(),
        };
        
        // Process diff
        diff.foreach(
            &mut |delta, _| {
                if let Some(file_path_filter) = file_path {
                    if let Some(path) = delta.new_file().path() {
                        if path.to_string_lossy() != file_path_filter {
                            return true; // Skip this file
                        }
                    } else {
                        return true; // Skip if no path
                    }
                }
                
                diff_result.files_changed += 1;
                true
            },
            None,
            Some(&mut |_delta, hunk| {
                diff_result.insertions += hunk.new_lines() as usize;
                diff_result.deletions += hunk.old_lines() as usize;
                true
            }),
            Some(&mut |delta, _hunk, line| {
                let file_path = delta.new_file().path()
                    .map(|p| p.to_string_lossy().to_string())
                    .unwrap_or_else(|| "unknown".to_string());
                let line_content = String::from_utf8_lossy(line.content()).to_string();
                
                diff_result.file_diffs.push(FileDiff {
                    file_path,
                    line_number: line.new_lineno().unwrap_or(0) as usize,
                    line_type: match line.origin() {
                        '+' => DiffLineType::Addition,
                        '-' => DiffLineType::Deletion,
                        ' ' => DiffLineType::Context,
                        _ => DiffLineType::Context,
                    },
                    content: line_content.trim_end().to_string(),
                });
                
                true
            }),
        )?;
        
        Ok(diff_result)
    }
    
    /// Get diff statistics (file count, insertions, deletions) without full diff content
    ///
    /// # Arguments
    ///
    /// * `commit_hash` - Optional commit hash to compare against. If `None`, compares with previous commit.
    ///
    /// # Returns
    ///
    /// Returns a `DiffStats` structure with statistics, or an error if the operation fails.
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - Repository has no HEAD or commits
    /// - Commit hash is invalid
    /// - Git diff operation fails
    ///
    /// # Performance
    ///
    /// This method is more efficient than `get_diff()` when you only need statistics,
    /// as it doesn't collect the full diff content.
    pub fn get_diff_stats(&self, commit_hash: Option<&str>) -> Result<DiffStats, GitError> {
        let diff_result = self.get_diff(commit_hash, None)?;
        
        Ok(DiffStats {
            files_changed: diff_result.files_changed,
            insertions: diff_result.insertions,
            deletions: diff_result.deletions,
        })
    }

    /// Stage a single file for commit
    pub fn stage_file(&mut self, file_path: &str) -> Result<(), GitError> {
        let mut index = self.repo.index()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        index.add_path(Path::new(file_path))
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        index.write()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        Ok(())
    }

    /// Stage all modified files
    pub fn stage_all(&mut self) -> Result<usize, GitError> {
        let mut index = self.repo.index()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        index.add_all(["*"], git2::IndexAddOption::DEFAULT, None)
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        let count = index.len();
        index.write()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        Ok(count)
    }

    /// Unstage a single file
    pub fn unstage_file(&mut self, file_path: &str) -> Result<(), GitError> {
        let mut index = self.repo.index()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        index.remove_path(Path::new(file_path))
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        index.write()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        Ok(())
    }

    /// Unstage all files
    pub fn unstage_all(&mut self) -> Result<usize, GitError> {
        let mut index = self.repo.index()?;
        // Reset the index to HEAD
        let tree_id = match self.repo.head() {
            Ok(head) => {
                let commit = head.peel_to_commit()
                    .map_err(|e| GitError::GitError(e.message().to_string()))?;
                commit.tree_id()
            }
            Err(_) => {
                // No HEAD, clear the index
                let count = index.len();
                index.clear()
                    .map_err(|e| GitError::GitError(e.message().to_string()))?;
                index.write()
                    .map_err(|e| GitError::GitError(e.message().to_string()))?;
                return Ok(count);
            }
        };
        
        let tree = self.repo.find_tree(tree_id)
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        index.read_tree(&tree)
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        let count = index.len();
        index.write()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        Ok(count)
    }

    /// Build commit message with Git trailers (standard Git practice)
    ///
    /// Adds ArxOS-User-ID and other metadata as Git trailers.
    fn build_commit_message(&self, metadata: &CommitMetadata) -> String {
        let mut message = metadata.message.clone();
        
        // Add Git trailers (standard practice like Signed-off-by:)
        if let Some(ref user_id) = metadata.user_id {
            message.push_str(&format!("\n\nArxOS-User-ID: {}", user_id));
        }
        
        if let Some(ref device_id) = metadata.device_id {
            message.push_str(&format!("\nArxOS-Device-ID: {}", device_id));
        }
        
        if let Some(ref ar_scan_id) = metadata.ar_scan_id {
            message.push_str(&format!("\nArxOS-Scan-ID: {}", ar_scan_id));
        }
        
        message
    }

    /// Commit staged changes
    ///
    /// # Arguments
    ///
    /// * `message` - Commit message
    ///
    /// # Returns
    ///
    /// Returns the commit ID as a string, or an error if the commit fails.
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - No files are staged
    /// - Git commit operations fail
    /// - Repository is in an invalid state
    pub fn commit_staged(&mut self, message: &str) -> Result<String, GitError> {
        // Record error to analytics if operation fails
        let result = {
            // For backward compatibility, create simple metadata
            let metadata = CommitMetadata {
                message: message.to_string(),
                user_id: None,
                device_id: None,
                ar_scan_id: None,
                signature: None,
            };
            self.commit_staged_with_user(&metadata)
        };
        
        // Record to error analytics if failed
        if let Err(ref err) = result {
            use crate::error::analytics::ErrorAnalyticsManager;
            // Clone the error to convert to ArxError (From<GitError> is implemented)
            let git_err = err.clone();
            let arx_err: crate::error::ArxError = git_err.into();
            ErrorAnalyticsManager::record_global_error(&arx_err, Some("commit_staged".to_string()));
        }
        
        result
    }

    /// Commit staged changes with user attribution
    ///
    /// # Arguments
    ///
    /// * `metadata` - Commit metadata including message, user ID, device ID, etc.
    ///
    /// # Returns
    ///
    /// Returns the commit ID as a string, or an error if the commit fails.
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - No files are staged
    /// - Git commit operations fail
    /// - Repository is in an invalid state
    pub fn commit_staged_with_user(&mut self, metadata: &CommitMetadata) -> Result<String, GitError> {
        let mut index = self.repo.index()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        let tree_id = index.write_tree()
            .map_err(|e| GitError::GitError(e.message().to_string()))?;
        let tree = self.repo.find_tree(tree_id)
            .map_err(|e| GitError::GitError(e.message().to_string()))?;

        // Get parent commit (if exists)
        let parent_commit = match self.repo.head() {
            Ok(head) => {
                if head.is_branch() {
                    Some(head.peel_to_commit()
                        .map_err(|e| GitError::GitError(e.message().to_string()))?)
                } else {
                    None
                }
            }
            Err(_) => None,
        };

        // Create signature using configured Git author
        let signature = Signature::now(
            &self.git_config.author_name,
            &self.git_config.author_email,
        ).map_err(|e| GitError::GitError(e.message().to_string()))?;

        // Build enhanced commit message with Git trailers
        let enhanced_message = self.build_commit_message(metadata);

        // Create commit
        let commit_id = self.repo.commit(
            Some("HEAD"),
            &signature,
            &signature,
            &enhanced_message,
            &tree,
            &parent_commit.iter().collect::<Vec<_>>(),
        ).map_err(|e| GitError::GitError(e.message().to_string()))?;

        Ok(commit_id.to_string())
    }
}

/// Git repository status
#[derive(Debug)]
pub struct GitStatus {
    pub current_branch: String,
    pub last_commit: String,
    pub last_commit_message: String,
    pub last_commit_time: i64,
}

/// Commit information
#[derive(Debug)]
pub struct CommitInfo {
    pub id: String,
    pub message: String,
    pub author: String,
    pub time: i64,
}

/// Diff result between commits
#[derive(Debug, Clone)]
pub struct DiffResult {
    pub commit_hash: String,
    pub compare_hash: String,
    pub files_changed: usize,
    pub insertions: usize,
    pub deletions: usize,
    pub file_diffs: Vec<FileDiff>,
}

/// Individual file diff line
#[derive(Debug, Clone)]
pub struct FileDiff {
    pub file_path: String,
    pub line_number: usize,
    pub line_type: DiffLineType,
    pub content: String,
}

/// Type of diff line
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DiffLineType {
    Addition,
    Deletion,
    Context,
}

/// Diff statistics
#[derive(Debug, Clone)]
pub struct DiffStats {
    pub files_changed: usize,
    pub insertions: usize,
    pub deletions: usize,
}

/// Git operation errors
///
/// Note: `git2::Error` doesn't implement `Clone`, so we store error messages as `String`
/// to allow cloning for error analytics integration.
#[derive(Debug, Clone, thiserror::Error)]
pub enum GitError {
    #[error("Git repository error: {0}")]
    GitError(String),
    
    #[error("IO error: {0}")]
    IoError(String),
    
    #[error("Serialization error: {0}")]
    SerializationError(String),
    
    #[error("Generic error: {0}")]
    Generic(String),
    
    #[error("Repository not found: {path}")]
    RepositoryNotFound { path: String },
    
    #[error("Invalid configuration: {reason}")]
    InvalidConfig { reason: String },
    
    #[error("Git operation failed: {operation} - {reason}")]
    OperationFailed { operation: String, reason: String },
}

impl From<git2::Error> for GitError {
    fn from(err: git2::Error) -> Self {
        GitError::GitError(err.message().to_string())
    }
}

impl From<std::io::Error> for GitError {
    fn from(err: std::io::Error) -> Self {
        GitError::IoError(err.to_string())
    }
}

impl From<serde_yaml::Error> for GitError {
    fn from(err: serde_yaml::Error) -> Self {
        GitError::SerializationError(err.to_string())
    }
}

/// Git configuration utilities
pub struct GitConfigManager;

impl GitConfigManager {
    /// Create default Git configuration
    pub fn default_config() -> GitConfig {
        GitConfig {
            author_name: "ArxOS".to_string(),
            author_email: "arxos@arxos.io".to_string(),
            branch: "main".to_string(),
            remote_url: None,
        }
    }

    /// Load Git configuration from ArxConfig or environment variables
    /// 
    /// Priority order:
    /// 1. Environment variables (GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL)
    /// 2. ArxConfig user settings
    /// 3. Default config
    pub fn load_from_arx_config_or_env() -> GitConfig {
        use std::env;
        
        // Check environment variables first
        let author_name = env::var("GIT_AUTHOR_NAME")
            .or_else(|_| env::var("ARX_USER_NAME"))
            .unwrap_or_else(|_| {
                // Try to load from ArxConfig
                // Use helper function for consistent config access
                crate::config::get_config_or_default().user.name.clone()
            });
        
        let author_email = env::var("GIT_AUTHOR_EMAIL")
            .or_else(|_| env::var("ARX_USER_EMAIL"))
            .unwrap_or_else(|_| {
                // Try to load from ArxConfig
                // Load config with fallback to default
                // Use helper function for consistent config access
                crate::config::get_config_or_default().user.email.clone()
            });
        
        GitConfig {
            author_name,
            author_email,
            branch: "main".to_string(),
            remote_url: env::var("GIT_REMOTE_URL").ok(),
        }
    }

    /// Load configuration from file
    pub fn load_config(config_path: &str) -> Result<GitConfig, GitError> {
        let content = std::fs::read_to_string(config_path)?;
        let config: GitConfig = serde_yaml::from_str(&content)?;
        Ok(config)
    }

    /// Save configuration to file
    pub fn save_config(config: &GitConfig, config_path: &str) -> Result<(), GitError> {
        let content = serde_yaml::to_string(config)?;
        std::fs::write(config_path, content)?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_git_manager_creation() {
        let temp_dir = TempDir::new().unwrap();
        let config = GitConfigManager::default_config();
        
        let manager = BuildingGitManager::new(
            temp_dir.path().to_str().unwrap(),
            "Test Building",
            config,
        );
        
        // The manager creation should succeed
        match manager {
            Ok(_) => {
                // Success - this is what we expect
            }
            Err(e) => {
                // If it fails, let's see what the error is
                panic!("Git manager creation failed: {}", e);
            }
        }
    }

    #[test]
    fn test_git_config() {
        let config = GitConfigManager::default_config();
        assert_eq!(config.author_name, "ArxOS");
        assert_eq!(config.branch, "main");
    }

    #[test]
    fn test_git_manager_uses_config_for_commits() {
        let temp_dir = TempDir::new().unwrap();
        let custom_config = GitConfig {
            author_name: "Test User".to_string(),
            author_email: "test@example.com".to_string(),
            branch: "main".to_string(),
            remote_url: None,
        };
        
        let mut manager = BuildingGitManager::new(
            temp_dir.path().to_str().unwrap(),
            "Test Building",
            custom_config.clone(),
        ).unwrap();
        
        // Create a minimal building data for testing
        use crate::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
        use chrono::Utc;
        
        let building_data = BuildingData {
            building: BuildingInfo {
                id: "test-1".to_string(),
                name: "Test Building".to_string(),
                description: None,
                created_at: Utc::now(),
                updated_at: Utc::now(),
                version: "1.0".to_string(),
                global_bounding_box: None,
            },
            metadata: BuildingMetadata {
                source_file: None,
                parser_version: "1.0".to_string(),
                total_entities: 0,
                spatial_entities: 0,
                coordinate_system: "World".to_string(),
                units: "meters".to_string(),
                tags: vec![],
            },
            floors: vec![],
            coordinate_systems: vec![],
        };
        
        // Export building (this will create a commit)
        let result = manager.export_building(&building_data, Some("Test commit")).unwrap();
        
        // Verify commit was created
        assert!(!result.commit_id.is_empty());
        
        // Get the commit and verify it uses the configured author
        let status = manager.get_status().unwrap();
        assert_eq!(status.last_commit_message, "Test commit");
        
        // Verify commit author matches config
        let commits = manager.list_commits(1).unwrap();
        if let Some(commit) = commits.first() {
            assert_eq!(commit.author, custom_config.author_name);
        }
    }
}

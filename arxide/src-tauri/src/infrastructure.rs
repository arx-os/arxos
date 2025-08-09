// Infrastructure Layer for ArxIDE
// This module contains repository implementations and external services
// following Clean Architecture principles

use crate::domain::{
    Project, ProjectRepository, ExportService, EventPublisher, ExportFormat, DomainEvent,
    ProjectService,
};
use crate::application::{ProjectApplicationService, ApplicationConfig};
use serde_json;
use std::collections::HashMap;
use std::path::Path;
use std::sync::Arc;
use tokio::sync::RwLock;
use chrono::{DateTime, Utc};
use uuid::Uuid;
use log;

// File-based Project Repository Implementation
pub struct FileProjectRepository {
    base_path: String,
}

impl FileProjectRepository {
    pub fn new(base_path: String) -> Self {
        Self { base_path }
    }

    fn get_project_path(&self, project_id: &str) -> String {
        format!("{}/{}.json", self.base_path, project_id)
    }

    fn get_recent_projects_path(&self) -> String {
        format!("{}/recent_projects.json", self.base_path)
    }
}

#[async_trait::async_trait]
impl ProjectRepository for FileProjectRepository {
    async fn save(&self, project: &Project) -> Result<(), String> {
        let project_path = self.get_project_path(&project.id);

        // Ensure directory exists
        if let Some(parent) = Path::new(&project_path).parent() {
            tokio::fs::create_dir_all(parent).await
                .map_err(|e| format!("Failed to create directory: {}", e))?;
        }

        // Serialize project
        let content = serde_json::to_string_pretty(project)
            .map_err(|e| format!("Failed to serialize project: {}", e))?;

        // Write to file
        tokio::fs::write(&project_path, content).await
            .map_err(|e| format!("Failed to save project: {}", e))?;

        log::info!("Project saved to: {}", project_path);
        Ok(())
    }

    async fn load(&self, project_id: &str) -> Result<Project, String> {
        let project_path = self.get_project_path(project_id);

        if !Path::new(&project_path).exists() {
            return Err(format!("Project file not found: {}", project_path));
        }

        // Read file content
        let content = tokio::fs::read_to_string(&project_path).await
            .map_err(|e| format!("Failed to read project file: {}", e))?;

        // Deserialize project
        let project: Project = serde_json::from_str(&content)
            .map_err(|e| format!("Failed to parse project data: {}", e))?;

        log::info!("Project loaded from: {}", project_path);
        Ok(project)
    }

    async fn list_recent(&self, limit: usize) -> Result<Vec<Project>, String> {
        let recent_projects_path = self.get_recent_projects_path();

        if !Path::new(&recent_projects_path).exists() {
            return Ok(Vec::new());
        }

        // Read recent projects file
        let content = tokio::fs::read_to_string(&recent_projects_path).await
            .map_err(|e| format!("Failed to read recent projects: {}", e))?;

        // Deserialize recent projects
        let recent_project_ids: Vec<String> = serde_json::from_str(&content)
            .map_err(|e| format!("Failed to parse recent projects: {}", e))?;

        // Load each project
        let mut projects = Vec::new();
        for project_id in recent_project_ids.into_iter().take(limit) {
            match self.load(&project_id).await {
                Ok(project) => projects.push(project),
                Err(e) => {
                    log::warn!("Failed to load recent project {}: {}", project_id, e);
                }
            }
        }

        Ok(projects)
    }

    async fn delete(&self, project_id: &str) -> Result<(), String> {
        let project_path = self.get_project_path(project_id);

        if Path::new(&project_path).exists() {
            tokio::fs::remove_file(&project_path).await
                .map_err(|e| format!("Failed to delete project file: {}", e))?;

            log::info!("Project deleted: {}", project_path);
        }

        Ok(())
    }
}

// In-Memory Project Repository Implementation (for testing)
pub struct InMemoryProjectRepository {
    projects: Arc<RwLock<HashMap<String, Project>>>,
    recent_projects: Arc<RwLock<Vec<String>>>,
}

impl InMemoryProjectRepository {
    pub fn new() -> Self {
        Self {
            projects: Arc::new(RwLock::new(HashMap::new())),
            recent_projects: Arc::new(RwLock::new(Vec::new())),
        }
    }
}

#[async_trait::async_trait]
impl ProjectRepository for InMemoryProjectRepository {
    async fn save(&self, project: &Project) -> Result<(), String> {
        let mut projects = self.projects.write().await;
        projects.insert(project.id.clone(), project.clone());

        // Update recent projects
        let mut recent = self.recent_projects.write().await;
        recent.retain(|id| id != &project.id);
        recent.insert(0, project.id.clone());

        log::info!("Project saved to memory: {}", project.id);
        Ok(())
    }

    async fn load(&self, project_id: &str) -> Result<Project, String> {
        let projects = self.projects.read().await;
        projects.get(project_id)
            .cloned()
            .ok_or_else(|| format!("Project not found: {}", project_id))
    }

    async fn list_recent(&self, limit: usize) -> Result<Vec<Project>, String> {
        let projects = self.projects.read().await;
        let recent = self.recent_projects.read().await;

        let mut result = Vec::new();
        for project_id in recent.iter().take(limit) {
            if let Some(project) = projects.get(project_id) {
                result.push(project.clone());
            }
        }

        Ok(result)
    }

    async fn delete(&self, project_id: &str) -> Result<(), String> {
        let mut projects = self.projects.write().await;
        projects.remove(project_id);

        let mut recent = self.recent_projects.write().await;
        recent.retain(|id| id != project_id);

        log::info!("Project deleted from memory: {}", project_id);
        Ok(())
    }
}

// Export Service Implementation
pub struct ArxideExportService;

impl ArxideExportService {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait::async_trait]
impl ExportService for ArxideExportService {
    async fn export_project(&self, project: &Project, format: ExportFormat) -> Result<String, String> {
        project.export(format)
    }
}

// Event Publisher Implementation
pub struct LoggingEventPublisher;

impl LoggingEventPublisher {
    pub fn new() -> Self {
        Self
    }
}

#[async_trait::async_trait]
impl EventPublisher for LoggingEventPublisher {
    async fn publish(&self, event: &DomainEvent) -> Result<(), String> {
        match event {
            DomainEvent::ProjectCreated(e) => {
                log::info!("Project created: {} ({})", e.name, e.project_id);
            }
            DomainEvent::ProjectOpened(e) => {
                log::info!("Project opened: {} from {}", e.project_id, e.path);
            }
            DomainEvent::ProjectSaved(e) => {
                log::info!("Project saved: {} to {}", e.project_id, e.path);
            }
            DomainEvent::ProjectExported(e) => {
                log::info!("Project exported: {} to {:?}", e.project_id, e.format);
            }
            DomainEvent::ObjectAdded(e) => {
                log::debug!("Object added: {} ({}) to project {}", e.object_type, e.object_id, e.project_id);
            }
            DomainEvent::ObjectModified(e) => {
                log::debug!("Object modified: {} in project {}", e.object_id, e.project_id);
            }
            DomainEvent::ObjectDeleted(e) => {
                log::debug!("Object deleted: {} from project {}", e.object_id, e.project_id);
            }
            DomainEvent::ConstraintAdded(e) => {
                log::debug!("Constraint added: {} ({}) to project {}", e.constraint_type, e.constraint_id, e.project_id);
            }
            DomainEvent::ConstraintViolated(e) => {
                log::warn!("Constraint violated: {} in project {}: {}", e.constraint_id, e.project_id, e.message);
            }
        }
        Ok(())
    }
}

// Infrastructure Services
pub struct InfrastructureServices {
    pub project_repository: Box<dyn ProjectRepository>,
    pub export_service: Box<dyn ExportService>,
    pub event_publisher: Box<dyn EventPublisher>,
    pub project_service: ProjectService,
    pub application_service: ProjectApplicationService,
    pub config: ApplicationConfig,
}

impl InfrastructureServices {
    pub fn new(config: ApplicationConfig) -> Self {
        // Create repository (file-based for production, in-memory for testing)
        let repository: Box<dyn ProjectRepository> = if cfg!(test) {
            Box::new(InMemoryProjectRepository::new())
        } else {
            let app_dir = dirs::data_dir()
                .unwrap_or_else(|| std::path::PathBuf::from("."))
                .join("arxide")
                .to_string_lossy()
                .to_string();
            Box::new(FileProjectRepository::new(app_dir))
        };

        // Create services
        let export_service = Box::new(ArxideExportService::new());
        let event_publisher = Box::new(LoggingEventPublisher::new());

        // Create domain service
        let project_service = ProjectService::new(
            repository.clone(),
            export_service.clone(),
            event_publisher.clone(),
        );

        // Create application service
        let application_service = ProjectApplicationService::new(
            project_service.clone(),
            repository.clone(),
        );

        Self {
            project_repository: repository,
            export_service,
            event_publisher,
            project_service,
            application_service,
            config,
        }
    }

    pub fn get_project_service(&self) -> &ProjectService {
        &self.project_service
    }

    pub fn get_application_service(&self) -> &ProjectApplicationService {
        &self.application_service
    }

    pub fn get_config(&self) -> &ApplicationConfig {
        &self.config
    }
}

// Configuration Management
pub struct ConfigurationManager {
    config: ApplicationConfig,
}

impl ConfigurationManager {
    pub fn new() -> Self {
        Self {
            config: ApplicationConfig::default(),
        }
    }

    pub fn load_from_file(&mut self, path: &str) -> Result<(), String> {
        if Path::new(path).exists() {
            let content = std::fs::read_to_string(path)
                .map_err(|e| format!("Failed to read config file: {}", e))?;

            let config: ApplicationConfig = serde_json::from_str(&content)
                .map_err(|e| format!("Failed to parse config: {}", e))?;

            self.config = config;
            log::info!("Configuration loaded from: {}", path);
        }
        Ok(())
    }

    pub fn save_to_file(&self, path: &str) -> Result<(), String> {
        let content = serde_json::to_string_pretty(&self.config)
            .map_err(|e| format!("Failed to serialize config: {}", e))?;

        std::fs::write(path, content)
            .map_err(|e| format!("Failed to write config file: {}", e))?;

        log::info!("Configuration saved to: {}", path);
        Ok(())
    }

    pub fn get_config(&self) -> &ApplicationConfig {
        &self.config
    }

    pub fn update_config(&mut self, config: ApplicationConfig) {
        self.config = config;
    }
}

// File System Service
pub struct FileSystemService {
    base_path: String,
}

impl FileSystemService {
    pub fn new(base_path: String) -> Self {
        Self { base_path }
    }

    pub async fn ensure_directory(&self, path: &str) -> Result<(), String> {
        let full_path = format!("{}/{}", self.base_path, path);
        tokio::fs::create_dir_all(&full_path).await
            .map_err(|e| format!("Failed to create directory: {}", e))
    }

    pub async fn read_file(&self, path: &str) -> Result<String, String> {
        let full_path = format!("{}/{}", self.base_path, path);
        tokio::fs::read_to_string(&full_path).await
            .map_err(|e| format!("Failed to read file: {}", e))
    }

    pub async fn write_file(&self, path: &str, content: &str) -> Result<(), String> {
        let full_path = format!("{}/{}", self.base_path, path);

        // Ensure parent directory exists
        if let Some(parent) = Path::new(&full_path).parent() {
            tokio::fs::create_dir_all(parent).await
                .map_err(|e| format!("Failed to create directory: {}", e))?;
        }

        tokio::fs::write(&full_path, content).await
            .map_err(|e| format!("Failed to write file: {}", e))
    }

    pub async fn delete_file(&self, path: &str) -> Result<(), String> {
        let full_path = format!("{}/{}", self.base_path, path);
        tokio::fs::remove_file(&full_path).await
            .map_err(|e| format!("Failed to delete file: {}", e))
    }

    pub async fn list_files(&self, path: &str) -> Result<Vec<String>, String> {
        let full_path = format!("{}/{}", self.base_path, path);
        let mut entries = tokio::fs::read_dir(&full_path).await
            .map_err(|e| format!("Failed to read directory: {}", e))?;

        let mut files = Vec::new();
        while let Some(entry) = entries.next_entry().await
            .map_err(|e| format!("Failed to read directory entry: {}", e))? {
            if let Ok(file_name) = entry.file_name().into_string() {
                files.push(file_name);
            }
        }

        Ok(files)
    }

    pub async fn file_exists(&self, path: &str) -> bool {
        let full_path = format!("{}/{}", self.base_path, path);
        Path::new(&full_path).exists()
    }

    pub async fn get_file_size(&self, path: &str) -> Result<u64, String> {
        let full_path = format!("{}/{}", self.base_path, path);
        let metadata = tokio::fs::metadata(&full_path).await
            .map_err(|e| format!("Failed to get file metadata: {}", e))?;
        Ok(metadata.len())
    }

    pub async fn get_file_modified_time(&self, path: &str) -> Result<DateTime<Utc>, String> {
        let full_path = format!("{}/{}", self.base_path, path);
        let metadata = tokio::fs::metadata(&full_path).await
            .map_err(|e| format!("Failed to get file metadata: {}", e))?;

        let modified = metadata.modified()
            .map_err(|e| format!("Failed to get modification time: {}", e))?;

        let datetime: DateTime<Utc> = modified.into();
        Ok(datetime)
    }
}

// Backup Service
pub struct BackupService {
    file_system: FileSystemService,
    backup_path: String,
}

impl BackupService {
    pub fn new(base_path: String) -> Self {
        let backup_path = format!("{}/backups", base_path);
        Self {
            file_system: FileSystemService::new(base_path),
            backup_path,
        }
    }

    pub async fn create_backup(&self, project_id: &str) -> Result<String, String> {
        let timestamp = Utc::now().format("%Y%m%d_%H%M%S").to_string();
        let backup_filename = format!("{}_{}.json", project_id, timestamp);
        let backup_path = format!("{}/{}", self.backup_path, backup_filename);

        // Read project file
        let project_content = self.file_system.read_file(&format!("{}.json", project_id)).await?;

        // Write backup
        self.file_system.write_file(&backup_path, &project_content).await?;

        log::info!("Backup created: {}", backup_path);
        Ok(backup_path)
    }

    pub async fn restore_backup(&self, backup_filename: &str) -> Result<String, String> {
        let backup_content = self.file_system.read_file(&format!("backups/{}", backup_filename)).await?;

        // Parse project ID from backup filename
        let project_id = backup_filename.split('_').next()
            .ok_or_else(|| "Invalid backup filename".to_string())?;

        // Restore project
        self.file_system.write_file(&format!("{}.json", project_id), &backup_content).await?;

        log::info!("Backup restored: {} -> {}", backup_filename, project_id);
        Ok(project_id.to_string())
    }

    pub async fn list_backups(&self) -> Result<Vec<String>, String> {
        self.file_system.list_files("backups").await
    }

    pub async fn delete_backup(&self, backup_filename: &str) -> Result<(), String> {
        self.file_system.delete_file(&format!("backups/{}", backup_filename)).await
    }
}

// Error handling for infrastructure layer
#[derive(Debug, thiserror::Error)]
pub enum InfrastructureError {
    #[error("File system error: {0}")]
    FileSystemError(String),
    #[error("Serialization error: {0}")]
    SerializationError(String),
    #[error("Configuration error: {0}")]
    ConfigurationError(String),
    #[error("Backup error: {0}")]
    BackupError(String),
}

impl From<InfrastructureError> for String {
    fn from(err: InfrastructureError) -> String {
        err.to_string()
    }
}

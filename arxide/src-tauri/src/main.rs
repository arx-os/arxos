// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// Clean Architecture Layers
mod domain;
mod application;
mod infrastructure;

use domain::{Project, ExportFormat, ConstraintSeverity};
use application::{ProjectApplicationService, ApplicationConfig, CreateProjectRequest, AddObjectRequest, AddConstraintRequest, ExportProjectRequest};
use infrastructure::{InfrastructureServices, ConfigurationManager, BackupService, FileSystemService};

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::Path;
use chrono::{DateTime, Utc};
use uuid::Uuid;

// Custom error type for better error handling
#[derive(Debug, thiserror::Error)]
pub enum ArxideError {
    #[error("File operation failed: {0}")]
    FileError(#[from] std::io::Error),
    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),
    #[error("Invalid project data: {0}")]
    ValidationError(String),
    #[error("Project not found: {0}")]
    ProjectNotFound(String),
    #[error("Export failed: {0}")]
    ExportError(String),
    #[error("System error: {0}")]
    SystemError(String),
}

impl From<ArxideError> for String {
    fn from(err: ArxideError) -> String {
        err.to_string()
    }
}

// Project data structure with validation
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ProjectData {
    pub id: String,
    pub name: String,
    pub description: String,
    pub created_at: String,
    pub last_modified: String,
    pub objects: Vec<serde_json::Value>,
    pub constraints: Vec<serde_json::Value>,
    pub settings: HashMap<String, serde_json::Value>,
}

impl ProjectData {
    pub fn new(name: String, description: String) -> Self {
        let now = Utc::now().to_rfc3339();
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            description,
            created_at: now.clone(),
            last_modified: now,
            objects: Vec::new(),
            constraints: Vec::new(),
            settings: HashMap::new(),
        }
    }

    pub fn validate(&self) -> Result<(), ArxideError> {
        if self.name.trim().is_empty() {
            return Err(ArxideError::ValidationError("Project name cannot be empty".to_string()));
        }
        if self.description.len() > 1000 {
            return Err(ArxideError::ValidationError("Project description too long".to_string()));
        }
        Ok(())
    }

    pub fn update_last_modified(&mut self) {
        self.last_modified = Utc::now().to_rfc3339();
    }
}

// Application state management
#[derive(Debug, Clone)]
pub struct ArxideState {
    pub recent_projects: Vec<ProjectData>,
    pub current_project: Option<ProjectData>,
    pub app_initialized: bool,
}

impl Default for ArxideState {
    fn default() -> Self {
        Self {
            recent_projects: Vec::new(),
            current_project: None,
            app_initialized: false,
        }
    }
}

mod commands {
    use super::*;
    use std::sync::Arc;
    use tokio::sync::RwLock;
    use notify::{Watcher, RecursiveMode};

    // Global infrastructure services
    lazy_static::lazy_static! {
        static ref INFRASTRUCTURE: Arc<RwLock<InfrastructureServices>> = Arc::new(RwLock::new(
            InfrastructureServices::new(ApplicationConfig::default())
        ));
    }

    /// Initialize ArxIDE application
    #[tauri::command]
    pub async fn initialize_arxide() -> Result<(), String> {
        log::info!("Initializing ArxIDE application...");

        let infrastructure = INFRASTRUCTURE.read().await;
        let application_service = infrastructure.get_application_service();

        // Load recent projects
        let recent_projects = application_service.list_recent_projects(10).await?;
        log::info!("Loaded {} recent projects", recent_projects.len());

        log::info!("ArxIDE initialized successfully");
        Ok(())
    }

    /// Get recent projects
    #[tauri::command]
    pub async fn get_recent_projects() -> Result<Vec<application::ProjectInfo>, String> {
        let infrastructure = INFRASTRUCTURE.read().await;
        let application_service = infrastructure.get_application_service();

        application_service.list_recent_projects(10).await
    }

    /// Greet command for testing
    #[tauri::command]
    pub async fn greet(name: String) -> Result<String, String> {
        if name.trim().is_empty() {
            return Err("Name cannot be empty".to_string());
        }
        Ok(format!("Hello, {}! Welcome to ArxIDE", name))
    }

    /// Create a new project
    #[tauri::command]
    pub async fn create_project(name: String, description: String) -> Result<application::CreateProjectResponse, String> {
        log::info!("Creating new project: {}", name);

        let infrastructure = INFRASTRUCTURE.read().await;
        let application_service = infrastructure.get_application_service();

        let request = CreateProjectRequest {
            name,
            description,
        };

        let response = application_service.create_project(request).await?;

        log::info!("Project created successfully: {}", response.project_id);
        Ok(response)
    }

    /// Open project from file
    #[tauri::command]
    pub async fn open_project(path: String) -> Result<ProjectData, String> {
        log::info!("Opening project from: {}", path);

        if !Path::new(&path).exists() {
            return Err(format!("Project file not found: {}", path));
        }

        let content = tokio::fs::read_to_string(&path).await
            .map_err(|e| format!("Failed to read project file: {}", e))?;

        let project: ProjectData = serde_json::from_str(&content)
            .map_err(|e| format!("Failed to parse project data: {}", e))?;

        project.validate().map_err(|e| e.to_string())?;

        // Update recent projects
        let mut state = APP_STATE.write().await;
        state.current_project = Some(project.clone());

        // Add to recent projects if not already present
        if !state.recent_projects.iter().any(|p| p.id == project.id) {
            state.recent_projects.insert(0, project.clone());
            if state.recent_projects.len() > 10 {
                state.recent_projects.truncate(10);
            }

            if let Err(e) = save_recent_projects_to_storage(&state.recent_projects).await {
                log::warn!("Failed to save recent projects: {}", e);
            }
        }

        log::info!("Project opened successfully: {}", project.id);
        Ok(project)
    }

    /// Save project to file
    #[tauri::command]
    pub async fn save_project(project: ProjectData, path: String) -> Result<(), String> {
        log::info!("Saving project to: {}", path);

        project.validate().map_err(|e| e.to_string())?;

        let mut project_to_save = project.clone();
        project_to_save.update_last_modified();

        let content = serde_json::to_string_pretty(&project_to_save)
            .map_err(|e| format!("Failed to serialize project: {}", e))?;

        // Ensure directory exists
        if let Some(parent) = Path::new(&path).parent() {
            tokio::fs::create_dir_all(parent).await
                .map_err(|e| format!("Failed to create directory: {}", e))?;
        }

        tokio::fs::write(&path, content).await
            .map_err(|e| format!("Failed to save project: {}", e))?;

        // Update current project
        let mut state = APP_STATE.write().await;
        state.current_project = Some(project_to_save);

        log::info!("Project saved successfully");
        Ok(())
    }

    /// Export project to SVGX format
    #[tauri::command]
    pub async fn export_to_svgx(project: Project) -> Result<String, String> {
        log::info!("Exporting project to SVGX: {}", project.id);

        let infrastructure = INFRASTRUCTURE.read().await;
        let application_service = infrastructure.get_application_service();

        let request = ExportProjectRequest {
            format: application::ExportFormatDto::SVGX,
        };

        let response = application_service.export_project(&project, request).await?;

        log::info!("SVGX export completed successfully");
        Ok(response.content)
    }

    /// Watch file for changes
    #[tauri::command]
    pub async fn watch_file(path: String) -> Result<(), String> {
        log::info!("Setting up file watcher for: {}", path);

        if !Path::new(&path).exists() {
            return Err(format!("File not found: {}", path));
        }

        // Note: In a real implementation, you would set up a file watcher here
        // For now, we'll just log that the watch was requested
        log::info!("File watch requested for: {}", path);
        Ok(())
    }

    /// Export project to DXF format
    #[tauri::command]
    pub async fn export_to_dxf(project: Project) -> Result<String, String> {
        log::info!("Exporting project to DXF: {}", project.id);

        let infrastructure = INFRASTRUCTURE.read().await;
        let application_service = infrastructure.get_application_service();

        let request = ExportProjectRequest {
            format: application::ExportFormatDto::DXF,
        };

        let response = application_service.export_project(&project, request).await?;

        log::info!("DXF export completed successfully");
        Ok(response.content)
    }

    /// Export project to IFC format
    #[tauri::command]
    pub async fn export_to_ifc(project: Project) -> Result<String, String> {
        log::info!("Exporting project to IFC: {}", project.id);

        let infrastructure = INFRASTRUCTURE.read().await;
        let application_service = infrastructure.get_application_service();

        let request = ExportProjectRequest {
            format: application::ExportFormatDto::IFC,
        };

        let response = application_service.export_project(&project, request).await?;

        log::info!("IFC export completed successfully");
        Ok(response.content)
    }

    /// Read file from native file system
    #[tauri::command]
    pub async fn read_file(path: String) -> Result<String, String> {
        log::debug!("Reading file: {}", path);

        if !Path::new(&path).exists() {
            return Err(format!("File not found: {}", path));
        }

        match tokio::fs::read_to_string(&path).await {
            Ok(content) => {
                log::debug!("File read successfully: {} bytes", content.len());
                Ok(content)
            },
            Err(e) => {
                log::error!("Failed to read file {}: {}", path, e);
                Err(format!("Failed to read file: {}", e))
            },
        }
    }

    /// Write file to native file system
    #[tauri::command]
    pub async fn write_file(path: String, content: String) -> Result<(), String> {
        log::debug!("Writing file: {} ({} bytes)", path, content.len());

        // Ensure directory exists
        if let Some(parent) = Path::new(&path).parent() {
            tokio::fs::create_dir_all(parent).await
                .map_err(|e| format!("Failed to create directory: {}", e))?;
        }

        match tokio::fs::write(&path, content).await {
            Ok(_) => {
                log::debug!("File written successfully: {}", path);
                Ok(())
            },
            Err(e) => {
                log::error!("Failed to write file {}: {}", path, e);
                Err(format!("Failed to write file: {}", e))
            },
        }
    }

    /// Get system information
    #[tauri::command]
    pub async fn get_system_info() -> Result<HashMap<String, String>, String> {
        let mut info = HashMap::new();

        info.insert("platform".to_string(), std::env::consts::OS.to_string());
        info.insert("arch".to_string(), std::env::consts::ARCH.to_string());
        info.insert("app_version".to_string(), env!("CARGO_PKG_VERSION").to_string());
        info.insert("rust_version".to_string(), env!("RUST_VERSION").to_string());

        log::debug!("System info retrieved: {:?}", info);
        Ok(info)
    }

    // Helper functions
    async fn load_recent_projects_from_storage() -> Result<Vec<ProjectData>, ArxideError> {
        let app_dir = dirs::data_dir()
            .ok_or_else(|| ArxideError::SystemError("Could not determine data directory".to_string()))?
            .join("arxide");

        let projects_file = app_dir.join("recent_projects.json");

        if !projects_file.exists() {
            return Ok(Vec::new());
        }

        let content = tokio::fs::read_to_string(projects_file).await?;
        let projects: Vec<ProjectData> = serde_json::from_str(&content)?;
        Ok(projects)
    }

    async fn save_recent_projects_to_storage(projects: &[ProjectData]) -> Result<(), ArxideError> {
        let app_dir = dirs::data_dir()
            .ok_or_else(|| ArxideError::SystemError("Could not determine data directory".to_string()))?
            .join("arxide");

        tokio::fs::create_dir_all(&app_dir).await?;

        let projects_file = app_dir.join("recent_projects.json");
        let content = serde_json::to_string_pretty(projects)?;

        tokio::fs::write(projects_file, content).await?;
        Ok(())
    }

    fn generate_svgx_content(project: &ProjectData) -> Result<String, ArxideError> {
        // Generate SVGX format content
        let svgx_data = serde_json::json!({
            "version": "1.0",
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "objects": project.objects,
                "constraints": project.constraints
            }
        });

        Ok(serde_json::to_string_pretty(&svgx_data)?)
    }

    fn generate_dxf_content(project: &ProjectData) -> Result<String, ArxideError> {
        // Generate DXF format content (simplified)
        let mut dxf_content = String::new();
        dxf_content.push_str("0\nSECTION\n");
        dxf_content.push_str("2\nHEADER\n");
        dxf_content.push_str("9\n$ACADVER\n");
        dxf_content.push_str("1\nAC1021\n");
        dxf_content.push_str("0\nENDSEC\n");
        dxf_content.push_str("0\nSECTION\n");
        dxf_content.push_str("2\nENTITIES\n");

        // Add project objects as DXF entities
        for object in &project.objects {
            if let Some(obj_type) = object.get("type").and_then(|v| v.as_str()) {
                match obj_type {
                    "line" => {
                        dxf_content.push_str("0\nLINE\n");
                        dxf_content.push_str("8\n0\n");
                        dxf_content.push_str("10\n0.0\n");
                        dxf_content.push_str("20\n0.0\n");
                        dxf_content.push_str("11\n100.0\n");
                        dxf_content.push_str("21\n100.0\n");
                    },
                    "circle" => {
                        dxf_content.push_str("0\nCIRCLE\n");
                        dxf_content.push_str("8\n0\n");
                        dxf_content.push_str("10\n0.0\n");
                        dxf_content.push_str("20\n0.0\n");
                        dxf_content.push_str("40\n50.0\n");
                    },
                    _ => {}
                }
            }
        }

        dxf_content.push_str("0\nENDSEC\n");
        dxf_content.push_str("0\nEOF\n");

        Ok(dxf_content)
    }

    fn generate_ifc_content(project: &ProjectData) -> Result<String, ArxideError> {
        // Generate IFC format content (simplified)
        let mut ifc_content = String::new();
        ifc_content.push_str("ISO-10303-21;\n");
        ifc_content.push_str("HEADER;\n");
        ifc_content.push_str("FILE_DESCRIPTION(('ArxIDE Project'),'2;1');\n");
        ifc_content.push_str("FILE_NAME('");
        ifc_content.push_str(&project.name);
        ifc_content.push_str(".ifc','");
        ifc_content.push_str(&chrono::Utc::now().format("%Y-%m-%dT%H:%M:%S").to_string());
        ifc_content.push_str("',('ArxIDE'),('Arxos Team'),'','','');\n");
        ifc_content.push_str("FILE_SCHEMA(('IFC4'));\n");
        ifc_content.push_str("ENDSEC;\n");
        ifc_content.push_str("DATA;\n");

        // Add project objects as IFC entities
        for (i, object) in project.objects.iter().enumerate() {
            if let Some(obj_type) = object.get("type").and_then(|v| v.as_str()) {
                match obj_type {
                    "wall" => {
                        ifc_content.push_str(&format!("#{} = IFCPROXY('',$,IFCWALL,.,$);\n", i + 1));
                    },
                    "door" => {
                        ifc_content.push_str(&format!("#{} = IFCPROXY('',$,IFCDOOR,.,$);\n", i + 1));
                    },
                    "window" => {
                        ifc_content.push_str(&format!("#{} = IFCPROXY('',$,IFCWINDOW,.,$);\n", i + 1));
                    },
                    _ => {}
                }
            }
        }

        ifc_content.push_str("ENDSEC;\n");
        ifc_content.push_str("END-ISO-10303-21;\n");

        Ok(ifc_content)
    }
}

fn main() {
    // Initialize logging
    env_logger::init();

    log::info!("Starting ArxIDE application...");

    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            commands::read_file,
            commands::write_file,
            commands::get_system_info,
            commands::initialize_arxide,
            commands::get_recent_projects,
            commands::greet,
            commands::create_project,
            commands::open_project,
            commands::save_project,
            commands::export_to_svgx,
            commands::watch_file,
            commands::export_to_dxf,
            commands::export_to_ifc
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

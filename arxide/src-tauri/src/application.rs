// Application Layer for ArxIDE
// This module contains use cases and application services
// following Clean Architecture principles

use crate::domain::{
    Project, CadObject, Constraint, Position, Dimensions, ExportFormat, ConstraintSeverity,
    ProjectService, ProjectRepository, ExportService, EventPublisher, DomainEvent,
    ProjectCreatedEvent, ProjectOpenedEvent, ProjectSavedEvent, ProjectExportedEvent,
};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc};

// DTOs (Data Transfer Objects)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateProjectRequest {
    pub name: String,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateProjectResponse {
    pub project_id: String,
    pub name: String,
    pub description: String,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectInfo {
    pub id: String,
    pub name: String,
    pub description: String,
    pub object_count: usize,
    pub constraint_count: usize,
    pub created_at: DateTime<Utc>,
    pub modified_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AddObjectRequest {
    pub object_type: String,
    pub position: PositionDto,
    pub dimensions: Option<DimensionsDto>,
    pub properties: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PositionDto {
    pub x: f64,
    pub y: f64,
    pub z: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DimensionsDto {
    pub width: f64,
    pub height: f64,
    pub depth: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AddObjectResponse {
    pub object_id: String,
    pub object_type: String,
    pub position: PositionDto,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AddConstraintRequest {
    pub constraint_type: String,
    pub target_objects: Vec<String>,
    pub parameters: HashMap<String, serde_json::Value>,
    pub severity: ConstraintSeverityDto,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ConstraintSeverityDto {
    Info,
    Warning,
    Error,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AddConstraintResponse {
    pub constraint_id: String,
    pub constraint_type: String,
    pub severity: ConstraintSeverityDto,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportProjectRequest {
    pub format: ExportFormatDto,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ExportFormatDto {
    SVGX,
    DXF,
    IFC,
    PDF,
    PNG,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportProjectResponse {
    pub content: String,
    pub format: ExportFormatDto,
    pub exported_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConstraintViolationDto {
    pub constraint_id: String,
    pub message: String,
    pub severity: ConstraintSeverityDto,
}

// Use Cases
pub struct CreateProjectUseCase {
    project_service: ProjectService,
}

impl CreateProjectUseCase {
    pub fn new(project_service: ProjectService) -> Self {
        Self { project_service }
    }

    pub async fn execute(&self, request: CreateProjectRequest) -> Result<CreateProjectResponse, String> {
        // Validate request
        if request.name.trim().is_empty() {
            return Err("Project name cannot be empty".to_string());
        }

        if request.description.len() > 1000 {
            return Err("Project description too long (max 1000 characters)".to_string());
        }

        // Create project using domain service
        let project = self.project_service.create_project(request.name, request.description).await?;

        // Return response
        Ok(CreateProjectResponse {
            project_id: project.id,
            name: project.name,
            description: project.description,
            created_at: project.created_at,
        })
    }
}

pub struct LoadProjectUseCase {
    project_service: ProjectService,
}

impl LoadProjectUseCase {
    pub fn new(project_service: ProjectService) -> Self {
        Self { project_service }
    }

    pub async fn execute(&self, project_id: &str) -> Result<Project, String> {
        if project_id.trim().is_empty() {
            return Err("Project ID cannot be empty".to_string());
        }

        self.project_service.load_project(project_id).await
    }
}

pub struct SaveProjectUseCase {
    project_service: ProjectService,
}

impl SaveProjectUseCase {
    pub fn new(project_service: ProjectService) -> Self {
        Self { project_service }
    }

    pub async fn execute(&self, mut project: Project) -> Result<(), String> {
        if project.name.trim().is_empty() {
            return Err("Project name cannot be empty".to_string());
        }

        self.project_service.save_project(&mut project).await
    }
}

pub struct AddObjectUseCase {
    project_service: ProjectService,
}

impl AddObjectUseCase {
    pub fn new(project_service: ProjectService) -> Self {
        Self { project_service }
    }

    pub async fn execute(&self, project: &mut Project, request: AddObjectRequest) -> Result<AddObjectResponse, String> {
        // Validate request
        if request.object_type.trim().is_empty() {
            return Err("Object type cannot be empty".to_string());
        }

        // Convert DTOs to domain objects
        let position = Position::new_2d(request.position.x, request.position.y);
        let dimensions = request.dimensions.map(|d| Dimensions::new_2d(d.width, d.height));

        // Create CAD object
        let object = CadObject::new(
            request.object_type,
            position,
            dimensions,
        );

        // Add properties
        let mut object_with_properties = object;
        for (key, value) in request.properties {
            object_with_properties.set_property(key, value);
        }

        // Add object to project
        project.add_object(object_with_properties.clone())?;

        // Return response
        Ok(AddObjectResponse {
            object_id: object_with_properties.id,
            object_type: object_with_properties.object_type,
            position: PositionDto {
                x: object_with_properties.position.x,
                y: object_with_properties.position.y,
                z: object_with_properties.position.z,
            },
        })
    }
}

pub struct UpdateObjectUseCase {
    project_service: ProjectService,
}

impl UpdateObjectUseCase {
    pub fn new(project_service: ProjectService) -> Self {
        Self { project_service }
    }

    pub async fn execute(&self, project: &mut Project, object_id: &str, updates: HashMap<String, serde_json::Value>) -> Result<(), String> {
        if object_id.trim().is_empty() {
            return Err("Object ID cannot be empty".to_string());
        }

        project.update_object(object_id, updates)
    }
}

pub struct RemoveObjectUseCase {
    project_service: ProjectService,
}

impl RemoveObjectUseCase {
    pub fn new(project_service: ProjectService) -> Self {
        Self { project_service }
    }

    pub async fn execute(&self, project: &mut Project, object_id: &str) -> Result<(), String> {
        if object_id.trim().is_empty() {
            return Err("Object ID cannot be empty".to_string());
        }

        project.remove_object(object_id)
    }
}

pub struct AddConstraintUseCase {
    project_service: ProjectService,
}

impl AddConstraintUseCase {
    pub fn new(project_service: ProjectService) -> Self {
        Self { project_service }
    }

    pub async fn execute(&self, project: &mut Project, request: AddConstraintRequest) -> Result<AddConstraintResponse, String> {
        // Validate request
        if request.constraint_type.trim().is_empty() {
            return Err("Constraint type cannot be empty".to_string());
        }

        if request.target_objects.is_empty() {
            return Err("Constraint must target at least one object".to_string());
        }

        // Convert DTO to domain object
        let severity = match request.severity {
            ConstraintSeverityDto::Info => ConstraintSeverity::Info,
            ConstraintSeverityDto::Warning => ConstraintSeverity::Warning,
            ConstraintSeverityDto::Error => ConstraintSeverity::Error,
            ConstraintSeverityDto::Critical => ConstraintSeverity::Critical,
        };

        let constraint = Constraint::new(
            request.constraint_type,
            request.target_objects,
            request.parameters,
            severity,
        );

        // Add constraint to project
        project.add_constraint(constraint.clone())?;

        // Return response
        Ok(AddConstraintResponse {
            constraint_id: constraint.id,
            constraint_type: constraint.constraint_type,
            severity: match constraint.severity {
                ConstraintSeverity::Info => ConstraintSeverityDto::Info,
                ConstraintSeverity::Warning => ConstraintSeverityDto::Warning,
                ConstraintSeverity::Error => ConstraintSeverityDto::Error,
                ConstraintSeverity::Critical => ConstraintSeverityDto::Critical,
            },
        })
    }
}

pub struct ExportProjectUseCase {
    project_service: ProjectService,
}

impl ExportProjectUseCase {
    pub fn new(project_service: ProjectService) -> Self {
        Self { project_service }
    }

    pub async fn execute(&self, project: &Project, request: ExportProjectRequest) -> Result<ExportProjectResponse, String> {
        // Convert DTO to domain enum
        let format = match request.format {
            ExportFormatDto::SVGX => ExportFormat::SVGX,
            ExportFormatDto::DXF => ExportFormat::DXF,
            ExportFormatDto::IFC => ExportFormat::IFC,
            ExportFormatDto::PDF => ExportFormat::PDF,
            ExportFormatDto::PNG => ExportFormat::PNG,
        };

        // Export project
        let content = self.project_service.export_project(project, format).await?;

        // Return response
        Ok(ExportProjectResponse {
            content,
            format: request.format,
            exported_at: Utc::now(),
        })
    }
}

pub struct ValidateProjectUseCase {
    project_service: ProjectService,
}

impl ValidateProjectUseCase {
    pub fn new(project_service: ProjectService) -> Self {
        Self { project_service }
    }

    pub async fn execute(&self, project: &Project) -> Vec<ConstraintViolationDto> {
        let violations = self.project_service.validate_project(project).await;

        violations.into_iter().map(|v| ConstraintViolationDto {
            constraint_id: v.constraint_id,
            message: v.message,
            severity: match v.severity {
                ConstraintSeverity::Info => ConstraintSeverityDto::Info,
                ConstraintSeverity::Warning => ConstraintSeverityDto::Warning,
                ConstraintSeverity::Error => ConstraintSeverityDto::Error,
                ConstraintSeverity::Critical => ConstraintSeverityDto::Critical,
            },
        }).collect()
    }
}

pub struct ListRecentProjectsUseCase {
    repository: Box<dyn ProjectRepository>,
}

impl ListRecentProjectsUseCase {
    pub fn new(repository: Box<dyn ProjectRepository>) -> Self {
        Self { repository }
    }

    pub async fn execute(&self, limit: usize) -> Result<Vec<ProjectInfo>, String> {
        let projects = self.repository.list_recent(limit).await?;

        let project_infos = projects.into_iter().map(|p| ProjectInfo {
            id: p.id,
            name: p.name,
            description: p.description,
            object_count: p.objects.len(),
            constraint_count: p.constraints.len(),
            created_at: p.created_at,
            modified_at: p.modified_at,
        }).collect();

        Ok(project_infos)
    }
}

// Application Services
pub struct ProjectApplicationService {
    create_project_use_case: CreateProjectUseCase,
    load_project_use_case: LoadProjectUseCase,
    save_project_use_case: SaveProjectUseCase,
    add_object_use_case: AddObjectUseCase,
    update_object_use_case: UpdateObjectUseCase,
    remove_object_use_case: RemoveObjectUseCase,
    add_constraint_use_case: AddConstraintUseCase,
    export_project_use_case: ExportProjectUseCase,
    validate_project_use_case: ValidateProjectUseCase,
    list_recent_projects_use_case: ListRecentProjectsUseCase,
}

impl ProjectApplicationService {
    pub fn new(
        project_service: ProjectService,
        repository: Box<dyn ProjectRepository>,
    ) -> Self {
        Self {
            create_project_use_case: CreateProjectUseCase::new(project_service.clone()),
            load_project_use_case: LoadProjectUseCase::new(project_service.clone()),
            save_project_use_case: SaveProjectUseCase::new(project_service.clone()),
            add_object_use_case: AddObjectUseCase::new(project_service.clone()),
            update_object_use_case: UpdateObjectUseCase::new(project_service.clone()),
            remove_object_use_case: RemoveObjectUseCase::new(project_service.clone()),
            add_constraint_use_case: AddConstraintUseCase::new(project_service.clone()),
            export_project_use_case: ExportProjectUseCase::new(project_service.clone()),
            validate_project_use_case: ValidateProjectUseCase::new(project_service),
            list_recent_projects_use_case: ListRecentProjectsUseCase::new(repository),
        }
    }

    pub async fn create_project(&self, request: CreateProjectRequest) -> Result<CreateProjectResponse, String> {
        self.create_project_use_case.execute(request).await
    }

    pub async fn load_project(&self, project_id: &str) -> Result<Project, String> {
        self.load_project_use_case.execute(project_id).await
    }

    pub async fn save_project(&self, project: Project) -> Result<(), String> {
        self.save_project_use_case.execute(project).await
    }

    pub async fn add_object(&self, project: &mut Project, request: AddObjectRequest) -> Result<AddObjectResponse, String> {
        self.add_object_use_case.execute(project, request).await
    }

    pub async fn update_object(&self, project: &mut Project, object_id: &str, updates: HashMap<String, serde_json::Value>) -> Result<(), String> {
        self.update_object_use_case.execute(project, object_id, updates).await
    }

    pub async fn remove_object(&self, project: &mut Project, object_id: &str) -> Result<(), String> {
        self.remove_object_use_case.execute(project, object_id).await
    }

    pub async fn add_constraint(&self, project: &mut Project, request: AddConstraintRequest) -> Result<AddConstraintResponse, String> {
        self.add_constraint_use_case.execute(project, request).await
    }

    pub async fn export_project(&self, project: &Project, request: ExportProjectRequest) -> Result<ExportProjectResponse, String> {
        self.export_project_use_case.execute(project, request).await
    }

    pub async fn validate_project(&self, project: &Project) -> Vec<ConstraintViolationDto> {
        self.validate_project_use_case.execute(project).await
    }

    pub async fn list_recent_projects(&self, limit: usize) -> Result<Vec<ProjectInfo>, String> {
        self.list_recent_projects_use_case.execute(limit).await
    }
}

// Error handling for application layer
#[derive(Debug, thiserror::Error)]
pub enum ApplicationError {
    #[error("Validation error: {0}")]
    ValidationError(String),
    #[error("Domain error: {0}")]
    DomainError(String),
    #[error("Infrastructure error: {0}")]
    InfrastructureError(String),
    #[error("Business rule violation: {0}")]
    BusinessRuleViolation(String),
}

impl From<ApplicationError> for String {
    fn from(err: ApplicationError) -> String {
        err.to_string()
    }
}

// Application configuration
#[derive(Debug, Clone)]
pub struct ApplicationConfig {
    pub max_project_name_length: usize,
    pub max_project_description_length: usize,
    pub max_recent_projects: usize,
    pub default_export_format: ExportFormat,
    pub enable_constraint_validation: bool,
    pub enable_event_publishing: bool,
}

impl Default for ApplicationConfig {
    fn default() -> Self {
        Self {
            max_project_name_length: 100,
            max_project_description_length: 1000,
            max_recent_projects: 10,
            default_export_format: ExportFormat::SVGX,
            enable_constraint_validation: true,
            enable_event_publishing: true,
        }
    }
}

// Domain Layer for ArxIDE
// This module contains the core business logic and domain entities
// following Clean Architecture principles

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc};
use uuid::Uuid;

// Domain Events
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DomainEvent {
    ProjectCreated(ProjectCreatedEvent),
    ProjectOpened(ProjectOpenedEvent),
    ProjectSaved(ProjectSavedEvent),
    ProjectExported(ProjectExportedEvent),
    ObjectAdded(ObjectAddedEvent),
    ObjectModified(ObjectModifiedEvent),
    ObjectDeleted(ObjectDeletedEvent),
    ConstraintAdded(ConstraintAddedEvent),
    ConstraintViolated(ConstraintViolatedEvent),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectCreatedEvent {
    pub project_id: String,
    pub name: String,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectOpenedEvent {
    pub project_id: String,
    pub path: String,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectSavedEvent {
    pub project_id: String,
    pub path: String,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectExportedEvent {
    pub project_id: String,
    pub format: ExportFormat,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObjectAddedEvent {
    pub project_id: String,
    pub object_id: String,
    pub object_type: String,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObjectModifiedEvent {
    pub project_id: String,
    pub object_id: String,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObjectDeletedEvent {
    pub project_id: String,
    pub object_id: String,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConstraintAddedEvent {
    pub project_id: String,
    pub constraint_id: String,
    pub constraint_type: String,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConstraintViolatedEvent {
    pub project_id: String,
    pub constraint_id: String,
    pub severity: ConstraintSeverity,
    pub message: String,
    pub timestamp: DateTime<Utc>,
}

// Value Objects
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ExportFormat {
    SVGX,
    DXF,
    IFC,
    PDF,
    PNG,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ConstraintSeverity {
    Info,
    Warning,
    Error,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Dimensions {
    pub width: f64,
    pub height: f64,
    pub depth: Option<f64>,
}

impl Dimensions {
    pub fn new_2d(width: f64, height: f64) -> Self {
        Self {
            width,
            height,
            depth: None,
        }
    }

    pub fn new_3d(width: f64, height: f64, depth: f64) -> Self {
        Self {
            width,
            height,
            depth: Some(depth),
        }
    }

    pub fn area(&self) -> f64 {
        self.width * self.height
    }

    pub fn volume(&self) -> Option<f64> {
        self.depth.map(|d| self.width * self.height * d)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Position {
    pub x: f64,
    pub y: f64,
    pub z: Option<f64>,
}

impl Position {
    pub fn new_2d(x: f64, y: f64) -> Self {
        Self { x, y, z: None }
    }

    pub fn new_3d(x: f64, y: f64, z: f64) -> Self {
        Self { x, y, z: Some(z) }
    }

    pub fn distance_to(&self, other: &Position) -> f64 {
        let dx = self.x - other.x;
        let dy = self.y - other.y;
        let dz = match (self.z, other.z) {
            (Some(z1), Some(z2)) => z1 - z2,
            _ => 0.0,
        };
        (dx * dx + dy * dy + dz * dz).sqrt()
    }
}

// Domain Entities
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CadObject {
    pub id: String,
    pub object_type: String,
    pub position: Position,
    pub dimensions: Option<Dimensions>,
    pub properties: HashMap<String, serde_json::Value>,
    pub created_at: DateTime<Utc>,
    pub modified_at: DateTime<Utc>,
}

impl CadObject {
    pub fn new(
        object_type: String,
        position: Position,
        dimensions: Option<Dimensions>,
    ) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4().to_string(),
            object_type,
            position,
            dimensions,
            properties: HashMap::new(),
            created_at: now,
            modified_at: now,
        }
    }

    pub fn update_position(&mut self, new_position: Position) {
        self.position = new_position;
        self.modified_at = Utc::now();
    }

    pub fn update_dimensions(&mut self, new_dimensions: Dimensions) {
        self.dimensions = Some(new_dimensions);
        self.modified_at = Utc::now();
    }

    pub fn set_property(&mut self, key: String, value: serde_json::Value) {
        self.properties.insert(key, value);
        self.modified_at = Utc::now();
    }

    pub fn get_property(&self, key: &str) -> Option<&serde_json::Value> {
        self.properties.get(key)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Constraint {
    pub id: String,
    pub constraint_type: String,
    pub target_objects: Vec<String>,
    pub parameters: HashMap<String, serde_json::Value>,
    pub severity: ConstraintSeverity,
    pub is_active: bool,
    pub created_at: DateTime<Utc>,
    pub modified_at: DateTime<Utc>,
}

impl Constraint {
    pub fn new(
        constraint_type: String,
        target_objects: Vec<String>,
        parameters: HashMap<String, serde_json::Value>,
        severity: ConstraintSeverity,
    ) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4().to_string(),
            constraint_type,
            target_objects,
            parameters,
            severity,
            is_active: true,
            created_at: now,
            modified_at: now,
        }
    }

    pub fn deactivate(&mut self) {
        self.is_active = false;
        self.modified_at = Utc::now();
    }

    pub fn activate(&mut self) {
        self.is_active = true;
        self.modified_at = Utc::now();
    }

    pub fn update_parameters(&mut self, parameters: HashMap<String, serde_json::Value>) {
        self.parameters = parameters;
        self.modified_at = Utc::now();
    }
}

// Aggregate Root
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Project {
    pub id: String,
    pub name: String,
    pub description: String,
    pub objects: HashMap<String, CadObject>,
    pub constraints: HashMap<String, Constraint>,
    pub settings: HashMap<String, serde_json::Value>,
    pub created_at: DateTime<Utc>,
    pub modified_at: DateTime<Utc>,
    pub events: Vec<DomainEvent>,
}

impl Project {
    pub fn new(name: String, description: String) -> Self {
        let now = Utc::now();
        let project_id = Uuid::new_v4().to_string();

        let mut project = Self {
            id: project_id.clone(),
            name,
            description,
            objects: HashMap::new(),
            constraints: HashMap::new(),
            settings: HashMap::new(),
            created_at: now,
            modified_at: now,
            events: Vec::new(),
        };

        // Add domain event
        project.add_event(DomainEvent::ProjectCreated(ProjectCreatedEvent {
            project_id: project_id.clone(),
            name: project.name.clone(),
            timestamp: now,
        }));

        project
    }

    pub fn add_object(&mut self, object: CadObject) -> Result<(), String> {
        // Validate object
        if object.object_type.trim().is_empty() {
            return Err("Object type cannot be empty".to_string());
        }

        let object_id = object.id.clone();
        self.objects.insert(object_id.clone(), object);
        self.modified_at = Utc::now();

        // Add domain event
        self.add_event(DomainEvent::ObjectAdded(ObjectAddedEvent {
            project_id: self.id.clone(),
            object_id,
            object_type: self.objects[&object_id].object_type.clone(),
            timestamp: Utc::now(),
        }));

        Ok(())
    }

    pub fn update_object(&mut self, object_id: &str, updates: HashMap<String, serde_json::Value>) -> Result<(), String> {
        if let Some(object) = self.objects.get_mut(object_id) {
            for (key, value) in updates {
                object.set_property(key, value);
            }
            self.modified_at = Utc::now();

            // Add domain event
            self.add_event(DomainEvent::ObjectModified(ObjectModifiedEvent {
                project_id: self.id.clone(),
                object_id: object_id.to_string(),
                timestamp: Utc::now(),
            }));

            Ok(())
        } else {
            Err(format!("Object with id {} not found", object_id))
        }
    }

    pub fn remove_object(&mut self, object_id: &str) -> Result<(), String> {
        if self.objects.remove(object_id).is_some() {
            self.modified_at = Utc::now();

            // Add domain event
            self.add_event(DomainEvent::ObjectDeleted(ObjectDeletedEvent {
                project_id: self.id.clone(),
                object_id: object_id.to_string(),
                timestamp: Utc::now(),
            }));

            Ok(())
        } else {
            Err(format!("Object with id {} not found", object_id))
        }
    }

    pub fn add_constraint(&mut self, constraint: Constraint) -> Result<(), String> {
        // Validate constraint
        if constraint.constraint_type.trim().is_empty() {
            return Err("Constraint type cannot be empty".to_string());
        }

        if constraint.target_objects.is_empty() {
            return Err("Constraint must target at least one object".to_string());
        }

        // Validate that target objects exist
        for object_id in &constraint.target_objects {
            if !self.objects.contains_key(object_id) {
                return Err(format!("Target object {} not found", object_id));
            }
        }

        let constraint_id = constraint.id.clone();
        self.constraints.insert(constraint_id.clone(), constraint);
        self.modified_at = Utc::now();

        // Add domain event
        self.add_event(DomainEvent::ConstraintAdded(ConstraintAddedEvent {
            project_id: self.id.clone(),
            constraint_id,
            constraint_type: self.constraints[&constraint_id].constraint_type.clone(),
            timestamp: Utc::now(),
        }));

        Ok(())
    }

    pub fn validate_constraints(&self) -> Vec<ConstraintViolation> {
        let mut violations = Vec::new();

        for (constraint_id, constraint) in &self.constraints {
            if !constraint.is_active {
                continue;
            }

            // Simple validation logic - in a real implementation, this would be more sophisticated
            match constraint.constraint_type.as_str() {
                "distance" => {
                    if let Some(min_distance) = constraint.parameters.get("min_distance") {
                        if let Some(max_distance) = constraint.parameters.get("max_distance") {
                            // Validate distance constraints
                            if let (Some(min), Some(max)) = (min_distance.as_f64(), max_distance.as_f64()) {
                                // Implementation would check actual distances between objects
                                if min > max {
                                    violations.push(ConstraintViolation {
                                        constraint_id: constraint_id.clone(),
                                        message: "Invalid distance range".to_string(),
                                        severity: constraint.severity.clone(),
                                    });
                                }
                            }
                        }
                    }
                }
                "dimension" => {
                    // Validate dimension constraints
                    for object_id in &constraint.target_objects {
                        if let Some(object) = self.objects.get(object_id) {
                            if let Some(dimensions) = &object.dimensions {
                                if let Some(max_width) = constraint.parameters.get("max_width") {
                                    if let Some(max) = max_width.as_f64() {
                                        if dimensions.width > max {
                                            violations.push(ConstraintViolation {
                                                constraint_id: constraint_id.clone(),
                                                message: format!("Object {} exceeds maximum width", object_id),
                                                severity: constraint.severity.clone(),
                                            });
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                _ => {
                    // Unknown constraint type
                    violations.push(ConstraintViolation {
                        constraint_id: constraint_id.clone(),
                        message: format!("Unknown constraint type: {}", constraint.constraint_type),
                        severity: ConstraintSeverity::Warning,
                    });
                }
            }
        }

        violations
    }

    pub fn export(&self, format: ExportFormat) -> Result<String, String> {
        match format {
            ExportFormat::SVGX => self.export_to_svgx(),
            ExportFormat::DXF => self.export_to_dxf(),
            ExportFormat::IFC => self.export_to_ifc(),
            ExportFormat::PDF => Err("PDF export not implemented".to_string()),
            ExportFormat::PNG => Err("PNG export not implemented".to_string()),
        }
    }

    fn export_to_svgx(&self) -> Result<String, String> {
        let svgx_data = serde_json::json!({
            "version": "1.0",
            "project": {
                "id": self.id,
                "name": self.name,
                "description": self.description,
                "objects": self.objects.values().collect::<Vec<_>>(),
                "constraints": self.constraints.values().collect::<Vec<_>>()
            }
        });

        serde_json::to_string_pretty(&svgx_data)
            .map_err(|e| format!("Failed to serialize SVGX: {}", e))
    }

    fn export_to_dxf(&self) -> Result<String, String> {
        let mut dxf_content = String::new();
        dxf_content.push_str("0\nSECTION\n");
        dxf_content.push_str("2\nHEADER\n");
        dxf_content.push_str("9\n$ACADVER\n");
        dxf_content.push_str("1\nAC1021\n");
        dxf_content.push_str("0\nENDSEC\n");
        dxf_content.push_str("0\nSECTION\n");
        dxf_content.push_str("2\nENTITIES\n");

        // Add objects as DXF entities
        for object in self.objects.values() {
            match object.object_type.as_str() {
                "line" => {
                    dxf_content.push_str("0\nLINE\n");
                    dxf_content.push_str("8\n0\n");
                    dxf_content.push_str(&format!("10\n{}\n", object.position.x));
                    dxf_content.push_str(&format!("20\n{}\n", object.position.y));
                    if let Some(dimensions) = &object.dimensions {
                        dxf_content.push_str(&format!("11\n{}\n", object.position.x + dimensions.width));
                        dxf_content.push_str(&format!("21\n{}\n", object.position.y + dimensions.height));
                    }
                }
                "circle" => {
                    dxf_content.push_str("0\nCIRCLE\n");
                    dxf_content.push_str("8\n0\n");
                    dxf_content.push_str(&format!("10\n{}\n", object.position.x));
                    dxf_content.push_str(&format!("20\n{}\n", object.position.y));
                    if let Some(dimensions) = &object.dimensions {
                        dxf_content.push_str(&format!("40\n{}\n", dimensions.width / 2.0));
                    }
                }
                _ => {}
            }
        }

        dxf_content.push_str("0\nENDSEC\n");
        dxf_content.push_str("0\nEOF\n");

        Ok(dxf_content)
    }

    fn export_to_ifc(&self) -> Result<String, String> {
        let mut ifc_content = String::new();
        ifc_content.push_str("ISO-10303-21;\n");
        ifc_content.push_str("HEADER;\n");
        ifc_content.push_str("FILE_DESCRIPTION(('ArxIDE Project'),'2;1');\n");
        ifc_content.push_str(&format!("FILE_NAME('{}.ifc','", self.name));
        ifc_content.push_str(&Utc::now().format("%Y-%m-%dT%H:%M:%S").to_string());
        ifc_content.push_str("',('ArxIDE'),('Arxos Team'),'','','');\n");
        ifc_content.push_str("FILE_SCHEMA(('IFC4'));\n");
        ifc_content.push_str("ENDSEC;\n");
        ifc_content.push_str("DATA;\n");

        // Add objects as IFC entities
        for (i, object) in self.objects.values().enumerate() {
            match object.object_type.as_str() {
                "wall" => {
                    ifc_content.push_str(&format!("#{} = IFCPROXY('',$,IFCWALL,.,$);\n", i + 1));
                }
                "door" => {
                    ifc_content.push_str(&format!("#{} = IFCPROXY('',$,IFCDOOR,.,$);\n", i + 1));
                }
                "window" => {
                    ifc_content.push_str(&format!("#{} = IFCPROXY('',$,IFCWINDOW,.,$);\n", i + 1));
                }
                _ => {}
            }
        }

        ifc_content.push_str("ENDSEC;\n");
        ifc_content.push_str("END-ISO-10303-21;\n");

        Ok(ifc_content)
    }

    fn add_event(&mut self, event: DomainEvent) {
        self.events.push(event);
    }

    pub fn clear_events(&mut self) {
        self.events.clear();
    }

    pub fn get_events(&self) -> &[DomainEvent] {
        &self.events
    }
}

// Domain Services
#[derive(Debug, Clone)]
pub struct ConstraintViolation {
    pub constraint_id: String,
    pub message: String,
    pub severity: ConstraintSeverity,
}

pub trait ProjectRepository {
    async fn save(&self, project: &Project) -> Result<(), String>;
    async fn load(&self, project_id: &str) -> Result<Project, String>;
    async fn list_recent(&self, limit: usize) -> Result<Vec<Project>, String>;
    async fn delete(&self, project_id: &str) -> Result<(), String>;
}

pub trait ExportService {
    async fn export_project(&self, project: &Project, format: ExportFormat) -> Result<String, String>;
}

pub trait EventPublisher {
    async fn publish(&self, event: &DomainEvent) -> Result<(), String>;
}

// Domain Services Implementation
pub struct ProjectService {
    repository: Box<dyn ProjectRepository>,
    export_service: Box<dyn ExportService>,
    event_publisher: Box<dyn EventPublisher>,
}

impl ProjectService {
    pub fn new(
        repository: Box<dyn ProjectRepository>,
        export_service: Box<dyn ExportService>,
        event_publisher: Box<dyn EventPublisher>,
    ) -> Self {
        Self {
            repository,
            export_service,
            event_publisher,
        }
    }

    pub async fn create_project(&self, name: String, description: String) -> Result<Project, String> {
        // Validate input
        if name.trim().is_empty() {
            return Err("Project name cannot be empty".to_string());
        }

        if description.len() > 1000 {
            return Err("Project description too long".to_string());
        }

        let mut project = Project::new(name, description);

        // Save project
        self.repository.save(&project).await?;

        // Publish events
        for event in project.get_events() {
            self.event_publisher.publish(event).await?;
        }

        Ok(project)
    }

    pub async fn load_project(&self, project_id: &str) -> Result<Project, String> {
        let project = self.repository.load(project_id).await?;

        // Publish project opened event
        let event = DomainEvent::ProjectOpened(ProjectOpenedEvent {
            project_id: project_id.to_string(),
            path: format!("projects/{}", project_id),
            timestamp: Utc::now(),
        });
        self.event_publisher.publish(&event).await?;

        Ok(project)
    }

    pub async fn save_project(&self, project: &mut Project) -> Result<(), String> {
        // Validate project
        if project.name.trim().is_empty() {
            return Err("Project name cannot be empty".to_string());
        }

        project.modified_at = Utc::now();

        // Save project
        self.repository.save(project).await?;

        // Publish events
        for event in project.get_events() {
            self.event_publisher.publish(event).await?;
        }

        // Clear events after publishing
        project.clear_events();

        Ok(())
    }

    pub async fn export_project(&self, project: &Project, format: ExportFormat) -> Result<String, String> {
        let export_content = self.export_service.export_project(project, format).await?;

        // Publish export event
        let event = DomainEvent::ProjectExported(ProjectExportedEvent {
            project_id: project.id.clone(),
            format,
            timestamp: Utc::now(),
        });
        self.event_publisher.publish(&event).await?;

        Ok(export_content)
    }

    pub async fn validate_project(&self, project: &Project) -> Vec<ConstraintViolation> {
        project.validate_constraints()
    }
}

//! Constraint validation system for game

use std::collections::HashMap;
use std::path::Path;
use crate::game::types::{Constraint, ConstraintType, ConstraintSeverity, ValidationResult, ConstraintViolation, GameEquipmentPlacement};
use crate::game::state::GameState;
use crate::spatial::{Point3D, BoundingBox3D};
use log::{info, warn};

/// Constraint validation system
pub struct ConstraintSystem {
    constraints: Vec<Constraint>,
    constraint_data: ConstraintData,
}

/// Constraint data loaded from YAML
#[derive(Debug, Clone)]
pub struct ConstraintData {
    pub structural: Vec<StructuralConstraint>,
    pub spatial: Vec<SpatialConstraint>,
    pub code: Vec<CodeConstraint>,
    pub budget: Vec<BudgetConstraint>,
    pub accessibility: Vec<AccessibilityConstraint>,
}

/// Structural constraint (wall support, load capacity)
#[derive(Debug, Clone)]
pub struct StructuralConstraint {
    pub id: String,
    pub floor: i32,
    pub valid_areas: Vec<ValidArea>,
    pub notes: Option<String>,
}

/// Valid area with bounding box and load capacity
#[derive(Debug, Clone)]
pub struct ValidArea {
    pub bbox: BoundingBox3D,
    pub load_capacity: Option<f64>, // kg
}

/// Spatial constraint (clearance, proximity)
#[derive(Debug, Clone)]
pub struct SpatialConstraint {
    pub id: String,
    pub equipment_type: Option<String>,
    pub min_clearance: f64,
    pub max_proximity: Option<f64>,
}

/// Code constraint (building code requirements)
#[derive(Debug, Clone)]
pub struct CodeConstraint {
    pub id: String,
    pub code_type: String,
    pub equipment_type: Option<String>,
    pub requirement: String,
    pub is_mandatory: bool,
}

/// Budget constraint
#[derive(Debug, Clone)]
pub struct BudgetConstraint {
    pub id: String,
    pub max_cost: Option<f64>,
    pub cost_per_item: HashMap<String, f64>,
}

/// Accessibility constraint (ADA requirements)
#[derive(Debug, Clone)]
pub struct AccessibilityConstraint {
    pub id: String,
    pub requirement: String,
    pub is_required: bool,
}

impl ConstraintSystem {
    /// Create new constraint system
    pub fn new() -> Self {
        Self {
            constraints: Vec::new(),
            constraint_data: ConstraintData {
                structural: Vec::new(),
                spatial: Vec::new(),
                code: Vec::new(),
                budget: Vec::new(),
                accessibility: Vec::new(),
            },
        }
    }

    /// Load constraints from YAML file
    pub fn load_from_file(constraints_path: &Path) -> Result<Self, Box<dyn std::error::Error>> {
        info!("Loading constraints from: {:?}", constraints_path);
        
        let mut system = Self::new();
        
        if !constraints_path.exists() {
            warn!("Constraints file not found, using empty constraint system");
            return Ok(system);
        }

        let content = std::fs::read_to_string(constraints_path)?;
        let data: serde_yaml::Value = serde_yaml::from_str(&content)?;

        if let Some(constraints_obj) = data.get("constraints") {
            // Load structural constraints
            if let Some(structural_seq) = constraints_obj.get("structural").and_then(|s| s.as_sequence()) {
                for (idx, item) in structural_seq.iter().enumerate() {
                    if let Some(constraint) = Self::parse_structural_constraint(item, idx) {
                        system.constraint_data.structural.push(constraint.clone());
                        system.constraints.push(Constraint {
                            id: constraint.id.clone(),
                            constraint_type: ConstraintType::Structural,
                            description: constraint.notes.clone().unwrap_or_else(|| "Structural constraint".to_string()),
                            severity: ConstraintSeverity::Error,
                        });
                    }
                }
            }

            // Load spatial constraints
            if let Some(spatial_seq) = constraints_obj.get("spatial").and_then(|s| s.as_sequence()) {
                for (idx, item) in spatial_seq.iter().enumerate() {
                    if let Some(constraint) = Self::parse_spatial_constraint(item, idx) {
                        system.constraint_data.spatial.push(constraint.clone());
                        system.constraints.push(Constraint {
                            id: constraint.id.clone(),
                            constraint_type: ConstraintType::Spatial,
                            description: format!("Minimum clearance: {}m", constraint.min_clearance),
                            severity: ConstraintSeverity::Warning,
                        });
                    }
                }
            }

            // Load code constraints
            if let Some(code_seq) = constraints_obj.get("code").and_then(|c| c.as_sequence()) {
                for (idx, item) in code_seq.iter().enumerate() {
                    if let Some(constraint) = Self::parse_code_constraint(item, idx) {
                        system.constraint_data.code.push(constraint.clone());
                        system.constraints.push(Constraint {
                            id: constraint.id.clone(),
                            constraint_type: ConstraintType::Code,
                            description: constraint.requirement.clone(),
                            severity: if constraint.is_mandatory {
                                ConstraintSeverity::Critical
                            } else {
                                ConstraintSeverity::Warning
                            },
                        });
                    }
                }
            }
        }

        info!("Loaded {} constraints", system.constraints.len());
        Ok(system)
    }

    /// Parse structural constraint from YAML
    fn parse_structural_constraint(item: &serde_yaml::Value, idx: usize) -> Option<StructuralConstraint> {
        let constraint_type = item.get("type")?.as_str()?;
        
        if constraint_type != "wall_support" {
            return None;
        }

        let floor = item.get("floor")?.as_i64()? as i32;
        
        let mut valid_areas = Vec::new();
        if let Some(areas) = item.get("valid_areas").and_then(|a| a.as_sequence()) {
            for area in areas {
                if let Some(bbox_data) = area.get("bbox") {
                    let min_data = bbox_data.get("min")?;
                    let max_data = bbox_data.get("max")?;
                    
                    let bbox = BoundingBox3D {
                        min: Point3D::new(
                            min_data.get("x")?.as_f64()?,
                            min_data.get("y")?.as_f64()?,
                            min_data.get("z")?.as_f64().unwrap_or(0.0),
                        ),
                        max: Point3D::new(
                            max_data.get("x")?.as_f64()?,
                            max_data.get("y")?.as_f64()?,
                            max_data.get("z")?.as_f64().unwrap_or(3.0),
                        ),
                    };
                    
                    let load_capacity = area.get("load_capacity")
                        .and_then(|l| l.as_f64());
                    
                    valid_areas.push(ValidArea {
                        bbox,
                        load_capacity,
                    });
                }
            }
        }

        Some(StructuralConstraint {
            id: format!("structural_{}", idx),
            floor,
            valid_areas,
            notes: item.get("notes").and_then(|n| n.as_str()).map(|s| s.to_string()),
        })
    }

    /// Parse spatial constraint from YAML
    fn parse_spatial_constraint(item: &serde_yaml::Value, idx: usize) -> Option<SpatialConstraint> {
        let constraint_type = item.get("type")?.as_str()?;
        
        if constraint_type != "clearance" {
            return None;
        }

        Some(SpatialConstraint {
            id: format!("spatial_{}", idx),
            equipment_type: item.get("equipment_type")
                .and_then(|e| e.as_str())
                .map(|s| s.to_string()),
            min_clearance: item.get("min_clearance")
                .and_then(|c| c.as_f64())
                .unwrap_or(0.5),
            max_proximity: item.get("max_proximity")
                .and_then(|p| p.as_f64()),
        })
    }

    /// Parse code constraint from YAML
    fn parse_code_constraint(item: &serde_yaml::Value, idx: usize) -> Option<CodeConstraint> {
        let code_type = item.get("type")?.as_str()?.to_string();
        
        Some(CodeConstraint {
            id: format!("code_{}", idx),
            code_type,
            equipment_type: item.get("equipment_type")
                .and_then(|e| e.as_str())
                .map(|s| s.to_string()),
            requirement: item.get("requirement")
                .and_then(|r| r.as_str())
                .unwrap_or("Code requirement")
                .to_string(),
            is_mandatory: item.get("is_mandatory")
                .and_then(|m| m.as_bool())
                .unwrap_or(true),
        })
    }

    /// Validate equipment placement against all constraints
    pub fn validate_placement(&self, placement: &GameEquipmentPlacement, game_state: &GameState) -> ValidationResult {
        let mut result = ValidationResult::default();
        
        // Validate structural constraints
        for constraint in &self.constraint_data.structural {
            if let Some(violation) = self.validate_structural(placement, constraint) {
                result.is_valid = false;
                result.violations.push(violation);
            }
        }

        // Validate spatial constraints
        for constraint in &self.constraint_data.spatial {
            if let Some(violation) = self.validate_spatial(placement, constraint, game_state) {
                result.is_valid = false;
                result.violations.push(violation);
            }
        }

        // Validate code constraints
        for constraint in &self.constraint_data.code {
            if let Some(violation) = self.validate_code(placement, constraint) {
                if constraint.is_mandatory {
                    result.is_valid = false;
                    result.violations.push(violation);
                } else {
                    result.warnings.push(violation.message);
                }
            }
        }

        result
    }

    /// Validate structural constraint (wall support)
    fn validate_structural(&self, placement: &GameEquipmentPlacement, constraint: &StructuralConstraint) -> Option<ConstraintViolation> {
        let pos = &placement.equipment.position;
        
        // Check if position is within any valid area
        for area in &constraint.valid_areas {
            if area.bbox.contains_point(&Point3D::new(pos.x, pos.y, pos.z)) {
                // Check load capacity if specified
                if let Some(_capacity) = area.load_capacity {
                    // TODO: Get equipment weight from properties
                    // For now, assume valid if in valid area
                }
                return None; // Valid position
            }
        }

        // Position not in any valid area
        Some(ConstraintViolation {
            constraint_id: constraint.id.clone(),
            constraint_type: ConstraintType::Structural,
            severity: ConstraintSeverity::Error,
            message: format!("Equipment position ({:.2}, {:.2}, {:.2}) not in valid wall support area", pos.x, pos.y, pos.z),
            suggestion: Some("Move equipment to a location with wall support".to_string()),
        })
    }

    /// Validate spatial constraint (clearance)
    fn validate_spatial(&self, placement: &GameEquipmentPlacement, constraint: &SpatialConstraint, game_state: &GameState) -> Option<ConstraintViolation> {
        // Check if this constraint applies to this equipment type
        if let Some(ref required_type) = constraint.equipment_type {
            let eq_type_str = format!("{:?}", placement.equipment.equipment_type);
            if !eq_type_str.contains(required_type) {
                return None; // Constraint doesn't apply
            }
        }

        // Check clearance against other equipment
        let pos = Point3D::new(
            placement.equipment.position.x,
            placement.equipment.position.y,
            placement.equipment.position.z,
        );

        for other_placement in &game_state.placements {
            if other_placement.equipment.id == placement.equipment.id {
                continue; // Skip self
            }

            let other_pos = Point3D::new(
                other_placement.equipment.position.x,
                other_placement.equipment.position.y,
                other_placement.equipment.position.z,
            );

            let distance = self.calculate_distance(&pos, &other_pos);
            
            if distance < constraint.min_clearance {
                return Some(ConstraintViolation {
                    constraint_id: constraint.id.clone(),
                    constraint_type: ConstraintType::Spatial,
                    severity: ConstraintSeverity::Warning,
                    message: format!(
                        "Insufficient clearance: {:.2}m between equipment (minimum: {:.2}m)",
                        distance, constraint.min_clearance
                    ),
                    suggestion: Some("Increase spacing between equipment".to_string()),
                });
            }
        }

        None
    }

    /// Validate code constraint
    fn validate_code(&self, placement: &GameEquipmentPlacement, constraint: &CodeConstraint) -> Option<ConstraintViolation> {
        // Check if this constraint applies to this equipment type
        if let Some(ref required_type) = constraint.equipment_type {
            let eq_type_str = format!("{:?}", placement.equipment.equipment_type);
            if !eq_type_str.contains(required_type) {
                return None; // Constraint doesn't apply
            }
        }

        // Basic validation - can be extended with specific code checks
        // For now, check if accessibility requirement exists
        if constraint.code_type.contains("accessibility") || constraint.code_type.contains("ADA") {
            // Check if equipment has accessibility notes
            let has_accessibility = placement.equipment.properties.contains_key("accessibility_compliant");
            if !has_accessibility && constraint.is_mandatory {
                return Some(ConstraintViolation {
                    constraint_id: constraint.id.clone(),
                    constraint_type: ConstraintType::Code,
                    severity: ConstraintSeverity::Critical,
                    message: constraint.requirement.clone(),
                    suggestion: Some("Verify accessibility compliance requirements".to_string()),
                });
            }
        }

        None
    }

    /// Calculate distance between two points
    fn calculate_distance(&self, p1: &Point3D, p2: &Point3D) -> f64 {
        let dx = p1.x - p2.x;
        let dy = p1.y - p2.y;
        let dz = p1.z - p2.z;
        (dx * dx + dy * dy + dz * dz).sqrt()
    }

    /// Get all constraints
    pub fn get_constraints(&self) -> &[Constraint] {
        &self.constraints
    }

    /// Get constraint by ID
    pub fn get_constraint(&self, id: &str) -> Option<&Constraint> {
        self.constraints.iter().find(|c| c.id == id)
    }
}

impl Default for ConstraintSystem {
    fn default() -> Self {
        Self::new()
    }
}

/// Helper trait for bounding box point containment
trait BoundingBoxContains {
    fn contains_point(&self, point: &Point3D) -> bool;
}

impl BoundingBoxContains for BoundingBox3D {
    fn contains_point(&self, point: &Point3D) -> bool {
        point.x >= self.min.x && point.x <= self.max.x &&
        point.y >= self.min.y && point.y <= self.max.y &&
        point.z >= self.min.z && point.z <= self.max.z
    }
}


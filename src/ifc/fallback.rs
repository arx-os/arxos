// Fallback IFC parser using custom STEP parsing
use crate::core::Building;
use crate::spatial::{Point3D, BoundingBox3D};
use log::info;

pub struct FallbackIFCParser {
    // Custom STEP parser implementation
}

impl FallbackIFCParser {
    pub fn new() -> Self {
        Self {}
    }
    
    pub fn parse_ifc_file(&self, file_path: &str) -> Result<(Building, Vec<crate::spatial::SpatialEntity>), Box<dyn std::error::Error>> {
        info!("Using custom STEP parser for: {}", file_path);
        
        let content = std::fs::read_to_string(file_path)?;
        let (building, spatial_entities) = self.parse_step_content(&content)?;
        
        info!("Parsed building: {} with {} spatial entities", building.name, spatial_entities.len());
        Ok((building, spatial_entities))
    }
    
    fn parse_step_content(&self, content: &str) -> Result<(Building, Vec<crate::spatial::SpatialEntity>), Box<dyn std::error::Error>> {
        // Basic STEP file parsing
        let lines: Vec<&str> = content.lines().collect();
        
        let mut building_name = "Unknown Building".to_string();
        let mut building_id = "unknown".to_string();
        let mut spatial_entities = Vec::new();
        
        // Parse STEP entities
        for line in lines {
            if line.starts_with("#") && line.contains("=") {
                if let Some(entity) = self.parse_entity_line(line) {
                    // Extract building information
                    if entity.entity_type == "IFCBUILDING" {
                        building_name = entity.name.clone();
                        building_id = entity.id.clone();
                    }
                    
                    // Extract spatial information for relevant entities
                    if self.is_spatial_entity(&entity.entity_type) {
                        if let Some(spatial_entity) = self.extract_spatial_data(&entity) {
                            spatial_entities.push(spatial_entity);
                        }
                    }
                }
            }
        }
        
        info!("Parsed building: {} (ID: {})", building_name, building_id);
        let building = Building::new(building_name, format!("/{}", building_id));
        Ok((building, spatial_entities))
    }
    
    pub fn extract_entities(&self, content: &str) -> Result<Vec<IFCEntity>, Box<dyn std::error::Error>> {
        let mut entities = Vec::new();
        let lines: Vec<&str> = content.lines().collect();
        
        for line in lines {
            if line.starts_with("#") && line.contains("=") {
                if let Some(entity) = self.parse_entity_line(line) {
                    entities.push(entity);
                }
            }
        }
        
        info!("Extracted {} entities from IFC file", entities.len());
        Ok(entities)
    }
    
    fn parse_entity_line(&self, line: &str) -> Option<IFCEntity> {
        // Parse entity lines like: #1=IFCBUILDING('Building-1',...)
        let parts: Vec<&str> = line.split('=').collect();
        if parts.len() != 2 {
            return None;
        }
        
        let id = parts[0].trim_start_matches('#').to_string();
        let entity_def = parts[1];
        
        // Extract entity type
        let entity_type = if entity_def.contains("IFCBUILDING") {
            "IFCBUILDING"
        } else if entity_def.contains("IFCSPACE") {
            "IFCSPACE"
        } else if entity_def.contains("IFCFLOWTERMINAL") {
            "IFCFLOWTERMINAL"
        } else if entity_def.contains("IFCBUILDINGELEMENT") {
            "IFCBUILDINGELEMENT"
        } else if entity_def.contains("IFCWALL") {
            "IFCWALL"
        } else if entity_def.contains("IFCDOOR") {
            "IFCDOOR"
        } else if entity_def.contains("IFCWINDOW") {
            "IFCWINDOW"
        } else {
            "UNKNOWN"
        };
        
        // Extract name if present
        let name = if let Some(name_start) = entity_def.find("'") {
            if let Some(name_end) = entity_def[name_start + 1..].find("'") {
                entity_def[name_start + 1..name_start + 1 + name_end].to_string()
            } else {
                "Unknown".to_string()
            }
        } else {
            "Unknown".to_string()
        };
        
        Some(IFCEntity {
            id,
            entity_type: entity_type.to_string(),
            name,
            definition: entity_def.to_string(),
        })
    }

    /// Check if an entity type has spatial information
    fn is_spatial_entity(&self, entity_type: &str) -> bool {
        matches!(entity_type, 
            "IFCSPACE" | "IFCFLOWTERMINAL" | "IFCBUILDINGELEMENT" | 
            "IFCWALL" | "IFCDOOR" | "IFCWINDOW"
        )
    }

    /// Extract spatial data from an IFC entity
    fn extract_spatial_data(&self, entity: &IFCEntity) -> Option<crate::spatial::SpatialEntity> {
        // For now, generate mock spatial data based on entity type
        // In a real implementation, this would parse coordinate data from the STEP definition
        
        let position = match entity.entity_type.as_str() {
            "IFCSPACE" => Point3D::new(
                (entity.id.parse::<f64>().unwrap_or(0.0) * 10.0) % 100.0,
                (entity.id.parse::<f64>().unwrap_or(0.0) * 7.0) % 80.0,
                (entity.id.parse::<f64>().unwrap_or(0.0) * 3.0) % 10.0,
            ),
            "IFCFLOWTERMINAL" => Point3D::new(
                (entity.id.parse::<f64>().unwrap_or(0.0) * 11.0) % 100.0,
                (entity.id.parse::<f64>().unwrap_or(0.0) * 8.0) % 80.0,
                (entity.id.parse::<f64>().unwrap_or(0.0) * 2.5) % 10.0,
            ),
            "IFCWALL" => Point3D::new(
                (entity.id.parse::<f64>().unwrap_or(0.0) * 9.0) % 100.0,
                (entity.id.parse::<f64>().unwrap_or(0.0) * 6.0) % 80.0,
                (entity.id.parse::<f64>().unwrap_or(0.0) * 4.0) % 10.0,
            ),
            _ => Point3D::new(
                (entity.id.parse::<f64>().unwrap_or(0.0) * 5.0) % 100.0,
                (entity.id.parse::<f64>().unwrap_or(0.0) * 3.0) % 80.0,
                (entity.id.parse::<f64>().unwrap_or(0.0) * 2.0) % 10.0,
            ),
        };

        // Create bounding box based on entity type
        let size = match entity.entity_type.as_str() {
            "IFCSPACE" => (5.0, 4.0, 3.0), // Room size
            "IFCFLOWTERMINAL" => (1.0, 1.0, 0.5), // Equipment size
            "IFCWALL" => (0.2, 10.0, 3.0), // Wall dimensions
            _ => (1.0, 1.0, 1.0), // Default size
        };

        let bounding_box = BoundingBox3D::new(
            Point3D::new(position.x - size.0/2.0, position.y - size.1/2.0, position.z - size.2/2.0),
            Point3D::new(position.x + size.0/2.0, position.y + size.1/2.0, position.z + size.2/2.0),
        );

        Some(crate::spatial::SpatialEntity::new(
            entity.id.clone(),
            entity.name.clone(),
            entity.entity_type.clone(),
            position,
        ).with_bounding_box(bounding_box))
    }
}

#[derive(Debug, Clone)]
pub struct IFCEntity {
    pub id: String,
    pub entity_type: String,
    pub name: String,
    pub definition: String,
}

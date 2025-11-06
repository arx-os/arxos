//! IFC entity extraction from STEP format
//!
//! Parses STEP file lines and extracts IFC entities.

use super::types::IFCEntity;

/// Extracts IFC entities from STEP file content
pub struct EntityExtractor;

impl EntityExtractor {
    pub fn new() -> Self {
        Self
    }
    
    /// Extract all entities from STEP content
    pub fn extract_entities(&self, content: &str) -> Result<Vec<IFCEntity>, Box<dyn std::error::Error>> {
        use log::info;
        
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
    
    /// Parse a single entity line from STEP format
    ///
    /// Format: #1=IFCBUILDING('Building-1',...)
    pub fn parse_entity_line(&self, line: &str) -> Option<IFCEntity> {
        let parts: Vec<&str> = line.split('=').collect();
        if parts.len() != 2 {
            return None;
        }
        
        let id = parts[0].trim_start_matches('#').to_string();
        let entity_def = parts[1];
        
        // Extract entity type (check more specific types first, excluding TYPE definitions)
        let entity_type = self.detect_entity_type(entity_def);
        
        // Extract name if present
        let name = self.extract_name(entity_def);
        
        Some(IFCEntity {
            id,
            entity_type: entity_type.to_string(),
            name,
            definition: entity_def.to_string(),
        })
    }
    
    /// Detect entity type from STEP definition
    fn detect_entity_type(&self, entity_def: &str) -> &str {
        if entity_def.contains("IFCBUILDINGSTOREY") {
            "IFCBUILDINGSTOREY"
        } else if entity_def.contains("IFCBUILDING") && !entity_def.contains("IFCBUILDINGTYPE") {
            "IFCBUILDING"
        } else if entity_def.contains("IFCSPACE") {
            "IFCSPACE"
        } else if entity_def.contains("IFCAIRTERMINALTYPE") {
            "IFCAIRTERMINALTYPE"
        } else if entity_def.contains("IFCAIRTERMINAL") {
            "IFCAIRTERMINAL"
        } else if entity_def.contains("IFCFLOWTERMINALTYPE") {
            "IFCFLOWTERMINALTYPE"
        } else if entity_def.contains("IFCFLOWTERMINAL") {
            "IFCFLOWTERMINAL"
        } else if entity_def.contains("IFCPRODUCTDEFINITIONSHAPE") {
            "IFCPRODUCTDEFINITIONSHAPE"
        } else if entity_def.contains("IFCSHAPEREPRESENTATION") {
            "IFCSHAPEREPRESENTATION"
        } else if entity_def.contains("IFCEXTRUDEDAREASOLID") {
            "IFCEXTRUDEDAREASOLID"
        } else if entity_def.contains("IFCARBITRARYCLOSEDPROFILEDEF") {
            "IFCARBITRARYCLOSEDPROFILEDEF"
        } else if entity_def.contains("IFCPOLYLINE") {
            "IFCPOLYLINE"
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
        }
    }
    
    /// Extract name from entity definition
    fn extract_name(&self, entity_def: &str) -> String {
        if let Some(name_start) = entity_def.find("'") {
            if let Some(name_end) = entity_def[name_start + 1..].find("'") {
                entity_def[name_start + 1..name_start + 1 + name_end].to_string()
            } else {
                "Unknown".to_string()
            }
        } else {
            "Unknown".to_string()
        }
    }
}

impl Default for EntityExtractor {
    fn default() -> Self {
        Self::new()
    }
}


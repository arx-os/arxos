//! glTF export functionality for ArxOS
//! 
//! This module provides glTF 2.0 export for building data.

use crate::yaml::BuildingData;
use std::path::Path;
use log::info;

/// glTF exporter for building data
pub struct GLTFExporter {
    building_data: BuildingData,
}

impl GLTFExporter {
    /// Create a new glTF exporter from building data
    pub fn new(building_data: &BuildingData) -> Self {
        Self {
            building_data: building_data.clone(),
        }
    }
    
    /// Export building to glTF format
    pub fn export(&self, output: &Path) -> Result<(), Box<dyn std::error::Error>> {
        info!("Exporting building to glTF: {}", output.display());
        
        // For now, we'll create a basic glTF JSON structure
        // A full implementation would use the gltf crate's Document API
        
        let gltf_json = self.generate_gltf_json()?;
        
        // Write to file
        std::fs::write(output, gltf_json)?;
        
        info!("Successfully exported glTF to {}", output.display());
        Ok(())
    }
    
    /// Generate glTF JSON representation
    fn generate_gltf_json(&self) -> Result<String, Box<dyn std::error::Error>> {
        use serde_json::{json, Map};
        
        // Create minimal glTF 2.0 structure
        let mut asset = Map::new();
        asset.insert("version".to_string(), json!("2.0"));
        asset.insert("generator".to_string(), json!("ArxOS"));
        
        let mut gltf = Map::new();
        gltf.insert("asset".to_string(), json!(asset));
        gltf.insert("scene".to_string(), json!(0));
        
        // Build scenes array
        let mut scenes = Vec::new();
        let mut scene = Map::new();
        
        // Collect all nodes for each floor
        let mut floor_nodes = Vec::new();
        for (idx, _floor) in self.building_data.floors.iter().enumerate() {
            let node_id = idx as u32;
            floor_nodes.push(json!(node_id));
        }
        scene.insert("nodes".to_string(), json!(floor_nodes));
        scenes.push(json!(scene));
        
        gltf.insert("scenes".to_string(), json!(scenes));
        
        // Build nodes array
        let mut nodes = Vec::new();
        for floor in &self.building_data.floors {
            let mut floor_node = Map::new();
            floor_node.insert("name".to_string(), json!(floor.name));
            
            // Add transformation for floor elevation
            let mut translation = Vec::new();
            translation.push(json!(0.0)); // x
            translation.push(json!(floor.elevation)); // y (elevation)
            translation.push(json!(0.0)); // z
            floor_node.insert("translation".to_string(), json!(translation));
            
            // Add equipment as child nodes
            let mut equipment_nodes = Vec::new();
            let base_node = nodes.len() as u32;
            for (idx, _equipment) in floor.equipment.iter().enumerate() {
                equipment_nodes.push(json!(base_node + idx as u32));
            }
            
            if !equipment_nodes.is_empty() {
                floor_node.insert("children".to_string(), json!(equipment_nodes));
            }
            
            nodes.push(json!(floor_node));
            
            // Add equipment nodes
            for equipment in &floor.equipment {
                let mut equipment_node = Map::new();
                equipment_node.insert("name".to_string(), json!(equipment.name));
                
                // Add equipment position
                let mut translation = Vec::new();
                translation.push(json!(equipment.position.x));
                translation.push(json!(equipment.position.y));
                translation.push(json!(equipment.position.z));
                equipment_node.insert("translation".to_string(), json!(translation));
                
                // Add metadata as extras
                if !equipment.properties.is_empty() {
                    let mut extras = Map::new();
                    for (key, value) in &equipment.properties {
                        extras.insert(key.clone(), json!(value));
                    }
                    equipment_node.insert("extras".to_string(), json!(extras));
                }
                
                nodes.push(json!(equipment_node));
            }
        }
        
        gltf.insert("nodes".to_string(), json!(nodes));
        
        // Add empty arrays for required fields
        gltf.insert("meshes".to_string(), json!([]));
        gltf.insert("accessors".to_string(), json!([]));
        gltf.insert("bufferViews".to_string(), json!([]));
        gltf.insert("buffers".to_string(), json!([]));
        gltf.insert("materials".to_string(), json!([]));
        gltf.insert("textures".to_string(), json!([]));
        gltf.insert("images".to_string(), json!([]));
        gltf.insert("samplers".to_string(), json!([]));
        
        // Add extensions used
        let extensions_used: Vec<String> = Vec::new();
        gltf.insert("extensionsUsed".to_string(), json!(extensions_used));
        gltf.insert("extensionsRequired".to_string(), json!(Vec::<String>::new()));
        
        // Convert to JSON string
        let json_string = serde_json::to_string_pretty(&gltf)?;
        Ok(json_string)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::yaml::{BuildingInfo, BuildingMetadata};
    use chrono::Utc;
    
    fn create_test_building() -> BuildingData {
        BuildingData {
            building: BuildingInfo {
                id: "test-1".to_string(),
                name: "Test Building".to_string(),
                description: Some("Test".to_string()),
                created_at: Utc::now(),
                updated_at: Utc::now(),
                version: "1.0".to_string(),
                global_bounding_box: None,
            },
            metadata: BuildingMetadata {
                source_file: None,
                parser_version: "Test".to_string(),
                total_entities: 0,
                spatial_entities: 0,
                coordinate_system: "LOCAL".to_string(),
                units: "meters".to_string(),
                tags: vec![],
            },
            floors: vec![],
            coordinate_systems: vec![],
        }
    }
    
    #[test]
    fn test_gltf_exporter_creation() {
        let building = create_test_building();
        let _exporter = GLTFExporter::new(&building);
        // Should not panic
    }
    
    #[test]
    fn test_gltf_json_generation() {
        let building = create_test_building();
        let exporter = GLTFExporter::new(&building);
        let json = exporter.generate_gltf_json().unwrap();
        assert!(json.contains("\"version\""));
        assert!(json.contains("\"asset\""));
    }
}


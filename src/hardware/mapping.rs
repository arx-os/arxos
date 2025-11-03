//! Sensor-equipment mapping management with persistence
//!
//! This module provides functionality to map sensors to equipment, store mappings,
//! and persist them to YAML files.

use super::{EquipmentSensorMapping, HardwareError, HardwareResult};
use crate::utils::path_safety::PathSafety;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use log::{info, warn};

/// Sensor-equipment mapping manager
#[derive(Debug)]
pub struct MappingManager {
    mappings: HashMap<String, EquipmentSensorMapping>,
    mapping_file: PathBuf,
}

/// Mapping collection for serialization
#[derive(Debug, Clone, Serialize, Deserialize)]
struct MappingCollection {
    mappings: Vec<EquipmentSensorMapping>,
}

impl MappingManager {
    /// Create a new mapping manager
    pub fn new(mapping_file: PathBuf) -> Self {
        Self {
            mappings: HashMap::new(),
            mapping_file,
        }
    }
    
    /// Load mappings from YAML file
    pub fn load(&mut self) -> HardwareResult<()> {
        if !self.mapping_file.exists() {
            info!("No mapping file found at {:?}, starting with empty mappings", self.mapping_file);
            return Ok(());
        }
        
        info!("Loading sensor-equipment mappings from {:?}", self.mapping_file);
        
        let base_dir = self.mapping_file.parent()
            .unwrap_or_else(|| Path::new("."));
        
        let content = PathSafety::read_file_safely(&self.mapping_file, base_dir)
            .map_err(|e| HardwareError::IoError(std::io::Error::other(format!("Failed to read mapping file: {}", e))))?;
        
        let collection: MappingCollection = serde_yaml::from_str(&content)
            .map_err(|e| HardwareError::YamlError(e))?;
        
        self.mappings.clear();
        for mapping in collection.mappings {
            self.mappings.insert(mapping.sensor_id.clone(), mapping);
        }
        
        info!("Loaded {} sensor-equipment mappings", self.mappings.len());
        Ok(())
    }
    
    /// Save mappings to YAML file
    pub fn save(&self) -> HardwareResult<()> {
        info!("Saving {} sensor-equipment mappings to {:?}", self.mappings.len(), self.mapping_file);
        
        let collection = MappingCollection {
            mappings: self.mappings.values().cloned().collect(),
        };
        
        let yaml_content = serde_yaml::to_string(&collection)
            .map_err(|e| HardwareError::YamlError(e))?;
        
        // Create parent directory if it doesn't exist
        if let Some(parent) = self.mapping_file.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| HardwareError::IoError(std::io::Error::other(format!("Failed to create directory: {}", e))))?;
        }
        
        std::fs::write(&self.mapping_file, yaml_content)
            .map_err(|e| HardwareError::IoError(std::io::Error::other(format!("Failed to write mapping file: {}", e))))?;
        
        info!("Successfully saved mappings");
        Ok(())
    }
    
    /// Add or update a mapping
    pub fn add_mapping(&mut self, mapping: EquipmentSensorMapping) {
        info!("Adding/updating mapping: sensor {} -> equipment {}", mapping.sensor_id, mapping.equipment_id);
        self.mappings.insert(mapping.sensor_id.clone(), mapping);
    }
    
    /// Get mapping for a sensor
    pub fn get_mapping(&self, sensor_id: &str) -> Option<&EquipmentSensorMapping> {
        self.mappings.get(sensor_id)
    }
    
    /// Get all mappings
    pub fn get_all_mappings(&self) -> Vec<&EquipmentSensorMapping> {
        self.mappings.values().collect()
    }
    
    /// Remove a mapping
    pub fn remove_mapping(&mut self, sensor_id: &str) -> bool {
        if self.mappings.remove(sensor_id).is_some() {
            info!("Removed mapping for sensor: {}", sensor_id);
            true
        } else {
            warn!("No mapping found for sensor: {}", sensor_id);
            false
        }
    }
    
    /// Find all sensors for an equipment
    pub fn find_sensors_for_equipment(&self, equipment_id: &str) -> Vec<&EquipmentSensorMapping> {
        self.mappings.values()
            .filter(|m| m.equipment_id == equipment_id)
            .collect()
    }
    
    /// Get mapping file path
    pub fn get_mapping_file(&self) -> &Path {
        &self.mapping_file
    }
}

impl Default for MappingManager {
    fn default() -> Self {
        Self::new(PathBuf::from("./sensor_mappings.yaml"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use super::super::SensorType;
    use tempfile::TempDir;
    
    #[test]
    fn test_mapping_manager_add_and_get() {
        let mut manager = MappingManager::default();
        
        let mapping = EquipmentSensorMapping {
            equipment_id: "HVAC-301".to_string(),
            sensor_id: "sensor_001".to_string(),
            sensor_type: SensorType::Temperature,
            threshold_min: Some(65.0),
            threshold_max: Some(75.0),
            alert_on_out_of_range: true,
        };
        
        manager.add_mapping(mapping.clone());
        
        let retrieved = manager.get_mapping("sensor_001").unwrap();
        assert_eq!(retrieved.equipment_id, "HVAC-301");
        assert_eq!(retrieved.sensor_id, "sensor_001");
    }
    
    #[test]
    fn test_mapping_manager_save_and_load() {
        let temp_dir = TempDir::new().unwrap();
        let mapping_file = temp_dir.path().join("mappings.yaml");
        
        let mut manager = MappingManager::new(mapping_file.clone());
        
        let mapping1 = EquipmentSensorMapping {
            equipment_id: "HVAC-301".to_string(),
            sensor_id: "sensor_001".to_string(),
            sensor_type: SensorType::Temperature,
            threshold_min: Some(65.0),
            threshold_max: Some(75.0),
            alert_on_out_of_range: true,
        };
        
        let mapping2 = EquipmentSensorMapping {
            equipment_id: "HVAC-302".to_string(),
            sensor_id: "sensor_002".to_string(),
            sensor_type: SensorType::Humidity,
            threshold_min: Some(40.0),
            threshold_max: Some(60.0),
            alert_on_out_of_range: true,
        };
        
        manager.add_mapping(mapping1);
        manager.add_mapping(mapping2);
        manager.save().unwrap();
        
        // Load into a new manager
        let mut manager2 = MappingManager::new(mapping_file);
        manager2.load().unwrap();
        
        assert_eq!(manager2.mappings.len(), 2);
        assert!(manager2.get_mapping("sensor_001").is_some());
        assert!(manager2.get_mapping("sensor_002").is_some());
    }
    
    #[test]
    fn test_mapping_manager_find_sensors_for_equipment() {
        let mut manager = MappingManager::default();
        
        let mapping1 = EquipmentSensorMapping {
            equipment_id: "HVAC-301".to_string(),
            sensor_id: "sensor_001".to_string(),
            sensor_type: SensorType::Temperature,
            threshold_min: None,
            threshold_max: None,
            alert_on_out_of_range: false,
        };
        
        let mapping2 = EquipmentSensorMapping {
            equipment_id: "HVAC-301".to_string(),
            sensor_id: "sensor_002".to_string(),
            sensor_type: SensorType::Humidity,
            threshold_min: None,
            threshold_max: None,
            alert_on_out_of_range: false,
        };
        
        manager.add_mapping(mapping1);
        manager.add_mapping(mapping2);
        
        let sensors = manager.find_sensors_for_equipment("HVAC-301");
        assert_eq!(sensors.len(), 2);
    }
}


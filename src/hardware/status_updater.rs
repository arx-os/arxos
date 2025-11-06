//! Equipment status updater for hardware integration
//! 
//! This module processes sensor data and updates equipment status in building data.

use super::{SensorData, HardwareError, HardwareResult, AlertGenerator, ThresholdCheck};
use crate::persistence::PersistenceManager;
use std::collections::HashMap;
use log::info;

/// Result of updating equipment from sensor data
#[derive(Debug, Clone)]
pub struct UpdateResult {
    pub equipment_id: String,
    pub old_status: String,
    pub new_status: String,
    pub timestamp: String,
    pub alerts: Vec<super::SensorAlert>,
}

/// Equipment status updater
pub struct EquipmentStatusUpdater {
    persistence: PersistenceManager,
    _mappings: Vec<SensorEquipmentMapping>,
    _building_name: String,
}

#[derive(Debug, Clone)]
struct SensorEquipmentMapping {
    sensor_id: String,
    equipment_id: String,
    #[allow(dead_code)] // Reserved for future type-specific processing
    sensor_type: String,
    thresholds: HashMap<String, ThresholdConfig>,
}

#[derive(Debug, Clone)]
struct ThresholdConfig {
    min: Option<f64>,
    max: Option<f64>,
}

impl EquipmentStatusUpdater {
    /// Create a new equipment status updater
    pub fn new(building_name: &str) -> HardwareResult<Self> {
        let persistence = PersistenceManager::new(building_name)
            .map_err(|e| HardwareError::IoError(std::io::Error::other(format!("Failed to create persistence manager: {}", e))))?;
        
        // Load sensor mappings from building data
        let mappings = Self::load_sensor_mappings(&persistence)?;
        
        Ok(Self {
            persistence,
            _mappings: mappings,
            _building_name: building_name.to_string(),
        })
    }
    
    /// Load sensor mappings from building data
    fn load_sensor_mappings(persistence: &PersistenceManager) -> HardwareResult<Vec<SensorEquipmentMapping>> {
        let building_data = persistence.load_building_data()
            .map_err(|e| HardwareError::IoError(std::io::Error::other(e.to_string())))?;
        
        let mut mappings = Vec::new();
        
        
        
        
        for floor in &building_data.floors {
            for equipment in &floor.equipment {
                if let Some(ref sensor_mappings) = equipment.sensor_mappings {
                    for mapping in sensor_mappings {
                        // Convert from YAML SensorMapping to internal format
                        let mut threshold_map = HashMap::new();
                        for (key, threshold_config) in &mapping.thresholds {
                            threshold_map.insert(key.clone(), ThresholdConfig {
                                min: threshold_config.min,
                                max: threshold_config.max,
                            });
                        }
                        
                        mappings.push(SensorEquipmentMapping {
                            sensor_id: mapping.sensor_id.clone(),
                            equipment_id: equipment.id.clone(),
                            sensor_type: mapping.sensor_type.clone(),
                            thresholds: threshold_map,
                        });
                    }
                }
            }
        }
        
        info!("Loaded {} sensor mappings from building data", mappings.len());
        Ok(mappings)
    }
    
    /// Process sensor data and update equipment status
    pub fn process_sensor_data(&mut self, sensor_data: &SensorData) -> HardwareResult<UpdateResult> {
        info!("Processing sensor data from: {}", sensor_data.metadata.sensor_id);
        
        // Find equipment mapped to this sensor
        let equipment_id = self.find_equipment_for_sensor(&sensor_data.metadata.sensor_id)?;
        
        // Load building data
        let mut building_data = self.persistence.load_building_data()
            .map_err(|e| HardwareError::IoError(std::io::Error::other(e.to_string())))?;
        
        // Find and update equipment
        let mut found = false;
        let mut old_status = String::new();
        let mut equipment_name = String::new();
        let mut alerts = Vec::new();
        
        for floor in &mut building_data.floors {
            if let Some(equipment) = floor.equipment.iter_mut().find(|e| e.id == equipment_id || e.name == equipment_id) {
                old_status = format!("{:?}", equipment.status);
                equipment_name = equipment.name.clone();
                
                // Check sensor thresholds and update status
                let threshold_check = self.check_sensor_thresholds(sensor_data);
                let sensor_value = self.extract_main_value(sensor_data).unwrap_or(0.0);
                
                // Generate alerts based on threshold check
                alerts = AlertGenerator::generate_alerts(
                    sensor_data,
                    &threshold_check,
                    &equipment_id,
                    sensor_value,
                );
                
                // Update status based on sensor readings
                use crate::core::EquipmentHealthStatus;
                match threshold_check {
                    ThresholdCheck::Critical => {
                        equipment.health_status = Some(EquipmentHealthStatus::Critical);
                    }
                    ThresholdCheck::OutOfRange => {
                        equipment.health_status = Some(EquipmentHealthStatus::Warning);
                    }
                    ThresholdCheck::Normal => {
                        equipment.health_status = Some(EquipmentHealthStatus::Healthy);
                    }
                }
                
                // Generate status change alert if status degraded
                let new_status_str = format!("{:?}", equipment.status);
                if let Some(status_alert) = AlertGenerator::generate_status_change_alert(
                    &equipment_id,
                    &old_status,
                    &new_status_str,
                ) {
                    alerts.push(status_alert);
                }
                
                // Update last sensor reading timestamp
                equipment.properties.insert("last_sensor_reading".to_string(), 
                                            sensor_data.metadata.timestamp.clone());
                equipment.properties.insert("last_sensor_id".to_string(), 
                                            sensor_data.metadata.sensor_id.clone());
                
                found = true;
                break;
            }
        }
        
        if !found {
            return Err(HardwareError::MappingError {
                reason: format!("Equipment '{}' not found in building data", equipment_id),
            });
        }
        
        // Save changes
        self.persistence.save_building_data(&building_data)
            .map_err(|e| HardwareError::IoError(std::io::Error::other(e.to_string())))?;
        
        // Get the new status after update
        let new_status = building_data.floors.iter()
            .flat_map(|f| &f.equipment)
            .find(|e| e.id == equipment_id || e.name == equipment_id)
            .map(|e| format!("{:?}", e.status))
            .unwrap_or_else(|| "Unknown".to_string());
        
        info!("Updated {}: {} → {} ({} alerts)", equipment_name, old_status, new_status, alerts.len());
        
        Ok(UpdateResult {
            equipment_id,
            old_status,
            new_status,
            timestamp: sensor_data.metadata.timestamp.clone(),
            alerts,
        })
    }
    
    /// Find equipment ID for a sensor
    fn find_equipment_for_sensor(&self, sensor_id: &str) -> HardwareResult<String> {
        // Check explicit mappings first
        if let Some(mapping) = self._mappings.iter().find(|m| m.sensor_id == sensor_id) {
            return Ok(mapping.equipment_id.clone());
        }
        
        // Try to infer from sensor ID pattern
        // For now, use sensor_id as equipment_id (assumes 1:1 mapping)
        Ok(sensor_id.to_string())
    }
    
    /// Check sensor thresholds and determine status
    fn check_sensor_thresholds(&self, sensor_data: &SensorData) -> ThresholdCheck {
        // Get a numeric value from sensor data
        let value = match self.extract_main_value(sensor_data) {
            Some(v) => v,
            None => {
                info!("Could not extract numeric value from sensor data, defaulting to Unknown status");
                return ThresholdCheck::Critical; // Unknown values are critical
            }
        };
        
        // Find matching sensor mapping to use configured thresholds
        let sensor_id = &sensor_data.metadata.sensor_id;
        let sensor_type = &sensor_data.metadata.sensor_type.to_lowercase();
        
        // Check if we have explicit thresholds for this sensor
        if let Some(mapping) = self._mappings.iter().find(|m| m.sensor_id == *sensor_id) {
            // Use configured thresholds from mapping
            for (key, threshold_config) in &mapping.thresholds {
                if sensor_type.contains(key) || sensor_type.contains(&key.to_lowercase()) {
                    // Check critical range
                    if let (Some(min), Some(max)) = (threshold_config.min, threshold_config.max) {
                        if value < min || value > max {
                            info!("Value {} is outside critical range [{}, {}]", value, min, max);
                            return ThresholdCheck::Critical;
                        }
                    }
                    
                    // Check warning range (if configured)
                    if let (Some(min), Some(max)) = (threshold_config.min, threshold_config.max) {
                        // Assume 90% of critical range as warning
                        let warning_min = min + (max - min) * 0.05;
                        let warning_max = max - (max - min) * 0.05;
                        if value < warning_min || value > warning_max {
                            info!("Value {} is outside warning range [{:.2}, {:.2}]", value, warning_min, warning_max);
                            return ThresholdCheck::OutOfRange;
                        }
                    }
                }
            }
        }
        
        // Fallback to default thresholds based on sensor type
        if sensor_type.contains("temperature") || sensor_type.contains("temp") {
            // Temperature-specific thresholds (in Fahrenheit for HVAC)
            if !(50.0..=100.0).contains(&value) {
                info!("Temperature {}°F is in critical range", value);
                return ThresholdCheck::Critical;
            }
            if !(60.0..=85.0).contains(&value) {
                info!("Temperature {}°F is in warning range", value);
                return ThresholdCheck::OutOfRange;
            }
        } else if sensor_type.contains("humidity") {
            // Humidity thresholds (percentage)
            if !(20.0..=80.0).contains(&value) {
                info!("Humidity {}% is in critical range", value);
                return ThresholdCheck::Critical;
            }
            if !(30.0..=70.0).contains(&value) {
                info!("Humidity {}% is in warning range", value);
                return ThresholdCheck::OutOfRange;
            }
        } else if sensor_type.contains("air_quality") || sensor_type.contains("co2") {
            // Air quality thresholds (ppm for CO2)
            if value > 1000.0 {
                info!("Air quality {} ppm is in critical range", value);
                return ThresholdCheck::Critical;
            }
            if value > 800.0 {
                info!("Air quality {} ppm is in warning range", value);
                return ThresholdCheck::OutOfRange;
            }
        }
        
        info!("Sensor value {} is within normal range", value);
        ThresholdCheck::Normal
    }
    
    fn extract_main_value(&self, sensor_data: &SensorData) -> Option<f64> {
        // Try to extract the first numeric value from data.values
        for value in sensor_data.data.values.values() {
            if let Some(num_val) = value.as_f64() {
                return Some(num_val);
            }
            if let Some(num_val) = value.as_u64().map(|v| v as f64) {
                return Some(num_val);
            }
            if let Some(num_val) = value.as_i64().map(|v| v as f64) {
                return Some(num_val);
            }
        }
        None
    }
    
    /// Commit changes to Git
    pub fn commit_changes(&self, message: &str) -> HardwareResult<String> {
        let building_data = self.persistence.load_building_data()
            .map_err(|e| HardwareError::IoError(std::io::Error::other(e.to_string())))?;
        
        self.persistence.save_and_commit(&building_data, Some(message))
            .map_err(|e| HardwareError::IoError(std::io::Error::other(e.to_string())))
    }
}


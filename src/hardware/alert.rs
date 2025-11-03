//! Alert generation for hardware sensors
//! 
//! This module generates explicit alert objects when sensor thresholds are exceeded
//! or equipment status changes to Warning or Critical states.

use super::{SensorData, SensorAlert, ThresholdCheck};
use chrono::Utc;

/// Alert generator for sensor data processing
pub struct AlertGenerator;

impl AlertGenerator {
    /// Generate alerts based on threshold check result
    /// 
    /// # Arguments
    /// * `sensor_data` - The sensor data that triggered the check
    /// * `threshold_check` - Result of threshold checking
    /// * `equipment_id` - ID of the affected equipment
    /// * `value` - The actual sensor value that triggered the alert
    /// 
    /// # Returns
    /// * Vector of SensorAlert objects (may be empty if no alert needed)
    pub fn generate_alerts(
        sensor_data: &SensorData,
        threshold_check: &ThresholdCheck,
        equipment_id: &str,
        value: f64,
    ) -> Vec<SensorAlert> {
        let mut alerts = Vec::new();

        match threshold_check {
            ThresholdCheck::Critical => {
                alerts.push(SensorAlert {
                    level: "critical".to_string(),
                    message: format!(
                        "Critical threshold exceeded for equipment '{}': sensor '{}' value {:.2} is out of critical range",
                        equipment_id,
                        sensor_data.metadata.sensor_id,
                        value
                    ),
                    timestamp: Utc::now().to_rfc3339(),
                });
            }
            ThresholdCheck::OutOfRange => {
                alerts.push(SensorAlert {
                    level: "warning".to_string(),
                    message: format!(
                        "Warning threshold exceeded for equipment '{}': sensor '{}' value {:.2} is out of normal range",
                        equipment_id,
                        sensor_data.metadata.sensor_id,
                        value
                    ),
                    timestamp: Utc::now().to_rfc3339(),
                });
            }
            ThresholdCheck::Normal => {
                // No alert for normal values
            }
        }

        alerts
    }

    /// Generate alert for status change
    /// 
    /// Generates an alert when equipment status changes to Warning or Critical.
    /// 
    /// # Arguments
    /// * `equipment_id` - ID of the equipment
    /// * `old_status` - Previous status
    /// * `new_status` - New status
    /// 
    /// # Returns
    /// * Option<SensorAlert> - Alert if status degraded, None otherwise
    pub fn generate_status_change_alert(
        equipment_id: &str,
        old_status: &str,
        new_status: &str,
    ) -> Option<SensorAlert> {
        // Only generate alert if status degraded (worse than before)
        let is_degraded = (old_status.contains("Healthy") || old_status.contains("Unknown"))
            && (new_status.contains("Warning") || new_status.contains("Critical"));
        
        if is_degraded {
            Some(SensorAlert {
                level: if new_status.contains("Critical") {
                    "critical".to_string()
                } else {
                    "warning".to_string()
                },
                message: format!(
                    "Equipment '{}' status changed: {} → {}",
                    equipment_id,
                    old_status,
                    new_status
                ),
                timestamp: Utc::now().to_rfc3339(),
            })
        } else {
            None
        }
    }

    /// Generate alert for sensor mapping not found
    /// 
    /// # Arguments
    /// * `sensor_id` - ID of the sensor that couldn't be mapped
    /// 
    /// # Returns
    /// * SensorAlert indicating mapping issue
    pub fn generate_mapping_alert(sensor_id: &str) -> SensorAlert {
        SensorAlert {
            level: "warning".to_string(),
            message: format!(
                "Sensor '{}' could not be mapped to equipment. Data received but not processed.",
                sensor_id
            ),
            timestamp: Utc::now().to_rfc3339(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hardware::SensorMetadata;
    use std::collections::HashMap;

    fn create_test_sensor_data() -> SensorData {
        SensorData {
            api_version: "arxos.io/v1".to_string(),
            kind: "SensorData".to_string(),
            metadata: SensorMetadata {
                sensor_id: "sensor-001".to_string(),
                sensor_type: "temperature".to_string(),
                room_path: None,
                timestamp: Utc::now().to_rfc3339(),
                source: "test".to_string(),
                building_id: None,
                equipment_id: Some("equipment-001".to_string()),
                extra: HashMap::new(),
            },
            data: crate::hardware::SensorDataValues {
                values: {
                    let mut map = HashMap::new();
                    map.insert("temperature".to_string(), serde_yaml::Value::Number(serde_yaml::Number::from(100)));
                    map
                },
            },
            alerts: vec![],
            arxos: None,
        }
    }

    #[test]
    fn test_generate_critical_alert() {
        let sensor_data = create_test_sensor_data();
        let alerts = AlertGenerator::generate_alerts(
            &sensor_data,
            &ThresholdCheck::Critical,
            "equipment-001",
            100.0,
        );
        
        assert_eq!(alerts.len(), 1);
        assert_eq!(alerts[0].level, "critical");
        assert!(alerts[0].message.contains("Critical threshold exceeded"));
        assert!(alerts[0].message.contains("equipment-001"));
    }

    #[test]
    fn test_generate_warning_alert() {
        let sensor_data = create_test_sensor_data();
        let alerts = AlertGenerator::generate_alerts(
            &sensor_data,
            &ThresholdCheck::OutOfRange,
            "equipment-001",
            85.0,
        );
        
        assert_eq!(alerts.len(), 1);
        assert_eq!(alerts[0].level, "warning");
        assert!(alerts[0].message.contains("Warning threshold exceeded"));
    }

    #[test]
    fn test_no_alert_for_normal() {
        let sensor_data = create_test_sensor_data();
        let alerts = AlertGenerator::generate_alerts(
            &sensor_data,
            &ThresholdCheck::Normal,
            "equipment-001",
            72.0,
        );
        
        assert_eq!(alerts.len(), 0);
    }

    #[test]
    fn test_status_change_alert() {
        let alert = AlertGenerator::generate_status_change_alert(
            "equipment-001",
            "Healthy",
            "Critical",
        );
        
        assert!(alert.is_some());
        let alert = alert.unwrap();
        assert_eq!(alert.level, "critical");
        assert!(alert.message.contains("status changed"));
    }

    #[test]
    fn test_status_change_no_alert_for_improvement() {
        let alert = AlertGenerator::generate_status_change_alert(
            "equipment-001",
            "Warning",
            "Healthy",
        );
        
        // Should not generate alert for status improvement
        assert!(alert.is_none());
    }
}


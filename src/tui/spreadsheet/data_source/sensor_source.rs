//! Sensor data source implementation
//!
//! Provides spreadsheet interface for sensor data. This is a simplified
//! read-only implementation for viewing sensor readings.

use super::super::types::{CellType, CellValue, ColumnDefinition};
use super::trait_def::SpreadsheetDataSource;
use std::error::Error;

/// Sensor data structure
///
/// Represents a single sensor reading with:
/// - Unique identifier
/// - Numeric value
/// - Timestamp of the reading
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct SensorData {
    pub id: String,
    pub value: f64,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

/// Sensor data source implementation
///
/// Note: This is a simplified implementation. Full sensor data handling
/// would require time-series data management which is beyond the scope
/// of the basic spreadsheet interface.
///
/// Features:
/// - Read-only access to sensor data
/// - Timestamp-based display
/// - No persistence (data is ephemeral)
pub struct SensorDataSource {
    sensor_data: Vec<SensorData>,
    #[allow(dead_code)] // Reserved for future filtering/display features
    building_name: String,
}

impl SensorDataSource {
    /// Create a new sensor data source
    ///
    /// In a real implementation, this would load sensor data from files or API.
    ///
    /// # Arguments
    ///
    /// * `building_name` - Name of the building for context
    pub fn new(building_name: String) -> Self {
        Self {
            sensor_data: Vec::new(),
            building_name,
        }
    }

    /// Load sensor data from files
    ///
    /// Loads sensor data from files in the building directory.
    /// Currently returns empty data as sensor file scanning depends on finalized
    /// sensor file format and directory structure specifications.
    ///
    /// # Returns
    ///
    /// Returns Ok(()) after clearing sensor data. In a full implementation,
    /// this would scan and load sensor data files.
    pub fn load_sensor_data(&mut self) -> Result<(), Box<dyn Error>> {
        // Sensor data loading from files requires finalized sensor file format
        // and directory structure. For now, returns empty data.
        self.sensor_data.clear();
        Ok(())
    }
}

impl SpreadsheetDataSource for SensorDataSource {
    fn columns(&self) -> Vec<ColumnDefinition> {
        vec![
            ColumnDefinition {
                id: "sensor.id".to_string(),
                label: "Sensor ID".to_string(),
                data_type: CellType::Text,
                editable: false,
                width: Some(36),
                validation: None,
                enum_values: None,
            },
            ColumnDefinition {
                id: "sensor.type".to_string(),
                label: "Type".to_string(),
                data_type: CellType::Text,
                editable: false,
                width: Some(15),
                validation: None,
                enum_values: None,
            },
            ColumnDefinition {
                id: "sensor.timestamp".to_string(),
                label: "Timestamp".to_string(),
                data_type: CellType::Date,
                editable: false,
                width: Some(20),
                validation: None,
                enum_values: None,
            },
            ColumnDefinition {
                id: "sensor.equipment_id".to_string(),
                label: "Equipment ID".to_string(),
                data_type: CellType::UUID,
                editable: false,
                width: Some(36),
                validation: None,
                enum_values: None,
            },
        ]
    }

    fn row_count(&self) -> usize {
        self.sensor_data.len()
    }

    fn get_cell(&self, row: usize, col: usize) -> Result<CellValue, Box<dyn Error>> {
        let sensor = self
            .sensor_data
            .get(row)
            .ok_or_else(|| format!("Row {} out of bounds", row))?;

        let columns = self.columns();
        let column = columns
            .get(col)
            .ok_or_else(|| format!("Column {} out of bounds", col))?;

        match column.id.as_str() {
            "sensor.id" => Ok(CellValue::Text(sensor.id.clone())),
            "sensor.value" => Ok(CellValue::Number(sensor.value)),
            "sensor.timestamp" => Ok(CellValue::Date(sensor.timestamp.to_string())),
            // Note: sensor_type and equipment_id fields don't exist in current SensorData
            "sensor.type" => Ok(CellValue::Empty),
            "sensor.equipment_id" => Ok(CellValue::Empty),
            _ => Ok(CellValue::Empty),
        }
    }

    fn set_cell(
        &mut self,
        _row: usize,
        _col: usize,
        _value: CellValue,
    ) -> Result<(), Box<dyn Error>> {
        // Sensor data is read-only in spreadsheet view
        Err("Sensor data is read-only".into())
    }

    fn save(&mut self, _commit: bool) -> Result<(), Box<dyn Error>> {
        // Sensor data is read-only
        Ok(())
    }

    fn reload(&mut self) -> Result<(), Box<dyn Error>> {
        self.load_sensor_data()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sensor_data_source_new() {
        let data_source = SensorDataSource::new("test_building".to_string());
        assert_eq!(data_source.row_count(), 0);
        assert!(data_source.sensor_data.is_empty());
    }

    #[test]
    fn test_sensor_data_source_columns() {
        let data_source = SensorDataSource::new("test_building".to_string());

        let columns = data_source.columns();
        assert!(!columns.is_empty());
        assert!(columns.iter().any(|c| c.id == "sensor.id"));
        assert!(columns.iter().any(|c| c.id == "sensor.type"));
        assert!(columns.iter().any(|c| c.id == "sensor.timestamp"));
        assert!(columns.iter().any(|c| c.id == "sensor.equipment_id"));
    }

    #[test]
    fn test_sensor_data_source_read_only() {
        let mut data_source = SensorDataSource::new("test_building".to_string());

        // Try to set a cell - should fail
        let result = data_source.set_cell(0, 0, CellValue::Text("test".to_string()));
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("read-only"));
    }

    #[test]
    fn test_sensor_data_source_save() {
        let mut data_source = SensorDataSource::new("test_building".to_string());

        // Save should succeed (no-op)
        assert!(data_source.save(false).is_ok());
        assert!(data_source.save(true).is_ok());
    }

    #[test]
    fn test_sensor_data_source_reload() {
        let mut data_source = SensorDataSource::new("test_building".to_string());
        assert!(data_source.reload().is_ok());
    }
}

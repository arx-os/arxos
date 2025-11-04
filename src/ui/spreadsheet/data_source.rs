//! Data source abstraction for spreadsheet
//!
//! Defines trait and implementations for converting building data to spreadsheet format

use crate::yaml::{BuildingData, EquipmentData, RoomData};
use crate::hardware::SensorData;
use super::types::{ColumnDefinition, CellValue, CellType, ValidationRule};
use std::collections::HashMap;

/// Trait for data sources that provide spreadsheet data
pub trait SpreadsheetDataSource: Send + Sync {
    /// Get the column definitions for this data source
    fn columns(&self) -> Vec<ColumnDefinition>;
    
    /// Get the number of rows
    fn row_count(&self) -> usize;
    
    /// Get cell value at (row, col)
    fn get_cell(&self, row: usize, col: usize) -> Result<CellValue, Box<dyn std::error::Error>>;
    
    /// Set cell value at (row, col)
    fn set_cell(&mut self, row: usize, col: usize, value: CellValue) -> Result<(), Box<dyn std::error::Error>>;
    
    /// Save changes to building.yaml and Git
    fn save(&mut self, commit: bool) -> Result<(), Box<dyn std::error::Error>>;
    
    /// Reload from building.yaml
    fn reload(&mut self) -> Result<(), Box<dyn std::error::Error>>;
}

/// Equipment data source implementation
pub struct EquipmentDataSource {
    equipment: Vec<EquipmentData>,
    building_data: BuildingData,
    building_name: String,
    modified_rows: std::collections::HashSet<usize>,
}

impl EquipmentDataSource {
    /// Create a new equipment data source from building data
    pub fn new(building_data: BuildingData, building_name: String) -> Self {
        // Collect all equipment from all floors
        let mut equipment = Vec::new();
        for floor in &building_data.floors {
            equipment.extend(floor.equipment.clone());
        }
        
        Self {
            equipment,
            building_data,
            building_name,
            modified_rows: std::collections::HashSet::new(),
        }
    }
    
    /// Get equipment type enum values
    fn equipment_type_values() -> Vec<String> {
        vec![
            "HVAC".to_string(),
            "Electrical".to_string(),
            "AV".to_string(),
            "Furniture".to_string(),
            "Safety".to_string(),
            "Plumbing".to_string(),
            "Network".to_string(),
        ]
    }
    
    /// Get equipment status enum values
    fn equipment_status_values() -> Vec<String> {
        vec![
            "Active".to_string(),
            "Inactive".to_string(),
            "Maintenance".to_string(),
            "OutOfOrder".to_string(),
            "Unknown".to_string(),
        ]
    }
}

impl SpreadsheetDataSource for EquipmentDataSource {
    fn columns(&self) -> Vec<ColumnDefinition> {
        vec![
            ColumnDefinition {
                id: "equipment.id".to_string(),
                label: "ID".to_string(),
                data_type: CellType::UUID,
                editable: false,
                width: Some(36),
                validation: None,
                enum_values: None,
            },
            ColumnDefinition {
                id: "equipment.name".to_string(),
                label: "Name".to_string(),
                data_type: CellType::Text,
                editable: true,
                width: Some(30),
                validation: Some(ValidationRule::Required),
                enum_values: None,
            },
            ColumnDefinition {
                id: "equipment.type".to_string(),
                label: "Type".to_string(),
                data_type: CellType::Enum(Self::equipment_type_values()),
                editable: true,
                width: Some(15),
                validation: None,
                enum_values: Some(Self::equipment_type_values()),
            },
            ColumnDefinition {
                id: "equipment.status".to_string(),
                label: "Status".to_string(),
                data_type: CellType::Enum(Self::equipment_status_values()),
                editable: true,
                width: Some(12),
                validation: None,
                enum_values: Some(Self::equipment_status_values()),
            },
        ]
    }
    
    fn row_count(&self) -> usize {
        self.equipment.len()
    }
    
    fn get_cell(&self, row: usize, col: usize) -> Result<CellValue, Box<dyn std::error::Error>> {
        let equipment = self.equipment.get(row)
            .ok_or_else(|| format!("Row {} out of bounds", row))?;
        
        let columns = self.columns();
        let column = columns.get(col)
            .ok_or_else(|| format!("Column {} out of bounds", col))?;
        
        match column.id.as_str() {
            "equipment.id" => Ok(CellValue::UUID(equipment.id.clone())),
            "equipment.name" => Ok(CellValue::Text(equipment.name.clone())),
            "equipment.type" => Ok(CellValue::Enum(equipment.equipment_type.clone())),
            "equipment.status" => {
                let status_str = match equipment.status {
                    crate::yaml::EquipmentStatus::Healthy => "Healthy",
                    crate::yaml::EquipmentStatus::Warning => "Warning",
                    crate::yaml::EquipmentStatus::Critical => "Critical",
                    crate::yaml::EquipmentStatus::Unknown => "Unknown",
                };
                Ok(CellValue::Enum(status_str.to_string()))
            }
            _ => Ok(CellValue::Empty),
        }
    }
    
    fn set_cell(&mut self, row: usize, col: usize, value: CellValue) -> Result<(), Box<dyn std::error::Error>> {
        // Get column ID first before mutable borrow
        let column_id = {
            let columns = self.columns();
            columns.get(col)
                .ok_or_else(|| format!("Column {} out of bounds", col))?
                .id.clone()
        };
        
        let equipment = self.equipment.get_mut(row)
            .ok_or_else(|| format!("Row {} out of bounds", row))?;
        
        match column_id.as_str() {
            "equipment.name" => {
                if let CellValue::Text(name) = value {
                    equipment.name = name;
                    self.modified_rows.insert(row);
                }
            }
            "equipment.type" => {
                if let CellValue::Enum(type_str) = value {
                    equipment.equipment_type = type_str;
                    self.modified_rows.insert(row);
                }
            }
            "equipment.status" => {
                if let CellValue::Enum(status_str) = value {
                    let status = match status_str.as_str() {
                        "Healthy" => crate::yaml::EquipmentStatus::Healthy,
                        "Warning" => crate::yaml::EquipmentStatus::Warning,
                        "Critical" => crate::yaml::EquipmentStatus::Critical,
                        "Unknown" => crate::yaml::EquipmentStatus::Unknown,
                        _ => return Err(format!("Invalid status: {}", status_str).into()),
                    };
                    equipment.status = status;
                    self.modified_rows.insert(row);
                }
            }
            _ => {
                return Err("Column is read-only or invalid".into());
            }
        }
        
        Ok(())
    }
    
    fn save(&mut self, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
        use crate::persistence::PersistenceManager;
        
        // Update building data with modified equipment
        // Match equipment by ID to update the correct equipment in building_data
        let mut building_data = self.building_data.clone();
        let mut modified_count = 0;
        
        // Create a map of modified equipment by ID
        let modified_equipment: std::collections::HashMap<String, &EquipmentData> = self.equipment
            .iter()
            .enumerate()
            .filter(|(idx, _)| self.modified_rows.contains(idx))
            .map(|(_, eq)| (eq.id.clone(), eq))
            .collect();
        
        // Update equipment in building data by matching IDs
        for floor in building_data.floors.iter_mut() {
            for equipment in floor.equipment.iter_mut() {
                if let Some(modified_eq) = modified_equipment.get(&equipment.id) {
                    *equipment = (*modified_eq).clone();
                    modified_count += 1;
                }
            }
        }
        
        // Save via persistence manager
        let persistence = PersistenceManager::new(&self.building_name)?;
        persistence.save_building_data(&building_data)?;
        
        // Update our building_data reference
        self.building_data = building_data;
        
        // Stage to Git if repository exists
        if persistence.has_git_repo() {
            use crate::git::{BuildingGitManager, manager::GitConfigManager};
            
            let repo_path = persistence.working_file()
                .parent()
                .and_then(|p| p.to_str())
                .ok_or_else(|| "Invalid repository path".to_string())?;
            
            let config = GitConfigManager::load_from_arx_config_or_env();
            let mut git_manager = BuildingGitManager::new(repo_path, &self.building_name, config)
                .map_err(|e| format!("Git error: {}", e))?;
            
            git_manager.stage_all()?;
            
            // Commit if requested
            if commit {
                let message = format!("Update equipment via spreadsheet ({} items modified)", modified_count);
                git_manager.commit_staged(&message)?;
            }
        }
        
        // Clear modified rows after successful save
        self.modified_rows.clear();
        
        Ok(())
    }
    
    fn reload(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        use crate::persistence::PersistenceManager;
        
        // Reload building data
        let persistence = PersistenceManager::new(&self.building_name)?;
        let building_data = persistence.load_building_data()?;
        
        // Update internal data
        self.building_data = building_data.clone();
        
        // Rebuild equipment list
        let mut equipment = Vec::new();
        for floor in &self.building_data.floors {
            equipment.extend(floor.equipment.clone());
        }
        self.equipment = equipment;
        
        // Clear modified rows
        self.modified_rows.clear();
        
        Ok(())
    }
}

/// Room data source implementation
pub struct RoomDataSource {
    rooms: Vec<RoomData>,
    building_data: BuildingData,
    building_name: String,
    modified_rows: std::collections::HashSet<usize>,
}

impl RoomDataSource {
    /// Create a new room data source from building data
    pub fn new(building_data: BuildingData, building_name: String) -> Self {
        // Collect all rooms from all floors
        let mut rooms = Vec::new();
        for floor in &building_data.floors {
            rooms.extend(floor.rooms.clone());
        }
        
        Self {
            rooms,
            building_data,
            building_name,
            modified_rows: std::collections::HashSet::new(),
        }
    }
    
    /// Get room type enum values
    fn room_type_values() -> Vec<String> {
        vec![
            "Classroom".to_string(),
            "Laboratory".to_string(),
            "Office".to_string(),
            "Gymnasium".to_string(),
            "Cafeteria".to_string(),
            "Library".to_string(),
            "Auditorium".to_string(),
            "Hallway".to_string(),
            "Restroom".to_string(),
            "Storage".to_string(),
            "Mechanical".to_string(),
            "Electrical".to_string(),
        ]
    }
}

impl SpreadsheetDataSource for RoomDataSource {
    fn columns(&self) -> Vec<ColumnDefinition> {
        vec![
            ColumnDefinition {
                id: "room.id".to_string(),
                label: "ID".to_string(),
                data_type: CellType::UUID,
                editable: false,
                width: Some(36),
                validation: None,
                enum_values: None,
            },
            ColumnDefinition {
                id: "room.name".to_string(),
                label: "Name".to_string(),
                data_type: CellType::Text,
                editable: true,
                width: Some(30),
                validation: Some(ValidationRule::Required),
                enum_values: None,
            },
            ColumnDefinition {
                id: "room.type".to_string(),
                label: "Type".to_string(),
                data_type: CellType::Enum(Self::room_type_values()),
                editable: true,
                width: Some(15),
                validation: None,
                enum_values: Some(Self::room_type_values()),
            },
            ColumnDefinition {
                id: "room.area".to_string(),
                label: "Area".to_string(),
                data_type: CellType::Number,
                editable: true,
                width: Some(12),
                validation: Some(ValidationRule::MinValue(0.0)),
                enum_values: None,
            },
            ColumnDefinition {
                id: "room.volume".to_string(),
                label: "Volume".to_string(),
                data_type: CellType::Number,
                editable: true,
                width: Some(12),
                validation: Some(ValidationRule::MinValue(0.0)),
                enum_values: None,
            },
        ]
    }
    
    fn row_count(&self) -> usize {
        self.rooms.len()
    }
    
    fn get_cell(&self, row: usize, col: usize) -> Result<CellValue, Box<dyn std::error::Error>> {
        let room = self.rooms.get(row)
            .ok_or_else(|| format!("Row {} out of bounds", row))?;
        
        let columns = self.columns();
        let column = columns.get(col)
            .ok_or_else(|| format!("Column {} out of bounds", col))?;
        
        match column.id.as_str() {
            "room.id" => Ok(CellValue::UUID(room.id.clone())),
            "room.name" => Ok(CellValue::Text(room.name.clone())),
            "room.type" => Ok(CellValue::Enum(room.room_type.clone())),
            "room.area" => Ok(room.area.map(CellValue::Number).unwrap_or(CellValue::Empty)),
            "room.volume" => Ok(room.volume.map(CellValue::Number).unwrap_or(CellValue::Empty)),
            _ => Ok(CellValue::Empty),
        }
    }
    
    fn set_cell(&mut self, row: usize, col: usize, value: CellValue) -> Result<(), Box<dyn std::error::Error>> {
        // Get column ID first before mutable borrow
        let column_id = {
            let columns = self.columns();
            columns.get(col)
                .ok_or_else(|| format!("Column {} out of bounds", col))?
                .id.clone()
        };
        
        let room = self.rooms.get_mut(row)
            .ok_or_else(|| format!("Row {} out of bounds", row))?;
        
        match column_id.as_str() {
            "room.name" => {
                if let CellValue::Text(name) = value {
                    room.name = name;
                    self.modified_rows.insert(row);
                }
            }
            "room.type" => {
                if let CellValue::Enum(type_str) = value {
                    room.room_type = type_str;
                    self.modified_rows.insert(row);
                }
            }
            "room.area" => {
                if let CellValue::Number(area) = value {
                    room.area = Some(area);
                    self.modified_rows.insert(row);
                } else if matches!(value, CellValue::Empty) {
                    room.area = None;
                    self.modified_rows.insert(row);
                }
            }
            "room.volume" => {
                if let CellValue::Number(volume) = value {
                    room.volume = Some(volume);
                    self.modified_rows.insert(row);
                } else if matches!(value, CellValue::Empty) {
                    room.volume = None;
                    self.modified_rows.insert(row);
                }
            }
            _ => {
                return Err("Column is read-only or invalid".into());
            }
        }
        
        Ok(())
    }
    
    fn save(&mut self, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
        use crate::persistence::PersistenceManager;
        
        // Update building data with modified rooms
        let mut building_data = self.building_data.clone();
        let mut modified_count = 0;
        
        // Create a map of modified rooms by ID
        let modified_rooms: std::collections::HashMap<String, &RoomData> = self.rooms
            .iter()
            .enumerate()
            .filter(|(idx, _)| self.modified_rows.contains(idx))
            .map(|(_, room)| (room.id.clone(), room))
            .collect();
        
        // Update rooms in building data by matching IDs
        for floor in building_data.floors.iter_mut() {
            for room in floor.rooms.iter_mut() {
                if let Some(modified_room) = modified_rooms.get(&room.id) {
                    *room = (*modified_room).clone();
                    modified_count += 1;
                }
            }
        }
        
        // Save via persistence manager
        let persistence = PersistenceManager::new(&self.building_name)?;
        persistence.save_building_data(&building_data)?;
        
        // Update our building_data reference
        self.building_data = building_data;
        
        // Stage to Git if repository exists
        if persistence.has_git_repo() {
            use crate::git::{BuildingGitManager, manager::GitConfigManager};
            
            let repo_path = persistence.working_file()
                .parent()
                .and_then(|p| p.to_str())
                .ok_or_else(|| "Invalid repository path".to_string())?;
            
            let config = GitConfigManager::load_from_arx_config_or_env();
            let mut git_manager = BuildingGitManager::new(repo_path, &self.building_name, config)
                .map_err(|e| format!("Git error: {}", e))?;
            
            git_manager.stage_all()?;
            
            // Commit if requested
            if commit {
                let message = format!("Update rooms via spreadsheet ({} items modified)", modified_count);
                git_manager.commit_staged(&message)?;
            }
        }
        
        // Clear modified rows after successful save
        self.modified_rows.clear();
        
        Ok(())
    }
    
    fn reload(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        use crate::persistence::PersistenceManager;
        
        // Reload building data
        let persistence = PersistenceManager::new(&self.building_name)?;
        let building_data = persistence.load_building_data()?;
        
        // Update internal data
        self.building_data = building_data.clone();
        
        // Rebuild rooms list
        let mut rooms = Vec::new();
        for floor in &self.building_data.floors {
            rooms.extend(floor.rooms.clone());
        }
        self.rooms = rooms;
        
        // Clear modified rows
        self.modified_rows.clear();
        
        Ok(())
    }
}

/// Sensor data source implementation
/// Note: This is a simplified implementation. Full sensor data handling
/// would require time-series data management which is beyond the scope
/// of the basic spreadsheet interface.
pub struct SensorDataSource {
    sensor_data: Vec<SensorData>,
    building_name: String,
}

impl SensorDataSource {
    /// Create a new sensor data source
    /// In a real implementation, this would load sensor data from files or API
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
    pub fn load_sensor_data(&mut self) -> Result<(), Box<dyn std::error::Error>> {
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
    
    fn get_cell(&self, row: usize, col: usize) -> Result<CellValue, Box<dyn std::error::Error>> {
        let sensor = self.sensor_data.get(row)
            .ok_or_else(|| format!("Row {} out of bounds", row))?;
        
        let columns = self.columns();
        let column = columns.get(col)
            .ok_or_else(|| format!("Column {} out of bounds", col))?;
        
        match column.id.as_str() {
            "sensor.id" => Ok(CellValue::Text(sensor.metadata.sensor_id.clone())),
            "sensor.type" => Ok(CellValue::Text(sensor.metadata.sensor_type.clone())),
            "sensor.timestamp" => Ok(CellValue::Date(sensor.metadata.timestamp.clone())),
            "sensor.equipment_id" => {
                let eq_id = sensor.metadata.equipment_id.clone()
                    .unwrap_or_else(|| "".to_string());
                if eq_id.is_empty() {
                    Ok(CellValue::Empty)
                } else {
                    Ok(CellValue::UUID(eq_id))
                }
            }
            _ => Ok(CellValue::Empty),
        }
    }
    
    fn set_cell(&mut self, _row: usize, _col: usize, _value: CellValue) -> Result<(), Box<dyn std::error::Error>> {
        // Sensor data is read-only in spreadsheet view
        Err("Sensor data is read-only".into())
    }
    
    fn save(&mut self, _commit: bool) -> Result<(), Box<dyn std::error::Error>> {
        // Sensor data is read-only
        Ok(())
    }
    
    fn reload(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        self.load_sensor_data()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::yaml::{BuildingData, BuildingInfo, BuildingMetadata, FloorData, EquipmentData, RoomData, EquipmentStatus};
    use crate::spatial::{Point3D, BoundingBox3D};
    use chrono::Utc;
    use std::collections::HashMap;
    
    fn create_test_building_data() -> BuildingData {
        BuildingData {
            building: BuildingInfo {
                id: "test-building-1".to_string(),
                name: "Test Building".to_string(),
                description: Some("Test".to_string()),
                created_at: Utc::now(),
                updated_at: Utc::now(),
                version: "1.0".to_string(),
                global_bounding_box: None,
            },
            metadata: BuildingMetadata {
                source_file: None,
                parser_version: "1.0".to_string(),
                total_entities: 0,
                spatial_entities: 0,
                coordinate_system: "World".to_string(),
                units: "meters".to_string(),
                tags: vec![],
            },
            floors: vec![
                FloorData {
                    id: "floor-1".to_string(),
                    name: "Ground Floor".to_string(),
                    level: 0,
                    elevation: 0.0,
                    rooms: vec![
                        RoomData {
                            id: "room-1".to_string(),
                            name: "Room 1".to_string(),
                            room_type: "Office".to_string(),
                            area: Some(100.0),
                            volume: Some(300.0),
                            position: Point3D::new(0.0, 0.0, 0.0),
                            bounding_box: BoundingBox3D::new(
                                Point3D::new(0.0, 0.0, 0.0),
                                Point3D::new(10.0, 10.0, 3.0),
                            ),
                            equipment: vec![],
                            properties: HashMap::new(),
                        },
                    ],
                    equipment: vec![
                        EquipmentData {
                            id: "eq-1".to_string(),
                            name: "HVAC Unit 1".to_string(),
                            equipment_type: "HVAC".to_string(),
                            system_type: "HVAC".to_string(),
                            position: Point3D::new(5.0, 5.0, 0.0),
                            bounding_box: BoundingBox3D::new(
                                Point3D::new(4.0, 4.0, 0.0),
                                Point3D::new(6.0, 6.0, 2.0),
                            ),
                            status: EquipmentStatus::Healthy,
                            properties: HashMap::new(),
                            universal_path: "/building/floor-1/eq-1".to_string(),
                            sensor_mappings: None,
                        },
                        EquipmentData {
                            id: "eq-2".to_string(),
                            name: "Electrical Panel 1".to_string(),
                            equipment_type: "Electrical".to_string(),
                            system_type: "Electrical".to_string(),
                            position: Point3D::new(8.0, 8.0, 0.0),
                            bounding_box: BoundingBox3D::new(
                                Point3D::new(7.0, 7.0, 0.0),
                                Point3D::new(9.0, 9.0, 1.5),
                            ),
                            status: EquipmentStatus::Warning,
                            properties: HashMap::new(),
                            universal_path: "/building/floor-1/eq-2".to_string(),
                            sensor_mappings: None,
                        },
                    ],
                    bounding_box: None,
                },
            ],
            coordinate_systems: vec![],
        }
    }
    
    #[test]
    fn test_equipment_data_source_new() {
        let building_data = create_test_building_data();
        let data_source = EquipmentDataSource::new(building_data, "test_building".to_string());
        
        assert_eq!(data_source.row_count(), 2);
        assert_eq!(data_source.equipment.len(), 2);
    }
    
    #[test]
    fn test_equipment_data_source_columns() {
        let building_data = create_test_building_data();
        let data_source = EquipmentDataSource::new(building_data, "test_building".to_string());
        
        let columns = data_source.columns();
        assert!(!columns.is_empty());
        assert!(columns.iter().any(|c| c.id == "equipment.id"));
        assert!(columns.iter().any(|c| c.id == "equipment.name"));
        assert!(columns.iter().any(|c| c.id == "equipment.type"));
    }
    
    #[test]
    fn test_equipment_data_source_get_cell() {
        let building_data = create_test_building_data();
        let data_source = EquipmentDataSource::new(building_data, "test_building".to_string());
        
        // Test getting ID (column 0)
        let id = data_source.get_cell(0, 0).unwrap();
        assert_eq!(id, CellValue::UUID("eq-1".to_string()));
        
        // Test getting name (column 1)
        let name = data_source.get_cell(0, 1).unwrap();
        assert_eq!(name, CellValue::Text("HVAC Unit 1".to_string()));
        
        // Test getting type (column 2)
        let eq_type = data_source.get_cell(0, 2).unwrap();
        assert_eq!(eq_type, CellValue::Enum("HVAC".to_string()));
    }
    
    #[test]
    fn test_equipment_data_source_get_cell_out_of_bounds() {
        let building_data = create_test_building_data();
        let data_source = EquipmentDataSource::new(building_data, "test_building".to_string());
        
        // Test row out of bounds
        assert!(data_source.get_cell(100, 0).is_err());
        
        // Test column out of bounds
        assert!(data_source.get_cell(0, 100).is_err());
    }
    
    #[test]
    fn test_equipment_data_source_set_cell() {
        let building_data = create_test_building_data();
        let mut data_source = EquipmentDataSource::new(building_data, "test_building".to_string());
        
        // Set name (column 1)
        let new_name = CellValue::Text("Updated Name".to_string());
        data_source.set_cell(0, 1, new_name.clone()).unwrap();
        
        // Verify it was set
        let retrieved = data_source.get_cell(0, 1).unwrap();
        assert_eq!(retrieved, new_name);
        
        // Verify row was marked as modified
        assert!(data_source.modified_rows.contains(&0));
    }
    
    #[test]
    fn test_equipment_data_source_set_cell_read_only() {
        let building_data = create_test_building_data();
        let mut data_source = EquipmentDataSource::new(building_data, "test_building".to_string());
        
        // Try to set ID (column 0, read-only)
        let result = data_source.set_cell(0, 0, CellValue::Text("new-id".to_string()));
        assert!(result.is_err());
    }
    
    #[test]
    fn test_room_data_source_new() {
        let building_data = create_test_building_data();
        let data_source = RoomDataSource::new(building_data, "test_building".to_string());
        
        assert_eq!(data_source.row_count(), 1);
        assert_eq!(data_source.rooms.len(), 1);
    }
    
    #[test]
    fn test_room_data_source_columns() {
        let building_data = create_test_building_data();
        let data_source = RoomDataSource::new(building_data, "test_building".to_string());
        
        let columns = data_source.columns();
        assert!(!columns.is_empty());
        assert!(columns.iter().any(|c| c.id == "room.id"));
        assert!(columns.iter().any(|c| c.id == "room.name"));
        assert!(columns.iter().any(|c| c.id == "room.type"));
    }
    
    #[test]
    fn test_room_data_source_get_cell() {
        let building_data = create_test_building_data();
        let data_source = RoomDataSource::new(building_data, "test_building".to_string());
        
        // Test getting ID
        let id = data_source.get_cell(0, 0).unwrap();
        assert_eq!(id, CellValue::UUID("room-1".to_string()));
        
        // Test getting name
        let name = data_source.get_cell(0, 1).unwrap();
        assert_eq!(name, CellValue::Text("Room 1".to_string()));
        
        // Test getting type
        let room_type = data_source.get_cell(0, 2).unwrap();
        assert_eq!(room_type, CellValue::Enum("Office".to_string()));
    }
    
    #[test]
    fn test_room_data_source_set_cell() {
        let building_data = create_test_building_data();
        let mut data_source = RoomDataSource::new(building_data, "test_building".to_string());
        
        // Set name
        let new_name = CellValue::Text("Updated Room".to_string());
        data_source.set_cell(0, 1, new_name.clone()).unwrap();
        
        // Verify it was set
        let retrieved = data_source.get_cell(0, 1).unwrap();
        assert_eq!(retrieved, new_name);
        
        // Verify row was marked as modified
        assert!(data_source.modified_rows.contains(&0));
    }
    
    #[test]
    fn test_sensor_data_source_columns() {
        let data_source = SensorDataSource::new("test_building".to_string());
        
        let columns = data_source.columns();
        assert!(!columns.is_empty());
        assert!(columns.iter().any(|c| c.id == "sensor.id"));
        assert!(columns.iter().any(|c| c.id == "sensor.type"));
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
}


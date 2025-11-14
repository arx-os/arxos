//! Room data source implementation
//!
//! Provides spreadsheet interface for room data, including
//! viewing and editing room properties with Git integration.

use super::super::types::{CellType, CellValue, ColumnDefinition, ValidationRule};
use super::trait_def::SpreadsheetDataSource;
use crate::core::{Room, RoomType};
use crate::yaml::BuildingData;
use std::collections::{HashMap, HashSet};
use std::error::Error;

/// Room data source implementation
///
/// Manages room data from building YAML files and provides
/// spreadsheet-style access with:
/// - Column definitions for room properties
/// - Cell-level read/write operations
/// - Change tracking
/// - Git integration for saves
/// - Automatic area/volume calculations
pub struct RoomDataSource {
    rooms: Vec<Room>,
    building_data: BuildingData,
    building_name: String,
    modified_rows: HashSet<usize>,
}

impl RoomDataSource {
    /// Create a new room data source from building data
    ///
    /// Collects all rooms from all floors and wings in the building
    /// and creates a flattened view for spreadsheet display.
    ///
    /// # Arguments
    ///
    /// * `building_data` - The building data loaded from YAML
    /// * `building_name` - Name of the building for persistence
    pub fn new(building_data: BuildingData, building_name: String) -> Self {
        // Collect all rooms from all floors (rooms are now in wings)
        let mut rooms = Vec::new();
        for floor in &building_data.building.floors {
            for wing in &floor.wings {
                rooms.extend(wing.rooms.clone());
            }
        }

        Self {
            rooms,
            building_data,
            building_name,
            modified_rows: HashSet::new(),
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
                id: "room.address".to_string(),
                label: "Address".to_string(),
                data_type: CellType::Text,
                editable: false,
                width: Some(50),
                validation: None,
                enum_values: None,
            },
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

    fn get_cell(&self, row: usize, col: usize) -> Result<CellValue, Box<dyn Error>> {
        let room = self
            .rooms
            .get(row)
            .ok_or_else(|| format!("Row {} out of bounds", row))?;

        let columns = self.columns();
        let column = columns
            .get(col)
            .ok_or_else(|| format!("Column {} out of bounds", col))?;

        match column.id.as_str() {
            "room.address" => {
                // RoomData doesn't have address field yet, so show "No address"
                Ok(CellValue::Text("No address".to_string()))
            }
            "room.id" => Ok(CellValue::UUID(room.id.clone())),
            "room.name" => Ok(CellValue::Text(room.name.clone())),
            "room.type" => Ok(CellValue::Enum(format!("{:?}", room.room_type))),
            "room.area" => {
                // Calculate area from dimensions
                let area = room.spatial_properties.dimensions.width
                    * room.spatial_properties.dimensions.depth;
                Ok(CellValue::Number(area))
            }
            "room.volume" => {
                // Calculate volume from dimensions
                let volume = room.spatial_properties.dimensions.width
                    * room.spatial_properties.dimensions.depth
                    * room.spatial_properties.dimensions.height;
                Ok(CellValue::Number(volume))
            }
            _ => Ok(CellValue::Empty),
        }
    }

    fn set_cell(
        &mut self,
        row: usize,
        col: usize,
        value: CellValue,
    ) -> Result<(), Box<dyn Error>> {
        // Get column ID first before mutable borrow
        let column_id = {
            let columns = self.columns();
            columns
                .get(col)
                .ok_or_else(|| format!("Column {} out of bounds", col))?
                .id
                .clone()
        };

        let room = self
            .rooms
            .get_mut(row)
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
                    // Parse room type string to enum
                    room.room_type = match type_str.as_str() {
                        "Classroom" => RoomType::Classroom,
                        "Laboratory" => RoomType::Laboratory,
                        "Office" => RoomType::Office,
                        "Gymnasium" => RoomType::Gymnasium,
                        "Cafeteria" => RoomType::Cafeteria,
                        "Library" => RoomType::Library,
                        "Auditorium" => RoomType::Auditorium,
                        "Hallway" => RoomType::Hallway,
                        "Restroom" => RoomType::Restroom,
                        "Storage" => RoomType::Storage,
                        "Mechanical" => RoomType::Mechanical,
                        "Electrical" => RoomType::Electrical,
                        _ => RoomType::Other(type_str),
                    };
                    self.modified_rows.insert(row);
                }
            }
            "room.area" => {
                if let CellValue::Number(area) = value {
                    // Update dimensions to reflect new area (preserve height, adjust width/depth proportionally)
                    let current_area = room.spatial_properties.dimensions.width
                        * room.spatial_properties.dimensions.depth;
                    if current_area > 0.0 {
                        let scale = (area / current_area).sqrt();
                        room.spatial_properties.dimensions.width *= scale;
                        room.spatial_properties.dimensions.depth *= scale;
                    } else {
                        // If no current area, set default dimensions
                        let side = area.sqrt();
                        room.spatial_properties.dimensions.width = side;
                        room.spatial_properties.dimensions.depth = side;
                    }
                    self.modified_rows.insert(row);
                }
            }
            "room.volume" => {
                if let CellValue::Number(volume) = value {
                    // Update height to reflect new volume (preserve area)
                    let area = room.spatial_properties.dimensions.width
                        * room.spatial_properties.dimensions.depth;
                    if area > 0.0 {
                        room.spatial_properties.dimensions.height = volume / area;
                    } else {
                        // If no area, set default dimensions
                        let side = volume.cbrt();
                        room.spatial_properties.dimensions.width = side;
                        room.spatial_properties.dimensions.depth = side;
                        room.spatial_properties.dimensions.height = side;
                    }
                    self.modified_rows.insert(row);
                }
            }
            _ => {
                return Err("Column is read-only or invalid".into());
            }
        }

        Ok(())
    }

    fn save(&mut self, commit: bool) -> Result<(), Box<dyn Error>> {
        use crate::persistence::PersistenceManager;

        // Update building data with modified rooms
        let mut building_data = self.building_data.clone();
        let mut modified_count = 0;

        // Create a map of modified rooms by ID
        let modified_rooms: HashMap<String, &Room> = self
            .rooms
            .iter()
            .enumerate()
            .filter(|(idx, _)| self.modified_rows.contains(idx))
            .map(|(_, room)| (room.id.clone(), room))
            .collect();

        // Update rooms in building data by matching IDs (rooms are now in wings)
        for floor in building_data.building.floors.iter_mut() {
            for wing in floor.wings.iter_mut() {
                for room in wing.rooms.iter_mut() {
                    if let Some(modified_room) = modified_rooms.get(&room.id) {
                        *room = (*modified_room).clone();
                        modified_count += 1;
                    }
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
            use crate::git::{manager::GitConfigManager, BuildingGitManager};

            let working_file_path = persistence.working_file();
            let repo_path = working_file_path
                .parent()
                .and_then(|p| p.to_str())
                .ok_or_else(|| "Invalid repository path".to_string())?;

            let config = GitConfigManager::load_from_arx_config_or_env();
            let mut git_manager = BuildingGitManager::new(repo_path, &self.building_name, config)
                .map_err(|e| format!("Git error: {}", e))?;

            git_manager.stage_all()?;

            // Commit if requested
            if commit {
                let message = format!(
                    "Update rooms via spreadsheet ({} items modified)",
                    modified_count
                );
                git_manager.commit_staged(&message)?;
            }
        }

        // Clear modified rows after successful save
        self.modified_rows.clear();

        Ok(())
    }

    fn reload(&mut self) -> Result<(), Box<dyn Error>> {
        use crate::persistence::PersistenceManager;

        // Reload building data
        let persistence = PersistenceManager::new(&self.building_name)?;
        let building_data = persistence.load_building_data()?;

        // Update internal data
        self.building_data = building_data.clone();

        // Rebuild rooms list (rooms are now in wings)
        let mut rooms = Vec::new();
        for floor in &self.building_data.building.floors {
            for wing in &floor.wings {
                rooms.extend(wing.rooms.clone());
            }
        }
        self.rooms = rooms;

        // Clear modified rows
        self.modified_rows.clear();

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_room_type_values() {
        let values = RoomDataSource::room_type_values();
        assert!(values.contains(&"Classroom".to_string()));
        assert!(values.contains(&"Laboratory".to_string()));
        assert_eq!(values.len(), 12);
    }
}

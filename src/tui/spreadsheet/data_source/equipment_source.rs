//! Equipment data source implementation
//!
//! Provides spreadsheet interface for equipment data, including
//! viewing and editing equipment properties with Git integration.

use super::super::types::{CellType, CellValue, ColumnDefinition, ValidationRule};
use super::trait_def::SpreadsheetDataSource;
use crate::core::{Equipment, EquipmentHealthStatus, EquipmentStatus, EquipmentType};
use crate::yaml::BuildingData;
use std::collections::{HashMap, HashSet};
use std::error::Error;

/// Equipment data source implementation
///
/// Manages equipment data from building YAML files and provides
/// spreadsheet-style access with:
/// - Column definitions for equipment properties
/// - Cell-level read/write operations
/// - Change tracking
/// - Git integration for saves
pub struct EquipmentDataSource {
    equipment: Vec<Equipment>,
    building_data: BuildingData,
    building_name: String,
    modified_rows: HashSet<usize>,
}

impl EquipmentDataSource {
    /// Create a new equipment data source from building data
    ///
    /// Collects all equipment from all floors in the building and
    /// creates a flattened view for spreadsheet display.
    ///
    /// # Arguments
    ///
    /// * `building_data` - The building data loaded from YAML
    /// * `building_name` - Name of the building for persistence
    pub fn new(building_data: BuildingData, building_name: String) -> Self {
        // Collect all equipment from all floors
        let mut equipment = Vec::new();
        for floor in &building_data.building.floors {
            equipment.extend(floor.equipment.clone());
        }

        Self {
            equipment,
            building_data,
            building_name,
            modified_rows: HashSet::new(),
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
                id: "equipment.address".to_string(),
                label: "Address".to_string(),
                data_type: CellType::Text,
                editable: false,
                width: Some(50),
                validation: None,
                enum_values: None,
            },
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

    fn get_cell(&self, row: usize, col: usize) -> Result<CellValue, Box<dyn Error>> {
        let equipment = self
            .equipment
            .get(row)
            .ok_or_else(|| format!("Row {} out of bounds", row))?;

        let columns = self.columns();
        let column = columns
            .get(col)
            .ok_or_else(|| format!("Column {} out of bounds", col))?;

        match column.id.as_str() {
            "equipment.address" => {
                if let Some(ref addr) = equipment.address {
                    Ok(CellValue::Text(addr.path.clone()))
                } else {
                    Ok(CellValue::Text("No address".to_string()))
                }
            }
            "equipment.id" => Ok(CellValue::UUID(equipment.id.clone())),
            "equipment.name" => Ok(CellValue::Text(equipment.name.clone())),
            "equipment.type" => Ok(CellValue::Enum(format!("{:?}", equipment.equipment_type))),
            "equipment.status" => {
                // Use health_status if available, otherwise use status
                let status_str = if let Some(health_status) = &equipment.health_status {
                    match health_status {
                        EquipmentHealthStatus::Healthy => "Healthy",
                        EquipmentHealthStatus::Warning => "Warning",
                        EquipmentHealthStatus::Critical => "Critical",
                        EquipmentHealthStatus::Unknown => "Unknown",
                    }
                } else {
                    match equipment.status {
                        EquipmentStatus::Active => "Active",
                        EquipmentStatus::Inactive => "Inactive",
                        EquipmentStatus::Maintenance => "Maintenance",
                        EquipmentStatus::OutOfOrder => "OutOfOrder",
                        EquipmentStatus::Unknown => "Unknown",
                    }
                };
                Ok(CellValue::Enum(status_str.to_string()))
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

        let equipment = self
            .equipment
            .get_mut(row)
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
                    equipment.equipment_type = match type_str.as_str() {
                        "HVAC" => EquipmentType::HVAC,
                        "Electrical" => EquipmentType::Electrical,
                        "AV" => EquipmentType::AV,
                        "Furniture" => EquipmentType::Furniture,
                        "Safety" => EquipmentType::Safety,
                        "Plumbing" => EquipmentType::Plumbing,
                        "Network" => EquipmentType::Network,
                        _ => EquipmentType::Other(type_str),
                    };
                    self.modified_rows.insert(row);
                }
            }
            "equipment.status" => {
                if let CellValue::Enum(status_str) = value {
                    // Update health_status if it's a health status, otherwise update status
                    match status_str.as_str() {
                        "Healthy" | "Warning" | "Critical" | "Unknown" => {
                            let health_status = match status_str.as_str() {
                                "Healthy" => EquipmentHealthStatus::Healthy,
                                "Warning" => EquipmentHealthStatus::Warning,
                                "Critical" => EquipmentHealthStatus::Critical,
                                "Unknown" => EquipmentHealthStatus::Unknown,
                                _ => unreachable!(),
                            };
                            equipment.health_status = Some(health_status);
                        }
                        "Active" | "Inactive" | "Maintenance" | "OutOfOrder" => {
                            let status = match status_str.as_str() {
                                "Active" => EquipmentStatus::Active,
                                "Inactive" => EquipmentStatus::Inactive,
                                "Maintenance" => EquipmentStatus::Maintenance,
                                "OutOfOrder" => EquipmentStatus::OutOfOrder,
                                _ => unreachable!(),
                            };
                            equipment.status = status;
                        }
                        _ => return Err(format!("Invalid status: {}", status_str).into()),
                    };
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

        // Update building data with modified equipment
        // Match equipment by ID to update the correct equipment in building_data
        let mut building_data = self.building_data.clone();
        let mut modified_count = 0;

        // Create a map of modified equipment by ID
        let modified_equipment: HashMap<String, &Equipment> = self
            .equipment
            .iter()
            .enumerate()
            .filter(|(idx, _)| self.modified_rows.contains(idx))
            .map(|(_, eq)| (eq.id.clone(), eq))
            .collect();

        // Update equipment in building data by matching IDs
        for floor in building_data.building.floors.iter_mut() {
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
                    "Update equipment via spreadsheet ({} items modified)",
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

        // Rebuild equipment list
        let mut equipment = Vec::new();
        for floor in &self.building_data.building.floors {
            equipment.extend(floor.equipment.clone());
        }
        self.equipment = equipment;

        // Clear modified rows
        self.modified_rows.clear();

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_equipment_type_values() {
        let values = EquipmentDataSource::equipment_type_values();
        assert!(values.contains(&"HVAC".to_string()));
        assert!(values.contains(&"Electrical".to_string()));
        assert_eq!(values.len(), 7);
    }

    #[test]
    fn test_equipment_status_values() {
        let values = EquipmentDataSource::equipment_status_values();
        assert!(values.contains(&"Active".to_string()));
        assert!(values.contains(&"Maintenance".to_string()));
        assert_eq!(values.len(), 5);
    }
}

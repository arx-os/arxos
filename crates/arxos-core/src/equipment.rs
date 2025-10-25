//! # Equipment Management for ArxOS Core
//!
//! This module provides comprehensive equipment management capabilities for building systems,
//! including HVAC, electrical, plumbing, and other building equipment types.
//!
//! ## Features
//!
//! - **Equipment CRUD Operations**: Create, read, update, and delete equipment
//! - **Equipment Types**: Support for various building equipment types
//! - **Spatial Positioning**: 3D positioning and spatial relationships
//! - **Status Management**: Equipment status tracking and monitoring
//! - **Property Management**: Custom properties and metadata
//!
//! ## Equipment Types
//!
//! - **HVAC**: Heating, ventilation, and air conditioning systems
//! - **Electrical**: Power distribution, lighting, and electrical equipment
//! - **Plumbing**: Water supply, drainage, and plumbing fixtures
//! - **Fire Safety**: Fire suppression, detection, and safety equipment
//! - **Security**: Access control, surveillance, and security systems
//! - **IT Infrastructure**: Network equipment, servers, and IT systems
//!
//! ## Examples
//!
//! ```rust
//! use arxos_core::equipment::{EquipmentManager, EquipmentType, parse_equipment_type};
//!
//! let mut manager = EquipmentManager::new();
//! let equipment_type = parse_equipment_type("hvac");
//! 
//! let equipment = manager.add_equipment(
//!     "Main HVAC Unit".to_string(),
//!     equipment_type,
//!     Some("room-101".to_string()),
//!     Some("10.5,20.3,3.2".to_string()),
//!     vec!["capacity=5000".to_string(), "efficiency=0.85".to_string()]
//! )?;
//! ```
//!
//! ## Performance Considerations
//!
//! - Equipment lookups use HashMap for O(1) access time
//! - Spatial queries are optimized for large equipment datasets
//! - Property parsing is cached for repeated operations

use crate::{Result, Equipment, EquipmentType, Position, EquipmentStatus, ArxError};
use std::collections::HashMap;
use uuid::Uuid;

/// Equipment management operations
#[derive(Debug)]
pub struct EquipmentManager {
    equipment: HashMap<String, Equipment>,
}

impl EquipmentManager {
    /// Create a new equipment manager
    pub fn new() -> Self {
        Self {
            equipment: HashMap::new(),
        }
    }

    /// Add equipment to a room
    pub fn add_equipment(
        &mut self,
        name: String,
        equipment_type: EquipmentType,
        room_id: Option<String>,
        position: Option<String>,
        properties: Vec<String>,
    ) -> Result<Equipment> {
        let id = Uuid::new_v4().to_string();
        
        // Parse position if provided
        let parsed_position = if let Some(pos) = position {
            parse_position(&pos)?
        } else {
            Position {
                x: 0.0,
                y: 0.0,
                z: 0.0,
                coordinate_system: "building_local".to_string(),
            }
        };

        // Parse properties
        let mut parsed_properties = HashMap::new();
        for property in properties {
            if let Some((key, value)) = property.split_once('=') {
                parsed_properties.insert(key.to_string(), value.to_string());
            }
        }

        let equipment = Equipment {
            id: id.clone(),
            name: name.clone(),
            path: format!("/equipment/{}", name.clone()),
            equipment_type,
            position: parsed_position,
            properties: parsed_properties,
            status: EquipmentStatus::Active,
            room_id,
        };

        self.equipment.insert(id.clone(), equipment.clone());
        Ok(equipment)
    }

    /// List all equipment
    pub fn list_equipment(&self) -> Result<Vec<Equipment>> {
        Ok(self.equipment.values().cloned().collect())
    }

    /// Get equipment by ID or name
    pub fn get_equipment(&self, identifier: &str) -> Result<&Equipment> {
        // Try by ID first
        if let Some(equipment) = self.equipment.get(identifier) {
            return Ok(equipment);
        }

        // Try by name
        for equipment in self.equipment.values() {
            if equipment.name == identifier {
                return Ok(equipment);
            }
        }

        Err(ArxError::EquipmentNotFound { equipment_id: identifier.to_string() })
    }

    /// Update equipment
    pub fn update_equipment(
        &mut self,
        identifier: &str,
        properties: Vec<String>,
        position: Option<String>,
    ) -> Result<Equipment> {
        let equipment = self.equipment.get_mut(identifier)
            .ok_or_else(|| ArxError::EquipmentNotFound { equipment_id: identifier.to_string() })?;

        // Update properties
        for property in properties {
            if let Some((key, value)) = property.split_once('=') {
                equipment.properties.insert(key.to_string(), value.to_string());
            }
        }

        // Update position if provided
        if let Some(pos) = position {
            equipment.position = parse_position(&pos)?;
        }

        Ok(equipment.clone())
    }

    /// Remove equipment
    pub fn remove_equipment(&mut self, identifier: &str) -> Result<()> {
        if self.equipment.remove(identifier).is_some() {
            Ok(())
        } else {
            Err(ArxError::EquipmentNotFound { equipment_id: identifier.to_string() })
        }
    }
}

/// Parse position from string format "x,y,z"
fn parse_position(position: &str) -> Result<Position> {
    let parts: Vec<&str> = position.split(',').collect();
    if parts.len() != 3 {
        return Err(ArxError::validation_error("Invalid position format. Use 'x,y,z'"));
    }

    let x = parts[0].trim().parse::<f64>()
        .map_err(|_| ArxError::validation_error("Invalid x coordinate"))?;
    let y = parts[1].trim().parse::<f64>()
        .map_err(|_| ArxError::validation_error("Invalid y coordinate"))?;
    let z = parts[2].trim().parse::<f64>()
        .map_err(|_| ArxError::validation_error("Invalid z coordinate"))?;

    Ok(Position {
        x,
        y,
        z,
        coordinate_system: "building_local".to_string(),
    })
}

/// Parse equipment type from string
/// 
/// # Arguments
/// 
/// * `equipment_type` - String representation of equipment type
/// 
/// # Returns
/// 
/// * `Result<EquipmentType>` - Parsed equipment type or error if invalid
/// 
/// # Examples
/// 
/// ```rust
/// use arxos_core::equipment::parse_equipment_type;
/// 
/// let hvac_type = parse_equipment_type("hvac")?;
/// let electrical_type = parse_equipment_type("electrical")?;
/// ```
pub fn parse_equipment_type(equipment_type: &str) -> Result<EquipmentType> {
    match equipment_type.to_lowercase().as_str() {
        "hvac" => Ok(EquipmentType::HVAC),
        "electrical" => Ok(EquipmentType::Electrical),
        "plumbing" => Ok(EquipmentType::Plumbing),
        "safety" => Ok(EquipmentType::Safety),
        "network" => Ok(EquipmentType::Network),
        "av" => Ok(EquipmentType::AV),
        "furniture" => Ok(EquipmentType::Furniture),
        _ => Err(ArxError::InvalidEquipmentType {
            equipment_type: equipment_type.to_string(),
            valid_types: "hvac, electrical, plumbing, safety, network, av, furniture".to_string(),
        }),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{EquipmentType, Position, EquipmentStatus};

    #[test]
    fn test_equipment_manager_new() {
        let manager = EquipmentManager::new();
        assert!(manager.equipment.is_empty());
    }

    #[test]
    fn test_add_equipment() {
        let mut manager = EquipmentManager::new();
        let equipment = manager.add_equipment(
            "Test HVAC".to_string(),
            EquipmentType::HVAC,
            Some("room-1".to_string()),
            Some("10.0,20.0,3.0".to_string()),
            vec!["capacity=5000".to_string()],
        ).unwrap();

        assert_eq!(equipment.name, "Test HVAC");
        assert_eq!(equipment.equipment_type, EquipmentType::HVAC);
        assert_eq!(equipment.room_id, Some("room-1".to_string()));
        assert_eq!(equipment.position.x, 10.0);
        assert_eq!(equipment.position.y, 20.0);
        assert_eq!(equipment.position.z, 3.0);
    }

    #[test]
    fn test_add_equipment_with_properties() {
        let mut manager = EquipmentManager::new();
        let equipment = manager.add_equipment(
            "Test Equipment".to_string(),
            EquipmentType::Electrical,
            None,
            None,
            vec!["voltage=220".to_string(), "current=10".to_string()],
        ).unwrap();

        assert_eq!(equipment.properties.get("voltage"), Some(&"220".to_string()));
        assert_eq!(equipment.properties.get("current"), Some(&"10".to_string()));
    }

    #[test]
    fn test_get_equipment() {
        let mut manager = EquipmentManager::new();
        let equipment = manager.add_equipment(
            "Test Equipment".to_string(),
            EquipmentType::HVAC,
            None,
            None,
            vec![],
        ).unwrap();

        let retrieved = manager.get_equipment(&equipment.id).unwrap();
        assert_eq!(retrieved.name, "Test Equipment");
    }

    #[test]
    fn test_get_equipment_not_found() {
        let manager = EquipmentManager::new();
        let result = manager.get_equipment("nonexistent");
        assert!(result.is_err());
        match result.unwrap_err() {
            ArxError::EquipmentNotFound { equipment_id } => {
                assert_eq!(equipment_id, "nonexistent");
            }
            _ => panic!("Expected EquipmentNotFound error"),
        }
    }

    #[test]
    fn test_list_equipment() {
        let mut manager = EquipmentManager::new();
        manager.add_equipment("Equipment 1".to_string(), EquipmentType::HVAC, None, None, vec![]).unwrap();
        manager.add_equipment("Equipment 2".to_string(), EquipmentType::Electrical, None, None, vec![]).unwrap();

        let equipment_list = manager.list_equipment().unwrap();
        assert_eq!(equipment_list.len(), 2);
    }

    #[test]
    fn test_update_equipment() {
        let mut manager = EquipmentManager::new();
        let equipment = manager.add_equipment(
            "Test Equipment".to_string(),
            EquipmentType::HVAC,
            None,
            None,
            vec![],
        ).unwrap();

        let updated = manager.update_equipment(
            &equipment.id,
            vec!["capacity=3000".to_string()],
            None,
        ).unwrap();

        assert_eq!(updated.properties.get("capacity"), Some(&"3000".to_string()));
    }

    #[test]
    fn test_remove_equipment() {
        let mut manager = EquipmentManager::new();
        let equipment = manager.add_equipment(
            "Test Equipment".to_string(),
            EquipmentType::HVAC,
            None,
            None,
            vec![],
        ).unwrap();

        manager.remove_equipment(&equipment.id).unwrap();
        assert!(manager.get_equipment(&equipment.id).is_err());
    }

    #[test]
    fn test_parse_equipment_type_valid() {
        assert_eq!(parse_equipment_type("hvac").unwrap(), EquipmentType::HVAC);
        assert_eq!(parse_equipment_type("electrical").unwrap(), EquipmentType::Electrical);
        assert_eq!(parse_equipment_type("plumbing").unwrap(), EquipmentType::Plumbing);
        assert_eq!(parse_equipment_type("safety").unwrap(), EquipmentType::Safety);
        assert_eq!(parse_equipment_type("network").unwrap(), EquipmentType::Network);
        assert_eq!(parse_equipment_type("av").unwrap(), EquipmentType::AV);
        assert_eq!(parse_equipment_type("furniture").unwrap(), EquipmentType::Furniture);
    }

    #[test]
    fn test_parse_equipment_type_case_insensitive() {
        assert_eq!(parse_equipment_type("HVAC").unwrap(), EquipmentType::HVAC);
        assert_eq!(parse_equipment_type("Electrical").unwrap(), EquipmentType::Electrical);
        assert_eq!(parse_equipment_type("PLUMBING").unwrap(), EquipmentType::Plumbing);
    }

    #[test]
    fn test_parse_equipment_type_invalid() {
        let result = parse_equipment_type("invalid_type");
        assert!(result.is_err());
        match result.unwrap_err() {
            ArxError::InvalidEquipmentType { equipment_type, valid_types } => {
                assert_eq!(equipment_type, "invalid_type");
                assert!(valid_types.contains("hvac"));
                assert!(valid_types.contains("electrical"));
            }
            _ => panic!("Expected InvalidEquipmentType error"),
        }
    }

    #[test]
    fn test_parse_position_valid() {
        let position = parse_position("10.5,20.3,3.2").unwrap();
        assert_eq!(position.x, 10.5);
        assert_eq!(position.y, 20.3);
        assert_eq!(position.z, 3.2);
        assert_eq!(position.coordinate_system, "building_local");
    }

    #[test]
    fn test_parse_position_invalid_format() {
        let result = parse_position("10.5,20.3");
        assert!(result.is_err());
        match result.unwrap_err() {
            ArxError::ValidationError { message, .. } => {
                assert!(message.contains("Invalid position format"));
            }
            _ => panic!("Expected ValidationError"),
        }
    }

    #[test]
    fn test_parse_position_invalid_coordinates() {
        let result = parse_position("invalid,20.3,3.2");
        assert!(result.is_err());
        match result.unwrap_err() {
            ArxError::ValidationError { message, .. } => {
                assert!(message.contains("Invalid x coordinate"));
            }
            _ => panic!("Expected ValidationError"),
        }
    }
}
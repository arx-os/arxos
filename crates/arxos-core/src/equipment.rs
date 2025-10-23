//! Equipment management for ArxOS Core

use crate::{Result, Equipment, EquipmentType, Position, EquipmentStatus, ArxError};
use std::collections::HashMap;
use uuid::Uuid;

/// Equipment management operations
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

        Err(ArxError::Unknown(format!("Equipment not found: {}", identifier)))
    }

    /// Update equipment
    pub fn update_equipment(
        &mut self,
        identifier: &str,
        properties: Vec<String>,
        position: Option<String>,
    ) -> Result<Equipment> {
        let equipment = self.equipment.get_mut(identifier)
            .ok_or_else(|| ArxError::Unknown(format!("Equipment not found: {}", identifier)))?;

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
            Err(ArxError::Unknown(format!("Equipment not found: {}", identifier)))
        }
    }
}

/// Parse position from string format "x,y,z"
fn parse_position(position: &str) -> Result<Position> {
    let parts: Vec<&str> = position.split(',').collect();
    if parts.len() != 3 {
        return Err(ArxError::Validation("Invalid position format. Use 'x,y,z'".to_string()));
    }

    let x = parts[0].trim().parse::<f64>()
        .map_err(|_| ArxError::Validation("Invalid x coordinate".to_string()))?;
    let y = parts[1].trim().parse::<f64>()
        .map_err(|_| ArxError::Validation("Invalid y coordinate".to_string()))?;
    let z = parts[2].trim().parse::<f64>()
        .map_err(|_| ArxError::Validation("Invalid z coordinate".to_string()))?;

    Ok(Position {
        x,
        y,
        z,
        coordinate_system: "building_local".to_string(),
    })
}

/// Parse equipment type from string
pub fn parse_equipment_type(equipment_type: &str) -> EquipmentType {
    match equipment_type.to_lowercase().as_str() {
        "hvac" => EquipmentType::HVAC,
        "electrical" => EquipmentType::Electrical,
        "plumbing" => EquipmentType::Plumbing,
        "safety" => EquipmentType::Safety,
        "network" => EquipmentType::Network,
        "av" => EquipmentType::AV,
        "furniture" => EquipmentType::Furniture,
        _ => EquipmentType::Other(equipment_type.to_string()),
    }
}
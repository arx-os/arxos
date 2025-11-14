//! Helper methods for IFC entity classification and extraction
//!
//! Utility methods for identifying entity types and extracting properties
//! from IFC entities during hierarchy building.

use crate::core::{EquipmentType, RoomType};
use super::types::IFCEntity;
use std::error::Error;

/// Check if entity is a storey (floor)
///
/// Returns true for IFC entities representing building floors/levels.
///
/// # Supported Types
///
/// - IFCBUILDINGSTOREY
/// - IFCBUILDINGFLOOR
/// - IFCLEVEL
pub fn is_storey_entity(entity_type: &str) -> bool {
    matches!(
        entity_type.to_uppercase().as_str(),
        "IFCBUILDINGSTOREY" | "IFCBUILDINGFLOOR" | "IFCLEVEL"
    )
}

/// Check if entity is a space (room)
///
/// Returns true for IFC entities representing rooms/spaces.
///
/// # Supported Types
///
/// - IFCSPACE
/// - IFCROOM
/// - IFCZONE
pub fn is_space_entity(entity_type: &str) -> bool {
    matches!(
        entity_type.to_uppercase().as_str(),
        "IFCSPACE" | "IFCROOM" | "IFCZONE"
    )
}

/// Check if entity is equipment (excludes TYPE definitions)
///
/// Returns true for IFC entities representing equipment/fixtures.
/// TYPE definitions (e.g., IFCFANTYPE) are explicitly excluded.
///
/// # Supported Types
///
/// - IFCFLOWTERMINAL
/// - IFCAIRTERMINAL
/// - IFCLIGHTFIXTURE
/// - IFCDISTRIBUTIONELEMENT
/// - IFCFAN
/// - IFCPUMP
pub fn is_equipment_entity(entity_type: &str) -> bool {
    let entity_upper = entity_type.to_uppercase();

    // Exclude TYPE definitions
    if entity_upper.contains("TYPE") {
        return false;
    }

    matches!(
        entity_upper.as_str(),
        "IFCFLOWTERMINAL"
            | "IFCAIRTERMINAL"
            | "IFCLIGHTFIXTURE"
            | "IFCDISTRIBUTIONELEMENT"
            | "IFCFAN"
            | "IFCPUMP"
    )
}

/// Extract storey name from IFC entity
///
/// Returns the entity's name if available, otherwise generates a fallback.
pub fn extract_storey_name(storey: &IFCEntity) -> Result<String, Box<dyn Error>> {
    if !storey.name.is_empty() && storey.name != "Unknown" {
        Ok(storey.name.clone())
    } else {
        Ok(format!("Floor-{}", storey.id))
    }
}

/// Extract storey level from IFC entity
///
/// Attempts to parse the floor level from the entity name.
/// Handles common naming patterns like "First Floor", "Floor 2", "Ground Floor".
///
/// # Fallback
///
/// Returns 1 (first floor) if no level can be determined.
pub fn extract_storey_level(storey: &IFCEntity) -> Result<i32, Box<dyn Error>> {
    // Try to parse level from storey name (e.g., "First Floor" -> 1, "Floor 2" -> 2)
    let name_lower = storey.name.to_lowercase();

    if name_lower.contains("first") || name_lower.contains("1") || name_lower.contains("ground") {
        Ok(1)
    } else if name_lower.contains("second") || name_lower.contains("2") {
        Ok(2)
    } else if name_lower.contains("third") || name_lower.contains("3") {
        Ok(3)
    } else {
        // Extract any number from the name
        let numbers: Vec<i32> = storey
            .name
            .chars()
            .filter(|c| c.is_ascii_digit())
            .filter_map(|c| c.to_digit(10).map(|d| d as i32))
            .collect();

        if !numbers.is_empty() {
            Ok(numbers[0])
        } else {
            Ok(1) // Default to first floor
        }
    }
}

/// Extract space name from IFC entity
///
/// Returns the entity's name if available, otherwise generates a fallback.
pub fn extract_space_name(space: &IFCEntity) -> Result<String, Box<dyn Error>> {
    if !space.name.is_empty() && space.name != "Unknown" {
        Ok(space.name.clone())
    } else {
        Ok(format!("Space-{}", space.id))
    }
}

/// Extract space type from IFC entity
///
/// Currently defaults to Office type. Can be enhanced to parse actual
/// room type from IFC properties when that information is available.
///
/// # Note
///
/// This is a reasonable default as most building spaces are office-type.
/// Future enhancement could parse IFCSPACE ObjectType or PredefinedType.
pub fn extract_space_type(_space: &IFCEntity) -> Result<RoomType, Box<dyn Error>> {
    // Currently defaults to Office - can be enhanced to parse actual room type from IFC properties
    Ok(RoomType::Office)
}

/// Map IFC equipment type to ArxOS EquipmentType
///
/// Converts IFC entity types to ArxOS equipment classifications.
///
/// # Mapping
///
/// - HVAC: IFCFLOWTERMINAL, IFCAIRTERMINAL, IFCFAN, IFCPUMP
/// - Electrical: IFCLIGHTFIXTURE, IFCDISTRIBUTIONELEMENT, IFCSWITCHINGDEVICE
/// - Safety: IFCFIREALARM, IFCFIREDETECTOR
/// - Plumbing: IFCPIPE, IFCPIPEFITTING, IFCTANK
/// - Other: Any unrecognized type
pub fn extract_equipment_type(ifc_entity_type: &str) -> Result<EquipmentType, Box<dyn Error>> {
    match ifc_entity_type.to_uppercase().as_str() {
        "IFCFLOWTERMINAL" | "IFCAIRTERMINAL" | "IFCFAN" | "IFCPUMP" => Ok(EquipmentType::HVAC),
        "IFCLIGHTFIXTURE" | "IFCDISTRIBUTIONELEMENT" | "IFCSWITCHINGDEVICE" => {
            Ok(EquipmentType::Electrical)
        }
        "IFCFIREALARM" | "IFCFIREDETECTOR" => Ok(EquipmentType::Safety),
        "IFCPIPE" | "IFCPIPEFITTING" | "IFCTANK" => Ok(EquipmentType::Plumbing),
        _ => Ok(EquipmentType::Other(ifc_entity_type.to_string())),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_is_storey_entity() {
        assert!(is_storey_entity("IFCBUILDINGSTOREY"));
        assert!(is_storey_entity("IFCBUILDINGFLOOR"));
        assert!(is_storey_entity("IFCLEVEL"));
        assert!(is_storey_entity("ifcbuildingstorey")); // Case insensitive
        assert!(!is_storey_entity("IFCBUILDING"));
        assert!(!is_storey_entity("IFCSPACE"));
    }

    #[test]
    fn test_is_space_entity() {
        assert!(is_space_entity("IFCSPACE"));
        assert!(is_space_entity("IFCROOM"));
        assert!(is_space_entity("IFCZONE"));
        assert!(is_space_entity("ifcspace")); // Case insensitive
        assert!(!is_space_entity("IFCBUILDING"));
    }

    #[test]
    fn test_is_equipment_entity() {
        assert!(is_equipment_entity("IFCFLOWTERMINAL"));
        assert!(is_equipment_entity("IFCAIRTERMINAL"));
        assert!(is_equipment_entity("IFCLIGHTFIXTURE"));
        assert!(is_equipment_entity("IFCFAN"));
        assert!(!is_equipment_entity("IFCFANTYPE")); // TYPE excluded
        assert!(!is_equipment_entity("IFCBUILDING"));
    }

    #[test]
    fn test_extract_storey_level() {
        let floor1 = IFCEntity::new(
            "#1".to_string(),
            "IFCBUILDINGSTOREY".to_string(),
            "First Floor".to_string(),
            "".to_string(),
        );
        assert_eq!(extract_storey_level(&floor1).unwrap(), 1);

        let floor2 = IFCEntity::new(
            "#2".to_string(),
            "IFCBUILDINGSTOREY".to_string(),
            "Floor 2".to_string(),
            "".to_string(),
        );
        assert_eq!(extract_storey_level(&floor2).unwrap(), 2);
    }

    #[test]
    fn test_extract_equipment_type() {
        assert!(matches!(
            extract_equipment_type("IFCFAN").unwrap(),
            EquipmentType::HVAC
        ));
        assert!(matches!(
            extract_equipment_type("IFCLIGHTFIXTURE").unwrap(),
            EquipmentType::Electrical
        ));
        assert!(matches!(
            extract_equipment_type("IFCFIREALARM").unwrap(),
            EquipmentType::Safety
        ));
    }
}

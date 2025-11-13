//! IFC Type Mapping System
//!
//! Maps ArxOS EquipmentType to IFC entity types for game-created equipment.
//! Ensures proper IFC representation when exporting game plans.

use crate::core::EquipmentType;
use crate::game::ifc_sync::IFCSyncManager;
use log::{info, warn};

/// IFC entity type mapper for equipment types
pub struct IFCTypeMapper;

impl IFCTypeMapper {
    /// Map EquipmentType to IFC entity type string
    pub fn map_equipment_type_to_ifc(equipment_type: &EquipmentType) -> String {
        match equipment_type {
            EquipmentType::HVAC => "IFCAIRTERMINAL".to_string(),
            EquipmentType::Electrical => "IFCLIGHTFIXTURE".to_string(),
            EquipmentType::AV => "IFCDISTRIBUTIONELEMENT".to_string(),
            EquipmentType::Plumbing => "IFCFLOWTERMINAL".to_string(),
            EquipmentType::Network => "IFCCABLECARRIERSEGMENT".to_string(),
            EquipmentType::Furniture => "IFCFURNISHINGELEMENT".to_string(),
            EquipmentType::Safety => "IFCDISTRIBUTIONELEMENT".to_string(),
            EquipmentType::Other(name) => {
                // Try to map based on name patterns
                let name_lower = name.to_lowercase();
                if name_lower.contains("light")
                    || name_lower.contains("lamp")
                    || name_lower.contains("fixture")
                {
                    "IFCLIGHTFIXTURE".to_string()
                } else if name_lower.contains("air")
                    || name_lower.contains("vent")
                    || name_lower.contains("hvac")
                {
                    "IFCAIRTERMINAL".to_string()
                } else if name_lower.contains("pump") {
                    "IFCPUMP".to_string()
                } else if name_lower.contains("fan") {
                    "IFCFAN".to_string()
                } else if name_lower.contains("valve") {
                    "IFCVALVE".to_string()
                } else if name_lower.contains("switch") || name_lower.contains("panel") {
                    "IFCELECTRICDISTRIBUTIONBOARD".to_string()
                } else {
                    // Default to generic distribution element
                    "IFCDISTRIBUTIONELEMENT".to_string()
                }
            }
        }
    }

    /// Map IFC entity type string to EquipmentType (reverse mapping)
    pub fn map_ifc_to_equipment_type(ifc_type: &str) -> EquipmentType {
        match ifc_type {
            "IFCAIRTERMINAL" | "IFCAIRTERMINALBOX" | "IFCAIRTERMINALDIFFUSER" => {
                EquipmentType::HVAC
            }
            "IFCLIGHTFIXTURE" | "IFCLAMP" => EquipmentType::Electrical,
            "IFCFLOWTERMINAL" | "IFCFLOWCONTROLLER" | "IFCFLOWMETER" => EquipmentType::Plumbing,
            "IFCCABLECARRIERSEGMENT" | "IFCCABLESEGMENT" | "IFCELECTRICFLOWSTORAGEDEVICE" => {
                EquipmentType::Network
            }
            "IFCFURNISHINGELEMENT" => EquipmentType::Furniture,
            "IFCPUMP" | "IFCFAN" | "IFCVALVE" => {
                // These could be HVAC or Plumbing - default to Plumbing
                EquipmentType::Plumbing
            }
            "IFCELECTRICDISTRIBUTIONBOARD" | "IFCELECTRICMOTOR" => EquipmentType::Electrical,
            _ => {
                // Default to Other with the IFC type name
                EquipmentType::Other(ifc_type.to_string())
            }
        }
    }

    /// Apply IFC type mapping to equipment in sync manager
    pub fn apply_mapping_to_sync_manager(
        sync_manager: &mut IFCSyncManager,
        equipment_id: &str,
        equipment_type: &EquipmentType,
    ) {
        let ifc_entity_type = Self::map_equipment_type_to_ifc(equipment_type);
        sync_manager.set_entity_type(equipment_id, ifc_entity_type);
        info!(
            "Mapped equipment '{}' type '{:?}' to IFC entity type",
            equipment_id, equipment_type
        );
    }

    /// Validate IFC entity type is valid IFC4 entity
    pub fn validate_ifc_entity_type(ifc_type: &str) -> bool {
        let valid_types = [
            // Spatial
            "IFCSPACE",
            "IFCROOM",
            "IFCBUILDINGSTOREY",
            // HVAC
            "IFCAIRTERMINAL",
            "IFCAIRTERMINALBOX",
            "IFCAIRTERMINALDIFFUSER",
            "IFCAIRTOAIRHEATRECOVERY",
            "IFCAIRHANDLINGUNIT",
            // Electrical
            "IFCLIGHTFIXTURE",
            "IFCLAMP",
            "IFCELECTRICDISTRIBUTIONBOARD",
            "IFCELECTRICMOTOR",
            "IFCELECTRICGENERATOR",
            // Plumbing
            "IFCFLOWTERMINAL",
            "IFCFLOWCONTROLLER",
            "IFCFLOWMETER",
            "IFCPUMP",
            "IFCVALVE",
            // Network
            "IFCCABLECARRIERSEGMENT",
            "IFCCABLESEGMENT",
            // Mechanical
            "IFCFAN",
            "IFCMECHANICALFASTENER",
            // Generic
            "IFCDISTRIBUTIONELEMENT",
            "IFCFLOWSTEREOTYPE",
            // Furniture
            "IFCFURNISHINGELEMENT",
        ];

        valid_types.contains(&ifc_type)
    }

    /// Get recommended IFC entity type based on equipment name and type
    pub fn get_recommended_ifc_type(
        equipment_type: &EquipmentType,
        equipment_name: &str,
    ) -> String {
        let base_type = Self::map_equipment_type_to_ifc(equipment_type);

        // Refine based on name if it's the generic type
        if base_type == "IFCDISTRIBUTIONELEMENT" {
            let name_lower = equipment_name.to_lowercase();

            // Try to find more specific type
            if name_lower.contains("board") || name_lower.contains("panel") {
                "IFCELECTRICDISTRIBUTIONBOARD".to_string()
            } else if name_lower.contains("outlet") || name_lower.contains("receptacle") {
                "IFCELECTRICFLOWSTORAGEDEVICE".to_string()
            } else {
                base_type
            }
        } else {
            base_type
        }
    }

    /// Get all supported IFC entity types for equipment
    pub fn get_supported_ifc_types() -> Vec<&'static str> {
        vec![
            "IFCAIRTERMINAL",
            "IFCLIGHTFIXTURE",
            "IFCFLOWTERMINAL",
            "IFCPUMP",
            "IFCFAN",
            "IFCVALVE",
            "IFCELECTRICDISTRIBUTIONBOARD",
            "IFCDISTRIBUTIONELEMENT",
            "IFCFURNISHINGELEMENT",
        ]
    }

    /// Get equipment type description for IFC entity type
    pub fn get_ifc_type_description(ifc_type: &str) -> String {
        match ifc_type {
            "IFCAIRTERMINAL" => "Air terminal for HVAC system (diffuser, grille, etc.)".to_string(),
            "IFCLIGHTFIXTURE" => "Light fixture or lamp".to_string(),
            "IFCFLOWTERMINAL" => "Flow terminal for plumbing (faucet, shower, etc.)".to_string(),
            "IFCPUMP" => "Pump for fluid circulation".to_string(),
            "IFCFAN" => "Fan for air circulation".to_string(),
            "IFCVALVE" => "Valve for flow control".to_string(),
            "IFCELECTRICDISTRIBUTIONBOARD" => "Electrical distribution panel or board".to_string(),
            "IFCDISTRIBUTIONELEMENT" => "Generic distribution element".to_string(),
            "IFCFURNISHINGELEMENT" => "Furniture or furnishing element".to_string(),
            _ => format!("Unknown IFC entity type: {}", ifc_type),
        }
    }
}

/// Helper to apply IFC type mapping to a game equipment placement
pub fn apply_ifc_type_mapping(
    sync_manager: &mut IFCSyncManager,
    equipment_id: &str,
    equipment_type: &EquipmentType,
    equipment_name: &str,
) {
    let ifc_type = IFCTypeMapper::get_recommended_ifc_type(equipment_type, equipment_name);

    if IFCTypeMapper::validate_ifc_entity_type(&ifc_type) {
        sync_manager.set_entity_type(equipment_id, ifc_type);
    } else {
        warn!(
            "Invalid IFC entity type generated for equipment '{}', using generic type",
            equipment_id
        );
        sync_manager.set_entity_type(equipment_id, "IFCDISTRIBUTIONELEMENT".to_string());
    }
}

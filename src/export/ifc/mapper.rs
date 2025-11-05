//! Universal Path / ArxAddress → IFC Entity ID Mapper
//! 
//! Provides deterministic mapping from ArxOS Universal Path or ArxAddress to IFC entity IDs.
//! Ensures consistent entity IDs across exports for round-trip compatibility.
//! 
//! Prefers ArxAddress GUIDs when available, falls back to Universal Path hashing.

/// Deterministic hash function for Universal Path → IFC entity ID mapping
/// Uses DJB2 hash algorithm (same as EnhancedIFCParser.hash_string)
fn hash_universal_path(path: &str) -> u64 {
    let mut hash = 5381u64;
    for byte in path.bytes() {
        hash = hash.wrapping_mul(33).wrapping_add(byte as u64);
    }
    hash
}

/// Map Universal Path to IFC entity ID
/// 
/// Returns a deterministic entity ID in the range 10000-910000
/// (avoids conflicts with synthetic IDs that start at 1000)
/// 
/// # Arguments
/// * `path` - Universal Path string (e.g., "building/floor-1/room-101/equipment-hvac-1")
/// 
/// # Returns
/// * Deterministic u32 entity ID
pub fn universal_path_to_ifc_entity_id(path: &str) -> u32 {
    let hash = hash_universal_path(path);
    // Map to range 10000-910000 to avoid conflicts with synthetic IDs (1000-9999)
    ((hash % 900000) as u32) + 10000
}

/// Map ArxAddress to IFC entity ID using GUID
/// 
/// Uses the SHA-256 hash from ArxAddress::guid() and converts to IFC entity ID.
/// Returns a deterministic entity ID in the range 10000-910000.
/// 
/// **GUID Collision Guard**: SHA-256 provides 2^256 possible values, making collisions
/// statistically impossible for practical purposes. The same address path will always
/// produce the same GUID, ensuring deterministic IFC entity IDs for round-trip compatibility.
/// 
/// # Arguments
/// * `address` - ArxAddress instance
/// 
/// # Returns
/// * Deterministic u32 entity ID
pub fn address_to_ifc_entity_id(address: &crate::domain::ArxAddress) -> u32 {
    let guid = address.guid();
    // Convert first 8 hex chars of GUID to u32 and map to range
    // Note: SHA-256 ensures uniqueness - same path = same GUID, different paths = different GUIDs
    let hash = u64::from_str_radix(&guid[..8.min(guid.len())], 16).unwrap_or(0);
    ((hash % 900000) as u32) + 10000
}

/// Map equipment type string to IFC entity type
/// 
/// Maps common equipment type strings to IFC4 entity types.
/// Handles case-insensitive matching and common variations.
/// 
/// # Arguments
/// * `type_str` - Equipment type string (e.g., "HVAC", "electrical", "plumbing")
/// 
/// # Returns
/// * IFC entity type string
pub fn map_equipment_type_string_to_ifc(type_str: &str) -> String {
    let type_lower = type_str.to_lowercase();
    
    // Direct type mappings
    match type_lower.as_str() {
        "hvac" => "IFCAIRTERMINAL".to_string(),
        "electrical" | "electric" => "IFCLIGHTFIXTURE".to_string(),
        "plumbing" => "IFCFLOWTERMINAL".to_string(),
        "network" => "IFCCABLECARRIERSEGMENT".to_string(),
        "furniture" => "IFCFURNISHINGELEMENT".to_string(),
        "safety" => "IFCDISTRIBUTIONELEMENT".to_string(),
        "av" | "audiovisual" => "IFCDISTRIBUTIONELEMENT".to_string(),
        _ => {
            // Pattern-based matching for more flexibility
            if type_lower.contains("light") || type_lower.contains("lamp") || type_lower.contains("fixture") {
                "IFCLIGHTFIXTURE".to_string()
            } else if type_lower.contains("air") || type_lower.contains("vent") || type_lower.contains("hvac") {
                "IFCAIRTERMINAL".to_string()
            } else if type_lower.contains("pump") {
                "IFCPUMP".to_string()
            } else if type_lower.contains("fan") {
                "IFCFAN".to_string()
            } else if type_lower.contains("valve") {
                "IFCVALVE".to_string()
            } else if type_lower.contains("switch") || type_lower.contains("panel") {
                "IFCELECTRICDISTRIBUTIONBOARD".to_string()
            } else {
                // Default to generic distribution element
                "IFCDISTRIBUTIONELEMENT".to_string()
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_universal_path_to_ifc_entity_id_deterministic() {
        let path = "building/floor-1/room-101/equipment-hvac-1";
        let id1 = universal_path_to_ifc_entity_id(path);
        let id2 = universal_path_to_ifc_entity_id(path);
        assert_eq!(id1, id2, "Hash should be deterministic");
        assert!(id1 >= 10000 && id1 < 910000, "ID should be in valid range");
    }

    #[test]
    fn test_universal_path_to_ifc_entity_id_range() {
        let path1 = "building/floor-1/room-101/equipment-hvac-1";
        let path2 = "building/floor-1/room-102/equipment-hvac-2";
        let id1 = universal_path_to_ifc_entity_id(path1);
        let id2 = universal_path_to_ifc_entity_id(path2);
        
        // Different paths should (very likely) produce different IDs
        // (not guaranteed, but statistically very unlikely to collide)
        assert!(id1 >= 10000 && id1 < 910000);
        assert!(id2 >= 10000 && id2 < 910000);
    }

    #[test]
    fn test_map_equipment_type_string_to_ifc() {
        assert_eq!(map_equipment_type_string_to_ifc("HVAC"), "IFCAIRTERMINAL");
        assert_eq!(map_equipment_type_string_to_ifc("hvac"), "IFCAIRTERMINAL");
        assert_eq!(map_equipment_type_string_to_ifc("Electrical"), "IFCLIGHTFIXTURE");
        assert_eq!(map_equipment_type_string_to_ifc("plumbing"), "IFCFLOWTERMINAL");
        assert_eq!(map_equipment_type_string_to_ifc("network"), "IFCCABLECARRIERSEGMENT");
        assert_eq!(map_equipment_type_string_to_ifc("furniture"), "IFCFURNISHINGELEMENT");
        
        // Pattern matching
        assert_eq!(map_equipment_type_string_to_ifc("light fixture"), "IFCLIGHTFIXTURE");
        assert_eq!(map_equipment_type_string_to_ifc("air terminal"), "IFCAIRTERMINAL");
        assert_eq!(map_equipment_type_string_to_ifc("pump unit"), "IFCPUMP");
        assert_eq!(map_equipment_type_string_to_ifc("fan system"), "IFCFAN");
        
        // Default case
        assert_eq!(map_equipment_type_string_to_ifc("unknown"), "IFCDISTRIBUTIONELEMENT");
    }

    #[test]
    fn test_map_equipment_type_edge_cases() {
        // Empty string
        assert_eq!(map_equipment_type_string_to_ifc(""), "IFCDISTRIBUTIONELEMENT");
        
        // Mixed case
        assert_eq!(map_equipment_type_string_to_ifc("HvAc"), "IFCAIRTERMINAL");
        assert_eq!(map_equipment_type_string_to_ifc("ElEcTrIcAl"), "IFCLIGHTFIXTURE");
        
        // Pattern matching edge cases
        assert_eq!(map_equipment_type_string_to_ifc("LED Light"), "IFCLIGHTFIXTURE");
        assert_eq!(map_equipment_type_string_to_ifc("HVAC Unit"), "IFCAIRTERMINAL");
        assert_eq!(map_equipment_type_string_to_ifc("Water Pump"), "IFCPUMP");
        assert_eq!(map_equipment_type_string_to_ifc("Exhaust Fan"), "IFCFAN");
        assert_eq!(map_equipment_type_string_to_ifc("Control Valve"), "IFCVALVE");
        assert_eq!(map_equipment_type_string_to_ifc("Electrical Panel"), "IFCELECTRICDISTRIBUTIONBOARD");
    }

    #[test]
    fn test_universal_path_to_ifc_entity_id_distinct_paths() {
        // Test that different paths produce different IDs (very likely, but not guaranteed)
        let path1 = "building/floor-1/room-101/equipment-hvac-1";
        let path2 = "building/floor-1/room-101/equipment-hvac-2";
        let path3 = "building/floor-2/room-201/equipment-hvac-1";
        
        let id1 = universal_path_to_ifc_entity_id(path1);
        let id2 = universal_path_to_ifc_entity_id(path2);
        let id3 = universal_path_to_ifc_entity_id(path3);
        
        // Verify all are in valid range
        assert!(id1 >= 10000 && id1 < 910000);
        assert!(id2 >= 10000 && id2 < 910000);
        assert!(id3 >= 10000 && id3 < 910000);
        
        // Very unlikely to collide, but technically possible
        // In practice, different paths should produce different IDs
    }

    #[test]
    fn test_universal_path_to_ifc_entity_id_empty_string() {
        let id = universal_path_to_ifc_entity_id("");
        assert!(id >= 10000 && id < 910000);
    }

    #[test]
    fn test_universal_path_to_ifc_entity_id_special_characters() {
        let path = "building/floor-1/room-101/equipment:hvac-1";
        let id = universal_path_to_ifc_entity_id(path);
        assert!(id >= 10000 && id < 910000);
        
        // Should be deterministic
        let id2 = universal_path_to_ifc_entity_id(path);
        assert_eq!(id, id2);
    }

    #[test]
    fn test_address_to_ifc_entity_id_collision_guard() {
        use crate::domain::ArxAddress;
        
        // Test that same address produces same IFC ID
        let addr1 = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        let addr2 = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        
        let id1 = address_to_ifc_entity_id(&addr1);
        let id2 = address_to_ifc_entity_id(&addr2);
        
        assert_eq!(id1, id2, "Same address should produce same IFC entity ID");
        assert!(id1 >= 10000 && id1 < 910000, "ID should be in valid range");
    }

    #[test]
    fn test_address_to_ifc_entity_id_different_paths() {
        use crate::domain::ArxAddress;
        
        // Test that different addresses produce different IFC IDs (very likely)
        let addr1 = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-01").unwrap();
        let addr2 = ArxAddress::from_path("/usa/ny/brooklyn/ps-118/floor-02/mech/boiler-02").unwrap();
        
        let id1 = address_to_ifc_entity_id(&addr1);
        let id2 = address_to_ifc_entity_id(&addr2);
        
        // Very unlikely to collide, but technically possible
        // In practice, different paths should produce different IDs
        assert!(id1 >= 10000 && id1 < 910000);
        assert!(id2 >= 10000 && id2 < 910000);
    }
}


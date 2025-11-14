//! Character mappings and symbols for ASCII rendering
//!
//! Provides equipment-specific symbols and legends for 3D ASCII visualization.

use crate::core::EquipmentType;

/// Get ASCII symbol for equipment type
///
/// Maps equipment types to visually distinct ASCII characters for rendering.
///
/// # Arguments
///
/// * `equipment_type` - The type of equipment to get a symbol for
///
/// # Returns
///
/// A single ASCII character representing the equipment type
///
/// # Symbol Mappings
///
/// - HVAC: ▲ (triangle pointing up)
/// - Electrical: ● (filled circle)
/// - Plumbing: ◊ (diamond)
/// - Safety: ◈ (diamond with cross)
/// - Network: ↯ (lightning bolt)
/// - AV: ♫ (music note)
/// - Furniture: ⌂ (house)
/// - Generic: ╬ (cross)
pub fn get_equipment_symbol(equipment_type: &EquipmentType) -> char {
    match equipment_type {
        EquipmentType::HVAC => '▲',
        EquipmentType::Electrical => '●',
        EquipmentType::Plumbing => '◊',
        EquipmentType::Safety => '◈',
        EquipmentType::Network => '↯',
        EquipmentType::AV => '♫',
        EquipmentType::Furniture => '⌂',
        EquipmentType::Generic => '╬',
    }
}

/// Get floor character
pub const FLOOR_CHAR: char = '─';

/// Get wall character
pub const WALL_CHAR: char = '█';

/// Get room character
pub const ROOM_CHAR: char = '○';

/// Legend text for ASCII visualization
pub const LEGEND: &str =
    "Legend: █=Wall │ ╬=Generic │ ○=Room │ ─=Floor │ ▲=HVAC │ ●=Electrical │ ◊=Plumbing │ ◈=Safety │ ↯=Network │ ♫=AV │ ⌂=Furniture";

/// Get equipment symbol with fallback
///
/// Returns the equipment symbol, or a generic fallback if the type is unknown.
pub fn get_equipment_symbol_safe(equipment_type: &EquipmentType) -> char {
    get_equipment_symbol(equipment_type)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_equipment_symbols() {
        assert_eq!(get_equipment_symbol(&EquipmentType::HVAC), '▲');
        assert_eq!(get_equipment_symbol(&EquipmentType::Electrical), '●');
        assert_eq!(get_equipment_symbol(&EquipmentType::Plumbing), '◊');
        assert_eq!(get_equipment_symbol(&EquipmentType::Safety), '◈');
        assert_eq!(get_equipment_symbol(&EquipmentType::Network), '↯');
        assert_eq!(get_equipment_symbol(&EquipmentType::AV), '♫');
        assert_eq!(get_equipment_symbol(&EquipmentType::Furniture), '⌂');
        assert_eq!(get_equipment_symbol(&EquipmentType::Generic), '╬');
    }

    #[test]
    fn test_special_characters() {
        assert_eq!(FLOOR_CHAR, '─');
        assert_eq!(WALL_CHAR, '█');
        assert_eq!(ROOM_CHAR, '○');
    }

    #[test]
    fn test_legend_not_empty() {
        assert!(!LEGEND.is_empty());
        assert!(LEGEND.contains("HVAC"));
        assert!(LEGEND.contains("Electrical"));
    }
}

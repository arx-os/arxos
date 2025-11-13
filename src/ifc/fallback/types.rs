//! Type definitions for IFC fallback parser

/// IFC entity extracted from STEP file
#[derive(Debug, Clone)]
pub struct IFCEntity {
    pub id: String,
    pub entity_type: String,
    pub name: String,
    pub definition: String,
}

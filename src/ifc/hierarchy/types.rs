//! IFC entity types for hierarchy building
//!
//! Core data structures representing IFC entities used in hierarchy construction.

/// IFC entity structure for hierarchy building
///
/// This structure represents a simplified IFC entity extracted from IFC files.
/// It contains the minimal information needed to build the ArxOS building hierarchy.
///
/// # Fields
///
/// * `id` - Unique identifier for the entity (e.g., "#123")
/// * `entity_type` - IFC entity type (e.g., "IFCBUILDING", "IFCSPACE")
/// * `name` - Human-readable name of the entity
/// * `definition` - Complete IFC definition string for parsing attributes
///
/// # Examples
///
/// ```ignore
/// use crate::ifc::hierarchy::IFCEntity;
///
/// let entity = IFCEntity {
///     id: "#42".to_string(),
///     entity_type: "IFCBUILDING".to_string(),
///     name: "Main Building".to_string(),
///     definition: "IFCBUILDING(#42,$,$,'Main Building',$,#15,#20)".to_string(),
/// };
/// ```
#[derive(Debug, Clone)]
pub struct IFCEntity {
    /// Unique identifier (e.g., "#123")
    pub id: String,

    /// IFC entity type (e.g., "IFCBUILDING", "IFCBUILDINGSTOREY", "IFCSPACE")
    pub entity_type: String,

    /// Human-readable name
    pub name: String,

    /// Complete IFC definition for attribute parsing
    pub definition: String,
}

impl IFCEntity {
    /// Create a new IFC entity
    ///
    /// # Arguments
    ///
    /// * `id` - Unique identifier
    /// * `entity_type` - IFC entity type
    /// * `name` - Entity name
    /// * `definition` - IFC definition string
    pub fn new(id: String, entity_type: String, name: String, definition: String) -> Self {
        Self {
            id,
            entity_type,
            name,
            definition,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ifc_entity_creation() {
        let entity = IFCEntity::new(
            "#123".to_string(),
            "IFCBUILDING".to_string(),
            "Test Building".to_string(),
            "IFCBUILDING(#123,$,$,'Test Building',$,#15,#20)".to_string(),
        );

        assert_eq!(entity.id, "#123");
        assert_eq!(entity.entity_type, "IFCBUILDING");
        assert_eq!(entity.name, "Test Building");
    }
}

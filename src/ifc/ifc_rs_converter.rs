//! Converter from ifc_rs types to ArxOS IFCEntity format
//!
//! This module bridges ifc_rs's parsed IFC data structures to ArxOS's internal
//! IFCEntity representation used by HierarchyBuilder.

use crate::error::ArxResult;
use crate::ifc::hierarchy::IFCEntity;
use ifc_rs::IFC;
use ifc_rs::traits::ifc_type::IfcType;

/// Converts ifc_rs parsed IFC data to ArxOS IFCEntity format
///
/// This struct provides methods to extract entities from ifc_rs and convert them
/// to the simplified IFCEntity format expected by HierarchyBuilder.
pub struct IFCRsConverter;

impl IFCRsConverter {
    /// Convert ifc_rs IFC data to a vector of IFCEntity
    ///
    /// Extracts all supported entity types from the ifc_rs DataMap and converts them
    /// to ArxOS IFCEntity format. The entities are collected in a flat list suitable
    /// for processing by HierarchyBuilder.
    ///
    /// # Arguments
    ///
    /// * `ifc` - The parsed IFC data from ifc_rs
    ///
    /// # Returns
    ///
    /// A vector of IFCEntity instances representing the building elements
    ///
    /// # Examples
    ///
    /// ```ignore
    /// use ifc_rs::IFC;
    /// use crate::ifc::ifc_rs_converter::IFCRsConverter;
    ///
    /// let ifc = IFC::from_file("building.ifc")?;
    /// let entities = IFCRsConverter::convert(&ifc)?;
    /// ```
    pub fn convert(ifc: &IFC) -> ArxResult<Vec<IFCEntity>> {
        let mut entities = Vec::new();

        // Extract all IFC entities using ifc_rs's type system
        // The ifc_rs library provides a find_all_of_type method on DataMap
        // that we use to iterate through each supported entity type
        
        Self::extract_all_entities(ifc, &mut entities)?;

        Ok(entities)
    }

    /// Extract all entities from the IFC data
    ///
    /// This is a helper method that iterates through the ifc_rs DataMap and
    /// extracts entity information. Since the DataMap field is private, we use
    /// the public API methods provided by ifc_rs.
    ///
    /// # Implementation Notes
    ///
    /// The ifc_rs DataMap provides:
    /// - `find_all_of_type::<T>()` - Find all entities of a specific type
    /// - `get_untyped(id)` - Get entity by ID without type checking
    ///
    /// Each IfcType has:
    /// - `type_name()` - Get the type name as a string
    /// - `Display` trait - String representation
    ///
    /// We use the public IfcExtractor API to navigate the entity hierarchy.
    fn extract_all_entities(ifc: &IFC, entities: &mut Vec<IFCEntity>) -> ArxResult<()> {
        use ifc_rs::prelude::*;

        // Extract Project entities
        Self::extract_entities_of_type::<Project>(ifc, "IFCPROJECT", entities);
        
        // Extract Site entities
        Self::extract_entities_of_type::<Site>(ifc, "IFCSITE", entities);
        
        // Extract Building entities
        Self::extract_entities_of_type::<Building>(ifc, "IFCBUILDING", entities);
        
        // Extract Storey entities
        Self::extract_entities_of_type::<Storey>(ifc, "IFCBUILDINGSTOREY", entities);
        
        // Extract Space entities
        Self::extract_entities_of_type::<Space>(ifc, "IFCSPACE", entities);
        
        // Extract Wall entities
        Self::extract_entities_of_type::<Wall>(ifc, "IFCWALL", entities);
        
        // Extract Slab entities
        Self::extract_entities_of_type::<Slab>(ifc, "IFCSLAB", entities);
        
        // Extract Roof entities
        Self::extract_entities_of_type::<Roof>(ifc, "IFCROOF", entities);
        
        // Extract Window entities
        Self::extract_entities_of_type::<Window>(ifc, "IFCWINDOW", entities);
        
        // Extract Door entities
        Self::extract_entities_of_type::<Door>(ifc, "IFCDOOR", entities);

        Ok(())
    }

    /// Extract entities of a specific type from the IFC data
    ///
    /// Uses ifc_rs's `find_all_of_type` method to find all entities of type T
    /// and convert them to IFCEntity format.
    ///
    /// # Type Parameters
    ///
    /// * `T` - The ifc_rs entity type to extract (must implement IfcType)
    ///
    /// # Arguments
    ///
    /// * `ifc` - The parsed IFC data
    /// * `entity_type_name` - The IFC type name (e.g., "IFCBUILDING")
    /// * `entities` - Vector to append extracted entities to
    fn extract_entities_of_type<T: IfcType>(
        ifc: &IFC,
        entity_type_name: &str,
        entities: &mut Vec<IFCEntity>,
    ) {
        // Use find_all_of_type to get typed iterator
        for (typed_id, entity) in ifc.data.find_all_of_type::<T>() {
            let id = format!("#{}", typed_id.id().0);
            let definition = entity.to_string();
            
            // Extract name from the entity
            // The name extraction varies by entity type, so we'll use a helper
            let name = Self::extract_name(&definition);
            
            entities.push(IFCEntity {
                id,
                entity_type: entity_type_name.to_string(),
                name,
                definition,
            });
        }
    }

    /// Extract the name field from an IFC entity definition
    ///
    /// IFC entities typically have their name as one of the first string parameters.
    /// This method performs a simple extraction looking for quoted strings in the
    /// definition.
    ///
    /// # Arguments
    ///
    /// * `definition` - The complete IFC entity definition string
    ///
    /// # Returns
    ///
    /// The extracted name, or an empty string if no name found
    ///
    /// # Examples
    ///
    /// ```ignore
    /// let def = "IFCBUILDING(#42,#100,'Building Name',$,$,#15,#20)";
    /// let name = IFCRsConverter::extract_name(def);
    /// assert_eq!(name, "Building Name");
    /// ```
    fn extract_name(definition: &str) -> String {
        // Find the first quoted string in the definition
        // IFC format uses single quotes for strings
        if let Some(start) = definition.find('\'') {
            if let Some(end) = definition[start + 1..].find('\'') {
                return definition[start + 1..start + 1 + end].to_string();
            }
        }
        
        // No name found - return empty string
        String::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_name() {
        let def = "IFCBUILDING(#42,#100,'Main Building',$,$,#15,#20)";
        assert_eq!(IFCRsConverter::extract_name(def), "Main Building");
        
        let def2 = "IFCSPACE(#123,#200,'Office Room',$,$,#30,#40)";
        assert_eq!(IFCRsConverter::extract_name(def2), "Office Room");
        
        let def3 = "IFCWALL(#456,#300,$,$,$,#50,#60)";
        assert_eq!(IFCRsConverter::extract_name(def3), "");
    }

    #[test]
    fn test_convert_with_sample_file() {
        // This test requires the sample file to be present
        if let Ok(ifc) = ifc_rs::IFC::from_file("test_data/sample_building.ifc") {
            let result = IFCRsConverter::convert(&ifc);
            assert!(result.is_ok());
            
            let entities = result.unwrap();
            assert!(!entities.is_empty(), "Should extract at least some entities");
            
            // Check that we have various entity types
            let has_building = entities.iter().any(|e| e.entity_type == "IFCBUILDING");
            let has_storey = entities.iter().any(|e| e.entity_type == "IFCBUILDINGSTOREY");
            
            println!("Extracted {} entities", entities.len());
            println!("Has building: {}", has_building);
            println!("Has storey: {}", has_storey);
        }
    }
}

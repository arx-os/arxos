//! Equipment relationship parsing

use super::types::{EnhancedIFCParser, EquipmentRelationship, RelationshipType};
use crate::spatial::SpatialEntity;
use log::info;

impl EnhancedIFCParser {
    /// Parse equipment relationships from IFC data
    pub fn parse_equipment_relationships(
        &self,
        entities: &[SpatialEntity],
    ) -> Vec<EquipmentRelationship> {
        let mut relationships = Vec::new();

        for entity in entities {
            // Parse different types of relationships based on entity type
            match entity.entity_type.as_str() {
                "IFCDUCTSEGMENT" | "IFCPIPESEGMENT" => {
                    self.parse_flow_segment_relationships(entity, &mut relationships);
                }
                "IFCDUCTFITTING" | "IFCPIPEFITTING" => {
                    self.parse_fitting_relationships(entity, &mut relationships);
                }
                "IFCFLOWTERMINAL" | "IFCAIRTERMINAL" => {
                    self.parse_terminal_relationships(entity, &mut relationships);
                }
                "IFCFLOWCONTROLLER" => {
                    self.parse_controller_relationships(entity, &mut relationships);
                }
                _ => {
                    // For other equipment types, look for generic connections
                    self.parse_generic_relationships(entity, &mut relationships);
                }
            }
        }

        info!("Parsed {} equipment relationships", relationships.len());
        relationships
    }

    /// Parse flow segment relationships (ducts, pipes)
    fn parse_flow_segment_relationships(
        &self,
        entity: &SpatialEntity,
        relationships: &mut Vec<EquipmentRelationship>,
    ) {
        // Flow segments typically connect to fittings and other segments
        // For now, we'll create proximity-based relationships
        // In a full implementation, we would parse IFC connection data

        // Create relationship to nearby equipment
        let relationship = EquipmentRelationship {
            from_entity_id: entity.id.clone(),
            to_entity_id: format!("{}_CONNECTION", entity.id),
            relationship_type: RelationshipType::Flow,
            connection_type: Some("DUCT_SEGMENT".to_string()),
            properties: vec![
                ("length".to_string(), "estimated".to_string()),
                ("diameter".to_string(), "standard".to_string()),
            ],
        };

        relationships.push(relationship);
    }

    /// Parse fitting relationships (elbows, tees, reducers)
    fn parse_fitting_relationships(
        &self,
        entity: &SpatialEntity,
        relationships: &mut Vec<EquipmentRelationship>,
    ) {
        // Fittings connect multiple flow segments
        let relationship = EquipmentRelationship {
            from_entity_id: entity.id.clone(),
            to_entity_id: format!("{}_INLET", entity.id),
            relationship_type: RelationshipType::Flow,
            connection_type: Some("FITTING".to_string()),
            properties: vec![
                ("fitting_type".to_string(), "elbow".to_string()),
                ("angle".to_string(), "90_degrees".to_string()),
            ],
        };

        relationships.push(relationship);

        // Add outlet connection
        let outlet_relationship = EquipmentRelationship {
            from_entity_id: entity.id.clone(),
            to_entity_id: format!("{}_OUTLET", entity.id),
            relationship_type: RelationshipType::Flow,
            connection_type: Some("FITTING".to_string()),
            properties: vec![
                ("fitting_type".to_string(), "elbow".to_string()),
                ("angle".to_string(), "90_degrees".to_string()),
            ],
        };

        relationships.push(outlet_relationship);
    }

    /// Parse terminal relationships (air terminals, outlets)
    fn parse_terminal_relationships(
        &self,
        entity: &SpatialEntity,
        relationships: &mut Vec<EquipmentRelationship>,
    ) {
        // Terminals connect to supply/return systems
        let relationship = EquipmentRelationship {
            from_entity_id: entity.id.clone(),
            to_entity_id: format!("{}_SUPPLY", entity.id),
            relationship_type: RelationshipType::Flow,
            connection_type: Some("TERMINAL".to_string()),
            properties: vec![
                ("flow_rate".to_string(), "variable".to_string()),
                ("pressure".to_string(), "low".to_string()),
            ],
        };

        relationships.push(relationship);
    }

    /// Parse controller relationships (valves, dampers)
    fn parse_controller_relationships(
        &self,
        entity: &SpatialEntity,
        relationships: &mut Vec<EquipmentRelationship>,
    ) {
        // Controllers regulate flow in systems
        let relationship = EquipmentRelationship {
            from_entity_id: entity.id.clone(),
            to_entity_id: format!("{}_CONTROL", entity.id),
            relationship_type: RelationshipType::Control,
            connection_type: Some("CONTROLLER".to_string()),
            properties: vec![
                ("control_type".to_string(), "modulating".to_string()),
                ("position".to_string(), "variable".to_string()),
            ],
        };

        relationships.push(relationship);
    }

    /// Parse generic equipment relationships
    fn parse_generic_relationships(
        &self,
        entity: &SpatialEntity,
        relationships: &mut Vec<EquipmentRelationship>,
    ) {
        // For generic equipment, create spatial relationships
        let relationship = EquipmentRelationship {
            from_entity_id: entity.id.clone(),
            to_entity_id: format!("{}_SPATIAL", entity.id),
            relationship_type: RelationshipType::Spatial,
            connection_type: Some("GENERIC".to_string()),
            properties: vec![
                ("spatial_type".to_string(), "proximity".to_string()),
                ("distance".to_string(), "calculated".to_string()),
            ],
        };

        relationships.push(relationship);
    }

    /// Find equipment connected to a specific entity
    pub fn find_connected_equipment<'a>(
        &self,
        entity_id: &str,
        relationships: &'a [EquipmentRelationship],
    ) -> Vec<&'a EquipmentRelationship> {
        relationships
            .iter()
            .filter(|rel| rel.from_entity_id == entity_id || rel.to_entity_id == entity_id)
            .collect()
    }

    /// Get equipment network (all connected equipment)
    pub fn get_equipment_network(
        &self,
        start_entity_id: &str,
        relationships: &[EquipmentRelationship],
    ) -> Vec<String> {
        let mut network = Vec::new();
        let mut visited = std::collections::HashSet::new();
        let mut to_visit = vec![start_entity_id.to_string()];

        while let Some(current_id) = to_visit.pop() {
            if visited.contains(&current_id) {
                continue;
            }

            visited.insert(current_id.clone());
            network.push(current_id.clone());

            // Find all connected equipment
            for rel in relationships {
                if rel.from_entity_id == current_id && !visited.contains(&rel.to_entity_id) {
                    to_visit.push(rel.to_entity_id.clone());
                } else if rel.to_entity_id == current_id && !visited.contains(&rel.from_entity_id) {
                    to_visit.push(rel.from_entity_id.clone());
                }
            }
        }

        network
    }

    /// Calculate equipment system efficiency
    pub fn calculate_system_efficiency(&self, relationships: &[EquipmentRelationship]) -> f64 {
        let total_relationships = relationships.len() as f64;
        if total_relationships == 0.0 {
            return 0.0;
        }

        // Count different types of connections
        let flow_connections = relationships
            .iter()
            .filter(|rel| rel.relationship_type == RelationshipType::Flow)
            .count() as f64;

        let control_connections = relationships
            .iter()
            .filter(|rel| rel.relationship_type == RelationshipType::Control)
            .count() as f64;

        // Calculate efficiency based on connection types
        let flow_efficiency = flow_connections / total_relationships;
        let control_efficiency = control_connections / total_relationships;

        // Weighted average (flow connections are more important)
        0.7 * flow_efficiency + 0.3 * control_efficiency
    }
}

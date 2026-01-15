//! Entity Registry for IFC reference resolution.
//! 
//! This module manages the graph of STEP entities and their mapping 
//! to the ArxOS domain (ArxAddress).

use std::collections::HashMap;
use crate::core::domain::ArxAddress;
use super::lexer::{RawEntity, Param};

/// A graph-aware cache for STEP entities and their ArxOS counterparts.
pub struct EntityRegistry {
    /// Mapping from STEP ID (#123) to raw entity data.
    entities: HashMap<u64, RawEntity>,
    /// Mapping from Class Name (e.g., "IFCSPACE") to list of IDs.
    class_map: HashMap<String, Vec<u64>>,
    /// Mapping from STEP ID to resolved ArxAddress.
    address_map: HashMap<u64, ArxAddress>,
}

impl EntityRegistry {
    /// Create a new empty registry.
    pub fn new() -> Self {
        Self {
            entities: HashMap::new(),
            class_map: HashMap::new(),
            address_map: HashMap::new(),
        }
    }

    /// Register a raw entity into the cache.
    pub fn register(&mut self, entity: RawEntity) {
        let id = entity.id;
        let class = entity.class.clone();
        self.entities.insert(id, entity);
        self.class_map.entry(class).or_default().push(id);
    }

    /// Look up a raw entity by its STEP ID.
    pub fn get_raw(&self, id: u64) -> Option<&RawEntity> {
        self.entities.get(&id)
    }

    /// Get all entity IDs for a specific class.
    pub fn get_by_class(&self, class: &str) -> &[u64] {
        self.class_map.get(class).map(|v| v.as_slice()).unwrap_or(&[])
    }

    /// Map a STEP ID to an ArxAddress.
    pub fn set_address(&mut self, id: u64, address: ArxAddress) {
        self.address_map.insert(id, address);
    }

    /// Get the resolved ArxAddress for a STEP ID.
    pub fn get_address(&self, id: u64) -> Option<&ArxAddress> {
        self.address_map.get(&id)
    }

    /// Clear all data in the registry.
    pub fn clear(&mut self) {
        self.entities.clear();
        self.address_map.clear();
    }

    /// Get the count of registered entities.
    pub fn entity_count(&self) -> usize {
        self.entities.len()
    }

    /// Populate the registry from a lexer.
    pub fn populate_from_lexer(&mut self, mut lexer: crate::ifc::parser::lexer::StepLexer) {
        while let Some(entity) = lexer.next_entity() {
            self.register(entity);
        }
    }

    /// Get all entity IDs that are contained within or aggregated by a specific entity.
    pub fn get_contained(&self, container_id: u64) -> Vec<u64> {
        let mut kids = Vec::new();
        // Look through IfcRelAggregates and IfcRelContainedInSpatialStructure
        for &rel_id in self.get_by_class("IFCRELAGGREGATES") {
            if let Some(rel) = self.get_raw(rel_id) {
                if matches!(rel.params.get(4), Some(Param::Reference(id)) if *id == container_id) {
                    if let Some(Param::List(related)) = rel.params.get(5) {
                        for p in related {
                            if let Param::Reference(id) = p { kids.push(*id); }
                        }
                    }
                }
            }
        }
        for &rel_id in self.get_by_class("IFCRELCONTAINEDINSPATIALSTRUCTURE") {
            if let Some(rel) = self.get_raw(rel_id) {
                if matches!(rel.params.get(5), Some(Param::Reference(id)) if *id == container_id) {
                    if let Some(Param::List(related)) = rel.params.get(4) {
                        for p in related {
                            if let Param::Reference(id) = p { kids.push(*id); }
                        }
                    }
                }
            }
        }
        kids
    }

    /// Find children of a specific class under a parent.
    pub fn find_children_of(&self, parent_id: u64, class: &str) -> Vec<u64> {
        self.get_contained(parent_id)
            .into_iter()
            .filter(|&id| self.get_raw(id).map(|e| e.class == class).unwrap_or(false))
            .collect()
    }
}

impl Default for EntityRegistry {
    fn default() -> Self {
        Self::new()
    }
}

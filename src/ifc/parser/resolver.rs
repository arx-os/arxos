//! IFC Resolver for domain mapping and hierarchy reconstruction.
//! 
//! This module takes raw STEP entities and resolves them into 
//! high-level ArxOS domain objects like Buildings, Floors, and Rooms.

use std::collections::HashMap;
use crate::core::domain::ArxAddress;
use crate::core::{Building, Equipment, EquipmentType, Floor, Position, Room, RoomType, Wing};
use crate::yaml::BuildingData;
use super::lexer::{Param, RawEntity};
use super::registry::EntityRegistry;
use super::geometry::GeometryResolver;
use super::mesh::MeshResolver;
use anyhow::{Result, anyhow};

/// Resolver for mapping IFC entities to ArxOS domain objects.
pub struct IfcResolver<'a> {
    registry: &'a mut EntityRegistry,
    // Building metadata for ArxAddress
    country: String,
    state: String,
    city: String,
}

impl<'a> IfcResolver<'a> {
    /// Create a new resolver with a populated registry.
    pub fn new(registry: &'a mut EntityRegistry) -> Self {
        Self { 
            registry,
            country: "Global".to_string(),
            state: "HQ".to_string(),
            city: "Main".to_string(),
        }
    }

    /// Set building metadata for ArxAddress generation.
    pub fn with_metadata(mut self, country: &str, state: &str, city: &str) -> Self {
        self.country = country.to_string();
        self.state = state.to_string();
        self.city = city.to_string();
        self
    }

    /// Resolve the entire building hierarchy into BuildingData.
    pub fn resolve_all(&mut self) -> Result<BuildingData> {
        let mut building = Building::default();
        let mut equipment_list = Vec::new();

        // 1. Find the root Project entity
        let project_id = self.find_root_entity("IFCPROJECT")
            .ok_or_else(|| anyhow!("No IFCPROJECT found in file"))?;

        // 2. Start traversal from Project -> Site -> Building
        if let Some(building_id) = self.find_building_under(project_id) {
            building = self.resolve_building(building_id)?;
            equipment_list = self.resolve_equipment_under(building_id)?;
            
            // 3. Extract Geolocation from Site
            if let Some(site_id) = self.find_root_entity("IFCSITE") {
                self.resolve_site_metadata(site_id, &mut building)?;
            }

            // 4. Extract AR Anchors (Annotations)
            let mut anchors = self.resolve_ar_anchors()?;
            equipment_list.append(&mut anchors);
        }

        Ok(BuildingData {
            building,
            equipment: equipment_list,
        })
    }

    // --- Traversal Helpers ---

    fn find_root_entity(&self, class_name: &str) -> Option<u64> {
        self.registry.get_by_class(class_name).first().copied()
    }

    fn find_building_under(&self, _project_id: u64) -> Option<u64> {
        // For simplicity in v1, we just find the first IFCBUILDING.
        self.find_root_entity("IFCBUILDING")
    }

    fn resolve_building(&mut self, id: u64) -> Result<Building> {
        let raw = self.registry.get_raw(id).ok_or_else(|| anyhow!("Building entity #{} not found", id))?;
        let name = self.extract_string_param(raw, 2).unwrap_or_else(|| "Unknown Building".to_string());
        
        // Generate ArxAddress for Building
        let addr = ArxAddress::new(&self.country, &self.state, &self.city, &name, "", "", "");
        self.registry.set_address(id, addr);

        let mut building = Building::new(name, "".to_string());
        
        // Resolve Properties
        let mut props = HashMap::new();
        self.resolve_properties(id, &mut props);
        for (k, v) in props {
            building.add_metadata_property(k, v);
        }
        
        let floor_ids = self.find_children_of(id, "IFCBUILDINGSTOREY");
        for floor_id in floor_ids {
            building.floors.push(self.resolve_floor(floor_id, id)?);
        }

        Ok(building)
    }

    fn resolve_floor(&mut self, id: u64, parent_id: u64) -> Result<Floor> {
        let raw = self.registry.get_raw(id).ok_or_else(|| anyhow!("Floor entity #{} not found", id))?;
        let name = self.extract_string_param(raw, 2).unwrap_or_else(|| "Unknown Floor".to_string());
        
        // Generate ArxAddress for Floor
        if let Some(parent_addr) = self.registry.get_address(parent_id) {
            let (_, _, _, building_name, _, _, _) = parent_addr.parts().unwrap_or_default();
            let addr = ArxAddress::new(&self.country, &self.state, &self.city, &building_name, &name, "", "");
            self.registry.set_address(id, addr);
        }

        let mut floor = Floor::new(name, 0); // Defaulting to level 0, can be refined with IfcStorey
        let mut default_wing = Wing::new("Main".to_string());

        for room_id in self.registry.get_contained(id) {
            default_wing.rooms.push(self.resolve_room(room_id, id)?);
        }
        
        floor.wings.push(default_wing);

        // Resolve Properties
        self.resolve_properties(id, &mut floor.properties);

        Ok(floor)
    }

    fn resolve_room(&mut self, id: u64, parent_id: u64) -> Result<Room> {
        let name = {
            let raw = self.registry.get_raw(id).ok_or_else(|| anyhow!("Room entity #{} not found", id))?;
            self.extract_string_param(raw, 2).unwrap_or_else(|| "Unknown Room".to_string())
        };
        
        // Generate ArxAddress for Room
        if let Some(parent_addr) = self.registry.get_address(parent_id) {
            let (_, _, _, building_name, floor_name, _, _) = parent_addr.parts().unwrap_or_default();
            let addr = ArxAddress::new(&self.country, &self.state, &self.city, &building_name, &floor_name, &name, "");
            self.registry.set_address(id, addr);
        }

        let mut room = Room::new(name, RoomType::Other("Space".to_string()));
        let raw = self.registry.get_raw(id).unwrap();

        // Resolve Properties
        self.resolve_properties(id, &mut room.properties);

        // Extract Mesh if available
        let geom_resolver = GeometryResolver::new(self.registry);
        let mesh_resolver = MeshResolver::new(self.registry, &geom_resolver);

        // IfcSpace has ObjectPlacement at Param 2 and Representation at Param 4
        if let Some(Param::Reference(placement_id)) = raw.params.get(2) {
            let transform = geom_resolver.resolve_placement(*placement_id);
            if let Some(Param::Reference(shape_id)) = raw.params.get(4) {
                if let Some(mesh) = mesh_resolver.resolve_mesh_item(*shape_id, &transform) {
                    room.spatial_properties.mesh = Some(mesh);
                }
            }
        }
        
        Ok(room)
    }

    fn resolve_site_metadata(&mut self, id: u64, building: &mut Building) -> Result<()> {
        let raw = self.registry.get_raw(id).ok_or_else(|| anyhow!("Site entity #{} not found", id))?;
        
        // Param 8: RefLatitude
        // Param 9: RefLongitude
        // Param 10: RefElevation
        
        if let Some(Param::List(lat)) = raw.params.get(8) {
            let lat_deg = self.convert_dms_to_decimal(lat).unwrap_or(0.0);
            building.add_metadata_property("geo:latitude".to_string(), lat_deg.to_string());
        }

        if let Some(Param::List(lon)) = raw.params.get(9) {
            let lon_deg = self.convert_dms_to_decimal(lon).unwrap_or(0.0);
            building.add_metadata_property("geo:longitude".to_string(), lon_deg.to_string());
        }

        if let Some(Param::Float(elev)) = raw.params.get(10) {
            building.add_metadata_property("geo:elevation".to_string(), elev.to_string());
        }

        Ok(())
    }

    fn resolve_ar_anchors(&mut self) -> Result<Vec<Equipment>> {
        let mut anchors = Vec::new();
        let geom_resolver = GeometryResolver::new(self.registry);
        let mesh_resolver = MeshResolver::new(self.registry, &geom_resolver);

        for &id in self.registry.get_by_class("IFCANNOTATION") {
            if let Some(raw) = self.registry.get_raw(id) {
                let name = self.extract_string_param(raw, 2).unwrap_or_else(|| format!("Marker_{}", id));
                
                // If it's labeled as a marker or anchor
                if name.to_uppercase().contains("MARKER") || name.to_uppercase().contains("ANCHOR") {
                    let mut eq = Equipment::new(name, "".to_string(), EquipmentType::Other("AR_Anchor".to_string()));
                    
                    if let Some(Param::Reference(placement_id)) = raw.params.get(2) {
                        let transform = geom_resolver.resolve_placement(*placement_id);
                        let origin = transform.transform_point(&nalgebra::Vector3::new(0.0, 0.0, 0.0));
                        eq.position = Position {
                            x: origin.x,
                            y: origin.y,
                            z: origin.z,
                            coordinate_system: "building_local".to_string(),
                        };
                        
                        // Resolve Properties
                        self.resolve_properties(id, &mut eq.properties);
                        
                        if let Some(Param::Reference(shape_id)) = raw.params.get(4) {
                            if let Some(mesh) = mesh_resolver.extract_mesh_from_shape(*shape_id, &transform) {
                                eq.mesh = Some(mesh);
                            }
                        }
                    }
                    
                    anchors.push(eq);
                }
            }
        }
        Ok(anchors)
    }

    fn convert_dms_to_decimal(&self, dms: &[Param]) -> Option<f64> {
        let d = self.extract_float(dms, 0)? as f64;
        let m = self.extract_float(dms, 1)? as f64;
        let s = self.extract_float(dms, 2)? as f64;
        let ms = self.extract_float(dms, 3).unwrap_or(0.0) as f64;

        let sign = if d < 0.0 { -1.0 } else { 1.0 };
        Some(sign * (d.abs() + m / 60.0 + (s + ms / 1_000_000.0) / 3600.0))
    }

    fn extract_float(&self, list: &[Param], index: usize) -> Option<f64> {
        match list.get(index)? {
            Param::Float(f) => Some(*f),
            Param::Integer(i) => Some(*i as f64),
            _ => None,
        }
    }

    fn resolve_equipment_under(&mut self, _building_id: u64) -> Result<Vec<Equipment>> {
        let mut equipment_list = Vec::new();
        
        let classes = [
            "IFCFLOWTERMINAL", "IFCFLOWCONTROLLER", "IFCSENSOR", 
            "IFCAIRTERMINAL", "IFCLIGHTFIXTURE", "IFCBOILER", 
            "IFCCHILLER", "IFCFAN", "IFCPUMP", "IFCVALVE", 
            "IFCLAMP", "IFCOUTLET", "IFCSWITCHINGDEVICE",
            "IFCFIREALARM", "IFCFIRESUPRESSION"
        ];
        
        let geom_resolver = GeometryResolver::new(self.registry);
        let mesh_resolver = MeshResolver::new(self.registry, &geom_resolver);

        for &class in &classes {
            for &id in self.registry.get_by_class(class) {
                let eq_data = if let Some(raw) = self.registry.get_raw(id) {
                    let name = self.extract_string_param(raw, 2).unwrap_or_else(|| format!("{}_{}", class, id));
                    let eq_type = self.map_class_to_type(class);
                    Some((name, eq_type))
                } else {
                    None
                };

                if let Some((name, eq_type)) = eq_data {
                    let mut eq = Equipment::new(name, "".to_string(), eq_type); // Empty path, using address instead

                    // Generate ArxAddress for Equipment (Fixture)
                    if let Some(container_id) = self.find_container_of(id) {
                        if let Some(container_addr) = self.registry.get_address(container_id) {
                            let (country, state, city, building, floor, room, _) = container_addr.parts().unwrap_or_default();
                            eq.address = Some(ArxAddress::new(&country, &state, &city, &building, &floor, &room, &eq.name));
                        }
                    }

                    // Extract Placement and Mesh
                    if let Some(raw) = self.registry.get_raw(id) {
                        if let Some(Param::Reference(placement_id)) = raw.params.get(2) {
                            let transform = geom_resolver.resolve_placement(*placement_id);
                            eq.position = Position {
                                x: transform.matrix[(0, 3)],
                                y: transform.matrix[(1, 3)],
                                z: transform.matrix[(2, 3)],
                                coordinate_system: "building_local".to_string(),
                            };

                            if let Some(Param::Reference(shape_id)) = raw.params.get(4) {
                                if let Some(mesh) = mesh_resolver.resolve_mesh_item(*shape_id, &transform) {
                                    eq.mesh = Some(mesh);
                                }
                            }
                        }
                    }

                    equipment_list.push(eq);
                }
            }
        }

        Ok(equipment_list)
    }

    fn map_class_to_type(&self, class: &str) -> EquipmentType {
        match class {
            "IFCFLOWSEGMENT" | "IFCFLOWFITTING" | "IFCFLOWTERMINAL" | "IFCFLOWMOVINGDEVICE" => EquipmentType::HVAC,
            "IFCCABLESEGMENT" | "IFCCABLEFITTING" | "IFCSWITCHINGDEVICE" | "IFCPROTECTIVEDEVICE" => EquipmentType::Electrical,
            "IFCLAMP" | "IFCLIGHTFIXTURE" => EquipmentType::Other("Lighting".to_string()),
            "IFCVALVE" | "IFCPIPESEGMENT" | "IFCPIPEFITTING" | "IFCSANITARYTERMINAL" => EquipmentType::Plumbing,
            "IFCAUDIOVISUALAPPLIANCE" => EquipmentType::AV,
            "IFCFURNITURE" => EquipmentType::Furniture,
            "IFCFIREALLOWANCE" | "IFCALARM" => EquipmentType::Safety,
            "IFCCOMMUNICATIONSAPPLIANCE" => EquipmentType::Network,
            _ => EquipmentType::Other(class.to_string()),
        }
    }

    // --- Property Resolution ---

    fn resolve_properties(&self, entity_id: u64, out_props: &mut std::collections::HashMap<String, String>) {
        // Properties are linked via IFCRELDEFINESBYPROPERTIES
        // RelatedObjects: Param 4 (List of references)
        // RelatingPropertyDefinition: Param 5 (Reference to Pset)

        for &rel_id in self.registry.get_by_class("IFCRELDEFINESBYPROPERTIES") {
            if let Some(rel_raw) = self.registry.get_raw(rel_id) {
                if let Some(Param::List(related_objects)) = rel_raw.params.get(4) {
                    let is_related = related_objects.iter().any(|p| {
                        matches!(p, Param::Reference(id) if *id == entity_id)
                    });

                    if is_related {
                        if let Some(Param::Reference(pset_id)) = rel_raw.params.get(5) {
                            self.extract_property_set(*pset_id, out_props);
                        }
                    }
                }
            }
        }
    }

    fn extract_property_set(&self, pset_id: u64, out_props: &mut std::collections::HashMap<String, String>) {
        if let Some(pset_raw) = self.registry.get_raw(pset_id) {
            if pset_raw.class == "IFCPROPERTYSET" {
                let pset_name = self.extract_string_param(pset_raw, 2).unwrap_or_else(|| "Pset_Unknown".to_string());
                
                // HasProperties: Param 4 (List of references)
                if let Some(Param::List(properties)) = pset_raw.params.get(4) {
                    for prop_param in properties {
                        if let Param::Reference(prop_id) = prop_param {
                            self.extract_single_property(*prop_id, &pset_name, out_props);
                        }
                    }
                }
            }
        }
    }

    fn extract_single_property(&self, prop_id: u64, pset_name: &str, out_props: &mut std::collections::HashMap<String, String>) {
        if let Some(prop_raw) = self.registry.get_raw(prop_id) {
            if prop_raw.class == "IFCPROPERTYSINGLEVALUE" {
                let name = self.extract_string_param(prop_raw, 0).unwrap_or_else(|| "Unknown".to_string());
                // NominalValue: Param 2 (Typed value or simple value)
                if let Some(value) = self.extract_value_param(&prop_raw.params, 2) {
                    let key = format!("{}:{}", pset_name, name);
                    out_props.insert(key, value);
                }
            }
        }
    }

    fn extract_value_param(&self, params: &[Param], index: usize) -> Option<String> {
        match params.get(index)? {
            Param::String(s) => Some(s.clone()),
            Param::Float(f) => Some(f.to_string()),
            Param::Integer(i) => Some(i.to_string()),
            Param::Boolean(b) => Some(b.to_string()),
            Param::Typed(_type_name, val) => {
                // Nested value in IfcLabel, IfcText, etc.
                self.extract_typed_value(val)
            }
            _ => None,
        }
    }

    fn extract_typed_value(&self, val: &Param) -> Option<String> {
        match val {
            Param::String(s) => Some(s.clone()),
            Param::Float(f) => Some(f.to_string()),
            Param::Integer(i) => Some(i.to_string()),
            Param::Boolean(b) => Some(b.to_string()),
            _ => None,
        }
    }

    // --- Relationship Discovery ---

    fn find_container_of(&self, entity_id: u64) -> Option<u64> {
        // Look for IFCRELCONTAINEDINSPATIALSTRUCTURE where RelatedElements contains entity_id
        for &id in self.registry.get_by_class("IFCRELCONTAINEDINSPATIALSTRUCTURE") {
            if let Some(entity) = self.registry.get_raw(id) {
                // Param 4: RelatedElements (List of References)
                if let Some(Param::List(elements)) = entity.params.get(4) {
                    for item in elements {
                        if let Param::Reference(e_id) = item {
                            if *e_id == entity_id {
                                // Param 5: RelatingStructure (The Container)
                                if let Some(Param::Reference(container_id)) = entity.params.get(5) {
                                    return Some(*container_id);
                                }
                            }
                        }
                    }
                }
            }
        }
        None
    }

    fn find_children_of(&self, parent_id: u64, child_class: &str) -> Vec<u64> {
        let mut children = Vec::new();
        // Look for IFCRELAGGREGATES where RelatingObject is the parent
        // then follow RelatedObjects list.
        for &id in self.registry.get_by_class("IFCRELAGGREGATES") {
            if let Some(entity) = self.registry.get_raw(id) {
                // Param 4 is usually the parent (RelatingObject)
                if let Some(Param::Reference(p_id)) = entity.params.get(4) {
                    if *p_id == parent_id {
                        // Param 5 is the list of children (RelatedObjects)
                        if let Some(Param::List(list)) = entity.params.get(5) {
                            for item in list {
                                if let Param::Reference(c_id) = item {
                                    if let Some(c_entity) = self.registry.get_raw(*c_id) {
                                        if c_entity.class == child_class {
                                            children.push(*c_id);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        children
    }

    // --- Data Extraction Helpers ---

    fn extract_string_param(&self, entity: &RawEntity, index: usize) -> Option<String> {
        match entity.params.get(index)? {
            Param::String(s) => Some(s.clone()),
            _ => None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ifc::parser::registry::EntityRegistry;

    #[test]
    fn test_extract_string_param() {
        let mut registry = EntityRegistry::new();
        let resolver = IfcResolver::new(&mut registry);
        
        let entity = RawEntity {
            id: 1,
            class: "TEST".to_string(),
            params: vec![Param::String("Hello".to_string())]
        };
        
        assert_eq!(resolver.extract_string_param(&entity, 0), Some("Hello".to_string()));
        assert_eq!(resolver.extract_string_param(&entity, 1), None);
    }
}

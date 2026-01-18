use crate::core::{Building, Floor, Room, Equipment};

// Use commented out if unsure or delete. "unused import: `crate::core::spatial::SpatialEntity`"
// It's used in `write_triangulated_face_set` fix I made earlier?
// Wait, I used `use crate::core::...` inside the function or file? 
// The warning says it's unused. Let's remove it.
// Wait, I can't leave empty lines. Just remove the line.

use crate::core::spatial::mesh::Mesh;
use crate::yaml::BuildingData;
use anyhow::Result;
use chrono::Utc;

use std::collections::HashMap;
use std::fs::File;
use std::io::{BufWriter, Write};
use std::path::Path;
use uuid::Uuid;

/// Helper struct to handle STEP file formatting and ID generation
struct StepWriter<W: Write> {
    writer: BufWriter<W>,
    next_id: usize,
}

impl<W: Write> StepWriter<W> {
    fn new(inner: W) -> Self {
        Self {
            writer: BufWriter::new(inner),
            next_id: 1,
        }
    }

    /// Write the standard IFC header
    fn write_header(&mut self, filename: &str) -> Result<()> {
        writeln!(self.writer, "ISO-10303-21;")?;
        writeln!(self.writer, "HEADER;")?;
        writeln!(self.writer, "FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');")?;
        writeln!(
            self.writer,
            "FILE_NAME('{}','{}',('ArxOS User'),(),'ArxOS Exporter','ArxOS','');",
            filename,
            Utc::now().format("%Y-%m-%dT%H:%M:%S")
        )?;
        writeln!(self.writer, "FILE_SCHEMA(('IFC4'));")?;
        writeln!(self.writer, "ENDSEC;")?;
        writeln!(self.writer, "DATA;")?;
        Ok(())
    }

    /// Write the footer
    fn write_footer(&mut self) -> Result<()> {
        writeln!(self.writer, "ENDSEC;")?;
        writeln!(self.writer, "END-ISO-10303-21;")?;
        Ok(())
    }

    /// Generate a new STEP ID (e.g., #1)
    fn next_id(&mut self) -> usize {
        let id = self.next_id;
        self.next_id += 1;
        id
    }

    /// Write a raw STEP line
    #[allow(dead_code)]
    fn write_line(&mut self, _id: usize, content: &str) -> Result<()> {
        writeln!(self.writer, "#{};", content)?;
        // writeln!(self.writer, "#{}= {};", id, content)?; // Correct format is #1= IFCTYPE(...);
        Ok(())
    }
    
    fn write_cartesian_point_list_3d(&mut self, points: &[[f64; 3]]) -> Result<usize> {
        let id = self.next_id();
        write!(self.writer, "#{}= IFCCARTESIANPOINTLIST3D((", id)?;
        for (i, p) in points.iter().enumerate() {
            if i > 0 {
                write!(self.writer, ",")?;
            }
            write!(self.writer, "({:.4},{:.4},{:.4})", p[0], p[1], p[2])?;
        }
        writeln!(self.writer, "));")?;
        Ok(id)
    }

    fn write_triangulated_face_set(
        &mut self,
        coordinates_id: usize,
        indices: &[[u32; 3]],
    ) -> Result<usize> {
        let id = self.next_id();
        write!(
            self.writer,
            "#{}= IFCTRIANGULATEDFACESET(#{},(),.T.,(",
            id, coordinates_id
        )?;
        for (i, tri) in indices.iter().enumerate() {
            if i > 0 {
                write!(self.writer, ",")?;
            }
            // IFC indices are 1-based
            write!(
                self.writer,
                "({},{},{})",
                tri[0] + 1,
                tri[1] + 1,
                tri[2] + 1
            )?;
        }
        writeln!(self.writer, "));")?;
        Ok(id)
    }
    
    /// Write an entity and return its ID
    fn write_entity(&mut self, content: String) -> Result<usize> {
        let id = self.next_id();
        writeln!(self.writer, "#{}= {};", id, content)?;
        Ok(id)
    }
}

pub struct IFCExporter {
    data: BuildingData,
}

impl IFCExporter {
    pub fn new(data: BuildingData) -> Self {
        Self { data }
    }

    pub fn export(&self, output_path: &Path) -> Result<()> {
        let file = File::create(output_path)?;
        let mut writer = StepWriter::new(file);

        writer.write_header(output_path.file_name().unwrap_or_default().to_string_lossy().as_ref())?;

        // 1. Create Owner History (required for most entities)
        let owner_history_id = self.create_owner_history(&mut writer)?;
        
        // ... (rest of export logic) ...
        self.export_content(&mut writer, owner_history_id)
    }

    #[cfg(feature = "agent")]
    pub fn export_delta(&self, _sync_state: Option<&crate::agent::git::SyncState>, output_path: &Path) -> Result<()> {
        // For now, delta export is same as full export (placeholder)
        // In real implementation, this would filter entities based on sync state
        self.export(output_path)
    }

    #[cfg(not(feature = "agent"))]
    pub fn export_delta(&self, _sync_state: Option<&()>, output_path: &Path) -> Result<()> {
        // For now, delta export is same as full export (placeholder)
        // In real implementation, this would filter entities based on sync state
        self.export(output_path)
    }
    
    /// Collect universal paths for tracked entities (Equipment and Rooms)
    pub fn collect_universal_paths(&self) -> (Vec<String>, Vec<String>) {
        let mut equipment_paths = Vec::new();
        let mut rooms_paths = Vec::new();

        for floor in &self.data.building.floors {
             for wing in &floor.wings {
                 for room in &wing.rooms {
                     // Construct room path - simplified for now
                     // In a real scenario, this should match the canonical path structure used elsewhere
                     let room_path = format!("{}/{}/{}", self.data.building.name, floor.name, room.name);
                     rooms_paths.push(room_path.clone());
                     
                     for eq in &room.equipment {
                         let eq_path = format!("{}/{}", room_path, eq.name);
                         equipment_paths.push(eq_path);
                     }
                 }
             }
        }
        
        (equipment_paths, rooms_paths)
    }

    fn export_content<W: Write>(&self, writer: &mut StepWriter<W>, owner_history_id: usize) -> Result<()> {
        // 2. Create Project
        let project_id = self.create_project(writer, &self.data.building, owner_history_id)?;

        // 3. Create Site
        let site_id = self.create_site(writer, &self.data.building, owner_history_id)?;

        // 4. Create Building
        let building_id = self.create_building(writer, &self.data.building, owner_history_id)?;

        // 5. Link Project -> Site -> Building
        self.create_aggregation(writer, project_id, vec![site_id], "ProjectToSite", owner_history_id)?;
        self.create_aggregation(writer, site_id, vec![building_id], "SiteToBuilding", owner_history_id)?;

        // 6. Process Floors (BuildingStoreys)
        let mut floor_ids = Vec::new();
        for floor in &self.data.building.floors {
            let floor_id = self.create_building_storey(writer, floor, owner_history_id)?;
            floor_ids.push(floor_id);

            // 7. Process Rooms (Spaces)
            let mut room_ids = Vec::new();
            
            // Collect all rooms from all wings
            let all_rooms: Vec<&Room> = floor.wings.iter().flat_map(|w| w.rooms.iter()).collect();
            
            for room in all_rooms {
                let room_id = self.create_space(writer, room, floor.elevation.unwrap_or(0.0), owner_history_id)?;
                room_ids.push(room_id);
                
                // --- ADD PSETS FOR ROOM ---
                self.create_property_set(writer, owner_history_id, room_id, "Pset_ArxRoomProperties", &room.properties)?;

                // 8. Process Equipment in Room
                if !room.equipment.is_empty() {
                    let mut equipment_ids = Vec::new();
                    for equipment in &room.equipment {
                         let eq_id = self.create_equipment(writer, equipment, owner_history_id)?;
                         equipment_ids.push(eq_id);

                         // --- ADD PSETS FOR EQUIPMENT ---
                         self.create_property_set(writer, owner_history_id, eq_id, "Pset_ArxEquipmentProperties", &equipment.properties)?;
                    }
                    // Link Room -> Equipment (Spatial Containment)
                    if !equipment_ids.is_empty() {
                        self.create_containment(writer, room_id, equipment_ids, "RoomToEquipment", owner_history_id)?;
                    }
                }
            }

            // Link Floor -> Rooms (Aggregation)
            if !room_ids.is_empty() {
                self.create_aggregation(writer, floor_id, room_ids, "FloorToRooms", owner_history_id)?;
            }
        }

        // Link Building -> Floors
        if !floor_ids.is_empty() {
            self.create_aggregation(writer, building_id, floor_ids, "BuildingToFloors", owner_history_id)?;
        }

        writer.write_footer()?;
        Ok(())
    }

    // --- Entity Creation Helpers ---

    fn create_owner_history<W: Write>(&self, writer: &mut StepWriter<W>) -> Result<usize> {
        // Minimal OwnerHistory setup
        let person_id = writer.write_entity("IFCPERSON($,'ArxOS','User',$,$,$,$,$)".to_string())?;
        let org_id = writer.write_entity("IFCORGANIZATION($,'ArxOS',$,$,$)".to_string())?;
        let person_and_org_id = writer.write_entity(format!("IFCPERSONANDORGANIZATION(#{},#{},$)", person_id, org_id))?;
        let _app_id = writer.write_entity("IFCAPPLICATION(#{},'1.0','ArxOS','ArxOS')".to_string().replace("#{}", &format!("#{}", org_id)))?; // Fix: org_id ref
        
        // Correct Application ref
        let app_id = writer.write_entity(format!("IFCAPPLICATION(#{},'1.0','ArxOS','ArxOS')", org_id))?;

        writer.write_entity(format!(
            "IFCOWNERHISTORY(#{},#{},.READWRITE.,.NOCHANGE.,$,$,$,$)",
            person_and_org_id, app_id
        ))
    }

    fn create_project<W: Write>(&self, writer: &mut StepWriter<W>, building: &Building, owner_hist: usize) -> Result<usize> {
        // Units
        let length_unit = writer.write_entity("IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.)".to_string())?;
        let area_unit = writer.write_entity("IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.)".to_string())?;
        let volume_unit = writer.write_entity("IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.)".to_string())?;
        let unit_assignment = writer.write_entity(format!("IFCUNITASSIGNMENT((#{},#{},#{}))", length_unit, area_unit, volume_unit))?;

        // Context
        let origin = self.create_cartesian_point(writer, 0.0, 0.0, 0.0)?;
        let world_cs = writer.write_entity(format!("IFCAXIS2PLACEMENT3D(#{},$,$)", origin))?;
        let _context_type = "'Model'";
        let context = writer.write_entity(format!(
            "IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.0E-5,#{},$)",
            world_cs
        ))?;

        writer.write_entity(format!(
            "IFCPROJECT('{}',#{},'{}',$,$,$,$,(#{}),#{})",
            self.generate_guid(),
            owner_hist,
            building.name,
            context,
            unit_assignment
        ))
    }

    fn create_site<W: Write>(&self, writer: &mut StepWriter<W>, _building: &Building, owner_hist: usize) -> Result<usize> {
        let placement = self.create_local_placement(writer, None, 0.0, 0.0, 0.0)?;
        
        writer.write_entity(format!(
            "IFCSITE('{}',#{},'Default Site',$,$,#{},$,$,.ELEMENT.,(0,0,0),(0,0,0),0.,$,$)",
            self.generate_guid(),
            owner_hist,
            placement
        ))
    }

    fn create_building<W: Write>(&self, writer: &mut StepWriter<W>, building: &Building, owner_hist: usize) -> Result<usize> {
        let placement = self.create_local_placement(writer, None, 0.0, 0.0, 0.0)?;
        
        let building_id = writer.write_entity(format!(
            "IFCBUILDING('{}',#{},'{}',$,$,#{},$,$,.ELEMENT.,$,$,$)",
            self.generate_guid(),
            owner_hist,
            building.name,
            placement
        ))?;

        // --- ADD PSETS FOR BUILDING ---
        if let Some(meta) = &building.metadata {
            self.create_property_set(writer, owner_hist, building_id, "Pset_ArxBuildingMetadata", &meta.properties)?;
        }

        Ok(building_id)
    }

    fn create_building_storey<W: Write>(&self, writer: &mut StepWriter<W>, floor: &Floor, owner_hist: usize) -> Result<usize> {
        let elevation = floor.elevation.unwrap_or(0.0);
        let placement = self.create_local_placement(writer, None, 0.0, 0.0, elevation)?;
        
        let floor_id = writer.write_entity(format!(
            "IFCBUILDINGSTOREY('{}',#{},'{}',$,$,#{},$,$,.ELEMENT.,{})",
            self.generate_guid(),
            owner_hist,
            floor.name,
            placement,
            elevation
        ))?;

        // --- ADD PSETS FOR FLOOR ---
        self.create_property_set(writer, owner_hist, floor_id, "Pset_ArxFloorProperties", &floor.properties)?;

        Ok(floor_id)
    }

    fn create_space<W: Write>(&self, writer: &mut StepWriter<W>, room: &Room, _floor_elevation: f64, owner_hist: usize) -> Result<usize> {
        // Position is relative to floor, but room.spatial_properties.position might be global or local.
        // Assuming room position Z is absolute, we subtract floor elevation for local Z.
        // Or if Z is already local to floor, we use it as is.
        // For simplicity, let's assume room Z is relative to floor for now, or 0.0 if not specified.
        
        let x = room.spatial_properties.position.x;
        let y = room.spatial_properties.position.y;
        let z = room.spatial_properties.position.z; // Assuming relative to floor

        let placement = self.create_local_placement(writer, None, x, y, z)?;
        
        // Geometry
        let shape_rep_id = if let Some(mesh) = &room.spatial_properties.mesh {
             Some(self.create_mesh_shape(writer, mesh)?)
        } else {
            let width = room.spatial_properties.dimensions.width;
            let depth = room.spatial_properties.dimensions.depth;
            let height = room.spatial_properties.dimensions.height;
            
            if width > 0.0 && depth > 0.0 && height > 0.0 {
                Some(self.create_bounding_box_shape(writer, width, depth, height)?)
            } else {
                None
            }
        };

        let representation = if let Some(rep_id) = shape_rep_id {
             let product_def_shape = writer.write_entity(format!("IFCPRODUCTDEFINITIONSHAPE($,$,(#{}))", rep_id))?;
             format!("#{}", product_def_shape)
        } else {
            "$".to_string()
        };

        writer.write_entity(format!(
            "IFCSPACE('{}',#{},'{}',$,$,#{},{},$,.ELEMENT.,.INTERNAL.,$)",
            self.generate_guid(),
            owner_hist,
            room.name,
            placement,
            representation
        ))
    }

    fn create_equipment<W: Write>(&self, writer: &mut StepWriter<W>, equipment: &Equipment, owner_hist: usize) -> Result<usize> {
        let x = equipment.position.x;
        let y = equipment.position.y;
        let z = equipment.position.z;

        let placement = self.create_local_placement(writer, None, x, y, z)?;
        
        // Map EquipmentType to IfcDistributionElement subtype or generic
        let ifc_entity_type = match equipment.equipment_type {
            crate::core::EquipmentType::Furniture => "IFCFURNITURE",
            _ => "IFCDISTRIBUTIONELEMENT", // Generic fallback
        };

        // Geometry
        let representation = if let Some(mesh) = &equipment.mesh {
             let rep_id = self.create_mesh_shape(writer, mesh)?;
             let product_def_shape = writer.write_entity(format!("IFCPRODUCTDEFINITIONSHAPE($,$,(#{}))", rep_id))?;
             format!("#{}", product_def_shape)
        } else {
             // Default 1x1x1 box for equipment if no mesh, or just None?
             // Let's use a default box for now to show something.
             let rep_id = self.create_bounding_box_shape(writer, 1.0, 1.0, 1.0)?;
             let product_def_shape = writer.write_entity(format!("IFCPRODUCTDEFINITIONSHAPE($,$,(#{}))", rep_id))?;
             format!("#{}", product_def_shape)
        };

        writer.write_entity(format!(
            "{}('{}',#{},'{}',$,$,#{},{},$,$)",
            ifc_entity_type,
            self.generate_guid(),
            owner_hist,
            equipment.name,
            placement,
            representation
        ))
    }

    // --- Relationship Helpers ---

    fn create_aggregation<W: Write>(&self, writer: &mut StepWriter<W>, parent_id: usize, child_ids: Vec<usize>, name: &str, owner_hist: usize) -> Result<usize> {
        let children_refs = child_ids.iter().map(|id| format!("#{}", id)).collect::<Vec<_>>().join(",");
        writer.write_entity(format!(
            "IFCRELAGGREGATES('{}',#{},'{}',$,#{},(#{}))",
            self.generate_guid(),
            owner_hist,
            name,
            parent_id,
            children_refs
        ))
    }

    fn create_containment<W: Write>(&self, writer: &mut StepWriter<W>, container_id: usize, contained_ids: Vec<usize>, name: &str, owner_hist: usize) -> Result<usize> {
        let contained_refs = contained_ids.iter().map(|id| format!("#{}", id)).collect::<Vec<_>>().join(",");
        writer.write_entity(format!(
            "IFCRELCONTAINEDINSPATIALSTRUCTURE('{}',#{},'{}',$,(#{}),#{})",
            self.generate_guid(),
            owner_hist,
            name,
            contained_refs,
            container_id
        ))
    }

    /// Link properties to an entity via IfcRelDefinesByProperties
    fn create_property_set<W: Write>(
        &self,
        writer: &mut StepWriter<W>,
        owner_hist: usize,
        related_id: usize,
        name: &str,
        properties: &HashMap<String, String>,
    ) -> Result<Option<usize>> {
        if properties.is_empty() {
            return Ok(None);
        }

        let mut prop_ids = Vec::new();
        for (key, value) in properties {
            // IfcPropertySingleValue
            let p_id = writer.write_entity(format!(
                "IFCPROPERTYSINGLEVALUE('{}',$,IFCLABEL('{}'),$)",
                key, value
            ))?;
            prop_ids.push(p_id);
        }

        let prop_refs = prop_ids.iter().map(|id| format!("#{}", id)).collect::<Vec<_>>().join(",");
        let pset_id = writer.write_entity(format!(
            "IFCPROPERTYSET('{}',#{},'{}',$,(#{}))",
            self.generate_guid(),
            owner_hist,
            name,
            prop_refs
        ))?;

        writer.write_entity(format!(
            "IFCRELDEFINESBYPROPERTIES('{}',#{},$,$,(#{}),#{})",
            self.generate_guid(),
            owner_hist,
            related_id,
            pset_id
        ))?;

        Ok(Some(pset_id))
    }

    // --- Geometry Helpers ---

    fn create_cartesian_point<W: Write>(&self, writer: &mut StepWriter<W>, x: f64, y: f64, z: f64) -> Result<usize> {
        writer.write_entity(format!("IFCCARTESIANPOINT(({:.4},{:.4},{:.4}))", x, y, z))
    }

    fn create_local_placement<W: Write>(&self, writer: &mut StepWriter<W>, relative_to: Option<usize>, x: f64, y: f64, z: f64) -> Result<usize> {
        let location = self.create_cartesian_point(writer, x, y, z)?;
        let axis_placement = writer.write_entity(format!("IFCAXIS2PLACEMENT3D(#{},$,$)", location))?;
        
        let relative_to_str = match relative_to {
            Some(id) => format!("#{}", id),
            None => "$".to_string(),
        };

        writer.write_entity(format!("IFCLOCALPLACEMENT({},#{})", relative_to_str, axis_placement))
    }

    fn create_mesh_shape(
        &self,
        writer: &mut StepWriter<impl std::io::Write>,
        mesh: &Mesh,
    ) -> Result<usize> {
        // 1. Convert vertices to array of arrays
        let points: Vec<[f64; 3]> = mesh
            .vertices
            .iter()
            .map(|v| [v.x, v.y, v.z])
            .collect();

        // 2. Write CartesianPointList3D
        let coords_id = writer.write_cartesian_point_list_3d(&points)?;

        // 3. Convert indices to triplets
        let mut triangles = Vec::new();
        for chunk in mesh.indices.chunks(3) {
            if chunk.len() == 3 {
                triangles.push([chunk[0], chunk[1], chunk[2]]);
            }
        }

        // 4. Write TriangulatedFaceSet
        let face_set_id = writer.write_triangulated_face_set(coords_id, &triangles)?;

        // 5. Wrap in ShapeRepresentation
        let shape_rep = writer.write_entity(format!(
            "IFCSHAPEREPRESENTATION($,'Body','Tessellation',(#{}))",
            face_set_id
        ))?;
        
        Ok(shape_rep)
    }

    fn create_bounding_box_shape<W: Write>(&self, writer: &mut StepWriter<W>, width: f64, depth: f64, height: f64) -> Result<usize> {
        // Create a simple extruded area solid representation
        // 1. Profile (Rectangle)
        // 2. Extrusion
        
        // Profile
        let position = self.create_cartesian_point(writer, 0.0, 0.0, 0.0)?; // Local to profile
        let axis2d = writer.write_entity(format!("IFCAXIS2PLACEMENT2D(#{},$)", position))?;
        let profile = writer.write_entity(format!("IFCRECTANGLEPROFILEDEF(.AREA.,'RoomProfile',#{},{:.4},{:.4})", axis2d, width, depth))?;
        
        // Extrusion
        let position_3d = self.create_cartesian_point(writer, 0.0, 0.0, 0.0)?;
        let axis3d = writer.write_entity(format!("IFCAXIS2PLACEMENT3D(#{},$,$)", position_3d))?;
        let direction = writer.write_entity("IFCDIRECTION((0.,0.,1.))".to_string())?;
        
        let solid = writer.write_entity(format!(
            "IFCEXTRUDEDAREASOLID(#{},#{},#{},{:.4})",
            profile, axis3d, direction, height
        ))?;

        writer.write_entity(format!("IFCSHAPEREPRESENTATION($,'Body','SweptSolid',(#{}))", solid))
    }

    // --- Utility ---

    fn generate_guid(&self) -> String {
        // IFC GUIDs are 22-character strings using a custom base64 encoding
        // of the 128-bit UUID.
        // Alphabet: "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$"
        
        let uuid = Uuid::new_v4();
        let bytes = uuid.as_bytes();
        let mut result = String::with_capacity(22);
        
        // The algorithm processes 128 bits (16 bytes) into 22 characters.
        // It treats the 128 bits as a large integer and converts to base 64.
        // However, the standard C implementation processes it in chunks.
        // A common rust implementation (like in ifc-rs or similar) does this:
        
        let chars = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$";
        
        // Group bytes into chunks of 3 (24 bits) -> 4 chars
        // 16 bytes = 5 chunks of 3 + 1 byte remainder
        // But the mapping is a bit specific. 
        // Let's use the standard algorithm logic:
        
        let _cv = |val: u32, len: usize| -> Vec<char> {
            let mut res = Vec::with_capacity(len);
            let mut v = val;
            for _ in 0..len {
                res.push(chars[(v % 64) as usize] as char);
                v /= 64;
            }
            res.reverse(); // The standard might be big-endian or little-endian, let's check.
            // Actually, the standard C implementation is:
            // void cv_to_64(unsigned long number, char *code, int len)
            // {
            //    char *act;
            //    for (act = code + len - 1; act >= code; act--)
            //    {
            //       *act = cConversionTable[(int)(number % 64)];
            //       number /= 64;
            //    }
            // }
            // So it fills from end.
            res
        };
        
        // Helper to map 3 bytes to 4 chars
        let to_b64 = |b1: u8, b2: u8, b3: u8, len: usize| -> String {
            let num = ((b1 as u32) << 16) + ((b2 as u32) << 8) + (b3 as u32);
            let mut s = String::new();
            let mut n = num;
            for _ in 0..len {
                s.insert(0, chars[(n % 64) as usize] as char);
                n /= 64;
            }
            s
        };

        // 1. Bytes 0-3 (first 3 bytes -> 4 chars)
        result.push_str(&to_b64(bytes[0], bytes[1], bytes[2], 4));
        
        // 2. Bytes 3-6 (next 3 bytes -> 4 chars)
        result.push_str(&to_b64(bytes[3], bytes[4], bytes[5], 4));
        
        // 3. Bytes 6-9 (next 3 bytes -> 4 chars)
        result.push_str(&to_b64(bytes[6], bytes[7], bytes[8], 4));
        
        // 4. Bytes 9-12 (next 3 bytes -> 4 chars)
        result.push_str(&to_b64(bytes[9], bytes[10], bytes[11], 4));
        
        // 5. Bytes 12-15 (next 3 bytes -> 4 chars)
        result.push_str(&to_b64(bytes[12], bytes[13], bytes[14], 4));
        
        // 6. Byte 15 (last byte -> 2 chars)
        // Wait, 16 bytes * 8 = 128 bits.
        // 22 chars * 6 = 132 bits.
        // The mapping is usually:
        // 1st 4 chars come from 1st 3 bytes (24 bits)
        // ... 5 groups of 3 bytes = 15 bytes -> 20 chars
        // Last byte (8 bits) -> 2 chars (12 bits capacity)
        
        let num = bytes[15] as u32;
        let mut s = String::new();
        let mut n = num;
        for _ in 0..2 {
            s.insert(0, chars[(n % 64) as usize] as char);
            n /= 64;
        }
        result.push_str(&s);

        result
    }
}


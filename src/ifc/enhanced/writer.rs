//! IFC file writing functionality

use super::types::EnhancedIFCParser;
use crate::error::{ArxError, ArxResult};
use crate::spatial::SpatialEntity;
use log::info;
use std::fs::File;
use std::io::Write;

impl EnhancedIFCParser {
    /// Write IFC entities from SpatialEntity data (for terminal 3D → IFC sync)
    pub fn write_spatial_entities_to_ifc(
        &self,
        entities: &[Box<dyn SpatialEntity>],
        output_path: &str,
    ) -> ArxResult<()> {
        let mut file = File::create(output_path).map_err(|e| {
            ArxError::io_error("Failed to create IFC output file")
                .with_file_path(output_path)
                .with_debug_info(format!("IO Error: {}", e))
        })?;

        // Write IFC header
        self.write_ifc_header(&mut file)?;

        // Write coordinate system definitions
        self.write_coordinate_systems(&mut file)?;

        // Write spatial entities
        for entity in entities {
            self.write_spatial_entity(&mut file, entity.as_ref())?;
        }

        // Write IFC footer
        self.write_ifc_footer(&mut file)?;

        info!(
            "Successfully wrote {} spatial entities to IFC file: {}",
            entities.len(),
            output_path
        );
        Ok(())
    }

    /// Write IFC file header
    fn write_ifc_header(&self, file: &mut File) -> ArxResult<()> {
        self.write_line(file, "ISO-10303-21;")?;
        self.write_line(file, "HEADER;")?;
        self.write_line(
            file,
            "FILE_DESCRIPTION(('ArxOS Generated IFC File'),'2;1');",
        )?;
        self.write_line(file, "FILE_NAME('arxos_generated.ifc','2024-01-01T00:00:00',('ArxOS'),('ArxOS Terminal 3D Sync'),'ArxOS','ArxOS','');")?;
        self.write_line(file, "FILE_SCHEMA(('IFC4'));")?;
        self.write_line(file, "ENDSEC;")?;
        self.write_line(file, "")?;
        self.write_line(file, "DATA;")?;
        Ok(())
    }

    /// Write coordinate system definitions
    fn write_coordinate_systems(&self, file: &mut File) -> ArxResult<()> {
        // Write global coordinate system
        self.write_line(file, "#1=IFCCARTESIANPOINT((0.,0.,0.));")?;
        self.write_line(file, "#2=IFCDIRECTION((0.,0.,1.));")?;
        self.write_line(file, "#3=IFCDIRECTION((1.,0.,0.));")?;
        self.write_line(file, "#4=IFCAXIS2PLACEMENT3D(#1,#2,#3);")?;
        self.write_line(file, "#5=IFCLOCALPLACEMENT($,#4);")?;
        self.write_line(file, "")?;
        Ok(())
    }

    /// Write a single spatial entity to IFC format
    fn write_spatial_entity(&self, file: &mut File, entity: &dyn SpatialEntity) -> ArxResult<()> {
        // Generate unique ID for this entity
        let entity_id = self.generate_entity_id(entity.id());

        // Write coordinate point
        let point_id = entity_id + 1;
        self.write_line(
            file,
            &format!(
                "#{}={}(({:.3},{:.3},{:.3}));",
                point_id,
                "IFCCARTESIANPOINT",
                entity.position().x,
                entity.position().y,
                entity.position().z
            ),
        )?;

        // Write local placement
        let placement_id = entity_id + 2;
        self.write_line(
            file,
            &format!("#{}={}(#{});", placement_id, "IFCLOCALPLACEMENT", point_id),
        )?;

        // Write entity based on type
        match entity.entity_type() {
            "IFCSPACE" => self.write_ifc_space(file, entity, entity_id, placement_id)?,
            "IFCROOM" => self.write_ifc_room(file, entity, entity_id, placement_id)?,
            "IFCAIRTERMINAL" => {
                self.write_ifc_air_terminal(file, entity, entity_id, placement_id)?
            }
            "IFCLIGHTFIXTURE" => {
                self.write_ifc_light_fixture(file, entity, entity_id, placement_id)?
            }
            "IFCFAN" => self.write_ifc_fan(file, entity, entity_id, placement_id)?,
            "IFCPUMP" => self.write_ifc_pump(file, entity, entity_id, placement_id)?,
            _ => self.write_generic_equipment(file, entity, entity_id, placement_id)?,
        }

        self.write_line(file, "")?;
        Ok(())
    }

    /// Generate unique entity ID from string hash
    fn generate_entity_id(&self, id_str: &str) -> u32 {
        let hash = self.hash_string(id_str);
        (hash % 1000000) as u32 + 1000 // Start from 1000 to avoid conflicts
    }

    /// Write IFCSPACE entity
    fn write_ifc_space(
        &self,
        file: &mut File,
        entity: &dyn SpatialEntity,
        entity_id: u32,
        placement_id: u32,
    ) -> ArxResult<()> {
        self.write_line(
            file,
            &format!(
                "#{}={}('{}','{}',$,#{});",
                entity_id, "IFCSPACE", entity.id(), entity.name(), placement_id
            ),
        )?;
        Ok(())
    }

    /// Write IFCROOM entity
    fn write_ifc_room(
        &self,
        file: &mut File,
        entity: &dyn SpatialEntity,
        entity_id: u32,
        placement_id: u32,
    ) -> ArxResult<()> {
        self.write_line(
            file,
            &format!(
                "#{}={}('{}','{}',$,#{});",
                entity_id, "IFCROOM", entity.id(), entity.name(), placement_id
            ),
        )?;
        Ok(())
    }

    /// Write IFCAIRTERMINAL entity
    fn write_ifc_air_terminal(
        &self,
        file: &mut File,
        entity: &dyn SpatialEntity,
        entity_id: u32,
        placement_id: u32,
    ) -> ArxResult<()> {
        self.write_line(
            file,
            &format!(
                "#{}={}('{}','{}',$,#{});",
                entity_id, "IFCAIRTERMINAL", entity.id(), entity.name(), placement_id
            ),
        )?;
        Ok(())
    }

    /// Write IFCLIGHTFIXTURE entity
    fn write_ifc_light_fixture(
        &self,
        file: &mut File,
        entity: &dyn SpatialEntity,
        entity_id: u32,
        placement_id: u32,
    ) -> ArxResult<()> {
        self.write_line(
            file,
            &format!(
                "#{}={}('{}','{}',$,#{});",
                entity_id, "IFCLIGHTFIXTURE", entity.id(), entity.name(), placement_id
            ),
        )?;
        Ok(())
    }

    /// Write IFCFAN entity
    fn write_ifc_fan(
        &self,
        file: &mut File,
        entity: &dyn SpatialEntity,
        entity_id: u32,
        placement_id: u32,
    ) -> ArxResult<()> {
        self.write_line(
            file,
            &format!(
                "#{}={}('{}','{}',$,#{});",
                entity_id, "IFCFAN", entity.id(), entity.name(), placement_id
            ),
        )?;
        Ok(())
    }

    /// Write IFCPUMP entity
    fn write_ifc_pump(
        &self,
        file: &mut File,
        entity: &dyn SpatialEntity,
        entity_id: u32,
        placement_id: u32,
    ) -> ArxResult<()> {
        self.write_line(
            file,
            &format!(
                "#{}={}('{}','{}',$,#{});",
                entity_id, "IFCPUMP", entity.id(), entity.name(), placement_id
            ),
        )?;
        Ok(())
    }

    /// Write generic equipment entity
    fn write_generic_equipment(
        &self,
        file: &mut File,
        entity: &dyn SpatialEntity,
        entity_id: u32,
        placement_id: u32,
    ) -> ArxResult<()> {
        self.write_line(
            file,
            &format!(
                "#{}={}('{}','{}',$,#{});",
                entity_id, "IFCDISTRIBUTIONELEMENT", entity.id(), entity.name(), placement_id
            ),
        )?;
        Ok(())
    }

    /// Write IFC file footer
    fn write_ifc_footer(&self, file: &mut File) -> ArxResult<()> {
        self.write_line(file, "ENDSEC;")?;
        self.write_line(file, "END-ISO-10303-21;")?;
        Ok(())
    }

    /// Helper function to handle IO errors consistently
    fn write_line(&self, file: &mut File, line: &str) -> ArxResult<()> {
        writeln!(file, "{}", line).map_err(|e| {
            ArxError::io_error("Failed to write IFC data")
                .with_debug_info(format!("IO Error: {}", e))
        })
    }
}

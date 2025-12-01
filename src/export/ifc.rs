use crate::yaml::BuildingData;
use anyhow::Result;
use std::path::Path;

pub struct IFCExporter {
    data: BuildingData,
}

impl IFCExporter {
    pub fn new(data: BuildingData) -> Self {
        Self { data }
    }

    pub fn export(&self, output_path: &Path) -> Result<()> {
        let mut content = String::new();
        
        // Header
        content.push_str("ISO-10303-21;\n");
        content.push_str("HEADER;\n");
        content.push_str("FILE_DESCRIPTION(('ArxOS Export'),'2;1');\n");
        content.push_str(&format!("FILE_NAME('{}','{}',('ArxOS User'),(),'ArxOS Export','ArxOS','');\n", 
            output_path.file_name().unwrap_or_default().to_string_lossy(),
            chrono::Utc::now().format("%Y-%m-%dT%H:%M:%S")
        ));
        content.push_str("FILE_SCHEMA(('IFC4'));\n");
        content.push_str("ENDSEC;\n");
        
        // Data
        content.push_str("DATA;\n");
        content.push_str(&format!("/* Building: {} (ID: {}) */\n", self.data.building.name, self.data.building.id));
        
        // Iterate and add comments for structure
        for floor in &self.data.building.floors {
            content.push_str(&format!("/* Floor: {} (Level: {}) */\n", floor.name, floor.level));
            for wing in &floor.wings {
                 content.push_str(&format!("/* Wing: {} */\n", wing.name));
                 for room in &wing.rooms {
                     content.push_str(&format!("/* Room: {} */\n", room.name));
                 }
            }
        }
        
        content.push_str("ENDSEC;\n");
        content.push_str("END-ISO-10303-21;");
        
        std::fs::write(output_path, content)?;
        Ok(())
    }
}

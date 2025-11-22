use crate::cli::commands::Command;
use crate::ifc::IFCProcessor;
use crate::yaml::BuildingYamlSerializer;
use crate::core::BuildingMetadata;
use crate::yaml::BuildingData;
use crate::utils::path_safety::PathSafety;
use anyhow::anyhow;
use std::error::Error;
use std::path::Path;

pub struct ImportCommand {
    pub ifc_file: String,
    pub repo: Option<String>,
    pub dry_run: bool,
}

impl Command for ImportCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        println!("🏗️  Importing IFC file: {}", self.ifc_file);

        if self.dry_run {
            println!("🔍 Dry run mode enabled - no changes will be written");
        }

        let processor = IFCProcessor::new();
        let serializer = BuildingYamlSerializer::new();
        let repo_root = Path::new(".");

        // 1. Extract hierarchy
        let building_data = match processor.extract_hierarchy(&self.ifc_file) {
            Ok((mut building, floors)) => {
                if !floors.is_empty() {
                    building.floors = floors;
                }
                
                building.metadata = Some(BuildingMetadata {
                    source_file: Some(self.ifc_file.clone()),
                    parser_version: "2.0.0".to_string(),
                    total_entities: 0,
                    spatial_entities: 0,
                    coordinate_system: "Unknown".to_string(),
                    units: "Meters".to_string(),
                    tags: Vec::new(),
                });

                BuildingData {
                    building,
                    equipment: Vec::new(),
                }
            }
            Err(e) => {
                return Err(format!("Failed to parse IFC file: {}", e).into());
            }
        };

        if self.dry_run {
            println!("✅ Parsed successfully:");
            println!("  Building: {}", building_data.building.name);
            println!("  Floors: {}", building_data.building.floors.len());
            return Ok(());
        }

        // 2. Write to YAML
        let yaml_filename = format!("{}.yaml", building_data.building.name.replace(" ", "_").to_lowercase());
        let yaml_path = repo_root.join(&yaml_filename);
        
        PathSafety::validate_path_for_write(&yaml_path).map_err(|e| anyhow!(e))?;
        
        let yaml_content = serializer.to_yaml(&building_data)
            .map_err(|e| anyhow!("Failed to serialize YAML: {}", e))?;

        std::fs::write(&yaml_path, yaml_content)
            .map_err(|e| anyhow!("Failed to write YAML to {}: {}", yaml_path.display(), e))?;

        println!("✅ Imported successfully to {}", yaml_path.display());

        Ok(())
    }

    fn name(&self) -> &'static str {
        "import"
    }
}

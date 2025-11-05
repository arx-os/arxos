//! IFC file processing command handlers
//!
//! Handles IFC file processing operations such as hierarchy extraction.

use crate::cli::IFCCommands;
use crate::ifc;
use crate::yaml;

/// Handle IFC processing commands
///
/// Routes IFC subcommands to their respective handlers.
///
/// # Arguments
///
/// * `subcommand` - The IFC command variant to execute
///
/// # Returns
///
/// Returns `Ok(())` if the command executes successfully, or an error if it fails.
pub fn handle_ifc_command(subcommand: IFCCommands) -> Result<(), Box<dyn std::error::Error>> {
    match subcommand {
        IFCCommands::ExtractHierarchy { file, output } => {
            println!("🔧 Extracting building hierarchy from: {}", file);
            
            // Validate IFC file exists
            if !std::path::Path::new(&file).exists() {
                return Err(format!(
                    "IFC file '{}' not found. Please check the file path and ensure the file exists.",
                    file
                ).into());
            }
            
            // Extract hierarchy
            let processor = ifc::IFCProcessor::new();
            match processor.extract_hierarchy(&file) {
                Ok((building, floors)) => {
                    println!("✅ Successfully extracted building hierarchy");
                    println!("   Building: {}", building.name);
                    println!("   Building ID: {}", building.id);
                    println!("   Floors: {}", floors.len());
                    
                    // Display floor information
                    for floor in floors.iter() {
                        println!("   - {}: level {}", floor.name, floor.level);
                        
                        // Count rooms and equipment on this floor
                        let room_count: usize = floor.wings.iter().map(|w| w.rooms.len()).sum();
                        let equipment_count = floor.equipment.len();
                        println!("      Rooms: {}, Equipment: {}", room_count, equipment_count);
                    }
                    
                    // Generate YAML output if requested
                    if let Some(output_file) = output {
                        let serializer = yaml::BuildingYamlSerializer::new();
                        let building_data = serializer.serialize_building(&building, &[], Some(&file))
                            .map_err(|e| format!("Failed to serialize building: {}", e))?;
                        
                        serializer.write_to_file(&building_data, &output_file)
                            .map_err(|e| format!("Failed to write YAML file: {}", e))?;
                        
                        println!("📄 Hierarchy written to: {}", output_file);
                    }
                    
                    println!("✅ Hierarchy extraction completed");
                }
                Err(e) => {
                    return Err(format!(
                        "Failed to extract hierarchy from '{}': {}. Please check that the file is a valid IFC file.",
                        file, e
                    ).into());
                }
            }
        }
    }
    
    Ok(())
}

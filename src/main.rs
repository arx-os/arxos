pub mod core;
pub mod cli;
pub mod spatial;
pub mod git;
pub mod ifc;
pub mod render;
pub mod yaml;
pub mod path;

use clap::Parser;
use cli::Cli;
use core::Building;
use log::info;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging
    env_logger::init();
    
    info!("Starting ArxOS v2.0");
    let cli = Cli::parse();
    
    match cli.command {
        cli::Commands::Import { ifc_file, repo } => {
            println!("Importing IFC file: {}", ifc_file);
            if let Some(repo_url) = repo {
                println!("To repository: {}", repo_url);
            }
            
            // Use real IFC processor
            let processor = ifc::IFCProcessor::new();
            match processor.process_file(&ifc_file) {
                Ok((building, spatial_entities)) => {
                    println!("✅ Successfully parsed building: {}", building.name);
                    println!("   Building ID: {}", building.id);
                    println!("   Created: {}", building.created_at.format("%Y-%m-%d %H:%M:%S"));
                    println!("   Spatial entities found: {}", spatial_entities.len());
                    
                    // Display spatial information
                    for entity in spatial_entities.iter().take(5) { // Show first 5 entities
                        println!("   - {}: {} at {}", entity.entity_type, entity.name, entity.position);
                    }
                    if spatial_entities.len() > 5 {
                        println!("   ... and {} more entities", spatial_entities.len() - 5);
                    }

                    // Generate YAML output
                    let serializer = yaml::BuildingYamlSerializer::new();
                    match serializer.serialize_building(&building, &spatial_entities, Some(&ifc_file)) {
                        Ok(building_data) => {
                            let yaml_file = format!("{}.yaml", building.name.to_lowercase().replace(" ", "_"));
                            match serializer.write_to_file(&building_data, &yaml_file) {
                                Ok(_) => {
                                    println!("📄 Generated YAML file: {}", yaml_file);
                                    println!("   Floors: {}", building_data.floors.len());
                                    println!("   Total rooms: {}", building_data.floors.iter().map(|f| f.rooms.len()).sum::<usize>());
                                    println!("   Total equipment: {}", building_data.floors.iter().map(|f| f.equipment.len()).sum::<usize>());
                                }
                                Err(e) => {
                                    println!("❌ Error writing YAML file: {}", e);
                                }
                            }
                        }
                        Err(e) => {
                            println!("❌ Error serializing building data: {}", e);
                        }
                    }
                }
                Err(e) => {
                    println!("❌ Error processing IFC file: {}", e);
                }
            }
        }
        cli::Commands::Export { repo } => {
            println!("Exporting to repository: {}", repo);
            
            // Check if we have a YAML file to export
            let yaml_files: Vec<String> = std::fs::read_dir(".")
                .unwrap()
                .filter_map(|entry| {
                    let entry = entry.ok()?;
                    let path = entry.path();
                    if path.extension()? == "yaml" {
                        path.to_str().map(|s| s.to_string())
                    } else {
                        None
                    }
                })
                .collect();
            
            if yaml_files.is_empty() {
                println!("❌ No YAML files found. Please run 'import' first to generate building data.");
                return Ok(());
            }
            
            // Use the first YAML file found
            let yaml_file = &yaml_files[0];
            println!("📄 Using YAML file: {}", yaml_file);
            
            // Read and parse the YAML file
            let yaml_content = std::fs::read_to_string(yaml_file)?;
            let building_data: yaml::BuildingData = serde_yaml::from_str(&yaml_content)?;
            
            // Initialize Git manager
            let config = git::GitConfigManager::default_config();
            let mut git_manager = git::BuildingGitManager::new(&repo, &building_data.building.name, config)?;
            
            // Export to Git repository
            match git_manager.export_building(&building_data, Some("Initial building data export")) {
                Ok(result) => {
                    println!("✅ Successfully exported to Git repository!");
                    println!("   Commit ID: {}", result.commit_id);
                    println!("   Files changed: {}", result.files_changed);
                    println!("   Message: {}", result.message);
                    
                    // Show repository status
                    if let Ok(status) = git_manager.get_status() {
                        println!("   Current branch: {}", status.current_branch);
                        println!("   Last commit: {}", &status.last_commit[..8]);
                    }
                }
                Err(e) => {
                    println!("❌ Error exporting to Git repository: {}", e);
                }
            }
        }
        cli::Commands::Render { building, floor } => {
            println!("Rendering building: {}", building);
            if let Some(floor_num) = floor {
                println!("Floor: {}", floor_num);
            }
            
            // Create mock building for demonstration
            let mock_building = Building::new(building, "/MOCK".to_string());
            let renderer = render::BuildingRenderer::new(mock_building);
            renderer.render_floor(floor.unwrap_or(1))?;
        }
        cli::Commands::Validate { path } => {
            if let Some(data_path) = path {
                println!("Validating data at: {}", data_path);
            } else {
                println!("Validating current directory");
            }
            println!("✅ Validation completed (mock implementation)");
        }
    }
    
    Ok(())
}

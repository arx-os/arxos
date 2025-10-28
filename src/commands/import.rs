// Import command handler
// Handles IFC file importing and building data generation

use crate::ifc;
use crate::progress;
use crate::core::Building;
use log::warn;

/// Helper function to generate YAML output from building data
fn generate_yaml_output(building: &Building, building_name: &str) -> Result<String, Box<dyn std::error::Error>> {
    use crate::yaml::BuildingYamlSerializer;
    
    let serializer = BuildingYamlSerializer::new();
    
    // Try to serialize with hierarchical data first (empty spatial entities)
    let building_data = match serializer.serialize_building(building, &[], None) {
        Ok(data) => data,
        Err(_) => {
            // Fallback: try without spatial data
            serializer.serialize_building(building, &[], None)?
        }
    };
    
    let yaml_file = format!("{}.yaml", building_name.to_lowercase().replace(" ", "_"));
    
    serializer.write_to_file(&building_data, &yaml_file)?;
    
    println!("📄 Generated YAML file: {}", yaml_file);
    println!("   Floors: {}", building_data.floors.len());
    println!("   Total rooms: {}", building_data.floors.iter().map(|f| f.rooms.len()).sum::<usize>());
    println!("   Total equipment: {}", building_data.floors.iter().map(|f| f.equipment.len()).sum::<usize>());
    
    Ok(yaml_file)
}

/// Handle the import command
pub fn handle_import(ifc_file: String, repo: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    println!("🚀 Importing IFC file: {}", ifc_file);
    if let Some(ref repo_path) = repo {
        println!("📦 To repository: {}", repo_path);
    }
    
    // Validate IFC file exists
    if !std::path::Path::new(&ifc_file).exists() {
        return Err(format!(
            "IFC file '{}' not found. Please check the file path and ensure the file exists.",
            ifc_file
        ).into());
    }
    
    // Create progress reporter
    let progress_reporter = progress::utils::create_ifc_progress(100);
    let progress_context = progress::ProgressContext::with_reporter(progress_reporter.clone());
    
    // Use IFC processor to extract hierarchy
    let processor = ifc::IFCProcessor::new();
    
    // Extract building hierarchy from IFC file
    match processor.extract_hierarchy(&ifc_file) {
        Ok((building, floors)) => {
            progress_reporter.finish_success(&format!("Successfully extracted building hierarchy: {}", building.name));
            println!("✅ Building: {}", building.name);
            println!("   Building ID: {}", building.id);
            println!("   Created: {}", building.created_at.format("%Y-%m-%d %H:%M:%S"));
            println!("   Floors found: {}", floors.len());
            
            // Display floor information
            for floor in floors.iter().take(5) {
                println!("   - {}: level {}", floor.name, floor.level);
            }
            if floors.len() > 5 {
                println!("   ... and {} more floors", floors.len() - 5);
            }
            
            // Generate YAML output using helper function
            match generate_yaml_output(&building, &building.name) {
                Ok(yaml_file) => {
                    // Initialize Git repo if requested
                    if let Some(ref repo_path) = repo {
                        match initialize_git_repo(repo_path, &yaml_file, &building.name) {
                            Ok(_) => println!("✅ Initialized Git repository at: {}", repo_path),
                            Err(e) => println!("⚠️  Git initialization failed: {}", e),
                        }
                    }
                },
                Err(e) => {
                    println!("❌ Error generating YAML file: {}", e);
                }
            }
        }
        Err(e) => {
            progress_reporter.finish_error(&format!("Error processing IFC file: {}", e));
            warn!("Hierarchy extraction failed, trying fallback parsing: {}", e);
            
            // Fallback to old parsing method
            match processor.process_file_with_progress(&ifc_file, progress_context) {
                Ok((building, spatial_entities)) => {
                    progress_reporter.finish_success(&format!("Successfully parsed building: {}", building.name));
                    println!("✅ Building: {}", building.name);
                    println!("   Building ID: {}", building.id);
                    println!("   Created: {}", building.created_at.format("%Y-%m-%d %H:%M:%S"));
                    println!("   Spatial entities found: {}", spatial_entities.len());
                    
                    // Display spatial information
                    for entity in spatial_entities.iter().take(5) {
                        println!("   - {}: {} at {}", entity.entity_type, entity.name, entity.position);
                    }
                    if spatial_entities.len() > 5 {
                        println!("   ... and {} more entities", spatial_entities.len() - 5);
                    }

                    // Generate YAML output using helper function
                    match generate_yaml_output(&building, &building.name) {
                        Ok(yaml_file) => {
                            // Initialize Git repo if requested
                            if let Some(ref repo_path) = repo {
                                match initialize_git_repo(repo_path, &yaml_file, &building.name) {
                                    Ok(_) => println!("✅ Initialized Git repository at: {}", repo_path),
                                    Err(e) => println!("⚠️  Git initialization failed: {}", e),
                                }
                            }
                        },
                        Err(e) => {
                            println!("❌ Error generating YAML file: {}", e);
                        }
                    }
                }
                Err(fallback_error) => {
                    progress_reporter.finish_error(&format!("Error processing IFC file: {}", fallback_error));
                    return Err(format!(
                        "Failed to process IFC file '{}': {}. \
                        Please check that the file is a valid IFC file and try again. \
                        Common issues:\n\
                        - File is corrupted or incomplete\n\
                        - Unsupported IFC version\n\
                        - Missing required IFC entities\n\
                        - File permissions issues",
                        ifc_file, fallback_error
                    ).into());
                }
            }
        }
    }
    
    Ok(())
}

/// Initialize Git repository and commit YAML file
fn initialize_git_repo(repo_path: &str, yaml_file: &str, building_name: &str) -> Result<(), Box<dyn std::error::Error>> {
    use crate::git::manager::{BuildingGitManager, GitConfig};
    use crate::yaml::BuildingData;
    
    // Create Git config with default values
    let git_config = GitConfig {
        author_name: std::env::var("GIT_AUTHOR_NAME").unwrap_or_else(|_| "ArxOS System".to_string()),
        author_email: std::env::var("GIT_AUTHOR_EMAIL").unwrap_or_else(|_| "system@arxos.dev".to_string()),
        branch: "main".to_string(),
        remote_url: None,
    };
    
    // Initialize Git manager
    let mut git_manager = BuildingGitManager::new(repo_path, building_name, git_config.clone())?;
    
    // Load the YAML file directly
    let content = std::fs::read_to_string(yaml_file)?;
    let building_data: BuildingData = serde_yaml::from_str(&content)?;
    
    // Export to Git and commit
    let result = git_manager.export_building(&building_data, Some(&format!("Initial import from IFC: {}", building_name)))?;
    
    println!("   Committed: {}", result.commit_id);
    println!("   Files changed: {}", result.files_changed);
    
    Ok(())
}


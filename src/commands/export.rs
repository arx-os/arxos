// Export command handler
// Handles exporting building data to Git repository

use crate::git;
use crate::yaml;
use crate::utils::loading;
use std::path::Path;

/// Check if a path is a valid Git repository
fn is_git_repository(path: &str) -> bool {
    let git_dir = Path::new(path).join(".git");
    git_dir.exists() && git_dir.is_dir()
}

/// Initialize Git repository if it doesn't exist
fn init_git_repository(path: &str) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔧 Initializing Git repository at: {}", path);
    
    let repo_path = Path::new(path);
    
    // Create directory if it doesn't exist
    std::fs::create_dir_all(repo_path)?;
    
    // Initialize Git repository using git2
    match git2::Repository::init(repo_path) {
        Ok(_) => {
            println!("✅ Git repository initialized successfully");
            Ok(())
        }
        Err(e) => {
            Err(format!("Failed to initialize Git repository: {}", e).into())
        }
    }
}

/// Validate Git repository or initialize it
fn ensure_git_repository(path: &str) -> Result<(), Box<dyn std::error::Error>> {
    // Check if Git repository exists
    if !is_git_repository(path) {
        // Check if path exists and is a directory
        if Path::new(path).exists() {
            // Path exists but is not a Git repository
            return Err(format!(
                "Path '{}' exists but is not a Git repository. Please:\n\
                1. Remove the existing directory, or\n\
                2. Initialize it as a Git repository with 'git init'",
                path
            ).into());
        }
        
        // Initialize new Git repository
        init_git_repository(path)?;
    }
    
    Ok(())
}

/// Handle the export command
pub fn handle_export(repo: String) -> Result<(), Box<dyn std::error::Error>> {
    println!("📤 Exporting to repository: {}", repo);
    
    // Check if we have YAML files to export
    let yaml_files = loading::find_yaml_files()?;
    
    if yaml_files.is_empty() {
        println!("❌ No YAML files found. Please run 'import' first to generate building data.");
        println!("💡 Tip: Use 'arxos import <ifc_file>' to import an IFC file first");
        return Ok(());
    }
    
    // Use the first YAML file found
    let yaml_file = &yaml_files[0];
    println!("📄 Using YAML file: {}", yaml_file);
    
    // Read and parse the YAML file
    let yaml_content = std::fs::read_to_string(yaml_file)?;
    let building_data: yaml::BuildingData = match serde_yaml::from_str(&yaml_content) {
        Ok(data) => data,
        Err(e) => {
            return Err(format!("Failed to parse YAML file '{}': {}", yaml_file, e).into());
        }
    };
    
    // Validate or initialize Git repository
    ensure_git_repository(&repo)?;
    
    // Initialize Git manager
    let config = git::manager::GitConfigManager::default_config();
    let mut git_manager = match git::manager::BuildingGitManager::new(&repo, &building_data.building.name, config) {
        Ok(manager) => manager,
        Err(e) => {
            return Err(format!("Failed to initialize Git manager: {}", e).into());
        }
    };
    
    // Export to Git repository
    println!("💾 Exporting building data to Git...");
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
            return Err(format!("Export failed: {}", e).into());
        }
    }
    
    Ok(())
}


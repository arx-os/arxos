// Export command handler
// Handles exporting building data to Git repository or other formats

use crate::git;
use crate::yaml;
use crate::utils::loading;
use crate::export::{IFCExporter, ARExporter, ARFormat};
use crate::export::ifc::IFCSyncState;
use std::path::{Path, PathBuf};

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

/// Handle the export command with format support
pub fn handle_export_with_format(
    format: String,
    output: Option<String>,
    repo: Option<String>,
    delta: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    match format.to_lowercase().as_str() {
        "git" => {
            let repo_path = repo.ok_or("--repo required for git format")?;
            handle_export(repo_path)
        }
        "ifc" => {
            let output_path = output.ok_or("--output required for ifc format")?;
            handle_export_ifc(PathBuf::from(output_path), delta)
        }
        "gltf" | "usdz" => {
            let output_path = output.ok_or("--output required for AR format")?;
            let ar_format = format.parse::<ARFormat>()
                .map_err(|e| format!("Invalid AR format: {}", e))?;
            handle_export_ar(PathBuf::from(output_path), ar_format)
        }
        _ => Err(format!("Unsupported export format: {}. Supported: git, ifc, gltf, usdz", format).into())
    }
}

/// Handle the export command (legacy - Git repository only)
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
    let yaml_file = yaml_files.first()
        .ok_or("No YAML files found to export")?;
    println!("📄 Using YAML file: {}", yaml_file);
    
    // Read and parse the YAML file with path safety
    use crate::utils::path_safety::PathSafety;
    let base_dir = std::env::current_dir()
        .map_err(|e| format!("Failed to get current directory: {}", e))?;
    
    let yaml_content = PathSafety::read_file_safely(
        std::path::Path::new(yaml_file),
        &base_dir
    )
    .map_err(|e| format!("Failed to read YAML file '{}': {}", yaml_file, e))?;
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

/// Handle IFC export
fn handle_export_ifc(output_path: PathBuf, delta: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("📤 Exporting to IFC: {}", output_path.display());
    
    // Check if we have YAML files to export
    let yaml_files = loading::find_yaml_files()?;
    
    if yaml_files.is_empty() {
        println!("❌ No YAML files found. Please run 'import' first to generate building data.");
        return Ok(());
    }
    
    // Use the first YAML file found
    let yaml_file = yaml_files.first()
        .ok_or("No YAML files found to export")?;
    println!("📄 Using YAML file: {}", yaml_file);
    
    // Read and parse the YAML file with path safety
    use crate::utils::path_safety::PathSafety;
    let base_dir = std::env::current_dir()
        .map_err(|e| format!("Failed to get current directory: {}", e))?;
    
    let yaml_content = PathSafety::read_file_safely(
        std::path::Path::new(yaml_file),
        &base_dir
    )
    .map_err(|e| format!("Failed to read YAML file '{}': {}", yaml_file, e))?;
    let building_data: yaml::BuildingData = match serde_yaml::from_str(&yaml_content) {
        Ok(data) => data,
        Err(e) => {
            return Err(format!("Failed to parse YAML file '{}': {}", yaml_file, e).into());
        }
    };
    
    // Load sync state if delta mode
    let sync_state_path = IFCSyncState::default_path();
    let sync_state = if delta {
        IFCSyncState::load(&sync_state_path)
    } else {
        None
    };
    
    // Create exporter
    let exporter = IFCExporter::new(building_data.clone());
    
    // Export
    if delta && sync_state.is_some() {
        println!("📊 Delta mode: exporting only changes");
        exporter.export_delta(sync_state.as_ref(), &output_path)?;
    } else {
        println!("📤 Full export mode: exporting all data");
        exporter.export(&output_path)?;
    }
    
    // Update sync state
    let (equipment_paths, rooms_paths) = exporter.collect_universal_paths();
    let mut updated_state = sync_state.unwrap_or_else(|| IFCSyncState::new(output_path.clone()));
    updated_state.update_after_export(equipment_paths, rooms_paths);
    updated_state.save(&sync_state_path)?;
    
    println!("✅ Successfully exported IFC file: {}", output_path.display());
    Ok(())
}

/// Handle AR export (glTF/USDZ)
fn handle_export_ar(output_path: PathBuf, format: ARFormat) -> Result<(), Box<dyn std::error::Error>> {
    println!("📤 Exporting to {}: {}", format, output_path.display());
    
    // Check if we have YAML files to export
    let yaml_files = loading::find_yaml_files()?;
    
    if yaml_files.is_empty() {
        println!("❌ No YAML files found. Please run 'import' first to generate building data.");
        return Ok(());
    }
    
    // Use the first YAML file found
    let yaml_file = yaml_files.first()
        .ok_or("No YAML files found to export")?;
    println!("📄 Using YAML file: {}", yaml_file);
    
    // Read and parse the YAML file with path safety
    use crate::utils::path_safety::PathSafety;
    let base_dir = std::env::current_dir()
        .map_err(|e| format!("Failed to get current directory: {}", e))?;
    
    let yaml_content = PathSafety::read_file_safely(
        std::path::Path::new(yaml_file),
        &base_dir
    )
    .map_err(|e| format!("Failed to read YAML file '{}': {}", yaml_file, e))?;
    let building_data: yaml::BuildingData = match serde_yaml::from_str(&yaml_content) {
        Ok(data) => data,
        Err(e) => {
            return Err(format!("Failed to parse YAML file '{}': {}", yaml_file, e).into());
        }
    };
    
    // Create exporter and export
    let exporter = ARExporter::new(building_data);
    exporter.export(format, &output_path)?;
    
    println!("✅ Successfully exported {} file: {}", format, output_path.display());
    Ok(())
}

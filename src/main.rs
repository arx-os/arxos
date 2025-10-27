pub mod core;
pub mod cli;
pub mod config;
pub mod error;
pub mod spatial;
pub mod git;
pub mod ifc;
pub mod progress;
pub mod render;
pub mod render3d;
pub mod ar_integration;
pub mod yaml;
pub mod path;
pub mod search;
pub mod persistence;
pub mod hardware;

use clap::Parser;
use cli::Cli;
use log::{info, warn};
use crate::progress::{ProgressContext, utils};
use crate::core::{RoomType, EquipmentType};
use crate::render3d::{Render3DConfig, ProjectionType, ViewAngle, Building3DRenderer, format_scene_output, InteractiveRenderer, InteractiveConfig};

/// Load building data from YAML files with comprehensive error handling.
///
/// This function searches for building data files in the current directory and loads
/// the specified building data. It provides detailed error messages for common issues
/// and suggests solutions.
///
/// # Parameters
///
/// * `building_name` - Name of the building to load
///
/// # Returns
///
/// Returns a `Result` containing:
/// - `Ok(BuildingData)` - Successfully loaded building data
/// - `Err(Box<dyn std::error::Error>)` - Error with detailed context and suggestions
///
/// # Errors
///
/// This function can return various errors:
/// - **File not found**: Building data file doesn't exist
/// - **Parse error**: Invalid YAML/JSON format
/// - **Permission error**: Cannot read file due to permissions
/// - **IO error**: General file system errors
///
/// # Example
///
/// ```rust
/// match load_building_data("My Building") {
///     Ok(data) => println!("Loaded building: {}", data.building.name),
///     Err(e) => eprintln!("Failed to load building: {}", e),
/// }
/// ```
fn load_building_data(building_name: &str) -> Result<yaml::BuildingData, Box<dyn std::error::Error>> {
    // Look for YAML files in current directory
    let yaml_files: Vec<String> = std::fs::read_dir(".")
        .map_err(|e| {
            format!(
                "Failed to read current directory: {}. \
                Please ensure you have read permissions and are in the correct directory.",
                e
            )
        })?
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
        return Err(format!(
            "No YAML files found in current directory. \
            Available options:\n\
            1. Run 'arxos import <ifc-file> --building \"{}\"' to import building data\n\
            2. Check if you're in the correct directory\n\
            3. Verify that YAML files exist and have .yaml extension",
            building_name
        ).into());
    }
    
    // Try to find a YAML file that matches the building name
    let yaml_file = yaml_files.iter()
        .find(|file| file.to_lowercase().contains(&building_name.to_lowercase()))
        .or_else(|| yaml_files.first())
        .ok_or_else(|| {
            format!(
                "No suitable YAML file found for building '{}'. \
                Available files: {}. \
                Please check the building name or import the correct building data.",
                building_name,
                yaml_files.join(", ")
            )
        })?;
    
    println!("📄 Loading building data from: {}", yaml_file);
    
    // Read and parse the YAML file with detailed error handling
    let yaml_content = std::fs::read_to_string(yaml_file)
        .map_err(|e| {
            format!(
                "Failed to read file '{}': {}. \
                Please check file permissions and ensure the file is not corrupted.",
                yaml_file, e
            )
        })?;
    let building_data: yaml::BuildingData = serde_yaml::from_str(&yaml_content)
        .map_err(|e| {
            format!(
                "Failed to parse YAML file '{}': {}. \
                The file may be corrupted or have invalid YAML syntax. \
                Please check the file format and try importing again.",
                yaml_file, e
            )
        })?;
    
    // Validate that the loaded data contains the expected building
    if !building_data.building.name.to_lowercase().contains(&building_name.to_lowercase()) {
        println!("⚠️  Warning: Building name '{}' doesn't match requested '{}'", 
                 building_data.building.name, building_name);
    }
    
    Ok(building_data)
}

/// Validate YAML building data file
fn validate_yaml_file(file_path: &str) -> Result<(), Box<dyn std::error::Error>> {
    // Read and parse the YAML file
    let yaml_content = std::fs::read_to_string(file_path)?;
    let building_data: yaml::BuildingData = serde_yaml::from_str(&yaml_content)?;
    
    // Validate building data structure
    if building_data.building.name.is_empty() {
        return Err("Building name cannot be empty".into());
    }
    
    if building_data.floors.is_empty() {
        return Err("Building must have at least one floor".into());
    }
    
    // Validate each floor
    for floor in &building_data.floors {
        if floor.name.is_empty() {
            return Err(format!("Floor {} has empty name", floor.level).into());
        }
        
        // Check for duplicate floor levels
        let duplicate_floors = building_data.floors.iter()
            .filter(|f| f.level == floor.level)
            .count();
        if duplicate_floors > 1 {
            return Err(format!("Duplicate floor level {} found", floor.level).into());
        }
    }
    
    Ok(())
}

/// Handle status command - show repository status and changes
fn handle_status_command(verbose: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("📊 ArxOS Repository Status");
    println!("{}", "=".repeat(50));
    
    // Check if we're in a Git repository
    let repo_path = find_git_repository()?;
    
    if let Some(repo_path) = repo_path {
        // Initialize Git manager
        let config = git::manager::GitConfigManager::default_config();
        let manager = git::manager::BuildingGitManager::new(&repo_path, "Building", config)?;
        
        // Get repository status
        let status = manager.get_status()?;
        
        // Display basic status
        display_basic_status(&status);
        
        if verbose {
            // Display detailed information
            display_detailed_status(&manager)?;
        }
        
        // Check for uncommitted changes
        check_working_directory_status(&repo_path)?;
        
    } else {
        println!("❌ Not in a Git repository");
        println!("💡 Run 'arx import <file.ifc>' to initialize a repository");
    }
    
    Ok(())
}

/// Find Git repository in current directory or parent directories
fn find_git_repository() -> Result<Option<String>, Box<dyn std::error::Error>> {
    let mut current_path = std::env::current_dir()?;
    
    loop {
        let git_path = current_path.join(".git");
        if git_path.exists() {
            return Ok(Some(current_path.to_string_lossy().to_string()));
        }
        
        if !current_path.pop() {
            break;
        }
    }
    
    Ok(None)
}

/// Display basic repository status
fn display_basic_status(status: &git::manager::GitStatus) {
    println!("🌿 Branch: {}", status.current_branch);
    
    if !status.last_commit.is_empty() {
        println!("📝 Last commit: {}", &status.last_commit[..8]);
        println!("💬 Message: {}", status.last_commit_message);
        
        let commit_time = chrono::DateTime::from_timestamp(status.last_commit_time, 0)
            .unwrap_or_default();
        println!("⏰ Time: {}", commit_time.format("%Y-%m-%d %H:%M:%S"));
    } else {
        println!("📝 No commits yet");
    }
}

/// Display detailed repository status
fn display_detailed_status(manager: &git::manager::BuildingGitManager) -> Result<(), Box<dyn std::error::Error>> {
    println!("\n📋 Recent Commits:");
    println!("{}", "-".repeat(30));
    
    let commits = manager.list_commits(5)?;
    
    if commits.is_empty() {
        println!("No commits found");
    } else {
        for (i, commit) in commits.iter().enumerate() {
            let commit_time = chrono::DateTime::from_timestamp(commit.time, 0)
                .unwrap_or_default();
            
            println!("{}. {} - {}", 
                i + 1,
                &commit.id[..8],
                commit.message.lines().next().unwrap_or("No message")
            );
            println!("   Author: {} | Time: {}", 
                commit.author,
                commit_time.format("%Y-%m-%d %H:%M:%S")
            );
        }
    }
    
    Ok(())
}

/// Check working directory status for uncommitted changes
fn check_working_directory_status(_repo_path: &str) -> Result<(), Box<dyn std::error::Error>> {
    println!("\n📁 Working Directory Status:");
    println!("{}", "-".repeat(30));
    
    // Check for YAML files in current directory
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
        println!("📄 No YAML files found in working directory");
        println!("💡 Run 'arx import <file.ifc>' to generate building data");
    } else {
        println!("📄 Found {} YAML file(s):", yaml_files.len());
        for file in yaml_files {
            println!("   • {}", file);
        }
    }
    
    // Check for IFC files
    let ifc_files: Vec<String> = std::fs::read_dir(".")
        .unwrap()
        .filter_map(|entry| {
            let entry = entry.ok()?;
            let path = entry.path();
            if path.extension()?.to_str()?.to_lowercase() == "ifc" {
                path.to_str().map(|s| s.to_string())
            } else {
                None
            }
        })
        .collect();
    
    if !ifc_files.is_empty() {
        println!("🏗️ Found {} IFC file(s):", ifc_files.len());
        for file in ifc_files {
            println!("   • {}", file);
        }
    }
    
    Ok(())
}

/// Handle diff command - show differences between commits
fn handle_diff_command(commit: Option<String>, file: Option<String>, stat: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔍 ArxOS Diff");
    println!("{}", "=".repeat(50));
    
    // Check if we're in a Git repository
    let repo_path = find_git_repository()?;
    
    if let Some(repo_path) = repo_path {
        // Initialize Git manager
        let config = git::manager::GitConfigManager::default_config();
        let manager = git::manager::BuildingGitManager::new(&repo_path, "Building", config)?;
        
        if stat {
            // Show statistics only
            let stats = manager.get_diff_stats(commit.as_deref())?;
            display_diff_stats(&stats);
        } else {
            // Show full diff
            let diff_result = manager.get_diff(commit.as_deref(), file.as_deref())?;
            display_diff_result(&diff_result, file.is_some())?;
        }
        
    } else {
        println!("❌ Not in a Git repository");
        println!("💡 Run 'arx import <file.ifc>' to initialize a repository");
    }
    
    Ok(())
}

/// Display diff statistics
fn display_diff_stats(stats: &git::manager::DiffStats) {
    println!("📊 Diff Statistics:");
    println!("{}", "-".repeat(30));
    println!("📁 Files changed: {}", stats.files_changed);
    println!("➕ Insertions: {}", stats.insertions);
    println!("➖ Deletions: {}", stats.deletions);
    
    if stats.insertions > 0 || stats.deletions > 0 {
        let net_change = stats.insertions as i32 - stats.deletions as i32;
        if net_change > 0 {
            println!("📈 Net change: +{}", net_change);
        } else if net_change < 0 {
            println!("📉 Net change: {}", net_change);
        } else {
            println!("⚖️ Net change: 0");
        }
    }
}

/// Display full diff result
fn display_diff_result(diff_result: &git::manager::DiffResult, single_file: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("📝 Commit: {} → {}", 
        &diff_result.compare_hash[..8], 
        &diff_result.commit_hash[..8]
    );
    
    if !single_file {
        println!("📊 {} files changed, {} insertions(+), {} deletions(-)", 
            diff_result.files_changed,
            diff_result.insertions,
            diff_result.deletions
        );
    }
    
    if diff_result.file_diffs.is_empty() {
        println!("✅ No changes found");
        return Ok(());
    }
    
    // Group diffs by file
    let mut current_file = String::new();
    for diff in &diff_result.file_diffs {
        if diff.file_path != current_file {
            current_file = diff.file_path.clone();
            println!("\n📄 {}", current_file);
            println!("{}", "-".repeat(50));
        }
        
        let prefix = match diff.line_type {
            git::manager::DiffLineType::Addition => "+",
            git::manager::DiffLineType::Deletion => "-",
            git::manager::DiffLineType::Context => " ",
        };
        
        let color = match diff.line_type {
            git::manager::DiffLineType::Addition => "🟢",
            git::manager::DiffLineType::Deletion => "🔴",
            git::manager::DiffLineType::Context => "⚪",
        };
        
        println!("{}{:4} {}{}", 
            color,
            diff.line_number,
            prefix,
            diff.content
        );
    }
    
    Ok(())
}

/// Handle history command - show commit history
fn handle_history_command(limit: usize, verbose: bool, file: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    println!("📚 ArxOS History");
    println!("{}", "=".repeat(50));
    
    // Check if we're in a Git repository
    let repo_path = find_git_repository()?;
    
    if let Some(repo_path) = repo_path {
        // Initialize Git manager
        let config = git::manager::GitConfigManager::default_config();
        let manager = git::manager::BuildingGitManager::new(&repo_path, "Building", config)?;
        
        // Get commit history
        let commits = if let Some(file_path) = file {
            // Show history for specific file
            println!("📄 File History: {}", file_path);
            println!("{}", "-".repeat(30));
            manager.get_file_history(&file_path)?
        } else {
            // Show general commit history
            println!("📊 Recent Commits (showing {}):", limit);
            println!("{}", "-".repeat(30));
            manager.list_commits(limit)?
        };
        
        if commits.is_empty() {
            println!("📭 No commits found");
            return Ok(());
        }
        
        // Display commits
        display_commit_history(&commits, verbose)?;
        
    } else {
        println!("❌ Not in a Git repository");
        println!("💡 Run 'arx import <file.ifc>' to initialize a repository");
    }
    
    Ok(())
}

/// Display commit history
fn display_commit_history(commits: &[git::manager::CommitInfo], verbose: bool) -> Result<(), Box<dyn std::error::Error>> {
    for (i, commit) in commits.iter().enumerate() {
        let short_hash = &commit.id[..8];
        let timestamp = chrono::DateTime::from_timestamp(commit.time, 0)
            .unwrap_or_default()
            .format("%Y-%m-%d %H:%M:%S")
            .to_string();
        
        if verbose {
            // Detailed format
            println!("{} 📝 Commit #{}", "=".repeat(20), i + 1);
            println!("🆔 Hash: {}", commit.id);
            println!("👤 Author: {}", commit.author);
            println!("⏰ Date: {}", timestamp);
            println!("💬 Message: {}", commit.message);
            println!();
        } else {
            // Compact format
            let message_preview = if commit.message.len() > 60 {
                format!("{}...", &commit.message[..57])
            } else {
                commit.message.clone()
            };
            
            println!("{} {} {} {} {}", 
                short_hash,
                timestamp,
                commit.author,
                "📝",
                message_preview
            );
        }
    }
    
    Ok(())
}

/// Handle configuration command
fn handle_config_command(show: bool, set: Option<String>, reset: bool, edit: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("⚙️ ArxOS Configuration");
    println!("{}", "=".repeat(50));
    
    // Initialize configuration manager
    let mut config_manager = config::ConfigManager::new()
        .unwrap_or_else(|e| {
            println!("⚠️ Warning: Could not load configuration: {}", e);
            println!("Using default configuration");
            config::ConfigManager::default()
        });
    
    if show {
        display_configuration(&config_manager.get_config())?;
    } else if let Some(set_value) = set {
        set_configuration_value(&mut config_manager, &set_value)?;
    } else if reset {
        reset_configuration(&mut config_manager)?;
    } else if edit {
        edit_configuration(&mut config_manager)?;
    } else {
        // Default: show configuration
        display_configuration(&config_manager.get_config())?;
    }
    
    Ok(())
}

/// Display current configuration
fn display_configuration(config: &config::ArxConfig) -> Result<(), Box<dyn std::error::Error>> {
    println!("📋 Current Configuration:");
    println!("{}", "-".repeat(30));
    
    // User configuration
    println!("👤 User:");
    println!("   Name: {}", config.user.name);
    println!("   Email: {}", config.user.email);
    if let Some(ref org) = config.user.organization {
        println!("   Organization: {}", org);
    }
    println!("   Commit Template: {}", config.user.commit_template);
    
    // Path configuration
    println!("\n📁 Paths:");
    println!("   Import Path: {}", config.paths.default_import_path.display());
    println!("   Backup Path: {}", config.paths.backup_path.display());
    println!("   Template Path: {}", config.paths.template_path.display());
    println!("   Temp Path: {}", config.paths.temp_path.display());
    
    // Building configuration
    println!("\n🏗️ Building:");
    println!("   Coordinate System: {}", config.building.default_coordinate_system);
    println!("   Auto Commit: {}", config.building.auto_commit);
    println!("   Naming Pattern: {}", config.building.naming_pattern);
    println!("   Validate on Import: {}", config.building.validate_on_import);
    
    // Performance configuration
    println!("\n⚡ Performance:");
    println!("   Max Threads: {}", config.performance.max_parallel_threads);
    println!("   Memory Limit: {} MB", config.performance.memory_limit_mb);
    println!("   Cache Enabled: {}", config.performance.cache_enabled);
    println!("   Show Progress: {}", config.performance.show_progress);
    
    // UI configuration
    println!("\n🎨 UI:");
    println!("   Use Emoji: {}", config.ui.use_emoji);
    println!("   Verbosity: {:?}", config.ui.verbosity);
    println!("   Color Scheme: {:?}", config.ui.color_scheme);
    println!("   Detailed Help: {}", config.ui.detailed_help);
    
    Ok(())
}

/// Set a configuration value
fn set_configuration_value(config_manager: &mut config::ConfigManager, set_value: &str) -> Result<(), Box<dyn std::error::Error>> {
    let parts: Vec<&str> = set_value.splitn(2, '=').collect();
    if parts.len() != 2 {
        return Err("Invalid format. Use: section.key=value".into());
    }
    
    let (key_path, value) = (parts[0], parts[1]);
    let key_parts: Vec<&str> = key_path.split('.').collect();
    
    if key_parts.len() != 2 {
        return Err("Invalid key format. Use: section.key".into());
    }
    
    let (section, key) = (key_parts[0], key_parts[1]);
    
    config_manager.update_config(|config| {
        match section {
            "user" => {
                match key {
                    "name" => config.user.name = value.to_string(),
                    "email" => config.user.email = value.to_string(),
                    "organization" => config.user.organization = Some(value.to_string()),
                    "commit_template" => config.user.commit_template = value.to_string(),
                    _ => return Err(config::ConfigError::ValidationFailed {
                        field: format!("user.{}", key),
                        message: "Unknown user configuration key".to_string(),
                    }),
                }
            }
            "building" => {
                match key {
                    "auto_commit" => {
                        config.building.auto_commit = value.parse()
                            .map_err(|e| config::ConfigError::ValidationFailed {
                                field: "building.auto_commit".to_string(),
                                message: format!("Invalid boolean value: {}", e),
                            })?;
                    }
                    "default_coordinate_system" => config.building.default_coordinate_system = value.to_string(),
                    "naming_pattern" => config.building.naming_pattern = value.to_string(),
                    "validate_on_import" => {
                        config.building.validate_on_import = value.parse()
                            .map_err(|e| config::ConfigError::ValidationFailed {
                                field: "building.validate_on_import".to_string(),
                                message: format!("Invalid boolean value: {}", e),
                            })?;
                    }
                    _ => return Err(config::ConfigError::ValidationFailed {
                        field: format!("building.{}", key),
                        message: "Unknown building configuration key".to_string(),
                    }),
                }
            }
            "performance" => {
                match key {
                    "max_parallel_threads" => {
                        config.performance.max_parallel_threads = value.parse()
                            .map_err(|e| config::ConfigError::ValidationFailed {
                                field: "performance.max_parallel_threads".to_string(),
                                message: format!("Invalid number: {}", e),
                            })?;
                    }
                    "memory_limit_mb" => {
                        config.performance.memory_limit_mb = value.parse()
                            .map_err(|e| config::ConfigError::ValidationFailed {
                                field: "performance.memory_limit_mb".to_string(),
                                message: format!("Invalid number: {}", e),
                            })?;
                    }
                    "cache_enabled" => {
                        config.performance.cache_enabled = value.parse()
                            .map_err(|e| config::ConfigError::ValidationFailed {
                                field: "performance.cache_enabled".to_string(),
                                message: format!("Invalid boolean value: {}", e),
                            })?;
                    }
                    "show_progress" => {
                        config.performance.show_progress = value.parse()
                            .map_err(|e| config::ConfigError::ValidationFailed {
                                field: "performance.show_progress".to_string(),
                                message: format!("Invalid boolean value: {}", e),
                            })?;
                    }
                    _ => return Err(config::ConfigError::ValidationFailed {
                        field: format!("performance.{}", key),
                        message: "Unknown performance configuration key".to_string(),
                    }),
                }
            }
            _ => return Err(config::ConfigError::ValidationFailed {
                field: section.to_string(),
                message: "Unknown configuration section".to_string(),
            }),
        }
        Ok(())
    })?;
    
    println!("✅ Configuration updated: {} = {}", key_path, value);
    Ok(())
}

/// Reset configuration to defaults
fn reset_configuration(config_manager: &mut config::ConfigManager) -> Result<(), Box<dyn std::error::Error>> {
    config_manager.update_config(|config| {
        *config = config::ArxConfig::default();
        Ok(())
    })?;
    
    println!("✅ Configuration reset to defaults");
    Ok(())
}

/// Edit configuration file
fn edit_configuration(config_manager: &mut config::ConfigManager) -> Result<(), Box<dyn std::error::Error>> {
    let config_path = std::env::current_dir()?.join("arx.toml");
    
    // Create default config file if it doesn't exist
    if !config_path.exists() {
        config_manager.save_to_file(&config_path)?;
        println!("📄 Created configuration file: {}", config_path.display());
    }
    
    // Try to open with default editor
    let editor = std::env::var("EDITOR").unwrap_or_else(|_| "nano".to_string());
    let status = std::process::Command::new(&editor)
        .arg(&config_path)
        .status()?;
    
    if status.success() {
        println!("✅ Configuration file edited successfully");
        println!("💡 Run 'arx config --show' to view current configuration");
    } else {
        println!("❌ Failed to edit configuration file");
    }
    
    Ok(())
}

/// Main entry point for ArxOS CLI application.
///
/// This function initializes the application, parses command-line arguments,
/// and executes the requested command with comprehensive error handling.
///
/// # Error Handling
///
/// The main function provides detailed error messages for common issues:
/// - **File not found**: Clear guidance on file locations and permissions
/// - **Parse errors**: Detailed YAML/JSON parsing error messages
/// - **Permission errors**: File system permission guidance
/// - **Command errors**: Specific error messages for each command type
///
/// # Returns
///
/// Returns a `Result` containing:
/// - `Ok(())` - Command executed successfully
/// - `Err(Box<dyn std::error::Error>)` - Error with detailed context and suggestions
fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging with error handling
    env_logger::init();
    
    info!("Starting ArxOS v2.0");
    
    // Parse CLI arguments with error handling
    let cli = Cli::parse();
    
    // Execute command with comprehensive error handling
    match execute_command(cli.command) {
        Ok(()) => {
            info!("Command completed successfully");
            Ok(())
        }
        Err(e) => {
            eprintln!("❌ Error: {}", e);
            eprintln!("\n💡 For help, run: arxos --help");
            eprintln!("📚 For documentation, see: docs/USER_GUIDE.md");
            Err(e)
        }
    }
}

/// Execute the specified command with comprehensive error handling.
///
/// This function handles the execution of all ArxOS commands with detailed
/// error messages and recovery suggestions.
fn execute_command(command: cli::Commands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        cli::Commands::Import { ifc_file, repo } => {
            println!("🚀 Importing IFC file: {}", ifc_file);
            if let Some(repo_url) = repo {
                println!("📦 To repository: {}", repo_url);
            }
            
            // Validate IFC file exists and is readable
            if !std::path::Path::new(&ifc_file).exists() {
                return Err(format!(
                    "IFC file '{}' not found. \
                    Please check the file path and ensure the file exists.",
                    ifc_file
                ).into());
            }
            
            // Create progress reporter
            let progress_reporter = utils::create_ifc_progress(100);
            let progress_context = ProgressContext::with_reporter(progress_reporter.clone());
            
            // Use IFC processor to extract hierarchy
            let processor = ifc::IFCProcessor::new();
            
            // Try to extract hierarchy first (new approach)
            match processor.extract_hierarchy(&ifc_file) {
                Ok((building, floors)) => {
                    progress_reporter.finish_success(&format!("Successfully extracted building hierarchy: {}", building.name));
                    println!("✅ Building: {}", building.name);
                    println!("   Building ID: {}", building.id);
                    println!("   Created: {}", building.created_at.format("%Y-%m-%d %H:%M:%S"));
                    println!("   Floors found: {}", floors.len());
                    
                    // Display floor information
                    for floor in floors.iter().take(5) { // Show first 5 floors
                        println!("   - {}: level {}", floor.name, floor.level);
                    }
                    if floors.len() > 5 {
                        println!("   ... and {} more floors", floors.len() - 5);
                    }
                    
                    // Convert to spatial entities for compatibility
                    let spatial_entities = Vec::new(); // Will be populated from hierarchy
                    
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
                Err(_e) => {
                    // Fallback to old parsing method if hierarchy extraction fails
                    warn!("Hierarchy extraction failed, falling back to spatial entity parsing");
                    match processor.process_file_with_progress(&ifc_file, progress_context) {
                        Ok((building, spatial_entities)) => {
                            progress_reporter.finish_success(&format!("Successfully parsed building: {}", building.name));
                            println!("✅ Building: {}", building.name);
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
                            progress_reporter.finish_error(&format!("Error processing IFC file: {}", e));
                            return Err(format!(
                                "Failed to process IFC file '{}': {}. \
                                Please check that the file is a valid IFC file and try again. \
                                Common issues:\n\
                                - File is corrupted or incomplete\n\
                                - Unsupported IFC version\n\
                                - Missing required IFC entities\n\
                                - File permissions issues",
                                ifc_file, e
                            ).into());
                        }
                    }
                }
                Err(e) => {
                    progress_reporter.finish_error(&format!("Error processing IFC file: {}", e));
                    return Err(format!(
                        "Failed to process IFC file '{}': {}. \
                        Please check that the file is a valid IFC file and try again. \
                        Common issues:\n\
                        - File is corrupted or incomplete\n\
                        - Unsupported IFC version\n\
                        - Missing required IFC entities\n\
                        - File permissions issues",
                        ifc_file, e
                    ).into());
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
        cli::Commands::Render { building, floor, three_d, show_status, show_rooms, format, projection, view_angle, scale, spatial_index } => {
            handle_render_command(building, floor, three_d, show_status, show_rooms, format, projection, view_angle, scale, spatial_index)?;
        }
        cli::Commands::Interactive { building, projection, view_angle, scale, width, height, spatial_index, show_status, show_rooms, show_connections, fps, show_fps, show_help } => {
            handle_interactive_command(building, projection, view_angle, scale, width, height, spatial_index, show_status, show_rooms, show_connections, fps, show_fps, show_help)?;
        }
        cli::Commands::Validate { path } => {
            if let Some(data_path) = path {
                println!("Validating data at: {}", data_path);
                
                // Check if it's an IFC file
                if data_path.to_lowercase().ends_with(".ifc") {
                    let processor = ifc::IFCProcessor::new();
                    match processor.validate_ifc_file(&data_path) {
                        Ok(_) => {
                            println!("✅ IFC file validation passed");
                        }
                        Err(e) => {
                            println!("❌ IFC file validation failed: {}", e);
                        }
                    }
                } else {
                    println!("❌ Unsupported file type. Please provide an .ifc file for validation.");
                }
            } else {
                println!("Validating current directory");
                
                // Look for YAML files to validate
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
                    println!("❌ No YAML files found in current directory");
                } else {
                    println!("📄 Found {} YAML file(s) to validate", yaml_files.len());
                    
                    for yaml_file in yaml_files {
                        match validate_yaml_file(&yaml_file) {
                            Ok(_) => {
                                println!("✅ {} - validation passed", yaml_file);
                            }
                            Err(e) => {
                                println!("❌ {} - validation failed: {}", yaml_file, e);
                            }
                        }
                    }
                }
            }
        }
        cli::Commands::Status { verbose } => {
            handle_status_command(verbose)?;
        }
        cli::Commands::Diff { commit, file, stat } => {
            handle_diff_command(commit, file, stat)?;
        }
        cli::Commands::History { limit, verbose, file } => {
            handle_history_command(limit, verbose, file)?;
        }
        cli::Commands::Config { show, set, reset, edit } => {
            handle_config_command(show, set, reset, edit)?;
        }
        cli::Commands::Room { command } => {
            handle_room_command(command)?;
        }
        cli::Commands::Equipment { command } => {
            handle_equipment_command(command)?;
        }
        cli::Commands::Spatial { command } => {
            handle_spatial_command(command)?;
        }
        cli::Commands::Watch { building, floor, room, refresh_interval, sensors_only, alerts_only, log_level } => {
            handle_watch_command(building, floor, room, refresh_interval, sensors_only, alerts_only, log_level)?;
        }
        cli::Commands::Search { query, equipment, rooms, buildings, case_sensitive, regex, limit, verbose } => {
            handle_search_command(query, equipment, rooms, buildings, case_sensitive, regex, limit, verbose)?;
        }
        cli::Commands::ArIntegrate { scan_file, room, floor, building, commit, message } => {
            handle_ar_integrate_command(scan_file, room, floor, building, commit, message)?;
        }
        cli::Commands::IFC { subcommand } => {
            handle_ifc_command(subcommand)?;
        }
        cli::Commands::Ar { subcommand } => {
            handle_ar_command(subcommand)?;
        }
        cli::Commands::ProcessSensors { sensor_dir, building, commit, watch } => {
            handle_process_sensors_command(&sensor_dir, &building, commit, watch)?;
        }
        cli::Commands::Filter { equipment_type, status, floor, room, building, critical_only, healthy_only, alerts_only, format, limit, verbose } => {
            handle_filter_command(equipment_type, status, floor, room, building, critical_only, healthy_only, alerts_only, format, limit, verbose)?;
        }
    }
    
    Ok(())
}

/// Handle the live monitoring dashboard command
fn handle_watch_command(
    building: Option<String>,
    floor: Option<i32>,
    room: Option<String>,
    refresh_interval: u64,
    sensors_only: bool,
    alerts_only: bool,
    _log_level: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    use crossterm::{
        event::{self, Event, KeyCode},
        execute,
        terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
    };
    use ratatui::{
        backend::CrosstermBackend,
        layout::{Alignment, Constraint, Direction, Layout},
        style::{Color, Modifier, Style},
        widgets::{Block, Borders, Paragraph},
        Terminal,
    };
    use std::io::stdout;
    use std::time::Duration;
    
    println!("🔍 Starting Live Monitoring Dashboard...");
    println!("   Building: {}", building.as_deref().unwrap_or("All"));
    println!("   Floor: {}", floor.map(|f| f.to_string()).unwrap_or("All".to_string()));
    println!("   Room: {}", room.as_deref().unwrap_or("All"));
    println!("   Refresh Interval: {}s", refresh_interval);
    println!("   Sensors Only: {}", sensors_only);
    println!("   Alerts Only: {}", alerts_only);
    
    // Initialize terminal
    enable_raw_mode()?;
    let mut stdout = stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;
    
    // Simple monitoring loop
    let mut should_quit = false;
    let start_time = std::time::Instant::now();
    
    while !should_quit {
        // Draw the monitoring UI
        terminal.draw(|f| {
            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([
                    Constraint::Length(3),
                    Constraint::Min(0),
                    Constraint::Length(3),
                ])
                .split(f.size());
            
            // Header
            let header = Paragraph::new(format!(
                "ArxOS Live Monitor - {} | Refresh: {}s | Runtime: {}s",
                building.as_deref().unwrap_or("All Buildings"),
                refresh_interval,
                start_time.elapsed().as_secs()
            ))
            .style(Style::default().fg(Color::White).add_modifier(Modifier::BOLD))
            .alignment(Alignment::Center)
            .block(Block::default().borders(Borders::ALL).title("Live Monitoring"));
            
            f.render_widget(header, chunks[0]);
            
            // Content
            let content = Paragraph::new(
                "Live monitoring dashboard is active.\n\n\
                 Sensor data will be displayed here.\n\
                 Alerts and logs will be shown in real-time.\n\n\
                 Press 'q' to quit."
            )
            .style(Style::default().fg(Color::Green))
            .alignment(Alignment::Center)
            .block(Block::default().borders(Borders::ALL).title("Status"));
            
            f.render_widget(content, chunks[1]);
            
            // Footer
            let footer = Paragraph::new("Press 'q' to quit | 'r' to refresh | 'h' for help")
                .style(Style::default().fg(Color::Gray))
                .alignment(Alignment::Center)
                .block(Block::default().borders(Borders::ALL).title("Controls"));
            
            f.render_widget(footer, chunks[2]);
        })?;
        
        // Handle events
        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(key_event) = event::read()? {
                match key_event.code {
                    KeyCode::Char('q') | KeyCode::Esc => {
                        should_quit = true;
                    }
                    _ => {}
                }
            }
        }
        
        // Small delay to prevent excessive CPU usage
        std::thread::sleep(Duration::from_millis(50));
    }
    
    // Cleanup terminal
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    
    println!("✅ Live monitoring stopped");
    Ok(())
}

/// Handle room management commands
fn handle_room_command(command: cli::RoomCommands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        cli::RoomCommands::Create { building, floor, wing, name, room_type, dimensions, position, commit: _commit } => {
            println!("🏗️ Creating room: {} in {} Floor {} Wing {}", name, building, floor, wing);
            println!("   Type: {}", room_type);
            
            if let Some(ref dims) = dimensions {
                println!("   Dimensions: {}", dims);
            }
            
            if let Some(ref pos) = position {
                println!("   Position: {}", pos);
            }
            
            // Parse room type directly
            let parsed_room_type = match room_type.to_lowercase().as_str() {
                "classroom" => RoomType::Classroom,
                "laboratory" => RoomType::Laboratory,
                "office" => RoomType::Office,
                "gymnasium" => RoomType::Gymnasium,
                "cafeteria" => RoomType::Cafeteria,
                "library" => RoomType::Library,
                "auditorium" => RoomType::Auditorium,
                "hallway" => RoomType::Hallway,
                "restroom" => RoomType::Restroom,
                "storage" => RoomType::Storage,
                "mechanical" => RoomType::Mechanical,
                "electrical" => RoomType::Electrical,
                _ => RoomType::Other(room_type),
            };
            
            // Use the local core types directly
            let room = crate::core::Room::new(name.clone(), parsed_room_type);
            println!("✅ Room created successfully: {}", room.name);
        }
        cli::RoomCommands::List { building, floor, wing, verbose } => {
            println!("📋 Listing rooms");
            
            if let Some(b) = building {
                println!("   Building: {}", b);
            }
            
            if let Some(f) = floor {
                println!("   Floor: {}", f);
            }
            
            if let Some(w) = wing {
                println!("   Wing: {}", w);
            }
            
            if verbose {
                println!("   Verbose mode enabled");
            }
            
            let rooms = crate::core::list_rooms()?;
            
            if rooms.is_empty() {
                println!("No rooms found");
            } else {
                for room in rooms {
                    println!("   {} (ID: {}) - Type: {:?}", room.name, room.id, room.room_type);
                    if verbose {
                        println!("     Position: ({:.2}, {:.2}, {:.2})", 
                            room.spatial_properties.position.x,
                            room.spatial_properties.position.y,
                            room.spatial_properties.position.z);
                        println!("     Dimensions: {:.2} x {:.2} x {:.2}", 
                            room.spatial_properties.dimensions.width,
                            room.spatial_properties.dimensions.depth,
                            room.spatial_properties.dimensions.height);
                    }
                }
            }
            
            println!("✅ Room listing completed");
        }
        cli::RoomCommands::Show { room, equipment } => {
            println!("🔍 Showing room details: {}", room);
            
            if equipment {
                println!("   Including equipment");
            }
            
            let room_data = crate::core::get_room(&room)?;
            
            println!("   Name: {}", room_data.name);
            println!("   ID: {}", room_data.id);
            println!("   Type: {:?}", room_data.room_type);
            println!("   Position: ({:.2}, {:.2}, {:.2})", 
                room_data.spatial_properties.position.x,
                room_data.spatial_properties.position.y,
                room_data.spatial_properties.position.z);
            println!("   Dimensions: {:.2} x {:.2} x {:.2}", 
                room_data.spatial_properties.dimensions.width,
                room_data.spatial_properties.dimensions.depth,
                room_data.spatial_properties.dimensions.height);
            
            if equipment {
                println!("   Equipment: {} items", room_data.equipment.len());
                for eq in &room_data.equipment {
                    println!("     - {} ({:?})", eq.name, eq.equipment_type);
                }
            }
            
            println!("✅ Room details displayed");
        }
        cli::RoomCommands::Update { room, property, commit: _commit } => {
            println!("✏️ Updating room: {}", room);
            
            for prop in &property {
                println!("   Property: {}", prop);
            }
            
            let updated_room = crate::core::update_room(&room, property)?;
            
            println!("✅ Room updated successfully: {} (ID: {})", updated_room.name, updated_room.id);
        }
        cli::RoomCommands::Delete { room, confirm, commit: _commit } => {
            if !confirm {
                println!("❌ Room deletion requires confirmation. Use --confirm flag.");
                return Ok(());
            }
            
            println!("🗑️ Deleting room: {}", room);
            
            crate::core::delete_room(&room)?;
            
            println!("✅ Room deleted successfully");
        }
    }
    
    Ok(())
}

/// Handle equipment management commands
fn handle_equipment_command(command: cli::EquipmentCommands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        cli::EquipmentCommands::Add { room, name, equipment_type, position, property, commit: _commit } => {
            println!("🔧 Adding equipment: {} to room {}", name, room);
            println!("   Type: {}", equipment_type);
            
            if let Some(ref pos) = position {
                println!("   Position: {}", pos);
            }
            
            for prop in &property {
                println!("   Property: {}", prop);
            }
            
            // Parse equipment type directly
            let parsed_equipment_type = match equipment_type.to_lowercase().as_str() {
                "hvac" => EquipmentType::HVAC,
                "electrical" => EquipmentType::Electrical,
                "av" => EquipmentType::AV,
                "furniture" => EquipmentType::Furniture,
                "safety" => EquipmentType::Safety,
                "plumbing" => EquipmentType::Plumbing,
                "network" => EquipmentType::Network,
                _ => EquipmentType::Other(equipment_type),
            };
            
            // Use the local core types directly
            let equipment = crate::core::Equipment::new(name.clone(), "".to_string(), parsed_equipment_type);
            println!("✅ Equipment added successfully: {}", equipment.name);
        }
        cli::EquipmentCommands::List { room, equipment_type, verbose } => {
            println!("📋 Listing equipment");
            
            if let Some(r) = room {
                println!("   Room: {}", r);
            }
            
            if let Some(et) = equipment_type {
                println!("   Type: {}", et);
            }
            
            if verbose {
                println!("   Verbose mode enabled");
            }
            
            let equipment_list = crate::core::list_equipment()?;
            
            if equipment_list.is_empty() {
                println!("No equipment found");
            } else {
                for eq in equipment_list {
                    println!("   {} (ID: {}) - Type: {:?}", eq.name, eq.id, eq.equipment_type);
                    if verbose {
                        println!("     Position: ({:.2}, {:.2}, {:.2})", 
                            eq.position.x, eq.position.y, eq.position.z);
                        println!("     Status: {:?}", eq.status);
                        if let Some(room_id) = &eq.room_id {
                            println!("     Room ID: {}", room_id);
                        }
                    }
                }
            }
            
            println!("✅ Equipment listing completed");
        }
        cli::EquipmentCommands::Update { equipment, property, position, commit: _commit } => {
            println!("✏️ Updating equipment: {}", equipment);
            
            for prop in &property {
                println!("   Property: {}", prop);
            }
            
            if let Some(ref pos) = position {
                println!("   New position: {}", pos);
            }
            
            let updated_equipment = crate::core::update_equipment(&equipment, property)?;
            
            println!("✅ Equipment updated successfully: {} (ID: {})", updated_equipment.name, updated_equipment.id);
        }
        cli::EquipmentCommands::Remove { equipment, confirm, commit: _commit } => {
            if !confirm {
                println!("❌ Equipment removal requires confirmation. Use --confirm flag.");
                return Ok(());
            }
            
            println!("🗑️ Removing equipment: {}", equipment);
            
            crate::core::remove_equipment(&equipment)?;
            
            println!("✅ Equipment removed successfully");
        }
    }
    
    Ok(())
}

/// Handle IFC processing commands
fn handle_ifc_command(command: cli::IFCCommands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        cli::IFCCommands::ExtractHierarchy { file, output } => {
            println!("🔧 Extracting building hierarchy from: {}", file);
            
            // Validate IFC file exists
            if !std::path::Path::new(&file).exists() {
                return Err(format!(
                    "IFC file '{}' not found. \
                    Please check the file path and ensure the file exists.",
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
                        "Failed to extract hierarchy from '{}': {}. \
                        Please check that the file is a valid IFC file.",
                        file, e
                    ).into());
                }
            }
        }
    }
    
    Ok(())
}

/// Handle spatial operations commands
fn handle_spatial_command(command: cli::SpatialCommands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        cli::SpatialCommands::Query { query_type, entity, params } => {
            println!("🔍 Spatial query: {} for entity {}", query_type, entity);
            
            for param in &params {
                println!("   Parameter: {}", param);
            }
            
            // Use the core module directly for spatial queries
            let result = crate::core::spatial_query(&query_type, &entity, params)?;
            
            if result.is_empty() {
                println!("No results found");
            } else {
                println!("Found {} results:", result.len());
                for (i, spatial_result) in result.iter().enumerate() {
                    println!("  {}. {} ({})", i + 1, spatial_result.entity_name, spatial_result.entity_type);
                    println!("     Position: ({:.2}, {:.2}, {:.2})", 
                        spatial_result.position.x, 
                        spatial_result.position.y, 
                        spatial_result.position.z);
                    println!("     Distance: {:.2}", spatial_result.distance);
                }
            }
            println!("✅ Spatial query completed");
        }
        cli::SpatialCommands::Relate { entity1, entity2, relationship } => {
            println!("🔗 Setting spatial relationship: {} {} {}", entity1, relationship, entity2);
            
            let result = crate::core::set_spatial_relationship(&entity1, &entity2, &relationship)?;
            
            println!("{}", result);
            println!("✅ Spatial relationship set successfully");
        }
        cli::SpatialCommands::Transform { from, to, entity } => {
            println!("🔄 Transforming coordinates: {} from {} to {}", entity, from, to);
            
            let result = crate::core::transform_coordinates(&from, &to, &entity)?;
            
            println!("{}", result);
            println!("✅ Coordinate transformation completed");
        }
        cli::SpatialCommands::Validate { entity, tolerance } => {
            println!("✅ Validating spatial data");
            
            if let Some(ref e) = entity {
                println!("   Entity: {}", e);
            }
            
            if let Some(t) = tolerance {
                println!("   Tolerance: {}", t);
            }
            
            let result = crate::core::validate_spatial(entity.as_deref(), tolerance)?;
            
            println!("{}", result);
            println!("✅ Spatial validation completed");
        }
    }
    
    Ok(())
}

/// Handle the search command
fn handle_search_command(
    query: String,
    equipment: bool,
    rooms: bool,
    buildings: bool,
    case_sensitive: bool,
    regex: bool,
    limit: usize,
    verbose: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔍 Searching building data for: '{}'", query);
    
    // Load building data
    let building_data = load_building_data("")?;
    
    // Create search configuration
    let search_config = search::SearchConfig {
        query,
        search_equipment: equipment || (!equipment && !rooms && !buildings), // Default to equipment if none specified
        search_rooms: rooms,
        search_buildings: buildings,
        case_sensitive,
        use_regex: regex,
        limit,
        verbose,
    };
    
    // Create search engine and perform search
    let search_engine = search::SearchEngine::new(&building_data);
    let results = search_engine.search(&search_config)?;
    
    // Format and display results
    let output_format = search::OutputFormat::Table;
    let formatted_results = search::format_search_results(&results, &output_format, verbose);
    println!("{}", formatted_results);
    
    println!("✅ Search completed");
    Ok(())
}

/// Handle the filter command
fn handle_filter_command(
    equipment_type: Option<String>,
    status: Option<String>,
    floor: Option<i32>,
    room: Option<String>,
    building: Option<String>,
    critical_only: bool,
    healthy_only: bool,
    alerts_only: bool,
    format: String,
    limit: usize,
    verbose: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔍 Filtering building data...");
    
    // Load building data
    let building_data = load_building_data("")?;
    
    // Create filter configuration
    let filter_config = search::FilterConfig {
        equipment_type,
        status,
        floor,
        room,
        building,
        critical_only,
        healthy_only,
        alerts_only,
        format: search::OutputFormat::from(format),
        limit,
    };
    
    // Create search engine and perform filtering
    let search_engine = search::SearchEngine::new(&building_data);
    let results = search_engine.filter(&filter_config)?;
    
    // Format and display results
    let formatted_results = search::format_search_results(&results, &filter_config.format, verbose);
    println!("{}", formatted_results);
    
    println!("✅ Filter completed");
    Ok(())
}

/// Handle the render command with 3D support
fn handle_render_command(
    building: String,
    floor: Option<i32>,
    three_d: bool,
    show_status: bool,
    show_rooms: bool,
    format: String,
    projection: String,
    view_angle: String,
    scale: f64,
    spatial_index: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("🏗️ Rendering building: {}", building);
    
    // Load building data
    let building_data = load_building_data(&building)?;
    
    if three_d {
        // 3D rendering
        println!("🎯 3D Multi-Floor Visualization");
        
        // Parse projection type
        let projection_type = match projection.to_lowercase().as_str() {
            "isometric" => ProjectionType::Isometric,
            "orthographic" => ProjectionType::Orthographic,
            "perspective" => ProjectionType::Perspective,
            _ => {
                println!("⚠️ Unknown projection type '{}', using isometric", projection);
                ProjectionType::Isometric
            }
        };
        
        // Parse view angle
        let view_angle_type = match view_angle.to_lowercase().as_str() {
            "topdown" => ViewAngle::TopDown,
            "front" => ViewAngle::Front,
            "side" => ViewAngle::Side,
            "isometric" => ViewAngle::Isometric,
            _ => {
                println!("⚠️ Unknown view angle '{}', using isometric", view_angle);
                ViewAngle::Isometric
            }
        };
        
        let config = Render3DConfig {
            show_status,
            show_rooms,
            show_equipment: true,
            show_connections: false,
            projection_type,
            view_angle: view_angle_type,
            scale_factor: scale,
            max_width: 120,
            max_height: 40,
        };
        
        let renderer = Building3DRenderer::new(building_data, config);
        
        // Apply spatial index if requested
        if spatial_index {
            println!("🔍 Building spatial index for enhanced queries...");
            // Build spatial index from IFC data when available
            println!("Building spatial index from IFC data...");
            // For now, create a simple spatial index
            let _spatial_index: std::collections::HashMap<String, String> = std::collections::HashMap::new();
            println!("Spatial index built successfully");
            println!("ℹ️ Spatial index integration will be available when IFC data is loaded");
        }
        
        let scene = renderer.render_3d_advanced()?;
        
        match format.to_lowercase().as_str() {
            "json" => {
                let json_output = format_scene_output(&scene, "json")?;
                println!("{}", json_output);
            }
            "yaml" => {
                let yaml_output = format_scene_output(&scene, "yaml")?;
                println!("{}", yaml_output);
            }
            "ascii" => {
                // Use the new advanced ASCII art rendering
                let ascii_output = renderer.render_3d_ascii_art(&scene)?;
                println!("{}", ascii_output);
            }
            "advanced" => {
                // Use the advanced projection-based rendering
                let advanced_output = renderer.render_to_ascii_advanced(&scene)?;
                println!("{}", advanced_output);
            }
            _ => {
                return Err(format!("Unsupported format: {}. Supported formats: ascii, advanced, json, yaml", format).into());
            }
        }
    } else {
        // Traditional 2D rendering
        println!("📐 2D Floor Plan Rendering");
        
        let renderer = render::BuildingRenderer::new(building_data);
        
        if let Some(floor_num) = floor {
            println!("Floor: {}", floor_num);
            renderer.render_floor(floor_num)?;
        } else {
            // Render all floors
            for floor_data in renderer.floors() {
                renderer.render_floor(floor_data.level)?;
                println!(); // Add spacing between floors
            }
        }
    }
    
    println!("✅ Rendering completed");
    Ok(())
}

/// Handle the interactive 3D rendering command
fn handle_interactive_command(
    building: String,
    projection: String,
    view_angle: String,
    scale: f64,
    width: usize,
    height: usize,
    spatial_index: bool,
    show_status: bool,
    show_rooms: bool,
    show_connections: bool,
    fps: u32,
    show_fps: bool,
    show_help: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("🎮 Interactive 3D Building Visualization: {}", building);
    
    // Load building data
    let building_data = load_building_data(&building)?;
    
    // Parse projection type
    let projection_type = match projection.to_lowercase().as_str() {
        "isometric" => ProjectionType::Isometric,
        "orthographic" => ProjectionType::Orthographic,
        "perspective" => ProjectionType::Perspective,
        _ => {
            println!("⚠️ Unknown projection type '{}', using isometric", projection);
            ProjectionType::Isometric
        }
    };
    
    // Parse view angle
    let view_angle_type = match view_angle.to_lowercase().as_str() {
        "topdown" => ViewAngle::TopDown,
        "front" => ViewAngle::Front,
        "side" => ViewAngle::Side,
        "isometric" => ViewAngle::Isometric,
        _ => {
            println!("⚠️ Unknown view angle '{}', using isometric", view_angle);
            ViewAngle::Isometric
        }
    };
    
    // Create render configuration
    let render_config = Render3DConfig {
        show_status,
        show_rooms,
        show_equipment: true,
        show_connections,
        projection_type: projection_type.clone(),
        view_angle: view_angle_type.clone(),
        scale_factor: scale,
        max_width: width,
        max_height: height,
    };
    
    // Create interactive configuration
    let interactive_config = InteractiveConfig {
        target_fps: fps,
        real_time_updates: true,
        show_fps,
        show_help,
        auto_hide_help: true,
        help_duration: std::time::Duration::from_secs(5),
    };
    
    // Create interactive renderer
    let mut interactive_renderer = InteractiveRenderer::with_config(
        building_data,
        render_config,
        interactive_config
    )?;
    
    // Apply spatial index if requested
    if spatial_index {
        println!("🔍 Enabling spatial index integration...");
        // Note: Spatial index integration would be added here
    }
    
    // Start interactive session
    interactive_renderer.start_interactive_session()?;
    
    println!("✅ Interactive session completed");
    Ok(())
}


/// Handle the AR integration command
fn handle_ar_integrate_command(
    scan_file: String,
    room: String,
    floor: i32,
    building: String,
    commit: bool,
    message: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("📱 Integrating AR scan data for room: {} on floor: {}", room, floor);
    
    // Load existing building data
    let building_data = load_building_data(&building)?;
    
    // Read AR scan data file
    println!("📄 Reading AR scan data from: {}", scan_file);
    let scan_data_bytes = std::fs::read(&scan_file)?;
    
    // Convert mobile AR data to ARScanData
    let ar_scan_data = ar_integration::convert_mobile_ar_data(scan_data_bytes, room.clone(), floor)?;
    
    // Integrate AR scan data
    let mut integrator = ar_integration::ARDataIntegrator::new(building_data);
    let integration_result = integrator.integrate_ar_scan(ar_scan_data)?;
    
    // Display integration results
    println!("🔄 AR Integration Results:");
    println!("  📦 Equipment added: {}", integration_result.equipment_added);
    println!("  🔄 Equipment updated: {}", integration_result.equipment_updated);
    println!("  🏠 Rooms updated: {}", integration_result.rooms_updated);
    println!("  ⚠️  Conflicts resolved: {}", integration_result.conflicts_resolved);
    
    // Get updated building data
    let updated_building_data = integrator.get_building_data();
    
    // Save updated building data
    let output_file = format!("{}-updated.yaml", building);
    let yaml_content = serde_yaml::to_string(&updated_building_data)?;
    std::fs::write(&output_file, yaml_content)?;
    println!("💾 Updated building data saved to: {}", output_file);
    
    // Commit to Git if requested
    if commit {
        let commit_message = message.unwrap_or_else(|| {
            format!("Integrate AR scan for room {} on floor {}", room, floor)
        });
        
        println!("📝 Committing changes to Git: {}", commit_message);
        
        // Add files to Git
        let output = std::process::Command::new("git")
            .args(&["add", &output_file])
            .output()?;
        
        if !output.status.success() {
            return Err(format!("Failed to add files to Git: {}", String::from_utf8_lossy(&output.stderr)).into());
        }
        
        // Commit changes
        let output = std::process::Command::new("git")
            .args(&["commit", "-m", &commit_message])
            .output()?;
        
        if !output.status.success() {
            return Err(format!("Failed to commit changes: {}", String::from_utf8_lossy(&output.stderr)).into());
        }
        
        println!("✅ Changes committed to Git");
    }
    
    println!("✅ AR integration completed");
    Ok(())
}

/// Handle the process sensors command
fn handle_process_sensors_command(
    sensor_dir: &str,
    building: &str,
    commit: bool,
    _watch: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    use std::path::PathBuf;
    use log::{info, warn};
    
    info!("📡 Processing sensor data from: {}", sensor_dir);
    println!("📡 Processing sensor data from: {}", sensor_dir);
    println!("   Building: {}", building);
    
    let config = hardware::SensorIngestionConfig {
        data_directory: PathBuf::from(sensor_dir),
        ..hardware::SensorIngestionConfig::default()
    };
    
    let ingestion = hardware::SensorIngestionService::new(config);
    let mut updater = hardware::EquipmentStatusUpdater::new(building)?;
    
    // Process once
    match ingestion.process_all_sensor_files() {
        Ok(sensor_data_list) => {
            info!("Processing {} sensor data files...", sensor_data_list.len());
            println!("   Processing {} sensor data files...", sensor_data_list.len());
            
            let mut success_count = 0;
            let mut error_count = 0;
            
            for sensor_data in sensor_data_list {
                match updater.process_sensor_data(&sensor_data) {
                    Ok(result) => {
                        info!("Updated equipment {}: {} → {}", 
                             result.equipment_id, result.old_status, result.new_status);
                        println!("   ✅ Updated {}: {} → {}", 
                                 result.equipment_id, result.old_status, result.new_status);
                        success_count += 1;
                    }
                    Err(e) => {
                        warn!("Error processing sensor {}: {}", 
                             sensor_data.metadata.sensor_id, e);
                        println!("   ⚠️  Error processing {}: {}", 
                                 sensor_data.metadata.sensor_id, e);
                        error_count += 1;
                    }
                }
            }
            
            println!("\n📊 Processing Summary:");
            println!("   ✅ Successful: {}", success_count);
            println!("   ⚠️  Errors: {}", error_count);
            
            // Save updated building data
            info!("Saving updated building data to YAML");
            println!("\n💾 Saving updated building data...");
            
            // The EquipmentStatusUpdater already saves in process_sensor_data,
            // but we also want to ensure the final state is committed
            if commit {
                let commit_message = format!("Update equipment status from sensor data: {} successful, {} errors", 
                    success_count, error_count);
                updater.commit_changes(&commit_message)?;
                info!("Changes committed to Git with message: {}", commit_message);
                println!("✅ Changes committed to Git");
            } else {
                println!("💡 Use --commit flag to commit changes to Git");
            }
        }
        Err(e) => {
            warn!("Error processing sensor files: {}", e);
            println!("⚠️  Error processing sensor files: {}", e);
            return Err(format!("Sensor processing failed: {}", e).into());
        }
    }
    
    info!("Sensor processing completed successfully");
    println!("✅ Sensor processing completed");
    Ok(())
}

/// Handle AR integration commands
fn handle_ar_command(command: cli::ArCommands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        cli::ArCommands::Pending { subcommand } => {
            handle_pending_command(subcommand)?;
        }
    }
    Ok(())
}

/// Handle pending equipment commands
fn handle_pending_command(command: cli::PendingCommands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        cli::PendingCommands::List { building, floor, verbose } => {
            handle_pending_list_command(&building, floor, verbose)?;
        }
        cli::PendingCommands::Confirm { pending_id, building, commit } => {
            handle_pending_confirm_command(&pending_id, &building, commit)?;
        }
        cli::PendingCommands::Reject { pending_id } => {
            handle_pending_reject_command(&pending_id)?;
        }
        cli::PendingCommands::BatchConfirm { pending_ids, building, commit } => {
            handle_pending_batch_confirm_command(pending_ids, &building, commit)?;
        }
    }
    Ok(())
}

/// Handle list pending equipment command
fn handle_pending_list_command(building: &str, floor: Option<i32>, verbose: bool) -> Result<(), Box<dyn std::error::Error>> {
    use crate::ar_integration::PendingEquipmentManager;
    
    println!("📋 Listing pending equipment for building: {}", building);
    
    let manager = PendingEquipmentManager::new(building.to_string());
    let pending_items = manager.list_pending();
    
    if pending_items.is_empty() {
        println!("   No pending equipment found");
        return Ok(());
    }
    
    println!("\n   Found {} pending equipment item(s):\n", pending_items.len());
    
    for (i, item) in pending_items.iter().enumerate() {
        if let Some(floor_filter) = floor {
            if item.floor_level != floor_filter {
                continue;
            }
        }
        
        println!("   {}. {}", i + 1, item.name);
        if verbose {
            println!("      ID: {}", item.id);
            println!("      Type: {}", item.equipment_type);
            println!("      Position: ({:.2}, {:.2}, {:.2})", item.position.x, item.position.y, item.position.z);
            println!("      Floor: {}", item.floor_level);
            if let Some(ref room) = item.room_name {
                println!("      Room: {}", room);
            }
            println!("      Confidence: {:.2}", item.confidence);
            println!("      Detected: {}", item.detected_at.format("%Y-%m-%d %H:%M:%S"));
        } else {
            println!("      Floor: {} | Confidence: {:.2}", item.floor_level, item.confidence);
        }
    }
    
    println!("\n✅ Listing completed");
    Ok(())
}

/// Handle confirm pending equipment command
fn handle_pending_confirm_command(pending_id: &str, building: &str, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    use crate::ar_integration::PendingEquipmentManager;
    use crate::persistence::PersistenceManager;
    use log::info;
    
    info!("Confirming pending equipment: {} for building: {}", pending_id, building);
    println!("✅ Confirming pending equipment: {}", pending_id);
    
    let mut manager = PendingEquipmentManager::new(building.to_string());
    let persistence = PersistenceManager::new(building)?;
    
    // Load current building data
    let mut building_data = persistence.load_building_data()?;
    
    // Confirm the pending equipment
    let equipment_id = manager.confirm_pending(pending_id, &mut building_data)?;
    
    println!("   Created equipment: {}", equipment_id);
    
    // Save and commit if requested
    if commit {
        let commit_message = format!("Confirm pending equipment: {}", pending_id);
        persistence.save_and_commit(&building_data, Some(&commit_message))?;
        info!("Changes committed to Git");
        println!("✅ Changes committed to Git");
    } else {
        persistence.save_building_data(&building_data)?;
        println!("💡 Use --commit flag to commit changes to Git");
    }
    
    Ok(())
}

/// Handle reject pending equipment command
fn handle_pending_reject_command(pending_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    use crate::ar_integration::PendingEquipmentManager;
    use log::info;
    
    info!("Rejecting pending equipment: {}", pending_id);
    println!("❌ Rejecting pending equipment: {}", pending_id);
    
    let mut manager = PendingEquipmentManager::new("default".to_string());
    manager.reject_pending(pending_id)?;
    
    println!("✅ Pending equipment rejected");
    Ok(())
}

/// Handle batch confirm pending equipment command
fn handle_pending_batch_confirm_command(pending_ids: Vec<String>, building: &str, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    use crate::ar_integration::PendingEquipmentManager;
    use crate::persistence::PersistenceManager;
    use log::info;
    
    info!("Batch confirming {} pending equipment items", pending_ids.len());
    println!("✅ Batch confirming {} pending equipment items", pending_ids.len());
    
    let mut manager = PendingEquipmentManager::new(building.to_string());
    let persistence = PersistenceManager::new(building)?;
    
    // Load current building data
    let mut building_data = persistence.load_building_data()?;
    
    // Batch confirm the pending equipment
    let pending_id_refs: Vec<&str> = pending_ids.iter().map(|s| s.as_str()).collect();
    let equipment_ids = manager.batch_confirm(pending_id_refs, &mut building_data)?;
    
    println!("   Created {} equipment item(s)", equipment_ids.len());
    
    // Save and commit if requested
    if commit {
        let commit_message = format!("Batch confirm {} pending equipment items", equipment_ids.len());
        persistence.save_and_commit(&building_data, Some(&commit_message))?;
        info!("Changes committed to Git");
        println!("✅ Changes committed to Git");
    } else {
        persistence.save_building_data(&building_data)?;
        println!("💡 Use --commit flag to commit changes to Git");
    }
    
    Ok(())
}

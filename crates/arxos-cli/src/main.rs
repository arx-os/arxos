//! ArxOS CLI - Command-line interface
//!
//! This is the main CLI application for ArxOS, providing terminal-based
//! building management capabilities.

use clap::Parser;
use cli::Cli;
use log::info;
use arxos_core::{ArxOSCore, parse_room_type, parse_equipment_type, Building, BuildingData};

/// Load building data from YAML files
fn load_building_data(building_name: &str) -> Result<BuildingData, Box<dyn std::error::Error>> {
    // Look for YAML files in current directory
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
        return Err(format!("No YAML files found. Please run 'import' first to generate building data.").into());
    }
    
    // Try to find a YAML file that matches the building name
    let yaml_file = yaml_files.iter()
        .find(|file| file.to_lowercase().contains(&building_name.to_lowercase()))
        .or_else(|| yaml_files.first())
        .ok_or("No suitable YAML file found")?;
    
    println!("📄 Loading building data from: {}", yaml_file);
    
    // Read and parse the YAML file
    let yaml_content = std::fs::read_to_string(yaml_file)?;
    let building_data: BuildingData = serde_yaml::from_str(&yaml_content)?;
    
    Ok(building_data)
}

/// Validate YAML building data file
fn validate_yaml_file(file_path: &str) -> Result<(), Box<dyn std::error::Error>> {
    // Read and parse the YAML file
    let yaml_content = std::fs::read_to_string(file_path)?;
    let building_data: BuildingData = serde_yaml::from_str(&yaml_content)?;
    
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

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging
    env_logger::init();
    
    info!("Starting ArxOS v2.0");
    let cli = Cli::parse();
    
    match cli.command {
        cli::Commands::Import { ifc_file, repo } => {
            println!("🚀 Importing IFC file: {}", ifc_file);
            if let Some(repo_url) = repo {
                println!("📦 To repository: {}", repo_url);
            }
            
            // Create progress reporter
            let progress_reporter = utils::create_ifc_progress(100);
            let progress_context = ProgressContext::with_reporter(progress_reporter.clone());
            
            // Use real IFC processor with progress
            let processor = ifc::IFCProcessor::new();
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
                    let serializer = arxos_core::BuildingYamlSerializer::new();
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
            let building_data: BuildingData = serde_yaml::from_str(&yaml_content)?;
            
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
            
            // Load real building data from YAML files
            let building_data = load_building_data(&building)?;
            let renderer = render::BuildingRenderer::new(building_data);
            renderer.render_floor(floor.unwrap_or(1))?;
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
    let mut core = ArxOSCore::new().map_err(|e| format!("Failed to initialize core: {}", e))?;
    
    match command {
        cli::RoomCommands::Create { building, floor, wing, name, room_type, dimensions, position } => {
            println!("🏗️ Creating room: {} in {} Floor {} Wing {}", name, building, floor, wing);
            println!("   Type: {}", room_type);
            
            if let Some(ref dims) = dimensions {
                println!("   Dimensions: {}", dims);
            }
            
            if let Some(ref pos) = position {
                println!("   Position: {}", pos);
            }
            
            let parsed_room_type = parse_room_type(&room_type);
            let room = core.room_manager().create_room(
                name.clone(),
                parsed_room_type,
                floor,
                wing.clone(),
                dimensions.clone(),
                position.clone(),
            ).map_err(|e| format!("Failed to create room: {}", e))?;
            
            println!("✅ Room created successfully: {} (ID: {})", room.name, room.id);
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
            
            let rooms = core.room_manager().list_rooms()
                .map_err(|e| format!("Failed to list rooms: {}", e))?;
            
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
            
            let room_data = core.room_manager().get_room(&room)
                .map_err(|e| format!("Failed to get room: {}", e))?;
            
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
        cli::RoomCommands::Update { room, property } => {
            println!("✏️ Updating room: {}", room);
            
            for prop in &property {
                println!("   Property: {}", prop);
            }
            
            let updated_room = core.room_manager().update_room(&room, property)
                .map_err(|e| format!("Failed to update room: {}", e))?;
            
            println!("✅ Room updated successfully: {} (ID: {})", updated_room.name, updated_room.id);
        }
        cli::RoomCommands::Delete { room, confirm } => {
            if !confirm {
                println!("❌ Room deletion requires confirmation. Use --confirm flag.");
                return Ok(());
            }
            
            println!("🗑️ Deleting room: {}", room);
            
            core.room_manager().delete_room(&room)
                .map_err(|e| format!("Failed to delete room: {}", e))?;
            
            println!("✅ Room deleted successfully");
        }
    }
    
    Ok(())
}

/// Handle equipment management commands
fn handle_equipment_command(command: cli::EquipmentCommands) -> Result<(), Box<dyn std::error::Error>> {
    let mut core = ArxOSCore::new().map_err(|e| format!("Failed to initialize core: {}", e))?;
    
    match command {
        cli::EquipmentCommands::Add { room, name, equipment_type, position, property } => {
            println!("🔧 Adding equipment: {} to room {}", name, room);
            println!("   Type: {}", equipment_type);
            
            if let Some(ref pos) = position {
                println!("   Position: {}", pos);
            }
            
            for prop in &property {
                println!("   Property: {}", prop);
            }
            
            let parsed_equipment_type = parse_equipment_type(&equipment_type);
            let equipment = core.equipment_manager().add_equipment(
                name.clone(),
                parsed_equipment_type,
                Some(room.clone()),
                position.clone(),
                property.clone(),
            ).map_err(|e| format!("Failed to add equipment: {}", e))?;
            
            println!("✅ Equipment added successfully: {} (ID: {})", equipment.name, equipment.id);
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
            
            let equipment_list = core.equipment_manager().list_equipment()
                .map_err(|e| format!("Failed to list equipment: {}", e))?;
            
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
        cli::EquipmentCommands::Update { equipment, property, position } => {
            println!("✏️ Updating equipment: {}", equipment);
            
            for prop in &property {
                println!("   Property: {}", prop);
            }
            
            if let Some(ref pos) = position {
                println!("   New position: {}", pos);
            }
            
            let updated_equipment = core.equipment_manager().update_equipment(
                &equipment,
                property,
                position,
            ).map_err(|e| format!("Failed to update equipment: {}", e))?;
            
            println!("✅ Equipment updated successfully: {} (ID: {})", updated_equipment.name, updated_equipment.id);
        }
        cli::EquipmentCommands::Remove { equipment, confirm } => {
            if !confirm {
                println!("❌ Equipment removal requires confirmation. Use --confirm flag.");
                return Ok(());
            }
            
            println!("🗑️ Removing equipment: {}", equipment);
            
            core.equipment_manager().remove_equipment(&equipment)
                .map_err(|e| format!("Failed to remove equipment: {}", e))?;
            
            println!("✅ Equipment removed successfully");
        }
    }
    
    Ok(())
}

/// Handle spatial operations commands
fn handle_spatial_command(command: cli::SpatialCommands) -> Result<(), Box<dyn std::error::Error>> {
    let mut core = ArxOSCore::new().map_err(|e| format!("Failed to initialize core: {}", e))?;
    
    match command {
        cli::SpatialCommands::Query { query_type, entity, params } => {
            println!("🔍 Spatial query: {} for entity {}", query_type, entity);
            
            for param in &params {
                println!("   Parameter: {}", param);
            }
            
            let result = core.spatial_manager().query_spatial(&query_type, &entity, params)
                .map_err(|e| format!("Failed to execute spatial query: {}", e))?;
            
            println!("{}", result);
            println!("✅ Spatial query completed");
        }
        cli::SpatialCommands::Relate { entity1, entity2, relationship } => {
            println!("🔗 Setting spatial relationship: {} {} {}", entity1, relationship, entity2);
            
            let result = core.spatial_manager().set_spatial_relationship(&entity1, &entity2, &relationship)
                .map_err(|e| format!("Failed to set spatial relationship: {}", e))?;
            
            println!("{}", result);
            println!("✅ Spatial relationship set successfully");
        }
        cli::SpatialCommands::Transform { from, to, entity } => {
            println!("🔄 Transforming coordinates: {} from {} to {}", entity, from, to);
            
            let result = core.spatial_manager().transform_coordinates(&from, &to, &entity)
                .map_err(|e| format!("Failed to transform coordinates: {}", e))?;
            
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
            
            let result = core.spatial_manager().validate_spatial(entity.as_deref(), tolerance)
                .map_err(|e| format!("Failed to validate spatial data: {}", e))?;
            
            println!("{}", result);
            println!("✅ Spatial validation completed");
        }
    }
    
    Ok(())
}

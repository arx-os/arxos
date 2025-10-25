//! # ArxOS CLI - Command-line Interface
//!
//! This is the main CLI application for ArxOS, providing comprehensive terminal-based
//! building management capabilities with a rich command set and interactive features.
//!
//! ## Features
//!
//! - **Building Data Management**: Import IFC files, export to Git repositories
//! - **3D Visualization**: Interactive 3D building rendering with terminal graphics
//! - **Git Integration**: Full Git workflow support (status, diff, history)
//! - **Live Monitoring**: Real-time building monitoring dashboard
//! - **Configuration Management**: Comprehensive configuration system
//! - **Room & Equipment Management**: CRUD operations for building components
//! - **Spatial Operations**: Advanced spatial queries and operations
//!
//! ## Commands
//!
//! ### Core Commands
//! - `import <file.ifc>` - Import IFC building data
//! - `export <repo>` - Export building data to Git repository
//! - `render <building>` - Render 3D building visualization
//! - `validate [path]` - Validate building data integrity
//!
//! ### Git Commands
//! - `status [--verbose]` - Show repository status
//! - `diff [commit] [file] [--stat]` - Show differences between commits
//! - `history [--limit N] [--verbose] [--file FILE]` - Show commit history
//!
//! ### Management Commands
//! - `room create/list/show/update/delete` - Room management
//! - `equipment add/list/update/remove` - Equipment management
//! - `spatial query/relate/transform/validate` - Spatial operations
//!
//! ### System Commands
//! - `config [--show] [--set KEY=VALUE] [--reset] [--edit]` - Configuration
//! - `watch [--building NAME] [--floor N] [--room NAME]` - Live monitoring
//!
//! ## Examples
//!
//! ```bash
//! # Import building data
//! arx import building.ifc
//! 
//! # Show repository status
//! arx status --verbose
//! 
//! # Render 3D building
//! arx render "Main Building"
//! 
//! # Create a new room
//! arx room create --building "Main Building" --floor 1 --wing "A" --name "Classroom 101" --type classroom
//! 
//! # Start live monitoring
//! arx watch --building "Main Building" --refresh-interval 5
//! ```
//!
//! ## Interactive Features
//!
//! - **3D Rendering**: Interactive terminal-based 3D visualization
//! - **Live Dashboard**: Real-time monitoring with `crossterm`/`ratatui`
//! - **Progress Indicators**: Visual progress bars for long operations
//! - **Rich Output**: Emoji-enhanced output for better UX
//!
//! ## Configuration
//!
//! ArxOS uses TOML configuration files (`arx.toml`) for settings:
//!
//! ```toml
//! [user]
//! name = "John Doe"
//! email = "john@example.com"
//! 
//! [building]
//! default_coordinate_system = "building_local"
//! auto_commit = true
//! 
//! [performance]
//! max_parallel_threads = 4
//! memory_limit_mb = 1024
//! ```

use clap::Parser;
use log::info;
use arxos_core::{ArxOSCore, parse_room_type, parse_equipment_type, Building, BuildingData};

// Import our modular components
mod cli;
mod error;
mod utils;
mod handlers;

use cli::Cli;
use error::CliError;
use utils::{load_building_data, validate_yaml_file, display_success, display_error};
use handlers::{
    handle_status_command, handle_diff_command, handle_history_command,
    handle_config_command, handle_room_command, handle_equipment_command,
    handle_spatial_command, handle_watch_command
};


/// Main entry point for the ArxOS CLI application
fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();
    
    let cli = Cli::parse();
    
    info!("Starting ArxOS CLI with command: {:?}", cli.command);
    
    // Execute the command
    execute_command(cli)?;
    
    Ok(())
}

/// Execute CLI command with comprehensive error handling
fn execute_command(cli: Cli) -> Result<(), Box<dyn std::error::Error>> {
    match cli.command {
        cli::Commands::Import { file } => {
            println!("📥 Importing IFC file: {}", file);
            
            // Check if file exists
            if !std::path::Path::new(&file).exists() {
                return Err(format!("File '{}' not found. Please check the path and try again.", file).into());
            }
            
            // Initialize ArxOS core
            let core = ArxOSCore::new()?;
            
            // Process IFC file
            println!("🔄 Processing IFC file...");
            let result = core.process_ifc_file(&file)?;
            
            println!("✅ Import completed successfully!");
            println!("📊 Processed {} entities", result.total_entities);
            println!("🏢 Building: {}", result.building_name);
            println!("📁 Output directory: {}", result.output_directory);
        }
        
        cli::Commands::Export { repo } => {
            println!("📤 Exporting to repository: {}", repo);
            
            // Initialize ArxOS core
            let core = ArxOSCore::new()?;
            
            // Export to repository
            let result = core.export_to_repository(&repo)?;
            
            println!("✅ Export completed successfully!");
            println!("📊 Exported {} files", result.files_exported);
            println!("📁 Repository: {}", result.repository_path);
        }
        
        cli::Commands::Render { building } => {
            println!("🎨 Rendering 3D building: {}", building);
            
            // Load building data
            let building_data = load_building_data(&building)?;
            
            // Initialize ArxOS core
            let core = ArxOSCore::new()?;
            
            // Render building
            let result = core.render_building_3d(&building_data)?;
            
            println!("✅ Rendering completed successfully!");
            println!("📊 Rendered {} floors", result.floors_rendered);
            println!("📁 Output: {}", result.output_path);
        }
        
        cli::Commands::Validate { path } => {
            let target_path = path.unwrap_or_else(|| ".".to_string());
            println!("🔍 Validating building data at: {}", target_path);
            
            // Validate YAML files in the directory
            let yaml_files: Vec<String> = std::fs::read_dir(&target_path)
                .map_err(|e| format!("Failed to read directory '{}': {}", target_path, e))?
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
                return Err(format!("No YAML files found in '{}'. Please run 'import' first.", target_path).into());
            }
            
            let mut valid_files = 0;
            let mut invalid_files = 0;
            
            for yaml_file in &yaml_files {
                match validate_yaml_file(yaml_file) {
                    Ok(_) => {
                        println!("✅ {} - Valid", yaml_file);
                        valid_files += 1;
                    }
                    Err(e) => {
                        println!("❌ {} - Invalid: {}", yaml_file, e);
                        invalid_files += 1;
                    }
                }
            }
            
            println!("\n📊 Validation Summary:");
            println!("✅ Valid files: {}", valid_files);
            println!("❌ Invalid files: {}", invalid_files);
            
            if invalid_files > 0 {
                return Err(format!("Validation failed: {} files have errors", invalid_files).into());
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
        
        cli::Commands::Watch { building, floor, room, refresh_interval } => {
            handle_watch_command(building, floor, room, refresh_interval)?;
        }
        
        cli::Commands::Interactive { building } => {
            println!("🎮 Starting interactive 3D renderer for: {}", building);
            
            // Load building data
            let building_data = load_building_data(&building)?;
            
            // Initialize ArxOS core
            let core = ArxOSCore::new()?;
            
            // Start interactive renderer
            let result = core.start_interactive_renderer(&building_data)?;
            
            println!("✅ Interactive session completed!");
            println!("📊 Rendered {} frames", result.frames_rendered);
            println!("⏱️  Session duration: {}ms", result.session_duration_ms);
        }
    }
    
    Ok(())
}

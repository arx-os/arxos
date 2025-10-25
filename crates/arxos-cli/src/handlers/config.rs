//! # Configuration Command Handlers
//!
//! This module handles configuration-related CLI commands.

use crate::error::CliError;
use crate::utils::display::{display_success, display_error, display_info};
use arxos_core::ArxOSCore;

/// Handle the config command
pub fn handle_config_command(show: bool, set: Option<String>, reset: bool, edit: bool) -> Result<(), CliError> {
    let mut core = ArxOSCore::new();
    
    if show {
        let config = core.get_configuration().map_err(|e| CliError::CoreOperation(e))?;
        display_info("Current Configuration:");
        println!("  Config file: {}", config.config_file_path);
        println!("  User name: {}", config.user_name);
        println!("  User email: {}", config.user_email);
        println!("  Building name: {}", config.building_name);
        println!("  Coordinate system: {}", config.coordinate_system);
        println!("  Auto commit: {}", config.auto_commit);
        println!("  Max parallel threads: {}", config.max_parallel_threads);
        println!("  Memory limit (MB): {}", config.memory_limit_mb);
    }
    
    if let Some(set_value) = set {
        // Parse key=value format
        if let Some((key, value)) = set_value.split_once('=') {
            core.set_configuration_value(key.trim(), value.trim()).map_err(|e| CliError::CoreOperation(e))?;
            display_info(&format!("Configuration updated: {} = {}", key.trim(), value.trim()));
        } else {
            display_error("Invalid format. Use: key=value");
            return Err(CliError::ValidationError("Invalid configuration format".to_string()));
        }
    }
    
    if reset {
        core.reset_configuration().map_err(|e| CliError::CoreOperation(e))?;
        display_info("Configuration reset to defaults");
    }
    
    if edit {
        let config_path = "./arx.toml";
        display_info(&format!("Opening configuration file: {}", config_path));
        display_info("Please edit the file manually and save your changes");
    }
    
    display_success("Configuration command completed");
    Ok(())
}

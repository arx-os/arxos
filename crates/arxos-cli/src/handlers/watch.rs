//! # Watch Command Handlers
//!
//! This module handles live monitoring CLI commands with full integration
//! to the ArxOS core functionality.

use crate::error::CliError;
use crate::utils::display::{display_success, display_error, display_info};
use arxos_core::ArxOSCore;

/// Handle watch command for live monitoring with full core integration
pub fn handle_watch_command(
    building: Option<String>,
    floor: Option<i32>,
    room: Option<String>,
    refresh_interval: Option<u64>,
) -> Result<(), CliError> {
    let building_name = building.unwrap_or_else(|| "Default Building".to_string());
    let interval = refresh_interval.unwrap_or(5);
    
    display_info(&format!("Starting live monitoring for building: {}", building_name));
    display_info(&format!("Refresh interval: {} seconds", interval));
    
    if let Some(floor_num) = floor {
        display_info(&format!("Floor: {}", floor_num));
    }
    
    if let Some(room_name) = room {
        display_info(&format!("Room: {}", room_name));
    }
    
    display_info("Press Ctrl+C to stop monitoring");
    display_info("=".repeat(50));
    
    // Initialize core
    let core = ArxOSCore::new()
        .map_err(|e| CliError::CoreOperation {
            operation: "initialize core".to_string(),
            source: e,
        })?;
    
    // Start live monitoring using core
    let result = core.start_live_monitoring(&building_name, floor, room.as_deref(), interval)
        .map_err(|e| CliError::CoreOperation {
            operation: "start live monitoring".to_string(),
            source: e,
        })?;
    
    display_success("Monitoring session completed!");
    display_info(&format!("Total updates: {}", result.total_updates));
    display_info(&format!("Session duration: {}ms", result.session_duration_ms));
    display_info(&format!("Alerts generated: {}", result.alerts_generated));
    display_info(&format!("Data points collected: {}", result.data_points_collected));
    
    Ok(())
}

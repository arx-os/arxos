//! # Spatial Command Handlers
//!
//! This module handles spatial operations CLI commands with full integration
//! to the ArxOS core functionality.

use crate::error::CliError;
use crate::utils::display::{display_success, display_error, display_info};
use crate::cli::SpatialCommands;
use arxos_core::ArxOSCore;

/// Handle spatial commands with full core integration
pub fn handle_spatial_command(command: SpatialCommands) -> Result<(), CliError> {
    let core = ArxOSCore::new()
        .map_err(|e| CliError::CoreOperation {
            operation: "initialize core".to_string(),
            source: e,
        })?;

    match command {
        SpatialCommands::Query { building, query_type, parameters } => {
            display_info(&format!("Performing spatial query: {} in building: {}", query_type, building));
            display_info(&format!("Parameters: {:?}", parameters));
            
            // Perform spatial query using core
            let results = core.spatial_query(&building, &query_type, &parameters)
                .map_err(|e| CliError::CoreOperation {
                    operation: "spatial query".to_string(),
                    source: e,
                })?;
            
            if results.is_empty() {
                display_info("No spatial query results found");
            } else {
                display_success(&format!("Found {} spatial query results:", results.len()));
                for (i, result) in results.iter().enumerate() {
                    display_info(&format!("  {}. {} - {}", i + 1, result.entity_type, result.entity_name));
                    display_info(&format!("    Distance: {:.2}", result.distance));
                    display_info(&format!("    Position: ({:.2}, {:.2}, {:.2})", result.position.x, result.position.y, result.position.z));
                }
            }
        }
        
        SpatialCommands::Relate { building, entity1, entity2 } => {
            display_info(&format!("Analyzing spatial relationship between {} and {} in building: {}", entity1, entity2, building));
            
            // Get spatial relationship using core
            let relationship = core.get_spatial_relationship(&building, &entity1, &entity2)
                .map_err(|e| CliError::CoreOperation {
                    operation: "get spatial relationship".to_string(),
                    source: e,
                })?;
            
            display_success("Spatial relationship analysis:");
            display_info(&format!("  Distance: {:.2}", relationship.distance));
            display_info(&format!("  Angle: {:.2}°", relationship.angle));
            display_info(&format!("  Relationship: {:?}", relationship.relationship_type));
        }
        
        SpatialCommands::Transform { building, entity, transformation } => {
            display_info(&format!("Applying spatial transformation: {} to entity: {} in building: {}", transformation, entity, building));
            
            // Apply spatial transformation using core
            let result = core.apply_spatial_transformation(&building, &entity, &transformation)
                .map_err(|e| CliError::CoreOperation {
                    operation: "apply spatial transformation".to_string(),
                    source: e,
                })?;
            
            display_success("Spatial transformation completed:");
            display_info(&format!("  New position: ({:.2}, {:.2}, {:.2})", result.new_position.x, result.new_position.y, result.new_position.z));
            display_info(&format!("  New orientation: ({:.2}, {:.2}, {:.2})", result.new_orientation.x, result.new_orientation.y, result.new_orientation.z));
        }
        
        SpatialCommands::Validate { building } => {
            display_info(&format!("Validating spatial data for building: {}", building));
            
            // Validate spatial data using core
            let validation = core.validate_spatial_data(&building)
                .map_err(|e| CliError::CoreOperation {
                    operation: "validate spatial data".to_string(),
                    source: e,
                })?;
            
            display_success("Spatial validation completed:");
            display_info(&format!("  Total entities: {}", validation.total_entities));
            display_info(&format!("  Valid entities: {}", validation.valid_entities));
            display_info(&format!("  Invalid entities: {}", validation.invalid_entities));
            
            if !validation.errors.is_empty() {
                display_error("Validation errors found:");
                for error in &validation.errors {
                    display_error(&format!("  - {}", error));
                }
            } else {
                display_success("All spatial data is valid!");
            }
        }
    }
    
    Ok(())
}

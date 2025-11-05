//! Spatial operations command handlers
//!
//! Handles spatial queries, relationships, transformations, and validation.

use crate::cli::SpatialCommands;

/// Handle spatial operations commands
///
/// Routes spatial subcommands to their respective handlers.
///
/// # Arguments
///
/// * `command` - The spatial command variant to execute
///
/// # Returns
///
/// Returns `Ok(())` if the command executes successfully, or an error if it fails.
pub fn handle_spatial_command(command: SpatialCommands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        SpatialCommands::Query { query_type, entity, params } => {
            handle_spatial_query(query_type, entity, params)
        }
        SpatialCommands::Relate { entity1, entity2, relationship } => {
            handle_spatial_relate(entity1, entity2, relationship)
        }
        SpatialCommands::Transform { from, to, entity } => {
            handle_spatial_transform(from, to, entity)
        }
        SpatialCommands::Validate { entity, tolerance } => {
            handle_spatial_validate(entity, tolerance)
        }
    }
}

/// Handle spatial query command
///
/// Performs spatial queries on building entities (e.g., find nearest, within radius, etc.).
///
/// # Arguments
///
/// * `query_type` - Type of spatial query to perform
/// * `entity` - Target entity for the query
/// * `params` - Additional parameters for the query
///
/// # Returns
///
/// Returns `Ok(())` if query succeeds, or an error if query fails.
fn handle_spatial_query(query_type: String, entity: String, params: Vec<String>) -> Result<(), Box<dyn std::error::Error>> {
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
    Ok(())
}

/// Handle spatial relationship command
///
/// Sets spatial relationships between entities (e.g., "contains", "adjacent", "above", etc.).
///
/// # Arguments
///
/// * `entity1` - First entity in the relationship
/// * `entity2` - Second entity in the relationship
/// * `relationship` - Type of relationship to establish
///
/// # Returns
///
/// Returns `Ok(())` if relationship is set successfully, or an error if it fails.
fn handle_spatial_relate(entity1: String, entity2: String, relationship: String) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔗 Setting spatial relationship: {} {} {}", entity1, relationship, entity2);
    
    let result = crate::core::set_spatial_relationship(&entity1, &entity2, &relationship)?;
    
    println!("{}", result);
    println!("✅ Spatial relationship set successfully");
    Ok(())
}

/// Handle coordinate transformation command
///
/// Transforms entity coordinates from one coordinate system to another.
///
/// # Arguments
///
/// * `from` - Source coordinate system name
/// * `to` - Target coordinate system name
/// * `entity` - Entity to transform
///
/// # Returns
///
/// Returns `Ok(())` if transformation succeeds, or an error if it fails.
fn handle_spatial_transform(from: String, to: String, entity: String) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔄 Transforming coordinates: {} from {} to {}", entity, from, to);
    
    let result = crate::core::transform_coordinates(&from, &to, &entity)?;
    
    println!("{}", result);
    println!("✅ Coordinate transformation completed");
    Ok(())
}

/// Handle spatial validation command
///
/// Validates spatial data for correctness (e.g., overlapping rooms, invalid coordinates).
///
/// # Arguments
///
/// * `entity` - Optional entity to validate (if `None`, validates all entities)
/// * `tolerance` - Optional tolerance for validation checks
///
/// # Returns
///
/// Returns `Ok(())` if validation passes, or an error if validation fails.
fn handle_spatial_validate(entity: Option<String>, tolerance: Option<f64>) -> Result<(), Box<dyn std::error::Error>> {
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
    Ok(())
}

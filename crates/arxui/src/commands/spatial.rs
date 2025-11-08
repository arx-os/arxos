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
        SpatialCommands::GridToReal { grid, building } => handle_grid_to_real(grid, building),
        SpatialCommands::RealToGrid { x, y, z, building } => handle_real_to_grid(x, y, z, building),
        SpatialCommands::Query {
            query_type,
            entity,
            params,
        } => handle_spatial_query(query_type, entity, params),
        SpatialCommands::Relate {
            entity1,
            entity2,
            relationship,
        } => handle_spatial_relate(entity1, entity2, relationship),
        SpatialCommands::Transform { from, to, entity } => {
            handle_spatial_transform(from, to, entity)
        }
        SpatialCommands::Validate { entity, tolerance } => {
            handle_spatial_validate(entity, tolerance)
        }
    }
}

/// Handle grid to real coordinate conversion
fn handle_grid_to_real(
    grid: String,
    building: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::load_building_data_from_dir;
    use crate::spatial::{GridCoordinate, GridSystem};

    println!(
        "🔢 Converting grid coordinate to real coordinates: {}",
        grid
    );

    let grid_coord = GridCoordinate::parse(&grid)?;
    println!(
        "   Parsed grid: Column {}, Row {}",
        grid_coord.column, grid_coord.row
    );

    // Try to load grid system from building data, or use default
    // Note: Grid system configuration can be added to building metadata in the future
    let grid_system = if let Some(building_name) = building {
        match load_building_data_from_dir() {
            Ok(building_data) => {
                if building_data.building.name == building_name {
                    println!(
                        "   📐 Building '{}' found, using default grid system",
                        building_name
                    );
                    println!("   💡 Tip: Grid system configuration will be stored in building metadata in a future release");
                    GridSystem::default()
                } else {
                    println!(
                        "   ⚠️  Building '{}' not found, using default grid system",
                        building_name
                    );
                    GridSystem::default()
                }
            }
            Err(_) => {
                println!("   ⚠️  Could not load building data, using default grid system");
                GridSystem::default()
            }
        }
    } else {
        GridSystem::default()
    };

    let real_coords = grid_system.grid_to_real(&grid_coord);
    println!(
        "   Real coordinates: ({:.2}, {:.2}, {:.2})",
        real_coords.x, real_coords.y, real_coords.z
    );
    println!("✅ Conversion completed");

    Ok(())
}

/// Handle real to grid coordinate conversion
fn handle_real_to_grid(
    x: f64,
    y: f64,
    z: Option<f64>,
    building: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::persistence::load_building_data_from_dir;
    use crate::spatial::{GridSystem, Point3D};

    let z_coord = z.unwrap_or(0.0);
    println!(
        "🔢 Converting real coordinates to grid: ({:.2}, {:.2}, {:.2})",
        x, y, z_coord
    );

    // Try to load grid system from building data, or use default
    // Note: Grid system configuration can be added to building metadata in the future
    let grid_system = if let Some(building_name) = building {
        match load_building_data_from_dir() {
            Ok(building_data) => {
                if building_data.building.name == building_name {
                    println!(
                        "   📐 Building '{}' found, using default grid system",
                        building_name
                    );
                    println!("   💡 Tip: Grid system configuration will be stored in building metadata in a future release");
                    GridSystem::default()
                } else {
                    println!(
                        "   ⚠️  Building '{}' not found, using default grid system",
                        building_name
                    );
                    GridSystem::default()
                }
            }
            Err(_) => {
                println!("   ⚠️  Could not load building data, using default grid system");
                GridSystem::default()
            }
        }
    } else {
        GridSystem::default()
    };

    let point = Point3D::new(x, y, z_coord);
    let grid_coord = grid_system.real_to_grid(&point);
    println!("   Grid coordinate: {}", grid_coord);
    println!("✅ Conversion completed");

    Ok(())
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
fn handle_spatial_query(
    query_type: String,
    entity: String,
    params: Vec<String>,
) -> Result<(), Box<dyn std::error::Error>> {
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
            println!(
                "  {}. {} ({})",
                i + 1,
                spatial_result.entity_name,
                spatial_result.entity_type
            );
            println!(
                "     Position: ({:.2}, {:.2}, {:.2})",
                spatial_result.position.x, spatial_result.position.y, spatial_result.position.z
            );
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
fn handle_spatial_relate(
    entity1: String,
    entity2: String,
    relationship: String,
) -> Result<(), Box<dyn std::error::Error>> {
    println!(
        "🔗 Setting spatial relationship: {} {} {}",
        entity1, relationship, entity2
    );

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
fn handle_spatial_transform(
    from: String,
    to: String,
    entity: String,
) -> Result<(), Box<dyn std::error::Error>> {
    println!(
        "🔄 Transforming coordinates: {} from {} to {}",
        entity, from, to
    );

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
fn handle_spatial_validate(
    entity: Option<String>,
    tolerance: Option<f64>,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("✅ Validating spatial data");

    if let Some(ref e) = entity {
        println!("   Entity: {}", e);
    }

    if let Some(t) = tolerance {
        println!("   Tolerance: {}", t);
    }

    let result = crate::core::validate_spatial(entity.as_deref(), tolerance)?;

    println!("   Entities checked: {}", result.entities_checked);
    println!("   Issues found: {}", result.issues_found);

    if result.is_valid {
        println!("✅ Spatial validation passed - all entities valid");
    } else {
        println!(
            "⚠️  Spatial validation found {} issues:",
            result.issues_found
        );
        for (i, issue) in result.issues.iter().enumerate() {
            println!(
                "   {}. {} [{}] - {}: {}",
                i + 1,
                issue.entity_name,
                issue.entity_type,
                issue.issue_type,
                issue.message
            );
        }
    }

    println!("✅ Spatial validation completed");
    Ok(())
}

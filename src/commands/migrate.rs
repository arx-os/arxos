//! Migration command for adding ArxAddress to existing fixtures
//!
//! One-shot migration script that fills address: for every existing fixture
//! in building YAML files by inferring from grid/floor/room data.

use crate::domain::ArxAddress;
use crate::persistence::PersistenceManager;
use crate::utils::loading;
use crate::spatial::grid::to_address::infer_room_from_grid;
use std::path::Path;
use glob::glob;

/// Migrate existing fixtures to include ArxAddress
///
/// Scans all YAML files in the current directory and adds address fields
/// to equipment that don't have them, based on existing grid/floor/room data.
///
/// # Arguments
///
/// * `dry_run` - If true, show what would be migrated without making changes
///
/// # Returns
///
/// Returns `Ok(())` if migration completes successfully, or an error if migration fails.
pub fn handle_migrate_address(dry_run: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("🔄 Migrating existing fixtures to ArxAddress format");
    
    if dry_run {
        println!("   (DRY RUN - no changes will be made)");
    }

    // Find all YAML files in current directory
    let yaml_pattern = "*.yaml";
    let mut migrated_count = 0;
    let mut error_count = 0;

    for entry in glob(yaml_pattern)? {
        match entry {
            Ok(path) => {
                if let Err(e) = migrate_file(&path, dry_run) {
                    eprintln!("❌ Error migrating {}: {}", path.display(), e);
                    error_count += 1;
                } else {
                    migrated_count += 1;
                }
            }
            Err(e) => {
                eprintln!("❌ Error reading file: {}", e);
                error_count += 1;
            }
        }
    }

    println!("\n✅ Migration completed:");
    println!("   Files processed: {}", migrated_count);
    if error_count > 0 {
        println!("   Errors: {}", error_count);
    }

    if dry_run {
        println!("\n💡 Run without --dry-run to apply changes");
    }

    Ok(())
}

/// Migrate a single YAML file
fn migrate_file(file_path: &Path, dry_run: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("📄 Processing: {}", file_path.display());

    let building_data = loading::load_building_data(
        file_path.to_str().unwrap_or("")
    )?;

    let mut modified = false;
    let building_name = building_data.building.name.clone();
    let mut building_data = building_data;

    // Process each floor
    for floor in &mut building_data.floors {
        let floor_level = floor.level;
        for equipment in &mut floor.equipment {
            // Skip if address already exists
            if equipment.address.is_some() {
                continue;
            }

            // Try to infer address from existing data
            // Extract needed data before mutable borrow
            let equipment_path = equipment.path.clone();
            let equipment_properties = equipment.properties.clone();
            let equipment_type_str = format!("{:?}", equipment.equipment_type);
            let equipment_id = equipment.id.clone();
            
            if let Some(addr) = infer_address_from_equipment_data(
                &equipment_path,
                &equipment_properties,
                &equipment_type_str,
                &equipment_id,
                &building_name,
                floor_level,
            )? {
                if dry_run {
                    println!("   Would add address {} to equipment: {}", addr.path, equipment.name);
                } else {
                    // Validate before assigning
                    addr.validate()?;
                    equipment.address = Some(addr);
                    modified = true;
                    println!("   ✓ Added address to equipment: {}", equipment.name);
                }
            } else {
                println!("   ⚠️  Could not infer address for equipment: {}", equipment.name);
            }
        }
    }

    // Save if modified and not dry run
    if modified && !dry_run {
        let building_name = building_data.building.name.clone();
        let persistence = PersistenceManager::new(&building_name)?;
        persistence.save_building_data(&building_data)?;
        println!("   💾 Saved changes to {}", file_path.display());
    }

    Ok(())
}

/// Infer ArxAddress from existing equipment data
fn infer_address_from_equipment_data(
    universal_path: &str,
    properties: &std::collections::HashMap<String, String>,
    equipment_type: &str,
    equipment_id: &str,
    building_name: &str,
    floor_level: i32,
) -> Result<Option<ArxAddress>, Box<dyn std::error::Error>> {
    // Try to find room from universal_path or properties
    let room = if let Some(room_name) = extract_room_from_path(universal_path) {
        Some(room_name)
    } else if let Some(grid) = properties.get("grid") {
        // Try to infer from grid
        infer_room_from_grid(grid).ok()
    } else {
        None
    };

    if let Some(room_name) = room {
        // Build address from available data
        let building_name_sanitized = building_name.to_lowercase().replace(" ", "-");
        let floor_str = format!("floor-{:02}", floor_level);
        
        // Infer fixture type from equipment type
        let fixture_type = match equipment_type.to_lowercase().as_str() {
            "hvac" => "boiler",
            "plumbing" => "valve",
            "electrical" => "panel",
            _ => "equipment",
        };
        
        // Use ID or generate a simple one
        let fixture_id = if let Some(id_suffix) = equipment_id.split('-').next_back() {
            format!("{}-{}", fixture_type, id_suffix)
        } else {
            format!("{}-01", fixture_type)
        };

        let addr = ArxAddress::new(
            "usa", "ny", "brooklyn", // Defaults - could be improved with config
            &building_name_sanitized,
            &floor_str,
            &room_name.to_lowercase().replace(" ", "-"),
            &fixture_id,
        );
        
        // Validate the generated address
        addr.validate()?;
        Ok(Some(addr))
    } else {
        Ok(None)
    }
}

/// Extract room name from universal_path format
fn extract_room_from_path(path: &str) -> Option<String> {
    // Try to parse /BUILDING/{building}/FLOOR/{floor}/ROOM/{room}/... format
    let parts: Vec<&str> = path.split('/').collect();
    
    for (i, part) in parts.iter().enumerate() {
        if *part == "ROOM" && i + 1 < parts.len() {
            return Some(parts[i + 1].to_string());
        }
    }
    
    None
}


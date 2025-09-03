//! Example: Building Intelligence Database
//! 
//! Demonstrates storing ArxObjects and performing spatial queries

use arxos_core::persistence_simple::ArxObjectDatabase;
use arxos_core::arxobject_simple::{ArxObject, object_types, ObjectCategory};
use arxos_core::ply_parser_simple::SimplePlyParser;
use std::env;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    
    println!("ArxOS Building Intelligence Database");
    println!("====================================\n");
    
    // Create or open database
    let db_path = if args.len() > 1 {
        &args[1]
    } else {
        "building.db"
    };
    
    let mut db = if db_path == ":memory:" {
        println!("Using in-memory database");
        ArxObjectDatabase::new_memory()?
    } else {
        println!("Using database: {}", db_path);
        ArxObjectDatabase::open(db_path)?
    };
    
    // Option 1: Load from PLY file if provided
    if args.len() > 2 {
        let ply_file = &args[2];
        println!("\nLoading PLY file: {}", ply_file);
        
        let parser = SimplePlyParser::new();
        let objects = parser.parse_to_arxobjects(ply_file, 0x0001)?;
        
        println!("Parsed {} ArxObjects", objects.len());
        
        let count = db.insert_batch(&objects)?;
        println!("Inserted {} objects into database", count);
    } else {
        // Option 2: Generate sample building data
        println!("\nGenerating sample building data...");
        generate_sample_building(&mut db)?;
    }
    
    // Demonstrate spatial queries
    println!("\n=== Spatial Query Examples ===\n");
    
    // 1. Find all electrical outlets
    println!("1. Finding all electrical outlets:");
    let outlets = db.find_by_type(0x0001, object_types::OUTLET)?;
    println!("   Found {} outlets", outlets.len());
    if !outlets.is_empty() {
        let (x, y, z) = outlets[0].position_meters();
        println!("   First outlet at: ({:.2}m, {:.2}m, {:.2}m)", x, y, z);
    }
    
    // 2. Find objects near a specific point
    println!("\n2. Finding objects within 2 meters of (5, 5, 1):");
    let nearby = db.find_within_radius(5.0, 5.0, 1.0, 2.0)?;
    println!("   Found {} objects nearby", nearby.len());
    for obj in nearby.iter().take(3) {
        let (x, y, z) = obj.position_meters();
        let category = ObjectCategory::from_type(obj.object_type);
        println!("   - {:?} at ({:.2}m, {:.2}m, {:.2}m)", category, x, y, z);
    }
    
    // 3. Find objects in a room (bounding box)
    println!("\n3. Finding objects in room (0-4m x 0-4m x 0-3m):");
    let room_objects = db.find_in_box(0.0, 0.0, 0.0, 4.0, 4.0, 3.0)?;
    println!("   Found {} objects in room", room_objects.len());
    
    // Group by category
    let mut categories = std::collections::HashMap::new();
    for obj in &room_objects {
        let category = ObjectCategory::from_type(obj.object_type);
        *categories.entry(category).or_insert(0) += 1;
    }
    
    for (category, count) in categories {
        println!("   - {:?}: {}", category, count);
    }
    
    // 4. Find nearest maintenance items
    println!("\n4. Finding 5 nearest objects to maintenance point (10, 10, 1):");
    let nearest = db.find_nearest(10.0, 10.0, 1.0, 5)?;
    for (obj, distance) in nearest {
        let (x, y, z) = obj.position_meters();
        let category = ObjectCategory::from_type(obj.object_type);
        println!("   - {:?} at ({:.2}m, {:.2}m, {:.2}m) - Distance: {:.2}m", 
                 category, x, y, z, distance);
    }
    
    // 5. Floor analysis
    println!("\n5. Analyzing floors:");
    for floor_num in 0..3 {
        let floor_height = floor_num as f32 * 3.0;
        let floor_objects = db.find_on_floor(0x0001, floor_height, 1.5)?;
        if !floor_objects.is_empty() {
            println!("   Floor {}: {} objects", floor_num, floor_objects.len());
        }
    }
    
    // Show database statistics
    println!("\n=== Database Statistics ===\n");
    let stats = db.get_stats()?;
    stats.print_summary();
    
    // Calculate data compression
    let raw_size = stats.total_objects * std::mem::size_of::<ArxObject>();
    println!("\nStorage efficiency:");
    println!("  Raw ArxObject size: {} bytes", raw_size);
    println!("  Per object: {} bytes", std::mem::size_of::<ArxObject>());
    
    Ok(())
}

fn generate_sample_building(db: &mut ArxObjectDatabase) -> Result<(), Box<dyn std::error::Error>> {
    let mut objects = Vec::new();
    
    // Generate 3 floors
    for floor in 0..3 {
        let z_base = floor * 3000; // 3 meters per floor
        
        // Add outlets every 2 meters along walls
        for i in 0..5 {
            // North wall
            objects.push(ArxObject::new(0x0001, object_types::OUTLET, 
                                       i * 2000, 0, z_base + 300));
            // South wall
            objects.push(ArxObject::new(0x0001, object_types::OUTLET, 
                                       i * 2000, 10000, z_base + 300));
            // East wall
            objects.push(ArxObject::new(0x0001, object_types::OUTLET, 
                                       0, i * 2000, z_base + 300));
            // West wall
            objects.push(ArxObject::new(0x0001, object_types::OUTLET, 
                                       10000, i * 2000, z_base + 300));
        }
        
        // Add light switches near doors
        objects.push(ArxObject::new(0x0001, object_types::LIGHT_SWITCH, 
                                   1000, 100, z_base + 1200));
        objects.push(ArxObject::new(0x0001, object_types::LIGHT_SWITCH, 
                                   9000, 100, z_base + 1200));
        
        // Add ceiling lights in grid
        for x in 0..3 {
            for y in 0..3 {
                objects.push(ArxObject::new(0x0001, object_types::LIGHT, 
                                           2000 + x * 3000, 
                                           2000 + y * 3000, 
                                           z_base + 2800));
            }
        }
        
        // Add smoke detectors
        objects.push(ArxObject::new(0x0001, object_types::SMOKE_DETECTOR, 
                                   5000, 2000, z_base + 2900));
        objects.push(ArxObject::new(0x0001, object_types::SMOKE_DETECTOR, 
                                   5000, 8000, z_base + 2900));
        
        // Add thermostat
        objects.push(ArxObject::new(0x0001, object_types::THERMOSTAT, 
                                   5000, 100, z_base + 1500));
        
        // Add HVAC vents
        for i in 0..4 {
            objects.push(ArxObject::new(0x0001, object_types::HVAC_VENT, 
                                       1000 + i * 2500, 5000, z_base + 2950));
        }
    }
    
    // Add emergency exits on ground floor
    objects.push(ArxObject::new(0x0001, object_types::EMERGENCY_EXIT, 0, 5000, 0));
    objects.push(ArxObject::new(0x0001, object_types::EMERGENCY_EXIT, 10000, 5000, 0));
    
    // Add fire alarms on each floor
    for floor in 0..3 {
        objects.push(ArxObject::new(0x0001, object_types::FIRE_ALARM, 
                                   100, 5000, floor * 3000 + 2000));
    }
    
    println!("Generated {} objects for 3-floor building", objects.len());
    
    db.insert_batch(&objects)?;
    
    Ok(())
}
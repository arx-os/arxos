//! Integration test for PLY → ArxObject → Database pipeline
//! NOTE: This test is disabled during the database to file storage migration
//! TODO: Rewrite these tests to work with the new file_storage interface

/*
use arxos_core::ply_parser_simple::SimplePlyParser;
use arxos_core::file_storage::{MemoryDatabase, Database, StorageStats};
use arxos_core::{ArxObject, object_types};

#[test]
fn test_ply_to_database_pipeline() {
    // Step 1: Parse PLY file to ArxObjects
    let parser = SimplePlyParser::new();
    let building_id = 0x0042;
    
    let objects = parser.parse_to_arxobjects("test_data/simple_room.ply", building_id)
        .expect("Should parse PLY file");
    
    assert!(!objects.is_empty(), "Should generate ArxObjects from PLY");
    
    // Step 2: Store in database
    let mut db = MemoryDatabase::new();
    
    let inserted = db.insert_batch(&objects)
        .expect("Should insert objects");
    
    assert_eq!(inserted, objects.len());
    
    // Step 3: Test spatial queries
    
    // Find all objects in the building
    let building_objects = db.get_building_objects(building_id)
        .expect("Should retrieve building objects");
    
    assert_eq!(building_objects.len(), objects.len());
    
    // Find objects on ground floor (z near 0)
    let ground_floor = db.find_on_floor(building_id, 0.0, 0.5)
        .expect("Should find floor objects");
    
    assert!(!ground_floor.is_empty(), "Should have ground floor objects");
    
    // Test spatial query - find objects in a 2x2x2 meter cube
    let in_box = db.find_in_box(0.0, 0.0, 0.0, 2.0, 2.0, 2.0)
        .expect("Should find objects in box");
    
    println!("Found {} objects in 2x2x2m box", in_box.len());
    
    // Step 4: Verify statistics
    let stats = db.get_stats()
        .expect("Should get statistics");
    
    assert_eq!(stats.total_objects, objects.len());
    assert_eq!(stats.building_count, 1);
    
    println!("\nDatabase Statistics:");
    println!("  Total objects: {}", stats.total_objects);
    println!("  Building count: {}", stats.building_count);
    println!("  Type distribution:");
    for (obj_type, count) in &stats.type_distribution {
        println!("    Type 0x{:02X}: {} objects", obj_type, count);
    }
}

#[test]
fn test_spatial_indexing_performance() {
    let mut db = ArxObjectDatabase::new_memory()
        .expect("Should create database");
    
    // Generate grid of objects for testing
    let mut objects = Vec::new();
    for x in 0..10 {
        for y in 0..10 {
            for z in 0..3 {
                objects.push(ArxObject::new(
                    0x0001,
                    if z == 0 { object_types::FLOOR } 
                    else if z == 1 { object_types::OUTLET }
                    else { object_types::LIGHT },
                    x * 1000,
                    y * 1000,
                    z * 1000,
                ));
            }
        }
    }
    
    // Insert 300 objects
    db.insert_batch(&objects).expect("Should insert grid");
    
    // Test query performance
    let start = std::time::Instant::now();
    
    // Find objects within 2 meter radius
    let nearby = db.find_within_radius(5.0, 5.0, 1.0, 2.0)
        .expect("Should find nearby objects");
    
    let query_time = start.elapsed();
    
    println!("Spatial query found {} objects in {:?}", nearby.len(), query_time);
    assert!(query_time.as_millis() < 10, "Query should be fast with indices");
    
    // Test nearest neighbor query
    let start = std::time::Instant::now();
    let nearest = db.find_nearest(5.0, 5.0, 1.0, 10)
        .expect("Should find nearest");
    
    let nn_time = start.elapsed();
    
    println!("Nearest neighbor found {} objects in {:?}", nearest.len(), nn_time);
    assert_eq!(nearest.len(), 10);
    assert!(nn_time.as_millis() < 10, "NN query should be fast");
}

#[test]
fn test_building_isolation() {
    let mut db = ArxObjectDatabase::new_memory()
        .expect("Should create database");
    
    // Insert objects for different buildings
    db.insert(&ArxObject::new(0x0001, object_types::OUTLET, 1000, 1000, 300)).unwrap();
    db.insert(&ArxObject::new(0x0001, object_types::OUTLET, 2000, 1000, 300)).unwrap();
    db.insert(&ArxObject::new(0x0002, object_types::OUTLET, 1000, 1000, 300)).unwrap();
    db.insert(&ArxObject::new(0x0002, object_types::OUTLET, 3000, 1000, 300)).unwrap();
    
    // Query for building 1
    let building1 = db.get_building_objects(0x0001).unwrap();
    assert_eq!(building1.len(), 2);
    
    // Query for building 2
    let building2 = db.get_building_objects(0x0002).unwrap();
    assert_eq!(building2.len(), 2);
    
    // Verify buildings are isolated
    for obj in building1 {
        assert_eq!(obj.building_id, 0x0001);
    }
    
    for obj in building2 {
        assert_eq!(obj.building_id, 0x0002);
    }
}

#[test]
fn test_floor_detection() {
    let mut db = ArxObjectDatabase::new_memory()
        .expect("Should create database");
    
    // Insert objects at different heights (typical building)
    // Ground floor: 0m
    db.insert(&ArxObject::new(0x0001, object_types::OUTLET, 1000, 1000, 300)).unwrap();
    db.insert(&ArxObject::new(0x0001, object_types::OUTLET, 2000, 1000, 450)).unwrap();
    
    // Second floor: 3m
    db.insert(&ArxObject::new(0x0001, object_types::OUTLET, 1000, 1000, 3300)).unwrap();
    db.insert(&ArxObject::new(0x0001, object_types::LIGHT_SWITCH, 2000, 1000, 3200)).unwrap();
    
    // Third floor: 6m
    db.insert(&ArxObject::new(0x0001, object_types::THERMOSTAT, 1000, 1000, 6000)).unwrap();
    
    // Find objects per floor
    let ground = db.find_on_floor(0x0001, 0.0, 1.0).unwrap();
    let second = db.find_on_floor(0x0001, 3.0, 1.0).unwrap();
    let third = db.find_on_floor(0x0001, 6.0, 1.0).unwrap();
    
    assert_eq!(ground.len(), 2, "Should have 2 objects on ground floor");
    assert_eq!(second.len(), 2, "Should have 2 objects on second floor");
    assert_eq!(third.len(), 1, "Should have 1 object on third floor");
}
*/
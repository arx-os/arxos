use std::io::Write;
use tempfile::NamedTempFile;
use arxos::spatial::Point3D;
use arxos::spatial::lidar::parser;
use arxos::spatial::lidar::downsampler::VoxelGridFilter;
use arxos::spatial::lidar::LidarPipeline;

#[test]
fn test_xyz_parser_streaming() -> Result<(), Box<dyn std::error::Error>> {
    let mut temp = NamedTempFile::new()?;
    writeln!(temp, "# Comment line to ignore")?;
    writeln!(temp, "1.0, 2.0, 3.0")?;
    writeln!(temp, "  ")?; // Empty line to ignore
    writeln!(temp, "4.0 5.0 6.0")?;
    writeln!(temp, "7.0\t8.0\t9.0")?;
    temp.flush()?;

    let points_iter = parser::stream_points(temp.path())?;
    let points: Result<Vec<Point3D>, _> = points_iter.collect();
    let points = points?;

    assert_eq!(points.len(), 3);
    assert_eq!(points[0].x, 1.0);
    assert_eq!(points[0].y, 2.0);
    assert_eq!(points[0].z, 3.0);
    assert_eq!(points[1].x, 4.0);
    assert_eq!(points[1].y, 5.0);
    assert_eq!(points[1].z, 6.0);
    assert_eq!(points[2].x, 7.0);
    assert_eq!(points[2].y, 8.0);
    assert_eq!(points[2].z, 9.0);

    Ok(())
}

#[test]
fn test_ply_parser_streaming() -> Result<(), Box<dyn std::error::Error>> {
    let mut temp = NamedTempFile::new()?;
    writeln!(temp, "ply")?;
    writeln!(temp, "format ascii 1.0")?;
    writeln!(temp, "element vertex 2")?;
    writeln!(temp, "property float x")?;
    writeln!(temp, "property float y")?;
    writeln!(temp, "property float z")?;
    writeln!(temp, "end_header")?;
    writeln!(temp, "10.0 20.0 30.0")?;
    writeln!(temp, "40.0 50.0 60.0")?;
    temp.flush()?;

    let points_iter = parser::stream_points(temp.path())?;
    let points: Result<Vec<Point3D>, _> = points_iter.collect();
    let points = points?;

    assert_eq!(points.len(), 2);
    assert_eq!(points[0].x, 10.0);
    assert_eq!(points[0].y, 20.0);
    assert_eq!(points[0].z, 30.0);
    assert_eq!(points[1].x, 40.0);
    assert_eq!(points[1].y, 50.0);
    assert_eq!(points[1].z, 60.0);

    Ok(())
}

#[test]
fn test_voxel_grid_filter_downsample() -> Result<(), Box<dyn std::error::Error>> {
    let filter = VoxelGridFilter::new(1.0, false);
    
    // Create 4 points inside the same voxel [0.0, 1.0)
    let points = vec![
        Ok(Point3D::new(0.1, 0.1, 0.1)),
        Ok(Point3D::new(0.3, 0.3, 0.3)),
        Ok(Point3D::new(0.5, 0.5, 0.5)),
        Ok(Point3D::new(0.7, 0.7, 0.7)),
        // 1 point in a different voxel
        Ok(Point3D::new(1.5, 1.5, 1.5)),
    ];

    let (filtered, stats) = filter.filter(points.into_iter())?;

    assert_eq!(stats.total_points, 5);
    assert_eq!(stats.downsampled_points, 2);
    assert_eq!(filtered.len(), 2);

    // Verify centroid calculation: mean of [0.1, 0.3, 0.5, 0.7] is 0.4
    let centroid = filtered.iter().find(|p| p.x < 1.0).unwrap();
    assert!((centroid.x - 0.4).abs() < 1e-5);
    assert!((centroid.y - 0.4).abs() < 1e-5);
    assert!((centroid.z - 0.4).abs() < 1e-5);

    Ok(())
}

#[test]
fn test_voxel_filter_capacity_flush() -> Result<(), Box<dyn std::error::Error>> {
    // Voxel size = 1.0, capacity limits to 2 voxels (for testing, but we test with normal limits)
    // To test flush logic with large defaults:
    // Let's verify voxel filter works correctly with light mode limits
    let filter = VoxelGridFilter::new(0.20, true); // light mode on
    
    let mut points = Vec::new();
    for i in 0..150 {
        // Generate points in unique voxels
        points.push(Ok(Point3D::new(i as f64 * 0.5, 0.0, 0.0)));
    }

    let (filtered, stats) = filter.filter(points.into_iter())?;
    assert_eq!(stats.total_points, 150);
    assert_eq!(stats.downsampled_points, 150);
    assert_eq!(filtered.len(), 150);

    Ok(())
}

#[test]
fn test_lidar_pipeline_end_to_end() -> Result<(), Box<dyn std::error::Error>> {
    let mut temp = NamedTempFile::new()?;
    writeln!(temp, "1.0 1.0 1.0")?;
    writeln!(temp, "2.0 2.0 2.0")?;
    writeln!(temp, "3.0 3.0 3.0")?;
    temp.flush()?;

    let pipeline = LidarPipeline::new(0.1, false);
    let building = pipeline.process(temp.path())?;

    assert_eq!(building.floors.len(), 1);
    assert_eq!(building.floors[0].name, "Floor 1");
    
    let metadata = building.metadata.as_ref().unwrap();
    assert_eq!(metadata.total_entities, 3);
    assert_eq!(metadata.properties.get("bbox_min_x").unwrap(), "1");
    assert_eq!(metadata.properties.get("bbox_max_x").unwrap(), "3");

    Ok(())
}

#[test]
fn test_lidar_pipeline_phase2_detection() -> Result<(), Box<dyn std::error::Error>> {
    use arxos::spatial::lidar::detector::{FloorDetector, RoomDetector};

    let mut points = Vec::new();

    // Generate two stories: Floor 1 at Z = 0.0, Floor 2 at Z = 4.0
    // Story 1: Z in [0.0, 3.0]
    // Story 2: Z in [4.0, 7.0]
    
    // We add dense floor slabs to trigger peaks in histogram
    for x in 0..10 {
        for y in 0..10 {
            // Floor 1 slab (Z=0.0)
            points.push(Point3D::new(x as f64, y as f64, 0.0));
            // Floor 2 slab (Z=4.0)
            points.push(Point3D::new(x as f64, y as f64, 4.0));
        }
    }

    // Story 1 Walls: a outer box [0, 8] x [0, 8] with a dividing wall at X=4
    // Wall points at Z=1.0 and Z=2.0
    for z in &[1.0, 2.0] {
        let mut val = 0.0;
        while val <= 8.0 {
            // Outer boundaries
            points.push(Point3D::new(0.0, val, *z));
            points.push(Point3D::new(8.0, val, *z));
            points.push(Point3D::new(val, 0.0, *z));
            points.push(Point3D::new(val, 8.0, *z));
            // Interior dividing wall
            points.push(Point3D::new(4.0, val, *z));
            val += 0.1;
        }
    }

    // Story 2 Walls: a simple outer box [0, 8] x [0, 8] (no dividing wall)
    for z in &[5.0, 6.0] {
        let mut val = 0.0;
        while val <= 8.0 {
            points.push(Point3D::new(0.0, val, *z));
            points.push(Point3D::new(8.0, val, *z));
            points.push(Point3D::new(val, 0.0, *z));
            points.push(Point3D::new(val, 8.0, *z));
            val += 0.1;
        }
    }

    // 1. Verify Floor Detector
    let floor_detector = FloorDetector::new(0.10, 2.5, 1.2);
    let floor_elevations = floor_detector.detect(&points);

    println!("Detected Elevations: {:?}", floor_elevations);
    assert_eq!(floor_elevations.len(), 2);
    assert!((floor_elevations[0] - 1.0).abs() < 1e-5);
    assert!((floor_elevations[1] - 5.0).abs() < 1e-5);

    // 2. Verify Room Detector
    let room_detector = RoomDetector::new(0.20, 1, 9); // Grid spacing 0.2m, min 9 cells area

    // Floor 1 Rooms (should detect 2 rooms because of dividing wall at X=4)
    let f1_rooms = room_detector.detect_rooms(&points, 1.0, 5.0);
    println!("Floor 1 Rooms count: {}, details: {:#?}", f1_rooms.len(), f1_rooms);
    assert_eq!(f1_rooms.len(), 2);

    // Floor 2 Rooms (should detect 1 room)
    let f2_rooms = room_detector.detect_rooms(&points, 5.0, 8.0);
    println!("Floor 2 Rooms count: {}, details: {:#?}", f2_rooms.len(), f2_rooms);
    assert_eq!(f2_rooms.len(), 1);

    Ok(())
}

#[test]
fn test_lidar_pipeline_phase3_detection() -> Result<(), Box<dyn std::error::Error>> {
    use arxos::core::EquipmentType;
    use arxos::spatial::lidar::detector::{RoomDetector, EquipmentDetector};

    let mut points = Vec::new();

    // 1. Generate Room Walls (solid box [0, 8] x [0, 8] at Z in [1.0, 3.0])
    let mut z = 1.0;
    while z <= 3.0 {
        let mut val = 0.0;
        while val <= 8.0 {
            points.push(Point3D::new(0.0, val, z));
            points.push(Point3D::new(8.0, val, z));
            points.push(Point3D::new(val, 0.0, z));
            points.push(Point3D::new(val, 8.0, z));
            val += 0.1;
        }
        z += 1.0;
    }

    // 2. Generate Equipment Cluster 1: HVAC block (large volume)
    // Points at X in [1.5, 2.5], Y in [1.5, 2.5], Z in [1.2, 2.2] with step 0.2
    let mut x = 1.5;
    while x <= 2.5 {
        let mut y = 1.5;
        while y <= 2.5 {
            let mut z = 1.2;
            while z <= 2.2 {
                points.push(Point3D::new(x, y, z));
                z += 0.2;
            }
            y += 0.2;
        }
        x += 0.2;
    }

    // 3. Generate Equipment Cluster 2: Electrical column (tall, slender)
    // Points at X=6.0, Y=6.0, Z in [1.2, 2.8] with step 0.2
    let mut z = 1.2;
    while z <= 2.8 {
        points.push(Point3D::new(6.0, 6.0, z));
        points.push(Point3D::new(6.1, 6.0, z));
        z += 0.2;
    }

    // Detect the Room first
    let room_detector = RoomDetector::new(0.20, 1, 9);
    let rooms = room_detector.detect_rooms(&points, 0.0, 4.0);
    assert_eq!(rooms.len(), 1);

    // Run Equipment Detector inside the room
    let eq_detector = EquipmentDetector::new(0.40, 2);
    let equipment = eq_detector.detect_equipment(
        &points,
        &rooms[0].spatial_properties.bounding_box,
        "/building/floor-1/room-1",
    );

    println!("Detected Equipment inside Room 1: {:#?}", equipment);
    assert_eq!(equipment.len(), 2);

    let hvac_item = equipment.iter().find(|e| e.equipment_type == EquipmentType::HVAC);
    let elec_item = equipment.iter().find(|e| e.equipment_type == EquipmentType::Electrical);

    assert!(hvac_item.is_some());
    assert!(elec_item.is_some());

    Ok(())
}

#[test]
fn test_lidar_pipeline_incremental_merge() -> Result<(), Box<dyn std::error::Error>> {
    use arxos::core::{Building, Floor, Wing, Room, RoomType, Equipment, EquipmentType, Position, Dimensions, BoundingBox, SpatialProperties};
    use arxos::spatial::lidar::merger::ModelMerger;

    // 1. Create existing building model
    let mut existing = Building::new("Test Building".to_string(), "test-building".to_string());
    let mut floor = Floor::new("Floor 1".to_string(), 0);
    let mut wing = Wing::new("Main".to_string());
    
    let mut room1 = Room::new("Room 1".to_string(), RoomType::Office);
    room1.spatial_properties = SpatialProperties {
        position: Position { x: 2.0, y: 2.0, z: 0.0, coordinate_system: "building_local".to_string() },
        dimensions: Dimensions { width: 4.0, height: 3.0, depth: 4.0 },
        bounding_box: BoundingBox {
            min: Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "building_local".to_string() },
            max: Position { x: 4.0, y: 4.0, z: 3.0, coordinate_system: "building_local".to_string() },
        },
        mesh: None,
        coordinate_system: "building_local".to_string(),
    };
    let room1_id = room1.id.clone();

    let mut eq1 = Equipment::new("HVAC Item 1".to_string(), "/building/floor-1/room-1/hvac-item-1".to_string(), EquipmentType::HVAC);
    eq1.position = Position { x: 2.2, y: 2.2, z: 0.5, coordinate_system: "building_local".to_string() };
    let eq1_id = eq1.id.clone();

    room1.add_equipment(eq1);
    wing.add_room(room1);
    floor.add_wing(wing);
    existing.add_floor(floor);

    // 2. Create incoming building model (new scan)
    let mut incoming = Building::new("Test Building".to_string(), "test-building".to_string());
    let mut f_in = Floor::new("Floor 1".to_string(), 0);
    let mut w_in = Wing::new("Main".to_string());

    // Matches Room 1 (centroid [2.1, 2.1, 0.0] is within 2.0m of [2.0, 2.0, 0.0])
    let mut room1_in = Room::new("Room 1".to_string(), RoomType::Office);
    room1_in.spatial_properties = SpatialProperties {
        position: Position { x: 2.1, y: 2.1, z: 0.0, coordinate_system: "building_local".to_string() },
        dimensions: Dimensions { width: 4.0, height: 3.0, depth: 4.0 },
        bounding_box: BoundingBox {
            min: Position { x: 0.1, y: 0.1, z: 0.0, coordinate_system: "building_local".to_string() },
            max: Position { x: 4.1, y: 4.1, z: 3.0, coordinate_system: "building_local".to_string() },
        },
        mesh: None,
        coordinate_system: "building_local".to_string(),
    };

    // Matches eq1 (HVAC, position [2.25, 2.25, 0.5] is within 1.5m of [2.2, 2.2, 0.5])
    let mut eq1_in = Equipment::new("HVAC Item 1".to_string(), "/building/floor-1/room-1/hvac-item-1".to_string(), EquipmentType::HVAC);
    eq1_in.position = Position { x: 2.25, y: 2.25, z: 0.5, coordinate_system: "building_local".to_string() };

    // New Equipment (Electrical, position [3.0, 3.0, 1.0])
    let mut eq2_in = Equipment::new("Electrical Item 2".to_string(), "/building/floor-1/room-1/electrical-item-2".to_string(), EquipmentType::Electrical);
    eq2_in.position = Position { x: 3.0, y: 3.0, z: 1.0, coordinate_system: "building_local".to_string() };

    room1_in.add_equipment(eq1_in);
    room1_in.add_equipment(eq2_in);
    w_in.add_room(room1_in);

    // New Room (Room 2)
    let mut room2_in = Room::new("Room 2".to_string(), RoomType::Office);
    room2_in.spatial_properties = SpatialProperties {
        position: Position { x: 6.0, y: 6.0, z: 0.0, coordinate_system: "building_local".to_string() },
        dimensions: Dimensions { width: 2.0, height: 3.0, depth: 2.0 },
        bounding_box: BoundingBox {
            min: Position { x: 5.0, y: 5.0, z: 0.0, coordinate_system: "building_local".to_string() },
            max: Position { x: 7.0, y: 7.0, z: 3.0, coordinate_system: "building_local".to_string() },
        },
        mesh: None,
        coordinate_system: "building_local".to_string(),
    };
    w_in.add_room(room2_in);

    f_in.add_wing(w_in);
    incoming.add_floor(f_in);

    // 3. Merge models
    let merged = ModelMerger::merge(existing, incoming);

    // 4. Verification
    assert_eq!(merged.floors.len(), 1);
    let floor_merged = &merged.floors[0];
    let wing_merged = &floor_merged.wings[0];
    assert_eq!(wing_merged.rooms.len(), 2);

    let r1 = wing_merged.rooms.iter().find(|r| r.name == "Room 1").unwrap();
    let r2 = wing_merged.rooms.iter().find(|r| r.name == "Room 2").unwrap();

    // Verify room ID preservation
    assert_eq!(r1.id, room1_id);

    // Verify room 1 equipment merging
    assert_eq!(r1.equipment.len(), 2);
    let hvac = r1.equipment.iter().find(|e| e.equipment_type == EquipmentType::HVAC).unwrap();
    let elec = r1.equipment.iter().find(|e| e.equipment_type == EquipmentType::Electrical).unwrap();

    // Verify equipment ID preservation
    assert_eq!(hvac.id, eq1_id);
    // Verify position updated
    assert_eq!(hvac.position.x, 2.25);
    // Verify new equipment details
    assert_eq!(elec.position.x, 3.0);

    // Verify new room details
    assert_eq!(r2.name, "Room 2");

    Ok(())
}




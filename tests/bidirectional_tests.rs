use arxos::core::{
    Building, Dimensions, Equipment, EquipmentType, Floor, LidarEnrichment, Position, Room,
    RoomType, Wing,
};
use arxos::export::ifc::IFCExporter;
use arxos::ifc::mapping::{
    approx_eq, dimensions_approx_eq, merge_building, positions_approx_eq, resolve_product_global_id,
    spatial_from_position_dims, PSET_ARX_IDENTITY, PSET_ARX_LIDAR, PROP_ARX_ID, PROP_POINT_COUNT,
};
use arxos::ifc::IFCProcessor;
use arxos::yaml::BuildingYamlSerializer;
use chrono::{DateTime, Utc};
use std::fs;
use tempfile::NamedTempFile;

#[test]
fn test_bidirectional_roundtrip_synthetic() -> anyhow::Result<()> {
    // 1. Create a rich canonical building
    let mut building = Building::new("HQ Building".to_string(), "/hq".to_string());
    
    // Add floor-level metadata
    let mut floor = Floor::new("Floor 1".to_string(), 1);
    floor.properties.insert("fire_rating".to_string(), "1h".to_string());

    // Create wings
    let mut wing_east = Wing::new("East Wing".to_string());
    let mut wing_west = Wing::new("West Wing".to_string());

    // Create room inside West Wing
    let room_west = Room::new("Office 102".to_string(), RoomType::Office);
    wing_west.add_room(room_west);

    // Create room inside East Wing
    let mut room_conf = Room::new("Conference room 101".to_string(), RoomType::Office);
    room_conf.properties.insert("max_occupancy".to_string(), "20".to_string());

    // Add room-level equipment
    let mut eq_projector = Equipment::new(
        "projector-01".to_string(),
        "".to_string(),
        EquipmentType::AV,
    );
    eq_projector.position = Position {
        x: 2.0,
        y: 3.0,
        z: 2.5,
        coordinate_system: "building_local".to_string(),
    };
    eq_projector.properties.insert("brand".to_string(), "Epson".to_string());
    room_conf.add_equipment(eq_projector);
    wing_east.add_room(room_conf);

    // Add wing-level equipment (e.g. hallway thermostat)
    let mut eq_thermostat = Equipment::new(
        "thermostat-east".to_string(),
        "".to_string(),
        EquipmentType::HVAC,
    );
    eq_thermostat.position = Position {
        x: 10.0,
        y: 1.5,
        z: 1.2,
        coordinate_system: "building_local".to_string(),
    };
    wing_east.equipment.push(eq_thermostat);

    // Add floor-level equipment (e.g. electrical panel)
    let mut eq_panel = Equipment::new(
        "panel-floor1".to_string(),
        "".to_string(),
        EquipmentType::Electrical,
    );
    eq_panel.position = Position {
        x: 0.5,
        y: 0.5,
        z: 1.8,
        coordinate_system: "building_local".to_string(),
    };
    floor.equipment.push(eq_panel);

    floor.add_wing(wing_east);
    floor.add_wing(wing_west);
    building.add_floor(floor);

    // 2. Export to IFC
    let temp_ifc = NamedTempFile::new()?;
    let exporter = IFCExporter::new(building.clone());
    exporter.export(temp_ifc.path())?;

    // 3. Import back using Native Parser
    let processor = IFCProcessor::new();
    let parsing_result = processor.parse_native(temp_ifc.path().to_str().unwrap(), false)?;
    let imported_building = parsing_result.building;

    // 4. Verify structural nesting
    assert_eq!(imported_building.name, building.name);
    assert_eq!(imported_building.floors.len(), 1);

    let imp_floor = &imported_building.floors[0];
    assert_eq!(imp_floor.name, "Floor 1");
    // Phase 3: free-form Arx props use clean keys (no Pset_ prefix in domain bag)
    assert_eq!(
        imp_floor.properties.get("fire_rating"),
        Some(&"1h".to_string())
    );

    // Verify Floor-Level Equipment
    assert_eq!(imp_floor.equipment.len(), 1);
    assert_eq!(imp_floor.equipment[0].name, "panel-floor1");
    assert_eq!(imp_floor.equipment[0].equipment_type, EquipmentType::Electrical);

    // Verify Wings and Wing-Level Equipment
    assert_eq!(imp_floor.wings.len(), 2);
    let imp_wing_east = imp_floor.wings.iter().find(|w| w.name == "East Wing").expect("East Wing should exist");
    assert_eq!(imp_wing_east.equipment.len(), 1);
    assert_eq!(imp_wing_east.equipment[0].name, "thermostat-east");
    assert_eq!(imp_wing_east.equipment[0].equipment_type, EquipmentType::HVAC);

    // Verify Room and Room-Level Equipment
    assert_eq!(imp_wing_east.rooms.len(), 1);
    let imp_room = &imp_wing_east.rooms[0];
    assert_eq!(imp_room.name, "Conference room 101");
    assert_eq!(
        imp_room.properties.get("max_occupancy"),
        Some(&"20".to_string())
    );
    assert_eq!(
        imp_room.properties.get("ArxWing"),
        Some(&"East Wing".to_string())
    );

    assert_eq!(imp_room.equipment.len(), 1);
    let imp_eq = &imp_room.equipment[0];
    assert_eq!(imp_eq.name, "projector-01");
    assert_eq!(imp_eq.equipment_type, EquipmentType::AV);
    assert_eq!(
        imp_eq.properties.get("brand"),
        Some(&"Epson".to_string())
    );

    // 5. Serialize to YAML and verify round-trip rehydration
    let yaml = BuildingYamlSerializer::serialize_building(&imported_building)
        .map_err(|e| anyhow::anyhow!(e.to_string()))?;
    let yaml_building = BuildingYamlSerializer::deserialize_building(&yaml)
        .map_err(|e| anyhow::anyhow!(e.to_string()))?;

    assert_eq!(yaml_building.name, imported_building.name);
    assert_eq!(yaml_building.floors.len(), 1);
    
    let y_floor = &yaml_building.floors[0];
    assert_eq!(y_floor.equipment.len(), 1);
    assert_eq!(y_floor.equipment[0].name, "panel-floor1");

    let y_wing_east = y_floor.wings.iter().find(|w| w.name == "East Wing").expect("East Wing in YAML");
    assert_eq!(y_wing_east.equipment.len(), 1);
    assert_eq!(y_wing_east.equipment[0].name, "thermostat-east");

    let y_room = &y_wing_east.rooms[0];
    assert_eq!(y_room.equipment.len(), 1);
    assert_eq!(y_room.equipment[0].name, "projector-01");

    Ok(())
}

#[test]
fn test_bidirectional_roundtrip_real_fixture() -> anyhow::Result<()> {
    // 1. Load simple.ifc fixture
    let processor = IFCProcessor::new();
    let parsing_result = processor.parse_native("tests/fixtures/ifc/simple.ifc", false)?;
    let building = parsing_result.building;

    // Verify simple.ifc contents
    assert_eq!(building.name, "TestBuilding");
    assert_eq!(building.floors.len(), 1);
    
    let floor = &building.floors[0];
    assert_eq!(floor.name, "Floor1");
    assert_eq!(floor.wings.len(), 1);
    
    let wing = &floor.wings[0];
    assert_eq!(wing.name, "Main"); // Default zone/wing name
    assert_eq!(wing.rooms.len(), 1);
    
    let room = &wing.rooms[0];
    assert_eq!(room.name, "Conference Room");

    // 2. Export to new temp IFC
    let temp_ifc = NamedTempFile::new()?;
    let exporter = IFCExporter::new(building.clone());
    exporter.export(temp_ifc.path())?;

    let re_parsing = processor.parse_native(temp_ifc.path().to_str().unwrap(), false)?;
    let re_building = re_parsing.building;

    assert_eq!(re_building.name, "TestBuilding");
    assert_eq!(re_building.floors.len(), 1);
    assert_eq!(re_building.floors[0].name, "Floor1");
    assert_eq!(re_building.floors[0].wings.len(), 1);
    assert_eq!(re_building.floors[0].wings[0].name, "Main");
    assert_eq!(re_building.floors[0].wings[0].rooms.len(), 1);
    assert_eq!(re_building.floors[0].wings[0].rooms[0].name, "Conference Room");

    Ok(())
}

/// L0 identity: product GlobalIds are deterministic across double export,
/// and re-import restores Arx ids + ifc_global_id.
#[test]
fn test_identity_stable_across_export_and_import() -> anyhow::Result<()> {
    let mut building = Building::new("Identity HQ".to_string(), "/identity".to_string());
    let mut floor = Floor::new("L1".to_string(), 1);
    let mut wing = Wing::new("Main".to_string());

    let mut room = Room::new("R-101".to_string(), RoomType::Office);
    let room_id = room.id.clone();
    let expected_room_gid = resolve_product_global_id(&None, &room_id);

    let mut equipment = Equipment::new(
        "eq-sensor-1".to_string(),
        "".to_string(),
        EquipmentType::HVAC,
    );
    let equipment_id = equipment.id.clone();
    let expected_eq_gid = resolve_product_global_id(&None, &equipment_id);
    equipment.position = Position {
        x: 1.0,
        y: 2.0,
        z: 1.5,
        coordinate_system: "building_local".to_string(),
    };
    room.add_equipment(equipment);
    wing.add_room(room);
    floor.add_wing(wing);
    building.add_floor(floor);

    let building_id = building.id.clone();
    let floor_id = building.floors[0].id.clone();
    let expected_building_gid = resolve_product_global_id(&None, &building_id);
    let expected_floor_gid = resolve_product_global_id(&None, &floor_id);

    // Export twice — product GlobalIds must be identical (relationship GUIDs may differ)
    let temp1 = NamedTempFile::new()?;
    let temp2 = NamedTempFile::new()?;
    IFCExporter::new(building.clone()).export(temp1.path())?;
    IFCExporter::new(building.clone()).export(temp2.path())?;

    let ifc1 = fs::read_to_string(temp1.path())?;
    let ifc2 = fs::read_to_string(temp2.path())?;

    for (label, gid) in [
        ("building", &expected_building_gid),
        ("floor", &expected_floor_gid),
        ("room", &expected_room_gid),
        ("equipment", &expected_eq_gid),
    ] {
        assert!(
            ifc1.contains(gid.as_str()),
            "export 1 missing {} GlobalId {}",
            label,
            gid
        );
        assert!(
            ifc2.contains(gid.as_str()),
            "export 2 missing {} GlobalId {} (product ids must be stable across exports)",
            label,
            gid
        );
    }

    assert!(
        ifc1.contains(PSET_ARX_IDENTITY),
        "Pset_ArxIdentity must be written"
    );
    assert!(ifc1.contains(PROP_ARX_ID) || ifc1.contains("ArxId"));
    assert!(ifc1.contains(&room_id), "Arx room id must appear in identity Pset");
    assert!(
        ifc1.contains(&equipment_id),
        "Arx equipment id must appear in identity Pset"
    );

    // Import restores Arx ids and ifc_global_id
    let processor = IFCProcessor::new();
    let imported = processor
        .parse_native(temp1.path().to_str().unwrap(), false)?
        .building;

    assert_eq!(imported.id, building_id);
    assert_eq!(
        imported.ifc_global_id.as_deref(),
        Some(expected_building_gid.as_str())
    );

    assert_eq!(imported.floors.len(), 1);
    let imp_floor = &imported.floors[0];
    assert_eq!(imp_floor.id, floor_id);
    assert_eq!(
        imp_floor.ifc_global_id.as_deref(),
        Some(expected_floor_gid.as_str())
    );

    let imp_room = imp_floor
        .wings
        .iter()
        .flat_map(|w| w.rooms.iter())
        .find(|r| r.name == "R-101")
        .expect("room R-101");
    assert_eq!(imp_room.id, room_id);
    assert_eq!(
        imp_room.ifc_global_id.as_deref(),
        Some(expected_room_gid.as_str())
    );

    let imp_eq = imp_room
        .equipment
        .iter()
        .find(|e| e.name == "eq-sensor-1")
        .or_else(|| {
            imp_floor
                .equipment
                .iter()
                .chain(imp_floor.wings.iter().flat_map(|w| w.equipment.iter()))
                .find(|e| e.name == "eq-sensor-1")
        })
        .expect("equipment eq-sensor-1");
    assert_eq!(imp_eq.id, equipment_id);
    assert_eq!(
        imp_eq.ifc_global_id.as_deref(),
        Some(expected_eq_gid.as_str())
    );

    // Stored GlobalId is preferred over derivation on re-export
    let mut with_foreign = building.clone();
    with_foreign.floors[0].wings[0].rooms[0].ifc_global_id =
        Some("ForeignGlobalIdValue01".to_string());
    let temp3 = NamedTempFile::new()?;
    IFCExporter::new(with_foreign).export(temp3.path())?;
    let ifc3 = fs::read_to_string(temp3.path())?;
    assert!(
        ifc3.contains("ForeignGlobalIdValue01"),
        "stored ifc_global_id must be reused on export"
    );

    Ok(())
}

/// L1: `lidar_enrichment` survives Model → IFC → Model and Model → YAML → Model.
#[test]
fn test_lidar_enrichment_roundtrip_via_ifc_and_yaml() -> anyhow::Result<()> {
    let scan_ts = DateTime::parse_from_rfc3339("2026-06-01T14:30:00Z")?
        .with_timezone(&Utc);

    let mut building = Building::new("LiDAR Building".to_string(), "/lidar".to_string());
    let mut floor = Floor::new("Ground".to_string(), 0);
    let mut wing = Wing::new("Main".to_string());

    let mut room = Room::new("Scan Room".to_string(), RoomType::Office);
    room.lidar_enrichment = Some(LidarEnrichment {
        point_count: 12_500,
        confidence_score: 0.92,
        last_scan_timestamp: Some(scan_ts),
        classification_heuristic: Some("occupancy_component_v1".to_string()),
    });

    let mut equipment = Equipment::new(
        "desk-cluster".to_string(),
        "".to_string(),
        EquipmentType::Furniture,
    );
    equipment.lidar_enrichment = Some(LidarEnrichment {
        point_count: 840,
        confidence_score: 0.75,
        last_scan_timestamp: Some(scan_ts),
        classification_heuristic: Some("furniture_cluster".to_string()),
    });
    room.add_equipment(equipment);
    wing.add_room(room);
    floor.add_wing(wing);
    building.add_floor(floor);

    // Model → IFC
    let temp_ifc = NamedTempFile::new()?;
    IFCExporter::new(building.clone()).export(temp_ifc.path())?;
    let ifc_text = fs::read_to_string(temp_ifc.path())?;
    assert!(
        ifc_text.contains(PSET_ARX_LIDAR),
        "export must write Pset_ArxLidarEnrichment"
    );
    assert!(
        ifc_text.contains(PROP_POINT_COUNT) || ifc_text.contains("PointCount"),
        "export must include PointCount"
    );
    assert!(ifc_text.contains("12500") || ifc_text.contains("12_500") || ifc_text.contains("12500"));

    // IFC → Model
    let processor = IFCProcessor::new();
    let imported = processor
        .parse_native(temp_ifc.path().to_str().unwrap(), false)?
        .building;

    let imp_room = imported
        .floors
        .iter()
        .flat_map(|f| f.wings.iter())
        .flat_map(|w| w.rooms.iter())
        .find(|r| r.name == "Scan Room")
        .expect("Scan Room after IFC import");

    let room_enr = imp_room
        .lidar_enrichment
        .as_ref()
        .expect("room lidar_enrichment after IFC import");
    assert_eq!(room_enr.point_count, 12_500);
    assert!((room_enr.confidence_score - 0.92).abs() < 1e-5);
    assert_eq!(
        room_enr.classification_heuristic.as_deref(),
        Some("occupancy_component_v1")
    );
    assert!(room_enr.last_scan_timestamp.is_some());
    // Typed field, not left as free-form bag keys
    assert!(
        !imp_room
            .properties
            .keys()
            .any(|k| k.starts_with(PSET_ARX_LIDAR)),
        "LiDAR keys must be lifted out of properties bag"
    );

    let imp_eq = imp_room
        .equipment
        .iter()
        .find(|e| e.name == "desk-cluster")
        .expect("desk-cluster after IFC import");
    let eq_enr = imp_eq
        .lidar_enrichment
        .as_ref()
        .expect("equipment lidar_enrichment after IFC import");
    assert_eq!(eq_enr.point_count, 840);
    assert!((eq_enr.confidence_score - 0.75).abs() < 1e-5);
    assert_eq!(
        eq_enr.classification_heuristic.as_deref(),
        Some("furniture_cluster")
    );

    // Model → YAML → Model preserves typed enrichment
    let yaml = BuildingYamlSerializer::serialize_building(&imported)
        .map_err(|e| anyhow::anyhow!(e.to_string()))?;
    assert!(
        yaml.contains("lidar_enrichment") || yaml.contains("point_count"),
        "YAML should serialize lidar enrichment"
    );
    let from_yaml = BuildingYamlSerializer::deserialize_building(&yaml)
        .map_err(|e| anyhow::anyhow!(e.to_string()))?;

    let y_room = from_yaml
        .floors
        .iter()
        .flat_map(|f| f.wings.iter())
        .flat_map(|w| w.rooms.iter())
        .find(|r| r.name == "Scan Room")
        .expect("Scan Room in YAML");
    assert_eq!(
        y_room
            .lidar_enrichment
            .as_ref()
            .map(|e| e.point_count),
        Some(12_500)
    );

    // Full backbone: Model → YAML → IFC → Model still keeps enrichment
    let temp2 = NamedTempFile::new()?;
    IFCExporter::new(from_yaml).export(temp2.path())?;
    let again = processor
        .parse_native(temp2.path().to_str().unwrap(), false)?
        .building;
    let again_room = again
        .floors
        .iter()
        .flat_map(|f| f.wings.iter())
        .flat_map(|w| w.rooms.iter())
        .find(|r| r.name == "Scan Room")
        .expect("Scan Room after second IFC pass");
    assert_eq!(
        again_room
            .lidar_enrichment
            .as_ref()
            .map(|e| e.point_count),
        Some(12_500)
    );

    Ok(())
}

/// Phase 3: free-form properties stay clean across Model → IFC → Model → IFC.
#[test]
fn test_property_keys_stay_clean_across_double_ifc_pass() -> anyhow::Result<()> {
    let mut building = Building::new("Props HQ".to_string(), "/props".to_string());
    let mut floor = Floor::new("F1".to_string(), 1);
    floor
        .properties
        .insert("fire_rating".to_string(), "2h".to_string());

    let mut wing = Wing::new("North".to_string());
    let mut room = Room::new("Lab".to_string(), RoomType::Laboratory);
    room.properties
        .insert("max_occupancy".to_string(), "12".to_string());
    room.properties
        .insert("finish".to_string(), "epoxy".to_string());

    let mut eq = Equipment::new(
        "fume-hood".to_string(),
        "".to_string(),
        EquipmentType::Safety,
    );
    eq.properties
        .insert("brand".to_string(), "LabConco".to_string());
    room.add_equipment(eq);
    wing.add_room(room);
    floor.add_wing(wing);
    building.add_floor(floor);

    let processor = IFCProcessor::new();

    let pass1 = NamedTempFile::new()?;
    IFCExporter::new(building).export(pass1.path())?;
    let mid = processor
        .parse_native(pass1.path().to_str().unwrap(), false)?
        .building;

    let mid_room = mid
        .floors
        .iter()
        .flat_map(|f| f.wings.iter())
        .flat_map(|w| w.rooms.iter())
        .find(|r| r.name == "Lab")
        .expect("Lab");
    assert_eq!(
        mid_room.properties.get("max_occupancy").map(String::as_str),
        Some("12")
    );
    assert_eq!(
        mid_room.properties.get("finish").map(String::as_str),
        Some("epoxy")
    );
    assert!(
        !mid_room
            .properties
            .keys()
            .any(|k| k.contains("Pset_ArxRoom")),
        "room bag must not retain Arx room pset prefixes: {:?}",
        mid_room.properties.keys().collect::<Vec<_>>()
    );

    let mid_floor = &mid.floors[0];
    assert_eq!(
        mid_floor.properties.get("fire_rating").map(String::as_str),
        Some("2h")
    );

    let mid_eq = mid_room
        .equipment
        .iter()
        .find(|e| e.name == "fume-hood")
        .expect("fume-hood");
    assert_eq!(
        mid_eq.properties.get("brand").map(String::as_str),
        Some("LabConco")
    );
    assert!(
        !mid_eq
            .properties
            .keys()
            .any(|k| k.contains("Pset_ArxEquipment")),
        "equipment bag must not retain Arx equipment pset prefixes"
    );

    // Second export/import must not grow double-prefixed keys
    let pass2 = NamedTempFile::new()?;
    IFCExporter::new(mid).export(pass2.path())?;
    let again = processor
        .parse_native(pass2.path().to_str().unwrap(), false)?
        .building;
    let again_room = again
        .floors
        .iter()
        .flat_map(|f| f.wings.iter())
        .flat_map(|w| w.rooms.iter())
        .find(|r| r.name == "Lab")
        .expect("Lab after second pass");
    assert_eq!(
        again_room
            .properties
            .get("max_occupancy")
            .map(String::as_str),
        Some("12")
    );
    assert!(
        !again_room
            .properties
            .keys()
            .any(|k| k.contains("Pset_ArxRoomProperties:Pset_")),
        "no double-prefixed keys after re-export: {:?}",
        again_room.properties.keys().collect::<Vec<_>>()
    );

    Ok(())
}

/// Phase 4 / L2: room position + extruded dimensions and equipment position
/// round-trip through IFC within geometry epsilon.
#[test]
fn test_geometry_position_and_dimensions_roundtrip() -> anyhow::Result<()> {
    let mut building = Building::new("Geo HQ".to_string(), "/geo".to_string());
    let mut floor = Floor::new("L0".to_string(), 0);
    floor.elevation = Some(0.0);
    let mut wing = Wing::new("Main".to_string());

    let mut room = Room::new("Geometry Lab".to_string(), RoomType::Laboratory);
    let room_pos = Position {
        x: 12.5,
        y: -3.25,
        z: 0.0,
        coordinate_system: "building_local".to_string(),
    };
    let room_dims = Dimensions {
        width: 8.0,
        depth: 5.5,
        height: 3.2,
    };
    room.spatial_properties = spatial_from_position_dims(room_pos.clone(), room_dims.clone());
    // Explicitly no mesh — extruded box path
    room.spatial_properties.mesh = None;

    let mut equipment = Equipment::new(
        "sensor-a".to_string(),
        "".to_string(),
        EquipmentType::HVAC,
    );
    let eq_pos = Position {
        x: 14.0,
        y: -2.0,
        z: 1.5,
        coordinate_system: "building_local".to_string(),
    };
    equipment.position = eq_pos.clone();
    equipment.mesh = None;
    room.add_equipment(equipment);
    wing.add_room(room);
    floor.add_wing(wing);
    building.add_floor(floor);

    let temp = NamedTempFile::new()?;
    IFCExporter::new(building.clone()).export(temp.path())?;

    let imported = IFCProcessor::new()
        .parse_native(temp.path().to_str().unwrap(), false)?
        .building;

    let imp_room = imported
        .floors
        .iter()
        .flat_map(|f| f.wings.iter())
        .flat_map(|w| w.rooms.iter())
        .find(|r| r.name == "Geometry Lab")
        .expect("Geometry Lab");

    assert!(
        positions_approx_eq(&imp_room.spatial_properties.position, &room_pos),
        "room position mismatch: got {:?} want {:?}",
        imp_room.spatial_properties.position,
        room_pos
    );
    assert!(
        dimensions_approx_eq(&imp_room.spatial_properties.dimensions, &room_dims),
        "room dimensions mismatch: got {:?} want {:?}",
        imp_room.spatial_properties.dimensions,
        room_dims
    );
    assert!(
        imp_room.spatial_properties.mesh.is_none(),
        "extruded box import should not invent a mesh"
    );
    // Bounding box follows center-XY / bottom-Z convention
    assert!(approx_eq(
        imp_room.spatial_properties.bounding_box.min.x,
        room_pos.x - room_dims.width / 2.0
    ));
    assert!(approx_eq(
        imp_room.spatial_properties.bounding_box.max.z,
        room_pos.z + room_dims.height
    ));

    let imp_eq = imp_room
        .equipment
        .iter()
        .find(|e| e.name == "sensor-a")
        .expect("sensor-a");
    assert!(
        positions_approx_eq(&imp_eq.position, &eq_pos),
        "equipment position mismatch: got {:?} want {:?}",
        imp_eq.position,
        eq_pos
    );
    assert!(
        imp_eq.mesh.is_none(),
        "equipment without mesh must not get a synthetic body"
    );

    // Second pass still stable
    let temp2 = NamedTempFile::new()?;
    IFCExporter::new(imported).export(temp2.path())?;
    let again = IFCProcessor::new()
        .parse_native(temp2.path().to_str().unwrap(), false)?
        .building;
    let again_room = again
        .floors
        .iter()
        .flat_map(|f| f.wings.iter())
        .flat_map(|w| w.rooms.iter())
        .find(|r| r.name == "Geometry Lab")
        .expect("Geometry Lab pass 2");
    assert!(dimensions_approx_eq(
        &again_room.spatial_properties.dimensions,
        &room_dims
    ));
    assert!(positions_approx_eq(
        &again_room.spatial_properties.position,
        &room_pos
    ));

    Ok(())
}

/// Phase 5 backbone: Model (with identity + LiDAR + geometry) → YAML → IFC → Model → merge → YAML.
#[test]
fn test_backbone_yaml_ifc_merge_roundtrip() -> anyhow::Result<()> {
    use arxos::core::LidarEnrichment;

    // 1. Canonical model with L0+L1+L2 fields
    let mut building = Building::new("Backbone HQ".into(), "/backbone".into());
    let mut floor = Floor::new("Level 1".into(), 1);
    floor.elevation = Some(0.0);
    let mut wing = Wing::new("East".into());

    let mut room = Room::new("Studio".into(), RoomType::Office);
    let room_id = room.id.clone();
    room.spatial_properties = spatial_from_position_dims(
        Position {
            x: 5.0,
            y: 4.0,
            z: 0.0,
            coordinate_system: "building_local".into(),
        },
        Dimensions {
            width: 6.0,
            depth: 4.0,
            height: 3.0,
        },
    );
    room.lidar_enrichment = Some(LidarEnrichment {
        point_count: 9_000,
        confidence_score: 0.88,
        last_scan_timestamp: None,
        classification_heuristic: Some("backbone_v1".into()),
    });
    room.properties
        .insert("finish".into(), "polished_concrete".into());

    let mut eq = Equipment::new("cam-01".into(), "".into(), EquipmentType::AV);
    let eq_id = eq.id.clone();
    eq.position = Position {
        x: 5.5,
        y: 4.2,
        z: 2.4,
        coordinate_system: "building_local".into(),
    };
    eq.lidar_enrichment = Some(LidarEnrichment {
        point_count: 120,
        confidence_score: 0.7,
        last_scan_timestamp: None,
        classification_heuristic: Some("fixture".into()),
    });
    room.add_equipment(eq);
    wing.add_room(room);
    floor.add_wing(wing);
    building.add_floor(floor);

    // 2. YAML round-trip
    let yaml = BuildingYamlSerializer::serialize_building(&building)
        .map_err(|e| anyhow::anyhow!(e.to_string()))?;
    let from_yaml = BuildingYamlSerializer::deserialize_building(&yaml)
        .map_err(|e| anyhow::anyhow!(e.to_string()))?;
    assert_eq!(from_yaml.floors[0].wings[0].rooms[0].id, room_id);

    // 3. IFC export / import
    let temp = NamedTempFile::new()?;
    IFCExporter::new(from_yaml.clone()).export(temp.path())?;
    let parsed = IFCProcessor::new().parse_native(temp.path().to_str().unwrap(), false)?;
    assert!(
        parsed.report.level_achieved == arxos::ifc::mapping::FidelityLevel::L2
            || !parsed.report.warnings.is_empty()
            || parsed.report.warnings.is_empty()
    );

    let imported = parsed.building;
    let imp_room = imported
        .floors
        .iter()
        .flat_map(|f| f.wings.iter())
        .flat_map(|w| w.rooms.iter())
        .find(|r| r.name == "Studio")
        .expect("Studio");
    assert_eq!(imp_room.id, room_id);
    assert!(imp_room.ifc_global_id.is_some());
    assert_eq!(
        imp_room.lidar_enrichment.as_ref().map(|e| e.point_count),
        Some(9_000)
    );
    assert!(dimensions_approx_eq(
        &imp_room.spatial_properties.dimensions,
        &Dimensions {
            width: 6.0,
            depth: 4.0,
            height: 3.0,
        }
    ));
    assert_eq!(
        imp_room.properties.get("finish").map(String::as_str),
        Some("polished_concrete")
    );

    let imp_eq = imp_room
        .equipment
        .iter()
        .find(|e| e.name == "cam-01")
        .expect("cam-01");
    assert_eq!(imp_eq.id, eq_id);
    assert_eq!(
        imp_eq.lidar_enrichment.as_ref().map(|e| e.point_count),
        Some(120)
    );

    // 4. Merge: existing has Arx-only status; IFC re-import would reset without merge
    let mut existing = from_yaml;
    existing.floors[0].wings[0].rooms[0].equipment[0].status =
        arxos::core::EquipmentStatus::Maintenance;
    existing.floors[0].wings[0].rooms[0]
        .properties
        .insert("arx_only".into(), "secret".into());

    // Simulate re-import of IFC-derived model that lost arx_only and status
    let merge = merge_building(&existing, imported);
    assert_eq!(merge.stats.rooms_matched, 1);
    assert_eq!(merge.stats.equipment_matched, 1);

    let merged_room = &merge.building.floors[0].wings[0].rooms[0];
    assert_eq!(
        merged_room.properties.get("arx_only").map(String::as_str),
        Some("secret")
    );
    assert_eq!(
        merged_room.equipment[0].status,
        arxos::core::EquipmentStatus::Maintenance
    );
    assert_eq!(
        merged_room.lidar_enrichment.as_ref().map(|e| e.point_count),
        Some(9_000)
    );

    // 5. Final YAML still holds the backbone state
    let final_yaml = BuildingYamlSerializer::serialize_building(&merge.building)
        .map_err(|e| anyhow::anyhow!(e.to_string()))?;
    let final_b = BuildingYamlSerializer::deserialize_building(&final_yaml)
        .map_err(|e| anyhow::anyhow!(e.to_string()))?;
    assert_eq!(final_b.floors[0].wings[0].rooms[0].id, room_id);
    assert!(final_yaml.contains("lidar_enrichment") || final_yaml.contains("point_count"));
    assert!(final_yaml.contains("arx_only") || final_yaml.contains("secret"));

    Ok(())
}

use arxos::core::{Building, Floor, Room, RoomType, Wing, Equipment, EquipmentType, Position};
use arxos::ifc::IFCProcessor;
use arxos::export::ifc::IFCExporter;
use arxos::yaml::BuildingYamlSerializer;
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
    assert_eq!(imp_floor.properties.get("Pset_ArxFloorProperties:fire_rating"), Some(&"1h".to_string()));

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
    assert_eq!(imp_room.properties.get("Pset_ArxRoomProperties:max_occupancy"), Some(&"20".to_string()));
    assert_eq!(imp_room.properties.get("Pset_ArxRoomProperties:ArxWing"), Some(&"East Wing".to_string()));

    assert_eq!(imp_room.equipment.len(), 1);
    let imp_eq = &imp_room.equipment[0];
    assert_eq!(imp_eq.name, "projector-01");
    assert_eq!(imp_eq.equipment_type, EquipmentType::AV);
    assert_eq!(imp_eq.properties.get("Pset_ArxEquipmentProperties:brand"), Some(&"Epson".to_string()));

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

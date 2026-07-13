#[cfg(test)]
mod tests {
    use crate::core::operations::spatial::{spatial_query, transform_coordinates};
    use crate::core::spatial::Point3D;
    use crate::core::types::Position;
    use crate::core::CoordinateSystemInfo;
    use crate::core::{Building, Equipment, EquipmentType, Floor, Room, RoomType, Wing};

    fn create_test_building() -> Building {
        let mut building = Building::new("Test Building".to_string(), "/test".to_string());

        building.coordinate_systems.push(CoordinateSystemInfo {
            name: "local_offset".to_string(),
            origin: Point3D::new(10.0, 10.0, 0.0),
            x_axis: Point3D::new(1.0, 0.0, 0.0),
            y_axis: Point3D::new(0.0, 1.0, 0.0),
            z_axis: Point3D::new(0.0, 0.0, 1.0),
            description: None,
        });

        let mut floor = Floor::new("Ground".to_string(), 0);
        let mut wing = Wing::new("East".to_string());

        let mut room = Room::new("Room A".to_string(), RoomType::Office);
        room.spatial_properties.position = Position {
            x: 0.0,
            y: 0.0,
            z: 0.0,
            coordinate_system: "building_local".to_string(),
        };
        room.spatial_properties.bounding_box = crate::core::types::BoundingBox::new(
            Position {
                x: 0.0,
                y: 0.0,
                z: 0.0,
                coordinate_system: "building_local".to_string(),
            },
            Position {
                x: 10.0,
                y: 10.0,
                z: 3.0,
                coordinate_system: "building_local".to_string(),
            },
        );
        wing.add_room(room);

        let mut room_b = Room::new("Room B".to_string(), RoomType::Office);
        room_b.spatial_properties.position = Position {
            x: 20.0,
            y: 0.0,
            z: 0.0,
            coordinate_system: "building_local".to_string(),
        };
        wing.add_room(room_b);

        floor.add_wing(wing);

        let mut equipment = Equipment::new(
            "TestEq".to_string(),
            "/eq".to_string(),
            EquipmentType::Other("Test".to_string()),
        );
        equipment.position = Position {
            x: 5.0,
            y: 5.0,
            z: 0.0,
            coordinate_system: "building_local".to_string(),
        };
        floor.equipment.push(equipment);

        building.add_floor(floor);
        building
    }

    #[test]
    fn test_spatial_query_distance() {
        let building = create_test_building();
        let results = spatial_query(
            &building,
            "distance",
            "",
            vec!["Room A".to_string(), "Room B".to_string()],
        )
        .unwrap();

        assert_eq!(results.len(), 1);
        assert_eq!(results[0].entity_name, "Room B");
        assert_eq!(results[0].distance, 20.0);
    }

    #[test]
    fn test_spatial_query_nearest() {
        let building = create_test_building();
        let results = spatial_query(
            &building,
            "nearest",
            "room",
            vec!["2.0".to_string(), "2.0".to_string(), "0.0".to_string()],
        )
        .unwrap();

        assert_eq!(results.len(), 1);
        assert_eq!(results[0].entity_name, "Room A");
    }

    #[test]
    fn test_transform_coordinates() {
        let building = create_test_building();

        let result =
            transform_coordinates(&building, "building_local", "local_offset", "Room A").unwrap();
        assert!(result.contains("Room A"));
        assert!(result.contains("local_offset"));
    }
}

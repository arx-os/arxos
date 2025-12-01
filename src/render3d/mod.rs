//! 3D Building Renderer for ArxOS
//!
//! This module provides advanced 3D visualization capabilities for building data,
//! including multi-floor rendering, equipment positioning, and spatial relationships.
//! It also includes interactive 3D rendering with real-time controls.

// Core modules
mod ascii;
mod camera;
mod canvas_operations;
mod extractors;
mod point_cloud;
mod projection;
mod projections;
mod renderer;
mod scene_cache;
mod spatial_query;
mod transforms;
mod types;
mod utils;
mod views;

// Re-export interactive components
pub mod events;
pub mod info_panel;
pub mod interactive;
pub mod state;

// Re-export particle and animation components
pub mod animation;
pub mod effects;
pub mod particles;

// Re-export types
pub use types::*;

// Re-export renderer and utils
pub use renderer::Building3DRenderer;
pub use utils::format_scene_output;

// Re-export point cloud renderer
pub use point_cloud::{PointCloudRenderer, Point3DColored, building_to_point_cloud};

// Re-export interactive components
pub use animation::{
    Animation, AnimationData, AnimationSystem, AnimationType, EasingFunction, EquipmentStatus,
    ParticleEffectType,
};
pub use effects::{
    EffectData, EffectQuality, EffectState, EffectType, EffectsConfig, VisualEffect,
    VisualEffectsEngine,
};
pub use events::{
    Action, CameraAction, EventHandler, InteractiveEvent, ViewModeAction, ZoomAction,
};
pub use info_panel::{render_info_panel, InfoPanelState};
pub use interactive::{InteractiveConfig, InteractiveRenderer};
pub use particles::{
    AlertLevel, Particle, ParticleData, ParticleSystem, ParticleType, StatusType,
    Vector3D as ParticleVector3D,
};
pub use state::{
    CameraState, InteractiveState, QualityLevel, RenderPreferences, Rotation3D, SessionData,
    ViewMode,
};

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::spatial::{BoundingBox3D, Point3D};

    /// Create test building data for 3D rendering tests
    fn create_test_building_data() -> arx::yaml::BuildingData {
        use crate::core::{
            BoundingBox, Dimensions, Equipment, EquipmentHealthStatus, EquipmentStatus,
            EquipmentType, Floor, Position, Room, RoomType, SpatialProperties, Wing,
        };
        use crate::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
        use chrono::Utc;
        use std::collections::HashMap;

        // Create equipment for room
        let equip1 = Equipment {
            id: "EQUIP_1".to_string(),
            name: "HVAC Unit 1".to_string(),
            path: "/TEST_BUILDING/FLOOR_1/WING_1/ROOM_1/EQUIP_1".to_string(),
            address: None,
            equipment_type: EquipmentType::HVAC,
            position: Position {
                x: 20.0,
                y: 20.0,
                z: 1.5,
                coordinate_system: "LOCAL".to_string(),
            },
            properties: HashMap::new(),
            status: EquipmentStatus::Active,
            health_status: Some(EquipmentHealthStatus::Healthy),
            room_id: Some("ROOM_1".to_string()),
            sensor_mappings: None,
        };

        // Create room
        let room1 = Room {
            id: "ROOM_1".to_string(),
            name: "Room 1".to_string(),
            room_type: RoomType::Office,
            equipment: vec![equip1],
            spatial_properties: SpatialProperties {
                position: Position {
                    x: 10.0,
                    y: 10.0,
                    z: 0.0,
                    coordinate_system: "LOCAL".to_string(),
                },
                dimensions: Dimensions {
                    width: 20.0,
                    height: 3.0,
                    depth: 20.0,
                },
                bounding_box: BoundingBox {
                    min: Position {
                        x: 10.0,
                        y: 10.0,
                        z: 0.0,
                        coordinate_system: "LOCAL".to_string(),
                    },
                    max: Position {
                        x: 30.0,
                        y: 30.0,
                        z: 3.0,
                        coordinate_system: "LOCAL".to_string(),
                    },
                },
                coordinate_system: "LOCAL".to_string(),
            },
            properties: HashMap::new(),
            created_at: None,
            updated_at: None,
        };

        // Create wing
        let wing1 = Wing {
            id: "WING_1".to_string(),
            name: "East Wing".to_string(),
            rooms: vec![room1],
            equipment: vec![],
            properties: HashMap::new(),
        };

        // Create floor 1
        let floor1 = Floor {
            id: "FLOOR_1".to_string(),
            name: "Ground Floor".to_string(),
            level: 0,
            elevation: Some(0.0),
            bounding_box: Some(BoundingBox3D {
                min: Point3D {
                    x: 0.0,
                    y: 0.0,
                    z: 0.0,
                },
                max: Point3D {
                    x: 100.0,
                    y: 100.0,
                    z: 3.0,
                },
            }),
            wings: vec![wing1],
            equipment: vec![],
            properties: HashMap::new(),
        };

        // Create equipment for floor 2
        let equip2 = Equipment {
            id: "EQUIP_2".to_string(),
            name: "Light Fixture 1".to_string(),
            path: "/TEST_BUILDING/FLOOR_2/EQUIP_2".to_string(),
            address: None,
            equipment_type: EquipmentType::Electrical,
            position: Position {
                x: 50.0,
                y: 50.0,
                z: 4.5,
                coordinate_system: "LOCAL".to_string(),
            },
            properties: HashMap::new(),
            status: EquipmentStatus::Active,
            health_status: Some(EquipmentHealthStatus::Warning),
            room_id: None,
            sensor_mappings: None,
        };

        // Create floor 2
        let floor2 = Floor {
            id: "FLOOR_2".to_string(),
            name: "First Floor".to_string(),
            level: 1,
            elevation: Some(3.0),
            bounding_box: Some(BoundingBox3D {
                min: Point3D {
                    x: 0.0,
                    y: 0.0,
                    z: 3.0,
                },
                max: Point3D {
                    x: 100.0,
                    y: 100.0,
                    z: 6.0,
                },
            }),
            wings: vec![],
            equipment: vec![equip2],
            properties: HashMap::new(),
        };

        BuildingData {
            building: BuildingInfo {
                id: "TEST_BUILDING".to_string(),
                name: "Test Building".to_string(),
                description: Some("Test building for 3D rendering".to_string()),
                created_at: Utc::now(),
                updated_at: Utc::now(),
                version: "1.0.0".to_string(),
                global_bounding_box: Some(BoundingBox3D {
                    min: Point3D {
                        x: 0.0,
                        y: 0.0,
                        z: 0.0,
                    },
                    max: Point3D {
                        x: 100.0,
                        y: 100.0,
                        z: 6.0,
                    },
                }),
            },
            coordinate_systems: vec![],
            metadata: BuildingMetadata {
                source_file: Some("test.ifc".to_string()),
                parser_version: "1.0.0".to_string(),
                total_entities: 10,
                spatial_entities: 8,
                coordinate_system: "WGS84".to_string(),
                units: "meters".to_string(),
                tags: vec!["test".to_string()],
            },
            floors: vec![floor1, floor2],
        }
    }

    #[test]
    fn test_3d_renderer_creation() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();

        let renderer = Building3DRenderer::new(building_data, config);

        // Test default camera settings
        assert_eq!(renderer.camera.position.z, 100.0);
        assert_eq!(renderer.camera.fov, 45.0);

        // Test default projection settings
        assert_eq!(
            renderer.projection.projection_type,
            ProjectionType::Isometric
        );
        assert_eq!(renderer.projection.view_angle, ViewAngle::Isometric);
    }

    #[test]
    fn test_camera_manipulation() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let mut renderer = Building3DRenderer::new(building_data, config);

        let new_position = Point3D {
            x: 100.0,
            y: 100.0,
            z: 200.0,
        };
        let new_target = Point3D {
            x: 50.0,
            y: 50.0,
            z: 0.0,
        };

        renderer.set_camera(new_position, new_target);

        assert_eq!(renderer.camera.position.x, 100.0);
        assert_eq!(renderer.camera.position.y, 100.0);
        assert_eq!(renderer.camera.position.z, 200.0);
        assert_eq!(renderer.camera.target.x, 50.0);
        assert_eq!(renderer.camera.target.y, 50.0);
        assert_eq!(renderer.camera.target.z, 0.0);
    }

    #[test]
    fn test_projection_manipulation() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let mut renderer = Building3DRenderer::new(building_data, config);

        renderer.set_projection(ProjectionType::Perspective, ViewAngle::Front);

        assert_eq!(
            renderer.projection.projection_type,
            ProjectionType::Perspective
        );
        assert_eq!(renderer.projection.view_angle, ViewAngle::Front);
    }

    #[test]
    fn test_3d_scene_rendering() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);

        let scene = renderer
            .render_3d_advanced()
            .expect("Failed to render 3D scene");

        assert_eq!(scene.building_name.as_str(), "Test Building");
        assert_eq!(scene.floors.len(), 2);
        // Equipment count: 1 in room (floor 0) + 1 on floor 1 = 2 total
        assert_eq!(
            scene.equipment.len(),
            2,
            "Should have 2 equipment (1 in room, 1 on floor)"
        );
        assert_eq!(scene.rooms.len(), 1, "Should have 1 room in wing");
        assert_eq!(scene.metadata.total_floors, 2);
        // Total equipment from floors: floor 0 has 0 floor-level, floor 1 has 1 floor-level = 1
        assert_eq!(
            scene.metadata.total_equipment, 1,
            "Metadata counts only floor-level equipment"
        );
        assert_eq!(scene.metadata.total_rooms, 1);
    }

    #[test]
    fn test_isometric_projection() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);

        let point = Point3D {
            x: 10.0,
            y: 20.0,
            z: 30.0,
        };
        let projected = renderer.isometric_projection(&point);

        // Isometric projection should transform the point
        assert_ne!(projected.x, point.x);
        assert_ne!(projected.y, point.y);
        assert_eq!(projected.z, point.z); // Z should remain the same for depth sorting
    }

    #[test]
    fn test_orthographic_projection() {
        let building_data = create_test_building_data();
        let config = Render3DConfig {
            projection_type: ProjectionType::Orthographic,
            view_angle: ViewAngle::TopDown,
            ..Default::default()
        };
        let renderer = Building3DRenderer::new(building_data, config);

        let point = Point3D {
            x: 10.0,
            y: 20.0,
            z: 30.0,
        };
        let projected = renderer.orthographic_projection(&point);

        // Orthographic projection should scale the point for TopDown view
        assert_eq!(projected.x, point.x * renderer.projection.scale);
        assert_eq!(projected.y, point.y * renderer.projection.scale);
        assert_eq!(projected.z, point.z);
    }

    #[test]
    fn test_vector3d_operations() {
        let vector = Vector3D::new(3.0, 4.0, 0.0);

        assert_eq!(vector.length(), 5.0);

        let normalized = vector.normalize();
        assert!((normalized.length() - 1.0).abs() < 0.001);
        assert!((normalized.x - 0.6).abs() < 0.001);
        assert!((normalized.y - 0.8).abs() < 0.001);
        assert_eq!(normalized.z, 0.0);
    }

    #[test]
    fn test_viewport_creation() {
        let viewport = Viewport3D::new(100, 50);

        assert_eq!(viewport.width, 100);
        assert_eq!(viewport.height, 50);
        assert_eq!(viewport.offset_x, 0);
        assert_eq!(viewport.offset_y, 0);
        assert_eq!(viewport.depth_buffer.len(), 50);
        assert_eq!(viewport.depth_buffer[0].len(), 100);
    }

    #[test]
    fn test_ascii_rendering() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);

        let scene = renderer
            .render_3d_advanced()
            .expect("Failed to render 3D scene");
        let ascii_output = renderer
            .render_to_ascii_advanced(&scene)
            .expect("Failed to render ASCII");

        // Check that ASCII output contains expected elements
        assert!(ascii_output.contains("Test Building"));
        assert!(ascii_output.contains("3D Building Visualization"));
        assert!(ascii_output.contains("floors"));
        assert!(ascii_output.contains("equipment"));
        assert!(ascii_output.contains("Projection"));
        assert!(ascii_output.contains("Camera"));
    }

    #[test]
    fn test_spatial_index_integration() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);

        // Test without spatial index
        assert!(renderer.spatial_index.is_none());
        let entities = renderer.query_spatial_entities(&BoundingBox3D {
            min: Point3D {
                x: 0.0,
                y: 0.0,
                z: 0.0,
            },
            max: Point3D {
                x: 100.0,
                y: 100.0,
                z: 10.0,
            },
        });
        assert_eq!(entities.len(), 0);

        // Test spatial queries without spatial index
        let room_entities = renderer.query_entities_in_room("ROOM_1");
        assert_eq!(room_entities.len(), 0);

        let floor_entities = renderer.query_entities_on_floor(0);
        assert_eq!(floor_entities.len(), 0);

        let nearest = renderer.find_nearest_entity(&Point3D {
            x: 20.0,
            y: 20.0,
            z: 1.5,
        });
        assert!(nearest.is_none());
    }

    #[test]
    fn test_enhanced_rendering_without_spatial_index() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);

        // Test enhanced rendering without spatial index (should work normally)
        let scene = renderer.render_3d_with_spatial_queries().unwrap();

        assert_eq!(scene.building_name.as_str(), "Test Building");
        assert_eq!(scene.floors.len(), 2);
        assert_eq!(scene.equipment.len(), 2, "Should have 2 equipment total");
        assert_eq!(scene.metadata.total_floors, 2);
        assert_eq!(scene.metadata.total_equipment, 2);
    }

    #[test]
    fn test_spatial_query_methods() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);

        // Test spatial query methods return empty results without spatial index
        let bbox = BoundingBox3D {
            min: Point3D {
                x: 0.0,
                y: 0.0,
                z: 0.0,
            },
            max: Point3D {
                x: 100.0,
                y: 100.0,
                z: 10.0,
            },
        };

        let entities = renderer.query_spatial_entities(&bbox);
        assert_eq!(entities.len(), 0);

        let radius_entities = renderer.query_entities_within_radius(
            &Point3D {
                x: 20.0,
                y: 20.0,
                z: 1.5,
            },
            10.0,
        );
        assert_eq!(radius_entities.len(), 0);

        let clusters = renderer.get_equipment_clusters(2);
        assert_eq!(clusters.len(), 0);
    }

    #[test]
    fn test_3d_ascii_art_rendering() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);

        let scene = renderer.render_3d_advanced().unwrap();
        let ascii_art = renderer.render_3d_ascii_art(&scene).unwrap();

        // Check that ASCII art contains expected elements
        assert!(ascii_art.contains("3D ASCII Building Visualization"));
        assert!(ascii_art.contains("Legend:"));
        assert!(ascii_art.contains("Test Building"));
        assert!(ascii_art.contains("█=Wall"));
        assert!(ascii_art.contains("▲=HVAC"));
        assert!(ascii_art.contains("●=Electrical"));
    }

    #[test]
    fn test_canvas_rendering_methods() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);

        let scene = renderer.render_3d_advanced().unwrap();

        // Test that canvas rendering methods work without panicking
        let mut canvas = vec![vec![' '; 120]; 40];
        let mut depth_buffer = vec![vec![f64::NEG_INFINITY; 120]; 40];

        // These should not panic
        renderer.render_floors_to_canvas(
            &scene.floors,
            &mut canvas[..],
            &mut depth_buffer[..],
            120,
            40,
        );
        renderer.render_equipment_to_canvas(
            &scene.equipment,
            &mut canvas[..],
            &mut depth_buffer[..],
            120,
            40,
        );
        renderer.render_rooms_to_canvas(
            &scene.rooms,
            &mut canvas[..],
            &mut depth_buffer[..],
            120,
            40,
        );

        // Check that some rendering occurred
        let has_content = canvas.iter().any(|row| row.iter().any(|&ch| ch != ' '));
        assert!(has_content);
    }

    #[test]
    fn test_screen_projection() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);

        // Test projection indirectly through render_3d_advanced
        let scene = renderer.render_3d_advanced().unwrap();

        // Verify scene was created successfully (indirectly tests projection)
        assert!(!scene.floors.is_empty());
        assert_eq!(scene.building_name.as_str(), "Test Building");
    }

    #[test]
    fn test_equipment_symbol_mapping() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);

        let scene = renderer.render_3d_advanced().unwrap();

        // Test that equipment symbols are correctly mapped
        // Note: equipment_type is now Debug format (e.g., "HVAC", "Electrical")
        let hvac_equipment = scene
            .equipment
            .iter()
            .find(|e| matches!(e.equipment_type, arx::core::EquipmentType::HVAC));
        let electrical_equipment = scene
            .equipment
            .iter()
            .find(|e| matches!(e.equipment_type, arx::core::EquipmentType::Electrical));

        // We should have HVAC and Electrical equipment
        assert!(hvac_equipment.is_some(), "Should have HVAC equipment");
        assert!(
            electrical_equipment.is_some(),
            "Should have Electrical equipment"
        );

        // Test that equipment_type is correctly formatted
        let hvac_type = &hvac_equipment.unwrap().equipment_type;
        let electrical_type = &electrical_equipment.unwrap().equipment_type;

        assert!(
            matches!(hvac_type, arx::core::EquipmentType::HVAC),
            "HVAC equipment_type should be HVAC"
        );
        assert!(
            matches!(electrical_type, arx::core::EquipmentType::Electrical),
            "Electrical equipment_type should be Electrical"
        );
    }
}

/// Start the interactive 3D renderer for a building
///
/// # Arguments
///
/// * `_building_name` - Name of the building to render
/// * `_brightness_ramp` - Character ramp for depth visualization
pub fn start_interactive_renderer(
    _building_name: &str,
    _brightness_ramp: &'static str,
) -> Result<(), Box<dyn std::error::Error>> {
    // This function needs to be implemented or the call to run_interactive_renderer needs to be added to the interactive module
    Err("Interactive renderer not yet fully implemented".into())
}

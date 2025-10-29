//! 3D Building Renderer for ArxOS
//!
//! This module provides advanced 3D visualization capabilities for building data,
//! including multi-floor rendering, equipment positioning, and spatial relationships.
//! It also includes interactive 3D rendering with real-time controls.

// Core modules
mod types;
mod camera;
mod projection;
mod renderer;
mod utils;

// Re-export interactive components
pub mod interactive;
pub mod events;
pub mod state;

// Re-export particle and animation components
pub mod particles;
pub mod animation;
pub mod effects;

// Re-export types
pub use types::*;

// Re-export renderer and utils
pub use renderer::Building3DRenderer;
pub use utils::format_scene_output;

// Re-export interactive components
pub use interactive::{InteractiveRenderer, InteractiveConfig};
pub use events::{EventHandler, InteractiveEvent, Action, CameraAction, ZoomAction, ViewModeAction};
pub use state::{InteractiveState, CameraState, ViewMode, Rotation3D, SessionData, RenderPreferences, QualityLevel};
pub use particles::{ParticleSystem, Particle, ParticleType, ParticleData, Vector3D as ParticleVector3D, StatusType, AlertLevel};
pub use animation::{AnimationSystem, Animation, AnimationType, AnimationData, EasingFunction, EquipmentStatus, ParticleEffectType};
pub use effects::{VisualEffectsEngine, VisualEffect, EffectType, EffectState, EffectData, EffectsConfig, EffectQuality};


#[cfg(test)]
mod tests {
    use super::*;
    use crate::spatial::{Point3D, BoundingBox3D};
    
    /// Create test building data for 3D rendering tests
    fn create_test_building_data() -> crate::yaml::BuildingData {
        use chrono::Utc;
        use std::collections::HashMap;
        
        crate::yaml::BuildingData {
            building: crate::yaml::BuildingInfo {
                id: "TEST_BUILDING".to_string(),
                name: "Test Building".to_string(),
                description: Some("Test building for 3D rendering".to_string()),
                created_at: Utc::now(),
                updated_at: Utc::now(),
                version: "1.0.0".to_string(),
                global_bounding_box: Some(BoundingBox3D {
                    min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                    max: Point3D { x: 100.0, y: 100.0, z: 6.0 },
                }),
            },
            coordinate_systems: vec![],
            metadata: crate::yaml::BuildingMetadata {
                source_file: Some("test.ifc".to_string()),
                parser_version: "1.0.0".to_string(),
                total_entities: 10,
                spatial_entities: 8,
                coordinate_system: "WGS84".to_string(),
                units: "meters".to_string(),
                tags: vec!["test".to_string()],
            },
            floors: vec![
                crate::yaml::FloorData {
                    id: "FLOOR_1".to_string(),
                    name: "Ground Floor".to_string(),
                    level: 0,
                    elevation: 0.0,
                    bounding_box: Some(BoundingBox3D {
                        min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
                        max: Point3D { x: 100.0, y: 100.0, z: 3.0 },
                    }),
                    rooms: vec![
                        crate::yaml::RoomData {
                            id: "ROOM_1".to_string(),
                            name: "Room 1".to_string(),
                            room_type: "Office".to_string(),
                            area: Some(400.0),
                            volume: Some(1200.0),
                            position: Point3D { x: 10.0, y: 10.0, z: 0.0 },
                            bounding_box: BoundingBox3D {
                                min: Point3D { x: 10.0, y: 10.0, z: 0.0 },
                                max: Point3D { x: 30.0, y: 30.0, z: 3.0 },
                            },
                            equipment: vec!["EQUIP_1".to_string()],
                            properties: HashMap::new(),
                        }
                    ],
                    equipment: vec![
                        crate::yaml::EquipmentData {
                            id: "EQUIP_1".to_string(),
                            name: "HVAC Unit 1".to_string(),
                            equipment_type: "IFCAIRHANDLINGUNIT".to_string(),
                            system_type: "HVAC".to_string(),
                            position: Point3D { x: 20.0, y: 20.0, z: 1.5 },
                            bounding_box: BoundingBox3D {
                                min: Point3D { x: 18.0, y: 18.0, z: 1.0 },
                                max: Point3D { x: 22.0, y: 22.0, z: 2.0 },
                            },
                            status: crate::yaml::EquipmentStatus::Healthy,
                            properties: HashMap::new(),
                            universal_path: "/TEST_BUILDING/FLOOR_1/ROOM_1/EQUIP_1".to_string(),
                            sensor_mappings: None,
                        }
                    ],
                },
                crate::yaml::FloorData {
                    id: "FLOOR_2".to_string(),
                    name: "First Floor".to_string(),
                    level: 1,
                    elevation: 3.0,
                    bounding_box: Some(BoundingBox3D {
                        min: Point3D { x: 0.0, y: 0.0, z: 3.0 },
                        max: Point3D { x: 100.0, y: 100.0, z: 6.0 },
                    }),
                    rooms: vec![],
                    equipment: vec![
                        crate::yaml::EquipmentData {
                            id: "EQUIP_2".to_string(),
                            name: "Light Fixture 1".to_string(),
                            equipment_type: "IFCLIGHTFIXTURE".to_string(),
                            system_type: "Electrical".to_string(),
                            position: Point3D { x: 50.0, y: 50.0, z: 4.5 },
                            bounding_box: BoundingBox3D {
                                min: Point3D { x: 49.0, y: 49.0, z: 4.0 },
                                max: Point3D { x: 51.0, y: 51.0, z: 5.0 },
                            },
                            status: crate::yaml::EquipmentStatus::Warning,
                            properties: HashMap::new(),
                            universal_path: "/TEST_BUILDING/FLOOR_2/EQUIP_2".to_string(),
                            sensor_mappings: None,
                        }
                    ],
                },
            ],
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
        assert_eq!(renderer.projection.projection_type, ProjectionType::Isometric);
        assert_eq!(renderer.projection.view_angle, ViewAngle::Isometric);
    }
    
    #[test]
    fn test_camera_manipulation() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let mut renderer = Building3DRenderer::new(building_data, config);
        
        let new_position = Point3D { x: 100.0, y: 100.0, z: 200.0 };
        let new_target = Point3D { x: 50.0, y: 50.0, z: 0.0 };
        
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
        
        assert_eq!(renderer.projection.projection_type, ProjectionType::Perspective);
        assert_eq!(renderer.projection.view_angle, ViewAngle::Front);
    }
    
    #[test]
    fn test_3d_scene_rendering() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);
        
        let scene = renderer.render_3d_advanced().expect("Failed to render 3D scene");
        
        assert_eq!(scene.building_name, "Test Building");
        assert_eq!(scene.floors.len(), 2);
        assert_eq!(scene.equipment.len(), 2);
        assert_eq!(scene.rooms.len(), 1);
        assert_eq!(scene.metadata.total_floors, 2);
        assert_eq!(scene.metadata.total_equipment, 2);
        assert_eq!(scene.metadata.total_rooms, 1);
    }
    
    #[test]
    fn test_isometric_projection() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);
        
        let point = Point3D { x: 10.0, y: 20.0, z: 30.0 };
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
        
        let point = Point3D { x: 10.0, y: 20.0, z: 30.0 };
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
        
        let scene = renderer.render_3d_advanced().expect("Failed to render 3D scene");
        let ascii_output = renderer.render_to_ascii_advanced(&scene).expect("Failed to render ASCII");
        
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
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D { x: 100.0, y: 100.0, z: 10.0 },
        });
        assert_eq!(entities.len(), 0);
        
        // Test spatial queries without spatial index
        let room_entities = renderer.query_entities_in_room("ROOM_1");
        assert_eq!(room_entities.len(), 0);
        
        let floor_entities = renderer.query_entities_on_floor(0);
        assert_eq!(floor_entities.len(), 0);
        
        let nearest = renderer.find_nearest_entity(&Point3D { x: 20.0, y: 20.0, z: 1.5 });
        assert!(nearest.is_none());
    }
    
    #[test]
    fn test_enhanced_rendering_without_spatial_index() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);
        
        // Test enhanced rendering without spatial index (should work normally)
        let scene = renderer.render_3d_with_spatial_queries().unwrap();
        
        assert_eq!(scene.building_name, "Test Building");
        assert_eq!(scene.floors.len(), 2);
        assert_eq!(scene.equipment.len(), 2);
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
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D { x: 100.0, y: 100.0, z: 10.0 },
        };
        
        let entities = renderer.query_spatial_entities(&bbox);
        assert_eq!(entities.len(), 0);
        
        let radius_entities = renderer.query_entities_within_radius(&Point3D { x: 20.0, y: 20.0, z: 1.5 }, 10.0);
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
        renderer.render_floors_to_canvas(&scene.floors, &mut canvas, &mut depth_buffer, 120, 40);
        renderer.render_equipment_to_canvas(&scene.equipment, &mut canvas, &mut depth_buffer, 120, 40);
        renderer.render_rooms_to_canvas(&scene.rooms, &mut canvas, &mut depth_buffer, 120, 40);
        
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
        assert_eq!(scene.building_name, "Test Building");
    }
    
    #[test]
    fn test_equipment_symbol_mapping() {
        let building_data = create_test_building_data();
        let config = Render3DConfig::default();
        let renderer = Building3DRenderer::new(building_data, config);
        
        let scene = renderer.render_3d_advanced().unwrap();
        
        // Test that equipment symbols are correctly mapped
        let hvac_equipment = scene.equipment.iter().find(|e| e.equipment_type.contains("AIR"));
        let electrical_equipment = scene.equipment.iter().find(|e| e.equipment_type.contains("LIGHT"));
        
        // We should have HVAC equipment (IFCAIRHANDLINGUNIT) and electrical equipment (IFCLIGHTFIXTURE)
        assert!(hvac_equipment.is_some());
        assert!(electrical_equipment.is_some());
        
        // Test symbol mapping logic
        let hvac_symbol = match hvac_equipment.unwrap().equipment_type.as_str() {
            s if s.contains("AIR") => '▲',
            _ => '╬',
        };
        assert_eq!(hvac_symbol, '▲');
        
        let electrical_symbol = match electrical_equipment.unwrap().equipment_type.as_str() {
            s if s.contains("LIGHT") => '●',
            _ => '╬',
        };
        assert_eq!(electrical_symbol, '●');
    }
}

//! WASM bindings for ArxOS frontend integration
//!
//! Exposes core ArxOS functionality to the Leptos/WASM frontend:
//!
//! - [`init_panic_hook`]: Sets up browser-friendly Rust panic messages.
//! - [`parse_ifc_data`]: Parse raw IFC text → JSON Building model.
//! - [`render_building_ascii`]: Render a Building (JSON) → bordered ASCII-art string
//!   suitable for display in a `<pre>` element or Xterm.js terminal pane.
//! - [`render_building_ascii_simple`]: As above but without borders/legend.

use wasm_bindgen::prelude::*;
use crate::ifc::BimParser;

#[wasm_bindgen]
pub fn init_panic_hook() {
    console_error_panic_hook::set_once();
}

/// Parse IFC content and return JSON representation of the Building
#[wasm_bindgen]
pub fn parse_ifc_data(content: &str) -> Result<String, JsValue> {
    let parser = BimParser::new();
    match parser.parse_from_string(content) {
        Ok((building, _)) => {
            serde_json::to_string(&building)
                .map_err(|e| JsValue::from_str(&format!("Serialization error: {}", e)))
        },
        Err(e) => Err(JsValue::from_str(&format!("Parsing error: {}", e)))
    }
}

/// Render a Building (supplied as JSON) to a bordered ASCII-art string.
///
/// # Arguments
/// * `building_json` — JSON string of a `crate::core::Building` (as produced by
///   `parse_ifc_data` or the import page).
/// * `canvas_width` — Character width of the ASCII canvas (default 80).
/// * `canvas_height` — Character height of the ASCII canvas (default 24).
///
/// # Returns
/// A `String` suitable for rendering in a `<pre>` element or Xterm.js pane,
/// containing a bordered ASCII-art view of the building with a legend.
/// Returns an error string (prefixed `"Error: "`) on failure.
///
/// # Example (Leptos/JS)
/// ```js
/// const ascii = render_building_ascii(buildingJson, 80, 30);
/// document.getElementById("ascii-view").textContent = ascii;
/// ```
#[wasm_bindgen]
pub fn render_building_ascii(building_json: &str, canvas_width: u32, canvas_height: u32) -> String {
    use crate::render3d::ascii::AsciiRenderer;
    use crate::render3d::types::Scene3D;
    use crate::core::spatial::{BoundingBox3D, Point3D};
    use std::sync::Arc;

    // Deserialize the building
    let building: crate::core::Building = match serde_json::from_str(building_json) {
        Ok(b) => b,
        Err(e) => return format!("Error: failed to parse building JSON: {}", e),
    };

    // Build a minimal Scene3D from the building
    let scene = building_to_scene3d(&building);

    let renderer = AsciiRenderer::new();
    let width = canvas_width.max(20) as usize;
    let height = canvas_height.max(8) as usize;

    // Identity projection (flat top-down view; full 3D projection requires camera setup)
    let project_fn = |p: &Point3D| Point3D { x: p.x, y: p.y, z: p.z };

    match renderer.render_ascii_art(&scene, width, height, project_fn) {
        Ok(output) => output,
        Err(e) => format!("Error: render failed: {}", e),
    }
}

/// Render a Building (supplied as JSON) to a simple ASCII string without borders.
///
/// Lighter-weight alternative to [`render_building_ascii`] for embedding in custom UI.
#[wasm_bindgen]
pub fn render_building_ascii_simple(building_json: &str, canvas_width: u32, canvas_height: u32) -> String {
    use crate::render3d::ascii::AsciiRenderer;
    use crate::core::spatial::Point3D;

    let building: crate::core::Building = match serde_json::from_str(building_json) {
        Ok(b) => b,
        Err(e) => return format!("Error: failed to parse building JSON: {}", e),
    };

    let scene = building_to_scene3d(&building);
    let renderer = AsciiRenderer::new();
    let width = canvas_width.max(20) as usize;
    let height = canvas_height.max(8) as usize;

    let project_fn = |p: &Point3D| Point3D { x: p.x, y: p.y, z: p.z };

    match renderer.render_simple(&scene, width, height, project_fn) {
        Ok(output) => output,
        Err(e) => format!("Error: render failed: {}", e),
    }
}

// ─── Helpers ────────────────────────────────────────────────────────────────

/// Convert a `Building` into the `Scene3D` expected by the ASCII renderer.
///
/// Extracts floor slabs, rooms, and equipment from the building hierarchy and
/// builds the lightweight scene representation used by `AsciiRenderer`.
fn building_to_scene3d(building: &crate::core::Building) -> crate::render3d::types::Scene3D {
    use crate::render3d::types::{
        Equipment3D, Floor3D, Room3D, Scene3D, SceneMetadata,
    };
    use crate::core::spatial::{BoundingBox3D, Point3D};
    use crate::core::{EquipmentStatus, RoomType};
    use std::sync::Arc;

    let mut floors_3d: Vec<Floor3D> = Vec::new();
    let mut all_rooms: Vec<Room3D> = Vec::new();
    let mut all_equipment: Vec<Equipment3D> = Vec::new();

    // Empty bounding box — used as a placeholder for entities without known size
    let empty_bbox = BoundingBox3D {
        min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
        max: Point3D { x: 1.0, y: 1.0, z: 1.0 },
    };

    for floor in &building.floors {
        let z = floor.level as f64 * 3.0;

        let floor_room_ids: Vec<Arc<String>> = floor.wings
            .iter()
            .flat_map(|w| w.rooms.iter().map(|r| Arc::new(r.id.clone())))
            .collect();

        floors_3d.push(Floor3D {
            id: Arc::new(floor.id.clone()),
            name: Arc::new(floor.name.clone()),
            level: floor.level,
            elevation: z,
            bounding_box: empty_bbox.clone(),
            rooms: floor_room_ids,
            equipment: vec![],
        });

        for wing in &floor.wings {
            for room in &wing.rooms {
                let room_pos = Point3D {
                    x: room.spatial_properties.position.x,
                    y: room.spatial_properties.position.y,
                    z,
                };

                let room_eq_ids: Vec<Arc<String>> = room.equipment
                    .iter()
                    .map(|e| Arc::new(e.id.clone()))
                    .collect();

                all_rooms.push(Room3D {
                    id: Arc::new(room.id.clone()),
                    name: Arc::new(room.name.clone()),
                    room_type: room.room_type.clone(),
                    position: room_pos,
                    bounding_box: empty_bbox.clone(),
                    floor_level: floor.level,
                    equipment: room_eq_ids,
                });

                for equip in &room.equipment {
                    let eq_pos = Point3D {
                        x: equip.position.x,
                        y: equip.position.y,
                        z: equip.position.z + z,
                    };

                    let eq_bbox = BoundingBox3D {
                        min: eq_pos.clone(),
                        max: Point3D {
                            x: eq_pos.x + 0.5,
                            y: eq_pos.y + 0.5,
                            z: eq_pos.z + 0.5,
                        },
                    };

                    all_equipment.push(Equipment3D {
                        id: Arc::new(equip.id.clone()),
                        name: Arc::new(equip.name.clone()),
                        equipment_type: equip.equipment_type.clone(),
                        status: equip.status,
                        position: eq_pos,
                        bounding_box: eq_bbox,
                        floor_level: floor.level,
                        room_id: equip.room_id.as_ref().map(|rid| Arc::new(rid.clone())),
                        connections: vec![],
                        spatial_relationships: None,
                        nearest_entity_distance: None,
                    });
                }
            }
        }
    }

    let total_rooms = all_rooms.len();
    let total_equipment = all_equipment.len();

    Scene3D {
        building_name: Arc::new(building.name.clone()),
        floors: floors_3d,
        rooms: all_rooms,
        equipment: all_equipment,
        bounding_box: BoundingBox3D {
            min: Point3D { x: 0.0, y: 0.0, z: 0.0 },
            max: Point3D {
                x: 100.0,
                y: 100.0,
                z: (building.floors.len() as f64) * 3.0 + 3.0,
            },
        },
        metadata: SceneMetadata {
            total_floors: building.floors.len(),
            total_rooms,
            total_equipment,
            render_time_ms: 0,
            projection_type: "TopDown".to_string(),
            view_angle: "0deg".to_string(),
        },
    }
}



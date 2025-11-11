use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// AR scan data representation for WebAssembly consumers.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct WasmArScanData {
    pub detected_equipment: Vec<WasmDetectedEquipment>,
    #[serde(default)]
    pub room_boundaries: WasmRoomBoundaries,
    pub device_type: Option<String>,
    pub app_version: Option<String>,
    pub scan_duration_ms: Option<u64>,
    pub point_count: Option<u64>,
    pub accuracy_estimate: Option<f64>,
    pub lighting_conditions: Option<String>,
    pub room_name: Option<String>,
    pub floor_level: Option<i32>,
}

/// Equipment detected during an AR scan.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct WasmDetectedEquipment {
    pub name: String,
    #[serde(rename = "type")]
    pub equipment_type: String,
    pub position: WasmPosition,
    pub confidence: f64,
    pub detection_method: Option<String>,
}

/// Cartesian position in meters.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WasmPosition {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

/// Structured representation of room boundaries.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct WasmRoomBoundaries {
    pub walls: Vec<WasmWall>,
    pub openings: Vec<WasmOpening>,
}

/// Wall segment with start/end points.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct WasmWall {
    pub start_point: WasmPosition,
    pub end_point: WasmPosition,
    pub height: f64,
    pub thickness: f64,
}

/// Door/window opening metadata.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct WasmOpening {
    pub position: WasmPosition,
    pub width: f64,
    pub height: f64,
    #[serde(rename = "type")]
    pub opening_type: String,
}

/// Equipment entry returned to the browser.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct WasmEquipmentInfo {
    pub id: String,
    pub name: String,
    #[serde(rename = "equipmentType")]
    pub equipment_type: String,
    pub status: String,
    pub position: WasmPosition,
    pub properties: HashMap<String, String>,
    pub address_path: String,
}

/// Mesh buffers for WebGL rendering generated from an AR scan.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct WasmMeshBuffers {
    /// Flattened XYZ positions for wall line segments (WebGL `LINES`).
    pub wall_positions: Vec<f32>,
    /// Flattened XYZ positions for equipment points (WebGL `POINTS`).
    pub equipment_positions: Vec<f32>,
    /// Flattened XYZ positions for ambient point-cloud proxy (optional fallback).
    pub point_cloud_positions: Vec<f32>,
    /// Bounding box minimum XYZ.
    pub bounds_min: [f32; 3],
    /// Bounding box maximum XYZ.
    pub bounds_max: [f32; 3],
}

/// Parse AR scan data from JSON.
#[cfg_attr(not(target_arch = "wasm32"), allow(dead_code))]
pub fn parse_ar_scan(json: &str) -> Result<WasmArScanData, serde_json::Error> {
    serde_json::from_str(json)
}

/// Convert parsed scan data into equipment summaries for UI display.
#[cfg_attr(not(target_arch = "wasm32"), allow(dead_code))]
pub fn extract_equipment_from_ar_scan(scan: &WasmArScanData) -> Vec<WasmEquipmentInfo> {
    scan.detected_equipment
        .iter()
        .map(|eq| {
            let mut props = HashMap::new();
            props.insert("confidence".to_string(), format!("{:.3}", eq.confidence));
            if let Some(ref method) = eq.detection_method {
                props.insert("detection_method".to_string(), method.clone());
            }

            WasmEquipmentInfo {
                id: eq.name.clone(),
                name: eq.name.clone(),
                equipment_type: eq.equipment_type.clone(),
                status: "Unknown".to_string(),
                position: WasmPosition {
                    x: eq.position.x,
                    y: eq.position.y,
                    z: eq.position.z,
                },
                properties: props,
                address_path: String::new(),
            }
        })
        .collect()
}

/// Convert scan data into WebGL-friendly mesh buffers.
#[cfg_attr(not(target_arch = "wasm32"), allow(dead_code))]
pub fn scan_to_mesh_buffers(scan: &WasmArScanData) -> WasmMeshBuffers {
    let mut wall_positions = Vec::with_capacity(scan.room_boundaries.walls.len() * 6);
    let mut equipment_positions = Vec::with_capacity(scan.detected_equipment.len() * 3);
    let mut bounds_min = [f32::MAX; 3];
    let mut bounds_max = [f32::MIN; 3];

    let mut update_bounds = |x: f32, y: f32, z: f32| {
        if x < bounds_min[0] {
            bounds_min[0] = x;
        }
        if y < bounds_min[1] {
            bounds_min[1] = y;
        }
        if z < bounds_min[2] {
            bounds_min[2] = z;
        }
        if x > bounds_max[0] {
            bounds_max[0] = x;
        }
        if y > bounds_max[1] {
            bounds_max[1] = y;
        }
        if z > bounds_max[2] {
            bounds_max[2] = z;
        }
    };

    for wall in &scan.room_boundaries.walls {
        let start = &wall.start_point;
        let end = &wall.end_point;
        let sx = start.x as f32;
        let sy = start.y as f32;
        let sz = start.z as f32;
        let ex = end.x as f32;
        let ey = end.y as f32;
        let ez = end.z as f32;

        wall_positions.extend_from_slice(&[sx, sy, sz, ex, ey, ez]);
        update_bounds(sx, sy, sz);
        update_bounds(ex, ey, ez);
    }

    for equipment in &scan.detected_equipment {
        let px = equipment.position.x as f32;
        let py = equipment.position.y as f32;
        let pz = equipment.position.z as f32;
        equipment_positions.extend_from_slice(&[px, py, pz]);
        update_bounds(px, py, pz);
    }

    if scan.room_boundaries.walls.is_empty() && scan.detected_equipment.is_empty() {
        bounds_min = [0.0; 3];
        bounds_max = [0.0; 3];
    }

    let point_cloud_positions = if !scan.detected_equipment.is_empty() {
        equipment_positions.clone()
    } else {
        Vec::new()
    };

    WasmMeshBuffers {
        wall_positions,
        equipment_positions,
        point_cloud_positions,
        bounds_min,
        bounds_max,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_sample_scan() {
        let json = r#"{"detectedEquipment": [], "roomBoundaries": {"walls": [], "openings": []}}"#;
        let parsed = parse_ar_scan(json).expect("valid json");
        assert!(parsed.detected_equipment.is_empty());
    }

    #[test]
    fn extract_equipment_properties() {
        let scan = WasmArScanData {
            detected_equipment: vec![WasmDetectedEquipment {
                name: "Unit-1".into(),
                equipment_type: "HVAC".into(),
                position: WasmPosition {
                    x: 1.0,
                    y: 2.0,
                    z: 3.0,
                },
                confidence: 0.9,
                detection_method: Some("Manual".into()),
            }],
            room_boundaries: WasmRoomBoundaries::default(),
            device_type: None,
            app_version: None,
            scan_duration_ms: None,
            point_count: None,
            accuracy_estimate: None,
            lighting_conditions: None,
            room_name: None,
            floor_level: None,
        };

        let equipment = extract_equipment_from_ar_scan(&scan);
        assert_eq!(equipment.len(), 1);
        assert_eq!(equipment[0].name, "Unit-1");
    }

    #[test]
    fn mesh_buffers_capture_bounds() {
        let scan = WasmArScanData {
            detected_equipment: vec![WasmDetectedEquipment {
                name: "Unit-1".into(),
                equipment_type: "HVAC".into(),
                position: WasmPosition {
                    x: 1.0,
                    y: 2.0,
                    z: 0.5,
                },
                confidence: 0.9,
                detection_method: None,
            }],
            room_boundaries: WasmRoomBoundaries {
                walls: vec![WasmWall {
                    start_point: WasmPosition {
                        x: 0.0,
                        y: 0.0,
                        z: 0.0,
                    },
                    end_point: WasmPosition {
                        x: 3.0,
                        y: 0.0,
                        z: 0.0,
                    },
                    height: 3.0,
                    thickness: 0.2,
                }],
                openings: vec![],
            },
            device_type: None,
            app_version: None,
            scan_duration_ms: None,
            point_count: None,
            accuracy_estimate: None,
            lighting_conditions: None,
            room_name: None,
            floor_level: None,
        };

        let buffers = scan_to_mesh_buffers(&scan);
        assert_eq!(buffers.wall_positions.len(), 6);
        assert_eq!(buffers.equipment_positions.len(), 3);
        assert!(buffers.bounds_max[0] >= 3.0);
        assert!(buffers.bounds_max[1] >= 2.0);
    }
}

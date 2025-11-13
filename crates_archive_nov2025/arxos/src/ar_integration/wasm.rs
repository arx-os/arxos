//! WASM/PWA-friendly helpers for AR scan data.
//!
//! This module replaces the legacy mobile FFI surface with pure Rust helpers that
//! can be reused from the upcoming WebAssembly frontend.  Functions here mirror the
//! JSON payloads produced by the retired native apps so existing datasets and tests
//! continue to work.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Parsed AR scan data emitted by the PWA (and legacy mobile clients).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WasmArScanData {
    #[serde(rename = "detectedEquipment", default)]
    pub detected_equipment: Vec<WasmDetectedEquipment>,
    #[serde(rename = "roomBoundaries", default)]
    pub room_boundaries: RoomBoundaries,
    #[serde(rename = "deviceType")]
    pub device_type: Option<String>,
    #[serde(rename = "appVersion")]
    pub app_version: Option<String>,
    #[serde(rename = "scanDurationMs")]
    pub scan_duration_ms: Option<u64>,
    #[serde(rename = "pointCount")]
    pub point_count: Option<u64>,
    #[serde(rename = "accuracyEstimate")]
    pub accuracy_estimate: Option<f64>,
    #[serde(rename = "lightingConditions")]
    pub lighting_conditions: Option<String>,
    #[serde(rename = "roomName")]
    pub room_name: Option<String>,
    #[serde(rename = "floorLevel")]
    pub floor_level: Option<i32>,
}

/// Equipment entry detected in an AR scan.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WasmDetectedEquipment {
    pub name: String,
    #[serde(rename = "type")]
    pub equipment_type: String,
    pub position: Position3D,
    pub confidence: f64,
    #[serde(rename = "detectionMethod")]
    pub detection_method: Option<String>,
}

/// Simplified equipment info extracted from scans for downstream workflows.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WasmEquipmentInfo {
    pub id: String,
    pub name: String,
    pub equipment_type: String,
    pub status: String,
    pub position: Position,
    pub properties: HashMap<String, String>,
    #[serde(rename = "addressPath")]
    pub address_path: String,
}

/// 3D position representation used in scan payloads.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, Default)]
pub struct Position3D {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

/// Position with coordinate-system metadata (used by extracted equipment).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Position {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    #[serde(rename = "coordinateSystem")]
    pub coordinate_system: String,
}

/// Room boundary information captured during the scan.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct RoomBoundaries {
    #[serde(default)]
    pub walls: Vec<Wall>,
    #[serde(default)]
    pub openings: Vec<Opening>,
}

/// Wall description within the scanned room.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Wall {
    #[serde(rename = "startPoint")]
    pub start_point: Position3D,
    #[serde(rename = "endPoint")]
    pub end_point: Position3D,
    pub height: f64,
    pub thickness: f64,
}

/// Door or window opening detected in the room.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Opening {
    pub position: Position3D,
    pub width: f64,
    pub height: f64,
    #[serde(rename = "type")]
    pub opening_type: String,
}

/// Parse AR scan JSON into a WASM-friendly data structure.
pub fn parse_ar_scan(json: &str) -> Result<WasmArScanData, serde_json::Error> {
    serde_json::from_str(json)
}

/// Convert parsed scan data into high-level equipment entries.
pub fn extract_equipment_from_ar_scan(scan: &WasmArScanData) -> Vec<WasmEquipmentInfo> {
    scan.detected_equipment
        .iter()
        .map(|detected| {
            let mut properties = HashMap::new();
            properties.insert("confidence".to_string(), detected.confidence.to_string());
            if let Some(method) = &detected.detection_method {
                properties.insert("detection_method".to_string(), method.clone());
            }

            WasmEquipmentInfo {
                id: detected.name.clone(),
                name: detected.name.clone(),
                equipment_type: detected.equipment_type.clone(),
                status: "Unknown".to_string(),
                position: Position {
                    x: detected.position.x,
                    y: detected.position.y,
                    z: detected.position.z,
                    coordinate_system: "world".to_string(),
                },
                properties,
                address_path: String::new(),
            }
        })
        .collect()
}

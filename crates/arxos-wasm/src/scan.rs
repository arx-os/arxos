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
}

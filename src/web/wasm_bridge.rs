//! WASM bindings for ArxOS frontend integration
//!
//! Exposes core ArxOS functionality to the Leptos/WASM frontend:
//!
//! - [`init_panic_hook`]: Sets up browser-friendly Rust panic messages.
//! - [`parse_ifc_data`]: Parse raw IFC text → JSON Building model.
//! - [`render_building_ascii`]: Render a Building (JSON) → bordered ASCII-art string
//!   suitable for display in a `<pre>` element or Xterm.js terminal pane.
//! - [`render_building_ascii_simple`]: As above but without borders/legend.

use crate::core::BuildingMetadata;
use crate::ifc::IFCProcessor;
use crate::ingest::{
    apply_text_to_sync_json, finalize_ingest, merge_sync_json, BuildingSyncEnvelope, IngestOptions,
    IngestSource, SyncSource, STORAGE_KEY_ACTIVE_BUILDING, STORAGE_KEY_LEGACY_BUILDING,
};
use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub fn init_panic_hook() {
    console_error_panic_hook::set_once();
}

/// localStorage key for the active building sync envelope.
#[wasm_bindgen]
pub fn storage_key_active_building() -> String {
    STORAGE_KEY_ACTIVE_BUILDING.to_string()
}

fn ifc_content_to_envelope(content: &str) -> Result<BuildingSyncEnvelope, JsValue> {
    let processor = IFCProcessor::new();
    let parsed = processor
        .parse_native_content(content, false)
        .map_err(|e| JsValue::from_str(&format!("Parsing error: {}", e)))?;

    let mut building = parsed.building;
    building.metadata = Some(BuildingMetadata {
        source_file: Some("wasm-upload.ifc".into()),
        parser_version: env!("CARGO_PKG_VERSION").to_string(),
        total_entities: parsed.stats.total_entities,
        spatial_entities: parsed.stats.spatial_entities,
        coordinate_system: "building_local".to_string(),
        units: "meters".to_string(),
        tags: vec!["ifc".to_string(), "wasm".to_string()],
        properties: Default::default(),
    });

    let mut result = finalize_ingest(
        building,
        IngestSource::Ifc,
        IngestOptions {
            validate: true,
            existing: None,
            policy: None,
        },
    );
    for w in parsed.report.warnings {
        result.report.warnings.push(w);
    }
    let mut env = BuildingSyncEnvelope::from_ingest(result);
    env.source = SyncSource::Wasm;
    Ok(env)
}

/// Parse IFC content via the **native** pipeline and return **Building** JSON
/// (backward compatible with earlier PWA code).
#[wasm_bindgen]
pub fn parse_ifc_data(content: &str) -> Result<String, JsValue> {
    let env = ifc_content_to_envelope(content)?;
    serde_json::to_string(&env.building)
        .map_err(|e| JsValue::from_str(&format!("Serialization error: {}", e)))
}

/// Parse IFC and return a full [`BuildingSyncEnvelope`] JSON (schema_version + report).
#[wasm_bindgen]
pub fn parse_ifc_data_with_report(content: &str) -> Result<String, JsValue> {
    let env = ifc_content_to_envelope(content)?;
    env.to_json()
        .map_err(|e| JsValue::from_str(&format!("Serialization error: {}", e)))
}

/// Merge two sync-envelope (or bare Building) JSON documents; returns envelope JSON.
#[wasm_bindgen]
pub fn merge_building_sync_json(
    existing_json: &str,
    incoming_json: &str,
) -> Result<String, JsValue> {
    merge_sync_json(existing_json, incoming_json).map_err(|e| JsValue::from_str(&e))
}

/// Apply a text/AR command script to a sync envelope JSON; returns updated envelope.
#[wasm_bindgen]
pub fn apply_text_script_json(envelope_json: &str, script: &str) -> Result<String, JsValue> {
    apply_text_to_sync_json(envelope_json, script).map_err(|e| JsValue::from_str(&e))
}

/// Extract Building JSON from an envelope (or pass through bare Building JSON).
#[wasm_bindgen]
pub fn building_json_from_envelope(json: &str) -> Result<String, JsValue> {
    let env = BuildingSyncEnvelope::from_json(json).map_err(|e| JsValue::from_str(&e))?;
    serde_json::to_string(&env.building)
        .map_err(|e| JsValue::from_str(&format!("Serialization error: {}", e)))
}

/// Persist envelope JSON to localStorage under the canonical key (and legacy key).
#[wasm_bindgen]
pub fn store_active_building(envelope_json: &str) -> Result<(), JsValue> {
    // Validate round-trip
    let env = BuildingSyncEnvelope::from_json(envelope_json).map_err(|e| JsValue::from_str(&e))?;
    let json = env
        .to_json()
        .map_err(|e| JsValue::from_str(&e.to_string()))?;
    let window = web_sys::window().ok_or_else(|| JsValue::from_str("no window"))?;
    let storage = window
        .local_storage()?
        .ok_or_else(|| JsValue::from_str("no localStorage"))?;
    storage
        .set_item(STORAGE_KEY_ACTIVE_BUILDING, &json)?;
    // Keep legacy key as bare building for older pages during migration
    if let Ok(bare) = serde_json::to_string(&env.building) {
        let _ = storage.set_item(STORAGE_KEY_LEGACY_BUILDING, &bare);
    }
    Ok(())
}

/// Load active building envelope from localStorage (canonical or legacy key).
#[wasm_bindgen]
pub fn load_active_building() -> Result<String, JsValue> {
    let window = web_sys::window().ok_or_else(|| JsValue::from_str("no window"))?;
    let storage = window
        .local_storage()?
        .ok_or_else(|| JsValue::from_str("no localStorage"))?;
    if let Ok(Some(json)) = storage.get_item(STORAGE_KEY_ACTIVE_BUILDING) {
        // Normalize
        let env = BuildingSyncEnvelope::from_json(&json).map_err(|e| JsValue::from_str(&e))?;
        return env.to_json().map_err(|e| JsValue::from_str(&e.to_string()));
    }
    if let Ok(Some(json)) = storage.get_item(STORAGE_KEY_LEGACY_BUILDING) {
        let env = BuildingSyncEnvelope::from_json(&json).map_err(|e| JsValue::from_str(&e))?;
        let out = env
            .to_json()
            .map_err(|e| JsValue::from_str(&e.to_string()))?;
        let _ = storage.set_item(STORAGE_KEY_ACTIVE_BUILDING, &out);
        return Ok(out);
    }
    Err(JsValue::from_str("no active building in storage"))
}

/// Render building hierarchy as plain text for the PWA "terminal" pane.
///
/// LiDAR point-cloud / Bevy visualization is deferred. This is a text tree only
/// (camera/AR capture remains a separate future path).
///
/// `canvas_width` / `canvas_height` are accepted for API stability but unused.
#[wasm_bindgen]
pub fn render_building_ascii(building_json: &str, _canvas_width: u32, _canvas_height: u32) -> String {
    building_hierarchy_text(building_json)
}

/// Lighter alias of [`render_building_ascii`] for embedding in custom UI.
#[wasm_bindgen]
pub fn render_building_ascii_simple(
    building_json: &str,
    canvas_width: u32,
    canvas_height: u32,
) -> String {
    render_building_ascii(building_json, canvas_width, canvas_height)
}

fn building_hierarchy_text(building_json: &str) -> String {
    let building: crate::core::Building = match serde_json::from_str(building_json) {
        Ok(b) => b,
        Err(e) => return format!("Error: failed to parse building JSON: {}", e),
    };

    let mut out = String::new();
    out.push_str(&format!("Building: {}\n", building.name));
    out.push_str(&format!("ID: {}\n", building.id));
    for floor in &building.floors {
        out.push_str(&format!("  Floor {} (level {})\n", floor.name, floor.level));
        for wing in &floor.wings {
            out.push_str(&format!("    Wing: {}\n", wing.name));
            for room in &wing.rooms {
                out.push_str(&format!("      Room: {}\n", room.name));
                let n = room.equipment.len();
                if n > 0 {
                    if n <= 5 {
                        for eq in &room.equipment {
                            out.push_str(&format!("        Equipment: {}\n", eq.name));
                        }
                    } else {
                        out.push_str(&format!("        Equipment: {} items\n", n));
                    }
                }
            }
        }
    }
    out
}

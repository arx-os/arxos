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

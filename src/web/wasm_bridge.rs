//! WASM bridge for ArxOS core functionality

use wasm_bindgen::prelude::*;

// TODO: Expose BimParser to WASM
// TODO: Convert Building to JSON for JavaScript interop

#[wasm_bindgen]
pub fn init_panic_hook() {
    console_error_panic_hook::set_once();
}

//! WebAssembly bindings for ArxOS.
//!
//! This crate exposes a small, browser-friendly surface that wraps core ArxOS
//! functionality. It is compiled to WebAssembly and consumed by the progressive
//! web app (PWA). Desktop and CLI builds should not depend on this crate.

#![allow(clippy::missing_errors_doc)]
#![allow(clippy::missing_panics_doc)]

use once_cell::sync::Lazy;
#[cfg(target_arch = "wasm32")]
use serde::Serialize;

static VERSION: Lazy<String> = Lazy::new(|| env!("CARGO_PKG_VERSION").to_string());

/// Initialize panic hooks or global state when running inside wasm32.
#[cfg(target_arch = "wasm32")]
fn init_once() {
    console_error_panic_hook::set_once();
}

mod geometry;
mod scan;

/// Exports intended for WebAssembly consumers.
#[cfg(target_arch = "wasm32")]
mod wasm_exports {
    use super::*;
    use crate::scan::{
        extract_equipment_from_ar_scan, parse_ar_scan as parse_scan_internal, scan_to_mesh_buffers,
    };
    use arx_command_catalog::{
        self, CommandAvailability as CatalogAvailability, CommandCategory as CatalogCategory,
    };
    use wasm_bindgen::prelude::*;

    #[wasm_bindgen(start)]
    pub fn start() {
        init_once();
    }

    #[wasm_bindgen]
    pub fn arxos_version() -> String {
        VERSION.clone()
    }

    #[wasm_bindgen]
    pub fn parse_ar_scan(json: &str) -> Result<JsValue, JsValue> {
        let data = parse_scan_internal(json)
            .map_err(|e| JsValue::from_str(&format!("Failed to parse AR scan JSON: {e}")))?;
        serde_wasm_bindgen::to_value(&data)
            .map_err(|e| JsValue::from_str(&format!("Failed to serialize AR scan data: {e}")))
    }

    #[wasm_bindgen]
    pub fn extract_equipment(json: &str) -> Result<JsValue, JsValue> {
        let scan = parse_scan_internal(json)
            .map_err(|e| JsValue::from_str(&format!("Failed to parse AR scan JSON: {e}")))?;
        let equipment = extract_equipment_from_ar_scan(&scan);
        serde_wasm_bindgen::to_value(&equipment)
            .map_err(|e| JsValue::from_str(&format!("Failed to serialize equipment list: {e}")))
    }

    #[wasm_bindgen]
    pub fn generate_scan_mesh(json: &str) -> Result<JsValue, JsValue> {
        let scan = parse_scan_internal(json)
            .map_err(|e| JsValue::from_str(&format!("Failed to parse AR scan JSON: {e}")))?;
        let buffers = scan_to_mesh_buffers(&scan);
        serde_wasm_bindgen::to_value(&buffers)
            .map_err(|e| JsValue::from_str(&format!("Failed to serialize mesh buffers: {e}")))
    }

    /// Validates that the provided JSON payload conforms to the expected schema.
    ///
    /// Returns `true` if the payload can be parsed into `WasmArScanData`,
    /// otherwise returns `false`.
    #[wasm_bindgen]
    pub fn validate_ar_scan(json: &str) -> bool {
        parse_scan_internal(json).is_ok()
    }

    #[derive(Serialize)]
    struct CategoryDto {
        slug: &'static str,
        label: &'static str,
    }

    #[derive(Serialize)]
    struct CommandEntryDto {
        name: &'static str,
        command: &'static str,
        description: &'static str,
        category: CategoryDto,
        shortcut: Option<&'static str>,
        tags: &'static [&'static str],
        availability: AvailabilityDto,
    }

    #[derive(Serialize)]
    struct AvailabilityDto {
        cli: bool,
        pwa: bool,
        agent: bool,
    }

    impl From<CatalogAvailability> for AvailabilityDto {
        fn from(value: CatalogAvailability) -> Self {
            Self {
                cli: value.cli,
                pwa: value.pwa,
                agent: value.agent,
            }
        }
    }

    const fn category_slug(category: CatalogCategory) -> &'static str {
        match category {
            CatalogCategory::Building => "building",
            CatalogCategory::Equipment => "equipment",
            CatalogCategory::Room => "room",
            CatalogCategory::Git => "git",
            CatalogCategory::ImportExport => "import-export",
            CatalogCategory::AR => "ar",
            CatalogCategory::Render => "render",
            CatalogCategory::Search => "search",
            CatalogCategory::Config => "config",
            CatalogCategory::Sensors => "sensors",
            CatalogCategory::Health => "health",
            CatalogCategory::Documentation => "documentation",
            CatalogCategory::Other => "other",
        }
    }

    #[wasm_bindgen]
    pub async fn command_palette() -> Result<JsValue, JsValue> {
        let entries: Vec<CommandEntryDto> = arx_command_catalog::all_commands()
            .iter()
            .map(|descriptor| CommandEntryDto {
                name: descriptor.name,
                command: descriptor.full_command,
                description: descriptor.description,
                category: CategoryDto {
                    slug: category_slug(descriptor.category),
                    label: descriptor.category.name(),
                },
                shortcut: descriptor.shortcut,
                tags: descriptor.tags,
                availability: descriptor.availability.into(),
            })
            .collect();

        serde_wasm_bindgen::to_value(&entries)
            .map_err(|e| JsValue::from_str(&format!("Failed to serialize command palette: {e}")))
    }

    #[wasm_bindgen]
    pub async fn command_categories() -> Result<JsValue, JsValue> {
        use CatalogCategory::*;
        let categories = [
            Building,
            Equipment,
            Room,
            Git,
            ImportExport,
            AR,
            Render,
            Search,
            Config,
            Sensors,
            Health,
            Documentation,
            Other,
        ];

        let payload: Vec<CategoryDto> = categories
            .iter()
            .map(|category| CategoryDto {
                slug: category_slug(*category),
                label: category.name(),
            })
            .collect();

        serde_wasm_bindgen::to_value(&payload)
            .map_err(|e| JsValue::from_str(&format!("Failed to serialize categories: {e}")))
    }

    #[wasm_bindgen]
    pub async fn command_details(name: String) -> Result<JsValue, JsValue> {
        let descriptor = arx_command_catalog::all_commands()
            .iter()
            .find(|entry| entry.name.eq_ignore_ascii_case(&name));

        match descriptor {
            Some(entry) => {
                let payload = CommandEntryDto {
                    name: entry.name,
                    command: entry.full_command,
                    description: entry.description,
                    category: CategoryDto {
                        slug: category_slug(entry.category),
                        label: entry.category.name(),
                    },
                    shortcut: entry.shortcut,
                    tags: entry.tags,
                    availability: entry.availability.into(),
                };
                serde_wasm_bindgen::to_value(&payload).map_err(|e| {
                    JsValue::from_str(&format!("Failed to serialize command details: {e}"))
                })
            }
            None => Err(JsValue::from_str("Command not found")),
        }
    }

    // ========================================
    // Geometry Module Exports (M03)
    // ========================================

    /// Get list of all buildings (summary information only)
    /// Returns: JSON array of BuildingSummary
    #[wasm_bindgen]
    pub async fn get_buildings() -> Result<JsValue, JsValue> {
        // M03: Return mock data for now (real data loading in M04 with agent)
        let summaries = vec![crate::geometry::create_mock_building_summary()];
        serde_wasm_bindgen::to_value(&summaries)
            .map_err(|e| JsValue::from_str(&format!("Failed to serialize buildings: {e}")))
    }

    /// Get full building data including all floors
    /// Returns: JSON Building
    #[wasm_bindgen]
    pub async fn get_building(_path: String) -> Result<JsValue, JsValue> {
        // M03: Return mock data for now (path parameter will be used in M04)
        let building = crate::geometry::create_mock_building();
        serde_wasm_bindgen::to_value(&building)
            .map_err(|e| JsValue::from_str(&format!("Failed to serialize building: {e}")))
    }

    /// Get specific floor with rooms and equipment
    /// Returns: JSON Floor
    #[wasm_bindgen]
    pub async fn get_floor(_building_path: String, floor_id: String) -> Result<JsValue, JsValue> {
        // M03: Return mock data based on floor_id
        let floor = match floor_id.as_str() {
            "floor-1" => crate::geometry::create_mock_floor("floor-1", "Ground Floor", 0),
            "floor-2" => crate::geometry::create_mock_floor("floor-2", "Second Floor", 1),
            "floor-3" => crate::geometry::create_mock_floor("floor-3", "Third Floor", 2),
            _ => return Err(JsValue::from_str(&format!("Floor not found: {floor_id}"))),
        };
        serde_wasm_bindgen::to_value(&floor)
            .map_err(|e| JsValue::from_str(&format!("Failed to serialize floor: {e}")))
    }

    /// Get bounding box for a floor (for viewport initialization)
    /// Returns: JSON BoundingBox
    #[wasm_bindgen]
    pub async fn get_floor_bounds(_building_path: String, floor_id: String) -> Result<JsValue, JsValue> {
        // M03: Return bounds from mock floor data
        let floor = match floor_id.as_str() {
            "floor-1" | "floor-2" | "floor-3" => {
                crate::geometry::create_mock_floor(&floor_id, "Floor", 0)
            }
            _ => return Err(JsValue::from_str(&format!("Floor not found: {floor_id}"))),
        };
        serde_wasm_bindgen::to_value(&floor.bounds)
            .map_err(|e| JsValue::from_str(&format!("Failed to serialize floor bounds: {e}")))
    }
}

/// Re-export wasm bindings when compiling for wasm32.
#[cfg(target_arch = "wasm32")]
pub use wasm_exports::*;

/// Placeholder exports for non-wasm builds so the crate still compiles during
/// host checks. These functions should never be invoked outside of tests.
#[cfg(not(target_arch = "wasm32"))]
pub fn arxos_version() -> String {
    VERSION.clone()
}

#[cfg(test)]
mod tests {
    #[test]
    fn version_constant_exists() {
        assert!(!super::arxos_version().is_empty());
    }
}

#[cfg(target_arch = "wasm32")]
#[cfg(test)]
mod wasm_tests {
    use super::*;
    use js_sys::Array;
    use wasm_bindgen::{JsCast, JsValue};
    use wasm_bindgen_test::*;

    wasm_bindgen_test_configure!(run_in_browser);

    #[wasm_bindgen_test]
    fn parse_and_extract_equipment() {
        let json = r#"
        {
            "detectedEquipment": [
                {
                    "name": "Unit-1",
                    "type": "HVAC",
                    "position": {"x": 1.0, "y": 2.0, "z": 3.0},
                    "confidence": 0.9,
                    "detectionMethod": "Manual"
                }
            ],
            "roomBoundaries": {"walls": [], "openings": []}
        }
        "#;

        let parsed = parse_ar_scan(json).unwrap();
        assert!(parsed.is_object());

        let equipment = extract_equipment(json).unwrap();
        let array: Array = equipment.dyn_into::<Array>().unwrap();
        assert_eq!(array.length(), 1);
    }
}

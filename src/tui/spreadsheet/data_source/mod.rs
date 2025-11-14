//! Data source module for spreadsheet
//!
//! This module provides trait definitions and implementations for
//! converting building data to spreadsheet format.
//!
//! # Module Structure
//!
//! - `trait_def` - Core SpreadsheetDataSource trait
//! - `equipment_source` - Equipment data implementation
//! - `room_source` - Room data implementation
//! - `sensor_source` - Sensor data implementation (read-only)
//!
//! # Examples
//!
//! ```ignore
//! use crate::tui::spreadsheet::data_source::{EquipmentDataSource, SpreadsheetDataSource};
//! use crate::yaml::BuildingData;
//!
//! let building_data = load_building_data()?;
//! let mut data_source = EquipmentDataSource::new(building_data, "my-building".to_string());
//!
//! // Access data via trait methods
//! let row_count = data_source.row_count();
//! let cell_value = data_source.get_cell(0, 0)?;
//! ```

pub mod equipment_source;
pub mod room_source;
pub mod sensor_source;
#[path = "trait.rs"]
pub mod trait_def;

// Re-export main types for convenience
pub use trait_def::SpreadsheetDataSource;

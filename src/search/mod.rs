//! Search and Filter module for ArxOS
//!
//! This module provides powerful search and filtering capabilities for building data,
//! including equipment, rooms, and buildings. It supports fuzzy matching, regex patterns,
//! multi-field search, and advanced filtering with real-time highlighting.
//!
//! # Features
//!
//! - **Multi-field Search**: Search across equipment names, types, system types, and universal paths
//! - **Fuzzy Matching**: Levenshtein distance algorithm for typo tolerance
//! - **Regex Support**: Full regex pattern matching across all fields
//! - **Advanced Filtering**: Filter by equipment type, status, floor, room, building
//! - **Real-time Highlighting**: Highlight matching text in search results
//! - **Multiple Output Formats**: Table, JSON, and YAML output formats
//! - **Performance Optimized**: Efficient search with result caching
//!
//! # Examples
//!
//! ## Basic Search
//! ```rust
//! use arxos::search::{SearchEngine, SearchConfig, OutputFormat};
//! use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
//! use chrono::Utc;
//!
//! // Create sample building data
//! let building_data = BuildingData {
//!     building: BuildingInfo {
//!         id: "test-001".to_string(),
//!         name: "Test Building".to_string(),
//!         description: Some("Test building for examples".to_string()),
//!         created_at: Utc::now(),
//!         updated_at: Utc::now(),
//!         version: "1.0".to_string(),
//!         global_bounding_box: None,
//!     },
//!     metadata: BuildingMetadata {
//!         source_file: None,
//!         parser_version: "1.0".to_string(),
//!         total_entities: 0,
//!         spatial_entities: 0,
//!         coordinate_system: "Cartesian".to_string(),
//!         units: "meters".to_string(),
//!         tags: vec![],
//!     },
//!     floors: vec![],
//!     coordinate_systems: vec![],
//! };
//!
//! let mut search_engine = SearchEngine::new(&building_data);
//!
//! let config = SearchConfig {
//!     query: "HVAC".to_string(),
//!     search_equipment: true,
//!     search_rooms: false,
//!     search_buildings: false,
//!     case_sensitive: false,
//!     use_regex: false,
//!     limit: 10,
//!     verbose: true,
//! };
//!
//! let results = search_engine.search(&config).unwrap();
//! println!("Found {} results", results.len());
//! ```
//!
//! ## Advanced Filtering
//! ```rust
//! use arxos::search::{SearchEngine, FilterConfig, OutputFormat};
//! use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
//! use chrono::Utc;
//!
//! // Create sample building data
//! let building_data = BuildingData {
//!     building: BuildingInfo {
//!         id: "test-001".to_string(),
//!         name: "Test Building".to_string(),
//!         description: Some("Test building for examples".to_string()),
//!         created_at: Utc::now(),
//!         updated_at: Utc::now(),
//!         version: "1.0".to_string(),
//!         global_bounding_box: None,
//!     },
//!     metadata: BuildingMetadata {
//!         source_file: None,
//!         parser_version: "1.0".to_string(),
//!         total_entities: 0,
//!         spatial_entities: 0,
//!         coordinate_system: "Cartesian".to_string(),
//!         units: "meters".to_string(),
//!         tags: vec![],
//!     },
//!     floors: vec![],
//!     coordinate_systems: vec![],
//! };
//!
//! let search_engine = SearchEngine::new(&building_data);
//!
//! let filter_config = FilterConfig {
//!     equipment_type: Some("HVAC".to_string()),
//!     status: Some("Critical".to_string()),
//!     floor: Some(1),
//!     room: None,
//!     building: None,
//!     critical_only: false,
//!     healthy_only: false,
//!     alerts_only: false,
//!     format: OutputFormat::Table,
//!     limit: 10,
//! };
//!
//! let results = search_engine.filter(&filter_config).unwrap();
//! ```
//!
//! ## Regex Search
//! ```rust
//! use arxos::search::{SearchEngine, SearchConfig};
//! use arxos::yaml::{BuildingData, BuildingInfo, BuildingMetadata};
//! use chrono::Utc;
//!
//! // Create sample building data
//! let building_data = BuildingData {
//!     building: BuildingInfo {
//!         id: "test-001".to_string(),
//!         name: "Test Building".to_string(),
//!         description: Some("Test building for examples".to_string()),
//!         created_at: Utc::now(),
//!         updated_at: Utc::now(),
//!         version: "1.0".to_string(),
//!         global_bounding_box: None,
//!     },
//!     metadata: BuildingMetadata {
//!         source_file: None,
//!         parser_version: "1.0".to_string(),
//!         total_entities: 0,
//!         spatial_entities: 0,
//!         coordinate_system: "Cartesian".to_string(),
//!         units: "meters".to_string(),
//!         tags: vec![],
//!     },
//!     floors: vec![],
//!     coordinate_systems: vec![],
//! };
//!
//! let search_engine = SearchEngine::new(&building_data);
//!
//! let config = SearchConfig {
//!     query: r"VAV.*Unit".to_string(),
//!     search_equipment: true,
//!     search_rooms: false,
//!     search_buildings: false,
//!     case_sensitive: false,
//!     use_regex: true,
//!     limit: 10,
//!     verbose: true,
//! };
//!
//! let results = search_engine.search(&config).unwrap();
//! ```

// Core modules
mod types;
mod engine;
mod formatter;

// Re-export public types and functions
pub use types::{SearchConfig, FilterConfig, OutputFormat, SearchResult};
pub use engine::SearchEngine;
pub use formatter::{format_search_results, format_search_results_with_highlight};

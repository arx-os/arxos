//! Type definitions for search functionality

use serde::{Deserialize, Serialize};

/// Search configuration for building data
#[derive(Debug, Clone)]
pub struct SearchConfig {
    pub query: String,
    pub search_equipment: bool,
    pub search_rooms: bool,
    pub search_buildings: bool,
    pub case_sensitive: bool,
    pub use_regex: bool,
    pub limit: usize,
    pub verbose: bool,
}

/// Filter configuration for building data
#[derive(Debug, Clone)]
pub struct FilterConfig {
    pub equipment_type: Option<String>,
    pub status: Option<String>,
    pub floor: Option<i32>,
    pub room: Option<String>,
    pub building: Option<String>,
    pub critical_only: bool,
    pub healthy_only: bool,
    pub alerts_only: bool,
    pub format: OutputFormat,
    pub limit: usize,
}

/// Output format for search and filter results
#[derive(Debug, Clone, PartialEq)]
pub enum OutputFormat {
    Table,
    Json,
    Yaml,
}

impl From<String> for OutputFormat {
    fn from(s: String) -> Self {
        match s.to_lowercase().as_str() {
            "json" => OutputFormat::Json,
            "yaml" => OutputFormat::Yaml,
            _ => OutputFormat::Table,
        }
    }
}

/// Search result containing matched data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    pub item_type: String, // "equipment", "room", "building"
    pub name: String,
    pub path: String,
    pub building: Option<String>,
    pub floor: Option<i32>,
    pub room: Option<String>,
    pub equipment_type: Option<String>,
    pub status: Option<String>,
    pub description: Option<String>,
    pub match_score: f64,
}

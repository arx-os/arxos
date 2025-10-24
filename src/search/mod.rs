//! Search and Filter module for ArxOS
//!
//! This module provides powerful search and filtering capabilities for building data,
//! including equipment, rooms, and buildings.

use crate::core::Building;
use crate::yaml::{BuildingData, RoomData, EquipmentData};
use regex::Regex;
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

/// Search engine for building data
pub struct SearchEngine {
    pub buildings: Vec<Building>,
    pub equipment: Vec<EquipmentData>,
    pub rooms: Vec<RoomData>,
}

impl SearchEngine {
    /// Create a new search engine with building data
    pub fn new(building_data: &BuildingData) -> Self {
        let mut equipment = Vec::new();
        let mut rooms = Vec::new();
        
        // Extract equipment and rooms from building data
        for floor in &building_data.floors {
            for room in &floor.rooms {
                rooms.push(room.clone());
            }
            equipment.extend(floor.equipment.clone());
        }
        
        // Create a Building struct from BuildingInfo
        let building = Building {
            id: building_data.building.id.clone(),
            name: building_data.building.name.clone(),
            path: format!("/{}", building_data.building.name),
            created_at: building_data.building.created_at,
            updated_at: building_data.building.updated_at,
            floors: Vec::new(), // We'll extract this from floors data
            equipment: Vec::new(),
        };
        
        Self {
            buildings: vec![building],
            equipment,
            rooms,
        }
    }
    
    /// Search building data with the given configuration
    pub fn search(&self, config: &SearchConfig) -> Result<Vec<SearchResult>, Box<dyn std::error::Error>> {
        let mut results = Vec::new();
        
        // Compile regex if needed
        let regex_pattern = if config.use_regex {
            Some(Regex::new(&config.query)?)
        } else {
            None
        };
        
        // Search buildings
        if config.search_buildings {
            for building in &self.buildings {
                if self.matches_building(building, &config.query, &regex_pattern, config.case_sensitive) {
                    results.push(SearchResult {
                        item_type: "building".to_string(),
                        name: building.name.clone(),
                        path: building.path.clone(),
                        building: Some(building.name.clone()),
                        floor: None,
                        room: None,
                        equipment_type: None,
                        status: None,
                        description: Some(format!("Building with {} floors", building.floors.len())),
                        match_score: self.calculate_match_score(&building.name, &config.query),
                    });
                }
            }
        }
        
        // Search rooms
        if config.search_rooms {
            for room in &self.rooms {
                if self.matches_room(room, &config.query, &regex_pattern, config.case_sensitive) {
                    results.push(SearchResult {
                        item_type: "room".to_string(),
                        name: room.name.clone(),
                        path: format!("/room/{}", room.id),
                        building: Some(self.buildings[0].name.clone()),
                        floor: None, // We'll need to determine this from the data structure
                        room: Some(room.name.clone()),
                        equipment_type: None,
                        status: None,
                        description: Some(format!("Room type: {}", room.room_type)),
                        match_score: self.calculate_match_score(&room.name, &config.query),
                    });
                }
            }
        }
        
        // Search equipment
        if config.search_equipment {
            for equipment in &self.equipment {
                if self.matches_equipment(equipment, &config.query, &regex_pattern, config.case_sensitive) {
                    results.push(SearchResult {
                        item_type: "equipment".to_string(),
                        name: equipment.name.clone(),
                        path: equipment.universal_path.clone(),
                        building: Some(self.buildings[0].name.clone()),
                        floor: None, // We'll need to determine this from the data structure
                        room: None, // EquipmentData doesn't have room_id
                        equipment_type: Some(equipment.equipment_type.clone()),
                        status: Some(format!("{:?}", equipment.status)),
                        description: Some(format!("{} equipment", equipment.equipment_type)),
                        match_score: self.calculate_match_score(&equipment.name, &config.query),
                    });
                }
            }
        }
        
        // Sort by match score (highest first) and apply limit
        results.sort_by(|a, b| b.match_score.partial_cmp(&a.match_score).unwrap());
        results.truncate(config.limit);
        
        Ok(results)
    }
    
    /// Filter building data with the given configuration
    pub fn filter(&self, config: &FilterConfig) -> Result<Vec<SearchResult>, Box<dyn std::error::Error>> {
        let mut results = Vec::new();
        
        for equipment in &self.equipment {
            if self.matches_filter(equipment, config) {
                results.push(SearchResult {
                    item_type: "equipment".to_string(),
                    name: equipment.name.clone(),
                    path: equipment.universal_path.clone(),
                    building: Some(self.buildings[0].name.clone()),
                    floor: None, // We'll need to determine this from the data structure
                    room: None, // EquipmentData doesn't have room_id
                    equipment_type: Some(equipment.equipment_type.clone()),
                    status: Some(format!("{:?}", equipment.status)),
                    description: Some(format!("{} equipment", equipment.equipment_type)),
                    match_score: 1.0, // All filtered results have equal relevance
                });
            }
        }
        
        // Apply limit
        results.truncate(config.limit);
        
        Ok(results)
    }
    
    /// Check if a building matches the search query
    fn matches_building(&self, building: &Building, query: &str, regex: &Option<Regex>, case_sensitive: bool) -> bool {
        let search_text = if case_sensitive {
            building.name.clone()
        } else {
            building.name.to_lowercase()
        };
        
        let search_query = if case_sensitive {
            query.to_string()
        } else {
            query.to_lowercase()
        };
        
        if let Some(regex) = regex {
            regex.is_match(&search_text)
        } else {
            search_text.contains(&search_query)
        }
    }
    
    /// Check if a room matches the search query
    fn matches_room(&self, room: &RoomData, query: &str, regex: &Option<Regex>, case_sensitive: bool) -> bool {
        let search_text = if case_sensitive {
            room.name.clone()
        } else {
            room.name.to_lowercase()
        };
        
        let search_query = if case_sensitive {
            query.to_string()
        } else {
            query.to_lowercase()
        };
        
        if let Some(regex) = regex {
            regex.is_match(&search_text)
        } else {
            search_text.contains(&search_query)
        }
    }
    
    /// Check if equipment matches the search query
    fn matches_equipment(&self, equipment: &EquipmentData, query: &str, regex: &Option<Regex>, case_sensitive: bool) -> bool {
        let search_text = if case_sensitive {
            equipment.name.clone()
        } else {
            equipment.name.to_lowercase()
        };
        
        let search_query = if case_sensitive {
            query.to_string()
        } else {
            query.to_lowercase()
        };
        
        if let Some(regex) = regex {
            regex.is_match(&search_text)
        } else {
            search_text.contains(&search_query)
        }
    }
    
    /// Check if equipment matches the filter criteria
    fn matches_filter(&self, equipment: &EquipmentData, config: &FilterConfig) -> bool {
        // Equipment type filter
        if let Some(ref equipment_type) = config.equipment_type {
            if !equipment.equipment_type.to_lowercase().contains(&equipment_type.to_lowercase()) {
                return false;
            }
        }
        
        // Status filter
        if let Some(ref status) = config.status {
            let status_str = format!("{:?}", equipment.status).to_lowercase();
            if !status_str.contains(&status.to_lowercase()) {
                return false;
            }
        }
        
        // Floor filter - we'll skip this for now since we don't have floor info directly
        // if let Some(floor) = config.floor {
        //     if equipment.floor != floor {
        //         return false;
        //     }
        // }
        
        // Room filter - we'll skip this for now since EquipmentData doesn't have room_id
        // if let Some(ref room) = config.room {
        //     if let Some(ref equipment_room) = equipment.room_id {
        //         if !equipment_room.to_lowercase().contains(&room.to_lowercase()) {
        //             return false;
        //         }
        //     } else {
        //         return false;
        //     }
        // }
        
        // Building filter - we'll skip this for now since we don't have building info directly
        // if let Some(ref building) = config.building {
        //     if let Some(ref equipment_building) = equipment.building {
        //         if !equipment_building.eq_ignore_ascii_case(building) {
        //             return false;
        //         }
        //     } else {
        //         return false;
        //     }
        // }
        
        // Critical only filter
        if config.critical_only {
            let status_str = format!("{:?}", equipment.status).to_lowercase();
            if !status_str.contains("critical") {
                return false;
            }
        }
        
        // Healthy only filter
        if config.healthy_only {
            let status_str = format!("{:?}", equipment.status).to_lowercase();
            if !status_str.contains("healthy") {
                return false;
            }
        }
        
        // Alerts only filter
        if config.alerts_only {
            let status_str = format!("{:?}", equipment.status).to_lowercase();
            if status_str.contains("healthy") {
                return false;
            }
        }
        
        true
    }
    
    /// Calculate match score for search results
    fn calculate_match_score(&self, text: &str, query: &str) -> f64 {
        let text_lower = text.to_lowercase();
        let query_lower = query.to_lowercase();
        
        // Exact match gets highest score
        if text_lower == query_lower {
            return 1.0;
        }
        
        // Starts with query gets high score
        if text_lower.starts_with(&query_lower) {
            return 0.9;
        }
        
        // Contains query gets medium score
        if text_lower.contains(&query_lower) {
            return 0.7;
        }
        
        // Partial match gets lower score
        let query_chars: Vec<char> = query_lower.chars().collect();
        let text_chars: Vec<char> = text_lower.chars().collect();
        
        let mut matches = 0;
        let mut query_idx = 0;
        
        for &text_char in &text_chars {
            if query_idx < query_chars.len() && text_char == query_chars[query_idx] {
                matches += 1;
                query_idx += 1;
            }
        }
        
        if matches > 0 {
            matches as f64 / query_chars.len() as f64 * 0.5
        } else {
            0.0
        }
    }
}

/// Format search results for display
pub fn format_search_results(results: &[SearchResult], format: &OutputFormat, verbose: bool) -> String {
    match format {
        OutputFormat::Table => format_table_results(results, verbose),
        OutputFormat::Json => serde_json::to_string_pretty(results).unwrap_or_else(|_| "[]".to_string()),
        OutputFormat::Yaml => serde_yaml::to_string(results).unwrap_or_else(|_| "[]".to_string()),
    }
}

/// Format results as a table
fn format_table_results(results: &[SearchResult], verbose: bool) -> String {
    if results.is_empty() {
        return "No results found.".to_string();
    }
    
    let mut output = String::new();
    
    if verbose {
        // Detailed table format
        output.push_str(&format!("{:<12} {:<20} {:<30} {:<15} {:<10} {:<15} {:<10}\n", 
            "Type", "Name", "Path", "Building", "Floor", "Room", "Status"));
        output.push_str(&format!("{:-<12} {:-<20} {:-<30} {:-<15} {:-<10} {:-<15} {:-<10}\n", 
            "", "", "", "", "", "", ""));
        
        for result in results {
            output.push_str(&format!("{:<12} {:<20} {:<30} {:<15} {:<10} {:<15} {:<10}\n",
                result.item_type,
                result.name,
                result.path,
                result.building.as_deref().unwrap_or("-"),
                result.floor.map(|f| f.to_string()).unwrap_or("-".to_string()),
                result.room.as_deref().unwrap_or("-"),
                result.status.as_deref().unwrap_or("-")
            ));
        }
    } else {
        // Simple table format
        output.push_str(&format!("{:<12} {:<20} {:<30}\n", "Type", "Name", "Path"));
        output.push_str(&format!("{:-<12} {:-<20} {:-<30}\n", "", "", ""));
        
        for result in results {
            output.push_str(&format!("{:<12} {:<20} {:<30}\n",
                result.item_type,
                result.name,
                result.path
            ));
        }
    }
    
    output.push_str(&format!("\nFound {} results.\n", results.len()));
    output
}

//! Search engine implementation

use super::types::{SearchConfig, FilterConfig, SearchResult};
use crate::core::Building;
use crate::yaml::{BuildingData, RoomData, EquipmentData};
use regex::Regex;

/// Search engine for building data with advanced filtering and fuzzy matching capabilities.
///
/// The `SearchEngine` provides comprehensive search and filtering functionality for building data,
/// including equipment, rooms, and buildings. It supports multiple search modes, fuzzy matching,
/// regex patterns, and real-time result highlighting.
pub struct SearchEngine {
    /// Building data to search through
    pub buildings: Vec<Building>,
    /// Equipment data for searching
    pub equipment: Vec<EquipmentData>,
    /// Room data for searching
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
    
    /// Search building data with the given configuration.
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
                    let (floor, room) = self.extract_location_from_path(&equipment.universal_path);
                    results.push(SearchResult {
                        item_type: "equipment".to_string(),
                        name: equipment.name.clone(),
                        path: equipment.universal_path.clone(),
                        building: Some(self.buildings[0].name.clone()),
                        floor,
                        room,
                        equipment_type: Some(equipment.equipment_type.clone()),
                        status: Some(format!("{:?}", equipment.status)),
                        description: Some(format!("{} equipment", equipment.system_type)),
                        match_score: self.calculate_match_score(&equipment.name, &config.query),
                    });
                }
            }
        }
        
        // Sort by match score (highest first) and apply limit
        results.sort_by(|a, b| {
            b.match_score.partial_cmp(&a.match_score)
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        results.truncate(config.limit);
        
        Ok(results)
    }
    
    /// Filter building data with the given configuration
    pub fn filter(&self, config: &FilterConfig) -> Result<Vec<SearchResult>, Box<dyn std::error::Error>> {
        let mut results = Vec::new();
        
        for equipment in &self.equipment {
            if self.matches_filter(equipment, config) {
                let (floor, room) = self.extract_location_from_path(&equipment.universal_path);
                results.push(SearchResult {
                    item_type: "equipment".to_string(),
                    name: equipment.name.clone(),
                    path: equipment.universal_path.clone(),
                    building: Some(self.buildings[0].name.clone()),
                    floor,
                    room,
                    equipment_type: Some(equipment.equipment_type.clone()),
                    status: Some(format!("{:?}", equipment.status)),
                    description: Some(format!("{} equipment", equipment.system_type)),
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
        if let Some(regex) = regex {
            // For regex, use the original text without case conversion
            regex.is_match(&building.name)
        } else {
            // For regular search, apply case sensitivity
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
            
            search_text.contains(&search_query)
        }
    }
    
    /// Check if a room matches the search query
    fn matches_room(&self, room: &RoomData, query: &str, regex: &Option<Regex>, case_sensitive: bool) -> bool {
        if let Some(regex) = regex {
            // For regex, use the original text without case conversion
            regex.is_match(&room.name)
        } else {
            // For regular search, apply case sensitivity
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
            
            search_text.contains(&search_query)
        }
    }
    
    /// Check if equipment matches the search query (enhanced multi-field search)
    fn matches_equipment(&self, equipment: &EquipmentData, query: &str, regex: &Option<Regex>, case_sensitive: bool) -> bool {
        if let Some(regex) = regex {
            // For regex, search across multiple fields
            regex.is_match(&equipment.name) ||
            regex.is_match(&equipment.equipment_type) ||
            regex.is_match(&equipment.system_type) ||
            regex.is_match(&equipment.universal_path)
        } else {
            // For regular search, search across multiple fields
            let search_query = if case_sensitive {
                query.to_string()
            } else {
                query.to_lowercase()
            };
            
            let name_match = if case_sensitive {
                equipment.name.contains(&search_query)
            } else {
                equipment.name.to_lowercase().contains(&search_query)
            };
            
            let type_match = if case_sensitive {
                equipment.equipment_type.contains(&search_query) ||
                equipment.system_type.contains(&search_query)
            } else {
                equipment.equipment_type.to_lowercase().contains(&search_query) ||
                equipment.system_type.to_lowercase().contains(&search_query)
            };
            
            let path_match = if case_sensitive {
                equipment.universal_path.contains(&search_query)
            } else {
                equipment.universal_path.to_lowercase().contains(&search_query)
            };
            
            name_match || type_match || path_match
        }
    }
    
    /// Check if equipment matches the filter criteria
    fn matches_filter(&self, equipment: &EquipmentData, config: &FilterConfig) -> bool {
        // Equipment type filter - check both equipment_type and system_type
        if let Some(ref equipment_type) = config.equipment_type {
            let search_type = equipment_type.to_lowercase();
            let eq_type = equipment.equipment_type.to_lowercase();
            let sys_type = equipment.system_type.to_lowercase();
            
            if !eq_type.contains(&search_type) && !sys_type.contains(&search_type) {
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
        
        // Floor filter
        if let Some(floor) = config.floor {
            let (equipment_floor, _) = self.extract_location_from_path(&equipment.universal_path);
            if equipment_floor != Some(floor) {
                return false;
            }
        }
        
        // Room filter
        if let Some(ref room) = config.room {
            let (_, equipment_room) = self.extract_location_from_path(&equipment.universal_path);
            if let Some(ref eq_room) = equipment_room {
                if !eq_room.to_lowercase().contains(&room.to_lowercase()) {
                    return false;
                }
            } else {
                return false;
            }
        }
        
        // Building filter
        if let Some(ref building) = config.building {
            if !self.buildings[0].name.to_lowercase().contains(&building.to_lowercase()) {
                return false;
            }
        }
        
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
    
    /// Calculate match score for search results with fuzzy matching
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
        
        // Contains query gets medium-high score
        if text_lower.contains(&query_lower) {
            return 0.8;
        }
        
        // Fuzzy matching using edit distance
        let fuzzy_score = self.calculate_fuzzy_score(&text_lower, &query_lower);
        if fuzzy_score > 0.0 {
            return fuzzy_score;
        }
        
        // Partial character matching
        let partial_score = self.calculate_partial_score(&text_lower, &query_lower);
        if partial_score > 0.0 {
            return partial_score * 0.3; // Lower weight for partial matches
        }
        
        0.0
    }
    
    /// Calculate fuzzy matching score using edit distance
    fn calculate_fuzzy_score(&self, text: &str, query: &str) -> f64 {
        if query.len() < 3 {
            return 0.0; // Skip fuzzy matching for very short queries
        }
        
        let edit_distance = self.levenshtein_distance(text, query);
        let max_len = text.len().max(query.len()) as f64;
        
        if max_len == 0.0 {
            return 0.0;
        }
        
        let similarity = 1.0 - (edit_distance as f64 / max_len);
        
        // Only return fuzzy score if similarity is reasonably high
        if similarity > 0.6 {
            similarity * 0.6 // Cap fuzzy score at 0.6
        } else {
            0.0
        }
    }
    
    /// Calculate Levenshtein distance between two strings
    fn levenshtein_distance(&self, s1: &str, s2: &str) -> usize {
        let s1_chars: Vec<char> = s1.chars().collect();
        let s2_chars: Vec<char> = s2.chars().collect();
        
        let s1_len = s1_chars.len();
        let s2_len = s2_chars.len();
        
        if s1_len == 0 {
            return s2_len;
        }
        if s2_len == 0 {
            return s1_len;
        }
        
        let mut matrix = vec![vec![0; s2_len + 1]; s1_len + 1];
        
        for i in 0..=s1_len {
            matrix[i][0] = i;
        }
        
        for j in 0..=s2_len {
            matrix[0][j] = j;
        }
        
        for i in 1..=s1_len {
            for j in 1..=s2_len {
                let cost = if s1_chars[i - 1] == s2_chars[j - 1] { 0 } else { 1 };
                matrix[i][j] = (matrix[i - 1][j] + 1)
                    .min(matrix[i][j - 1] + 1)
                    .min(matrix[i - 1][j - 1] + cost);
            }
        }
        
        matrix[s1_len][s2_len]
    }
    
    /// Calculate partial character matching score
    fn calculate_partial_score(&self, text: &str, query: &str) -> f64 {
        let query_chars: Vec<char> = query.chars().collect();
        let text_chars: Vec<char> = text.chars().collect();
        
        let mut matches = 0;
        let mut query_idx = 0;
        
        for &text_char in &text_chars {
            if query_idx < query_chars.len() && text_char == query_chars[query_idx] {
                matches += 1;
                query_idx += 1;
            }
        }
        
        if matches > 0 {
            matches as f64 / query_chars.len() as f64
        } else {
            0.0
        }
    }
    
    /// Extract floor and room information from universal path
    fn extract_location_from_path(&self, path: &str) -> (Option<i32>, Option<String>) {
        // Parse universal path: /BUILDING/{building}/FLOOR/{floor}/ROOM/{room}/{system}/{equipment}
        // or: /BUILDING/{building}/FLOOR/{floor}/{system}/{equipment}
        
        let parts: Vec<&str> = path.split('/').collect();
        
        let mut floor: Option<i32> = None;
        let mut room: Option<String> = None;
        
        for (i, part) in parts.iter().enumerate() {
            if *part == "FLOOR" && i + 1 < parts.len() {
                if let Ok(floor_num) = parts[i + 1].parse::<i32>() {
                    floor = Some(floor_num);
                }
            }
            // Handle FLOOR-{number} format
            if let Some(floor_str) = part.strip_prefix("FLOOR-") {
                // Remove "FLOOR-" prefix
                if let Ok(floor_num) = floor_str.parse::<i32>() {
                    floor = Some(floor_num);
                }
            }
            if *part == "ROOM" && i + 1 < parts.len() {
                room = Some(parts[i + 1].to_string());
            }
        }
        
        (floor, room)
    }
}


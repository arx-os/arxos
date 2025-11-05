// Universal Path System for ArxOS
// Implements hierarchical addressing for building components
//
// DEPRECATED: This module is deprecated in favor of the new ArxAddress system (src/domain/address.rs).
// UniversalPath is kept for backward compatibility but should not be used in new code.
// Use ArxAddress for all new implementations.
//
// Suppress deprecation warnings within this module since we're maintaining backward compatibility.
#![allow(deprecated)]

use std::collections::HashMap;
use regex::Regex;
use serde::{Deserialize, Serialize};

/// Universal path for building components
/// Format: /BUILDING/{building-name}/FLOOR/{floor-level}/{system-type}/{equipment-name}
/// Example: /BUILDING/Office-Building/FLOOR/2/HVAC/VAV-301
///
/// **DEPRECATED**: Use `ArxAddress` from `crate::domain::address` instead.
/// This type is kept for backward compatibility only.
#[deprecated(note = "Use ArxAddress from crate::domain::address instead")]
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub(crate) struct UniversalPath {
    pub path: String,
    pub components: PathComponents,
}

/// Parsed components of a universal path
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PathComponents {
    pub building_name: String,
    pub floor_level: i32,
    pub system_type: String,
    pub equipment_name: Option<String>,
    pub room_name: Option<String>,
}

/// Path generator with validation and conflict resolution
/// DEPRECATED: This is kept for backward compatibility only. Use ArxAddress instead.
#[allow(dead_code)]
pub(crate) struct PathGenerator {
    used_paths: HashMap<String, String>, // path -> entity_id mapping
    building_name: String,
}

#[allow(dead_code)]
impl PathGenerator {
    pub(crate) fn new(building_name: &str) -> Self {
        Self {
            used_paths: HashMap::new(),
            building_name: Self::sanitize_name(building_name),
        }
    }

    /// Generate universal path for equipment
    pub(crate) fn generate_equipment_path(
        &mut self,
        equipment_name: &str,
        floor_level: i32,
        system_type: &str,
        room_name: Option<&str>,
    ) -> Result<UniversalPath, PathError> {
        let sanitized_equipment = Self::sanitize_name(equipment_name);
        let sanitized_system = Self::sanitize_name(system_type);
        
        let base_path = if let Some(room) = room_name {
            let sanitized_room = Self::sanitize_name(room);
            format!(
                "/BUILDING/{}/FLOOR/{}/ROOM/{}/{}/{}",
                self.building_name, floor_level, sanitized_room, sanitized_system, sanitized_equipment
            )
        } else {
            format!(
                "/BUILDING/{}/FLOOR/{}/{}/{}",
                self.building_name, floor_level, sanitized_system, sanitized_equipment
            )
        };

        // Check for conflicts and resolve
        let final_path = self.resolve_path_conflict(&base_path, &sanitized_equipment)?;

        let components = PathComponents {
            building_name: self.building_name.clone(),
            floor_level,
            system_type: sanitized_system,
            equipment_name: Some(sanitized_equipment),
            room_name: room_name.map(Self::sanitize_name),
        };

        Ok(UniversalPath {
            path: final_path,
            components,
        })
    }

    /// Generate universal path for room
    pub(crate) fn generate_room_path(
        &mut self,
        room_name: &str,
        floor_level: i32,
    ) -> Result<UniversalPath, PathError> {
        let sanitized_room = Self::sanitize_name(room_name);
        
        let base_path = format!(
            "/BUILDING/{}/FLOOR/{}/ROOM/{}",
            self.building_name, floor_level, sanitized_room
        );

        // Check for conflicts and resolve
        let final_path = self.resolve_path_conflict(&base_path, &sanitized_room)?;

        let components = PathComponents {
            building_name: self.building_name.clone(),
            floor_level,
            system_type: "ROOM".to_string(),
            equipment_name: None,
            room_name: Some(sanitized_room),
        };

        Ok(UniversalPath {
            path: final_path,
            components,
        })
    }

    /// Generate universal path for floor
    pub(crate) fn generate_floor_path(&self, floor_level: i32) -> UniversalPath {
        let path = format!(
            "/BUILDING/{}/FLOOR/{}",
            self.building_name, floor_level
        );

        let components = PathComponents {
            building_name: self.building_name.clone(),
            floor_level,
            system_type: "FLOOR".to_string(),
            equipment_name: None,
            room_name: None,
        };

        UniversalPath { path, components }
    }

    /// Generate universal path for building
    pub(crate) fn generate_building_path(&self) -> UniversalPath {
        let path = format!("/BUILDING/{}", self.building_name);

        let components = PathComponents {
            building_name: self.building_name.clone(),
            floor_level: 0,
            system_type: "BUILDING".to_string(),
            equipment_name: None,
            room_name: None,
        };

        UniversalPath { path, components }
    }

    /// Convert universal path to file system path
    pub(crate) fn to_file_path(&self, universal_path: &UniversalPath) -> String {
        let path = &universal_path.path;
        
        // Remove leading /BUILDING/ and convert to file path
        let file_path = path
            .strip_prefix("/BUILDING/")
            .unwrap_or(path)
            .replace("/", "/")
            .to_lowercase();

        format!("{}.yml", file_path)
    }

    /// Convert universal path to directory structure
    pub(crate) fn to_directory_structure(&self, universal_path: &UniversalPath) -> Vec<String> {
        let components = &universal_path.components;
        let mut dirs = vec![
            "buildings".to_string(),
            self.building_name.to_lowercase(),
        ];

        match components.system_type.as_str() {
            "FLOOR" => {
                dirs.push("floors".to_string());
                dirs.push(format!("floor-{}", components.floor_level));
            }
            "ROOM" => {
                dirs.push("floors".to_string());
                dirs.push(format!("floor-{}", components.floor_level));
                dirs.push("rooms".to_string());
            }
            _ => {
                dirs.push("floors".to_string());
                dirs.push(format!("floor-{}", components.floor_level));
                dirs.push("equipment".to_string());
                dirs.push(components.system_type.to_lowercase());
            }
        }

        dirs
    }

    /// Sanitize name for Git-safe paths
    fn sanitize_name(name: &str) -> String {
        // Compile regex patterns (these are static patterns, compilation should never fail)
        // Use expect with clear message since these are hardcoded patterns
        let re = Regex::new(r"[^a-zA-Z0-9\-_]")
            .expect("Internal error: Failed to compile sanitization regex");
        let sanitized = re.replace_all(name, "-");
        
        // Remove multiple consecutive dashes
        let re_dashes = Regex::new(r"-+")
            .expect("Internal error: Failed to compile dash regex");
        let cleaned = re_dashes.replace_all(&sanitized, "-");
        
        // Remove leading/trailing dashes
        cleaned.trim_matches('-').to_string()
    }

    /// Resolve path conflicts by adding numeric suffixes
    fn resolve_path_conflict(&mut self, base_path: &str, entity_name: &str) -> Result<String, PathError> {
        if !self.used_paths.contains_key(base_path) {
            self.used_paths.insert(base_path.to_string(), entity_name.to_string());
            return Ok(base_path.to_string());
        }

        // Try with numeric suffixes
        for i in 1..=999 {
            let conflict_path = format!("{}-{}", base_path, i);
            if !self.used_paths.contains_key(&conflict_path) {
                self.used_paths.insert(conflict_path.clone(), entity_name.to_string());
                return Ok(conflict_path);
            }
        }

        Err(PathError::TooManyConflicts {
            base_path: base_path.to_string(),
        })
    }

    /// Parse existing universal path
    pub(crate) fn parse_path(path: &str) -> Result<UniversalPath, PathError> {
        let re = Regex::new(r"^/BUILDING/([^/]+)/FLOOR/(\d+)(?:/ROOM/([^/]+))?(?:/([^/]+)/([^/]+))?$")
            .map_err(|e| PathError::ValidationFailed {
                reason: format!("Failed to compile path regex: {}", e),
            })?;
        
        if let Some(caps) = re.captures(path) {
            let building_name = caps.get(1)
                .ok_or_else(|| PathError::InvalidFormat {
                    path: path.to_string(),
                })?
                .as_str()
                .to_string();
            
            let floor_level = caps.get(2)
                .ok_or_else(|| PathError::InvalidFormat {
                    path: path.to_string(),
                })?
                .as_str()
                .parse::<i32>()
                .map_err(|e| PathError::InvalidFormat {
                    path: format!("{} (parse error: {})", path, e),
                })?;
            
            let room_name = caps.get(3).map(|m| m.as_str().to_string());
            let system_type = caps.get(4)
                .map(|m| m.as_str().to_string())
                .unwrap_or_else(|| "FLOOR".to_string());
            let equipment_name = caps.get(5).map(|m| m.as_str().to_string());

            let components = PathComponents {
                building_name,
                floor_level,
                system_type,
                equipment_name,
                room_name,
            };

            Ok(UniversalPath {
                path: path.to_string(),
                components,
            })
        } else {
            Err(PathError::InvalidFormat {
                path: path.to_string(),
            })
        }
    }

    /// Get all used paths
    pub(crate) fn get_used_paths(&self) -> &HashMap<String, String> {
        &self.used_paths
    }

    /// Clear used paths (for testing)
    pub(crate) fn clear_paths(&mut self) {
        self.used_paths.clear();
    }
}

/// Path generation errors
#[derive(Debug, thiserror::Error)]
pub enum PathError {
    #[error("Path conflict: too many conflicts for base path {base_path}")]
    TooManyConflicts { base_path: String },
    
    #[error("Invalid path format: {path}")]
    InvalidFormat { path: String },
    
    #[error("Path validation failed: {reason}")]
    ValidationFailed { reason: String },
}

/// Path validation utilities
pub struct PathValidator;

impl PathValidator {
    /// Validate universal path format
    pub fn validate_path(path: &str) -> Result<(), PathError> {
        if path.is_empty() {
            return Err(PathError::ValidationFailed {
                reason: "Path cannot be empty".to_string(),
            });
        }

        if !path.starts_with("/BUILDING/") {
            return Err(PathError::ValidationFailed {
                reason: "Path must start with /BUILDING/".to_string(),
            });
        }

        if path.len() > 500 {
            return Err(PathError::ValidationFailed {
                reason: "Path too long (max 500 characters)".to_string(),
            });
        }

        // Check for invalid characters
        let invalid_chars = ['<', '>', ':', '"', '|', '?', '*'];
        for ch in invalid_chars {
            if path.contains(ch) {
                return Err(PathError::ValidationFailed {
                    reason: format!("Path contains invalid character: {}", ch),
                });
            }
        }

        Ok(())
    }

    /// Validate path components
    pub fn validate_components(components: &PathComponents) -> Result<(), PathError> {
        if components.building_name.is_empty() {
            return Err(PathError::ValidationFailed {
                reason: "Building name cannot be empty".to_string(),
            });
        }

        if components.floor_level < 0 {
            return Err(PathError::ValidationFailed {
                reason: "Floor level cannot be negative".to_string(),
            });
        }

        if components.system_type.is_empty() {
            return Err(PathError::ValidationFailed {
                reason: "System type cannot be empty".to_string(),
            });
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_path_generation() {
        let mut generator = PathGenerator::new("Office Building");
        
        let equipment_path = generator.generate_equipment_path(
            "VAV-301",
            2,
            "HVAC",
            Some("Room-101"),
        ).unwrap();

        assert_eq!(equipment_path.path, "/BUILDING/Office-Building/FLOOR/2/ROOM/Room-101/HVAC/VAV-301");
        assert_eq!(equipment_path.components.building_name, "Office-Building");
        assert_eq!(equipment_path.components.floor_level, 2);
        assert_eq!(equipment_path.components.system_type, "HVAC");
        assert_eq!(equipment_path.components.equipment_name, Some("VAV-301".to_string()));
        assert_eq!(equipment_path.components.room_name, Some("Room-101".to_string()));
    }

    #[test]
    fn test_path_sanitization() {
        let mut generator = PathGenerator::new("Building with Spaces & Special!@#");
        
        let path = generator.generate_equipment_path(
            "Equipment-Name",
            1,
            "HVAC",
            None,
        ).unwrap();

        assert!(path.path.contains("Building-with-Spaces-Special"));
        assert!(!path.path.contains(" "));
        assert!(!path.path.contains("!"));
        assert!(!path.path.contains("@"));
        assert!(!path.path.contains("#"));
    }

    #[test]
    fn test_path_conflict_resolution() {
        let mut generator = PathGenerator::new("Test Building");
        
        let path1 = generator.generate_equipment_path("Equipment", 1, "HVAC", None).unwrap();
        let path2 = generator.generate_equipment_path("Equipment", 1, "HVAC", None).unwrap();
        
        assert_ne!(path1.path, path2.path);
        assert!(path2.path.contains("-1"));
    }

    #[test]
    fn test_path_parsing() {
        let path_str = "/BUILDING/Office-Building/FLOOR/2/HVAC/VAV-301";
        let parsed = PathGenerator::parse_path(path_str).unwrap();
        
        assert_eq!(parsed.path, path_str);
        assert_eq!(parsed.components.building_name, "Office-Building");
        assert_eq!(parsed.components.floor_level, 2);
        assert_eq!(parsed.components.system_type, "HVAC");
        assert_eq!(parsed.components.equipment_name, Some("VAV-301".to_string()));
    }

    #[test]
    fn test_file_path_conversion() {
        let mut generator = PathGenerator::new("Test Building");
        let universal_path = generator.generate_equipment_path("Equipment", 1, "HVAC", None).unwrap();
        let file_path = generator.to_file_path(&universal_path);
        
        assert!(file_path.ends_with(".yml"));
        assert!(file_path.contains("test-building"));
    }

    #[test]
    fn test_directory_structure() {
        let mut generator = PathGenerator::new("Test Building");
        let universal_path = generator.generate_equipment_path("Equipment", 1, "HVAC", None).unwrap();
        let dirs = generator.to_directory_structure(&universal_path);
        
        assert_eq!(dirs, vec!["buildings", "test-building", "floors", "floor-1", "equipment", "hvac"]);
    }
}

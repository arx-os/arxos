//! BILT Rating Models

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

/// BILT Rating scale from 0z (minimal) to 1A (complete digital twin)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BiltRating {
    pub building_id: String,
    pub current_grade: String,  // e.g., "0z", "0y", "0x", ..., "1A"
    pub numeric_score: f64,     // 0.0 to 100.0 for precise calculations
    pub components: RatingComponents,
    pub last_updated: DateTime<Utc>,
    pub version: u64,           // Increments on each update
}

/// Components that contribute to BILT rating
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct RatingComponents {
    /// Basic structure documentation (floor plans, spaces)
    pub structure_score: f64,
    
    /// Object inventory and documentation
    pub inventory_score: f64,
    
    /// Properties and metadata completeness
    pub metadata_score: f64,
    
    /// IoT sensors and real-time data
    pub sensors_score: f64,
    
    /// Historical data and maintenance records
    pub history_score: f64,
    
    /// Verification and data quality
    pub quality_score: f64,
    
    /// Recent contribution activity
    pub activity_score: f64,
}

/// Data completeness metrics for rating calculation
#[derive(Debug, Clone)]
pub struct BuildingDataMetrics {
    pub total_objects: u64,
    pub documented_objects: u64,
    pub objects_with_properties: u64,
    pub objects_with_location: u64,
    pub objects_with_sensors: u64,
    pub total_contributions_last_30_days: u64,
    pub unique_contributors_last_30_days: u64,
    pub verified_contributions: u64,
    pub building_age_days: u64,  // Days since first contribution
}

/// Rating change event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RatingChangeEvent {
    pub building_id: String,
    pub old_grade: String,
    pub new_grade: String,
    pub old_score: f64,
    pub new_score: f64,
    pub trigger_reason: String,  // What caused this rating change
    pub timestamp: DateTime<Utc>,
}

/// Grade conversion utilities
impl BiltRating {
    /// Convert numeric score to BILT grade (0z to 1A)
    pub fn score_to_grade(score: f64) -> String {
        match score {
            s if s < 5.0 => "0z".to_string(),
            s if s < 10.0 => "0y".to_string(),
            s if s < 15.0 => "0x".to_string(),
            s if s < 20.0 => "0w".to_string(),
            s if s < 25.0 => "0v".to_string(),
            s if s < 30.0 => "0u".to_string(),
            s if s < 35.0 => "0t".to_string(),
            s if s < 40.0 => "0s".to_string(),
            s if s < 45.0 => "0r".to_string(),
            s if s < 50.0 => "0q".to_string(),
            s if s < 55.0 => "0p".to_string(),
            s if s < 60.0 => "0o".to_string(),
            s if s < 65.0 => "0n".to_string(),
            s if s < 70.0 => "0m".to_string(),
            s if s < 72.5 => "1z".to_string(),
            s if s < 75.0 => "1y".to_string(),
            s if s < 77.5 => "1x".to_string(),
            s if s < 80.0 => "1w".to_string(),
            s if s < 82.5 => "1v".to_string(),
            s if s < 85.0 => "1u".to_string(),
            s if s < 87.5 => "1t".to_string(),
            s if s < 90.0 => "1s".to_string(),
            s if s < 92.5 => "1r".to_string(),
            s if s < 95.0 => "1q".to_string(),
            s if s < 97.5 => "1p".to_string(),
            _ => "1A".to_string(), // 97.5+ is the highest grade
        }
    }
    
    /// Grade progression value (higher is better)
    pub fn grade_progression_value(grade: &str) -> u32 {
        match grade {
            "0z" => 0, "0y" => 1, "0x" => 2, "0w" => 3, "0v" => 4,
            "0u" => 5, "0t" => 6, "0s" => 7, "0r" => 8, "0q" => 9,
            "0p" => 10, "0o" => 11, "0n" => 12, "0m" => 13,
            "1z" => 14, "1y" => 15, "1x" => 16, "1w" => 17, "1v" => 18,
            "1u" => 19, "1t" => 20, "1s" => 21, "1r" => 22, "1q" => 23,
            "1p" => 24, "1A" => 25,
            _ => 0,
        }
    }
}
//! BILT Rating Calculator
//! 
//! Algorithmic calculation of building ratings based on data completeness,
//! contribution activity, and data quality signals.

use anyhow::Result;
use chrono::{DateTime, Utc, Duration};
use std::sync::Arc;
use uuid::Uuid;

use crate::database::Database;
use super::models::*;

/// BILT Rating Calculator
pub struct BiltRatingCalculator {
    /// Weight for each rating component
    weights: ComponentWeights,
}

/// Weights for rating calculation components
#[derive(Debug, Clone)]
struct ComponentWeights {
    structure: f64,    // Basic floor plans, spaces
    inventory: f64,    // Object count and documentation
    metadata: f64,     // Properties, descriptions
    sensors: f64,      // IoT integration
    history: f64,      // Maintenance records, changes
    quality: f64,      // Verification, data accuracy
    activity: f64,     // Recent contributions
}

impl Default for ComponentWeights {
    fn default() -> Self {
        Self {
            structure: 0.15,   // 15% - Basic building structure
            inventory: 0.20,   // 20% - Object inventory
            metadata: 0.20,    // 20% - Rich metadata
            sensors: 0.15,     // 15% - IoT sensors
            history: 0.10,     // 10% - Historical data
            quality: 0.10,     // 10% - Data verification
            activity: 0.10,    // 10% - Recent activity
        }
    }
}

impl BiltRatingCalculator {
    /// Create new calculator with default weights
    pub fn new() -> Self {
        Self {
            weights: ComponentWeights::default(),
        }
    }
    
    /// Calculate complete building rating
    pub async fn calculate_building_rating(
        &self,
        database: &Database,
        building_id: &str,
    ) -> Result<BiltRating> {
        // Gather building data metrics
        let metrics = self.gather_building_metrics(database, building_id).await?;
        
        // Calculate component scores
        let components = self.calculate_components(&metrics);
        
        // Calculate overall numeric score
        let numeric_score = self.calculate_overall_score(&components);
        
        // Convert to BILT grade
        let current_grade = BiltRating::score_to_grade(numeric_score);
        
        Ok(BiltRating {
            building_id: building_id.to_string(),
            current_grade,
            numeric_score,
            components,
            last_updated: Utc::now(),
            version: 1, // Will be incremented by service
        })
    }
    
    /// Gather raw data metrics from database
    async fn gather_building_metrics(
        &self,
        database: &Database,
        building_id: &str,
    ) -> Result<BuildingDataMetrics> {
        // Query database for building statistics
        let query = r#"
            SELECT 
                COUNT(*) as total_objects,
                COUNT(CASE WHEN properties IS NOT NULL AND properties != '{}' THEN 1 END) as objects_with_properties,
                COUNT(CASE WHEN location IS NOT NULL THEN 1 END) as objects_with_location,
                COUNT(CASE WHEN state->>'status' IS NOT NULL THEN 1 END) as documented_objects,
                COALESCE(
                    (SELECT COUNT(*) 
                     FROM object_history 
                     WHERE building_id = $1 
                       AND created_at > NOW() - INTERVAL '30 days'), 
                    0
                ) as contributions_last_30_days,
                COALESCE(
                    (SELECT COUNT(DISTINCT source) 
                     FROM object_history 
                     WHERE building_id = $1 
                       AND created_at > NOW() - INTERVAL '30 days'), 
                    0
                ) as unique_contributors_last_30_days,
                COALESCE(
                    (SELECT EXTRACT(DAYS FROM NOW() - MIN(created_at))
                     FROM building_objects 
                     WHERE building_id = $1), 
                    0
                ) as building_age_days
            FROM building_objects 
            WHERE building_id = $1
        "#;
        
        let results = database.raw_query(query).await?;
        
        if let Some(row) = results.first() {
            Ok(BuildingDataMetrics {
                total_objects: row.get("total_objects")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(0),
                documented_objects: row.get("documented_objects")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(0),
                objects_with_properties: row.get("objects_with_properties")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(0),
                objects_with_location: row.get("objects_with_location")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(0),
                objects_with_sensors: 0, // TODO: Add sensor detection logic
                total_contributions_last_30_days: row.get("contributions_last_30_days")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(0),
                unique_contributors_last_30_days: row.get("unique_contributors_last_30_days")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(0),
                verified_contributions: 0, // TODO: Add verification tracking
                building_age_days: row.get("building_age_days")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(0),
            })
        } else {
            // Empty building - minimal metrics
            Ok(BuildingDataMetrics {
                total_objects: 0,
                documented_objects: 0,
                objects_with_properties: 0,
                objects_with_location: 0,
                objects_with_sensors: 0,
                total_contributions_last_30_days: 0,
                unique_contributors_last_30_days: 0,
                verified_contributions: 0,
                building_age_days: 0,
            })
        }
    }
    
    /// Calculate component scores from metrics
    fn calculate_components(&self, metrics: &BuildingDataMetrics) -> RatingComponents {
        RatingComponents {
            structure_score: self.calculate_structure_score(metrics),
            inventory_score: self.calculate_inventory_score(metrics),
            metadata_score: self.calculate_metadata_score(metrics),
            sensors_score: self.calculate_sensors_score(metrics),
            history_score: self.calculate_history_score(metrics),
            quality_score: self.calculate_quality_score(metrics),
            activity_score: self.calculate_activity_score(metrics),
        }
    }
    
    /// Structure completeness (basic floor plans, spaces)
    fn calculate_structure_score(&self, metrics: &BuildingDataMetrics) -> f64 {
        if metrics.total_objects == 0 {
            return 0.0; // No structure documented
        }
        
        // Basic structure exists if there are any objects
        let base_score = 30.0; // Minimum for having any structure
        
        // Bonus for location documentation
        let location_bonus = if metrics.total_objects > 0 {
            (metrics.objects_with_location as f64 / metrics.total_objects as f64) * 50.0
        } else {
            0.0
        };
        
        // Bonus for object count (more detailed structure)
        let detail_bonus = (metrics.total_objects as f64).ln().max(0.0) * 5.0;
        
        (base_score + location_bonus + detail_bonus).min(100.0)
    }
    
    /// Inventory completeness (object documentation)
    fn calculate_inventory_score(&self, metrics: &BuildingDataMetrics) -> f64 {
        if metrics.total_objects == 0 {
            return 0.0;
        }
        
        // Score based on object count with diminishing returns
        let count_score = (metrics.total_objects as f64).sqrt() * 10.0;
        
        // Documentation completeness ratio
        let doc_ratio = metrics.documented_objects as f64 / metrics.total_objects as f64;
        let doc_score = doc_ratio * 60.0;
        
        (count_score + doc_score).min(100.0)
    }
    
    /// Metadata richness (properties, descriptions)
    fn calculate_metadata_score(&self, metrics: &BuildingDataMetrics) -> f64 {
        if metrics.total_objects == 0 {
            return 0.0;
        }
        
        let property_ratio = metrics.objects_with_properties as f64 / metrics.total_objects as f64;
        property_ratio * 100.0
    }
    
    /// IoT sensor integration
    fn calculate_sensors_score(&self, metrics: &BuildingDataMetrics) -> f64 {
        if metrics.total_objects == 0 {
            return 0.0;
        }
        
        let sensor_ratio = metrics.objects_with_sensors as f64 / metrics.total_objects as f64;
        sensor_ratio * 100.0
    }
    
    /// Historical data depth
    fn calculate_history_score(&self, metrics: &BuildingDataMetrics) -> f64 {
        let age_score = (metrics.building_age_days as f64 / 365.0).min(2.0) * 25.0; // Max 2 years
        let contribution_score = (metrics.total_contributions_last_30_days as f64).ln().max(0.0) * 15.0;
        
        (age_score + contribution_score).min(100.0)
    }
    
    /// Data quality and verification
    fn calculate_quality_score(&self, metrics: &BuildingDataMetrics) -> f64 {
        if metrics.total_contributions_last_30_days == 0 {
            return 50.0; // Neutral score for no recent activity
        }
        
        // Quality based on contributor diversity
        let contributor_diversity = if metrics.total_contributions_last_30_days > 0 {
            metrics.unique_contributors_last_30_days as f64 / metrics.total_contributions_last_30_days as f64
        } else {
            0.0
        };
        
        // Verified contributions ratio (when implemented)
        let verification_ratio = if metrics.total_contributions_last_30_days > 0 {
            metrics.verified_contributions as f64 / metrics.total_contributions_last_30_days as f64
        } else {
            0.5 // Assume 50% verified for now
        };
        
        ((contributor_diversity * 50.0) + (verification_ratio * 50.0)).min(100.0)
    }
    
    /// Recent activity score (signal of care/investment)
    fn calculate_activity_score(&self, metrics: &BuildingDataMetrics) -> f64 {
        // Recent contributions indicate active care
        let recent_activity = (metrics.total_contributions_last_30_days as f64).ln().max(0.0) * 20.0;
        
        // Contributor engagement
        let engagement = (metrics.unique_contributors_last_30_days as f64) * 15.0;
        
        (recent_activity + engagement).min(100.0)
    }
    
    /// Calculate overall weighted score
    fn calculate_overall_score(&self, components: &RatingComponents) -> f64 {
        self.weights.structure * components.structure_score +
        self.weights.inventory * components.inventory_score +
        self.weights.metadata * components.metadata_score +
        self.weights.sensors * components.sensors_score +
        self.weights.history * components.history_score +
        self.weights.quality * components.quality_score +
        self.weights.activity * components.activity_score
    }
}
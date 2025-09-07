//! BILT Rating System
//! 
//! Calculates real-time building ratings based on data completeness,
//! quality, and contribution activity. Ratings range from 0z (minimal data)
//! to 1A (fully documented digital twin).

pub mod calculator;
pub mod models;
pub mod events;
pub mod handlers;
pub mod triggers;

pub use calculator::BiltRatingCalculator;
pub use models::*;
pub use events::*;
pub use triggers::RatingTriggerSystem;

use axum::{
    routing::{get, post},
    Router,
};
use anyhow::Result;
use uuid::Uuid;
use std::sync::Arc;
use crate::database::Database;

/// BILT Rating Service
pub struct RatingService {
    calculator: Arc<BiltRatingCalculator>,
    database: Arc<Database>,
}

impl RatingService {
    /// Create new rating service
    pub fn new(database: Arc<Database>) -> Self {
        Self {
            calculator: Arc::new(BiltRatingCalculator::new()),
            database,
        }
    }
    
    /// Calculate and update building rating
    pub async fn update_building_rating(&self, building_id: &str) -> Result<BiltRating> {
        let rating = self.calculator.calculate_building_rating(&self.database, building_id).await?;
        self.store_rating(&rating).await?;
        Ok(rating)
    }
    
    /// Get current building rating
    pub async fn get_building_rating(&self, building_id: &str) -> Result<Option<BiltRating>> {
        self.load_rating(building_id).await
    }
    
    /// List building ratings with filtering
    pub async fn list_building_ratings(&self, params: &handlers::ListRatingsQuery) -> Result<Vec<handlers::BuildingRatingInfo>> {
        let sort_column = match params.sort_by {
            handlers::RatingSortBy::Score => "numeric_score DESC",
            handlers::RatingSortBy::Grade => "current_grade",
            handlers::RatingSortBy::Updated => "updated_at DESC",
            handlers::RatingSortBy::Building => "building_id",
        };
        
        let query = format!(
            "SELECT r.building_id, b.name as building_name, r.current_grade, 
                    r.numeric_score, r.updated_at, r.version
             FROM bilt_ratings r
             LEFT JOIN buildings b ON r.building_id = b.id::text
             ORDER BY {} LIMIT {}",
            sort_column, params.limit
        );
        
        let results = self.database.raw_query(&query).await?;
        let mut ratings = Vec::new();
        
        for row in results {
            ratings.push(handlers::BuildingRatingInfo {
                building_id: row.get("building_id").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                building_name: row.get("building_name").and_then(|v| v.as_str()).map(|s| s.to_string()),
                current_grade: row.get("current_grade").and_then(|v| v.as_str()).unwrap_or("0z").to_string(),
                numeric_score: row.get("numeric_score").and_then(|v| v.as_f64()).unwrap_or(0.0),
                last_updated: chrono::Utc::now(), // TODO: Parse from database
                version: row.get("version").and_then(|v| v.as_u64()).unwrap_or(1),
            });
        }
        
        Ok(ratings)
    }
    
    /// Get rating history for a building
    pub async fn get_rating_history(&self, building_id: &str, params: &handlers::RatingHistoryQuery) -> Result<Vec<RatingChangeEvent>> {
        let mut query = format!(
            "SELECT old_grade, new_grade, old_score, new_score, trigger_reason, created_at
             FROM bilt_rating_history 
             WHERE building_id = '{}'",
            building_id
        );
        
        if let Some(since_version) = params.since_version {
            // This would require tracking versions in history table
        }
        
        query.push_str(&format!(" ORDER BY created_at DESC LIMIT {}", params.limit));
        
        let results = self.database.raw_query(&query).await?;
        let mut history = Vec::new();
        
        for row in results {
            history.push(RatingChangeEvent {
                building_id: building_id.to_string(),
                old_grade: row.get("old_grade").and_then(|v| v.as_str()).unwrap_or("0z").to_string(),
                new_grade: row.get("new_grade").and_then(|v| v.as_str()).unwrap_or("0z").to_string(),
                old_score: row.get("old_score").and_then(|v| v.as_f64()).unwrap_or(0.0),
                new_score: row.get("new_score").and_then(|v| v.as_f64()).unwrap_or(0.0),
                trigger_reason: row.get("trigger_reason").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                timestamp: chrono::Utc::now(), // TODO: Parse from database
            });
        }
        
        Ok(history)
    }
    
    /// Get system-wide rating statistics
    pub async fn get_rating_statistics(&self) -> Result<handlers::RatingStatistics> {
        let stats_query = "
            SELECT 
                COUNT(*) as total_buildings,
                AVG(numeric_score) as avg_score,
                COUNT(CASE WHEN updated_at > NOW() - INTERVAL '7 days' THEN 1 END) as recent_improvements,
                COUNT(CASE WHEN last_calculated_at > NOW() - INTERVAL '1 day' THEN 1 END) as recent_calculations
            FROM bilt_ratings
        ";
        
        let grade_query = "
            SELECT current_grade, COUNT(*) as count 
            FROM bilt_ratings 
            GROUP BY current_grade
        ";
        
        let stats_results = self.database.raw_query(stats_query).await?;
        let grade_results = self.database.raw_query(grade_query).await?;
        
        let mut grade_distribution = std::collections::HashMap::new();
        for row in grade_results {
            if let (Some(grade), Some(count)) = (
                row.get("current_grade").and_then(|v| v.as_str()),
                row.get("count").and_then(|v| v.as_u64())
            ) {
                grade_distribution.insert(grade.to_string(), count);
            }
        }
        
        if let Some(stats_row) = stats_results.first() {
            Ok(handlers::RatingStatistics {
                total_buildings: stats_row.get("total_buildings").and_then(|v| v.as_u64()).unwrap_or(0),
                average_score: stats_row.get("avg_score").and_then(|v| v.as_f64()).unwrap_or(0.0),
                grade_distribution,
                recent_improvements: stats_row.get("recent_improvements").and_then(|v| v.as_u64()).unwrap_or(0),
                recent_calculations: stats_row.get("recent_calculations").and_then(|v| v.as_u64()).unwrap_or(0),
            })
        } else {
            Ok(handlers::RatingStatistics {
                total_buildings: 0,
                average_score: 0.0,
                grade_distribution: std::collections::HashMap::new(),
                recent_improvements: 0,
                recent_calculations: 0,
            })
        }
    }
    
    /// Store rating in database
    async fn store_rating(&self, rating: &BiltRating) -> Result<()> {
        let query = "
            INSERT INTO bilt_ratings (
                building_id, current_grade, numeric_score,
                structure_score, inventory_score, metadata_score,
                sensors_score, history_score, quality_score, activity_score,
                last_calculated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (building_id) 
            DO UPDATE SET
                current_grade = EXCLUDED.current_grade,
                numeric_score = EXCLUDED.numeric_score,
                structure_score = EXCLUDED.structure_score,
                inventory_score = EXCLUDED.inventory_score,
                metadata_score = EXCLUDED.metadata_score,
                sensors_score = EXCLUDED.sensors_score,
                history_score = EXCLUDED.history_score,
                quality_score = EXCLUDED.quality_score,
                activity_score = EXCLUDED.activity_score,
                last_calculated_at = EXCLUDED.last_calculated_at
        ";
        
        // Use raw query with parameter binding (simplified for now)
        let insert_sql = format!(
            "INSERT INTO bilt_ratings (
                building_id, current_grade, numeric_score,
                structure_score, inventory_score, metadata_score,
                sensors_score, history_score, quality_score, activity_score,
                last_calculated_at
            ) VALUES ('{}', '{}', {}, {}, {}, {}, {}, {}, {}, {}, CURRENT_TIMESTAMP)
            ON CONFLICT (building_id) 
            DO UPDATE SET
                current_grade = EXCLUDED.current_grade,
                numeric_score = EXCLUDED.numeric_score,
                structure_score = EXCLUDED.structure_score,
                inventory_score = EXCLUDED.inventory_score,
                metadata_score = EXCLUDED.metadata_score,
                sensors_score = EXCLUDED.sensors_score,
                history_score = EXCLUDED.history_score,
                quality_score = EXCLUDED.quality_score,
                activity_score = EXCLUDED.activity_score,
                last_calculated_at = EXCLUDED.last_calculated_at",
            rating.building_id,
            rating.current_grade,
            rating.numeric_score,
            rating.components.structure_score,
            rating.components.inventory_score,
            rating.components.metadata_score,
            rating.components.sensors_score,
            rating.components.history_score,
            rating.components.quality_score,
            rating.components.activity_score
        );
        
        self.database.raw_query(&insert_sql).await?;
        Ok(())
    }
    
    /// Load rating from database
    async fn load_rating(&self, building_id: &str) -> Result<Option<BiltRating>> {
        let query = format!(
            "SELECT * FROM bilt_ratings WHERE building_id = '{}'",
            building_id
        );
        
        let results = self.database.raw_query(&query).await?;
        
        if let Some(row) = results.first() {
            let components = RatingComponents {
                structure_score: row.get("structure_score").and_then(|v| v.as_f64()).unwrap_or(0.0),
                inventory_score: row.get("inventory_score").and_then(|v| v.as_f64()).unwrap_or(0.0),
                metadata_score: row.get("metadata_score").and_then(|v| v.as_f64()).unwrap_or(0.0),
                sensors_score: row.get("sensors_score").and_then(|v| v.as_f64()).unwrap_or(0.0),
                history_score: row.get("history_score").and_then(|v| v.as_f64()).unwrap_or(0.0),
                quality_score: row.get("quality_score").and_then(|v| v.as_f64()).unwrap_or(0.0),
                activity_score: row.get("activity_score").and_then(|v| v.as_f64()).unwrap_or(0.0),
            };
            
            Ok(Some(BiltRating {
                building_id: building_id.to_string(),
                current_grade: row.get("current_grade").and_then(|v| v.as_str()).unwrap_or("0z").to_string(),
                numeric_score: row.get("numeric_score").and_then(|v| v.as_f64()).unwrap_or(0.0),
                components,
                last_updated: chrono::Utc::now(), // TODO: Parse from database
                version: row.get("version").and_then(|v| v.as_u64()).unwrap_or(1),
            }))
        } else {
            Ok(None)
        }
    }
}

/// Create rating API routes
pub fn rating_routes(rating_service: Arc<RatingService>) -> Router {
    Router::new()
        // Building rating endpoints
        .route("/api/buildings/:id/rating", 
            get(handlers::get_building_rating)
            .post(handlers::recalculate_building_rating)
        )
        .route("/api/buildings/:id/rating/breakdown", get(handlers::get_rating_breakdown))
        .route("/api/buildings/:id/rating/history", get(handlers::get_rating_history))
        
        // System-wide rating endpoints
        .route("/api/ratings", get(handlers::list_building_ratings))
        .route("/api/ratings/statistics", get(handlers::get_rating_statistics))
        
        .with_state(rating_service)
}
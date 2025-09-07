//! BILT Rating API Handlers

use axum::{
    extract::{Path, Query, State},
    response::Json,
    http::StatusCode,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use anyhow::Result;

use crate::api::error::{ApiError, ApiResult};
use super::{RatingService, BiltRating, RatingChangeEvent};

/// Get current building rating
pub async fn get_building_rating(
    State(service): State<Arc<RatingService>>,
    Path(building_id): Path<String>,
) -> ApiResult<Json<BiltRating>> {
    match service.get_building_rating(&building_id).await? {
        Some(rating) => Ok(Json(rating)),
        None => {
            // Calculate initial rating if none exists
            let rating = service.update_building_rating(&building_id).await?;
            Ok(Json(rating))
        }
    }
}

/// Force recalculate building rating
pub async fn recalculate_building_rating(
    State(service): State<Arc<RatingService>>,
    Path(building_id): Path<String>,
) -> ApiResult<Json<BiltRating>> {
    let rating = service.update_building_rating(&building_id).await?;
    Ok(Json(rating))
}

/// List all buildings with their current ratings
#[derive(Debug, Deserialize)]
pub struct ListRatingsQuery {
    #[serde(default)]
    pub sort_by: RatingSortBy,
    #[serde(default = "default_limit")]
    pub limit: u32,
}

#[derive(Debug, Deserialize, Default)]
#[serde(rename_all = "lowercase")]
pub enum RatingSortBy {
    #[default]
    Score,
    Grade,
    Updated,
    Building,
}

fn default_limit() -> u32 { 50 }

pub async fn list_building_ratings(
    State(service): State<Arc<RatingService>>,
    Query(params): Query<ListRatingsQuery>,
) -> ApiResult<Json<Vec<BuildingRatingInfo>>> {
    let ratings = service.list_building_ratings(&params).await?;
    Ok(Json(ratings))
}

/// Get rating history for a building
#[derive(Debug, Deserialize)]
pub struct RatingHistoryQuery {
    #[serde(default = "default_history_limit")]
    pub limit: u32,
    pub since_version: Option<u64>,
}

fn default_history_limit() -> u32 { 100 }

pub async fn get_rating_history(
    State(service): State<Arc<RatingService>>,
    Path(building_id): Path<String>,
    Query(params): Query<RatingHistoryQuery>,
) -> ApiResult<Json<Vec<RatingChangeEvent>>> {
    let history = service.get_rating_history(&building_id, &params).await?;
    Ok(Json(history))
}

/// Get rating statistics and trends
pub async fn get_rating_statistics(
    State(service): State<Arc<RatingService>>,
) -> ApiResult<Json<RatingStatistics>> {
    let stats = service.get_rating_statistics().await?;
    Ok(Json(stats))
}

/// Get rating breakdown for a building (component scores)
pub async fn get_rating_breakdown(
    State(service): State<Arc<RatingService>>,
    Path(building_id): Path<String>,
) -> ApiResult<Json<RatingBreakdown>> {
    match service.get_building_rating(&building_id).await? {
        Some(rating) => Ok(Json(RatingBreakdown::from_rating(&rating))),
        None => Err(ApiError::NotFound("Building rating not found".to_string())),
    }
}

/// Response models for API
#[derive(Debug, Serialize)]
pub struct BuildingRatingInfo {
    pub building_id: String,
    pub building_name: Option<String>,
    pub current_grade: String,
    pub numeric_score: f64,
    pub last_updated: chrono::DateTime<chrono::Utc>,
    pub version: u64,
}

#[derive(Debug, Serialize)]
pub struct RatingStatistics {
    pub total_buildings: u64,
    pub average_score: f64,
    pub grade_distribution: std::collections::HashMap<String, u64>,
    pub recent_improvements: u64,  // Buildings improved in last 7 days
    pub recent_calculations: u64,  // Ratings calculated in last 24 hours
}

#[derive(Debug, Serialize)]
pub struct RatingBreakdown {
    pub building_id: String,
    pub overall: RatingScore,
    pub components: ComponentBreakdown,
    pub recommendations: Vec<String>,
}

#[derive(Debug, Serialize)]
pub struct RatingScore {
    pub grade: String,
    pub score: f64,
    pub max_possible: f64,
}

#[derive(Debug, Serialize)]
pub struct ComponentBreakdown {
    pub structure: ComponentScore,
    pub inventory: ComponentScore,
    pub metadata: ComponentScore,
    pub sensors: ComponentScore,
    pub history: ComponentScore,
    pub quality: ComponentScore,
    pub activity: ComponentScore,
}

#[derive(Debug, Serialize)]
pub struct ComponentScore {
    pub score: f64,
    pub weight: f64,
    pub weighted_contribution: f64,
    pub description: String,
}

impl RatingBreakdown {
    pub fn from_rating(rating: &BiltRating) -> Self {
        let components = ComponentBreakdown {
            structure: ComponentScore {
                score: rating.components.structure_score,
                weight: 0.15,
                weighted_contribution: rating.components.structure_score * 0.15,
                description: "Basic floor plans and spatial documentation".to_string(),
            },
            inventory: ComponentScore {
                score: rating.components.inventory_score,
                weight: 0.20,
                weighted_contribution: rating.components.inventory_score * 0.20,
                description: "Object inventory and documentation completeness".to_string(),
            },
            metadata: ComponentScore {
                score: rating.components.metadata_score,
                weight: 0.20,
                weighted_contribution: rating.components.metadata_score * 0.20,
                description: "Rich properties and descriptive metadata".to_string(),
            },
            sensors: ComponentScore {
                score: rating.components.sensors_score,
                weight: 0.15,
                weighted_contribution: rating.components.sensors_score * 0.15,
                description: "IoT sensors and real-time data integration".to_string(),
            },
            history: ComponentScore {
                score: rating.components.history_score,
                weight: 0.10,
                weighted_contribution: rating.components.history_score * 0.10,
                description: "Historical data and maintenance records".to_string(),
            },
            quality: ComponentScore {
                score: rating.components.quality_score,
                weight: 0.10,
                weighted_contribution: rating.components.quality_score * 0.10,
                description: "Data verification and contributor diversity".to_string(),
            },
            activity: ComponentScore {
                score: rating.components.activity_score,
                weight: 0.10,
                weighted_contribution: rating.components.activity_score * 0.10,
                description: "Recent contribution activity and engagement".to_string(),
            },
        };

        let recommendations = Self::generate_recommendations(&components);

        Self {
            building_id: rating.building_id.clone(),
            overall: RatingScore {
                grade: rating.current_grade.clone(),
                score: rating.numeric_score,
                max_possible: 100.0,
            },
            components,
            recommendations,
        }
    }

    fn generate_recommendations(components: &ComponentBreakdown) -> Vec<String> {
        let mut recommendations = Vec::new();

        if components.structure.score < 50.0 {
            recommendations.push("Add more spatial documentation and location data".to_string());
        }
        if components.inventory.score < 50.0 {
            recommendations.push("Document more building objects and systems".to_string());
        }
        if components.metadata.score < 50.0 {
            recommendations.push("Add properties and descriptions to existing objects".to_string());
        }
        if components.sensors.score < 30.0 {
            recommendations.push("Install IoT sensors for real-time monitoring".to_string());
        }
        if components.activity.score < 40.0 {
            recommendations.push("Increase contribution activity to show building care".to_string());
        }

        if recommendations.is_empty() {
            recommendations.push("Excellent rating! Continue maintaining high data quality".to_string());
        }

        recommendations
    }
}
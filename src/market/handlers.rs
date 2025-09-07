//! Market API Handlers

use axum::{
    extract::{Path, Query, State},
    response::Json,
    http::StatusCode,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use uuid::Uuid;

use crate::api::error::{ApiError, ApiResult};
use super::{MarketService, Contribution, ContributionType};
use super::contribution::VerificationStatus;

/// Record a new contribution
pub async fn record_contribution(
    State(service): State<Arc<MarketService>>,
    Json(req): Json<RecordContributionRequest>,
) -> ApiResult<Json<RecordContributionResponse>> {
    let contribution = Contribution {
        id: Uuid::new_v4(),
        contributor_id: req.contributor_id,
        building_id: req.building_id,
        object_id: req.object_id,
        contribution_type: req.contribution_type,
        data_hash: req.data_hash,
        metadata: req.metadata,
        timestamp: chrono::Utc::now(),
        verification_status: VerificationStatus::Pending,
        quality_score: 0.5, // Default until verified
    };
    
    let rewards = service.process_contribution(contribution.clone()).await?;
    
    Ok(Json(RecordContributionResponse {
        contribution_id: contribution.id,
        rewards_distributed: rewards.total_reward,
        status: "success".to_string(),
    }))
}

/// Get contributor profile
pub async fn get_contributor_profile(
    State(service): State<Arc<MarketService>>,
    Path(contributor_id): Path<String>,
) -> ApiResult<Json<super::reputation::ContributorProfile>> {
    let profile = service.reputation_service.get_contributor_profile(&contributor_id).await?;
    Ok(Json(profile))
}

/// Get contributor token balance
pub async fn get_contributor_balance(
    State(service): State<Arc<MarketService>>,
    Path(contributor_id): Path<String>,
) -> ApiResult<Json<ContributorBalanceResponse>> {
    let balances = service.token_service.get_contributor_balance(&contributor_id).await?;
    
    let total_balance = balances.values().sum();
    
    Ok(Json(ContributorBalanceResponse {
        contributor_id,
        balances,
        total_balance,
    }))
}

/// Get building market valuation
pub async fn get_building_valuation(
    State(service): State<Arc<MarketService>>,
    Path(building_id): Path<String>,
) -> ApiResult<Json<super::MarketValuation>> {
    // Get building rating first
    let rating = crate::rating::BiltRating {
        building_id: building_id.clone(),
        current_grade: "0m".to_string(), // TODO: Get actual rating
        numeric_score: 50.0,
        components: Default::default(),
        last_updated: chrono::Utc::now(),
        version: 1,
    };
    
    let valuation = service.get_building_market_value(&building_id, &rating).await?;
    Ok(Json(valuation))
}

/// Get market statistics
pub async fn get_market_statistics(
    State(service): State<Arc<MarketService>>,
) -> ApiResult<Json<super::feeds::MarketStatistics>> {
    let stats = service.market_feed.get_market_stats().await?;
    Ok(Json(stats))
}

/// Get BILT token info
pub async fn get_token_info(
    State(service): State<Arc<MarketService>>,
    Path(building_id): Path<String>,
) -> ApiResult<Json<super::token::BiltToken>> {
    // Get building rating
    let rating = crate::rating::BiltRating {
        building_id: building_id.clone(),
        current_grade: "0m".to_string(), // TODO: Get actual rating
        numeric_score: 50.0,
        components: Default::default(),
        last_updated: chrono::Utc::now(),
        version: 1,
    };
    
    let token = service.token_service.create_or_update_token(&building_id, &rating).await?;
    Ok(Json(token))
}

/// Get top contributors
pub async fn get_top_contributors(
    State(service): State<Arc<MarketService>>,
    Query(params): Query<TopContributorsQuery>,
) -> ApiResult<Json<Vec<super::reputation::ContributorProfile>>> {
    let limit = params.limit.unwrap_or(10);
    let contributors = service.reputation_service.get_top_contributors(limit).await?;
    Ok(Json(contributors))
}

/// Get contribution history
pub async fn get_contribution_history(
    State(service): State<Arc<MarketService>>,
    Query(params): Query<ContributionHistoryQuery>,
) -> ApiResult<Json<Vec<Contribution>>> {
    let contributions = if let Some(building_id) = params.building_id {
        service.contribution_tracker.get_building_contributions(&building_id, params.limit).await?
    } else if let Some(contributor_id) = params.contributor_id {
        service.contribution_tracker.get_contributor_contributions(&contributor_id, params.limit).await?
    } else {
        return Err(ApiError::BadRequest("Must specify building_id or contributor_id".to_string()));
    };
    
    Ok(Json(contributions))
}

/// Verify a contribution
pub async fn verify_contribution(
    State(service): State<Arc<MarketService>>,
    Path(contribution_id): Path<Uuid>,
    Json(req): Json<VerifyContributionRequest>,
) -> ApiResult<Json<VerifyContributionResponse>> {
    service.contribution_tracker.verify_contribution(
        contribution_id,
        req.verification_status,
        &req.verifier_id,
    ).await?;
    
    Ok(Json(VerifyContributionResponse {
        contribution_id,
        status: "verified".to_string(),
    }))
}

/// Get reward parameters
pub async fn get_reward_parameters(
    State(service): State<Arc<MarketService>>,
) -> ApiResult<Json<super::incentives::RewardParameters>> {
    let params = service.incentive_calculator.get_reward_parameters();
    Ok(Json(params))
}

// Request/Response models

#[derive(Debug, Deserialize)]
pub struct RecordContributionRequest {
    pub contributor_id: String,
    pub building_id: String,
    pub object_id: Option<Uuid>,
    pub contribution_type: ContributionType,
    pub data_hash: String,
    pub metadata: serde_json::Value,
}

#[derive(Debug, Serialize)]
pub struct RecordContributionResponse {
    pub contribution_id: Uuid,
    pub rewards_distributed: f64,
    pub status: String,
}

#[derive(Debug, Serialize)]
pub struct ContributorBalanceResponse {
    pub contributor_id: String,
    pub balances: std::collections::HashMap<String, f64>,
    pub total_balance: f64,
}

#[derive(Debug, Deserialize)]
pub struct TopContributorsQuery {
    pub limit: Option<u32>,
}

#[derive(Debug, Deserialize)]
pub struct ContributionHistoryQuery {
    pub building_id: Option<String>,
    pub contributor_id: Option<String>,
    #[serde(default = "default_limit")]
    pub limit: u32,
}

fn default_limit() -> u32 { 100 }

#[derive(Debug, Deserialize)]
pub struct VerifyContributionRequest {
    pub verification_status: VerificationStatus,
    pub verifier_id: String,
}

#[derive(Debug, Serialize)]
pub struct VerifyContributionResponse {
    pub contribution_id: Uuid,
    pub status: String,
}
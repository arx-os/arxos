//! Market Integration & Token Economics
//! 
//! Implements the economic layer of ArxOS, including contribution tracking,
//! token rewards, reputation systems, and market data feeds.

pub mod contribution;
pub mod token;
pub mod reputation;
pub mod feeds;
pub mod incentives;
pub mod handlers;

pub use contribution::{ContributionTracker, Contribution, ContributionType};
pub use token::{BiltToken, TokenMetadata, TokenService};
pub use reputation::{ReputationService, ContributorProfile};
pub use feeds::{MarketDataFeed, PriceFeed};
pub use incentives::{IncentiveCalculator, RewardDistribution};

use anyhow::Result;
use std::sync::Arc;
use crate::database::Database;
use axum::{
    routing::{get, post},
    Router,
};

/// Market integration service coordinating all economic components
pub struct MarketService {
    pub contribution_tracker: Arc<ContributionTracker>,
    pub token_service: Arc<TokenService>,
    pub reputation_service: Arc<ReputationService>,
    pub market_feed: Arc<MarketDataFeed>,
    pub incentive_calculator: Arc<IncentiveCalculator>,
    database: Arc<Database>,
}

impl MarketService {
    /// Create new market service
    pub fn new(database: Arc<Database>) -> Self {
        let contribution_tracker = Arc::new(ContributionTracker::new(database.clone()));
        let reputation_service = Arc::new(ReputationService::new(database.clone()));
        let token_service = Arc::new(TokenService::new(database.clone()));
        let market_feed = Arc::new(MarketDataFeed::new());
        let incentive_calculator = Arc::new(IncentiveCalculator::new());
        
        Self {
            contribution_tracker,
            token_service,
            reputation_service,
            market_feed,
            incentive_calculator,
            database,
        }
    }
    
    /// Process a new contribution and calculate rewards
    pub async fn process_contribution(
        &self,
        contribution: Contribution,
    ) -> Result<RewardDistribution> {
        // Track the contribution
        self.contribution_tracker.record_contribution(&contribution).await?;
        
        // Update contributor reputation
        self.reputation_service.update_reputation(&contribution).await?;
        
        // Calculate token rewards
        let rewards = self.incentive_calculator.calculate_rewards(&contribution).await?;
        
        // Distribute tokens
        self.token_service.distribute_rewards(&rewards).await?;
        
        Ok(rewards)
    }
    
    /// Get current market value of a building
    pub async fn get_building_market_value(
        &self,
        building_id: &str,
        rating: &crate::rating::BiltRating,
    ) -> Result<MarketValuation> {
        // Get base property value from market feed
        let base_value = self.market_feed.get_property_base_value(building_id).await?;
        
        // Apply rating multiplier
        let rating_multiplier = self.calculate_rating_multiplier(rating);
        
        // Calculate BILT token value
        let token_value = self.token_service.calculate_token_value(building_id, rating).await?;
        
        Ok(MarketValuation {
            base_property_value: base_value,
            rating_multiplier,
            bilt_token_value: token_value,
            total_market_value: base_value * rating_multiplier + token_value,
            timestamp: chrono::Utc::now(),
        })
    }
    
    /// Calculate rating multiplier for market value
    fn calculate_rating_multiplier(&self, rating: &crate::rating::BiltRating) -> f64 {
        // Higher ratings exponentially increase value
        // 0z = 0.5x, 0m = 1.0x, 1A = 2.0x
        let normalized_score = rating.numeric_score / 100.0;
        0.5 + (normalized_score * normalized_score * 1.5)
    }
}

/// Market valuation of a building
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct MarketValuation {
    pub base_property_value: f64,
    pub rating_multiplier: f64,
    pub bilt_token_value: f64,
    pub total_market_value: f64,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

/// Create market API routes
pub fn market_routes(market_service: Arc<MarketService>) -> Router {
    Router::new()
        // Contribution endpoints
        .route("/api/contributions", post(handlers::record_contribution))
        .route("/api/contributions/history", get(handlers::get_contribution_history))
        .route("/api/contributions/:id/verify", post(handlers::verify_contribution))
        
        // Contributor endpoints
        .route("/api/contributors/:id/profile", get(handlers::get_contributor_profile))
        .route("/api/contributors/:id/balance", get(handlers::get_contributor_balance))
        .route("/api/contributors/top", get(handlers::get_top_contributors))
        
        // Token endpoints
        .route("/api/tokens/:building_id", get(handlers::get_token_info))
        
        // Market endpoints
        .route("/api/market/valuations/:building_id", get(handlers::get_building_valuation))
        .route("/api/market/statistics", get(handlers::get_market_statistics))
        .route("/api/market/rewards/parameters", get(handlers::get_reward_parameters))
        
        .with_state(market_service)
}
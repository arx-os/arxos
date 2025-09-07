//! BILT Token System
//! 
//! Implements the tokenization of building data contributions,
//! creating a tradeable asset backed by verified building information.

use anyhow::Result;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use std::sync::Arc;
use std::collections::HashMap;
use crate::database::Database;

/// BILT Token representing a building's data value
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BiltToken {
    pub token_id: String,              // Unique token identifier (building_id + version)
    pub building_id: String,
    pub current_supply: f64,           // Total tokens issued
    pub circulating_supply: f64,       // Tokens in circulation
    pub locked_supply: f64,            // Tokens locked in contracts
    pub token_metadata: TokenMetadata,
    pub market_data: MarketData,
    pub created_at: DateTime<Utc>,
    pub last_updated: DateTime<Utc>,
}

/// Token metadata containing building information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenMetadata {
    pub building_name: String,
    pub building_address: String,
    pub current_rating: String,        // BILT rating (0z-1A)
    pub data_completeness: f64,        // 0-100% completeness
    pub total_contributions: u64,
    pub unique_contributors: u64,
    pub last_contribution: DateTime<Utc>,
    pub verification_level: String,    // Level of data verification
    pub ipfs_hash: Option<String>,     // IPFS hash for off-chain data
}

/// Market data for token trading
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketData {
    pub current_price: f64,            // Current token price in USD
    pub market_cap: f64,               // Total market capitalization
    pub volume_24h: f64,               // 24-hour trading volume
    pub price_change_24h: f64,        // 24-hour price change percentage
    pub liquidity_depth: f64,          // Available liquidity
    pub holder_count: u64,             // Number of token holders
}

/// Token distribution for rewards
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenDistribution {
    pub contributor_id: String,
    pub building_id: String,
    pub amount: f64,
    pub distribution_type: DistributionType,
    pub contribution_id: Option<Uuid>,
    pub timestamp: DateTime<Utc>,
}

/// Types of token distributions
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DistributionType {
    ContributionReward,    // Direct contribution reward
    VerificationReward,    // Verification activity reward
    QualityBonus,         // Quality-based bonus
    ReferralReward,       // Referral program reward
    StakingReward,        // Staking/holding reward
    LiquidityProvision,   // Liquidity provider reward
}

/// Token service managing BILT tokens
pub struct TokenService {
    database: Arc<Database>,
}

impl TokenService {
    /// Create new token service
    pub fn new(database: Arc<Database>) -> Self {
        Self { database }
    }
    
    /// Create or update BILT token for a building
    pub async fn create_or_update_token(
        &self,
        building_id: &str,
        rating: &crate::rating::BiltRating,
    ) -> Result<BiltToken> {
        // Calculate token supply based on rating
        let base_supply = 1_000_000.0; // 1M base tokens
        let rating_multiplier = (rating.numeric_score / 100.0) * 2.0; // 0-2x multiplier
        let total_supply = base_supply * (1.0 + rating_multiplier);
        
        // Get building metadata
        let metadata = self.build_token_metadata(building_id, rating).await?;
        
        // Calculate market data
        let market_data = self.calculate_market_data(total_supply, rating.numeric_score).await?;
        
        let token = BiltToken {
            token_id: format!("BILT-{}", building_id),
            building_id: building_id.to_string(),
            current_supply: total_supply,
            circulating_supply: total_supply * 0.7, // 70% circulating
            locked_supply: total_supply * 0.3,      // 30% locked
            token_metadata: metadata,
            market_data,
            created_at: Utc::now(),
            last_updated: Utc::now(),
        };
        
        // Store token in database
        self.store_token(&token).await?;
        
        Ok(token)
    }
    
    /// Distribute token rewards
    pub async fn distribute_rewards(
        &self,
        rewards: &crate::market::incentives::RewardDistribution,
    ) -> Result<()> {
        for allocation in &rewards.allocations {
            let distribution = TokenDistribution {
                contributor_id: allocation.contributor_id.clone(),
                building_id: rewards.building_id.clone(),
                amount: allocation.token_amount,
                distribution_type: DistributionType::ContributionReward,
                contribution_id: Some(rewards.contribution_id),
                timestamp: Utc::now(),
            };
            
            self.record_distribution(&distribution).await?;
            self.update_contributor_balance(&allocation.contributor_id, allocation.token_amount).await?;
        }
        
        Ok(())
    }
    
    /// Calculate token value based on building rating
    pub async fn calculate_token_value(
        &self,
        building_id: &str,
        rating: &crate::rating::BiltRating,
    ) -> Result<f64> {
        // Base value calculation
        let base_value = 1.0; // $1 base per token
        
        // Rating premium (0z = 0.1x, 1A = 10x)
        let rating_premium = (rating.numeric_score / 100.0).powf(2.0) * 10.0;
        
        // Activity multiplier based on recent contributions
        let activity_multiplier = self.get_activity_multiplier(building_id).await?;
        
        // Calculate final token value
        let token_value = base_value * rating_premium * activity_multiplier;
        
        Ok(token_value)
    }
    
    /// Get token balance for a contributor
    pub async fn get_contributor_balance(
        &self,
        contributor_id: &str,
    ) -> Result<HashMap<String, f64>> {
        let query = format!(
            "SELECT building_id, SUM(amount) as balance 
             FROM token_distributions 
             WHERE contributor_id = '{}' 
             GROUP BY building_id",
            contributor_id
        );
        
        let results = self.database.raw_query(&query).await?;
        let mut balances = HashMap::new();
        
        for row in results {
            if let (Some(building_id), Some(balance)) = (
                row.get("building_id").and_then(|v| v.as_str()),
                row.get("balance").and_then(|v| v.as_f64())
            ) {
                balances.insert(building_id.to_string(), balance);
            }
        }
        
        Ok(balances)
    }
    
    /// Build token metadata from building data
    async fn build_token_metadata(
        &self,
        building_id: &str,
        rating: &crate::rating::BiltRating,
    ) -> Result<TokenMetadata> {
        // Query building information
        let query = format!(
            "SELECT b.name, COUNT(bo.id) as object_count,
                    COUNT(DISTINCT c.contributor_id) as contributor_count,
                    COUNT(c.id) as contribution_count,
                    MAX(c.timestamp) as last_contribution
             FROM buildings b
             LEFT JOIN building_objects bo ON b.id = bo.building_id
             LEFT JOIN contributions c ON b.id::text = c.building_id
             WHERE b.id::text = '{}'
             GROUP BY b.id, b.name",
            building_id
        );
        
        let results = self.database.raw_query(&query).await?;
        let row = results.first().ok_or_else(|| anyhow::anyhow!("Building not found"))?;
        
        Ok(TokenMetadata {
            building_name: row.get("name").and_then(|v| v.as_str()).unwrap_or("Unknown").to_string(),
            building_address: format!("Building {}", building_id), // TODO: Add real address
            current_rating: rating.current_grade.clone(),
            data_completeness: rating.numeric_score,
            total_contributions: row.get("contribution_count").and_then(|v| v.as_u64()).unwrap_or(0),
            unique_contributors: row.get("contributor_count").and_then(|v| v.as_u64()).unwrap_or(0),
            last_contribution: Utc::now(), // TODO: Parse from database
            verification_level: "standard".to_string(),
            ipfs_hash: None,
        })
    }
    
    /// Calculate market data for token
    async fn calculate_market_data(
        &self,
        total_supply: f64,
        rating_score: f64,
    ) -> Result<MarketData> {
        // Simple market data calculation
        let price_per_token = 0.01 * (1.0 + rating_score / 100.0);
        let market_cap = total_supply * price_per_token;
        
        Ok(MarketData {
            current_price: price_per_token,
            market_cap,
            volume_24h: market_cap * 0.1, // Assume 10% daily volume
            price_change_24h: 0.0,
            liquidity_depth: market_cap * 0.2, // 20% liquidity
            holder_count: 1, // Start with 1 holder
        })
    }
    
    /// Get activity multiplier for token value
    async fn get_activity_multiplier(&self, building_id: &str) -> Result<f64> {
        let query = format!(
            "SELECT COUNT(*) as recent_contributions 
             FROM contributions 
             WHERE building_id = '{}' 
               AND timestamp > NOW() - INTERVAL '7 days'",
            building_id
        );
        
        let results = self.database.raw_query(&query).await?;
        let recent_contributions = results.first()
            .and_then(|r| r.get("recent_contributions"))
            .and_then(|v| v.as_u64())
            .unwrap_or(0);
        
        // More activity = higher multiplier (1.0 to 2.0)
        Ok(1.0 + (recent_contributions as f64 / 100.0).min(1.0))
    }
    
    /// Store token in database
    async fn store_token(&self, token: &BiltToken) -> Result<()> {
        let query = format!(
            "INSERT INTO bilt_tokens (
                token_id, building_id, current_supply, circulating_supply,
                locked_supply, metadata, market_data, created_at, last_updated
            ) VALUES (
                '{}', '{}', {}, {}, {}, '{}', '{}', '{}', '{}'
            ) ON CONFLICT (token_id) DO UPDATE SET
                current_supply = EXCLUDED.current_supply,
                circulating_supply = EXCLUDED.circulating_supply,
                locked_supply = EXCLUDED.locked_supply,
                metadata = EXCLUDED.metadata,
                market_data = EXCLUDED.market_data,
                last_updated = EXCLUDED.last_updated",
            token.token_id,
            token.building_id,
            token.current_supply,
            token.circulating_supply,
            token.locked_supply,
            serde_json::to_string(&token.token_metadata)?,
            serde_json::to_string(&token.market_data)?,
            token.created_at.to_rfc3339(),
            token.last_updated.to_rfc3339()
        );
        
        self.database.raw_query(&query).await?;
        Ok(())
    }
    
    /// Record token distribution
    async fn record_distribution(&self, distribution: &TokenDistribution) -> Result<()> {
        let query = format!(
            "INSERT INTO token_distributions (
                id, contributor_id, building_id, amount,
                distribution_type, contribution_id, timestamp
            ) VALUES (
                '{}', '{}', '{}', {}, '{}', {}, '{}'
            )",
            Uuid::new_v4(),
            distribution.contributor_id,
            distribution.building_id,
            distribution.amount,
            serde_json::to_string(&distribution.distribution_type)?,
            distribution.contribution_id.map(|id| format!("'{}'", id)).unwrap_or_else(|| "NULL".to_string()),
            distribution.timestamp.to_rfc3339()
        );
        
        self.database.raw_query(&query).await?;
        Ok(())
    }
    
    /// Update contributor token balance
    async fn update_contributor_balance(
        &self,
        contributor_id: &str,
        amount: f64,
    ) -> Result<()> {
        let query = format!(
            "INSERT INTO contributor_balances (contributor_id, total_balance, last_updated)
             VALUES ('{}', {}, NOW())
             ON CONFLICT (contributor_id) DO UPDATE SET
                total_balance = contributor_balances.total_balance + {},
                last_updated = NOW()",
            contributor_id, amount, amount
        );
        
        self.database.raw_query(&query).await?;
        Ok(())
    }
}
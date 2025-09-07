//! Incentive Calculation System
//! 
//! Calculates token rewards and incentives for contributions,
//! implementing the economic model of the Building Whisperer.

use anyhow::Result;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use super::contribution::{Contribution, ContributionType, VerificationStatus};

/// Reward distribution for a contribution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RewardDistribution {
    pub contribution_id: Uuid,
    pub building_id: String,
    pub total_reward: f64,
    pub allocations: Vec<RewardAllocation>,
    pub timestamp: DateTime<Utc>,
}

/// Individual reward allocation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RewardAllocation {
    pub contributor_id: String,
    pub allocation_type: AllocationType,
    pub token_amount: f64,
    pub reason: String,
}

/// Types of reward allocations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AllocationType {
    Primary,      // Primary contributor
    Verifier,     // Verification participant
    Referrer,     // Referral bonus
    Network,      // Network effect bonus
}

/// Calculates incentives and rewards
pub struct IncentiveCalculator {
    // Reward parameters
    base_reward_pool: f64,
    quality_multiplier_max: f64,
    network_effect_bonus: f64,
}

impl IncentiveCalculator {
    /// Create new incentive calculator
    pub fn new() -> Self {
        Self {
            base_reward_pool: 10000.0,  // Daily reward pool
            quality_multiplier_max: 3.0, // Max quality bonus
            network_effect_bonus: 0.1,   // 10% network effect
        }
    }
    
    /// Calculate rewards for a contribution
    pub async fn calculate_rewards(
        &self,
        contribution: &Contribution,
    ) -> Result<RewardDistribution> {
        let mut allocations = Vec::new();
        
        // Calculate base reward
        let base_reward = self.calculate_base_reward(contribution);
        
        // Apply quality multiplier
        let quality_multiplier = self.calculate_quality_multiplier(contribution);
        
        // Apply verification multiplier
        let verification_multiplier = self.calculate_verification_multiplier(contribution);
        
        // Calculate final reward
        let contributor_reward = base_reward * quality_multiplier * verification_multiplier;
        
        // Primary contributor allocation
        allocations.push(RewardAllocation {
            contributor_id: contribution.contributor_id.clone(),
            allocation_type: AllocationType::Primary,
            token_amount: contributor_reward,
            reason: format!("Contribution: {:?}", contribution.contribution_type),
        });
        
        // Add network effect bonus
        if contribution.verification_status == VerificationStatus::PeerVerified {
            let network_bonus = contributor_reward * self.network_effect_bonus;
            allocations.push(RewardAllocation {
                contributor_id: contribution.contributor_id.clone(),
                allocation_type: AllocationType::Network,
                token_amount: network_bonus,
                reason: "Network effect bonus".to_string(),
            });
        }
        
        // Calculate total reward
        let total_reward = allocations.iter().map(|a| a.token_amount).sum();
        
        Ok(RewardDistribution {
            contribution_id: contribution.id,
            building_id: contribution.building_id.clone(),
            total_reward,
            allocations,
            timestamp: Utc::now(),
        })
    }
    
    /// Calculate base reward for contribution type
    fn calculate_base_reward(&self, contribution: &Contribution) -> f64 {
        contribution.contribution_type.base_reward()
    }
    
    /// Calculate quality multiplier (1.0 to max)
    fn calculate_quality_multiplier(&self, contribution: &Contribution) -> f64 {
        1.0 + (contribution.quality_score * (self.quality_multiplier_max - 1.0))
    }
    
    /// Calculate verification multiplier
    fn calculate_verification_multiplier(&self, contribution: &Contribution) -> f64 {
        match contribution.verification_status {
            VerificationStatus::ExpertVerified => 2.0,
            VerificationStatus::PeerVerified => 1.5,
            VerificationStatus::AutoVerified => 1.2,
            VerificationStatus::Pending => 0.8,
            VerificationStatus::Rejected => 0.0,
        }
    }
    
    /// Calculate rewards for bulk contributions
    pub async fn calculate_bulk_rewards(
        &self,
        contributions: &[Contribution],
    ) -> Result<Vec<RewardDistribution>> {
        let mut distributions = Vec::new();
        
        for contribution in contributions {
            let distribution = self.calculate_rewards(contribution).await?;
            distributions.push(distribution);
        }
        
        Ok(distributions)
    }
    
    /// Calculate referral rewards
    pub fn calculate_referral_reward(
        &self,
        referred_contribution_value: f64,
    ) -> f64 {
        referred_contribution_value * 0.05 // 5% referral bonus
    }
    
    /// Calculate staking rewards
    pub fn calculate_staking_reward(
        &self,
        staked_amount: f64,
        staking_duration_days: u64,
        building_rating: f64,
    ) -> f64 {
        let daily_rate = 0.0001 * (1.0 + building_rating / 100.0); // 0.01% daily + rating bonus
        staked_amount * daily_rate * staking_duration_days as f64
    }
    
    /// Calculate liquidity provision rewards
    pub fn calculate_liquidity_reward(
        &self,
        liquidity_provided: f64,
        volume_traded: f64,
        duration_hours: u64,
    ) -> f64 {
        let fee_share = 0.002; // 0.2% of volume
        let time_multiplier = (duration_hours as f64 / 24.0).sqrt(); // Longer provision = more reward
        
        (volume_traded * fee_share) * time_multiplier * (liquidity_provided / 100000.0)
    }
    
    /// Get reward parameters
    pub fn get_reward_parameters(&self) -> RewardParameters {
        RewardParameters {
            base_reward_pool: self.base_reward_pool,
            quality_multiplier_max: self.quality_multiplier_max,
            network_effect_bonus: self.network_effect_bonus,
            contribution_rewards: ContributionType::FloorPlanUpload.base_reward(),
            verification_multipliers: vec![
                ("expert".to_string(), 2.0),
                ("peer".to_string(), 1.5),
                ("auto".to_string(), 1.2),
            ],
        }
    }
}

/// Reward system parameters
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RewardParameters {
    pub base_reward_pool: f64,
    pub quality_multiplier_max: f64,
    pub network_effect_bonus: f64,
    pub contribution_rewards: f64,
    pub verification_multipliers: Vec<(String, f64)>,
}

impl Default for IncentiveCalculator {
    fn default() -> Self {
        Self::new()
    }
}
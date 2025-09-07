//! Contributor Reputation System
//! 
//! Tracks and manages contributor reputation based on contribution
//! quality, verification success, and community standing.

use anyhow::Result;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::sync::Arc;
use crate::database::Database;
use super::contribution::{Contribution, VerificationStatus};

/// Contributor profile with reputation metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContributorProfile {
    pub contributor_id: String,
    pub display_name: Option<String>,
    pub reputation_score: f64,        // 0-1000 reputation points
    pub trust_level: TrustLevel,
    pub total_contributions: u64,
    pub verified_contributions: u64,
    pub rejected_contributions: u64,
    pub specializations: Vec<Specialization>,
    pub badges: Vec<Badge>,
    pub joined_at: DateTime<Utc>,
    pub last_active: DateTime<Utc>,
}

/// Trust levels for contributors
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TrustLevel {
    Newcomer,      // 0-100 reputation
    Contributor,   // 100-300 reputation
    Trusted,       // 300-600 reputation
    Expert,        // 600-900 reputation
    Master,        // 900+ reputation
}

impl TrustLevel {
    /// Get trust level from reputation score
    pub fn from_score(score: f64) -> Self {
        match score {
            s if s < 100.0 => Self::Newcomer,
            s if s < 300.0 => Self::Contributor,
            s if s < 600.0 => Self::Trusted,
            s if s < 900.0 => Self::Expert,
            _ => Self::Master,
        }
    }
    
    /// Get verification weight for trust level
    pub fn verification_weight(&self) -> f64 {
        match self {
            Self::Newcomer => 0.1,
            Self::Contributor => 0.3,
            Self::Trusted => 0.6,
            Self::Expert => 0.9,
            Self::Master => 1.0,
        }
    }
    
    /// Get reward multiplier for trust level
    pub fn reward_multiplier(&self) -> f64 {
        match self {
            Self::Newcomer => 1.0,
            Self::Contributor => 1.2,
            Self::Trusted => 1.5,
            Self::Expert => 2.0,
            Self::Master => 3.0,
        }
    }
}

/// Areas of specialization
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum Specialization {
    ElectricalSystems,
    PlumbingSystems,
    HvacSystems,
    StructuralElements,
    SafetySystems,
    DataVerification,
    PhotoDocumentation,
    BimModeling,
    IoTIntegration,
}

/// Achievement badges
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Badge {
    pub badge_type: BadgeType,
    pub earned_at: DateTime<Utc>,
    pub metadata: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum BadgeType {
    FirstContribution,
    TenContributions,
    HundredContributions,
    ThousandContributions,
    QualityContributor,    // High quality score
    Verifier,              // Verified others' work
    EarlyAdopter,          // Early platform user
    BuildingPioneer,       // First to document a building
    DataHero,              // Exceptional contribution
}

/// Reputation service managing contributor profiles
pub struct ReputationService {
    database: Arc<Database>,
}

impl ReputationService {
    /// Create new reputation service
    pub fn new(database: Arc<Database>) -> Self {
        Self { database }
    }
    
    /// Get or create contributor profile
    pub async fn get_contributor_profile(
        &self,
        contributor_id: &str,
    ) -> Result<ContributorProfile> {
        let query = format!(
            "SELECT * FROM contributor_profiles WHERE contributor_id = '{}'",
            contributor_id
        );
        
        let results = self.database.raw_query(&query).await?;
        
        if let Some(row) = results.first() {
            self.parse_profile_row(row.clone())
        } else {
            // Create new profile
            self.create_new_profile(contributor_id).await
        }
    }
    
    /// Update reputation based on contribution
    pub async fn update_reputation(
        &self,
        contribution: &Contribution,
    ) -> Result<()> {
        let mut profile = self.get_contributor_profile(&contribution.contributor_id).await?;
        
        // Calculate reputation change
        let reputation_delta = self.calculate_reputation_change(contribution);
        
        // Update profile
        profile.reputation_score = (profile.reputation_score + reputation_delta).max(0.0).min(1000.0);
        profile.trust_level = TrustLevel::from_score(profile.reputation_score);
        profile.total_contributions += 1;
        
        if contribution.verification_status != VerificationStatus::Rejected {
            profile.verified_contributions += 1;
        } else {
            profile.rejected_contributions += 1;
        }
        
        profile.last_active = Utc::now();
        
        // Check for new badges
        let new_badges = self.check_badges(&profile, contribution).await?;
        profile.badges.extend(new_badges);
        
        // Save updated profile
        self.save_profile(&profile).await?;
        
        Ok(())
    }
    
    /// Calculate reputation change from contribution
    fn calculate_reputation_change(&self, contribution: &Contribution) -> f64 {
        let base_points = match contribution.verification_status {
            VerificationStatus::ExpertVerified => 10.0,
            VerificationStatus::PeerVerified => 5.0,
            VerificationStatus::AutoVerified => 3.0,
            VerificationStatus::Pending => 1.0,
            VerificationStatus::Rejected => -5.0,
        };
        
        // Apply quality multiplier
        let quality_multiplier = contribution.quality_score;
        
        base_points * quality_multiplier
    }
    
    /// Check for new badges
    async fn check_badges(
        &self,
        profile: &ContributorProfile,
        _contribution: &Contribution,
    ) -> Result<Vec<Badge>> {
        let mut new_badges = Vec::new();
        
        // Check contribution count badges
        if profile.total_contributions == 1 && !self.has_badge(profile, &BadgeType::FirstContribution) {
            new_badges.push(Badge {
                badge_type: BadgeType::FirstContribution,
                earned_at: Utc::now(),
                metadata: serde_json::json!({}),
            });
        }
        
        if profile.total_contributions == 10 && !self.has_badge(profile, &BadgeType::TenContributions) {
            new_badges.push(Badge {
                badge_type: BadgeType::TenContributions,
                earned_at: Utc::now(),
                metadata: serde_json::json!({}),
            });
        }
        
        if profile.total_contributions == 100 && !self.has_badge(profile, &BadgeType::HundredContributions) {
            new_badges.push(Badge {
                badge_type: BadgeType::HundredContributions,
                earned_at: Utc::now(),
                metadata: serde_json::json!({}),
            });
        }
        
        // Check quality badge
        let quality_rate = profile.verified_contributions as f64 / profile.total_contributions.max(1) as f64;
        if quality_rate > 0.95 && profile.total_contributions > 50 && !self.has_badge(profile, &BadgeType::QualityContributor) {
            new_badges.push(Badge {
                badge_type: BadgeType::QualityContributor,
                earned_at: Utc::now(),
                metadata: serde_json::json!({"quality_rate": quality_rate}),
            });
        }
        
        Ok(new_badges)
    }
    
    /// Check if profile has a badge
    fn has_badge(&self, profile: &ContributorProfile, badge_type: &BadgeType) -> bool {
        profile.badges.iter().any(|b| std::mem::discriminant(&b.badge_type) == std::mem::discriminant(badge_type))
    }
    
    /// Get top contributors
    pub async fn get_top_contributors(
        &self,
        limit: u32,
    ) -> Result<Vec<ContributorProfile>> {
        let query = format!(
            "SELECT * FROM contributor_profiles 
             ORDER BY reputation_score DESC 
             LIMIT {}",
            limit
        );
        
        let results = self.database.raw_query(&query).await?;
        let mut profiles = Vec::new();
        
        for row in results {
            profiles.push(self.parse_profile_row(row)?);
        }
        
        Ok(profiles)
    }
    
    /// Create new contributor profile
    async fn create_new_profile(&self, contributor_id: &str) -> Result<ContributorProfile> {
        let profile = ContributorProfile {
            contributor_id: contributor_id.to_string(),
            display_name: None,
            reputation_score: 0.0,
            trust_level: TrustLevel::Newcomer,
            total_contributions: 0,
            verified_contributions: 0,
            rejected_contributions: 0,
            specializations: Vec::new(),
            badges: Vec::new(),
            joined_at: Utc::now(),
            last_active: Utc::now(),
        };
        
        self.save_profile(&profile).await?;
        Ok(profile)
    }
    
    /// Save contributor profile
    async fn save_profile(&self, profile: &ContributorProfile) -> Result<()> {
        let query = format!(
            "INSERT INTO contributor_profiles (
                contributor_id, display_name, reputation_score, trust_level,
                total_contributions, verified_contributions, rejected_contributions,
                specializations, badges, joined_at, last_active
            ) VALUES (
                '{}', {}, {}, '{}', {}, {}, {}, '{}', '{}', '{}', '{}'
            ) ON CONFLICT (contributor_id) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                reputation_score = EXCLUDED.reputation_score,
                trust_level = EXCLUDED.trust_level,
                total_contributions = EXCLUDED.total_contributions,
                verified_contributions = EXCLUDED.verified_contributions,
                rejected_contributions = EXCLUDED.rejected_contributions,
                specializations = EXCLUDED.specializations,
                badges = EXCLUDED.badges,
                last_active = EXCLUDED.last_active",
            profile.contributor_id,
            profile.display_name.as_ref().map(|n| format!("'{}'", n)).unwrap_or_else(|| "NULL".to_string()),
            profile.reputation_score,
            serde_json::to_string(&profile.trust_level)?,
            profile.total_contributions,
            profile.verified_contributions,
            profile.rejected_contributions,
            serde_json::to_string(&profile.specializations)?,
            serde_json::to_string(&profile.badges)?,
            profile.joined_at.to_rfc3339(),
            profile.last_active.to_rfc3339()
        );
        
        self.database.raw_query(&query).await?;
        Ok(())
    }
    
    /// Parse database row into profile
    fn parse_profile_row(&self, row: serde_json::Value) -> Result<ContributorProfile> {
        Ok(ContributorProfile {
            contributor_id: row.get("contributor_id").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            display_name: row.get("display_name").and_then(|v| v.as_str()).map(|s| s.to_string()),
            reputation_score: row.get("reputation_score").and_then(|v| v.as_f64()).unwrap_or(0.0),
            trust_level: row.get("trust_level")
                .and_then(|v| v.as_str())
                .and_then(|s| serde_json::from_str(s).ok())
                .unwrap_or(TrustLevel::Newcomer),
            total_contributions: row.get("total_contributions").and_then(|v| v.as_u64()).unwrap_or(0),
            verified_contributions: row.get("verified_contributions").and_then(|v| v.as_u64()).unwrap_or(0),
            rejected_contributions: row.get("rejected_contributions").and_then(|v| v.as_u64()).unwrap_or(0),
            specializations: row.get("specializations")
                .and_then(|v| v.as_str())
                .and_then(|s| serde_json::from_str(s).ok())
                .unwrap_or_default(),
            badges: row.get("badges")
                .and_then(|v| v.as_str())
                .and_then(|s| serde_json::from_str(s).ok())
                .unwrap_or_default(),
            joined_at: row.get("joined_at")
                .and_then(|v| v.as_str())
                .and_then(|s| DateTime::parse_from_rfc3339(s).ok())
                .map(|dt| dt.with_timezone(&Utc))
                .unwrap_or_else(|| Utc::now()),
            last_active: row.get("last_active")
                .and_then(|v| v.as_str())
                .and_then(|s| DateTime::parse_from_rfc3339(s).ok())
                .map(|dt| dt.with_timezone(&Utc))
                .unwrap_or_else(|| Utc::now()),
        })
    }
}
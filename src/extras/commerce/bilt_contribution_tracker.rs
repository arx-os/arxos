//! BILT Contribution Tracking System
//! 
//! Tracks and validates all contributions to the ArxOS network,
//! calculating BILT rewards based on contribution type, quality, and context.
//! Integrates with blockchain for permanent record keeping.

use crate::arxobject::ArxObject;
use crate::file_storage::Database;
use serde::{Serialize, Deserialize};
use chrono::{DateTime, Utc};
use sha2::{Sha256, Digest};

/// Types of contributions that earn BILT tokens
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
#[repr(u8)]
pub enum ContributionType {
    // Field Contributions (Higher rewards)
    FullRoomScan = 1,       // Complete LiDAR scan of a room
    EquipmentTag = 2,       // Tag and identify equipment
    ARObjectPlace = 3,      // Place AR marker/object
    MaintenanceUpdate = 4,  // Update object status
    VerificationWalk = 5,   // Verify others' contributions
    EmergencyResponse = 6,  // Critical system documentation
    
    // Remote Contributions (Lower rewards)
    ObjectClassification = 10,  // Classify unidentified objects
    DataValidation = 11,        // Validate scan quality
    Documentation = 12,         // Write equipment specs
    RouteOptimization = 13,     // Optimize mesh routing
    BugReport = 14,            // Report system issues
    TrainingContent = 15,      // Create tutorials
}

/// Quality score for contributions
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum QualityScore {
    Poor = 1,
    Fair = 2,
    Good = 3,
    Excellent = 4,
    Perfect = 5,
}

/// A single contribution to the ArxOS network
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Contribution {
    /// Unique contribution ID
    pub id: u64,
    
    /// Contributor's Ethereum address
    pub contributor: [u8; 20],
    
    /// Building where contribution was made
    pub building_id: u16,
    
    /// Type of contribution
    pub contribution_type: ContributionType,
    
    /// Quality score from validation
    pub quality: QualityScore,
    
    /// Timestamp of contribution
    pub timestamp: DateTime<Utc>,
    
    /// BILT tokens earned
    pub bilt_earned: u32,
    
    /// Hash of contribution data for on-chain verification
    pub data_hash: [u8; 32],
    
    /// ArxObjects created/modified
    pub arx_objects: Vec<ArxObject>,
    
    /// GPS coordinates (for field contributions)
    pub location: Option<(f64, f64)>,
    
    /// Peer validations received
    pub validations: Vec<Validation>,
    
    /// Additional metadata
    pub metadata: ContributionMetadata,
}

/// Validation from another user
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Validation {
    pub validator: [u8; 20],
    pub timestamp: DateTime<Utc>,
    pub approved: bool,
    pub quality_score: QualityScore,
    pub comments: Option<String>,
}

/// Additional contribution metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContributionMetadata {
    /// Device used (iPhone model, terminal version, etc)
    pub device: String,
    
    /// Software version
    pub arxos_version: String,
    
    /// Network latency during contribution
    pub latency_ms: u32,
    
    /// Scan resolution/quality metrics
    pub scan_metrics: Option<ScanMetrics>,
    
    /// Time spent on contribution
    pub duration_seconds: u32,
}

/// Metrics for LiDAR scans
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScanMetrics {
    pub point_count: u32,
    pub coverage_percent: f32,
    pub accuracy_percent: f32,
    pub noise_level: f32,
    pub compression_ratio: f32,
}

/// BILT reward calculator
pub struct BiltCalculator {
    /// Base rewards for each contribution type
    base_rewards: std::collections::HashMap<ContributionType, (u32, u32)>, // (min, max)
    
    /// Multipliers for various conditions
    pub quality_multiplier: f32,
    pub urgency_multiplier: f32,
    pub rarity_multiplier: f32,
    pub streak_multiplier: f32,
}

impl BiltCalculator {
    pub fn new() -> Self {
        let mut base_rewards = std::collections::HashMap::new();
        
        // Field contributions (higher rewards)
        base_rewards.insert(ContributionType::FullRoomScan, (100, 500));
        base_rewards.insert(ContributionType::EquipmentTag, (10, 50));
        base_rewards.insert(ContributionType::ARObjectPlace, (20, 100));
        base_rewards.insert(ContributionType::MaintenanceUpdate, (5, 25));
        base_rewards.insert(ContributionType::VerificationWalk, (50, 200));
        base_rewards.insert(ContributionType::EmergencyResponse, (200, 1000));
        
        // Remote contributions (lower rewards)
        base_rewards.insert(ContributionType::ObjectClassification, (2, 10));
        base_rewards.insert(ContributionType::DataValidation, (1, 5));
        base_rewards.insert(ContributionType::Documentation, (5, 20));
        base_rewards.insert(ContributionType::RouteOptimization, (10, 50));
        base_rewards.insert(ContributionType::BugReport, (5, 25));
        base_rewards.insert(ContributionType::TrainingContent, (20, 100));
        
        Self {
            base_rewards,
            quality_multiplier: 1.0,
            urgency_multiplier: 1.0,
            rarity_multiplier: 1.0,
            streak_multiplier: 1.0,
        }
    }
    
    /// Calculate BILT reward for a contribution
    pub fn calculate_reward(
        &self,
        contribution_type: ContributionType,
        quality: QualityScore,
        context: &ContributionContext,
    ) -> u32 {
        let (min, max) = self.base_rewards
            .get(&contribution_type)
            .unwrap_or(&(1, 10));
        
        // Base reward based on quality
        let quality_factor = (quality as u32) as f32 / 5.0;
        let base = min + ((max - min) as f32 * quality_factor) as u32;
        
        // Apply multipliers
        let mut reward = base as f32;
        reward *= self.get_quality_multiplier(quality);
        reward *= self.get_time_multiplier(&context.timestamp);
        reward *= self.get_location_multiplier(context.is_field_contribution);
        reward *= self.get_streak_multiplier(context.daily_streak);
        reward *= self.get_rarity_multiplier(context.building_completion);
        
        // Bonus for first-time contributions
        if context.is_first_in_building {
            reward *= 1.5;
        }
        
        // Cap at maximum to prevent exploitation
        reward.min(max * 2) as u32
    }
    
    fn get_quality_multiplier(&self, quality: QualityScore) -> f32 {
        match quality {
            QualityScore::Poor => 0.5,
            QualityScore::Fair => 0.75,
            QualityScore::Good => 1.0,
            QualityScore::Excellent => 1.25,
            QualityScore::Perfect => 1.5,
        }
    }
    
    fn get_time_multiplier(&self, timestamp: &DateTime<Utc>) -> f32 {
        let hour = timestamp.hour();
        // Night shift bonus (10 PM - 6 AM)
        if hour >= 22 || hour < 6 {
            1.25
        } else {
            1.0
        }
    }
    
    fn get_location_multiplier(&self, is_field: bool) -> f32 {
        if is_field {
            1.2  // Field work gets 20% bonus
        } else {
            1.0
        }
    }
    
    fn get_streak_multiplier(&self, streak: u32) -> f32 {
        match streak {
            0..=2 => 1.0,
            3..=6 => 1.1,
            7..=13 => 1.2,
            14..=29 => 1.3,
            30..=99 => 1.5,
            _ => 2.0,  // 100+ day streak
        }
    }
    
    fn get_rarity_multiplier(&self, building_completion: f32) -> f32 {
        // More reward for contributing to less-complete buildings
        if building_completion < 0.1 {
            1.5  // <10% complete
        } else if building_completion < 0.25 {
            1.3  // <25% complete
        } else if building_completion < 0.5 {
            1.1  // <50% complete
        } else {
            1.0
        }
    }
}

/// Context for calculating contribution rewards
#[derive(Debug, Clone)]
pub struct ContributionContext {
    pub timestamp: DateTime<Utc>,
    pub is_field_contribution: bool,
    pub daily_streak: u32,
    pub building_completion: f32,
    pub is_first_in_building: bool,
}

/// Contribution tracker that manages all contributions
pub struct ContributionTracker {
    calculator: BiltCalculator,
    database: Database,
    pending_validations: Vec<Contribution>,
}

impl ContributionTracker {
    pub fn new(database: Database) -> Self {
        Self {
            calculator: BiltCalculator::new(),
            database,
            pending_validations: Vec::new(),
        }
    }
    
    /// Record a new contribution
    pub async fn record_contribution(
        &mut self,
        contributor: [u8; 20],
        building_id: u16,
        contribution_type: ContributionType,
        arx_objects: Vec<ArxObject>,
        metadata: ContributionMetadata,
    ) -> Result<Contribution, String> {
        // Generate contribution ID
        let id = self.generate_contribution_id();
        
        // Calculate initial quality (will be updated by validations)
        let quality = self.calculate_initial_quality(&arx_objects, &metadata);
        
        // Get context for reward calculation
        let context = self.get_contribution_context(contributor, building_id).await?;
        
        // Calculate BILT reward
        let bilt_earned = self.calculator.calculate_reward(
            contribution_type,
            quality,
            &context,
        );
        
        // Hash the contribution data
        let data_hash = self.hash_contribution_data(&arx_objects, &metadata);
        
        // Create contribution
        let contribution = Contribution {
            id,
            contributor,
            building_id,
            contribution_type,
            quality,
            timestamp: Utc::now(),
            bilt_earned,
            data_hash,
            arx_objects,
            location: metadata.scan_metrics.as_ref().map(|_| (0.0, 0.0)), // TODO: Get from device
            validations: Vec::new(),
            metadata,
        };
        
        // Store in database
        self.database.store_contribution(&contribution).await?;
        
        // Add to pending validations if field contribution
        if context.is_field_contribution {
            self.pending_validations.push(contribution.clone());
        }
        
        // Emit blockchain event
        self.emit_contribution_event(&contribution).await?;
        
        Ok(contribution)
    }
    
    /// Validate another user's contribution
    pub async fn validate_contribution(
        &mut self,
        contribution_id: u64,
        validator: [u8; 20],
        approved: bool,
        quality_score: QualityScore,
        comments: Option<String>,
    ) -> Result<(), String> {
        // Find contribution
        let contribution = self.database.get_contribution(contribution_id).await?;
        
        // Create validation
        let validation = Validation {
            validator,
            timestamp: Utc::now(),
            approved,
            quality_score,
            comments,
        };
        
        // Add validation to contribution
        self.database.add_validation(contribution_id, validation).await?;
        
        // Reward validator
        let validator_reward = if approved { 5 } else { 2 };
        self.reward_validator(validator, validator_reward).await?;
        
        // Update contribution quality based on validations
        self.update_contribution_quality(contribution_id).await?;
        
        Ok(())
    }
    
    fn generate_contribution_id(&self) -> u64 {
        // TODO: Implement proper ID generation
        rand::random()
    }
    
    fn calculate_initial_quality(
        &self,
        arx_objects: &[ArxObject],
        metadata: &ContributionMetadata,
    ) -> QualityScore {
        if let Some(scan) = &metadata.scan_metrics {
            if scan.accuracy_percent > 95.0 && scan.coverage_percent > 90.0 {
                QualityScore::Perfect
            } else if scan.accuracy_percent > 90.0 && scan.coverage_percent > 80.0 {
                QualityScore::Excellent
            } else if scan.accuracy_percent > 80.0 && scan.coverage_percent > 70.0 {
                QualityScore::Good
            } else if scan.accuracy_percent > 70.0 && scan.coverage_percent > 60.0 {
                QualityScore::Fair
            } else {
                QualityScore::Poor
            }
        } else {
            // Default quality for non-scan contributions
            QualityScore::Good
        }
    }
    
    fn hash_contribution_data(
        &self,
        arx_objects: &[ArxObject],
        metadata: &ContributionMetadata,
    ) -> [u8; 32] {
        let mut hasher = Sha256::new();
        
        // Hash ArxObjects
        for obj in arx_objects {
            hasher.update(&obj.to_bytes());
        }
        
        // Hash metadata
        hasher.update(metadata.device.as_bytes());
        hasher.update(metadata.arxos_version.as_bytes());
        
        let result = hasher.finalize();
        let mut hash = [0u8; 32];
        hash.copy_from_slice(&result);
        hash
    }
    
    async fn get_contribution_context(
        &self,
        contributor: [u8; 20],
        building_id: u16,
    ) -> Result<ContributionContext, String> {
        // TODO: Implement context retrieval from database
        Ok(ContributionContext {
            timestamp: Utc::now(),
            is_field_contribution: true,
            daily_streak: 7,
            building_completion: 0.35,
            is_first_in_building: false,
        })
    }
    
    async fn emit_contribution_event(&self, contribution: &Contribution) -> Result<(), String> {
        // TODO: Emit to blockchain
        println!(
            "Blockchain event: {} earned {} BILT for {:?}",
            hex::encode(contribution.contributor),
            contribution.bilt_earned,
            contribution.contribution_type
        );
        Ok(())
    }
    
    async fn reward_validator(&self, validator: [u8; 20], amount: u32) -> Result<(), String> {
        // TODO: Reward validator with BILT
        println!("Validator {} earned {} BILT", hex::encode(validator), amount);
        Ok(())
    }
    
    async fn update_contribution_quality(&self, contribution_id: u64) -> Result<(), String> {
        // TODO: Recalculate quality based on validations
        Ok(())
    }
}

/// Achievement system for gamification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Achievement {
    pub id: String,
    pub name: String,
    pub description: String,
    pub icon: String,
    pub bilt_reward: u32,
    pub xp_reward: u32,
    pub unlocked_at: Option<DateTime<Utc>>,
}

/// Player profile with gamification elements
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlayerProfile {
    pub eth_address: [u8; 20],
    pub username: String,
    pub avatar_seed: u32,
    
    // Stats
    pub total_bilt: u64,
    pub total_xp: u64,
    pub level: u8,
    pub daily_streak: u32,
    pub buildings_scanned: u32,
    pub objects_placed: u32,
    pub accuracy_rating: f32,
    
    // Achievements
    pub achievements: Vec<Achievement>,
    pub titles: Vec<String>,
    
    // Rankings
    pub global_rank: u32,
    pub district_rank: u32,
    pub weekly_rank: u32,
}

impl PlayerProfile {
    /// Calculate level from XP
    pub fn calculate_level(xp: u64) -> u8 {
        // Exponential level curve
        let level = ((xp as f64 / 100.0).sqrt() + 1.0) as u8;
        level.min(99)  // Cap at level 99
    }
    
    /// Get title based on level
    pub fn get_title(&self) -> &str {
        match self.level {
            0..=9 => "Apprentice Scanner",
            10..=24 => "Junior Technician",
            25..=49 => "Field Specialist",
            50..=74 => "Infrastructure Expert",
            75..=98 => "Master Builder",
            99 => "Legendary Architect",
            _ => "Unknown",
        }
    }
    
    /// Check and unlock achievements
    pub fn check_achievements(&mut self) -> Vec<Achievement> {
        let mut newly_unlocked = Vec::new();
        
        // First scan achievement
        if self.buildings_scanned == 1 && !self.has_achievement("first_scan") {
            newly_unlocked.push(Achievement {
                id: "first_scan".to_string(),
                name: "First Steps".to_string(),
                description: "Complete your first room scan".to_string(),
                icon: "🎯".to_string(),
                bilt_reward: 50,
                xp_reward: 100,
                unlocked_at: Some(Utc::now()),
            });
        }
        
        // Building master achievement
        if self.buildings_scanned >= 10 && !self.has_achievement("building_master") {
            newly_unlocked.push(Achievement {
                id: "building_master".to_string(),
                name: "Building Master".to_string(),
                description: "Fully digitize 10 buildings".to_string(),
                icon: "🏆".to_string(),
                bilt_reward: 1000,
                xp_reward: 2000,
                unlocked_at: Some(Utc::now()),
            });
        }
        
        // Accuracy king achievement
        if self.accuracy_rating > 0.99 && self.buildings_scanned > 5 
            && !self.has_achievement("accuracy_king") {
            newly_unlocked.push(Achievement {
                id: "accuracy_king".to_string(),
                name: "Pixel Perfect".to_string(),
                description: "Maintain 99% accuracy over 5 buildings".to_string(),
                icon: "👁️".to_string(),
                bilt_reward: 500,
                xp_reward: 1000,
                unlocked_at: Some(Utc::now()),
            });
        }
        
        // Add newly unlocked achievements
        for achievement in &newly_unlocked {
            self.achievements.push(achievement.clone());
            self.total_bilt += achievement.bilt_reward as u64;
            self.total_xp += achievement.xp_reward as u64;
        }
        
        // Recalculate level
        self.level = Self::calculate_level(self.total_xp);
        
        newly_unlocked
    }
    
    fn has_achievement(&self, id: &str) -> bool {
        self.achievements.iter().any(|a| a.id == id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_bilt_calculation() {
        let calculator = BiltCalculator::new();
        
        let context = ContributionContext {
            timestamp: Utc::now(),
            is_field_contribution: true,
            daily_streak: 7,
            building_completion: 0.2,
            is_first_in_building: false,
        };
        
        let reward = calculator.calculate_reward(
            ContributionType::FullRoomScan,
            QualityScore::Excellent,
            &context,
        );
        
        assert!(reward >= 100 && reward <= 1000);
    }
    
    #[test]
    fn test_level_calculation() {
        assert_eq!(PlayerProfile::calculate_level(0), 1);
        assert_eq!(PlayerProfile::calculate_level(100), 2);
        assert_eq!(PlayerProfile::calculate_level(400), 3);
        assert_eq!(PlayerProfile::calculate_level(10000), 11);
    }
}
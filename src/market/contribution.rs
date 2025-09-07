//! Contribution Tracking System
//! 
//! Tracks and verifies worker contributions to building data,
//! forming the foundation of the token reward system.

use anyhow::Result;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use std::sync::Arc;
use crate::database::Database;

/// Types of contributions that generate value
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum ContributionType {
    FloorPlanUpload,      // Initial building entry
    ObjectDocumentation,  // Adding/updating objects
    PropertyEnrichment,   // Adding metadata
    SensorInstallation,   // IoT integration
    MaintenanceRecord,    // Maintenance logs
    PhotoDocumentation,   // Visual documentation
    BimModelUpdate,       // BIM file updates
    VerificationActivity, // Verifying others' work
    QualityImprovement,  // Data corrections
}

impl ContributionType {
    /// Base token reward for contribution type
    pub fn base_reward(&self) -> f64 {
        match self {
            Self::FloorPlanUpload => 100.0,      // High reward for initial entry
            Self::ObjectDocumentation => 10.0,   // Per object documented
            Self::PropertyEnrichment => 5.0,     // Per property added
            Self::SensorInstallation => 50.0,    // High value for IoT
            Self::MaintenanceRecord => 8.0,      // Maintenance tracking
            Self::PhotoDocumentation => 15.0,    // Visual proof
            Self::BimModelUpdate => 75.0,        // Technical BIM work
            Self::VerificationActivity => 3.0,   // Verification work
            Self::QualityImprovement => 7.0,     // Data quality
        }
    }
    
    /// Impact on building rating
    pub fn rating_impact(&self) -> f64 {
        match self {
            Self::FloorPlanUpload => 5.0,
            Self::ObjectDocumentation => 1.0,
            Self::PropertyEnrichment => 0.5,
            Self::SensorInstallation => 3.0,
            Self::MaintenanceRecord => 0.8,
            Self::PhotoDocumentation => 1.5,
            Self::BimModelUpdate => 4.0,
            Self::VerificationActivity => 0.3,
            Self::QualityImprovement => 0.6,
        }
    }
}

/// A single contribution from a worker
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Contribution {
    pub id: Uuid,
    pub contributor_id: String,      // Worker/contributor identifier
    pub building_id: String,
    pub object_id: Option<Uuid>,     // Specific object if applicable
    pub contribution_type: ContributionType,
    pub data_hash: String,            // Hash of contributed data for verification
    pub metadata: serde_json::Value,  // Additional contribution details
    pub timestamp: DateTime<Utc>,
    pub verification_status: VerificationStatus,
    pub quality_score: f64,          // 0.0 to 1.0 quality rating
}

/// Verification status of contributions
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum VerificationStatus {
    Pending,
    AutoVerified,    // Automatically verified (e.g., sensor data)
    PeerVerified,    // Verified by other contributors
    ExpertVerified,  // Verified by domain expert
    Rejected,        // Failed verification
}

/// Tracks and manages contributions
pub struct ContributionTracker {
    database: Arc<Database>,
}

impl ContributionTracker {
    /// Create new contribution tracker
    pub fn new(database: Arc<Database>) -> Self {
        Self { database }
    }
    
    /// Record a new contribution
    pub async fn record_contribution(&self, contribution: &Contribution) -> Result<()> {
        let query = format!(
            "INSERT INTO contributions (
                id, contributor_id, building_id, object_id,
                contribution_type, data_hash, metadata,
                timestamp, verification_status, quality_score
            ) VALUES (
                '{}', '{}', '{}', {},
                '{}', '{}', '{}',
                '{}', '{}', {}
            )",
            contribution.id,
            contribution.contributor_id,
            contribution.building_id,
            contribution.object_id.map(|id| format!("'{}'", id)).unwrap_or_else(|| "NULL".to_string()),
            serde_json::to_string(&contribution.contribution_type)?,
            contribution.data_hash,
            contribution.metadata,
            contribution.timestamp.to_rfc3339(),
            serde_json::to_string(&contribution.verification_status)?,
            contribution.quality_score
        );
        
        self.database.raw_query(&query).await?;
        Ok(())
    }
    
    /// Get contributions for a building
    pub async fn get_building_contributions(
        &self,
        building_id: &str,
        limit: u32,
    ) -> Result<Vec<Contribution>> {
        let query = format!(
            "SELECT * FROM contributions 
             WHERE building_id = '{}' 
             ORDER BY timestamp DESC 
             LIMIT {}",
            building_id, limit
        );
        
        let results = self.database.raw_query(&query).await?;
        let mut contributions = Vec::new();
        
        for row in results {
            contributions.push(self.parse_contribution_row(row)?);
        }
        
        Ok(contributions)
    }
    
    /// Get contributions by a specific contributor
    pub async fn get_contributor_contributions(
        &self,
        contributor_id: &str,
        limit: u32,
    ) -> Result<Vec<Contribution>> {
        let query = format!(
            "SELECT * FROM contributions 
             WHERE contributor_id = '{}' 
             ORDER BY timestamp DESC 
             LIMIT {}",
            contributor_id, limit
        );
        
        let results = self.database.raw_query(&query).await?;
        let mut contributions = Vec::new();
        
        for row in results {
            contributions.push(self.parse_contribution_row(row)?);
        }
        
        Ok(contributions)
    }
    
    /// Verify a contribution
    pub async fn verify_contribution(
        &self,
        contribution_id: Uuid,
        verification_status: VerificationStatus,
        verifier_id: &str,
    ) -> Result<()> {
        let query = format!(
            "UPDATE contributions 
             SET verification_status = '{}',
                 metadata = jsonb_set(metadata, '{{verifier_id}}', '\"{}\"')
             WHERE id = '{}'",
            serde_json::to_string(&verification_status)?,
            verifier_id,
            contribution_id
        );
        
        self.database.raw_query(&query).await?;
        Ok(())
    }
    
    /// Calculate contribution statistics for a time period
    pub async fn get_contribution_stats(
        &self,
        building_id: &str,
        days: u32,
    ) -> Result<ContributionStats> {
        let query = format!(
            "SELECT 
                COUNT(*) as total_contributions,
                COUNT(DISTINCT contributor_id) as unique_contributors,
                AVG(quality_score) as avg_quality,
                SUM(CASE WHEN verification_status != 'rejected' THEN 1 ELSE 0 END) as verified_count
             FROM contributions
             WHERE building_id = '{}'
               AND timestamp > NOW() - INTERVAL '{} days'",
            building_id, days
        );
        
        let results = self.database.raw_query(&query).await?;
        
        if let Some(row) = results.first() {
            Ok(ContributionStats {
                total_contributions: row.get("total_contributions").and_then(|v| v.as_u64()).unwrap_or(0),
                unique_contributors: row.get("unique_contributors").and_then(|v| v.as_u64()).unwrap_or(0),
                average_quality: row.get("avg_quality").and_then(|v| v.as_f64()).unwrap_or(0.0),
                verification_rate: {
                    let total = row.get("total_contributions").and_then(|v| v.as_f64()).unwrap_or(1.0);
                    let verified = row.get("verified_count").and_then(|v| v.as_f64()).unwrap_or(0.0);
                    if total > 0.0 { verified / total } else { 0.0 }
                },
            })
        } else {
            Ok(ContributionStats::default())
        }
    }
    
    /// Parse database row into Contribution
    fn parse_contribution_row(&self, row: serde_json::Value) -> Result<Contribution> {
        Ok(Contribution {
            id: Uuid::parse_str(row.get("id").and_then(|v| v.as_str()).unwrap_or(""))?,
            contributor_id: row.get("contributor_id").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            building_id: row.get("building_id").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            object_id: row.get("object_id")
                .and_then(|v| v.as_str())
                .and_then(|s| Uuid::parse_str(s).ok()),
            contribution_type: serde_json::from_str(
                row.get("contribution_type").and_then(|v| v.as_str()).unwrap_or("\"object_documentation\"")
            )?,
            data_hash: row.get("data_hash").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            metadata: row.get("metadata").cloned().unwrap_or_else(|| serde_json::json!({})),
            timestamp: DateTime::parse_from_rfc3339(
                row.get("timestamp").and_then(|v| v.as_str()).unwrap_or("")
            )?.with_timezone(&Utc),
            verification_status: serde_json::from_str(
                row.get("verification_status").and_then(|v| v.as_str()).unwrap_or("\"pending\"")
            )?,
            quality_score: row.get("quality_score").and_then(|v| v.as_f64()).unwrap_or(0.5),
        })
    }
}

/// Contribution statistics
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ContributionStats {
    pub total_contributions: u64,
    pub unique_contributors: u64,
    pub average_quality: f64,
    pub verification_rate: f64,
}
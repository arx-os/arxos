use std::borrow::Cow;

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Represents an on-chain/off-chain fiat amount in cents (USD by default).
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Default)]
pub struct Money {
    /// ISO 4217 currency code (e.g., "USD")
    pub currency: Cow<'static, str>,
    /// Amount represented in the smallest currency unit (cents for USD)
    pub amount_cents: u128,
}

impl Money {
    pub fn usd_cents(amount_cents: u128) -> Self {
        Self {
            currency: Cow::Borrowed("USD"),
            amount_cents,
        }
    }

    pub fn from_usd(amount: f64) -> Self {
        let cents = (amount * 100.0).round() as u128;
        Self::usd_cents(cents)
    }

    pub fn as_usd(&self) -> f64 {
        (self.amount_cents as f64) / 100.0
    }

    pub fn zero() -> Self {
        Self::usd_cents(0)
    }
}

/// Tax assessment data captured for a building.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingValuation {
    pub building: String,
    pub assessed_value: Money,
    pub assessor: String,
    pub assessment_reference: Option<String>,
    pub assessed_at: DateTime<Utc>,
}

/// Granular record describing how a contributor's data was used in monetisation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContributionRecord {
    pub contributor_id: String,
    /// Logical dataset or product identifier sold to downstream consumers.
    pub dataset_id: String,
    /// Git commit SHA referencing the dataset snapshot.
    pub commit: String,
    /// Number of times this dataset slice was accessed in the accounting period.
    pub usage_count: u32,
    /// Revenue share allocated to the contributor for this period.
    pub revenue_share: Money,
    /// Quality score assigned by validation pipeline (0.0 - 1.0).
    pub quality_score: f32,
}

/// Revenue distribution for a specific accounting period.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RevenuePayout {
    /// Accounting period label (e.g., "2025-03").
    pub period: String,
    pub total_revenue: Money,
    pub staker_allocation: Money,
    pub burn_allocation: Money,
    pub treasury_allocation: Money,
}

/// High-level snapshot capturing the economic footprint of a building/project.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EconomySnapshot {
    pub valuations: Vec<BuildingValuation>,
    pub contributions: Vec<ContributionRecord>,
    pub revenue_history: Vec<RevenuePayout>,
}

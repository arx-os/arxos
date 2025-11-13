//! Economy domain types for ArxOS
//!
//! Defines core economic data structures for building valuations, contributions,
//! and revenue tracking.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Money type with currency support
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Money {
    pub amount_cents: i64,
    pub currency: String,
}

impl Money {
    pub fn usd_cents(cents: i64) -> Self {
        Self {
            amount_cents: cents,
            currency: "USD".to_string(),
        }
    }

    pub fn dollars(&self) -> f64 {
        self.amount_cents as f64 / 100.0
    }
}

/// Building valuation record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingValuation {
    pub building: String,
    pub assessed_value: Money,
    pub assessor: String,
    pub assessment_reference: Option<String>,
    pub assessed_at: DateTime<Utc>,
}

/// Contribution record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContributionRecord {
    pub contributor: String,
    pub building: String,
    pub amount: Money,
    pub contribution_type: String,
    pub contributed_at: DateTime<Utc>,
}

/// Revenue payout record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RevenuePayout {
    pub period: String,
    pub total_revenue: Money,
    pub staker_allocation: Money,
    pub burn_allocation: Money,
    pub treasury_allocation: Money,
}

/// Complete economy snapshot
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EconomySnapshot {
    pub valuations: Vec<BuildingValuation>,
    pub contributions: Vec<ContributionRecord>,
    pub revenue_history: Vec<RevenuePayout>,
}
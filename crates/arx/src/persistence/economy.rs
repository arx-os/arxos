use std::fs;
use std::path::{Path, PathBuf};

use crate::domain::economy::{ContributionRecord, EconomySnapshot};

use super::{PersistenceError, PersistenceResult};

const ECONOMY_DIR: &str = ".arxos/economy";
const SNAPSHOT_FILE: &str = "snapshot.yaml";
const CONTRIBUTIONS_FILE: &str = "contributions.yaml";

pub fn load_snapshot(base_dir: &Path) -> PersistenceResult<EconomySnapshot> {
    let path = economy_path(base_dir, SNAPSHOT_FILE);
    if !path.exists() {
        return Ok(EconomySnapshot::default());
    }

    let content = fs::read_to_string(&path).map_err(|e| PersistenceError::ReadError {
        reason: format!("Failed to read economy snapshot {:?}: {}", path, e),
    })?;

    serde_yaml::from_str(&content).map_err(|e| PersistenceError::DeserializationError {
        reason: format!("Invalid economy snapshot YAML {:?}: {}", path, e),
    })
}

pub fn save_snapshot(base_dir: &Path, snapshot: &EconomySnapshot) -> PersistenceResult<()> {
    let dir = economy_dir(base_dir);
    fs::create_dir_all(&dir).map_err(|e| PersistenceError::WriteError {
        reason: format!("Failed to create economy directory {:?}: {}", dir, e),
    })?;

    let yaml = serde_yaml::to_string(snapshot).map_err(PersistenceError::SerializationError)?;

    let path = economy_path(base_dir, SNAPSHOT_FILE);
    fs::write(&path, yaml).map_err(|e| PersistenceError::WriteError {
        reason: format!("Failed to write economy snapshot {:?}: {}", path, e),
    })?;

    Ok(())
}

pub fn append_contribution(base_dir: &Path, record: ContributionRecord) -> PersistenceResult<()> {
    let dir = economy_dir(base_dir);
    fs::create_dir_all(&dir).map_err(|e| PersistenceError::WriteError {
        reason: format!("Failed to create economy directory {:?}: {}", dir, e),
    })?;

    let path = economy_path(base_dir, CONTRIBUTIONS_FILE);
    let mut records = if path.exists() {
        let content = fs::read_to_string(&path).map_err(|e| PersistenceError::ReadError {
            reason: format!("Failed to read contribution ledger {:?}: {}", path, e),
        })?;
        serde_yaml::from_str::<Vec<ContributionRecord>>(&content).map_err(|e| {
            PersistenceError::DeserializationError {
                reason: format!("Invalid contribution ledger {:?}: {}", path, e),
            }
        })?
    } else {
        Vec::new()
    };

    records.push(record);

    let yaml = serde_yaml::to_string(&records).map_err(PersistenceError::SerializationError)?;

    fs::write(&path, yaml).map_err(|e| PersistenceError::WriteError {
        reason: format!("Failed to write contribution ledger {:?}: {}", path, e),
    })
}

fn economy_dir(base_dir: &Path) -> PathBuf {
    base_dir.join(ECONOMY_DIR)
}

fn economy_path(base_dir: &Path, filename: &str) -> PathBuf {
    economy_dir(base_dir).join(filename)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::domain::economy::{BuildingValuation, ContributionRecord, Money, RevenuePayout};
    use chrono::Utc;
    use tempfile::tempdir;

    #[test]
    fn load_snapshot_returns_default_when_missing() {
        let dir = tempdir().unwrap();
        let snapshot = load_snapshot(dir.path()).unwrap();
        assert!(snapshot.valuations.is_empty());
        assert!(snapshot.contributions.is_empty());
        assert!(snapshot.revenue_history.is_empty());
    }

    #[test]
    fn save_snapshot_roundtrip() {
        let dir = tempdir().unwrap();
        let snapshot = EconomySnapshot {
            valuations: vec![BuildingValuation {
                building: "alpha".into(),
                assessed_value: Money::usd_cents(1_250_000_00),
                assessor: "NYC DOB".into(),
                assessment_reference: Some("NYC-2025-0123".into()),
                assessed_at: Utc::now(),
            }],
            contributions: vec![],
            revenue_history: vec![RevenuePayout {
                period: "2025-03".into(),
                total_revenue: Money::usd_cents(500_00),
                staker_allocation: Money::usd_cents(300_00),
                burn_allocation: Money::usd_cents(100_00),
                treasury_allocation: Money::usd_cents(100_00),
            }],
        };

        save_snapshot(dir.path(), &snapshot).unwrap();
        let loaded = load_snapshot(dir.path()).unwrap();

        assert_eq!(snapshot.valuations.len(), loaded.valuations.len());
        assert_eq!(snapshot.revenue_history.len(), loaded.revenue_history.len());
        assert_eq!(
            snapshot.revenue_history[0].total_revenue.amount_cents,
            loaded.revenue_history[0].total_revenue.amount_cents
        );
    }

    #[test]
    fn append_contribution_persists_records() {
        let dir = tempdir().unwrap();
        let record = ContributionRecord {
            contributor_id: "user-123".into(),
            dataset_id: "dataset-hvac".into(),
            commit: "abc123".into(),
            usage_count: 4,
            revenue_share: Money::usd_cents(12_34),
            quality_score: 0.92,
        };

        append_contribution(dir.path(), record.clone()).unwrap();
        let ledger_path = economy_path(dir.path(), CONTRIBUTIONS_FILE);
        let content = fs::read_to_string(ledger_path).unwrap();
        let entries: Vec<ContributionRecord> = serde_yaml::from_str(&content).unwrap();

        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0].contributor_id, record.contributor_id);
        assert_eq!(
            entries[0].revenue_share.amount_cents,
            record.revenue_share.amount_cents
        );
    }
}

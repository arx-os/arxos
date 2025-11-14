use std::fs;
use std::path::{Path, PathBuf};

use crate::domain::economy::{ContributionRecord, EconomySnapshot};

use super::PersistenceResult;

const ECONOMY_DIR: &str = ".arxos/economy";
const SNAPSHOT_FILE: &str = "snapshot.yaml";
const CONTRIBUTIONS_FILE: &str = "contributions.yaml";

pub fn load_snapshot(base_dir: &Path) -> PersistenceResult<EconomySnapshot> {
    let path = economy_path(base_dir, SNAPSHOT_FILE);
    if !path.exists() {
        return Ok(EconomySnapshot {
            valuations: vec![],
            contributions: vec![],
            revenue_history: vec![],
        });
    }

    let content = fs::read_to_string(path)?;
    let snapshot = serde_yaml::from_str(&content)?;
    Ok(snapshot)
}

pub fn save_snapshot(base_dir: &Path, snapshot: &EconomySnapshot) -> PersistenceResult<()> {
    let dir = economy_dir(base_dir);
    fs::create_dir_all(&dir)?;

    let path = economy_path(base_dir, SNAPSHOT_FILE);
    let content = serde_yaml::to_string(snapshot)?;
    fs::write(path, content)?;
    Ok(())
}

pub fn append_contribution(base_dir: &Path, record: ContributionRecord) -> PersistenceResult<()> {
    let dir = economy_dir(base_dir);
    fs::create_dir_all(&dir)?;

    let path = economy_path(base_dir, CONTRIBUTIONS_FILE);
    let content = serde_yaml::to_string(&record)?;
    
    // Append to file
    if path.exists() {
        let mut existing = fs::read_to_string(&path)?;
        existing.push_str(&format!("---\n{}", content));
        fs::write(path, existing)?;
    } else {
        fs::write(path, content)?;
    }
    
    Ok(())
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
    use crate::domain::economy::{BuildingValuation, Money, RevenuePayout};
    use chrono::Utc;
    use tempfile::tempdir;

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
    }
}
//! Local access receipt for host gating (N7).
//!
//! After a buyer pays on-chain, hosts write/read `access-receipt.json`.
//! Commercial exports require a receipt whose `building_id` matches the model.

use serde::{Deserialize, Serialize};
use std::path::Path;

/// Proof-of-payment shell stored next to a project (not a chain light-client).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccessReceipt {
    pub package_version: u32,
    pub building_id: String,
    /// On-chain transaction hash (hex, optional 0x).
    pub tx_hash: String,
    /// Buyer wallet if known.
    pub payer: Option<String>,
    /// Whole $AXD paid (informational).
    pub amount_axd: Option<u64>,
    /// Access nonce hex if known.
    pub nonce_hex: Option<String>,
    /// Unix time when receipt was recorded locally.
    pub recorded_at: u64,
    pub summary: String,
}

impl AccessReceipt {
    pub fn new(building_id: &str, tx_hash: &str) -> Self {
        let recorded_at = chrono::Utc::now().timestamp() as u64;
        Self {
            package_version: 1,
            building_id: building_id.to_string(),
            tx_hash: tx_hash.to_string(),
            payer: None,
            amount_axd: None,
            nonce_hex: None,
            recorded_at,
            summary: format!(
                "access granted building={} tx={}",
                building_id,
                &tx_hash[..tx_hash.len().min(18)]
            ),
        }
    }

    pub fn load(path: impl AsRef<Path>) -> Result<Self, String> {
        let raw = std::fs::read_to_string(path.as_ref())
            .map_err(|e| format!("read access receipt: {}", e))?;
        serde_json::from_str(&raw).map_err(|e| format!("parse access receipt: {}", e))
    }

    pub fn save(&self, path: impl AsRef<Path>) -> Result<(), String> {
        let json = serde_json::to_string_pretty(self)
            .map_err(|e| format!("serialize access receipt: {}", e))?;
        std::fs::write(path.as_ref(), json).map_err(|e| format!("write access receipt: {}", e))
    }

    /// True if receipt authorizes export of this building id.
    pub fn authorizes(&self, building_id: &str) -> bool {
        !self.tx_hash.trim().is_empty() && self.building_id == building_id
    }
}

/// Default receipt path in a project root.
pub const DEFAULT_RECEIPT_FILE: &str = "access-receipt.json";

/// Verify a receipt file authorizes `building_id`.
pub fn require_access_receipt(
    receipt_path: impl AsRef<Path>,
    building_id: &str,
) -> Result<AccessReceipt, String> {
    let receipt = AccessReceipt::load(receipt_path.as_ref())?;
    if !receipt.authorizes(building_id) {
        return Err(format!(
            "access receipt building_id '{}' does not match model '{}' (or empty tx_hash)",
            receipt.building_id, building_id
        ));
    }
    Ok(receipt)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn receipt_round_trip_and_authorize() {
        let dir = tempdir().unwrap();
        let path = dir.path().join(DEFAULT_RECEIPT_FILE);
        let r = AccessReceipt::new("uuid-1", "0xabc123");
        r.save(&path).unwrap();
        let loaded = require_access_receipt(&path, "uuid-1").unwrap();
        assert_eq!(loaded.tx_hash, "0xabc123");
        assert!(require_access_receipt(&path, "other").is_err());
    }
}

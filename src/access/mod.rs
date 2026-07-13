//! Data-access quotes for the buyer side of the ArxOS economy.
//!
//! Software is free. **Access to verified building data** is what buyers pay for
//! with $AXD via `ArxPaymentRouter.payForAccess`.
//!
//! This module builds off-chain access requests (nonce + building id) that the
//! chain payment client can fulfill.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// Off-chain access request / receipt shell (package_version 1).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccessRequest {
    pub package_version: u32,
    /// Building UUID (must match Registry + contribution package).
    pub building_id: String,
    /// Optional human name from local model.
    pub building_name: Option<String>,
    /// Suggested payment in whole $AXD (buyer may pay more; not less than on-chain min).
    pub amount_axd: u64,
    /// Hex nonce (32 bytes) — mark used on-chain after payForAccess.
    pub nonce_hex: String,
    /// Unix timestamp when request was created.
    pub timestamp: u64,
    /// Operator summary.
    pub summary: String,
}

/// Build a fresh access request for a building UUID.
pub fn build_access_request(
    building_id: &str,
    building_name: Option<&str>,
    amount_axd: u64,
) -> AccessRequest {
    let timestamp = chrono::Utc::now().timestamp() as u64;
    let nonce = derive_nonce(building_id, timestamp, amount_axd);
    let nonce_hex = hex_encode32(&nonce);
    let summary = format!(
        "access building={} amount_axd={} nonce={}",
        building_id,
        amount_axd,
        &nonce_hex[..16.min(nonce_hex.len())]
    );
    AccessRequest {
        package_version: 1,
        building_id: building_id.to_string(),
        building_name: building_name.map(|s| s.to_string()),
        amount_axd,
        nonce_hex,
        timestamp,
        summary,
    }
}

/// Deterministic-ish nonce from inputs + random salt bytes from time.
fn derive_nonce(building_id: &str, timestamp: u64, amount: u64) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(b"arxos-access-v1");
    hasher.update(building_id.as_bytes());
    hasher.update(timestamp.to_le_bytes());
    hasher.update(amount.to_le_bytes());
    // Extra entropy: process id if available
    hasher.update(std::process::id().to_le_bytes());
    hasher.finalize().into()
}

/// Decode 64-char hex nonce.
pub fn parse_nonce_hex(hex_str: &str) -> Result<[u8; 32], String> {
    crate::contribution::parse_hex32(hex_str)
}

fn hex_encode32(bytes: &[u8; 32]) -> String {
    bytes.iter().map(|b| format!("{:02x}", b)).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn access_request_has_nonce() {
        let req = build_access_request("uuid-1", Some("HQ"), 1);
        assert_eq!(req.package_version, 1);
        assert_eq!(req.nonce_hex.len(), 64);
        assert_eq!(req.amount_axd, 1);
        assert!(parse_nonce_hex(&req.nonce_hex).is_ok());
    }
}

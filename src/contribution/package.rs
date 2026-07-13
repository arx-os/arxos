//! Portable contribution package (disk JSON) for oracle submission.

use serde::{Deserialize, Serialize};

use crate::core::Building;
use crate::validation::validate_building;

use super::commitment::{commit_building, BuildingCommitment};
use super::quality::{quality_from_building, QualityScores};

/// Serializable claim ready for oracle / audit trail.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContributionPackage {
    /// Schema of this package file.
    pub package_version: u32,
    /// Hash algorithm used for roots in this package.
    pub hash_algorithm: String,
    /// Building UUID (Registry `buildingId` candidate).
    pub building_id: String,
    /// Building human name (informational).
    pub building_name: String,
    /// Primary merkle root (hex) for Solidity `ContributionProof.merkleRoot`.
    pub merkle_root_hex: String,
    /// YAML content hash (hex).
    pub content_hash_hex: String,
    /// Entity structure root (hex).
    pub entity_root_hex: String,
    /// Optional Git commit oid when contribution is bound to a commit.
    pub git_commit: Option<String>,
    /// Serialized model size.
    pub data_size: u64,
    /// Quality 0–100.
    pub accuracy: u8,
    pub completeness: u8,
    /// Unix timestamp when package was built.
    pub timestamp: u64,
    /// Location used for locationHash (optional; 0,0 means unset).
    pub latitude: f64,
    pub longitude: f64,
    /// Hex location hash if computed (optional convenience).
    pub location_hash_hex: Option<String>,
    /// Validation had errors at package time (should be false for mint path).
    pub validation_errors: bool,
    /// Summary line for operators.
    pub summary: String,
}

/// Options for packaging a contribution.
#[derive(Debug, Clone)]
pub struct PackageOptions {
    pub latitude: f64,
    pub longitude: f64,
    pub git_commit: Option<String>,
    /// If true, refuse package when validation has errors.
    pub require_clean_validation: bool,
}

impl Default for PackageOptions {
    fn default() -> Self {
        Self {
            latitude: 0.0,
            longitude: 0.0,
            git_commit: None,
            require_clean_validation: true,
        }
    }
}

/// Build a contribution package from a Building (primary labor path).
pub fn build_contribution_package(
    building: &Building,
    opts: PackageOptions,
) -> Result<ContributionPackage, String> {
    let report = validate_building(building);
    if opts.require_clean_validation && report.has_errors() {
        let details: Vec<String> = report.errors().map(|e| e.message.clone()).collect();
        return Err(format!(
            "cannot contribute invalid building: {}",
            details.join("; ")
        ));
    }

    let commitment: BuildingCommitment = commit_building(building)?;
    let quality: QualityScores = quality_from_building(building);
    let timestamp = chrono::Utc::now().timestamp() as u64;

    let location_hash_hex = if opts.latitude != 0.0 || opts.longitude != 0.0 {
        Some(hex_encode(&location_hash(
            opts.latitude,
            opts.longitude,
            timestamp,
        )))
    } else {
        None
    };

    let merkle_hex = commitment.merkle_root_hex();
    let content_hex = commitment.content_hash_hex();
    let entity_hex = hex_encode(&commitment.entity_root);
    let summary = format!(
        "building={} merkle={} accuracy={} completeness={} git={}",
        commitment.building_id,
        &merkle_hex[..16.min(merkle_hex.len())],
        quality.accuracy,
        quality.completeness,
        opts.git_commit.as_deref().unwrap_or("none")
    );

    Ok(ContributionPackage {
        package_version: 1,
        hash_algorithm: commitment.algorithm.to_string(),
        building_id: commitment.building_id.clone(),
        building_name: building.name.clone(),
        merkle_root_hex: merkle_hex,
        content_hash_hex: content_hex,
        entity_root_hex: entity_hex,
        git_commit: opts.git_commit,
        data_size: commitment.data_size,
        accuracy: quality.accuracy,
        completeness: quality.completeness,
        timestamp,
        latitude: opts.latitude,
        longitude: opts.longitude,
        location_hash_hex,
        validation_errors: report.has_errors(),
        summary,
    })
}

fn location_hash(lat: f64, lon: f64, timestamp: u64) -> [u8; 32] {
    use sha2::{Digest, Sha256};
    let mut hasher = Sha256::new();
    hasher.update(lat.to_le_bytes());
    hasher.update(lon.to_le_bytes());
    hasher.update(timestamp.to_le_bytes());
    hasher.finalize().into()
}

fn hex_encode(bytes: &[u8; 32]) -> String {
    bytes.iter().map(|b| format!("{:02x}", b)).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::Floor;

    #[test]
    fn package_requires_valid_building() {
        let mut b = Building::new("".into(), "/x".into()); // empty name → validation error
        b.id = "id".into();
        b.add_floor(Floor::new("G".into(), 0));
        let err = build_contribution_package(&b, PackageOptions::default());
        assert!(err.is_err());
    }

    #[test]
    fn package_ok_for_valid_building() {
        let mut b = Building::new("Pkg HQ".into(), "/pkg".into());
        b.add_floor(Floor::new("G".into(), 0));
        let pkg = build_contribution_package(&b, PackageOptions::default()).unwrap();
        assert_eq!(pkg.package_version, 1);
        assert_eq!(pkg.building_id, b.id);
        assert_eq!(pkg.merkle_root_hex.len(), 64);
        assert!(!pkg.validation_errors);
    }
}

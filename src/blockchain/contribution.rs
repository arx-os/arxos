//! Building/labor contribution helpers for on-chain paths.
//!
//! Primary path: merkle root from validated `building.yaml` labor
//! ([`WorkContribution::from_building_merkle`]).
//! Optional secondary: hash of free-form key/value readings ([`DeviceReadings`]).

use crate::blockchain::merkle::ArxMerkleTree;
use crate::core::identity::ArxId;
use anyhow::Result;
use ethers::types::H256;
use ethers::utils::keccak256;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[cfg(test)]
use rs_merkle::Hasher;

#[cfg(feature = "agent")]
use tracing;

/// Free-form reading map for secondary contribution proofs (not BACnet/hardware).
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct DeviceReadings {
    pub readings: HashMap<String, f64>,
}

/// A documented unit of labor ready for on-chain validation.
#[derive(Debug, Clone)]
pub struct WorkContribution {
    pub worker_id: ArxId,
    pub entity_id: ArxId,
    pub change_hash: [u8; 32],
    pub timestamp: u64,
}

impl WorkContribution {
    /// Primary: contribution bound to a building-data merkle root (hex or raw 32 bytes).
    pub fn from_building_merkle(
        worker_id: ArxId,
        building_entity_id: ArxId,
        merkle_root: [u8; 32],
    ) -> Self {
        Self {
            worker_id,
            entity_id: building_entity_id,
            change_hash: merkle_root,
            timestamp: chrono::Utc::now().timestamp() as u64,
        }
    }

    /// Secondary: deterministic hash of key/value readings (lab/tests only).
    pub fn from_readings(worker_id: ArxId, entity_id: ArxId, state: &DeviceReadings) -> Self {
        Self {
            worker_id,
            entity_id,
            change_hash: Self::compute_readings_hash(state),
            timestamp: chrono::Utc::now().timestamp() as u64,
        }
    }

    /// Computes a deterministic hash of sorted readings.
    pub fn compute_readings_hash(state: &DeviceReadings) -> [u8; 32] {
        let mut keys: Vec<&String> = state.readings.keys().collect();
        keys.sort();

        let mut payload = String::new();
        for key in keys {
            if let Some(val) = state.readings.get(key) {
                payload.push_str(&format!("{}:{}|", key, val));
            }
        }

        keccak256(payload.as_bytes())
    }
}

/// Accumulates multiple `WorkContribution` actions to be batched into a single on-chain L2 root.
#[derive(Debug, Clone)]
pub struct ContributionBuffer {
    pub items: Vec<WorkContribution>,
    pub window_name: String,
}

impl ContributionBuffer {
    pub fn new(window_name: &str) -> Self {
        Self {
            items: Vec::new(),
            window_name: window_name.to_string(),
        }
    }

    pub fn add_contribution(&mut self, contribution: WorkContribution) {
        self.items.push(contribution);
    }

    /// Iterates through all batched contributions and computes a deterministic ordered root.
    pub fn generate_batch_root(&self) -> [u8; 32] {
        if self.items.is_empty() {
            return keccak256(self.window_name.as_bytes());
        }

        let tree = self.build_merkle_tree();
        tree.get_root()
            .unwrap_or_else(|| keccak256(self.window_name.as_bytes()))
    }

    /// Builds a proper binary Merkle Tree from the batched contributions.
    pub fn build_merkle_tree(&self) -> ArxMerkleTree {
        let leaves_data: Vec<Vec<u8>> = self
            .items
            .iter()
            .map(|item| {
                let row = format!(
                    "w:{}_e:{}_h:{}_t:{}|",
                    item.worker_id.0,
                    item.entity_id.0,
                    hex::encode(item.change_hash),
                    item.timestamp
                );
                row.into_bytes()
            })
            .collect();

        ArxMerkleTree::build_tree(&leaves_data)
    }
}

/// Service bridging building contributions to the ArxContribution tokenomics contract.
#[derive(Default)]
pub struct ContributionService;

impl ContributionService {
    pub fn new() -> Self {
        Self
    }

    /// Submit a building-merkle contribution (primary path).
    pub async fn submit_building_merkle(
        &self,
        worker_id: ArxId,
        entity_id: ArxId,
        merkle_root: [u8; 32],
    ) -> Result<H256> {
        let _contribution = WorkContribution::from_building_merkle(worker_id, entity_id, merkle_root);

        #[cfg(feature = "agent")]
        tracing::info!(
            "Submitting building WorkContribution: worker={}, entity={}, hash={:?}",
            _contribution.worker_id.0,
            _contribution.entity_id.0,
            hex::encode(_contribution.change_hash)
        );

        Ok(H256::repeat_byte(0xaa))
    }

    /// Submits an entire batch of `WorkContribution` items via a single Merkle root.
    pub async fn submit_batch(&self, buffer: &ContributionBuffer) -> Result<H256> {
        let _batch_root = buffer.generate_batch_root();

        #[cfg(feature = "agent")]
        tracing::info!(
            "Submitting ContributionBuffer: window='{}', items={}, root={:?}",
            buffer.window_name,
            buffer.items.len(),
            hex::encode(_batch_root)
        );

        Ok(H256::repeat_byte(0xbb))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_readings_hashing() {
        let mut readings = HashMap::new();
        readings.insert("Supply_Air_Temp".to_string(), 22.5);
        readings.insert("Return_Air_Temp".to_string(), 24.0);
        let state = DeviceReadings { readings };

        let hash = WorkContribution::compute_readings_hash(&state);
        assert_ne!(hash, [0u8; 32]);
    }

    #[test]
    fn test_batch_root_determinism() {
        let worker_1 = ArxId(uuid::Uuid::new_v4());
        let entity_1 = ArxId(uuid::Uuid::new_v4());
        let worker_2 = ArxId(uuid::Uuid::new_v4());
        let entity_2 = ArxId(uuid::Uuid::new_v4());

        let cont_1 = WorkContribution::from_readings(
            worker_1,
            entity_1,
            &DeviceReadings {
                readings: HashMap::from([("Sensor_A".into(), 10.0)]),
            },
        );
        let cont_2 = WorkContribution::from_readings(
            worker_2,
            entity_2,
            &DeviceReadings {
                readings: HashMap::from([("Sensor_B".into(), 20.0)]),
            },
        );
        let cont_3 = WorkContribution::from_readings(
            worker_1,
            entity_2,
            &DeviceReadings {
                readings: HashMap::from([("Sensor_C".into(), 30.0)]),
            },
        );

        let mut buffer_a = ContributionBuffer::new("Daily Batch - March 14");
        buffer_a.add_contribution(cont_1.clone());
        buffer_a.add_contribution(cont_2.clone());
        buffer_a.add_contribution(cont_3.clone());
        let root_a = buffer_a.generate_batch_root();

        let mut buffer_b = ContributionBuffer::new("Daily Batch - March 14");
        buffer_b.add_contribution(cont_3.clone());
        buffer_b.add_contribution(cont_1.clone());
        buffer_b.add_contribution(cont_2.clone());
        let root_b = buffer_b.generate_batch_root();
        assert_ne!(root_a, root_b);

        let mut buffer_c = ContributionBuffer::new("Daily Batch - March 14");
        buffer_c.add_contribution(cont_1.clone());
        buffer_c.add_contribution(cont_2.clone());
        buffer_c.add_contribution(cont_3.clone());
        assert_eq!(root_a, buffer_c.generate_batch_root());
    }

    #[test]
    fn test_merkle_tree_proof_generation_and_verification() {
        let worker_1 = ArxId(uuid::Uuid::new_v4());
        let entity_1 = ArxId(uuid::Uuid::new_v4());
        let worker_2 = ArxId(uuid::Uuid::new_v4());
        let entity_2 = ArxId(uuid::Uuid::new_v4());

        let cont_1 = WorkContribution::from_readings(
            worker_1,
            entity_1,
            &DeviceReadings {
                readings: HashMap::from([("Sensor_A".into(), 10.0)]),
            },
        );
        let cont_2 = WorkContribution::from_readings(
            worker_2,
            entity_2,
            &DeviceReadings {
                readings: HashMap::from([("Sensor_B".into(), 20.0)]),
            },
        );
        let cont_3 = WorkContribution::from_readings(
            worker_1,
            entity_2,
            &DeviceReadings {
                readings: HashMap::from([("Sensor_C".into(), 30.0)]),
            },
        );

        let mut buffer = ContributionBuffer::new("Daily Batch - March 14");
        buffer.add_contribution(cont_1.clone());
        buffer.add_contribution(cont_2.clone());
        buffer.add_contribution(cont_3.clone());

        let root = buffer.generate_batch_root();
        let tree = buffer.build_merkle_tree();
        assert_eq!(tree.get_root().unwrap(), root);

        let get_row_bytes = |item: &WorkContribution| {
            format!(
                "w:{}_e:{}_h:{}_t:{}|",
                item.worker_id.0,
                item.entity_id.0,
                hex::encode(item.change_hash),
                item.timestamp
            )
            .into_bytes()
        };

        let leaf_2_bytes = get_row_bytes(&cont_2);
        let leaf_2_hash = crate::blockchain::merkle::Keccak256Algorithm::hash(&leaf_2_bytes);
        let proof_bytes = tree.generate_proof(&[1]);
        let is_valid = ArxMerkleTree::verify_proof(
            root,
            &proof_bytes,
            &[1],
            &[leaf_2_hash],
            3,
        );
        assert!(is_valid);
    }
}

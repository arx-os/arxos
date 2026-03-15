use std::collections::HashMap;
use ethers::types::{H256, U256};
use ethers::utils::keccak256;
use crate::core::identity::ArxId; // Explicitly renamed ArxId
use crate::hardware::DeviceState;
use anyhow::Result;

#[cfg(feature = "agent")]
use tracing;

/// A documented unit of physical maintenance ready for on-chain validation.
#[derive(Debug, Clone)]
pub struct WorkContribution {
    pub worker_id: ArxId,
    pub entity_id: ArxId,
    pub change_hash: [u8; 32],
    pub timestamp: u64,
}

impl WorkContribution {
    pub fn new(worker_id: ArxId, entity_id: ArxId, state: &DeviceState) -> Self {
        Self {
            worker_id,
            entity_id,
            change_hash: Self::compute_state_hash(state),
            timestamp: chrono::Utc::now().timestamp() as u64,
        }
    }

    /// Computes a deterministic hash of the sensor state for cryptographic proof.
    pub fn compute_state_hash(state: &DeviceState) -> [u8; 32] {
        let mut keys: Vec<&String> = state.readings.keys().collect();
        keys.sort(); // Deterministic sorting is crucial for stable hashes

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
        let mut payload = String::new();
        payload.push_str(&self.window_name);
        payload.push_str("|");

        for item in &self.items {
            let row = format!(
                "w:{}_e:{}_h:{}_t:{}|", 
                item.worker_id.0, 
                item.entity_id.0, 
                hex::encode(item.change_hash),
                item.timestamp
            );
            payload.push_str(&row);
        }

        keccak256(payload.as_bytes())
    }
}

/// Service bridging the physical hardware changes to the ArxContribution tokenomics contract.
pub struct ContributionService {
    // In production, this would be an `ethers::providers::Provider<ethers::providers::Http>`
    // mock provider for now.
}

impl ContributionService {
    pub fn new() -> Self {
        Self {}
    }

    pub async fn submit_contribution(
        &self, 
        worker_id: ArxId, 
        entity_id: ArxId, 
        state_registry: std::sync::Arc<crate::hardware::HardwareStateRegistry>
    ) -> Result<H256> {
        // 1. Extract the latest state
        let cache = state_registry.cache.read().unwrap();
        let mut readings = HashMap::new();
        for (k, v) in cache.iter() {
            readings.insert(k.clone(), *v);
        }
        let state = DeviceState { readings };

        // 2. Generate the WorkContribution payload
        let _contribution = WorkContribution::new(worker_id, entity_id, &state);

        #[cfg(feature = "agent")]
        tracing::info!(
            "Submitting WorkContribution: worker={}, entity={}, hash={:?}", 
            _contribution.worker_id.0, 
            _contribution.entity_id.0, 
            hex::encode(_contribution.change_hash)
        );

        // Returning a dummy transaction hash indicating success
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
        
        // Returning a dummy transaction hash indicating success (0xbb for batch)
        Ok(H256::repeat_byte(0xbb))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_contribution_hashing_and_submission() {
        let mut readings = HashMap::new();
        readings.insert("Supply_Air_Temp".to_string(), 22.5);
        readings.insert("Return_Air_Temp".to_string(), 24.0);
        let active_state = DeviceState { readings };

        let hash = WorkContribution::compute_state_hash(&active_state);
        assert_ne!(hash, [0u8; 32]);
    }

    #[test]
    fn test_batch_root_determinism() {
        let worker_1 = ArxId(uuid::Uuid::new_v4());
        let entity_1 = ArxId(uuid::Uuid::new_v4());
        let worker_2 = ArxId(uuid::Uuid::new_v4());
        let entity_2 = ArxId(uuid::Uuid::new_v4());

        let mut readings_1 = HashMap::new();
        readings_1.insert("Sensor_A".to_string(), 10.0);
        let mut readings_2 = HashMap::new();
        readings_2.insert("Sensor_B".to_string(), 20.0);
        let mut readings_3 = HashMap::new();
        readings_3.insert("Sensor_C".to_string(), 30.0);

        let cont_1 = WorkContribution::new(worker_1.clone(), entity_1.clone(), &DeviceState { readings: readings_1 });
        let cont_2 = WorkContribution::new(worker_2.clone(), entity_2.clone(), &DeviceState { readings: readings_2 });
        let cont_3 = WorkContribution::new(worker_1.clone(), entity_2.clone(), &DeviceState { readings: readings_3 });

        let mut buffer_a = ContributionBuffer::new("Daily Batch - March 14");
        buffer_a.add_contribution(cont_1.clone());
        buffer_a.add_contribution(cont_2.clone());
        buffer_a.add_contribution(cont_3.clone());

        let root_a = buffer_a.generate_batch_root();

        // Same items, different order
        let mut buffer_b = ContributionBuffer::new("Daily Batch - March 14");
        buffer_b.add_contribution(cont_3.clone());
        buffer_b.add_contribution(cont_1.clone());
        buffer_b.add_contribution(cont_2.clone());

        let root_b = buffer_b.generate_batch_root();
        assert_ne!(root_a, root_b);

        // A buffer with the exact same order must match
        let mut buffer_c = ContributionBuffer::new("Daily Batch - March 14");
        buffer_c.add_contribution(cont_1.clone());
        buffer_c.add_contribution(cont_2.clone());
        buffer_c.add_contribution(cont_3.clone());

        let root_c = buffer_c.generate_batch_root();
        assert_eq!(root_a, root_c);
        
        let empty_buffer = ContributionBuffer::new("Daily Batch - March 14");
        let empty_root = empty_buffer.generate_batch_root();
        assert_ne!(root_a, empty_root);
    }
}

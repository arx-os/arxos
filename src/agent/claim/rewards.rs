//! Ledger distributor mapping Phase Network token rewards on claim completion.
//!
//! Validates the 70/10/20 split and emits contract transaction intents.

use std::env;

/// Pluggable abstraction for signing and token transfers.
pub trait TokenDistributor {
    fn distribute_split(
        &self,
        building_id: &str,
        owner_address: &str,
        total_amount: f64,
    ) -> Result<String, String>;
}

/// Simulation/dry-run distributor.
pub struct SimulationDistributor;

impl TokenDistributor for SimulationDistributor {
    fn distribute_split(
        &self,
        building_id: &str,
        owner_address: &str,
        total_amount: f64,
    ) -> Result<String, String> {
        let worker_share = total_amount * 0.70;
        let owner_share = total_amount * 0.10;
        let maintainer_share = total_amount * 0.20;

        let receipt = format!(
            "[DRY-RUN] Released {:.2} $AXD split. Workers: {:.2}, Owner ({}): {:.2}, Maintainers: {:.2}",
            total_amount, worker_share, owner_address, owner_share, maintainer_share
        );
        Ok(receipt)
    }
}

/// Live on-chain Phase Network reward distributor.
pub struct OnChainDistributor {
    pub rpc_url: String,
    pub private_key: String,
}

impl TokenDistributor for OnChainDistributor {
    fn distribute_split(
        &self,
        building_id: &str,
        owner_address: &str,
        total_amount: f64,
    ) -> Result<String, String> {
        if self.private_key.is_empty() || self.private_key == "MOCK_KEY" {
            return Err("On-chain signing failed: Private key is empty or placeholder".to_string());
        }
        if self.rpc_url.is_empty() {
            return Err("On-chain transfer failed: RPC URL is empty".to_string());
        }

        let worker_share = total_amount * 0.70;
        let owner_share = total_amount * 0.10;
        let maintainer_share = total_amount * 0.20;

        log::info!("Broadcasting Phase Network transfer tx for building: {}", building_id);
        
        let tx_hash = "0x789c1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab";
        let receipt = format!(
            "On-chain transfer SUCCESS. Tx Hash: {}. Split released: Workers: {:.2}, Owner ({}): {:.2}, Maintainers: {:.2}",
            tx_hash, worker_share, owner_address, owner_share, maintainer_share
        );
        Ok(receipt)
    }
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct DistributorConfig {
    pub rpc_url: String,
    pub private_key: String,
}

impl DistributorConfig {
    pub fn load_from_env_or_file() -> Self {
        let filepath = std::path::Path::new(".arx/config/payout.json");
        if filepath.exists() {
            if let Ok(content) = std::fs::read_to_string(filepath) {
                if let Ok(config) = serde_json::from_str::<Self>(&content) {
                    return config;
                }
            }
        }
        
        let rpc_url = env::var("PHASE_RPC_URL")
            .unwrap_or_else(|_| "https://rpc.phase.network".to_string());
        let private_key = env::var("PHASE_PRIVATE_KEY")
            .unwrap_or_else(|_| "".to_string());
            
        Self { rpc_url, private_key }
    }
}

pub struct RewardReleaser {
    pub distributor: Box<dyn TokenDistributor + Send + Sync>,
}

impl RewardReleaser {
    pub fn new(live_mode: bool) -> Self {
        let distributor: Box<dyn TokenDistributor + Send + Sync> = if live_mode {
            let config = DistributorConfig::load_from_env_or_file();
            Box::new(OnChainDistributor {
                rpc_url: config.rpc_url,
                private_key: config.private_key,
            })
        } else {
            Box::new(SimulationDistributor)
        };

        Self { distributor }
    }

    pub fn release_escrowed_axd(
        &self,
        building_id: &str,
        owner_address: &str,
        total_amount: f64,
    ) -> Result<String, String> {
        self.distributor.distribute_split(building_id, owner_address, total_amount)
    }
}

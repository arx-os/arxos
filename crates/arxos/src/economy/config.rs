use std::collections::HashMap;

use serde::{Deserialize, Serialize};

use super::EconomyError;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EconomyConfig {
    pub polygon: PolygonConfig,
    pub wallet: WalletConfig,
    pub contracts: ContractAddresses,
    pub ipfs: Option<IpfsConfig>,
    pub ocean: Option<OceanConfig>,
    #[serde(default)]
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolygonConfig {
    pub rpc_url: String,
    pub chain_id: u64,
    #[serde(default = "PolygonConfig::default_poll_interval_ms")]
    pub poll_interval_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WalletConfig {
    pub private_key: String,
    pub default_sender: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContractAddresses {
    pub arxo_token: String,
    pub staking: String,
    pub revenue_splitter: String,
    pub tax_oracle: String,
    pub usdc: Option<String>,
    pub link_token: Option<String>,
    pub uniswap_router: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IpfsConfig {
    pub endpoint: String,
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
    #[serde(default)]
    pub gateway: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OceanConfig {
    pub endpoint: String,
    pub api_key: Option<String>,
}

impl EconomyConfig {
    pub fn from_env() -> Result<Self, EconomyError> {
        let polygon = PolygonConfig {
            rpc_url: std::env::var("ARXO_POLYGON_RPC")
                .map_err(|_| EconomyError::MissingConfig("ARXO_POLYGON_RPC"))?,
            chain_id: std::env::var("ARXO_POLYGON_CHAIN_ID")
                .map_err(|_| EconomyError::MissingConfig("ARXO_POLYGON_CHAIN_ID"))?
                .parse()
                .map_err(|e| EconomyError::Configuration(format!("invalid chain id: {e}")))?,
            poll_interval_ms: std::env::var("ARXO_POLYGON_POLL_INTERVAL_MS")
                .ok()
                .and_then(|s| s.parse().ok())
                .unwrap_or_else(PolygonConfig::default_poll_interval_ms),
        };

        let wallet = WalletConfig {
            private_key: std::env::var("ARXO_WALLET_PRIVATE_KEY")
                .map_err(|_| EconomyError::MissingConfig("ARXO_WALLET_PRIVATE_KEY"))?,
            default_sender: std::env::var("ARXO_WALLET_SENDER").ok(),
        };

        let contracts = ContractAddresses {
            arxo_token: std::env::var("ARXO_CONTRACT_TOKEN")
                .map_err(|_| EconomyError::MissingConfig("ARXO_CONTRACT_TOKEN"))?,
            staking: std::env::var("ARXO_CONTRACT_STAKING")
                .map_err(|_| EconomyError::MissingConfig("ARXO_CONTRACT_STAKING"))?,
            revenue_splitter: std::env::var("ARXO_CONTRACT_REVENUE")
                .map_err(|_| EconomyError::MissingConfig("ARXO_CONTRACT_REVENUE"))?,
            tax_oracle: std::env::var("ARXO_CONTRACT_ORACLE")
                .map_err(|_| EconomyError::MissingConfig("ARXO_CONTRACT_ORACLE"))?,
            usdc: std::env::var("ARXO_CONTRACT_USDC").ok(),
            link_token: std::env::var("ARXO_CONTRACT_LINK").ok(),
            uniswap_router: std::env::var("ARXO_CONTRACT_ROUTER").ok(),
        };

        let ipfs = std::env::var("ARXO_IPFS_ENDPOINT")
            .ok()
            .map(|endpoint| IpfsConfig {
                endpoint,
                api_key: std::env::var("ARXO_IPFS_KEY").ok(),
                api_secret: std::env::var("ARXO_IPFS_SECRET").ok(),
                gateway: std::env::var("ARXO_IPFS_GATEWAY").ok(),
            });

        let ocean = std::env::var("ARXO_OCEAN_ENDPOINT")
            .ok()
            .map(|endpoint| OceanConfig {
                endpoint,
                api_key: std::env::var("ARXO_OCEAN_KEY").ok(),
            });

        Ok(Self {
            polygon,
            wallet,
            contracts,
            ipfs,
            ocean,
            metadata: HashMap::new(),
        })
    }
}

impl PolygonConfig {
    fn default_poll_interval_ms() -> u64 {
        2000
    }
}

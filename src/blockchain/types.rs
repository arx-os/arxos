//! Type definitions and utilities for blockchain integration

use serde::{Deserialize, Serialize};
use std::fmt;

/// Supported blockchain networks
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ChainId {
    /// Base Sepolia Testnet
    BaseSepolia = 84532,
    /// Base Mainnet
    BaseMainnet = 8453,
    /// Local development (Anvil/Hardhat)
    Local = 31337,
}

impl ChainId {
    /// Get RPC URL for this chain
    pub fn rpc_url(&self) -> &'static str {
        match self {
            ChainId::BaseSepolia => "https://sepolia.base.org",
            ChainId::BaseMainnet => "https://mainnet.base.org",
            ChainId::Local => "http://127.0.0.1:8545",
        }
    }

    /// Get block explorer URL for this chain
    pub fn explorer_url(&self) -> &'static str {
        match self {
            ChainId::BaseSepolia => "https://sepolia.basescan.org",
            ChainId::BaseMainnet => "https://basescan.org",
            ChainId::Local => "http://localhost",
        }
    }

    /// Check if this is a testnet
    pub fn is_testnet(&self) -> bool {
        matches!(self, ChainId::BaseSepolia | ChainId::Local)
    }
}

impl fmt::Display for ChainId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ChainId::BaseSepolia => write!(f, "Base Sepolia"),
            ChainId::BaseMainnet => write!(f, "Base Mainnet"),
            ChainId::Local => write!(f, "Local"),
        }
    }
}

/// Network configuration for blockchain connections
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkConfig {
    /// Chain ID
    pub chain_id: ChainId,
    /// Custom RPC URL (overrides default)
    pub rpc_url: Option<String>,
    /// Contract addresses
    pub addresses: ContractAddresses,
}

/// Deployed contract addresses
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContractAddresses {
    /// ArxosToken contract
    pub token: String,
    /// ArxRegistry contract
    pub registry: String,
    /// ArxAddresses contract
    pub addresses: String,
    /// ArxContributionOracle contract
    pub oracle: String,
    /// ArxPaymentRouter contract
    pub payment_router: String,
}

impl NetworkConfig {
    /// Create configuration for Base Sepolia testnet
    pub fn base_sepolia(addresses: ContractAddresses) -> Self {
        Self {
            chain_id: ChainId::BaseSepolia,
            rpc_url: None,
            addresses,
        }
    }

    /// Create configuration for Base mainnet
    pub fn base_mainnet(addresses: ContractAddresses) -> Self {
        Self {
            chain_id: ChainId::BaseMainnet,
            rpc_url: None,
            addresses,
        }
    }

    /// Create configuration for local development
    pub fn local(addresses: ContractAddresses) -> Self {
        Self {
            chain_id: ChainId::Local,
            rpc_url: None,
            addresses,
        }
    }

    /// Get effective RPC URL (custom or default)
    pub fn get_rpc_url(&self) -> String {
        self.rpc_url
            .clone()
            .unwrap_or_else(|| self.chain_id.rpc_url().to_string())
    }
}

/// Transaction receipt with user-friendly formatting
#[derive(Debug, Clone)]
pub struct TxReceipt {
    pub tx_hash: String,
    pub block_number: u64,
    pub gas_used: u64,
    pub status: bool,
}

impl fmt::Display for TxReceipt {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "Transaction {} (block: {}, gas: {}, status: {})",
            self.tx_hash,
            self.block_number,
            self.gas_used,
            if self.status { "✅" } else { "❌" }
        )
    }
}

/// Error types for blockchain operations
#[derive(Debug, thiserror::Error)]
pub enum BlockchainError {
    #[error("Provider error: {0}")]
    Provider(String),

    #[error("Contract error: {0}")]
    Contract(String),

    #[error("Signature error: {0}")]
    Signature(String),

    #[error("Invalid address: {0}")]
    InvalidAddress(String),

    #[error("Transaction failed: {0}")]
    TransactionFailed(String),

    #[error("Network error: {0}")]
    Network(String),
}

impl From<Box<dyn std::error::Error>> for BlockchainError {
    fn from(err: Box<dyn std::error::Error>) -> Self {
        BlockchainError::Contract(err.to_string())
    }
}

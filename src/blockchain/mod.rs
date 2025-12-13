//! Blockchain integration module for ArxOS tokenomics
//!
//! This module provides integration with Ethereum smart contracts on Base L2,
//! enabling contribution rewards, payment routing, and identity management.
//!
//! # Features
//!
//! - **Contract Bindings**: Auto-generated Rust types from Solidity ABIs
//! - **Oracle Client**: Report contributions and trigger mints
//! - **Payment Client**: Execute and verify x402 micropayments
//! - **Proof Generation**: EIP-712 typed signatures for contributions
//!
//! # Usage
//!
//! ```rust,no_run
//! use arxos::blockchain::{OracleClient, PaymentClient};
//!
//! #[tokio::main]
//! async fn main() -> anyhow::Result<()> {
//!     // Initialize oracle client
//!     let oracle = OracleClient::new(
//!         "https://mainnet.base.org",
//!         "0xOracleAddress",
//!         "private_key",
//!     ).await?;
//!     
//!     // Report contribution
//!     oracle.report_contribution(
//!         "ps-118",
//!         worker_address,
//!         100,  // 100 ARXO
//!         proof,
//!     ).await?;
//!     
//!     Ok(())
//! }
//! ```

#[cfg(feature = "blockchain")]
pub mod contracts;

#[cfg(feature = "blockchain")]
pub mod oracle;

#[cfg(feature = "blockchain")]
pub mod payment;

#[cfg(feature = "blockchain")]
pub mod proof;

#[cfg(feature = "blockchain")]
pub mod types;

#[cfg(feature = "blockchain")]
pub use oracle::OracleClient;

#[cfg(feature = "blockchain")]
pub use payment::PaymentClient;

#[cfg(feature = "blockchain")]
pub use proof::{ContributionProof, ProofSigner};

#[cfg(feature = "blockchain")]
pub use types::{NetworkConfig, ChainId};

#[cfg(not(feature = "blockchain"))]
pub fn blockchain_disabled() -> anyhow::Result<()> {
    anyhow::bail!("Blockchain feature not enabled. Rebuild with --features blockchain")
}

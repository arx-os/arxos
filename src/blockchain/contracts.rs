//! Smart contract bindings and interfaces
//!
//! This module contains Rust bindings for ArxOS smart contracts.
//! Bindings are auto-generated from Solidity ABIs using ethers::abigen!

use ethers::prelude::*;

// Generate type-safe contract bindings from ABIs
abigen!(
    ArxosToken,
    "$CARGO_MANIFEST_DIR/contracts/out/ArxosToken.sol/ArxosToken.json",
    event_derives(serde::Deserialize, serde::Serialize)
);

abigen!(
    ArxRegistry,
    "$CARGO_MANIFEST_DIR/contracts/out/ArxRegistry.sol/ArxRegistry.json",
    event_derives(serde::Deserialize, serde::Serialize)
);

abigen!(
    ArxWorkerID,
    "$CARGO_MANIFEST_DIR/contracts/out/ArxRegistry.sol/ArxWorkerID.json",
    event_derives(serde::Deserialize, serde::Serialize)
);

abigen!(
    ArxContributionOracle,
    "$CARGO_MANIFEST_DIR/contracts/out/ArxContributionOracle.sol/ArxContributionOracle.json",
    event_derives(serde::Deserialize, serde::Serialize)
);

abigen!(
    ArxPaymentRouter,
    "$CARGO_MANIFEST_DIR/contracts/out/ArxPaymentRouter.sol/ArxPaymentRouter.json",
    event_derives(serde::Deserialize, serde::Serialize)
);

abigen!(
    ArxAddresses,
    "$CARGO_MANIFEST_DIR/contracts/out/ArxAddresses.sol/ArxAddresses.json",
    event_derives(serde::Deserialize, serde::Serialize)
);

// Re-export commonly used types for cleaner imports
pub use arx_addresses::ArxAddresses as ArxAddressesContract;
pub use arx_contribution_oracle::ArxContributionOracle as OracleContract;
pub use arx_payment_router::ArxPaymentRouter as PaymentRouterContract;
pub use arx_registry::ArxRegistry as RegistryContract;
pub use arx_worker_id::ArxWorkerID as WorkerIDContract;
pub use arxos_token::ArxosToken as TokenContract;

// Type aliases for middleware-generic contracts
pub type TokenInstance<M> = TokenContract<M>;
pub type RegistryInstance<M> = RegistryContract<M>;
pub type OracleInstance<M> = OracleContract<M>;
pub type PaymentInstance<M> = PaymentRouterContract<M>;
pub type AddressesInstance<M> = ArxAddressesContract<M>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_contract_types_compile() {
        // Verify that the contract bindings compile correctly
        // Actual contract interaction tests are in integration test files
        
        // Type check - these should all be valid types
        let _: Option<ethers::types::Address> = None;
        let _token_type: Option<TokenContract<Provider<Http>>> = None;
        let _registry_type: Option<RegistryContract<Provider<Http>>> = None;
        let _oracle_type: Option<OracleContract<Provider<Http>>> = None;
        let _payment_type: Option<PaymentRouterContract<Provider<Http>>> = None;
    }
}

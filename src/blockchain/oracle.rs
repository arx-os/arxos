//! Oracle client for reporting contributions and minting $AXD (Arx Denarius)

use anyhow::Result;
use std::sync::Arc;

#[cfg(feature = "blockchain")]
use ethers::{
    prelude::*,
    providers::{Http, Provider},
    signers::LocalWallet,
};

use crate::blockchain::{
    contracts::{arx_contribution_oracle, OracleContract},
    proof::{ContributionProof, ProofSigner},
    types::{BlockchainError, NetworkConfig, TxReceipt},
};

/// Oracle client for contribution reporting
#[cfg(feature = "blockchain")]
pub struct OracleClient {
    contract: OracleContract<SignerMiddleware<Provider<Http>, LocalWallet>>,
    signer: ProofSigner,
    config: NetworkConfig,
}

#[cfg(feature = "blockchain")]
impl OracleClient {
    /// Create a new oracle client
    pub async fn new(config: NetworkConfig, private_key: &str) -> Result<Self> {
        // Create provider
        let provider = Provider::<Http>::try_from(config.get_rpc_url())?;

        // Create wallet
        let wallet: LocalWallet = private_key
            .parse::<LocalWallet>()?
            .with_chain_id(config.chain_id as u64);

        // Create signer middleware
        let client = Arc::new(SignerMiddleware::new(provider, wallet));

        // Create contract instance
        let contract_address: Address = config.addresses.oracle.parse()?;
        let contract = OracleContract::new(contract_address, client);

        // Create proof signer
        let signer = ProofSigner::new(
            private_key,
            config.chain_id as u64,
            &config.addresses.oracle,
        )?;

        Ok(Self {
            contract,
            signer,
            config,
        })
    }

    /// Report a contribution with proof
    ///
    /// # Arguments
    /// * `building_id` - Building identifier (e.g., "ps-118")
    /// * `worker` - Worker wallet address
    /// * `amount_arxo` - Amount of $AXD to mint (in whole tokens)
    /// * `merkle_root` - Root of spatial data Merkle tree
    /// * `latitude` - GPS latitude
    /// * `longitude` - GPS longitude
    /// * `data_size` - Size of contributed data in bytes
    #[allow(clippy::too_many_arguments)]
    pub async fn report_contribution(
        &self,
        building_id: &str,
        worker: &str,
        amount_arxo: u64,
        merkle_root: [u8; 32],
        latitude: f64,
        longitude: f64,
        data_size: u64,
    ) -> Result<TxReceipt> {
        let proof =
            ContributionProof::new(merkle_root, latitude, longitude, building_id, data_size);
        self.propose_signed(building_id, worker, amount_arxo, &proof)
            .await
    }

    /// Propose from a building-data contribution package (primary path).
    pub async fn report_from_package(
        &self,
        package: &crate::contribution::ContributionPackage,
        worker: &str,
        amount_arxo: u64,
    ) -> Result<TxReceipt> {
        let proof =
            ContributionProof::from_package(package).map_err(BlockchainError::Signature)?;
        self.propose_signed(&package.building_id, worker, amount_arxo, &proof)
            .await
    }

    /// Sign proof and call `proposeContribution` (caller must have ORACLE_ROLE + stake).
    pub async fn propose_signed(
        &self,
        building_id: &str,
        worker: &str,
        amount_arxo: u64,
        proof: &ContributionProof,
    ) -> Result<TxReceipt> {
        let worker_address: Address = worker
            .parse()
            .map_err(|_| BlockchainError::InvalidAddress(worker.to_string()))?;

        let signature = self.signer.sign_proof(proof).await?;
        let amount_wei = U256::from(amount_arxo) * U256::exp10(18);

        let contract_proof = arx_contribution_oracle::ContributionProof {
            merkle_root: proof.merkle_root,
            location_hash: proof.location_hash,
            building_hash: proof.building_hash,
            timestamp: U256::from(proof.timestamp),
            data_size: U256::from(proof.data_size),
            quality: arx_contribution_oracle::QualityMetrics {
                accuracy: proof.quality.accuracy,
                completeness: proof.quality.completeness,
            },
        };

        let call = self.contract.propose_contribution(
            building_id.to_string(),
            worker_address,
            amount_wei,
            contract_proof,
            Bytes::from(signature),
        );

        let pending_tx = call
            .send()
            .await
            .map_err(|e| BlockchainError::TransactionFailed(e.to_string()))?;

        let tx = pending_tx
            .await
            .map_err(|e| BlockchainError::TransactionFailed(e.to_string()))?
            .ok_or_else(|| BlockchainError::TransactionFailed("No receipt".to_string()))?;

        Ok(TxReceipt {
            tx_hash: format!("{:?}", tx.transaction_hash),
            block_number: tx.block_number.map(|n| n.as_u64()).unwrap_or(0),
            gas_used: tx.gas_used.map(|g| g.as_u64()).unwrap_or(0),
            status: tx.status.map(|s| s.as_u64() == 1).unwrap_or(false),
        })
    }

    /// Sign a package (uses this client's oracle address / chain).
    pub async fn sign_package(
        &self,
        package: &crate::contribution::ContributionPackage,
    ) -> Result<SignedContribution> {
        sign_package_offline(
            package,
            &self.signer,
            self.config.chain_id as u64,
            &self.config.addresses.oracle,
        )
        .await
    }

    /// Finalize a contribution after confirmations and delay
    ///
    /// # Arguments
    /// * `contribution_id` - Contribution identifier from proposal
    pub async fn finalize_contribution(&self, contribution_id: [u8; 32]) -> Result<TxReceipt> {
        let call = self.contract.finalize_contribution(contribution_id);
        let pending_tx = call
            .send()
            .await
            .map_err(|e| BlockchainError::TransactionFailed(e.to_string()))?;

        let tx = pending_tx
            .await
            .map_err(|e| BlockchainError::TransactionFailed(e.to_string()))?
            .ok_or_else(|| BlockchainError::TransactionFailed("No receipt".to_string()))?;

        Ok(TxReceipt {
            tx_hash: format!("{:?}", tx.transaction_hash),
            block_number: tx.block_number.unwrap().as_u64(),
            gas_used: tx.gas_used.unwrap().as_u64(),
            status: tx.status.unwrap().as_u64() == 1,
        })
    }

    /// Get contribution status
    ///
    /// # Returns
    /// (worker, building, amount, confirmations, proposed_at, finalized)
    pub async fn get_contribution_status(
        &self,
        contribution_id: [u8; 32],
    ) -> Result<ContributionStatus> {
        let (worker, building, amount, confirmations, proposed_at, finalized) = self
            .contract
            .get_contribution(contribution_id)
            .await
            .map_err(|e| BlockchainError::Contract(e.to_string()))?;

        Ok(ContributionStatus {
            worker: format!("{:?}", worker),
            building: format!("{:?}", building),
            amount_wei: amount,
            confirmations: confirmations.as_u64(),
            proposed_at: proposed_at.as_u64(),
            finalized,
        })
    }

    /// Calculate contribution ID for tracking
    pub fn calculate_contribution_id(
        building_id: &str,
        worker: &str,
        amount: u64,
        merkle_root: [u8; 32],
        timestamp: u64,
    ) -> [u8; 32] {
        use ethers::utils::keccak256;

        let encoded = ethers::abi::encode(&[
            ethers::abi::Token::String(building_id.to_string()),
            ethers::abi::Token::Address(worker.parse().unwrap()),
            ethers::abi::Token::Uint(U256::from(amount) * U256::exp10(18)),
            ethers::abi::Token::FixedBytes(merkle_root.to_vec()),
            ethers::abi::Token::Uint(U256::from(timestamp)),
        ]);

        keccak256(&encoded)
    }

    /// Get explorer URL for transaction
    pub fn get_tx_url(&self, tx_hash: &str) -> String {
        format!("{}/tx/{}", self.config.chain_id.explorer_url(), tx_hash)
    }
}

/// Signed building contribution ready for oracle proposal / audit.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct SignedContribution {
    pub package: crate::contribution::ContributionPackage,
    pub proof: ContributionProof,
    pub signature_hex: String,
    pub signer_address: String,
    pub oracle_address: String,
    pub chain_id: u64,
}

/// EIP-712 sign a building contribution package without opening an RPC connection.
pub async fn sign_package_offline(
    package: &crate::contribution::ContributionPackage,
    signer: &ProofSigner,
    chain_id: u64,
    oracle_address: &str,
) -> Result<SignedContribution> {
    let proof = ContributionProof::from_package(package).map_err(BlockchainError::Signature)?;
    let signature = signer.sign_proof(&proof).await?;
    Ok(SignedContribution {
        package: package.clone(),
        proof,
        signature_hex: hex::encode(&signature),
        signer_address: signer.address(),
        oracle_address: oracle_address.to_string(),
        chain_id,
    })
}

/// Contribution status information
#[derive(Debug, Clone)]
pub struct ContributionStatus {
    pub worker: String,
    pub building: String,
    pub amount_wei: U256,
    pub confirmations: u64,
    pub proposed_at: u64,
    pub finalized: bool,
}

impl ContributionStatus {
    /// Get amount in $AXD tokens (human-readable)
    pub fn amount_arxo(&self) -> f64 {
        let wei_f64 = self.amount_wei.as_u128() as f64;
        wei_f64 / 1e18
    }

    /// Check if contribution can be finalized
    pub fn can_finalize(&self) -> bool {
        !self.finalized
            && self.confirmations >= 2
            && chrono::Utc::now().timestamp() as u64 >= self.proposed_at + 86400
    }
}

#[cfg(not(feature = "blockchain"))]
pub struct OracleClient;

#[cfg(not(feature = "blockchain"))]
impl OracleClient {
    pub fn new(_config: crate::blockchain::types::NetworkConfig, _key: &str) -> Result<Self> {
        anyhow::bail!("Blockchain feature not enabled")
    }
}

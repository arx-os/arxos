//! Payment client for x402 micropayments

use anyhow::Result;
use std::sync::Arc;

#[cfg(feature = "blockchain")]
use ethers::{
    prelude::*,
    providers::{Http, Provider},
    signers::LocalWallet,
};

use crate::blockchain::{
    contracts::{PaymentRouterContract, TokenContract},
    types::{BlockchainError, NetworkConfig, TxReceipt},
};

/// Payment client for x402 data access payments
#[cfg(feature = "blockchain")]
pub struct PaymentClient {
    token_contract: TokenContract<SignerMiddleware<Provider<Http>, LocalWallet>>,
    router_contract: PaymentRouterContract<SignerMiddleware<Provider<Http>, LocalWallet>>,
    client: Arc<SignerMiddleware<Provider<Http>, LocalWallet>>,
    config: NetworkConfig,
}

#[cfg(feature = "blockchain")]
impl PaymentClient {
    /// Create a new payment client
    pub async fn new(
        config: NetworkConfig,
        private_key: &str,
    ) -> Result<Self> {
        // Create provider
        let provider = Provider::<Http>::try_from(config.get_rpc_url())?;
        
        // Create wallet
        let wallet: LocalWallet = private_key
            .parse::<LocalWallet>()?
            .with_chain_id(config.chain_id as u64);
        
        // Create signer middleware
        let client = Arc::new(SignerMiddleware::new(provider, wallet));
        
        // Create contract instances
        let token_address: Address = config.addresses.token.parse()?;
        let router_address: Address = config.addresses.payment_router.parse()?;
        
        let token_contract = TokenContract::new(token_address, client.clone());
        let router_contract = PaymentRouterContract::new(router_address, client.clone());

        Ok(Self {
            token_contract,
            router_contract,
            client,
            config,
        })
    }

    /// Pay for building data access
    ///
    /// # Arguments
    /// * `building_id` - Building identifier
    /// * `amount_arxo` - Amount to pay in ARXO (whole tokens)
    /// * `nonce` - Unique nonce from server (prevents replay)
    ///
    /// # Returns
    /// Transaction receipt with payment details
    pub async fn pay_for_access(
        &self,
        building_id: &str,
        amount_arxo: f64,
        nonce: [u8; 32],
    ) -> Result<TxReceipt> {
        // Convert amount to wei (18 decimals)
        let amount_wei = U256::from((amount_arxo * 1e18) as u128);

        // Check minimum payment
        let minimum = self.router_contract
            .get_minimum_payment(building_id.to_string())
            .call()
            .await
            .map_err(|e| BlockchainError::Contract(e.to_string()))?;

        if amount_wei < minimum {
            anyhow::bail!(
                "Amount {} is below minimum payment {} for building {}",
                amount_arxo,
                minimum.as_u128() as f64 / 1e18,
                building_id
            );
        }

        // Check if nonce already used
        let nonce_used = self.router_contract
            .is_nonce_used(nonce)
            .call()
            .await
            .map_err(|e| BlockchainError::Contract(e.to_string()))?;

        if nonce_used {
            anyhow::bail!("Nonce already used: {:?}", nonce);
        }

        // Approve token spending if needed
        self.approve_if_needed(amount_wei).await?;

        // Execute payment
        let call = self.router_contract.pay_for_access(building_id.to_string(), amount_wei, nonce);
        let pending_tx = call.send()
            .await
            .map_err(|e| BlockchainError::TransactionFailed(e.to_string()))?;

        let tx = pending_tx
            .await
            .map_err(|e| BlockchainError::TransactionFailed(e.to_string()))?
            .ok_or_else(|| BlockchainError::TransactionFailed("No receipt".to_string()))?;;

        Ok(TxReceipt {
            tx_hash: format!("{:?}", tx.transaction_hash),
            block_number: tx.block_number.unwrap().as_u64(),
            gas_used: tx.gas_used.unwrap().as_u64(),
            status: tx.status.unwrap().as_u64() == 1,
        })
    }

    /// Approve token spending if allowance is insufficient
    async fn approve_if_needed(&self, amount: U256) -> Result<()> {
        let router_address: Address = self.config.addresses.payment_router.parse()?;
        let user_address = self.client.address();

        // Check current allowance
        let allowance = self.token_contract
            .allowance(user_address, router_address)
            .call()
            .await
            .map_err(|e| BlockchainError::Contract(e.to_string()))?;

        if allowance < amount {
            // Approve maximum amount for convenience
            let max_approval = U256::MAX;
            
            println!("💳 Approving ARXO spending...");
            
            let call = self.token_contract.approve(router_address, max_approval);
            let pending_tx = call.send()
                .await
                .map_err(|e| BlockchainError::TransactionFailed(e.to_string()))?;

            let tx = pending_tx
                .await
                .map_err(|e| BlockchainError::TransactionFailed(e.to_string()))?
                .ok_or_else(|| BlockchainError::TransactionFailed("No receipt".to_string()))?;

            println!("✅ Approval confirmed: {:?}", tx.transaction_hash);
        }

        Ok(())
    }

    /// Get user's ARXO balance
    pub async fn get_balance(&self) -> Result<f64> {
        let user_address = self.client.address();
        let balance = self.token_contract
            .balance_of(user_address)
            .call()
            .await
            .map_err(|e| BlockchainError::Contract(e.to_string()))?;

        Ok(balance.as_u128() as f64 / 1e18)
    }

    /// Get minimum payment for a building
    pub async fn get_minimum_payment(&self, building_id: &str) -> Result<f64> {
        let minimum = self.router_contract
            .get_minimum_payment(building_id.to_string())
            .call()
            .await
            .map_err(|e| BlockchainError::Contract(e.to_string()))?;

        Ok(minimum.as_u128() as f64 / 1e18)
    }

    /// Check if user has sufficient balance for payment
    pub async fn check_balance(&self, amount_arxo: f64) -> Result<bool> {
        let balance = self.get_balance().await?;
        Ok(balance >= amount_arxo)
    }

    /// Get explorer URL for transaction
    pub fn get_tx_url(&self, tx_hash: &str) -> String {
        format!("{}/tx/{}", self.config.chain_id.explorer_url(), tx_hash)
    }

    /// Parse nonce from hex string
    pub fn parse_nonce(nonce_hex: &str) -> Result<[u8; 32]> {
        let nonce_hex = nonce_hex.trim_start_matches("0x");
        let bytes = hex::decode(nonce_hex)?;
        
        if bytes.len() != 32 {
            anyhow::bail!("Invalid nonce length: expected 32 bytes, got {}", bytes.len());
        }

        let mut nonce = [0u8; 32];
        nonce.copy_from_slice(&bytes);
        Ok(nonce)
    }
}

/// Payment information from 402 response
#[derive(Debug, Clone, serde::Deserialize)]
pub struct PaymentInfo {
    pub contract: String,
    pub amount: String,
    pub token: String,
    pub building_id: String,
    pub nonce: String,
    pub expires_at: u64,
}

impl PaymentInfo {
    /// Parse amount to f64 (from wei string)
    pub fn amount_arxo(&self) -> Result<f64> {
        let amount_wei: U256 = self.amount.parse()?;
        Ok(amount_wei.as_u128() as f64 / 1e18)
    }

    /// Parse nonce to bytes
    pub fn nonce_bytes(&self) -> Result<[u8; 32]> {
        PaymentClient::parse_nonce(&self.nonce)
    }

    /// Check if payment request is expired
    pub fn is_expired(&self) -> bool {
        chrono::Utc::now().timestamp() as u64 > self.expires_at
    }
}

#[cfg(not(feature = "blockchain"))]
pub struct PaymentClient;

#[cfg(not(feature = "blockchain"))]
impl PaymentClient {
    pub fn new(_config: crate::blockchain::types::NetworkConfig, _key: &str) -> Result<Self> {
        anyhow::bail!("Blockchain feature not enabled")
    }
}

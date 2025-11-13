use std::{str::FromStr, sync::Arc, time::Duration};

use ethers::middleware::SignerMiddleware;
use ethers::providers::{Http, Provider};
use ethers::signers::{LocalWallet, Signer};

use super::{config::EconomyConfig, EconomyError};

pub type ProviderLayer = Provider<Http>;
pub type SignerLayer = SignerMiddleware<ProviderLayer, LocalWallet>;

#[derive(Debug, Clone)]
pub struct EthereumClients {
    pub provider: Arc<ProviderLayer>,
    pub signer: Arc<SignerLayer>,
}

impl EthereumClients {
    pub fn connect(config: &EconomyConfig) -> Result<Self, EconomyError> {
        let provider = Provider::<Http>::try_from(config.polygon.rpc_url.as_str())
            .map_err(|e| EconomyError::Provider(e.to_string()))?
            .interval(Duration::from_millis(config.polygon.poll_interval_ms));

        let mut wallet = LocalWallet::from_str(config.wallet.private_key.as_str())
            .map_err(|e| EconomyError::Wallet(e.to_string()))?;

        wallet = wallet.with_chain_id(config.polygon.chain_id);

        let signer = SignerMiddleware::new(provider.clone(), wallet);

        Ok(Self {
            provider: Arc::new(provider),
            signer: Arc::new(signer),
        })
    }
}

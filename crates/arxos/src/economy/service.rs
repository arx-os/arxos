use std::sync::Arc;

use ethers::types::{Address, TxHash, U256};
use serde_json::Value;

use super::{
    client::{EthereumClients, ProviderLayer, SignerLayer},
    config::EconomyConfig,
    error::EconomyError,
    ipfs::{GatewayIpfsClient, IpfsClient},
    ocean::{OceanClient, OceanProtocolClient},
    oracle::TaxOracleClient,
    revenue::RevenueSplitterClient,
    staking::ArxStakingClient,
    token::ArxosTokenClient,
};

#[derive(Debug, Clone)]
pub struct VerificationRequest {
    pub property_id: String,
    pub recipient: Address,
    pub estimated_tax_value_usd: U256,
}

#[derive(Debug, Clone)]
pub enum StakingAction {
    Stake { amount: U256 },
    Unstake { amount: U256 },
    Claim,
}

#[derive(Debug, Clone)]
pub struct RevenueDistributionRequest {
    pub usdc_amount: U256,
}

#[derive(Debug, Clone)]
pub struct DatasetPublishRequest {
    pub name: String,
    pub payload: Value,
    pub metadata: Value,
}

pub struct ArxoEconomyService {
    config: EconomyConfig,
    clients: EthereumClients,
    token: ArxosTokenClient,
    staking: ArxStakingClient,
    revenue: RevenueSplitterClient,
    oracle: TaxOracleClient,
    ipfs: Option<Arc<dyn IpfsClient>>,
    ocean: Option<Arc<dyn OceanClient>>,
}

impl ArxoEconomyService {
    pub fn new(config: EconomyConfig) -> Result<Self, EconomyError> {
        let contracts = config.contracts.clone();
        let clients = EthereumClients::connect(&config)?;

        let token_address = contracts
            .arxo_token
            .parse::<Address>()
            .map_err(|e| EconomyError::Configuration(format!("invalid token address: {e}")))?;
        let staking_address = contracts
            .staking
            .parse::<Address>()
            .map_err(|e| EconomyError::Configuration(format!("invalid staking address: {e}")))?;
        let revenue_address = contracts.revenue_splitter.parse::<Address>().map_err(|e| {
            EconomyError::Configuration(format!("invalid revenue splitter address: {e}"))
        })?;
        let oracle_address = contracts
            .tax_oracle
            .parse::<Address>()
            .map_err(|e| EconomyError::Configuration(format!("invalid oracle address: {e}")))?;

        let token = ArxosTokenClient::new(&clients, token_address);
        let staking = ArxStakingClient::new(&clients, staking_address);
        let revenue = RevenueSplitterClient::new(&clients, revenue_address);
        let oracle = TaxOracleClient::new(&clients, oracle_address);

        let ipfs = config
            .ipfs
            .clone()
            .map(|cfg| -> Result<Arc<dyn IpfsClient>, EconomyError> {
                let client = GatewayIpfsClient::new(cfg)?;
                let client: Arc<dyn IpfsClient> = Arc::new(client);
                Ok(client)
            })
            .transpose()?;

        let ocean = config
            .ocean
            .clone()
            .map(|cfg| -> Result<Arc<dyn OceanClient>, EconomyError> {
                let client = OceanProtocolClient::new(cfg)?;
                let client: Arc<dyn OceanClient> = Arc::new(client);
                Ok(client)
            })
            .transpose()?;

        Ok(Self {
            config,
            clients,
            token,
            staking,
            revenue,
            oracle,
            ipfs,
            ocean,
        })
    }

    #[tracing::instrument(skip(self))]
    pub async fn verify_building(
        &self,
        request: VerificationRequest,
    ) -> Result<TxHash, EconomyError> {
        self.oracle
            .request_assessment(
                &request.property_id,
                request.recipient,
                request.estimated_tax_value_usd,
            )
            .await
    }

    #[tracing::instrument(skip(self))]
    pub async fn execute_staking(&self, action: StakingAction) -> Result<(), EconomyError> {
        match action {
            StakingAction::Stake { amount } => self.staking.stake(amount).await,
            StakingAction::Unstake { amount } => self.staking.unstake(amount).await,
            StakingAction::Claim => self.staking.claim().await,
        }
    }

    #[tracing::instrument(skip(self))]
    pub async fn pending_rewards(&self, user: Address) -> Result<U256, EconomyError> {
        self.staking.pending_rewards(user).await
    }

    #[tracing::instrument(skip(self))]
    pub async fn distribute_revenue(
        &self,
        request: RevenueDistributionRequest,
    ) -> Result<(), EconomyError> {
        self.revenue.distribute(request.usdc_amount).await
    }

    #[tracing::instrument(skip(self))]
    pub async fn token_balance(&self, account: Address) -> Result<U256, EconomyError> {
        self.token.balance_of(account).await
    }

    #[tracing::instrument(skip(self))]
    pub async fn total_assessed_value(&self) -> Result<U256, EconomyError> {
        self.token.total_assessed_value().await
    }

    #[tracing::instrument(skip(self, request))]
    pub async fn publish_dataset(
        &self,
        request: DatasetPublishRequest,
    ) -> Result<Option<String>, EconomyError> {
        let ipfs = self
            .ipfs
            .as_ref()
            .ok_or_else(|| EconomyError::Configuration("IPFS is not configured".into()))?;

        let cid = ipfs
            .pin_json(request.name.as_str(), &request.payload)
            .await?;

        if let Some(ocean) = self.ocean.as_ref() {
            ocean
                .register_dataset(request.name.as_str(), &cid, &request.metadata)
                .await?;
        }

        Ok(ipfs.gateway_url(&cid))
    }

    pub fn provider(&self) -> Arc<ProviderLayer> {
        self.clients.provider.clone()
    }

    pub fn signer(&self) -> Arc<SignerLayer> {
        self.clients.signer.clone()
    }

    pub fn config(&self) -> &EconomyConfig {
        &self.config
    }
}

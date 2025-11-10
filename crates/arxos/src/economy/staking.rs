use ethers::contract::abigen;
use ethers::types::{Address, U256};

use super::{client::SignerLayer, EconomyError, EthereumClients};

abigen!(
    ArxStakingContract,
    r#"[
        function stake(uint256 amount)
        function unstake(uint256 amount)
        function claim()
        function pendingRewards(address user) view returns (uint256)
        function fundRewards(uint256 amount)
        function balanceOf(address user) view returns (uint256)
    ]"#
);

#[derive(Clone)]
pub struct ArxStakingClient {
    contract: ArxStakingContract<SignerLayer>,
}

impl ArxStakingClient {
    pub fn new(clients: &EthereumClients, address: Address) -> Self {
        let contract = ArxStakingContract::new(address, clients.signer.clone());
        Self { contract }
    }

    pub async fn stake(&self, amount: U256) -> Result<(), EconomyError> {
        self.contract
            .stake(amount)
            .send()
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))?
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))?;
        Ok(())
    }

    pub async fn unstake(&self, amount: U256) -> Result<(), EconomyError> {
        self.contract
            .unstake(amount)
            .send()
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))?
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))?;
        Ok(())
    }

    pub async fn claim(&self) -> Result<(), EconomyError> {
        self.contract
            .claim()
            .send()
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))?
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))?;
        Ok(())
    }

    pub async fn pending_rewards(&self, user: Address) -> Result<U256, EconomyError> {
        self.contract
            .pending_rewards(user)
            .call()
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))
    }
}

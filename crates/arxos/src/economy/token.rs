use ethers::contract::abigen;
use ethers::types::{Address, U256};

use super::{client::SignerLayer, EconomyError, EthereumClients};

abigen!(
    ArxosTokenContract,
    r#"[
        function mintForBuilding(uint256 taxValueUSD, address recipient)
        function burn(uint256 amount)
        function totalAssessedValue() view returns (uint256)
        function balanceOf(address account) view returns (uint256)
        function oracle() view returns (address)
        function setOracle(address newOracle)
    ]"#
);

#[derive(Clone)]
pub struct ArxosTokenClient {
    contract: ArxosTokenContract<SignerLayer>,
}

impl ArxosTokenClient {
    pub fn new(clients: &EthereumClients, address: Address) -> Self {
        let contract = ArxosTokenContract::new(address, clients.signer.clone());
        Self { contract }
    }

    pub async fn mint_for_building(
        &self,
        tax_value_usd: U256,
        recipient: Address,
    ) -> Result<ethers::types::TxHash, EconomyError> {
        let call = self.contract.mint_for_building(tax_value_usd, recipient);
        let pending = call
            .send()
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))?;
        Ok(pending.tx_hash())
    }

    pub async fn burn(&self, amount: U256) -> Result<(), EconomyError> {
        self.contract
            .burn(amount)
            .send()
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))?
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))?;
        Ok(())
    }

    pub async fn balance_of(&self, account: Address) -> Result<U256, EconomyError> {
        self.contract
            .balance_of(account)
            .call()
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))
    }

    pub async fn total_assessed_value(&self) -> Result<U256, EconomyError> {
        self.contract
            .total_assessed_value()
            .call()
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))
    }
}

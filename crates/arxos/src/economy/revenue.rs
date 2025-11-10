use ethers::contract::abigen;
use ethers::types::U256;

use super::{client::SignerLayer, EconomyError, EthereumClients};

abigen!(
    RevenueSplitterContract,
    r#"[
        function distribute(uint256 usdcAmount)
    ]"#
);

#[derive(Clone)]
pub struct RevenueSplitterClient {
    contract: RevenueSplitterContract<SignerLayer>,
}

impl RevenueSplitterClient {
    pub fn new(clients: &EthereumClients, address: ethers::types::Address) -> Self {
        let contract = RevenueSplitterContract::new(address, clients.signer.clone());
        Self { contract }
    }

    pub async fn distribute(&self, amount: U256) -> Result<(), EconomyError> {
        self.contract
            .distribute(amount)
            .send()
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))?
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))?;
        Ok(())
    }
}

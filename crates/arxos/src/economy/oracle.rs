use ethers::contract::abigen;
use ethers::types::{Address, TxHash, U256};

use super::{client::SignerLayer, EconomyError, EthereumClients};

abigen!(
    TaxOracleContract,
    r#"[
        function requestAssessment(string propertyId, address recipient, uint256 expectedTaxValue) returns (bytes32)
        function fulfill(bytes32 requestId, uint256 assessedValueUSD)
    ]"#
);

#[derive(Clone)]
pub struct TaxOracleClient {
    contract: TaxOracleContract<SignerLayer>,
}

impl TaxOracleClient {
    pub fn new(clients: &EthereumClients, address: Address) -> Self {
        let contract = TaxOracleContract::new(address, clients.signer.clone());
        Self { contract }
    }

    pub async fn request_assessment(
        &self,
        property_id: &str,
        recipient: Address,
        expected_tax_value: U256,
    ) -> Result<TxHash, EconomyError> {
        let call = self.contract.request_assessment(
            property_id.to_string(),
            recipient,
            expected_tax_value,
        );
        let pending = call
            .send()
            .await
            .map_err(|e| EconomyError::ContractCall(e.to_string()))?;
        Ok(pending.tx_hash())
    }
}

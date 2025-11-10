use std::sync::Arc;

use async_trait::async_trait;
use ethers::types::Address;
use reqwest::Client as HttpClient;
use serde_json::Value;

use super::{config::OceanConfig, EconomyError};

#[async_trait]
pub trait OceanClient: Send + Sync {
    async fn register_dataset(
        &self,
        name: &str,
        cid: &str,
        metadata: &Value,
    ) -> Result<(), EconomyError>;
    async fn record_sale(
        &self,
        dataset_cid: &str,
        amount_usdc: f64,
        buyer: Address,
    ) -> Result<(), EconomyError>;
}

#[derive(Clone)]
pub struct OceanProtocolClient {
    config: OceanConfig,
    http: Arc<HttpClient>,
}

impl OceanProtocolClient {
    pub fn new(config: OceanConfig) -> Result<Self, EconomyError> {
        let http = HttpClient::builder()
            .build()
            .map_err(|e| EconomyError::Network(e.to_string()))?;

        Ok(Self {
            config,
            http: Arc::new(http),
        })
    }
}

#[async_trait]
impl OceanClient for OceanProtocolClient {
    async fn register_dataset(
        &self,
        name: &str,
        cid: &str,
        metadata: &Value,
    ) -> Result<(), EconomyError> {
        let endpoint = format!("{}/datasets", self.config.endpoint);
        let request = self.http.post(endpoint).json(&serde_json::json!({
            "name": name,
            "cid": cid,
            "metadata": metadata,
        }));

        let response = if let Some(ref api_key) = self.config.api_key {
            request
                .header("Authorization", format!("Bearer {api_key}"))
                .send()
                .await
        } else {
            request.send().await
        }
        .map_err(|e| EconomyError::Network(e.to_string()))?;

        if !response.status().is_success() {
            return Err(EconomyError::Network(format!(
                "failed to register dataset (status {})",
                response.status()
            )));
        }

        Ok(())
    }

    async fn record_sale(
        &self,
        dataset_cid: &str,
        amount_usdc: f64,
        buyer: Address,
    ) -> Result<(), EconomyError> {
        let endpoint = format!("{}/sales", self.config.endpoint);
        let request = self.http.post(endpoint).json(&serde_json::json!({
            "cid": dataset_cid,
            "amount_usdc": amount_usdc,
            "buyer": format!("{buyer:?}"),
        }));

        let response = if let Some(ref api_key) = self.config.api_key {
            request
                .header("Authorization", format!("Bearer {api_key}"))
                .send()
                .await
        } else {
            request.send().await
        }
        .map_err(|e| EconomyError::Network(e.to_string()))?;

        if !response.status().is_success() {
            return Err(EconomyError::Network(format!(
                "failed to record ocean sale (status {})",
                response.status()
            )));
        }

        Ok(())
    }
}

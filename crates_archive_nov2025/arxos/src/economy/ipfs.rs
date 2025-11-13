use std::sync::Arc;

use async_trait::async_trait;
use reqwest::{header, Client as HttpClient};
use serde_json::Value;

use super::{config::IpfsConfig, EconomyError};

#[async_trait]
pub trait IpfsClient: Send + Sync {
    async fn pin_bytes(&self, name: &str, data: Vec<u8>) -> Result<String, EconomyError>;
    async fn pin_json(&self, name: &str, payload: &Value) -> Result<String, EconomyError>;
    fn gateway_url(&self, cid: &str) -> Option<String>;
}

#[derive(Clone)]
pub struct GatewayIpfsClient {
    config: IpfsConfig,
    http: Arc<HttpClient>,
}

impl GatewayIpfsClient {
    pub fn new(config: IpfsConfig) -> Result<Self, EconomyError> {
        let mut headers = header::HeaderMap::new();
        if let Some(ref key) = config.api_key {
            headers.insert(
                "pinata_api_key",
                header::HeaderValue::from_str(key)
                    .map_err(|e| EconomyError::Configuration(e.to_string()))?,
            );
        }
        if let Some(ref secret) = config.api_secret {
            headers.insert(
                "pinata_secret_api_key",
                header::HeaderValue::from_str(secret)
                    .map_err(|e| EconomyError::Configuration(e.to_string()))?,
            );
        }

        let http = HttpClient::builder()
            .default_headers(headers)
            .build()
            .map_err(|e| EconomyError::Network(e.to_string()))?;

        Ok(Self {
            config,
            http: Arc::new(http),
        })
    }
}

#[async_trait]
impl IpfsClient for GatewayIpfsClient {
    async fn pin_bytes(&self, name: &str, data: Vec<u8>) -> Result<String, EconomyError> {
        let resp = self
            .http
            .post(format!(
                "{}/api/v0/add?pin=true&wrap-with-directory=false&cid-version=1&file-name={name}",
                self.config.endpoint
            ))
            .body(data)
            .send()
            .await
            .map_err(|e| EconomyError::Network(e.to_string()))?;

        let json: serde_json::Value = resp
            .json()
            .await
            .map_err(|e| EconomyError::Serialization(e.to_string()))?;
        json.get("Hash")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string())
            .ok_or_else(|| EconomyError::Network("missing CID from IPFS response".into()))
    }

    async fn pin_json(&self, name: &str, payload: &Value) -> Result<String, EconomyError> {
        let resp = self
            .http
            .post(format!("{}/pinning/pinJSONToIPFS", self.config.endpoint))
            .json(&serde_json::json!({
                "pinataMetadata": { "name": name },
                "pinataContent": payload,
            }))
            .send()
            .await
            .map_err(|e| EconomyError::Network(e.to_string()))?;

        let json: serde_json::Value = resp
            .json()
            .await
            .map_err(|e| EconomyError::Serialization(e.to_string()))?;
        json.get("IpfsHash")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string())
            .ok_or_else(|| EconomyError::Network("missing IpfsHash from IPFS response".into()))
    }

    fn gateway_url(&self, cid: &str) -> Option<String> {
        self.config
            .gateway
            .as_ref()
            .map(|gateway| format!("{gateway}/ipfs/{cid}"))
    }
}

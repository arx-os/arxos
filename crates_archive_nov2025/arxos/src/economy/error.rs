use thiserror::Error;

#[derive(Debug, Error)]
pub enum EconomyError {
    #[error("configuration error: {0}")]
    Configuration(String),
    #[error("missing configuration value: {0}")]
    MissingConfig(&'static str),
    #[error("invalid hex value: {0}")]
    InvalidHex(String),
    #[error("provider error: {0}")]
    Provider(String),
    #[error("wallet error: {0}")]
    Wallet(String),
    #[error("contract call failed: {0}")]
    ContractCall(String),
    #[error("serialization error: {0}")]
    Serialization(String),
    #[error("network error: {0}")]
    Network(String),
    #[error("io error: {0}")]
    Io(String),
}

impl From<std::io::Error> for EconomyError {
    fn from(value: std::io::Error) -> Self {
        Self::Io(value.to_string())
    }
}

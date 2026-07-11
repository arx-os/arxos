use serde::{Deserialize, Serialize};

/// Cryptographic identifier for workers, entities, and nodes in ArxOS.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ArxId(pub uuid::Uuid);

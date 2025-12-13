//! EIP-712 proof generation and signing for contributions
//!
//! This module implements the EIP-712 typed structured data signing standard
//! for verifying spatial data contributions to ArxOS.

use anyhow::Result;
use serde::{Deserialize, Serialize};

#[cfg(feature = "blockchain")]
use ethers::{
    core::types::{H256, U256},
    signers::{LocalWallet, Signer},
    utils::keccak256,
};

/// Contribution proof structure matching Solidity contract
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContributionProof {
    /// Root of spatial data Merkle tree (IFC entities, sensor data, etc.)
    pub merkle_root: [u8; 32],
    
    /// Hash of GPS coordinates: keccak256(abi.encodePacked(lat, lon, timestamp))
    pub location_hash: [u8; 32],
    
    /// Hash of building ID: keccak256(buildingId)
    pub building_hash: [u8; 32],
    
    /// Proof creation timestamp (Unix seconds)
    pub timestamp: u64,
    
    /// Size of contributed data in bytes
    pub data_size: u64,
}

impl ContributionProof {
    /// Create a new contribution proof
    pub fn new(
        merkle_root: [u8; 32],
        latitude: f64,
        longitude: f64,
        building_id: &str,
        data_size: u64,
    ) -> Self {
        let timestamp = chrono::Utc::now().timestamp() as u64;
        
        // Hash location: keccak256(abi.encodePacked(lat, lon, timestamp))
        let location_hash = Self::hash_location(latitude, longitude, timestamp);
        
        // Hash building ID: keccak256(buildingId)
        let building_hash = Self::hash_building_id(building_id);
        
        Self {
            merkle_root,
            location_hash,
            building_hash,
            timestamp,
            data_size,
        }
    }

    /// Hash GPS location with timestamp
    fn hash_location(latitude: f64, longitude: f64, timestamp: u64) -> [u8; 32] {
        #[cfg(feature = "blockchain")]
        {
            let encoded = ethers::abi::encode(&[
                ethers::abi::Token::Int(U256::from((latitude * 1_000_000.0) as i64)),
                ethers::abi::Token::Int(U256::from((longitude * 1_000_000.0) as i64)),
                ethers::abi::Token::Uint(U256::from(timestamp)),
            ]);
            keccak256(&encoded)
        }
        
        #[cfg(not(feature = "blockchain"))]
        {
            // Fallback to SHA256 if blockchain feature disabled
            let mut hasher = Sha256::new();
            hasher.update(latitude.to_le_bytes());
            hasher.update(longitude.to_le_bytes());
            hasher.update(timestamp.to_le_bytes());
            hasher.finalize().into()
        }
    }

    /// Hash building ID
    fn hash_building_id(building_id: &str) -> [u8; 32] {
        #[cfg(feature = "blockchain")]
        {
            keccak256(building_id.as_bytes())
        }
        
        #[cfg(not(feature = "blockchain"))]
        {
            let mut hasher = Sha256::new();
            hasher.update(building_id.as_bytes());
            hasher.finalize().into()
        }
    }

    /// Convert to EIP-712 struct hash
    #[cfg(feature = "blockchain")]
    pub fn struct_hash(&self) -> H256 {
        // EIP-712 typehash for ContributionProof
        let type_hash = keccak256(
            b"ContributionProof(bytes32 merkleRoot,bytes32 locationHash,bytes32 buildingHash,uint256 timestamp,uint256 dataSize)"
        );

        // Hash struct data according to EIP-712
        let encoded = ethers::abi::encode(&[
            ethers::abi::Token::FixedBytes(type_hash.to_vec()),
            ethers::abi::Token::FixedBytes(self.merkle_root.to_vec()),
            ethers::abi::Token::FixedBytes(self.location_hash.to_vec()),
            ethers::abi::Token::FixedBytes(self.building_hash.to_vec()),
            ethers::abi::Token::Uint(U256::from(self.timestamp)),
            ethers::abi::Token::Uint(U256::from(self.data_size)),
        ]);

        H256::from(keccak256(&encoded))
    }
}

/// Proof signer for creating EIP-712 signatures
#[cfg(feature = "blockchain")]
pub struct ProofSigner {
    wallet: LocalWallet,
    domain: Eip712Domain,
}

#[cfg(feature = "blockchain")]
#[derive(Debug, Clone)]
struct Eip712Domain {
    name: String,
    version: String,
    chain_id: u64,
    verifying_contract: String,
}

#[cfg(feature = "blockchain")]
impl ProofSigner {
    /// Create a new proof signer
    pub fn new(
        private_key: &str,
        chain_id: u64,
        oracle_address: &str,
    ) -> Result<Self> {
        let wallet: LocalWallet = private_key.parse()?;
        
        let domain = Eip712Domain {
            name: "ArxOS Contribution Oracle".to_string(),
            version: "1".to_string(),
            chain_id,
            verifying_contract: oracle_address.to_string(),
        };

        Ok(Self { wallet, domain })
    }

    /// Sign a contribution proof with EIP-712
    pub async fn sign_proof(&self, proof: &ContributionProof) -> Result<Vec<u8>> {
        // Create EIP-712 domain separator
        let domain_separator = self.domain_separator();
        
        // Get struct hash
        let struct_hash = proof.struct_hash();
        
        // Create digest: keccak256("\x19\x01" || domainSeparator || structHash)
        let digest = self.create_digest(domain_separator, struct_hash);
        
        // Sign digest
        let signature = self.wallet.sign_message(digest.as_bytes()).await?;
        
        Ok(signature.to_vec())
    }

    /// Create EIP-712 domain separator
    fn domain_separator(&self) -> H256 {
        let type_hash = keccak256(
            b"EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
        );

        let encoded = ethers::abi::encode(&[
            ethers::abi::Token::FixedBytes(type_hash.to_vec()),
            ethers::abi::Token::FixedBytes(keccak256(self.domain.name.as_bytes()).to_vec()),
            ethers::abi::Token::FixedBytes(keccak256(self.domain.version.as_bytes()).to_vec()),
            ethers::abi::Token::Uint(U256::from(self.domain.chain_id)),
            ethers::abi::Token::Address(self.domain.verifying_contract.parse().unwrap()),
        ]);

        H256::from(keccak256(&encoded))
    }

    /// Create final EIP-712 digest for signing
    fn create_digest(&self, domain_separator: H256, struct_hash: H256) -> H256 {
        let mut digest_input = Vec::new();
        digest_input.extend_from_slice(&[0x19, 0x01]);
        digest_input.extend_from_slice(domain_separator.as_bytes());
        digest_input.extend_from_slice(struct_hash.as_bytes());
        
        H256::from(keccak256(&digest_input))
    }

    /// Get wallet address
    pub fn address(&self) -> String {
        format!("{:?}", self.wallet.address())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_contribution_proof_creation() {
        let proof = ContributionProof::new(
            [0u8; 32],
            40.7128,  // NYC latitude
            -74.0060, // NYC longitude
            "ps-118",
            1024000,  // 1 MB
        );

        assert!(proof.timestamp > 0);
        assert_eq!(proof.data_size, 1024000);
    }

    #[test]
    fn test_hash_building_id() {
        let hash1 = ContributionProof::hash_building_id("ps-118");
        let hash2 = ContributionProof::hash_building_id("ps-118");
        let hash3 = ContributionProof::hash_building_id("different");

        assert_eq!(hash1, hash2);
        assert_ne!(hash1, hash3);
    }
}

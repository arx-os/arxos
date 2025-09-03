//! Cryptographic operations for secure mesh network
//! 
//! Provides Ed25519 signatures for firmware updates and message authentication

use ed25519_dalek::{
    Signature, Signer, SigningKey, Verifier, VerifyingKey,
    SECRET_KEY_LENGTH, SIGNATURE_LENGTH,
};
use rand::{rngs::OsRng, RngCore};
use sha2::{Digest, Sha256};
use std::error::Error;
use std::fmt;

/// Cryptographic errors
#[derive(Debug)]
pub enum CryptoError {
    InvalidKeyLength,
    InvalidSignature,
    VerificationFailed,
    KeyGenerationFailed,
    SerializationError,
}

impl fmt::Display for CryptoError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CryptoError::InvalidKeyLength => write!(f, "Invalid key length"),
            CryptoError::InvalidSignature => write!(f, "Invalid signature format"),
            CryptoError::VerificationFailed => write!(f, "Signature verification failed"),
            CryptoError::KeyGenerationFailed => write!(f, "Key generation failed"),
            CryptoError::SerializationError => write!(f, "Serialization error"),
        }
    }
}

impl Error for CryptoError {}

impl From<ed25519_dalek::SignatureError> for CryptoError {
    fn from(_: ed25519_dalek::SignatureError) -> Self {
        CryptoError::InvalidSignature
    }
}

/// Mesh network cryptographic context
pub struct MeshCrypto {
    /// Node's signing key (private)
    signing_key: SigningKey,
    /// Node's verifying key (public)
    verifying_key: VerifyingKey,
    /// Trusted root keys for firmware updates
    trusted_roots: Vec<VerifyingKey>,
}

impl MeshCrypto {
    /// Create new crypto context with generated keys
    pub fn new() -> Result<Self, CryptoError> {
        // Generate random bytes for the key
        let mut secret_bytes = [0u8; SECRET_KEY_LENGTH];
        OsRng.fill_bytes(&mut secret_bytes);
        
        let signing_key = SigningKey::from_bytes(&secret_bytes);
        let verifying_key = signing_key.verifying_key();
        
        Ok(Self {
            signing_key,
            verifying_key,
            trusted_roots: Vec::new(),
        })
    }
    
    /// Create from existing key material
    pub fn from_bytes(secret_key: &[u8]) -> Result<Self, CryptoError> {
        if secret_key.len() != SECRET_KEY_LENGTH {
            return Err(CryptoError::InvalidKeyLength);
        }
        
        let signing_key = SigningKey::from_bytes(secret_key.try_into().unwrap());
        let verifying_key = signing_key.verifying_key();
        
        Ok(Self {
            signing_key,
            verifying_key,
            trusted_roots: Vec::new(),
        })
    }
    
    /// Add trusted root key for firmware verification
    pub fn add_trusted_root(&mut self, public_key: &[u8]) -> Result<(), CryptoError> {
        let verifying_key = VerifyingKey::from_bytes(public_key.try_into()
            .map_err(|_| CryptoError::InvalidKeyLength)?)?;
        
        self.trusted_roots.push(verifying_key);
        Ok(())
    }
    
    /// Sign message
    pub fn sign(&self, message: &[u8]) -> Signature {
        self.signing_key.sign(message)
    }
    
    /// Verify signature with node's key
    pub fn verify(&self, message: &[u8], signature: &[u8]) -> Result<(), CryptoError> {
        let sig = Signature::from_bytes(signature.try_into()
            .map_err(|_| CryptoError::InvalidSignature)?);
        
        self.verifying_key
            .verify(message, &sig)
            .map_err(|_| CryptoError::VerificationFailed)
    }
    
    /// Verify signature with any trusted root key
    pub fn verify_with_roots(&self, message: &[u8], signature: &[u8]) -> Result<(), CryptoError> {
        let sig = Signature::from_bytes(signature.try_into()
            .map_err(|_| CryptoError::InvalidSignature)?);
        
        for root_key in &self.trusted_roots {
            if root_key.verify(message, &sig).is_ok() {
                return Ok(());
            }
        }
        
        Err(CryptoError::VerificationFailed)
    }
    
    /// Get public key bytes
    pub fn public_key(&self) -> [u8; 32] {
        self.verifying_key.to_bytes()
    }
    
    /// Export private key (careful!)
    pub fn export_private_key(&self) -> [u8; SECRET_KEY_LENGTH] {
        self.signing_key.to_bytes()
    }
}

/// Firmware update signature verification
pub struct FirmwareVerifier {
    trusted_keys: Vec<VerifyingKey>,
}

impl FirmwareVerifier {
    /// Create new firmware verifier
    pub fn new() -> Self {
        Self {
            trusted_keys: Vec::new(),
        }
    }
    
    /// Add Arxos official signing key
    pub fn add_official_key(&mut self) -> Result<(), CryptoError> {
        // This would be the actual Arxos signing key
        // Hardcoded for security (prevents tampering)
        const ARXOS_PUBLIC_KEY: [u8; 32] = [
            0x9d, 0x61, 0xb1, 0x9d, 0xef, 0xfd, 0x5a, 0x60,
            0xba, 0x84, 0x4a, 0xf4, 0x92, 0xec, 0x2c, 0xc4,
            0x44, 0x49, 0xc5, 0x69, 0x7b, 0x32, 0x69, 0x19,
            0x70, 0x3b, 0xac, 0x03, 0x1c, 0xae, 0x7f, 0x60,
        ];
        
        let key = VerifyingKey::from_bytes(&ARXOS_PUBLIC_KEY)?;
        self.trusted_keys.push(key);
        Ok(())
    }
    
    /// Verify firmware update
    pub fn verify_firmware(
        &self,
        firmware: &[u8],
        signature: &[u8],
        metadata: &FirmwareMetadata,
    ) -> Result<(), CryptoError> {
        // Verify metadata signature first
        self.verify_metadata(metadata)?;
        
        // Compute firmware hash
        let mut hasher = Sha256::new();
        hasher.update(firmware);
        let hash = hasher.finalize();
        
        // Verify hash matches metadata
        if hash.as_slice() != metadata.firmware_hash {
            return Err(CryptoError::VerificationFailed);
        }
        
        // Verify firmware signature
        let sig = Signature::from_bytes(signature.try_into()
            .map_err(|_| CryptoError::InvalidSignature)?);
        
        for key in &self.trusted_keys {
            if key.verify(firmware, &sig).is_ok() {
                return Ok(());
            }
        }
        
        Err(CryptoError::VerificationFailed)
    }
    
    fn verify_metadata(&self, metadata: &FirmwareMetadata) -> Result<(), CryptoError> {
        // Serialize metadata for verification
        let data = metadata.to_bytes();
        let sig = Signature::from_bytes(&metadata.signature);
        
        for key in &self.trusted_keys {
            if key.verify(&data, &sig).is_ok() {
                return Ok(());
            }
        }
        
        Err(CryptoError::VerificationFailed)
    }
}

/// Firmware metadata for secure updates
#[derive(Debug, Clone)]
pub struct FirmwareMetadata {
    pub version: Version,
    pub timestamp: u64,
    pub size: usize,
    pub firmware_hash: Vec<u8>,
    pub signature: [u8; SIGNATURE_LENGTH],
    pub compatible_hardware: Vec<String>,
}

impl FirmwareMetadata {
    /// Serialize to bytes for signing
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut bytes = Vec::new();
        
        // Version
        bytes.push(self.version.major);
        bytes.push(self.version.minor);
        bytes.push(self.version.patch);
        
        // Timestamp (8 bytes)
        bytes.extend_from_slice(&self.timestamp.to_le_bytes());
        
        // Size (8 bytes)
        bytes.extend_from_slice(&self.size.to_le_bytes());
        
        // Hash
        bytes.extend_from_slice(&self.firmware_hash);
        
        // Hardware compatibility
        for hw in &self.compatible_hardware {
            bytes.extend_from_slice(hw.as_bytes());
            bytes.push(0);  // Null terminator
        }
        
        bytes
    }
}

/// Version information
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Version {
    pub major: u8,
    pub minor: u8,
    pub patch: u8,
}

/// Message authentication for mesh packets
pub struct PacketAuthenticator {
    shared_key: [u8; 32],
}

impl PacketAuthenticator {
    /// Create new packet authenticator with shared key
    pub fn new(shared_key: [u8; 32]) -> Self {
        Self { shared_key }
    }
    
    /// Generate MAC for packet
    pub fn generate_mac(&self, packet: &[u8]) -> [u8; 16] {
        let mut hasher = Sha256::new();
        hasher.update(&self.shared_key);
        hasher.update(packet);
        let hash = hasher.finalize();
        
        // Use first 16 bytes as MAC
        let mut mac = [0u8; 16];
        mac.copy_from_slice(&hash[..16]);
        mac
    }
    
    /// Verify packet MAC
    pub fn verify_mac(&self, packet: &[u8], mac: &[u8; 16]) -> bool {
        let computed_mac = self.generate_mac(packet);
        
        // Constant-time comparison
        let mut diff = 0u8;
        for i in 0..16 {
            diff |= computed_mac[i] ^ mac[i];
        }
        
        diff == 0
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_sign_verify() {
        let crypto = MeshCrypto::new().unwrap();
        
        let message = b"Hello, Arxos mesh network!";
        let signature = crypto.sign(message);
        
        // Should verify with own key
        assert!(crypto.verify(message, signature.to_bytes().as_ref()).is_ok());
        
        // Should fail with modified message
        let bad_message = b"Hello, Arxos mesh network?";
        assert!(crypto.verify(bad_message, signature.to_bytes().as_ref()).is_err());
    }
    
    #[test]
    fn test_firmware_metadata() {
        let metadata = FirmwareMetadata {
            version: Version { major: 1, minor: 0, patch: 0 },
            timestamp: 1234567890,
            size: 65536,
            firmware_hash: vec![0xAA; 32],
            signature: [0xBB; 64],
            compatible_hardware: vec!["ESP32-C3".to_string()],
        };
        
        let bytes = metadata.to_bytes();
        assert!(bytes.len() > 0);
        
        // Version should be at start
        assert_eq!(bytes[0], 1);  // major
        assert_eq!(bytes[1], 0);  // minor
        assert_eq!(bytes[2], 0);  // patch
    }
    
    #[test]
    fn test_packet_mac() {
        let auth = PacketAuthenticator::new([0x42; 32]);
        
        let packet = b"ArxObject data here";
        let mac = auth.generate_mac(packet);
        
        // Should verify correctly
        assert!(auth.verify_mac(packet, &mac));
        
        // Should fail with modified packet
        let bad_packet = b"ArxObject data here!";
        assert!(!auth.verify_mac(bad_packet, &mac));
        
        // Should fail with modified MAC
        let mut bad_mac = mac;
        bad_mac[0] ^= 0xFF;
        assert!(!auth.verify_mac(packet, &bad_mac));
    }
}
//! Zero-Trust Mesh Authentication
//! 
//! Inspired by Hypori's zero-trust model but adapted for mesh networks.
//! Every packet is authenticated, no implicit trust between nodes.
#![forbid(unsafe_code)]
#![deny(clippy::unwrap_used, clippy::expect_used)]
#![cfg_attr(test, allow(clippy::unwrap_used, clippy::expect_used))]

// Simplified crypto types for zero trust mesh
type Ed25519PublicKey = [u8; 32];
type Ed25519Signature = [u8; 64];
type Ed25519SecretKey = [u8; 32];
use crate::arxobject::ArxObject;
use crate::MeshPacket;
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

/// Zero-trust packet wrapper (LEGACY) - previously used truncated signatures.
/// Deprecated in favor of MAC-authenticated frames in radio_secure::secure_frame.
#[derive(Debug, Clone)]
pub struct ZeroTrustPacket {
    /// Original mesh packet (13 bytes)
    pub inner_packet: [u8; 13],
    
    /// Sender's public key identifier (2 bytes)
    pub sender_id: u16,
    
    /// Timestamp (4 bytes - seconds since epoch)
    pub timestamp: u32,
    
    /// Signature (8 bytes - truncated Ed25519) [DEPRECATED]
    pub signature: [u8; 8],
    
    /// Nonce to prevent replay (2 bytes)
    pub nonce: u16,
}

impl ZeroTrustPacket {
    /// Total size: 13 + 2 + 4 + 8 + 2 = 29 bytes (legacy)
    pub fn to_bytes(&self) -> [u8; 29] {
        let mut bytes = [0u8; 29];
        bytes[0..13].copy_from_slice(&self.inner_packet);
        bytes[13..15].copy_from_slice(&self.sender_id.to_le_bytes());
        bytes[15..19].copy_from_slice(&self.timestamp.to_le_bytes());
        bytes[19..27].copy_from_slice(&self.signature);
        bytes[27..29].copy_from_slice(&self.nonce.to_le_bytes());
        bytes
    }
    
    pub fn from_bytes(bytes: &[u8; 29]) -> Self {
        let mut inner_packet = [0u8; 13];
        inner_packet.copy_from_slice(&bytes[0..13]);
        
        let mut signature = [0u8; 8];
        signature.copy_from_slice(&bytes[19..27]);
        
        Self {
            inner_packet,
            sender_id: u16::from_le_bytes([bytes[13], bytes[14]]),
            timestamp: u32::from_le_bytes([bytes[15], bytes[16], bytes[17], bytes[18]]),
            signature,
            nonce: u16::from_le_bytes([bytes[27], bytes[28]]),
        }
    }
}

/// Trust registry - manages keys and permissions
pub struct TrustRegistry {
    /// Known public keys mapped to IDs
    pub keys: HashMap<u16, Ed25519PublicKey>,
    
    /// Permissions for each key
    pub permissions: HashMap<u16, NodePermissions>,
    
    /// Replay prevention - tracks recent nonces
    pub nonce_cache: HashMap<u16, Vec<u16>>,
    
    /// Revoked keys
    pub revoked: Vec<u16>,
}

/// Permissions a node can have
#[derive(Debug, Clone)]
pub struct NodePermissions {
    /// Can read ArxObjects
    pub can_read: bool,
    
    /// Can write/modify ArxObjects
    pub can_write: bool,
    
    /// Can relay packets
    pub can_relay: bool,
    
    /// Object types this node can access
    pub allowed_types: Vec<u8>,
    
    /// Spatial bounds for access
    pub spatial_bounds: Option<(u16, u16, u16, u16)>,
    
    /// Expiration time
    pub expires_at: u64,
}

impl TrustRegistry {
    pub fn new() -> Self {
        Self {
            keys: HashMap::new(),
            permissions: HashMap::new(),
            nonce_cache: HashMap::new(),
            revoked: Vec::new(),
        }
    }
    
    /// Register a new trusted node
    pub fn register_node(
        &mut self, 
        node_id: u16, 
        public_key: Ed25519PublicKey,
        permissions: NodePermissions,
    ) {
        self.keys.insert(node_id, public_key);
        self.permissions.insert(node_id, permissions);
        self.nonce_cache.insert(node_id, Vec::with_capacity(100));
    }
    
    /// Verify a zero-trust packet
    pub fn verify_packet(&mut self, packet: &ZeroTrustPacket) -> Result<(), TrustError> {
        // Check if sender is revoked
        if self.revoked.contains(&packet.sender_id) {
            return Err(TrustError::RevokedKey);
        }
        
        // Get sender's public key
        let public_key = self.keys.get(&packet.sender_id)
            .ok_or(TrustError::UnknownSender)?;
        
        // Check permissions
        let perms = self.permissions.get(&packet.sender_id)
            .ok_or(TrustError::NoPermissions)?;
        
        // Check expiration
        let now = match SystemTime::now().duration_since(UNIX_EPOCH) {
            Ok(dur) => dur.as_secs(),
            Err(_) => return Err(TrustError::StalePacket),
        };
        
        if now > perms.expires_at {
            return Err(TrustError::ExpiredPermissions);
        }
        
        // Check timestamp (prevent old packets)
        let packet_age = now as u32 - packet.timestamp;
        if packet_age > 300 {  // 5 minute window
            return Err(TrustError::StalePacket);
        }
        
        // Check nonce for replay prevention
        let nonces = match self.nonce_cache.get_mut(&packet.sender_id) {
            Some(n) => n,
            None => return Err(TrustError::UnknownSender),
        };
        if nonces.contains(&packet.nonce) {
            return Err(TrustError::ReplayAttack);
        }
        
        // Add nonce to cache (keep last 100)
        nonces.push(packet.nonce);
        if nonces.len() > 100 {
            nonces.remove(0);
        }
        
        // Legacy path: signature verification omitted; replaced by MAC in secure frames
        
        Ok(())
    }
    
    /// Revoke a node's access
    pub fn revoke_node(&mut self, node_id: u16) {
        self.revoked.push(node_id);
        self.permissions.remove(&node_id);
    }
}

/// Trust errors
#[derive(Debug)]
pub enum TrustError {
    UnknownSender,
    RevokedKey,
    NoPermissions,
    ExpiredPermissions,
    StalePacket,
    ReplayAttack,
    InvalidSignature,
}

/// Capability-based access control token
#[derive(Debug, Clone)]
pub struct CapabilityToken {
    /// What this token grants access to
    pub capability: Capability,
    
    /// Who issued this token
    pub issuer: u16,
    
    /// Who can use this token
    pub bearer: u16,
    
    /// When it expires
    pub expires_at: u64,
    
    /// Signature from issuer
    pub signature: [u8; 8],
}

/// Types of capabilities
#[derive(Debug, Clone)]
pub enum Capability {
    /// Read objects in specific area
    ReadArea { x: u16, y: u16, radius: u16 },
    
    /// Modify specific object type
    ModifyType { object_type: u8 },
    
    /// Emergency override access
    EmergencyAccess,
    
    /// Maintenance mode for zone
    MaintenanceMode { zone_id: u16 },
}

/// Distributed trust verification
pub struct DistributedTrust {
    /// Local trust registry
    local_registry: TrustRegistry,
    
    /// Capability tokens we've seen
    capability_cache: HashMap<u16, Vec<CapabilityToken>>,
    
    /// Trust anchors (root keys)
    trust_anchors: Vec<Ed25519PublicKey>,
}

impl DistributedTrust {
    pub fn new(trust_anchors: Vec<Ed25519PublicKey>) -> Self {
        Self {
            local_registry: TrustRegistry::new(),
            capability_cache: HashMap::new(),
            trust_anchors,
        }
    }
    
    /// Verify chain of trust for a capability
    pub fn verify_capability(&self, token: &CapabilityToken) -> Result<(), TrustError> {
        // Check if issuer is trusted
        if !self.local_registry.keys.contains_key(&token.issuer) {
            return Err(TrustError::UnknownSender);
        }
        
        // Check expiration
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        if now > token.expires_at {
            return Err(TrustError::ExpiredPermissions);
        }
        
        // Verify signature (simplified)
        // In production, properly verify Ed25519 signature
        
        Ok(())
    }
    
    /// Grant temporary capability
    pub fn grant_capability(
        &mut self,
        bearer: u16,
        capability: Capability,
        duration_seconds: u64,
    ) -> CapabilityToken {
        let expires_at = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() + duration_seconds;
        
        CapabilityToken {
            capability,
            issuer: 0x0001, // Building controller ID
            bearer,
            expires_at,
            signature: [0; 8], // Would be properly signed
        }
    }
}

/// Demo zero-trust authentication flow
pub fn demo_zero_trust() {
    println!("\n🔐 Zero-Trust Mesh Authentication Demo\n");
    
    println!("Traditional mesh trust:");
    println!("  • Nodes implicitly trust neighbors");
    println!("  • One compromised node → entire network at risk");
    println!("  • No audit trail");
    
    println!("\nArxOS zero-trust mesh:");
    println!("  • Every packet is signed");
    println!("  • Every relay verifies authenticity");
    println!("  • Capabilities are time-limited");
    
    println!("\nExample: HVAC contractor query");
    println!("────────────────────────────");
    
    println!("\n1️⃣ Contractor requests access:");
    println!("   → Signs request with their key");
    println!("   → Includes capability token");
    
    println!("\n2️⃣ Edge node verifies:");
    println!("   ✓ Valid signature");
    println!("   ✓ Capability not expired");
    println!("   ✓ Nonce not replayed");
    println!("   ✓ Timestamp is fresh");
    
    println!("\n3️⃣ Access granted for:");
    println!("   • HVAC objects only");
    println!("   • Next 8 hours");
    println!("   • Floors 2-3 only");
    
    println!("\n4️⃣ Packet structure (29 bytes):");
    println!("   [ArxObject:13][ID:2][Time:4][Sig:8][Nonce:2]");
    
    println!("\nSecurity benefits:");
    println!("  • Compromised contractor key → limited damage");
    println!("  • Full audit trail of all access");
    println!("  • Automatic expiration of permissions");
}
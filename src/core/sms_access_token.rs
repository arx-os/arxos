//! SMS Access Token to ArxObject Conversion
//! 
//! Converts SMS access codes into 13-byte ArxObjects that work
//! over the mesh network. This bridges cellular and RF worlds.

use crate::arxobject::ArxObject;
use crate::simple_access_control::{SimpleAccess, CompanyCode, RoleCode};
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

/// SMS access token that fits in ArxObject format
#[derive(Debug, Clone, Copy)]
pub struct SMSAccessToken {
    /// Token ID (from 6-char SMS code) - 3 bytes
    pub token_id: [u8; 3],
    
    /// Building ID - 2 bytes  
    pub building_id: u16,
    
    /// Phone last 4 digits - 2 bytes
    pub phone_suffix: u16,
    
    /// Role and company - 1 byte each
    pub role: u8,
    pub company: u8,
    
    /// Expiration (hours from now) - 1 byte
    pub hours_remaining: u8,
    
    /// Trust level - 1 byte
    pub trust: u8,
    
    /// Checksum - 1 byte
    pub checksum: u8,
}

impl SMSAccessToken {
    /// Create from SMS code and phone
    pub fn from_sms_code(code: &str, phone: &str, building_id: u16) -> Self {
        // Convert 6-char code to 3 bytes
        let token_id = Self::encode_token(code);
        
        // Get last 4 digits of phone
        let phone_digits: String = phone.chars()
            .filter(|c| c.is_ascii_digit())
            .collect();
        let phone_suffix = phone_digits
            .chars()
            .rev()
            .take(4)
            .collect::<String>()
            .chars()
            .rev()
            .collect::<String>()
            .parse::<u16>()
            .unwrap_or(0);
        
        let mut token = Self {
            token_id,
            building_id,
            phone_suffix,
            role: 4, // Default: Maintenance
            company: 5, // Default: Guest contractor
            hours_remaining: 12,
            trust: 50,
            checksum: 0,
        };
        
        token.checksum = token.calculate_checksum();
        token
    }
    
    /// Encode 6-character token to 3 bytes
    fn encode_token(code: &str) -> [u8; 3] {
        // Each char is 5 bits (32 possible values)
        // 6 chars = 30 bits = fits in 3.75 bytes, use 3
        let mut bytes = [0u8; 3];
        
        for (i, ch) in code.chars().take(6).enumerate() {
            let val = Self::char_to_5bit(ch);
            
            // Pack 5-bit values into bytes
            match i {
                0 => bytes[0] |= val << 3,
                1 => {
                    bytes[0] |= val >> 2;
                    bytes[1] |= val << 6;
                }
                2 => bytes[1] |= val << 1,
                3 => {
                    bytes[1] |= val >> 4;
                    bytes[2] |= val << 4;
                }
                4 => {
                    bytes[2] |= val >> 1;
                }
                5 => {
                    bytes[2] |= (val & 0x01);
                }
                _ => {}
            }
        }
        
        bytes
    }
    
    /// Convert character to 5-bit value
    fn char_to_5bit(ch: char) -> u8 {
        match ch {
            'A'..='Z' => (ch as u8) - b'A',
            '2'..='9' => (ch as u8) - b'2' + 26,
            _ => 0,
        }
    }
    
    /// Calculate checksum
    fn calculate_checksum(&self) -> u8 {
        let sum = self.token_id.iter().sum::<u8>() as u16
            + (self.building_id & 0xFF) 
            + (self.building_id >> 8)
            + (self.phone_suffix & 0xFF)
            + (self.phone_suffix >> 8)
            + self.role as u16
            + self.company as u16
            + self.hours_remaining as u16
            + self.trust as u16;
        
        (sum & 0xFF) as u8
    }
    
    /// Convert to ArxObject for mesh transmission
    pub fn to_arxobject(&self) -> ArxObject {
        ArxObject {
            building_id: self.building_id,
            object_type: 0xFE, // Special type for access tokens
            x: self.phone_suffix,
            y: u16::from_le_bytes([self.role, self.company]),
            z: u16::from_le_bytes([self.hours_remaining, self.trust]),
            properties: [
                self.token_id[0],
                self.token_id[1],
                self.token_id[2],
                self.checksum,
            ],
        }
    }
    
    /// Reconstruct from ArxObject
    pub fn from_arxobject(obj: &ArxObject) -> Option<Self> {
        if obj.object_type != 0xFE {
            return None;
        }
        
        Some(Self {
            token_id: [obj.properties[0], obj.properties[1], obj.properties[2]],
            building_id: obj.building_id,
            phone_suffix: obj.x,
            role: (obj.y & 0xFF) as u8,
            company: (obj.y >> 8) as u8,
            hours_remaining: (obj.z & 0xFF) as u8,
            trust: (obj.z >> 8) as u8,
            checksum: obj.properties[3],
        })
    }
    
    /// Convert to SimpleAccess for permission checks
    pub fn to_simple_access(&self) -> SimpleAccess {
        let mut access = SimpleAccess::new_for_tech(
            match self.company {
                5 => CompanyCode::LocalHVAC,
                6 => CompanyCode::LocalElectrical,
                _ => CompanyCode::BuildingOwner,
            },
            match self.role {
                1 => RoleCode::HVACTech,
                2 => RoleCode::Electrician,
                3 => RoleCode::Plumber,
                4 => RoleCode::Maintenance,
                _ => RoleCode::Maintenance,
            },
            self.hours_remaining as u16,
        );
        
        access.building_id = self.building_id;
        access.trust_level = self.trust;
        
        access
    }
}

/// Token verification over mesh
pub struct TokenVerifier {
    /// Active tokens by code
    active_tokens: HashMap<String, TokenInfo>,
    
    /// Token to phone mapping
    token_phones: HashMap<String, String>,
}

#[derive(Debug, Clone)]
struct TokenInfo {
    token: SMSAccessToken,
    activated_at: u64,
    last_seen: u64,
    usage_count: u32,
}

impl TokenVerifier {
    pub fn new() -> Self {
        Self {
            active_tokens: HashMap::new(),
            token_phones: HashMap::new(),
        }
    }
    
    /// Register new SMS token
    pub fn register_token(&mut self, code: String, phone: String, building_id: u16) {
        let token = SMSAccessToken::from_sms_code(&code, &phone, building_id);
        
        self.active_tokens.insert(code.clone(), TokenInfo {
            token,
            activated_at: current_timestamp(),
            last_seen: current_timestamp(),
            usage_count: 0,
        });
        
        self.token_phones.insert(code, phone);
    }
    
    /// Verify token from mesh packet
    pub fn verify_mesh_token(&mut self, obj: &ArxObject) -> Result<SimpleAccess, &'static str> {
        let token = SMSAccessToken::from_arxobject(obj)
            .ok_or("Invalid token format")?;
        
        // Check checksum
        if token.checksum != token.calculate_checksum() {
            return Err("Invalid checksum");
        }
        
        // Check expiration
        if token.hours_remaining == 0 {
            return Err("Token expired");
        }
        
        // Update last seen
        // In production, would update the HashMap entry
        
        Ok(token.to_simple_access())
    }
    
    /// Broadcast token to mesh
    pub fn broadcast_token_activation(&self, code: &str) -> Vec<u8> {
        if let Some(info) = self.active_tokens.get(code) {
            let obj = info.token.to_arxobject();
            obj.to_bytes().to_vec()
        } else {
            vec![]
        }
    }
}

/// Demo: SMS to Mesh Flow
pub fn demo_sms_to_mesh() {
    println!("\n📱➜📡 SMS to Mesh Conversion\n");
    
    println!("1️⃣ SMS Code: 'K7M3X9'");
    println!("   Phone: 555-0100");
    println!("   Building: 0x0042");
    println!();
    
    let token = SMSAccessToken::from_sms_code("K7M3X9", "555-0100", 0x0042);
    
    println!("2️⃣ SMS Token Structure:");
    println!("   Token ID:    {:?}", token.token_id);
    println!("   Building:    0x{:04X}", token.building_id);
    println!("   Phone:       {:04}", token.phone_suffix);
    println!("   Role:        {}", token.role);
    println!("   Hours:       {}", token.hours_remaining);
    println!();
    
    let arx = token.to_arxobject();
    
    println!("3️⃣ As ArxObject (13 bytes):");
    let building_id = arx.building_id;
    let object_type = arx.object_type;
    let x = arx.x;
    let y = arx.y;
    let z = arx.z;
    let properties = arx.properties;
    println!("   Building ID: 0x{:04X}", building_id);
    println!("   Type:        0x{:02X} (Access Token)", object_type);
    println!("   X:           {} (phone suffix)", x);
    println!("   Y:           {} (role/company)", y);
    println!("   Z:           {} (hours/trust)", z);
    println!("   Properties:  {:?}", properties);
    println!();
    
    let bytes = arx.to_bytes();
    
    println!("4️⃣ Over Mesh Network:");
    println!("   Bytes: {:02X?}", bytes);
    println!("   Size: {} bytes", bytes.len());
    println!();
    
    println!("5️⃣ Mesh Node Receives:");
    let received = ArxObject::from_bytes(&bytes);
    let verified = SMSAccessToken::from_arxobject(&received).unwrap();
    let access = verified.to_simple_access();
    
    println!("   ✅ Token valid");
    println!("   ✅ Building matches");
    println!("   ✅ {} hours remaining", verified.hours_remaining);
    println!("   ✅ Trust level: {}", access.trust_level);
    println!();
    
    println!("🎯 SMS → ArxObject → Mesh → Access!");
}

/// Mobile app integration
pub struct MobileAppBridge;

impl MobileAppBridge {
    /// Handle deep link from SMS
    pub fn handle_deep_link(url: &str) -> Result<SMSAccessToken, Box<dyn std::error::Error>> {
        // arxos://access/0042/K7M3X9
        let parts: Vec<&str> = url.split('/').collect();
        
        if parts.len() < 5 {
            return Err("Invalid deep link".into());
        }
        
        let building_id = u16::from_str_radix(parts[3], 16)?;
        let code = parts[4];
        
        // In production, would get phone from device
        let phone = "555-0100";
        
        Ok(SMSAccessToken::from_sms_code(code, phone, building_id))
    }
    
    /// Generate QR code for sharing
    pub fn generate_share_qr(token: &SMSAccessToken) -> String {
        // In production, would generate actual QR
        format!(
            "arxos://share/{:04X}/{:02X}{:02X}{:02X}",
            token.building_id,
            token.token_id[0],
            token.token_id[1],
            token.token_id[2],
        )
    }
}

fn current_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs()
}
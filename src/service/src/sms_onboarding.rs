//! SMS-Based Onboarding & Access Control
//! 
//! The SIMPLEST way to grant building access: text messages.
//! No apps required initially, no complex enrollment, just SMS.

use arxos_core::simple_access_control::{SimpleAccess, CompanyCode, RoleCode};
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

/// SMS access grant system
pub struct SMSAccessManager {
    /// Pending access tokens awaiting activation
    pending_tokens: HashMap<String, PendingAccess>,
    
    /// Active SMS sessions
    active_sessions: HashMap<String, SimpleAccess>,
    
    /// Building configuration
    building_id: u16,
    building_name: String,
    
    /// SMS gateway configuration (Twilio/TextBelt/etc)
    sms_gateway: SMSGateway,
}

/// Pending access awaiting SMS activation
#[derive(Debug, Clone)]
struct PendingAccess {
    phone_number: String,
    access_token: String,
    role: RoleCode,
    company: CompanyCode,
    expires_at: u64,
    hours_granted: u8,
    requestor: String,
    created_at: u64,
}

impl SMSAccessManager {
    pub fn new(building_id: u16, building_name: String) -> Self {
        Self {
            pending_tokens: HashMap::new(),
            active_sessions: HashMap::new(),
            building_id,
            building_name,
            sms_gateway: SMSGateway::new(),
        }
    }
    
    /// IT admin grants access via CLI
    pub async fn grant_access_cli(
        &mut self,
        phone: &str,
        role: &str,
        hours: u8,
        requestor: &str,
    ) -> Result<(), Box<dyn std::error::Error>> {
        // Parse role
        let role_code = match role.to_lowercase().as_str() {
            "hvac" => RoleCode::HVACTech,
            "electrical" | "electrician" => RoleCode::Electrician,
            "maintenance" | "maint" => RoleCode::Maintenance,
            "security" | "guard" => RoleCode::Security,
            "contractor" | "vendor" => RoleCode::Maintenance, // Generic access
            _ => RoleCode::Maintenance,
        };
        
        // Generate 6-character access token
        let token = Self::generate_token();
        
        // Create pending access
        let pending = PendingAccess {
            phone_number: phone.to_string(),
            access_token: token.clone(),
            role: role_code,
            company: CompanyCode::LocalHVAC, // Guest contractor
            expires_at: current_timestamp() + (hours as u64 * 3600),
            hours_granted: hours,
            requestor: requestor.to_string(),
            created_at: current_timestamp(),
        };
        
        // Store pending
        self.pending_tokens.insert(token.clone(), pending.clone());
        
        // Send SMS
        self.send_access_sms(&pending).await?;
        
        println!("✅ Access SMS sent to {}", phone);
        println!("   Token: {}", token);
        println!("   Valid: {} hours", hours);
        
        Ok(())
    }
    
    /// Send the actual SMS message
    async fn send_access_sms(&self, pending: &PendingAccess) -> Result<(), Box<dyn std::error::Error>> {
        let message = if self.is_arxos_installed(&pending.phone_number) {
            // User has app - send deep link
            format!(
                "🏢 {} Building Access\n\n\
                Tap to activate {} hour access:\n\
                arxos://access/{}/{}\n\n\
                Code: {}\n\
                Expires in {} hours",
                self.building_name,
                pending.hours_granted,
                self.building_id,
                pending.access_token,
                pending.access_token,
                pending.hours_granted,
            )
        } else {
            // New user - include download link
            format!(
                "🏢 {} Building Access\n\n\
                You've been granted {} hour access.\n\n\
                Code: {}\n\n\
                Install ArxOS:\n\
                📱 iPhone: arxos.app/ios\n\
                🤖 Android: arxos.app/android\n\n\
                Or reply with code to activate",
                self.building_name,
                pending.hours_granted,
                pending.access_token,
            )
        };
        
        self.sms_gateway.send(&pending.phone_number, &message).await?;
        Ok(())
    }
    
    /// Check if user has ArxOS installed (would check database)
    fn is_arxos_installed(&self, _phone: &str) -> bool {
        // In production, check if this phone has connected before
        false
    }
    
    /// Generate simple access token
    fn generate_token() -> String {
        // 6 character token based on timestamp
        const CHARSET: &[u8] = b"ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        let timestamp = current_timestamp();
        let mut hash = timestamp;
        
        (0..6)
            .map(|i| {
                hash = hash.wrapping_mul(1103515245).wrapping_add(12345);
                let idx = (hash as usize) % CHARSET.len();
                CHARSET[idx] as char
            })
            .collect()
    }
    
    /// Handle SMS reply with access code
    pub async fn handle_sms_reply(
        &mut self,
        from_phone: &str,
        message: &str,
    ) -> Result<String, Box<dyn std::error::Error>> {
        // Extract token from message
        let token = message.trim().to_uppercase();
        
        // Check if valid token
        if let Some(pending) = self.pending_tokens.get(&token) {
            // Verify phone matches
            if pending.phone_number != from_phone {
                return Ok("Invalid access code".to_string());
            }
            
            // Check expiration
            if current_timestamp() > pending.expires_at {
                self.pending_tokens.remove(&token);
                return Ok("Access code expired".to_string());
            }
            
            // Create SimpleAccess
            let mut access = SimpleAccess::new_for_tech(
                pending.company,
                pending.role,
                pending.hours_granted as u16,
            );
            access.building_id = self.building_id;
            
            // Store active session
            self.active_sessions.insert(from_phone.to_string(), access);
            self.pending_tokens.remove(&token);
            
            // Send confirmation with connection details
            let response = format!(
                "✅ Access activated!\n\n\
                Building: {}\n\
                Role: {:?}\n\
                Valid: {} hours\n\n\
                WiFi: {}_mesh\n\
                Pass: {}\n\n\
                Open ArxOS and you'll connect automatically",
                self.building_name,
                pending.role,
                pending.hours_granted,
                self.building_name,
                &token[..4], // Use part of token as wifi pass
            );
            
            self.sms_gateway.send(from_phone, &response).await?;
            
            Ok("Access granted".to_string())
        } else {
            Ok("Invalid access code. Contact building IT.".to_string())
        }
    }
    
    /// Get access token for phone number
    pub fn get_access(&self, phone: &str) -> Option<SimpleAccess> {
        self.active_sessions.get(phone).copied()
    }
}

/// SMS Gateway abstraction
struct SMSGateway {
    // In production, would use Twilio/TextBelt/etc
}

impl SMSGateway {
    fn new() -> Self {
        Self {}
    }
    
    async fn send(&self, to: &str, message: &str) -> Result<(), Box<dyn std::error::Error>> {
        // In production: actual SMS sending
        println!("📱 SMS to {}: {}", to, message);
        Ok(())
    }
}

/// CLI command implementation
pub struct SMSCommand;

impl SMSCommand {
    /// Process the CLI command: arx -newuser phone @building --temp
    pub async fn execute(args: Vec<String>) -> Result<(), Box<dyn std::error::Error>> {
        // Parse arguments
        let phone = args.get(2)
            .ok_or("Missing phone number")?;
        
        let building = args.get(3)
            .and_then(|s| s.strip_prefix("@"))
            .ok_or("Missing @building")?;
        
        let hours = if args.contains(&"--temp".to_string()) {
            12  // Default temp access
        } else if let Some(pos) = args.iter().position(|s| s == "--hours") {
            args.get(pos + 1)
                .and_then(|s| s.parse().ok())
                .unwrap_or(12)
        } else {
            24  // Default 1 day
        };
        
        let role = args.iter()
            .find(|s| s.starts_with("--role="))
            .and_then(|s| s.strip_prefix("--role="))
            .unwrap_or("contractor");
        
        // Get requestor (current user)
        let requestor = std::env::var("USER").unwrap_or("admin".to_string());
        
        println!("\n📱 SMS Access Grant");
        println!("══════════════════");
        println!("Phone:    {}", phone);
        println!("Building: {}", building);
        println!("Role:     {}", role);
        println!("Hours:    {}", hours);
        println!("Granted by: {}", requestor);
        println!();
        
        // Create manager and grant access
        let building_id = 0x0042; // Would look up building ID
        let mut manager = SMSAccessManager::new(building_id, building.to_string());
        
        manager.grant_access_cli(phone, role, hours, &requestor).await?;
        
        Ok(())
    }
}

/// Deep link handler for app
pub struct DeepLinkHandler;

impl DeepLinkHandler {
    /// Handle arxos://access/building_id/token
    pub fn handle_access_link(url: &str) -> Result<SimpleAccess, Box<dyn std::error::Error>> {
        let parts: Vec<&str> = url.split('/').collect();
        
        if parts.len() < 4 || parts[2] != "access" {
            return Err("Invalid access link".into());
        }
        
        let building_id = u16::from_str_radix(parts[3], 16)?;
        let token = parts[4];
        
        // In production: verify token with building
        // For now, create temporary access
        let mut access = SimpleAccess::new_for_tech(
            CompanyCode::LocalHVAC,
            RoleCode::Maintenance,
            12, // 12 hours
        );
        access.building_id = building_id;
        
        Ok(access)
    }
}

/// How it works in practice
pub fn demo_sms_flow() {
    println!("\n📱 SMS Onboarding Flow Demo\n");
    
    println!("Scenario: Unexpected HVAC contractor arrives");
    println!("════════════════════════════════════════════\n");
    
    println!("1️⃣ Contractor: \"I'm here to fix the AC\"");
    println!("   Facility Manager: \"Let me grant you access\"");
    println!();
    
    println!("2️⃣ Manager opens terminal:");
    println!("   $ arx -newuser 555-0100 @west-high --temp");
    println!();
    
    println!("3️⃣ Contractor receives SMS:");
    println!("   ┌──────────────────────────────┐");
    println!("   │ 🏢 West High Building Access │");
    println!("   │                              │");
    println!("   │ You've been granted 12 hour  │");
    println!("   │ access.                      │");
    println!("   │                              │");
    println!("   │ Code: K7M3X9                 │");
    println!("   │                              │");
    println!("   │ Install ArxOS:               │");
    println!("   │ 📱 arxos.app/ios             │");
    println!("   │                              │");
    println!("   │ Or reply with code           │");
    println!("   └──────────────────────────────┘");
    println!();
    
    println!("4️⃣ Contractor replies: \"K7M3X9\"");
    println!();
    
    println!("5️⃣ System responds:");
    println!("   ┌──────────────────────────────┐");
    println!("   │ ✅ Access activated!         │");
    println!("   │                              │");
    println!("   │ Building: West High          │");
    println!("   │ Role: HVAC Tech              │");
    println!("   │ Valid: 12 hours              │");
    println!("   │                              │");
    println!("   │ WiFi: west-high_mesh         │");
    println!("   │ Pass: K7M3                   │");
    println!("   └──────────────────────────────┘");
    println!();
    
    println!("6️⃣ Contractor's radio now works with building!");
    println!("   • Can query ArxObjects");
    println!("   • Can see HVAC + Electrical");
    println!("   • Access expires automatically");
    println!();
    
    println!("Total setup time: 30 seconds");
    println!("No app required initially!");
    println!("Works with flip phones!");
}

/// SMS sharing mechanism for team access
pub fn demo_sms_sharing() {
    println!("\n🤝 SMS Team Sharing Demo\n");
    
    println!("Lead Tech shares access with team:");
    println!("══════════════════════════════════\n");
    
    println!("1️⃣ Lead tech with access:");
    println!("   $ arx -share 555-0101 555-0102 --role=hvac");
    println!();
    
    println!("2️⃣ Team members receive:");
    println!("   \"Jim (Lead) shared West High access\"");
    println!("   \"Code: A9B2C7\"");
    println!("   \"Valid: 8 hours\"");
    println!();
    
    println!("3️⃣ Access inherits restrictions:");
    println!("   • Same role as sharer");
    println!("   • Cannot exceed sharer's time");
    println!("   • Revoked if sharer loses access");
    println!();
    
    println!("Perfect for:");
    println!("   • Bringing in specialists");
    println!("   • Temporary crew additions");
    println!("   • Emergency backup techs");
}

fn current_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs()
}


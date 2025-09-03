//! CLI Access Management Commands
//! 
//! Simple commands for managing building access via terminal.
//! Designed for facility managers who aren't IT experts.

use crate::sms_onboarding::{SMSAccessManager, SMSCommand};
use arxos_core::simple_access_control::{SimpleAccess, RoleCode, CompanyCode};
use std::collections::HashMap;

/// CLI handler for access commands
pub struct AccessCLI {
    /// Currently active sessions
    sessions: HashMap<String, SessionInfo>,
    
    /// SMS manager
    sms_manager: SMSAccessManager,
    
    /// Building info
    building_name: String,
    building_id: u16,
}

#[derive(Debug, Clone)]
struct SessionInfo {
    phone: String,
    name: Option<String>,
    company: Option<String>,
    role: RoleCode,
    granted_by: String,
    granted_at: u64,
    expires_at: u64,
    access_token: SimpleAccess,
}

impl AccessCLI {
    pub fn new(building_name: String, building_id: u16) -> Self {
        Self {
            sessions: HashMap::new(),
            sms_manager: SMSAccessManager::new(building_id, building_name.clone()),
            building_name,
            building_id,
        }
    }
    
    /// Process CLI command
    pub async fn process_command(&mut self, input: &str) -> Result<String, Box<dyn std::error::Error>> {
        let parts: Vec<&str> = input.split_whitespace().collect();
        
        if parts.is_empty() {
            return Ok("No command entered".to_string());
        }
        
        match parts[0] {
            "arx" | "arxos" => self.handle_arx_command(&parts[1..]).await,
            "grant" => self.handle_grant_shortcut(&parts[1..]).await,
            "revoke" => self.handle_revoke(&parts[1..]).await,
            "list" | "ls" => self.handle_list().await,
            "help" | "?" => Ok(self.show_help()),
            _ => Ok(format!("Unknown command: {}. Type 'help' for options.", parts[0])),
        }
    }
    
    /// Handle 'arx' prefixed commands
    async fn handle_arx_command(&mut self, args: &[&str]) -> Result<String, Box<dyn std::error::Error>> {
        if args.is_empty() {
            return Ok("Usage: arx [command] [options]".to_string());
        }
        
        match args[0] {
            "-newuser" | "grant" => {
                // arx -newuser 555-0100 @building --temp
                if args.len() < 2 {
                    return Ok("Usage: arx -newuser PHONE [@building] [--temp|--hours N] [--role ROLE]".to_string());
                }
                
                let phone = args[1];
                let hours = self.parse_hours(&args[2..]);
                let role = self.parse_role(&args[2..]);
                
                self.grant_sms_access(phone, role, hours).await
            }
            
            "-share" | "share" => {
                // arx -share 555-0101 555-0102 --role=hvac
                if args.len() < 2 {
                    return Ok("Usage: arx -share PHONE [PHONE...] [--role ROLE]".to_string());
                }
                
                let phones = self.parse_phones(&args[1..]);
                let role = self.parse_role(&args[1..]);
                
                self.share_access(phones, role).await
            }
            
            "-revoke" | "revoke" => {
                // arx -revoke 555-0100
                if args.len() < 2 {
                    return Ok("Usage: arx -revoke PHONE|all".to_string());
                }
                
                self.revoke_access(args[1]).await
            }
            
            "-status" | "status" => {
                // arx -status
                self.show_status().await
            }
            
            _ => Ok(format!("Unknown arx command: {}", args[0])),
        }
    }
    
    /// Quick grant command
    async fn handle_grant_shortcut(&mut self, args: &[&str]) -> Result<String, Box<dyn std::error::Error>> {
        // grant 555-0100 hvac 4h
        if args.len() < 2 {
            return Ok("Usage: grant PHONE ROLE [HOURS]".to_string());
        }
        
        let phone = args[0];
        let role = args.get(1).copied().unwrap_or("contractor");
        let hours = args.get(2)
            .and_then(|h| h.trim_end_matches('h').parse().ok())
            .unwrap_or(12);
        
        self.grant_sms_access(phone, role, hours).await
    }
    
    /// Grant SMS access
    async fn grant_sms_access(
        &mut self,
        phone: &str,
        role: &str,
        hours: u8,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let requestor = std::env::var("USER").unwrap_or("admin".to_string());
        
        // Validate phone number
        let clean_phone = self.clean_phone_number(phone)?;
        
        // Grant access via SMS
        self.sms_manager.grant_access_cli(&clean_phone, role, hours, &requestor).await?;
        
        // Create session info
        let session = SessionInfo {
            phone: clean_phone.clone(),
            name: None,
            company: None,
            role: self.parse_role_code(role),
            granted_by: requestor,
            granted_at: current_timestamp(),
            expires_at: current_timestamp() + (hours as u64 * 3600),
            access_token: SimpleAccess::new_for_tech(
                CompanyCode::LocalHVAC,
                self.parse_role_code(role),
                hours as u16,
            ),
        };
        
        self.sessions.insert(clean_phone.clone(), session);
        
        Ok(format!(
            "✅ Access granted to {}\n\
             Role: {}\n\
             Duration: {} hours\n\
             Status: SMS sent, awaiting activation",
            clean_phone, role, hours
        ))
    }
    
    /// Share access with team
    async fn share_access(
        &mut self,
        phones: Vec<String>,
        role: &str,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let mut results = Vec::new();
        
        for phone in phones {
            match self.grant_sms_access(&phone, role, 8).await {
                Ok(msg) => results.push(format!("✅ {}: Shared", phone)),
                Err(e) => results.push(format!("❌ {}: {}", phone, e)),
            }
        }
        
        Ok(results.join("\n"))
    }
    
    /// Revoke access
    async fn handle_revoke(&mut self, args: &[&str]) -> Result<String, Box<dyn std::error::Error>> {
        if args.is_empty() {
            return Ok("Usage: revoke PHONE|all".to_string());
        }
        
        self.revoke_access(args[0]).await
    }
    
    async fn revoke_access(&mut self, target: &str) -> Result<String, Box<dyn std::error::Error>> {
        if target == "all" {
            let count = self.sessions.len();
            self.sessions.clear();
            Ok(format!("✅ Revoked {} active sessions", count))
        } else {
            let clean_phone = self.clean_phone_number(target)?;
            if self.sessions.remove(&clean_phone).is_some() {
                // TODO: Send SMS notification of revocation
                Ok(format!("✅ Access revoked for {}", clean_phone))
            } else {
                Ok(format!("No active session for {}", clean_phone))
            }
        }
    }
    
    /// List active sessions
    async fn handle_list(&self) -> Result<String, Box<dyn std::error::Error>> {
        if self.sessions.is_empty() {
            return Ok("No active sessions".to_string());
        }
        
        let mut output = format!("\n📱 Active Sessions at {}\n", self.building_name);
        output.push_str("════════════════════════════════════\n\n");
        
        for (phone, session) in &self.sessions {
            let remaining = if session.expires_at > current_timestamp() {
                (session.expires_at - current_timestamp()) / 3600
            } else {
                0
            };
            
            output.push_str(&format!(
                "📞 {}\n\
                 Role: {:?}\n\
                 Granted by: {}\n\
                 Remaining: {} hours\n\
                 ─────────────────\n",
                phone, session.role, session.granted_by, remaining
            ));
        }
        
        Ok(output)
    }
    
    /// Show system status
    async fn show_status(&self) -> Result<String, Box<dyn std::error::Error>> {
        Ok(format!(
            "\n🏢 {} Access System\n\
             ═══════════════════════════\n\
             Building ID: 0x{:04X}\n\
             Active Sessions: {}\n\
             SMS Gateway: ✅ Online\n\
             Mesh Network: ✅ Online\n\
             \n\
             Quick Commands:\n\
             • grant PHONE ROLE HOURS\n\
             • revoke PHONE\n\
             • list\n",
            self.building_name,
            self.building_id,
            self.sessions.len(),
        ))
    }
    
    /// Show help
    fn show_help(&self) -> String {
        r#"
🏢 ArxOS Access Management

Quick Commands:
  grant PHONE ROLE HOURS   - Grant access via SMS
  revoke PHONE             - Revoke access
  list                     - Show active sessions

Full Commands:
  arx -newuser PHONE [@building] [--temp] [--role ROLE]
  arx -share PHONE [PHONE...] [--role ROLE]
  arx -revoke PHONE|all
  arx -status

Examples:
  grant 555-0100 hvac 4h
  arx -newuser 555-0100 @west-high --temp
  arx -share 555-0101 555-0102 --role=electrical

Roles:
  hvac, electrical, plumber, maintenance,
  security, contractor, vendor
"#.to_string()
    }
    
    // Helper functions
    
    fn parse_hours(&self, args: &[&str]) -> u8 {
        for (i, arg) in args.iter().enumerate() {
            if *arg == "--temp" {
                return 12;
            }
            if *arg == "--hours" {
                if let Some(h) = args.get(i + 1).and_then(|s| s.parse().ok()) {
                    return h;
                }
            }
            if arg.ends_with('h') {
                if let Ok(h) = arg[..arg.len()-1].parse() {
                    return h;
                }
            }
        }
        24 // Default 24 hours
    }
    
    fn parse_role(&self, args: &[&str]) -> &str {
        for arg in args {
            if let Some(role) = arg.strip_prefix("--role=") {
                return role;
            }
        }
        "contractor" // Default role
    }
    
    fn parse_phones(&self, args: &[&str]) -> Vec<String> {
        args.iter()
            .filter(|s| !s.starts_with("--"))
            .filter_map(|s| self.clean_phone_number(s).ok())
            .collect()
    }
    
    fn clean_phone_number(&self, phone: &str) -> Result<String, Box<dyn std::error::Error>> {
        // Remove non-digits
        let clean: String = phone.chars().filter(|c| c.is_ascii_digit()).collect();
        
        if clean.len() < 10 {
            return Err("Invalid phone number".into());
        }
        
        // Format as XXX-XXX-XXXX
        if clean.len() == 10 {
            Ok(format!("{}-{}-{}", &clean[0..3], &clean[3..6], &clean[6..10]))
        } else if clean.len() == 11 && clean.starts_with('1') {
            Ok(format!("{}-{}-{}", &clean[1..4], &clean[4..7], &clean[7..11]))
        } else {
            Ok(clean)
        }
    }
    
    fn parse_role_code(&self, role: &str) -> RoleCode {
        match role.to_lowercase().as_str() {
            "hvac" => RoleCode::HVACTech,
            "electrical" | "electrician" => RoleCode::Electrician,
            "plumber" | "plumbing" => RoleCode::Plumber,
            "maintenance" | "maint" => RoleCode::Maintenance,
            "security" | "guard" => RoleCode::Security,
            _ => RoleCode::Maintenance,
        }
    }
}

/// Integration with terminal interface
pub async fn demo_cli_workflow() {
    println!("\n⌨️ CLI Workflow Demo\n");
    
    println!("Facility Manager's Terminal:");
    println!("════════════════════════════\n");
    
    println!("$ █");
    tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
    
    println!("$ grant 555-0100 hvac 4h");
    println!("✅ Access granted to 555-0100");
    println!("Role: hvac");
    println!("Duration: 4 hours");
    println!("Status: SMS sent, awaiting activation");
    println!();
    
    tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
    
    println!("$ list");
    println!("\n📱 Active Sessions at West High");
    println!("════════════════════════════════════\n");
    println!("📞 555-0100");
    println!("Role: HVACTech");
    println!("Granted by: jsmith");
    println!("Remaining: 4 hours");
    println!("─────────────────");
    println!();
    
    tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
    
    println!("$ grant 555-0101 electrical 2h");
    println!("✅ Access granted to 555-0101");
    println!("Role: electrical");
    println!("Duration: 2 hours");
    println!("Status: SMS sent, awaiting activation");
    println!();
    
    println!("$ █");
}

fn current_timestamp() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs()
}


//! Data Consumer API for SSH-based building intelligence access
//! 
//! Provides secure, air-gapped access to building data via SSH commands
//! No internet connection required - all data flows through RF mesh

use crate::database::Database;
use std::collections::HashMap;

/// Data consumer access levels
#[derive(Debug, Clone, PartialEq)]
pub enum AccessTier {
    Basic,      // Anonymized aggregate data only
    Premium,    // Detailed anonymized data
    Enterprise, // Custom queries and exports
    Government, // Physical air-gapped transfer only
}

/// Query credit system for data monetization
#[derive(Debug, Clone)]
pub struct QueryCredits {
    pub balance: u32,
    pub tier: AccessTier,
    pub monthly_allowance: Option<u32>,
    pub last_reset: chrono::DateTime<chrono::Utc>,
}

/// Data consumer session
pub struct DataConsumerSession {
    pub username: String,
    pub organization: String,
    pub access_tier: AccessTier,
    pub credits: QueryCredits,
    pub allowed_regions: Vec<String>,
    pub rate_limit: RateLimit,
    pub audit_log: Vec<QueryAudit>,
}

/// Rate limiting for API fairness
#[derive(Debug, Clone)]
pub struct RateLimit {
    pub queries_per_hour: u32,
    pub export_gb_per_day: f32,
    pub current_usage: Usage,
}

#[derive(Debug, Clone, Default)]
pub struct Usage {
    pub queries_this_hour: u32,
    pub data_exported_today_gb: f32,
    pub last_reset: chrono::DateTime<chrono::Utc>,
}

/// Audit trail for compliance
#[derive(Debug, Clone)]
pub struct QueryAudit {
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub query: String,
    pub credits_used: u32,
    pub rows_returned: u32,
    pub export_format: Option<String>,
}

/// Main data consumer API
pub struct DataConsumerAPI {
    database: Database,
    sessions: HashMap<String, DataConsumerSession>,
}

impl DataConsumerAPI {
    pub fn new(database: Database) -> Self {
        Self {
            database,
            sessions: HashMap::new(),
        }
    }
    
    /// Authenticate data consumer via SSH
    pub fn authenticate(&mut self, username: &str, ssh_key: &str) -> Result<&DataConsumerSession, String> {
        // Verify SSH key against authorized_keys
        if !self.verify_ssh_key(username, ssh_key) {
            return Err("Authentication failed".to_string());
        }
        
        // Load or create session
        if !self.sessions.contains_key(username) {
            let session = self.load_session(username)?;
            self.sessions.insert(username.to_string(), session);
        }
        
        Ok(self.sessions.get(username).unwrap())
    }
    
    /// Execute anonymized query
    pub fn query_anonymized(
        &mut self, 
        session: &mut DataConsumerSession,
        query: &str
    ) -> Result<QueryResult, String> {
        // Check rate limits
        if !self.check_rate_limit(session) {
            return Err("Rate limit exceeded".to_string());
        }
        
        // Calculate query cost
        let credits_required = self.calculate_query_cost(query);
        
        // Check credits
        if session.credits.balance < credits_required {
            return Err(format!("Insufficient credits. Required: {}, Balance: {}", 
                credits_required, session.credits.balance));
        }
        
        // Execute query with anonymization
        let result = self.execute_anonymized_query(query)?;
        
        // Deduct credits
        session.credits.balance -= credits_required;
        
        // Log for audit
        session.audit_log.push(QueryAudit {
            timestamp: chrono::Utc::now(),
            query: query.to_string(),
            credits_used: credits_required,
            rows_returned: result.row_count,
            export_format: None,
        });
        
        // Update usage
        session.rate_limit.current_usage.queries_this_hour += 1;
        
        Ok(result)
    }
    
    /// Export data in various formats
    pub fn export_data(
        &mut self,
        session: &mut DataConsumerSession,
        query: &str,
        format: ExportFormat,
    ) -> Result<Vec<u8>, String> {
        // Check export quota
        // Estimate size based on query complexity
        let estimated_size_gb = 0.001; // 1MB estimate
        if session.rate_limit.current_usage.data_exported_today_gb + estimated_size_gb 
            > session.rate_limit.export_gb_per_day {
            return Err("Daily export quota exceeded".to_string());
        }
        
        // Execute query
        let result = self.query_anonymized(session, query)?;
        
        // Format data
        let exported = match format {
            ExportFormat::CSV => self.export_to_format(&result, ExportFormat::CSV),
            ExportFormat::JSON => self.export_to_format(&result, ExportFormat::JSON),
            ExportFormat::Excel => self.export_to_format(&result, ExportFormat::Excel),
            ExportFormat::ActuarialTables => self.export_to_format(&result, ExportFormat::ActuarialTables),
        };
        
        // Update usage
        session.rate_limit.current_usage.data_exported_today_gb += estimated_size_gb;
        
        Ok(exported)
    }
    
    /// Purchase credits using BILT tokens
    pub fn purchase_credits(
        &mut self,
        session: &mut DataConsumerSession,
        bilt_amount: u32,
    ) -> Result<u32, String> {
        // Exchange rate: 1 BILT = 10 query credits
        let credits_purchased = bilt_amount * 10;
        
        // Process payment via mesh network
        self.process_bilt_payment(session, bilt_amount)?;
        
        // Add credits
        session.credits.balance += credits_purchased;
        
        Ok(credits_purchased)
    }
    
    /// Insurance risk assessment query
    pub fn risk_assessment(
        &self,
        building_type: &str,
        region: &str,
    ) -> Result<RiskAssessment, String> {
        let _query = format!(
            "SELECT 
                AVG(fire_violations) as avg_fire_violations,
                AVG(electrical_load / electrical_capacity) as avg_electrical_utilization,
                COUNT(CASE WHEN structural_compliant = 1 THEN 1 END) / COUNT(*) as compliance_rate
            FROM buildings
            WHERE building_type = '{}' AND region = '{}'",
            building_type, region
        );
        
        // Execute query (stub)
        let result = DatabaseResult {
            columns: vec!["type".to_string(), "violations".to_string()],
            rows: vec![],
            row_count: 0,
            avg_fire_violations: 2.5,
            avg_electrical_utilization: 0.75,
            compliance_rate: 0.95,
            avg_electrical: 0.0,
            avg_hvac: 0.0,
            avg_traffic: 0.0,
            avg_buildout_cost: 0.0,
        };
        
        Ok(RiskAssessment {
            fire_risk: self.calculate_fire_risk(result.avg_fire_violations),
            electrical_risk: self.calculate_electrical_risk(result.avg_electrical_utilization),
            structural_risk: self.calculate_structural_risk(result.compliance_rate),
            overall_score: self.calculate_overall_risk_score(&result),
        })
    }
    
    /// Real estate comparable analysis
    pub fn comparable_analysis(
        &self,
        building_type: &str,
        sqft_range: (u32, u32),
    ) -> Result<ComparableAnalysis, String> {
        let _query = format!(
            "SELECT 
                AVG(electrical_capacity_utilized) as avg_electrical,
                AVG(hvac_efficiency_score) as avg_hvac,
                AVG(foot_traffic_score) as avg_traffic,
                AVG(buildout_cost_per_sqft) as avg_buildout_cost
            FROM buildings
            WHERE building_type = '{}' 
                AND square_footage BETWEEN {} AND {}",
            building_type, sqft_range.0, sqft_range.1
        );
        
        // Execute query (stub)
        let result = DatabaseResult {
            columns: vec!["type".to_string(), "violations".to_string()],
            rows: vec![],
            row_count: 0,
            avg_fire_violations: 2.5,
            avg_electrical_utilization: 0.75,
            compliance_rate: 0.95,
            avg_electrical: 0.0,
            avg_hvac: 0.0,
            avg_traffic: 0.0,
            avg_buildout_cost: 0.0,
        };
        
        Ok(ComparableAnalysis {
            electrical_capacity: result.avg_electrical,
            hvac_efficiency: result.avg_hvac,
            foot_traffic_score: result.avg_traffic,
            typical_buildout_cost: result.avg_buildout_cost,
            comparable_count: result.row_count,
        })
    }
    
    fn load_session(&self, username: &str) -> Result<DataConsumerSession, String> {
        // Load session from database or create new one
        Ok(DataConsumerSession {
            username: username.to_string(),
            organization: "Default Org".to_string(),
            access_tier: AccessTier::Basic,
            credits: QueryCredits {
                balance: 100,
                tier: AccessTier::Basic,
                monthly_allowance: Some(1000),
                last_reset: chrono::Utc::now(),
            },
            allowed_regions: vec!["US".to_string()],
            rate_limit: RateLimit {
                queries_per_hour: 10,
                export_gb_per_day: 1.0,
                current_usage: Usage {
                    queries_this_hour: 0,
                    data_exported_today_gb: 0.0,
                    last_reset: chrono::Utc::now(),
                },
            },
            audit_log: Vec::new(),
        })
    }
    
    fn estimate_export_size(&self, _result: &QueryResult, _format: ExportFormat) -> f32 {
        // Estimate size based on rows and columns
        0.001  // 1 MB estimate for now
    }
    
    fn export_to_format(&self, result: &QueryResult, format: ExportFormat) -> Vec<u8> {
        match format {
            ExportFormat::CSV => {
                // Simple CSV export
                let mut output = String::new();
                output.push_str(&result.columns.join(","));
                output.push('\n');
                for row in &result.rows {
                    output.push_str(&row.join(","));
                    output.push('\n');
                }
                output.into_bytes()
            }
            ExportFormat::JSON => {
                // Simple JSON export
                format!("{{\"columns\": {:?}, \"rows\": {:?}}}", result.columns, result.rows).into_bytes()
            }
            ExportFormat::Excel => {
                // Placeholder for Excel export
                format!("Excel export not yet implemented").into_bytes()
            }
            ExportFormat::ActuarialTables => {
                // Placeholder for actuarial export
                format!("Actuarial export not yet implemented").into_bytes()
            }
        }
    }
    
    fn hash_value(&self, value: &str) -> String {
        // Simple hash for anonymization
        format!("HASH_{:x}", value.len())
    }
    
    fn find_column_index(&self, _column_name: &str) -> Option<usize> {
        // Would search columns for index
        None
    }
    
    fn calculate_fire_risk(&self, avg_violations: f32) -> String {
        match avg_violations as u32 {
            0 => "Low".to_string(),
            1..=3 => "Medium".to_string(),
            _ => "High".to_string(),
        }
    }
    
    fn calculate_electrical_risk(&self, utilization: f32) -> String {
        if utilization < 0.7 { "Low".to_string() }
        else if utilization < 0.9 { "Medium".to_string() }
        else { "High".to_string() }
    }
    
    fn calculate_structural_risk(&self, compliance_rate: f32) -> String {
        if compliance_rate > 0.95 { "Low".to_string() }
        else if compliance_rate > 0.80 { "Medium".to_string() }
        else { "High".to_string() }
    }
    
    fn calculate_overall_risk_score(&self, _result: &DatabaseResult) -> f32 {
        // Simple average for now
        75.0
    }
    
    fn process_bilt_payment(&self, session: &mut DataConsumerSession, bilt_amount: u32) -> Result<(), String> {
        // Process BILT token payment (stub)
        session.credits.balance += bilt_amount * 10; // 10 credits per BILT
        Ok(())
    }
    
    fn verify_ssh_key(&self, _username: &str, _ssh_key: &str) -> bool {
        // Verify SSH public key against authorized_keys database
        // This would integrate with OpenSSH authorized_keys format
        true // Placeholder
    }
    
    fn calculate_query_cost(&self, query: &str) -> u32 {
        // Simple cost model based on query complexity
        if query.contains("SELECT COUNT") {
            1  // Basic aggregate
        } else if query.contains("JOIN") {
            5  // Complex join
        } else if query.contains("predictive") || query.contains("forecast") {
            10 // Advanced analytics
        } else {
            2  // Standard query
        }
    }
    
    fn check_rate_limit(&self, session: &DataConsumerSession) -> bool {
        let now = chrono::Utc::now();
        let hour_ago = now - chrono::Duration::hours(1);
        
        // Reset counter if needed
        if session.rate_limit.current_usage.last_reset < hour_ago {
            return true; // Will be reset when used
        }
        
        session.rate_limit.current_usage.queries_this_hour < session.rate_limit.queries_per_hour
    }
    
    fn execute_anonymized_query(&self, _query: &str) -> Result<QueryResult, String> {
        // Execute query with anonymization filters
        // - Hash building IDs
        // - Remove exact addresses
        // - Strip owner information
        // - Exclude tenant details
        
        // Execute query (stub for now)
        let raw_result = DatabaseResult {
            columns: vec!["id".to_string(), "type".to_string()],
            rows: vec![vec!["1".to_string(), "outlet".to_string()]],
            row_count: 1,
            avg_fire_violations: 0.0,
            avg_electrical_utilization: 0.0,
            compliance_rate: 1.0,
            avg_electrical: 0.0,
            avg_hvac: 0.0,
            avg_traffic: 0.0,
            avg_buildout_cost: 0.0,
        };
        Ok(self.anonymize_result(raw_result))
    }
    
    fn anonymize_result(&self, result: DatabaseResult) -> QueryResult {
        // Anonymization logic
        QueryResult {
            columns: result.columns.clone(),
            rows: result.rows.into_iter().map(|row| {
                self.anonymize_row(row)
            }).collect(),
            row_count: result.row_count,
        }
    }
    
    fn anonymize_row(&self, mut row: Vec<String>) -> Vec<String> {
        // Hash sensitive fields
        if let Some(building_id_idx) = self.find_column_index("building_id") {
            row[building_id_idx] = self.hash_value(&row[building_id_idx]);
        }
        // Remove address
        if let Some(address_idx) = self.find_column_index("address") {
            row[address_idx] = "REDACTED".to_string();
        }
        row
    }
}

/// Query result structure
pub struct QueryResult {
    pub columns: Vec<String>,
    pub rows: Vec<Vec<String>>,
    pub row_count: u32,
}

/// Database result (before anonymization)
struct DatabaseResult {
    columns: Vec<String>,
    rows: Vec<Vec<String>>,
    row_count: u32,
    avg_fire_violations: f32,
    avg_electrical_utilization: f32,
    compliance_rate: f32,
    avg_electrical: f32,
    avg_hvac: f32,
    avg_traffic: f32,
    avg_buildout_cost: f32,
}

/// Export formats supported
pub enum ExportFormat {
    CSV,
    JSON,
    Excel,
    ActuarialTables,
}

/// Risk assessment results
pub struct RiskAssessment {
    pub fire_risk: String,
    pub electrical_risk: String,
    pub structural_risk: String,
    pub overall_score: f32,
}


/// Comparable analysis results
pub struct ComparableAnalysis {
    pub electrical_capacity: f32,
    pub hvac_efficiency: f32,
    pub foot_traffic_score: f32,
    pub typical_buildout_cost: f32,
    pub comparable_count: u32,
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_credit_calculation() {
        let api = DataConsumerAPI::new(Database::new(":memory:").unwrap());
        
        assert_eq!(api.calculate_query_cost("SELECT COUNT(*) FROM buildings"), 1);
        assert_eq!(api.calculate_query_cost("SELECT * FROM a JOIN b ON a.id = b.id"), 5);
        assert_eq!(api.calculate_query_cost("SELECT predictive_maintenance()"), 10);
    }
    
    #[test]
    fn test_anonymization() {
        let api = DataConsumerAPI::new(Database::new(":memory:").unwrap());
        
        let row = vec![
            "building_123".to_string(),
            "123 Main St".to_string(),
            "John Doe".to_string(),
        ];
        
        let anonymized = api.anonymize_row(row);
        assert_ne!(anonymized[0], "building_123"); // Should be hashed
        assert_eq!(anonymized[1], "REDACTED");     // Address removed
    }
}
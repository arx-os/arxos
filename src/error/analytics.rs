//! Error reporting and analytics for ArxOS

use crate::error::ArxError;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::SystemTime;

/// Detailed error report for analytics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorReport {
    pub timestamp: SystemTime,
    pub error_type: String,
    pub message: String,
    pub context: String,
    pub suggestions: Vec<String>,
    pub recovery_steps: Vec<String>,
    pub file_path: Option<String>,
    pub line_number: Option<usize>,
    pub operation: Option<String>,
}

/// Error analytics and statistics
#[derive(Debug, Default, Serialize)]
pub struct ErrorAnalytics {
    pub error_counts: HashMap<String, usize>,
    pub common_suggestions: HashMap<String, usize>,
    pub recovery_success_rate: HashMap<String, f64>,
    pub error_reports: Vec<ErrorReport>,
    pub total_errors: usize,
    pub successful_recoveries: usize,
}

impl ErrorAnalytics {
    /// Create a new error analytics instance
    pub fn new() -> Self {
        Self::default()
    }
    
    /// Record an error for analytics
    pub fn record_error(&mut self, error: &ArxError, operation: Option<String>) {
        self.total_errors += 1;
        
        let error_type = match error {
            ArxError::IfcProcessing { .. } => "IFC Processing",
            ArxError::Configuration { .. } => "Configuration",
            ArxError::GitOperation { .. } => "Git Operation",
            ArxError::Validation { .. } => "Validation",
            ArxError::IoError { .. } => "IO Error",
            ArxError::YamlProcessing { .. } => "YAML Processing",
            ArxError::SpatialData { .. } => "Spatial Data",
        };
        
        // Update error counts
        *self.error_counts.entry(error_type.to_string()).or_insert(0) += 1;
        
        // Record suggestions
        for suggestion in &error.context().suggestions {
            *self.common_suggestions.entry(suggestion.clone()).or_insert(0) += 1;
        }
        
        // Create detailed error report
        let report = ErrorReport {
            timestamp: SystemTime::now(),
            error_type: error_type.to_string(),
            message: error.to_string(),
            context: format!("{:?}", error.context()),
            suggestions: error.context().suggestions.clone(),
            recovery_steps: error.context().recovery_steps.clone(),
            file_path: error.context().file_path.clone(),
            line_number: error.context().line_number,
            operation,
        };
        
        self.error_reports.push(report);
    }
    
    /// Record a successful recovery
    pub fn record_recovery(&mut self, error_type: &str) {
        self.successful_recoveries += 1;
        
        // Update recovery success rate
        let current_rate = self.recovery_success_rate
            .get(error_type)
            .copied()
            .unwrap_or(0.0);
        
        let new_rate = (current_rate + 1.0) / 2.0; // Simple moving average
        self.recovery_success_rate.insert(error_type.to_string(), new_rate);
    }
    
    /// Generate a comprehensive analytics report
    pub fn generate_report(&self) -> String {
        let mut report = String::new();
        
        report.push_str("📊 Error Analytics Report\n");
        report.push_str("========================\n\n");
        
        // Overall statistics
        report.push_str(&format!("Total Errors: {}\n", self.total_errors));
        report.push_str(&format!("Successful Recoveries: {}\n", self.successful_recoveries));
        
        if self.total_errors > 0 {
            let recovery_rate = (self.successful_recoveries as f64 / self.total_errors as f64) * 100.0;
            report.push_str(&format!("Recovery Rate: {:.1}%\n", recovery_rate));
        }
        
        report.push('\n');
        
        // Error type breakdown
        report.push_str("Error Types:\n");
        for (error_type, count) in &self.error_counts {
            let percentage = (*count as f64 / self.total_errors as f64) * 100.0;
            report.push_str(&format!("  {}: {} ({:.1}%)\n", error_type, count, percentage));
        }
        
        report.push('\n');
        
        // Most common suggestions
        if !self.common_suggestions.is_empty() {
            report.push_str("Most Common Suggestions:\n");
            let mut suggestions: Vec<_> = self.common_suggestions.iter().collect();
            suggestions.sort_by(|a, b| b.1.cmp(a.1));
            
            for (suggestion, count) in suggestions.iter().take(5) {
                report.push_str(&format!("  • {} ({} times)\n", suggestion, count));
            }
        }
        
        report.push('\n');
        
        // Recovery success rates
        if !self.recovery_success_rate.is_empty() {
            report.push_str("Recovery Success Rates:\n");
            for (error_type, rate) in &self.recovery_success_rate {
                report.push_str(&format!("  {}: {:.1}%\n", error_type, rate * 100.0));
            }
        }
        
        report
    }
    
    /// Generate a summary for logging
    pub fn generate_summary(&self) -> String {
        format!(
            "Errors: {}, Recoveries: {}, Rate: {:.1}%",
            self.total_errors,
            self.successful_recoveries,
            if self.total_errors > 0 {
                (self.successful_recoveries as f64 / self.total_errors as f64) * 100.0
            } else {
                0.0
            }
        )
    }
    
    /// Get the most common error type
    pub fn most_common_error_type(&self) -> Option<&String> {
        self.error_counts
            .iter()
            .max_by_key(|(_, count)| *count)
            .map(|(error_type, _)| error_type)
    }
    
    /// Get error trends over time
    pub fn get_error_trends(&self) -> HashMap<String, Vec<usize>> {
        let mut trends: HashMap<String, Vec<usize>> = HashMap::new();
        
        // Group errors by hour (simplified)
        for report in &self.error_reports {
            let error_type = &report.error_type;
            // Handle timestamps before UNIX_EPOCH gracefully
            let hour = match report.timestamp.duration_since(SystemTime::UNIX_EPOCH) {
                Ok(duration) => duration.as_secs() / 3600, // Hours since epoch
                Err(_) => {
                    // Timestamp is before UNIX_EPOCH, skip this entry
                    continue;
                }
            };
            
            let trend = trends.entry(error_type.clone()).or_default();
            if trend.len() <= hour as usize {
                trend.resize(hour as usize + 1, 0);
            }
            trend[hour as usize] += 1;
        }
        
        trends
    }
    
    /// Export analytics data to JSON
    pub fn export_to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(self)
    }
    
    /// Clear all analytics data
    pub fn clear(&mut self) {
        self.error_counts.clear();
        self.common_suggestions.clear();
        self.recovery_success_rate.clear();
        self.error_reports.clear();
        self.total_errors = 0;
        self.successful_recoveries = 0;
    }
}

/// Error analytics manager for global error tracking
pub struct ErrorAnalyticsManager {
    analytics: ErrorAnalytics,
    enabled: bool,
}

impl ErrorAnalyticsManager {
    /// Create a new analytics manager
    pub fn new() -> Self {
        Self {
            analytics: ErrorAnalytics::new(),
            enabled: true,
        }
    }
    
    /// Enable or disable analytics
    pub fn set_enabled(&mut self, enabled: bool) {
        self.enabled = enabled;
    }
    
    /// Record an error
    pub fn record_error(&mut self, error: &ArxError, operation: Option<String>) {
        if self.enabled {
            self.analytics.record_error(error, operation);
        }
    }
    
    /// Record a successful recovery
    pub fn record_recovery(&mut self, error_type: &str) {
        if self.enabled {
            self.analytics.record_recovery(error_type);
        }
    }
    
    /// Get analytics data
    pub fn get_analytics(&self) -> &ErrorAnalytics {
        &self.analytics
    }
    
    /// Generate report
    pub fn generate_report(&self) -> String {
        self.analytics.generate_report()
    }
    
    /// Export to JSON
    pub fn export_to_json(&self) -> Result<String, serde_json::Error> {
        self.analytics.export_to_json()
    }
}

impl Default for ErrorAnalyticsManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_error_analytics_recording() {
        let mut analytics = ErrorAnalytics::new();
        
        let error = ArxError::ifc_processing("Test error")
            .with_suggestions(vec!["Suggestion 1".to_string()]);
        
        analytics.record_error(&error, Some("test_operation".to_string()));
        
        assert_eq!(analytics.total_errors, 1);
        assert_eq!(analytics.error_counts.get("IFC Processing"), Some(&1));
        assert_eq!(analytics.common_suggestions.get("Suggestion 1"), Some(&1));
    }
    
    #[test]
    fn test_recovery_recording() {
        let mut analytics = ErrorAnalytics::new();
        
        analytics.record_recovery("IFC Processing");
        
        assert_eq!(analytics.successful_recoveries, 1);
        assert!(analytics.recovery_success_rate.get("IFC Processing").is_some());
    }
    
    #[test]
    fn test_report_generation() {
        let mut analytics = ErrorAnalytics::new();
        
        let error = ArxError::ifc_processing("Test error");
        analytics.record_error(&error, None);
        
        let report = analytics.generate_report();
        assert!(report.contains("Total Errors: 1"));
        assert!(report.contains("IFC Processing: 1"));
    }
    
    #[test]
    fn test_analytics_manager() {
        let mut manager = ErrorAnalyticsManager::new();
        
        let error = ArxError::configuration("Test error");
        manager.record_error(&error, None);
        
        assert_eq!(manager.get_analytics().total_errors, 1);
        
        manager.set_enabled(false);
        manager.record_error(&error, None);
        
        // Should not record when disabled
        assert_eq!(manager.get_analytics().total_errors, 1);
    }
}

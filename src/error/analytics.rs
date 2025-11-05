//! Error reporting and analytics for ArxOS

use crate::error::ArxError;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::{Mutex, OnceLock};

/// Detailed error report for analytics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorReport {
    #[serde(with = "chrono::serde::ts_seconds_option")]
    pub timestamp: Option<DateTime<Utc>>,
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
#[derive(Debug, Default, Serialize, Clone)]
pub struct ErrorAnalytics {
    pub error_counts: HashMap<String, usize>,
    pub common_suggestions: HashMap<String, usize>,
    /// Track errors and recoveries per error type for accurate rate calculation
    pub error_type_totals: HashMap<String, usize>,
    pub error_type_recoveries: HashMap<String, usize>,
    /// Deprecated: Use error_type_totals and error_type_recoveries to calculate rates
    #[serde(skip)]
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
        
        // Update error type totals
        *self.error_type_totals.entry(error_type.to_string()).or_insert(0) += 1;
        
        // Create detailed error report
        let report = ErrorReport {
            timestamp: Some(Utc::now()),
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
        
        // Update recovery count for this error type
        *self.error_type_recoveries.entry(error_type.to_string()).or_insert(0) += 1;
        
        // Calculate accurate recovery rate: recoveries / total_errors for this type
        let total_errors_for_type = self.error_type_totals.get(error_type).copied().unwrap_or(0);
        let recoveries_for_type = self.error_type_recoveries.get(error_type).copied().unwrap_or(0);
        
        let rate = if total_errors_for_type > 0 {
            recoveries_for_type as f64 / total_errors_for_type as f64
        } else {
            0.0
        };
        
        self.recovery_success_rate.insert(error_type.to_string(), rate);
    }
    
    /// Get the recovery rate for a specific error type
    pub fn get_recovery_rate(&self, error_type: &str) -> f64 {
        let total_errors = self.error_type_totals.get(error_type).copied().unwrap_or(0);
        let recoveries = self.error_type_recoveries.get(error_type).copied().unwrap_or(0);
        
        if total_errors > 0 {
            (recoveries as f64 / total_errors as f64) * 100.0
        } else {
            0.0
        }
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
    /// 
    /// Returns a HashMap where keys are error types and values are HashMaps of hour -> count.
    /// This is more memory-efficient than using Vec<usize> for sparse data.
    pub fn get_error_trends(&self) -> HashMap<String, HashMap<u64, usize>> {
        let mut trends: HashMap<String, HashMap<u64, usize>> = HashMap::new();
        
        // Group errors by hour, using HashMap for efficient sparse storage
        for report in &self.error_reports {
            let error_type = &report.error_type;
            
            // Extract hour from timestamp
            let hour = if let Some(timestamp) = &report.timestamp {
                timestamp.timestamp() as u64 / 3600 // Hours since epoch
            } else {
                // Skip reports without valid timestamps
                continue;
            };
            
            // Use HashMap for sparse hour-based storage (more memory efficient)
            let trend = trends.entry(error_type.clone()).or_default();
            *trend.entry(hour).or_insert(0) += 1;
        }
        
        trends
    }
    
    /// Get error trends for a specific time window (last N hours)
    /// 
    /// This is more useful than get_error_trends() as it limits memory usage
    /// and focuses on recent errors.
    pub fn get_error_trends_window(&self, hours: u64) -> HashMap<String, HashMap<u64, usize>> {
        let mut trends: HashMap<String, HashMap<u64, usize>> = HashMap::new();
        let now_hour = Utc::now().timestamp() as u64 / 3600;
        let cutoff_hour = now_hour.saturating_sub(hours);
        
        for report in &self.error_reports {
            let error_type = &report.error_type;
            
            let hour = if let Some(timestamp) = &report.timestamp {
                timestamp.timestamp() as u64 / 3600
            } else {
                continue;
            };
            
            // Only include errors within the time window
            if hour < cutoff_hour {
                continue;
            }
            
            let trend = trends.entry(error_type.clone()).or_default();
            *trend.entry(hour).or_insert(0) += 1;
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
        self.error_type_totals.clear();
        self.error_type_recoveries.clear();
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

/// Global error analytics manager singleton
static GLOBAL_ERROR_ANALYTICS: OnceLock<Mutex<ErrorAnalyticsManager>> = OnceLock::new();

impl ErrorAnalyticsManager {
    /// Get or initialize the global error analytics manager
    pub fn global() -> &'static Mutex<ErrorAnalyticsManager> {
        GLOBAL_ERROR_ANALYTICS.get_or_init(|| Mutex::new(ErrorAnalyticsManager::new()))
    }
    
    /// Record an error to the global analytics manager
    pub fn record_global_error(error: &ArxError, operation: Option<String>) {
        if let Ok(mut manager) = Self::global().lock() {
            manager.record_error(error, operation);
        }
    }
    
    /// Record a recovery to the global analytics manager
    pub fn record_global_recovery(error_type: &str) {
        if let Ok(mut manager) = Self::global().lock() {
            manager.record_recovery(error_type);
        }
    }
    
    /// Get a snapshot of global analytics (for reporting)
    pub fn get_global_analytics() -> Option<ErrorAnalytics> {
        Self::global().lock().ok().map(|manager| {
            // Clone the analytics data for reporting
            manager.get_analytics().clone()
        })
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
        
        // Record an error first
        let error = ArxError::ifc_processing("Test error");
        analytics.record_error(&error, None);
        
        // Record a recovery
        analytics.record_recovery("IFC Processing");
        
        assert_eq!(analytics.successful_recoveries, 1);
        assert_eq!(analytics.error_type_totals.get("IFC Processing"), Some(&1));
        assert_eq!(analytics.error_type_recoveries.get("IFC Processing"), Some(&1));
        
        // Check recovery rate calculation
        let rate = analytics.get_recovery_rate("IFC Processing");
        assert_eq!(rate, 100.0); // 1 recovery / 1 error = 100%
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
    
    #[test]
    fn test_global_analytics() {
        let error = ArxError::io_error("Test error");
        ErrorAnalyticsManager::record_global_error(&error, Some("test_op".to_string()));
        
        if let Some(analytics) = ErrorAnalyticsManager::get_global_analytics() {
            assert_eq!(analytics.total_errors, 1);
        }
    }
    
    #[test]
    fn test_error_trends_window() {
        let mut analytics = ErrorAnalytics::new();
        
        let error = ArxError::ifc_processing("Test error");
        analytics.record_error(&error, None);
        
        // Get trends for last 24 hours
        let trends = analytics.get_error_trends_window(24);
        
        // Should have at least one error type
        assert!(!trends.is_empty());
    }
}

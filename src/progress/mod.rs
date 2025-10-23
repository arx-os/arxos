//! Progress reporting and progress bars for long-running operations

use indicatif::{ProgressBar, ProgressStyle};
use std::sync::Arc;

/// Progress reporter for long-running operations
pub struct ProgressReporter {
    pb: ProgressBar,
    operation_name: String,
}

impl ProgressReporter {
    /// Create a new progress reporter
    pub fn new(operation_name: &str, total_items: u64) -> Self {
        let pb = ProgressBar::new(total_items);
        pb.set_style(
            ProgressStyle::default_bar()
                .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} {msg}")
                .unwrap()
                .progress_chars("#>-"),
        );
        
        pb.set_message(format!("Starting {}", operation_name));
        
        Self {
            pb,
            operation_name: operation_name.to_string(),
        }
    }
    
    /// Update progress with current position and message
    pub fn update(&self, position: u64, message: &str) {
        self.pb.set_position(position);
        self.pb.set_message(message.to_string());
    }
    
    /// Increment progress by one
    pub fn inc(&self, message: &str) {
        self.pb.inc(1);
        self.pb.set_message(message.to_string());
    }
    
    /// Set a custom message
    pub fn set_message(&self, message: &str) {
        self.pb.set_message(message.to_string());
    }
    
    /// Finish the progress bar with success message
    pub fn finish_success(&self, message: &str) {
        self.pb.finish_with_message(format!("✅ {}", message));
    }
    
    /// Finish the progress bar with error message
    pub fn finish_error(&self, message: &str) {
        self.pb.finish_with_message(format!("❌ {}", message));
    }
    
    /// Abandon the progress bar
    pub fn abandon(&self) {
        self.pb.abandon();
    }
}

/// Progress callback function type
pub type ProgressCallback = Box<dyn Fn(u32) + Send + Sync>;

/// Progress context for operations that need progress reporting
pub struct ProgressContext {
    reporter: Option<Arc<ProgressReporter>>,
    callback: Option<ProgressCallback>,
}

impl ProgressContext {
    /// Create a new progress context
    pub fn new() -> Self {
        Self {
            reporter: None,
            callback: None,
        }
    }
    
    /// Create with progress reporter
    pub fn with_reporter(reporter: Arc<ProgressReporter>) -> Self {
        Self {
            reporter: Some(reporter),
            callback: None,
        }
    }
    
    /// Create with callback function
    pub fn with_callback(callback: ProgressCallback) -> Self {
        Self {
            reporter: None,
            callback: Some(callback),
        }
    }
    
    /// Update progress
    pub fn update(&self, progress: u32, message: &str) {
        if let Some(reporter) = &self.reporter {
            reporter.update(progress as u64, message);
        }
        
        if let Some(callback) = &self.callback {
            callback(progress);
        }
    }
    
    /// Finish with success
    pub fn finish_success(&self, message: &str) {
        if let Some(reporter) = &self.reporter {
            reporter.finish_success(message);
        }
    }
    
    /// Finish with error
    pub fn finish_error(&self, message: &str) {
        if let Some(reporter) = &self.reporter {
            reporter.finish_error(message);
        }
    }
}

impl Default for ProgressContext {
    fn default() -> Self {
        Self::new()
    }
}

/// Utility functions for common progress operations
pub mod utils {
    use super::*;
    
    /// Create a progress reporter for IFC processing
    pub fn create_ifc_progress(total_entities: u64) -> Arc<ProgressReporter> {
        Arc::new(ProgressReporter::new("IFC Processing", total_entities))
    }
    
    /// Create a progress reporter for Git operations
    pub fn create_git_progress(operation: &str) -> Arc<ProgressReporter> {
        Arc::new(ProgressReporter::new(operation, 100))
    }
    
    /// Create a progress reporter for file operations
    pub fn create_file_progress(operation: &str, total_files: u64) -> Arc<ProgressReporter> {
        Arc::new(ProgressReporter::new(operation, total_files))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_progress_reporter_creation() {
        let reporter = ProgressReporter::new("Test Operation", 100);
        assert_eq!(reporter.operation_name, "Test Operation");
    }
    
    #[test]
    fn test_progress_context_creation() {
        let context = ProgressContext::new();
        assert!(context.reporter.is_none());
        assert!(context.callback.is_none());
    }
    
    #[test]
    fn test_progress_context_with_reporter() {
        let reporter = Arc::new(ProgressReporter::new("Test", 100));
        let context = ProgressContext::with_reporter(reporter);
        assert!(context.reporter.is_some());
    }
}

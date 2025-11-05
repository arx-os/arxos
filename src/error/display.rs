//! Error display utilities for user-friendly messages

use crate::error::{ArxError, ErrorContext};

/// Configuration for error display formatting
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DisplayStyle {
    /// Use emojis for visual indicators (default)
    Emoji,
    /// Use plain text prefixes instead of emojis
    PlainText,
}

/// Global display style setting (defaults to Emoji)
static DISPLAY_STYLE: std::sync::OnceLock<std::sync::Mutex<DisplayStyle>> = 
    std::sync::OnceLock::new();

/// Set the global display style for error messages
pub fn set_display_style(style: DisplayStyle) {
    let style_mutex = DISPLAY_STYLE.get_or_init(|| std::sync::Mutex::new(DisplayStyle::Emoji));
    if let Ok(mut s) = style_mutex.lock() {
        *s = style;
    }
}

/// Get the current global display style
pub fn get_display_style() -> DisplayStyle {
    let style_mutex = DISPLAY_STYLE.get_or_init(|| std::sync::Mutex::new(DisplayStyle::Emoji));
    style_mutex.lock().map(|s| *s).unwrap_or(DisplayStyle::Emoji)
}

/// Trait for enhanced error display
pub trait ErrorDisplay {
    /// Display error with full context in a user-friendly format
    fn display_user_friendly(&self) -> String;
    
    /// Display error for debugging purposes
    fn display_debug(&self) -> String;
    
    /// Display error summary for logging
    fn display_summary(&self) -> String;
    
    /// Display error with a specific style (emoji or plain text)
    fn display_user_friendly_with_style(&self, style: DisplayStyle) -> String;
}

impl ErrorDisplay for ArxError {
    fn display_user_friendly(&self) -> String {
        self.display_user_friendly_with_style(get_display_style())
    }
    
    fn display_user_friendly_with_style(&self, style: DisplayStyle) -> String {
        let mut output = String::new();
        
        let (ifc_prefix, config_prefix, git_prefix, validation_prefix, io_prefix, yaml_prefix, spatial_prefix) = 
            match style {
                DisplayStyle::Emoji => (
                    "❌ IFC Processing Error:",
                    "⚙️ Configuration Error:",
                    "📦 Git Operation Error:",
                    "✅ Validation Error:",
                    "💾 IO Error:",
                    "📄 YAML Processing Error:",
                    "🗺️ Spatial Data Error:",
                ),
                DisplayStyle::PlainText => (
                    "[ERROR] IFC Processing Error:",
                    "[CONFIG] Configuration Error:",
                    "[GIT] Git Operation Error:",
                    "[VALIDATION] Validation Error:",
                    "[IO] IO Error:",
                    "[YAML] YAML Processing Error:",
                    "[SPATIAL] Spatial Data Error:",
                ),
            };
        
        match self {
            ArxError::IfcProcessing { message, context, .. } => {
                output.push_str(&format!("{} {}\n", ifc_prefix, message));
                Self::display_context(&mut output, context, style);
            }
            ArxError::Configuration { message, context, field } => {
                output.push_str(&format!("{} {}\n", config_prefix, message));
                if let Some(field) = field {
                    output.push_str(&format!("   Field: {}\n", field));
                }
                Self::display_context(&mut output, context, style);
            }
            ArxError::GitOperation { message, context, operation } => {
                output.push_str(&format!("{} {}\n", git_prefix, message));
                output.push_str(&format!("   Operation: {}\n", operation));
                Self::display_context(&mut output, context, style);
            }
            ArxError::Validation { message, context, file_path } => {
                output.push_str(&format!("{} {}\n", validation_prefix, message));
                if let Some(file_path) = file_path {
                    output.push_str(&format!("   File: {}\n", file_path));
                }
                Self::display_context(&mut output, context, style);
            }
            ArxError::IoError { message, context, path } => {
                output.push_str(&format!("{} {}\n", io_prefix, message));
                if let Some(path) = path {
                    output.push_str(&format!("   Path: {}\n", path));
                }
                Self::display_context(&mut output, context, style);
            }
            ArxError::YamlProcessing { message, context, file_path } => {
                output.push_str(&format!("{} {}\n", yaml_prefix, message));
                if let Some(file_path) = file_path {
                    output.push_str(&format!("   File: {}\n", file_path));
                }
                Self::display_context(&mut output, context, style);
            }
            ArxError::SpatialData { message, context, entity_type } => {
                output.push_str(&format!("{} {}\n", spatial_prefix, message));
                if let Some(entity_type) = entity_type {
                    output.push_str(&format!("   Entity Type: {}\n", entity_type));
                }
                Self::display_context(&mut output, context, style);
            }
        }
        
        output
    }
    
    fn display_debug(&self) -> String {
        let mut output = String::new();
        
        output.push_str(&format!("DEBUG ERROR: {}\n", self));
        
        let context = self.context();
        if let Some(debug_info) = &context.debug_info {
            output.push_str(&format!("Debug Info: {}\n", debug_info));
        }
        
        if let Some(file_path) = &context.file_path {
            output.push_str(&format!("File: {}\n", file_path));
        }
        
        if let Some(line_number) = context.line_number {
            output.push_str(&format!("Line: {}\n", line_number));
        }
        
        output
    }
    
    fn display_summary(&self) -> String {
        match self {
            ArxError::IfcProcessing { message, .. } => format!("IFC: {}", message),
            ArxError::Configuration { message, .. } => format!("Config: {}", message),
            ArxError::GitOperation { message, .. } => format!("Git: {}", message),
            ArxError::Validation { message, .. } => format!("Validation: {}", message),
            ArxError::IoError { message, .. } => format!("IO: {}", message),
            ArxError::YamlProcessing { message, .. } => format!("YAML: {}", message),
            ArxError::SpatialData { message, .. } => format!("Spatial: {}", message),
        }
    }
}

impl ArxError {
    fn display_context(output: &mut String, context: &ErrorContext, style: DisplayStyle) {
        let (suggestions_label, recovery_label, debug_label, help_label, file_label, line_label) = 
            match style {
                DisplayStyle::Emoji => (
                    "   💡 Suggestions:",
                    "   🔧 Recovery Steps:",
                    "   🐛 Debug Info:",
                    "   📖 Help:",
                    "   📁 File:",
                    "   📍 Line:",
                ),
                DisplayStyle::PlainText => (
                    "   [SUGGESTIONS]",
                    "   [RECOVERY STEPS]",
                    "   [DEBUG]",
                    "   [HELP]",
                    "   [FILE]",
                    "   [LINE]",
                ),
            };
        
        if !context.suggestions.is_empty() {
            output.push_str(&format!("{}\n", suggestions_label));
            for suggestion in &context.suggestions {
                output.push_str(&format!("      • {}\n", suggestion));
            }
        }
        
        if !context.recovery_steps.is_empty() {
            output.push_str(&format!("{}\n", recovery_label));
            for (i, step) in context.recovery_steps.iter().enumerate() {
                output.push_str(&format!("      {}. {}\n", i + 1, step));
            }
        }
        
        if let Some(debug_info) = &context.debug_info {
            output.push_str(&format!("{} {}\n", debug_label, debug_info));
        }
        
        if let Some(help_url) = &context.help_url {
            output.push_str(&format!("{} {}\n", help_label, help_url));
        }
        
        if let Some(file_path) = &context.file_path {
            output.push_str(&format!("{} {}\n", file_label, file_path));
        }
        
        if let Some(line_number) = context.line_number {
            output.push_str(&format!("{} {}\n", line_label, line_number));
        }
    }
}

/// Utility functions for error formatting
pub mod utils {
    use super::*;
    
    /// Format multiple errors into a single report
    pub fn format_error_report(errors: &[ArxError]) -> String {
        if errors.is_empty() {
            return "No errors occurred.".to_string();
        }
        
        let mut report = String::new();
        report.push_str(&format!("📊 Error Report ({} errors)\n", errors.len()));
        report.push_str(&"=".repeat(50));
        report.push('\n');
        
        for (i, error) in errors.iter().enumerate() {
            report.push_str(&format!("\n{}. {}\n", i + 1, error.display_summary()));
            if !error.context().suggestions.is_empty() {
                report.push_str("   Suggestions: ");
                report.push_str(&error.context().suggestions.join(", "));
                report.push('\n');
            }
        }
        
        report
    }
    
    /// Create a summary of error statistics
    pub fn create_error_summary(errors: &[ArxError]) -> String {
        use std::collections::HashMap;
        
        let mut counts: HashMap<String, usize> = HashMap::new();
        
        for error in errors {
            let error_type = match error {
                ArxError::IfcProcessing { .. } => "IFC Processing",
                ArxError::Configuration { .. } => "Configuration",
                ArxError::GitOperation { .. } => "Git Operation",
                ArxError::Validation { .. } => "Validation",
                ArxError::IoError { .. } => "IO Error",
                ArxError::YamlProcessing { .. } => "YAML Processing",
                ArxError::SpatialData { .. } => "Spatial Data",
            };
            
            *counts.entry(error_type.to_string()).or_insert(0) += 1;
        }
        
        let mut summary = String::new();
        summary.push_str("📈 Error Summary:\n");
        for (error_type, count) in counts {
            summary.push_str(&format!("   {}: {}\n", error_type, count));
        }
        
        summary
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_user_friendly_display() {
        let error = ArxError::ifc_processing("Test error")
            .with_suggestions(vec!["Suggestion 1".to_string()])
            .with_recovery(vec!["Step 1".to_string()]);
        
        let display = error.display_user_friendly();
        assert!(display.contains("❌ IFC Processing Error"));
        assert!(display.contains("💡 Suggestions"));
        assert!(display.contains("🔧 Recovery Steps"));
    }
    
    #[test]
    fn test_debug_display() {
        let error = ArxError::ifc_processing("Test error")
            .with_debug_info("Debug info")
            .with_file_path("test.ifc")
            .with_line_number(42);
        
        let display = error.display_debug();
        assert!(display.contains("DEBUG ERROR"));
        assert!(display.contains("Debug Info: Debug info"));
        assert!(display.contains("File: test.ifc"));
        assert!(display.contains("Line: 42"));
    }
    
    #[test]
    fn test_error_report_formatting() {
        let errors = vec![
            ArxError::ifc_processing("Error 1"),
            ArxError::configuration("Error 2"),
        ];
        
        let report = utils::format_error_report(&errors);
        assert!(report.contains("Error Report (2 errors)"));
        assert!(report.contains("1. IFC: Error 1"));
        assert!(report.contains("2. Config: Error 2"));
    }
}

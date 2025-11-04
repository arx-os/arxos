//! Export Format Types
//!
//! Defines supported export formats.

/// Export formats supported
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ExportFormat {
    /// Plain text (no colors)
    Text,
    /// ANSI colored text
    Ansi,
    /// HTML with colors
    Html,
    /// Markdown
    Markdown,
}

impl ExportFormat {
    /// Get all available formats
    pub fn all() -> Vec<ExportFormat> {
        vec![
            ExportFormat::Text,
            ExportFormat::Ansi,
            ExportFormat::Html,
            ExportFormat::Markdown,
        ]
    }
    
    /// Get format name
    pub fn name(&self) -> &'static str {
        match self {
            ExportFormat::Text => "Text",
            ExportFormat::Ansi => "ANSI",
            ExportFormat::Html => "HTML",
            ExportFormat::Markdown => "Markdown",
        }
    }
    
    /// Get file extension
    pub fn extension(&self) -> &'static str {
        match self {
            ExportFormat::Text => "txt",
            ExportFormat::Ansi => "ansi",
            ExportFormat::Html => "html",
            ExportFormat::Markdown => "md",
        }
    }
}


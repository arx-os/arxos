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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_export_format_all() {
        let formats = ExportFormat::all();
        assert_eq!(formats.len(), 4, "Should have 4 formats");
        assert!(formats.contains(&ExportFormat::Text));
        assert!(formats.contains(&ExportFormat::Ansi));
        assert!(formats.contains(&ExportFormat::Html));
        assert!(formats.contains(&ExportFormat::Markdown));
    }

    #[test]
    fn test_export_format_names() {
        assert_eq!(ExportFormat::Text.name(), "Text");
        assert_eq!(ExportFormat::Ansi.name(), "ANSI");
        assert_eq!(ExportFormat::Html.name(), "HTML");
        assert_eq!(ExportFormat::Markdown.name(), "Markdown");
    }

    #[test]
    fn test_export_format_extensions() {
        assert_eq!(ExportFormat::Text.extension(), "txt");
        assert_eq!(ExportFormat::Ansi.extension(), "ansi");
        assert_eq!(ExportFormat::Html.extension(), "html");
        assert_eq!(ExportFormat::Markdown.extension(), "md");
    }

    #[test]
    fn test_export_format_equality() {
        assert_eq!(ExportFormat::Text, ExportFormat::Text);
        assert_eq!(ExportFormat::Ansi, ExportFormat::Ansi);
        assert_ne!(ExportFormat::Text, ExportFormat::Ansi);
        assert_ne!(ExportFormat::Html, ExportFormat::Markdown);
    }
}

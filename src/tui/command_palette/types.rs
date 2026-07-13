//! Command Palette Types
//!
//! Defines core types for the command palette system.

/// Command entry in the palette
#[derive(Debug, Clone)]
pub struct CommandEntry {
    /// Command name/keyword
    pub name: String,
    /// Full command with arguments
    pub full_command: String,
    /// Description
    pub description: String,
    /// Category
    pub category: CommandCategory,
    /// Keyboard shortcut (if any)
    pub shortcut: Option<String>,
}

/// Command categories
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum CommandCategory {
    /// Building management commands
    Building,
    /// Equipment management
    Equipment,
    /// Room management
    Room,
    /// Git/version control
    Git,
    /// Import/export
    ImportExport,
    /// AR integration
    AR,
    /// Rendering/visualization
    Render,
    /// Search and filtering
    Search,
    /// Configuration
    Config,
    /// Sensors and monitoring
    Sensors,
    /// Health and validation
    Health,
    /// Documentation
    Documentation,
    /// Other/utility
    Other,
}

impl CommandCategory {
    /// Get category name
    pub fn name(&self) -> &'static str {
        match self {
            CommandCategory::Building => "Building",
            CommandCategory::Equipment => "Equipment",
            CommandCategory::Room => "Room",
            CommandCategory::Git => "Git",
            CommandCategory::ImportExport => "Import/Export",
            CommandCategory::AR => "AR",
            CommandCategory::Render => "Render",
            CommandCategory::Search => "Search",
            CommandCategory::Config => "Config",
            CommandCategory::Sensors => "Sensors",
            CommandCategory::Health => "Health",
            CommandCategory::Documentation => "Documentation",
            CommandCategory::Other => "Other",
        }
    }

    /// Get category icon
    pub fn icon(&self) -> &'static str {
        match self {
            CommandCategory::Building => "🏢",
            CommandCategory::Equipment => "⚙️",
            CommandCategory::Room => "🚪",
            CommandCategory::Git => "📦",
            CommandCategory::ImportExport => "📤",
            CommandCategory::AR => "📱",
            CommandCategory::Render => "🎨",
            CommandCategory::Search => "🔍",
            CommandCategory::Config => "⚙️",
            CommandCategory::Sensors => "📊",
            CommandCategory::Health => "💚",
            CommandCategory::Documentation => "📚",
            CommandCategory::Other => "📋",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_command_category_names() {
        let categories = vec![
            CommandCategory::Building,
            CommandCategory::Equipment,
            CommandCategory::Room,
            CommandCategory::Git,
            CommandCategory::ImportExport,
            CommandCategory::AR,
            CommandCategory::Render,
            CommandCategory::Search,
            CommandCategory::Config,
            CommandCategory::Sensors,
            CommandCategory::Health,
            CommandCategory::Documentation,
            CommandCategory::Other,
        ];

        for category in categories {
            let name = category.name();
            assert!(
                !name.is_empty(),
                "Category {:?} should have a name",
                category
            );
        }
    }

    #[test]
    fn test_command_category_icons() {
        let categories = vec![
            CommandCategory::Building,
            CommandCategory::Equipment,
            CommandCategory::Room,
            CommandCategory::Git,
            CommandCategory::ImportExport,
            CommandCategory::AR,
            CommandCategory::Render,
            CommandCategory::Search,
            CommandCategory::Config,
            CommandCategory::Sensors,
            CommandCategory::Health,
            CommandCategory::Documentation,
            CommandCategory::Other,
        ];

        for category in categories {
            let icon = category.icon();
            assert!(
                !icon.is_empty(),
                "Category {:?} should have an icon",
                category
            );
        }
    }

    #[test]
    fn test_command_entry_structure() {
        let entry = CommandEntry {
            name: "test".to_string(),
            full_command: "arxos test".to_string(),
            description: "Test command".to_string(),
            category: CommandCategory::Other,
            shortcut: Some("Ctrl+T".to_string()),
        };

        assert_eq!(entry.name, "test");
        assert_eq!(entry.full_command, "arxos test");
        assert_eq!(entry.description, "Test command");
        assert_eq!(entry.category, CommandCategory::Other);
        assert_eq!(entry.shortcut, Some("Ctrl+T".to_string()));
    }

    #[test]
    fn test_command_category_equality() {
        assert_eq!(CommandCategory::Building, CommandCategory::Building);
        assert_eq!(CommandCategory::Equipment, CommandCategory::Equipment);
        assert_ne!(CommandCategory::Building, CommandCategory::Equipment);
        assert_ne!(CommandCategory::Git, CommandCategory::Room);
    }
}

//! Help System Types
//!
//! Defines core types for the contextual help system.

/// Help context identifies which screen/feature is active
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HelpContext {
    EquipmentBrowser,
    RoomExplorer,
    StatusDashboard,
    SearchBrowser,
    WatchDashboard,
    ConfigWizard,
    ArPendingManager,
    DiffViewer,
    HealthDashboard,
    Interactive3D,
    CommandPalette,
    General,
}

/// Keyboard shortcut definition
#[derive(Debug, Clone)]
pub struct Shortcut {
    pub key: String,
    pub description: String,
    pub category: ShortcutCategory,
}

/// Shortcut categories for organization
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ShortcutCategory {
    Navigation,
    Actions,
    Views,
    Filters,
    General,
}

/// Help system state
pub struct HelpSystem {
    pub show_overlay: bool,
    pub show_cheat_sheet: bool,
    pub current_context: HelpContext,
    pub search_query: String,
    pub selected_category: Option<ShortcutCategory>,
}

impl HelpSystem {
    pub fn new(context: HelpContext) -> Self {
        Self {
            show_overlay: false,
            show_cheat_sheet: false,
            current_context: context,
            search_query: String::new(),
            selected_category: None,
        }
    }

    pub fn toggle_overlay(&mut self) {
        self.show_overlay = !self.show_overlay;
    }

    pub fn toggle_cheat_sheet(&mut self) {
        self.show_cheat_sheet = !self.show_cheat_sheet;
    }

    pub fn set_context(&mut self, context: HelpContext) {
        self.current_context = context;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_help_system_new() {
        let system = HelpSystem::new(HelpContext::General);
        assert!(!system.show_overlay);
        assert!(!system.show_cheat_sheet);
        assert_eq!(system.current_context, HelpContext::General);
        assert!(system.search_query.is_empty());
        assert!(system.selected_category.is_none());
    }

    #[test]
    fn test_help_system_toggle_overlay() {
        let mut system = HelpSystem::new(HelpContext::General);
        assert!(!system.show_overlay);

        system.toggle_overlay();
        assert!(system.show_overlay);

        system.toggle_overlay();
        assert!(!system.show_overlay);
    }

    #[test]
    fn test_help_system_toggle_cheat_sheet() {
        let mut system = HelpSystem::new(HelpContext::General);
        assert!(!system.show_cheat_sheet);

        system.toggle_cheat_sheet();
        assert!(system.show_cheat_sheet);

        system.toggle_cheat_sheet();
        assert!(!system.show_cheat_sheet);
    }

    #[test]
    fn test_help_system_set_context() {
        let mut system = HelpSystem::new(HelpContext::General);
        assert_eq!(system.current_context, HelpContext::General);

        system.set_context(HelpContext::EquipmentBrowser);
        assert_eq!(system.current_context, HelpContext::EquipmentBrowser);

        system.set_context(HelpContext::CommandPalette);
        assert_eq!(system.current_context, HelpContext::CommandPalette);
    }

    #[test]
    fn test_help_context_equality() {
        assert_eq!(HelpContext::EquipmentBrowser, HelpContext::EquipmentBrowser);
        assert_ne!(HelpContext::EquipmentBrowser, HelpContext::RoomExplorer);
        assert_ne!(HelpContext::General, HelpContext::CommandPalette);
    }

    #[test]
    fn test_shortcut_category_equality() {
        assert_eq!(ShortcutCategory::Navigation, ShortcutCategory::Navigation);
        assert_ne!(ShortcutCategory::Navigation, ShortcutCategory::Actions);
        assert_ne!(ShortcutCategory::Views, ShortcutCategory::Filters);
    }
}

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
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
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


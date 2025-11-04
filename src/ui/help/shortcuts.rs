//! Keyboard Shortcut Definitions
//!
//! Provides all keyboard shortcuts available in ArxOS TUI.

use super::types::{Shortcut, ShortcutCategory};

/// Get all keyboard shortcuts
pub fn get_all_shortcuts() -> Vec<Shortcut> {
    vec![
        // Navigation
        Shortcut { 
            key: "↑/↓ or j/k".to_string(), 
            description: "Navigate up/down".to_string(), 
            category: ShortcutCategory::Navigation 
        },
        Shortcut { 
            key: "←/→ or h/l".to_string(), 
            description: "Navigate left/right".to_string(), 
            category: ShortcutCategory::Navigation 
        },
        Shortcut { 
            key: "Enter".to_string(), 
            description: "Select/Activate".to_string(), 
            category: ShortcutCategory::Navigation 
        },
        Shortcut { 
            key: "Tab".to_string(), 
            description: "Switch sections/tabs".to_string(), 
            category: ShortcutCategory::Navigation 
        },
        Shortcut { 
            key: "Esc".to_string(), 
            description: "Cancel/Back".to_string(), 
            category: ShortcutCategory::Navigation 
        },
        
        // Actions
        Shortcut { 
            key: "r".to_string(), 
            description: "Refresh data".to_string(), 
            category: ShortcutCategory::Actions 
        },
        Shortcut { 
            key: "s".to_string(), 
            description: "Save/Search".to_string(), 
            category: ShortcutCategory::Actions 
        },
        Shortcut { 
            key: "e".to_string(), 
            description: "Edit".to_string(), 
            category: ShortcutCategory::Actions 
        },
        Shortcut { 
            key: "d".to_string(), 
            description: "Toggle details".to_string(), 
            category: ShortcutCategory::Actions 
        },
        Shortcut { 
            key: "f".to_string(), 
            description: "Filter".to_string(), 
            category: ShortcutCategory::Actions 
        },
        Shortcut { 
            key: "y".to_string(), 
            description: "Yes/Confirm".to_string(), 
            category: ShortcutCategory::Actions 
        },
        Shortcut { 
            key: "n".to_string(), 
            description: "No/Reject".to_string(), 
            category: ShortcutCategory::Actions 
        },
        
        // Views
        Shortcut { 
            key: "v".to_string(), 
            description: "Cycle view mode".to_string(), 
            category: ShortcutCategory::Views 
        },
        Shortcut { 
            key: "t".to_string(), 
            description: "Toggle view type".to_string(), 
            category: ShortcutCategory::Views 
        },
        Shortcut { 
            key: "i".to_string(), 
            description: "Toggle info panel".to_string(), 
            category: ShortcutCategory::Views 
        },
        Shortcut { 
            key: "c".to_string(), 
            description: "Collapse/Expand".to_string(), 
            category: ShortcutCategory::Views 
        },
        
        // Filters
        Shortcut { 
            key: "/".to_string(), 
            description: "Search".to_string(), 
            category: ShortcutCategory::Filters 
        },
        Shortcut { 
            key: "f".to_string(), 
            description: "Filter by type".to_string(), 
            category: ShortcutCategory::Filters 
        },
        
        // General
        Shortcut { 
            key: "? or h".to_string(), 
            description: "Show help".to_string(), 
            category: ShortcutCategory::General 
        },
        Shortcut { 
            key: "Ctrl+H".to_string(), 
            description: "Shortcut cheat sheet".to_string(), 
            category: ShortcutCategory::General 
        },
        Shortcut { 
            key: "q".to_string(), 
            description: "Quit".to_string(), 
            category: ShortcutCategory::General 
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_all_shortcuts() {
        let shortcuts = get_all_shortcuts();
        assert!(!shortcuts.is_empty(), "Should return shortcuts");
        // Should have shortcuts from multiple categories
        assert!(shortcuts.len() > 5, "Should have multiple shortcuts");
    }

    #[test]
    fn test_shortcuts_by_category() {
        let shortcuts = get_all_shortcuts();
        let navigation: Vec<_> = shortcuts.iter()
            .filter(|s| s.category == ShortcutCategory::Navigation)
            .collect();
        let actions: Vec<_> = shortcuts.iter()
            .filter(|s| s.category == ShortcutCategory::Actions)
            .collect();
        let views: Vec<_> = shortcuts.iter()
            .filter(|s| s.category == ShortcutCategory::Views)
            .collect();
        let filters: Vec<_> = shortcuts.iter()
            .filter(|s| s.category == ShortcutCategory::Filters)
            .collect();
        let general: Vec<_> = shortcuts.iter()
            .filter(|s| s.category == ShortcutCategory::General)
            .collect();
        
        assert!(!navigation.is_empty(), "Should have Navigation shortcuts");
        assert!(!actions.is_empty(), "Should have Actions shortcuts");
        assert!(!views.is_empty(), "Should have Views shortcuts");
        assert!(!filters.is_empty(), "Should have Filters shortcuts");
        assert!(!general.is_empty(), "Should have General shortcuts");
    }

    #[test]
    fn test_shortcut_categories_coverage() {
        let shortcuts = get_all_shortcuts();
        let categories: std::collections::HashSet<_> = shortcuts.iter()
            .map(|s| s.category)
            .collect();
        
        // All 5 categories should be represented
        assert!(categories.contains(&ShortcutCategory::Navigation));
        assert!(categories.contains(&ShortcutCategory::Actions));
        assert!(categories.contains(&ShortcutCategory::Views));
        assert!(categories.contains(&ShortcutCategory::Filters));
        assert!(categories.contains(&ShortcutCategory::General));
        assert_eq!(categories.len(), 5, "Should have all 5 categories");
    }

    #[test]
    fn test_shortcut_structure() {
        let shortcuts = get_all_shortcuts();
        for shortcut in &shortcuts {
            assert!(!shortcut.key.is_empty(), "Shortcut key should not be empty");
            assert!(!shortcut.description.is_empty(), "Shortcut description should not be empty");
        }
    }

    #[test]
    fn test_shortcut_no_empty_fields() {
        let shortcuts = get_all_shortcuts();
        for shortcut in &shortcuts {
            assert!(!shortcut.key.trim().is_empty(), "Shortcut key should not be empty or whitespace");
            assert!(!shortcut.description.trim().is_empty(), "Shortcut description should not be empty or whitespace");
        }
    }
}


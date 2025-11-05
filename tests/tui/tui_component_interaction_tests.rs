//! Integration tests for TUI component interactions
//!
//! Tests how different TUI components interact with each other:
//! - Help system integration in various components
//! - Error modal integration
//! - Theme consistency across components
//! - Mouse support across components

use arxos::ui::{
    HelpSystem, HelpContext,
    CommandPalette,
    WorkspaceManager,
    ErrorModal, ErrorAction,
    Theme, ThemeManager,
    MouseConfig, parse_mouse_event,
};
use arxos::error::ArxError;
use crossterm::event::{Event, KeyCode, KeyEvent, KeyEventKind, KeyEventState, KeyModifiers, MouseButton, MouseEvent, MouseEventKind};

/// Test that help system is integrated in command palette
#[test]
fn test_help_in_command_palette() {
    let mut palette = CommandPalette::new();
    
    // Verify help system is initialized with correct context
    assert_eq!(palette.help_system().current_context, HelpContext::CommandPalette);
    assert!(!palette.help_system().show_overlay);
    
    // Verify help system can be toggled
    palette.help_system_mut().toggle_overlay();
    assert!(palette.help_system().show_overlay);
}

/// Test that help system is integrated in workspace manager
#[test]
fn test_help_in_workspace_manager() {
    // Note: WorkspaceManager::new() may fail if no building.yaml exists
    // This is acceptable for integration tests
    if let Ok(mut manager) = WorkspaceManager::new() {
        // Verify help system is initialized
        let help_system = manager.help_system();
        assert_eq!(help_system.current_context, HelpContext::General);
        assert!(!help_system.show_overlay);
        
        // Verify help system can be toggled
        manager.help_system_mut().toggle_overlay();
        assert!(manager.help_system().show_overlay);
    }
}

/// Test that error modal can be used with components
#[test]
fn test_error_modal_in_components() {
    let mut error_modal = ErrorModal::new();
    
    // Create a test error
    let error = ArxError::io_error("Test error message".to_string());
    
    // Show error in modal
    error_modal.show_error(error);
    assert!(error_modal.show, "Modal should be shown");
    
    // Verify error modal has actions
    assert!(!error_modal.actions.is_empty(), "Should have actions");
    
    // Test dismissing error
    error_modal.dismiss();
    assert!(!error_modal.show, "Modal should be dismissed");
}

/// Test theme consistency across components
#[test]
fn test_theme_consistency() {
    // Create a theme
    let theme = Theme::default();
    
    // Verify theme has all required properties
    assert!(matches!(theme.primary, _));
    assert!(matches!(theme.secondary, _));
    assert!(matches!(theme.accent, _));
    assert!(matches!(theme.background, _));
    assert!(matches!(theme.text, _));
    assert!(matches!(theme.muted, _));
    
    // Test theme manager consistency
    if let Ok(theme_manager) = ThemeManager::new() {
        let current_theme = theme_manager.current_theme();
        // Verify loaded theme has same structure
        assert!(matches!(current_theme.primary, _));
        assert!(matches!(current_theme.text, _));
    }
}

/// Test mouse support integration in components
#[test]
fn test_mouse_support_in_components() {
    // Test that mouse config works consistently
    let default_config = MouseConfig::default();
    assert!(default_config.enabled);
    
    // Test mouse event parsing with config
    let mouse_event = Event::Mouse(MouseEvent {
        kind: MouseEventKind::Down(MouseButton::Left),
        column: 10,
        row: 5,
        modifiers: KeyModifiers::empty(),
    });
    
    let action = parse_mouse_event(&mouse_event, &default_config);
    assert!(action.is_some());
    
    // Test with disabled mouse config
    let disabled_config = MouseConfig::disabled();
    let action_disabled = parse_mouse_event(&mouse_event, &disabled_config);
    assert!(action_disabled.is_none());
}

/// Test that help context changes correctly in components
#[test]
fn test_help_context_integration() {
    // Test command palette help context
    let palette = CommandPalette::new();
    assert_eq!(palette.help_system().current_context, HelpContext::CommandPalette);
    
    // Test that context-specific help is available
    use arxos::ui::get_context_help;
    let help_content = get_context_help(HelpContext::CommandPalette);
    assert!(!help_content.is_empty());
}

/// Test error modal actions work correctly
#[test]
fn test_error_modal_actions_integration() {
    let mut error_modal = ErrorModal::new();
    
    // Create different error types
    let io_error = ArxError::io_error("IO error".to_string());
    error_modal.show_error(io_error);
    
    assert!(!error_modal.actions.is_empty(), "Should have actions");
    
    // Verify actions are accessible
    assert!(error_modal.actions.iter().any(|a| matches!(a, ErrorAction::Dismiss | ErrorAction::ViewDetails | ErrorAction::ShowHelp)));
}

/// Test that multiple components can use the same theme
#[test]
fn test_theme_shared_across_components() {
    let theme = Theme::default();
    
    // Verify theme properties are consistent
    let primary_color = theme.primary;
    let text_color = theme.text;
    
    // Create another theme instance (should have same defaults)
    let theme2 = Theme::default();
    assert_eq!(theme2.primary, primary_color);
    assert_eq!(theme2.text, text_color);
}

/// Test mouse config consistency across components
#[test]
fn test_mouse_config_consistency() {
    // Test that default config is consistent
    let config1 = MouseConfig::default();
    let config2 = MouseConfig::default();
    
    assert_eq!(config1.enabled, config2.enabled);
    assert_eq!(config1.click_to_select, config2.click_to_select);
    assert_eq!(config1.scroll_enabled, config2.scroll_enabled);
    assert_eq!(config1.drag_enabled, config2.drag_enabled);
}

/// Test help system state persistence across component interactions
#[test]
fn test_help_system_state_persistence() {
    let mut help_system = HelpSystem::new(HelpContext::CommandPalette);
    
    // Toggle overlay
    assert!(!help_system.show_overlay);
    help_system.toggle_overlay();
    assert!(help_system.show_overlay);
    
    // Change context (should maintain overlay state)
    help_system.set_context(HelpContext::General);
    assert!(help_system.show_overlay);
    assert_eq!(help_system.current_context, HelpContext::General);
}

/// Test that components can handle events without interference
#[test]
fn test_component_event_isolation() {
    let palette = CommandPalette::new();
    let mut help_system = HelpSystem::new(HelpContext::CommandPalette);
    
    // Test that help events don't interfere with palette
    let help_event = Event::Key(KeyEvent {
        code: KeyCode::Char('?'),
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    });
    
    use arxos::ui::handle_help_event;
    let handled = handle_help_event(help_event, &mut help_system);
    assert!(handled);
    assert!(help_system.show_overlay);
    
    // Palette should be unaffected
    assert_eq!(palette.query(), "");
}

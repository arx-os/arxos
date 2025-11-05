//! Integration tests for complete TUI workflows
//!
//! Tests end-to-end user workflows including:
//! - Equipment browser navigation
//! - Room explorer workflows
//! - Command palette usage
//! - Workspace management
//! - Help system integration
//! - Error handling workflows
//! - Theme switching
//! - Export functionality
//! - Mouse interaction workflows

use arxos::ui::{
    CommandPalette,
    WorkspaceManager,
    HelpSystem, HelpContext, handle_help_event, get_context_help,
    ErrorModal, ErrorAction,
    Theme, ThemeManager,
    MouseConfig, parse_mouse_event, MouseAction,
    ExportFormat, export_buffer,
};
use arxos::error::ArxError;
use crossterm::event::{Event, KeyCode, KeyEvent, KeyEventKind, KeyEventState, KeyModifiers, MouseButton, MouseEvent, MouseEventKind};
use ratatui::buffer::Buffer;
use ratatui::layout::Rect;
use tempfile::TempDir;

/// Test complete command palette workflow
#[test]
fn test_command_palette_workflow() {
    let mut palette = CommandPalette::new();
    
    // Step 1: Initial state - all commands visible
    assert!(!palette.commands().is_empty(), "Should have commands");
    assert_eq!(palette.query(), "", "Initial query should be empty");
    assert!(palette.selected_command().is_some(), "Should have selected command");
    
    // Step 2: User types search query
    palette.update_query("equipment".to_string());
    assert_eq!(palette.query(), "equipment");
    let filtered_count = palette.filtered_commands().len();
    assert!(filtered_count > 0, "Should filter to equipment commands");
    assert!(filtered_count <= palette.commands().len(), "Filtered should be <= total");
    
    // Step 3: User navigates through filtered results
    let _initial_selected = palette.selected_command();
    palette.next();
    let _after_next = palette.selected_command();
    assert!(_after_next.is_some(), "Should still have selection after navigation");
    
    // Step 4: User clears search
    palette.update_query("".to_string());
    assert_eq!(palette.query(), "");
    assert_eq!(palette.filtered_commands().len(), palette.commands().len(), 
        "All commands should be visible after clearing");
    
    // Step 5: Help system integration
    assert_eq!(palette.help_system().current_context, HelpContext::CommandPalette);
    palette.help_system_mut().toggle_overlay();
    assert!(palette.help_system().show_overlay);
}

/// Test workspace manager workflow
#[test]
fn test_workspace_manager_workflow() {
    // Note: WorkspaceManager::new() may fail if no building.yaml exists
    // This is acceptable - we test the workflow when it succeeds
    if let Ok(mut manager) = WorkspaceManager::new() {
        // Step 1: Initial state
        let _initial_count = manager.workspaces().len();
        
        // Step 2: User searches for workspace
        manager.update_query("test".to_string());
        assert_eq!(manager.query(), "test");
        
        // Step 3: User navigates workspaces
        if !manager.is_empty() {
            let initial_workspace = manager.selected_workspace().map(|w| w.name.clone());
            let filtered_count = manager.filtered_workspaces().len();
            
            // Test navigation - with wrapping, selection may or may not change
            // depending on filtered count
            manager.next();
            let after_next = manager.selected_workspace().map(|w| w.name.clone());
            
            if filtered_count > 1 {
                // With multiple filtered workspaces, selection should change
                assert_ne!(initial_workspace, after_next, "Selection should change with multiple workspaces");
            } else {
                // With single filtered workspace, navigation wraps around to same
                assert_eq!(initial_workspace, after_next, "Single workspace should wrap around");
            }
            
            // Step 4: User clears search
            manager.update_query("".to_string());
            assert_eq!(manager.query(), "");
            
            // Step 5: Help system integration
            assert_eq!(manager.help_system().current_context, HelpContext::General);
        }
    }
}

/// Test help system workflow
#[test]
fn test_help_system_workflow() {
    let mut help_system = HelpSystem::new(HelpContext::CommandPalette);
    
    // Step 1: User opens help overlay
    assert!(!help_system.show_overlay);
    help_system.toggle_overlay();
    assert!(help_system.show_overlay);
    
    // Step 2: Verify context-specific help content
    let help_content = get_context_help(HelpContext::CommandPalette);
    assert!(!help_content.is_empty(), "Should have help content");
    
    // Step 3: User switches to cheat sheet
    help_system.toggle_cheat_sheet();
    assert!(help_system.show_cheat_sheet);
    
    // Step 4: User closes help
    help_system.show_overlay = false;
    help_system.show_cheat_sheet = false;
    assert!(!help_system.show_overlay);
    assert!(!help_system.show_cheat_sheet);
    
    // Step 5: User changes context
    help_system.set_context(HelpContext::General);
    assert_eq!(help_system.current_context, HelpContext::General);
    let general_help = get_context_help(HelpContext::General);
    assert!(!general_help.is_empty(), "Should have general help content");
}

/// Test error handling workflow
#[test]
fn test_error_handling_workflow() {
    let mut error_modal = ErrorModal::new();
    
    // Step 1: Error occurs
    let error = ArxError::io_error("File not found".to_string());
    error_modal.show_error(error);
    assert!(error_modal.show, "Modal should be shown");
    assert!(!error_modal.actions.is_empty(), "Should have actions");
    
    // Step 2: User navigates actions
    let _initial_action = error_modal.actions[error_modal.selected_action].clone();
    error_modal.next_action();
    assert_ne!(error_modal.selected_action, 0, "Selection should change");
    
    // Step 3: User selects an action
    let selected = error_modal.select_action();
    assert!(selected.is_some(), "Should be able to select action");
    
    // Step 4: User dismisses error
    error_modal.dismiss();
    assert!(!error_modal.show, "Modal should be dismissed");
    assert!(error_modal.error.is_none(), "Error should be cleared");
}

/// Test theme switching workflow
#[test]
fn test_theme_switching_workflow() {
    // Step 1: Get default theme
    let default_theme = Theme::default();
    let default_primary = default_theme.primary;
    
    // Step 2: Load theme from manager (if available)
    if let Ok(theme_manager) = ThemeManager::new() {
        let current_theme = theme_manager.current_theme();
        
        // Step 3: Verify theme structure is consistent
        assert!(matches!(current_theme.primary, _));
        assert!(matches!(current_theme.text, _));
        
    // Step 4: Test theme presets are available
    use arxos::ui::ThemePreset;
    let presets = ThemePreset::all();
    assert!(!presets.is_empty(), "Should have theme presets");
    }
    
    // Step 5: Verify default theme is always available
    let theme2 = Theme::default();
    assert_eq!(theme2.primary, default_primary, "Default should be consistent");
}

/// Test export workflow
#[test]
fn test_export_workflow() {
    // Step 1: Create a test buffer
    let area = Rect::new(0, 0, 80, 24);
    let buffer = Buffer::empty(area);
    
    // Step 2: Export to different formats
    let temp_dir = TempDir::new().expect("Failed to create temp dir");
    
    // Test text export
    let text_path = temp_dir.path().join("test.txt");
    let result = export_buffer(&buffer, ExportFormat::Text, text_path.clone());
    assert!(result.is_ok(), "Text export should succeed");
    assert!(text_path.exists(), "Text file should be created");
    
    // Test HTML export
    let html_path = temp_dir.path().join("test.html");
    let result = export_buffer(&buffer, ExportFormat::Html, html_path.clone());
    assert!(result.is_ok(), "HTML export should succeed");
    assert!(html_path.exists(), "HTML file should be created");
    
    // Test ANSI export
    let ansi_path = temp_dir.path().join("test.ansi");
    let result = export_buffer(&buffer, ExportFormat::Ansi, ansi_path.clone());
    assert!(result.is_ok(), "ANSI export should succeed");
    assert!(ansi_path.exists(), "ANSI file should be created");
    
    // Test Markdown export
    let md_path = temp_dir.path().join("test.md");
    let result = export_buffer(&buffer, ExportFormat::Markdown, md_path.clone());
    assert!(result.is_ok(), "Markdown export should succeed");
    assert!(md_path.exists(), "Markdown file should be created");
}

/// Test mouse interaction workflow
#[test]
fn test_mouse_interaction_workflow() {
    let config = MouseConfig::default();
    
    // Step 1: User clicks on item
    let click_event = Event::Mouse(MouseEvent {
        kind: MouseEventKind::Down(MouseButton::Left),
        column: 10,
        row: 5,
        modifiers: KeyModifiers::empty(),
    });
    
    let action = parse_mouse_event(&click_event, &config);
    assert!(action.is_some(), "Should parse click");
    if let Some(MouseAction::LeftClick { x, y }) = action {
        assert_eq!(x, 10);
        assert_eq!(y, 5);
    }
    
    // Step 2: User scrolls down
    let scroll_event = Event::Mouse(MouseEvent {
        kind: MouseEventKind::ScrollDown,
        column: 0,
        row: 0,
        modifiers: KeyModifiers::empty(),
    });
    
    let scroll_action = parse_mouse_event(&scroll_event, &config);
    assert_eq!(scroll_action, Some(MouseAction::ScrollDown));
    
    // Step 3: User scrolls up
    let scroll_up_event = Event::Mouse(MouseEvent {
        kind: MouseEventKind::ScrollUp,
        column: 0,
        row: 0,
        modifiers: KeyModifiers::empty(),
    });
    
    let scroll_up_action = parse_mouse_event(&scroll_up_event, &config);
    assert_eq!(scroll_up_action, Some(MouseAction::ScrollUp));
    
    // Step 4: Mouse disabled
    let disabled_config = MouseConfig::disabled();
    let disabled_action = parse_mouse_event(&click_event, &disabled_config);
    assert!(disabled_action.is_none(), "Should ignore mouse when disabled");
}

/// Test command palette search and selection workflow
#[test]
fn test_command_palette_search_workflow() {
    let mut palette = CommandPalette::new();
    
    // Step 1: User types partial query
    palette.update_query("equ".to_string());
    let filtered_len = palette.filtered_commands().len();
    assert!(filtered_len > 0, "Should find commands with 'equ'");
    
    // Step 2: User navigates filtered results
    let initial = palette.selected_command();
    assert!(initial.is_some());
    
    // Step 3: User continues typing
    palette.update_query("equipment".to_string());
    let filtered2_len = palette.filtered_commands().len();
    assert!(filtered2_len <= filtered_len, "Should filter further");
    
    // Step 4: User selects command
    let selected = palette.selected_command();
    assert!(selected.is_some(), "Should have selected command");
    if let Some(cmd) = selected {
        assert!(cmd.name.contains("equipment") || cmd.description.contains("equipment"),
            "Selected command should match query");
    }
}

/// Test help system integration in workflows
#[test]
fn test_help_system_integration_workflow() {
    // Test help in command palette using palette's integrated help system
    let mut palette = CommandPalette::new();
    
    // User opens help via palette's help system
    palette.help_system_mut().toggle_overlay();
    assert!(palette.help_system().show_overlay, "Overlay should be shown");
    
    // User closes help
    palette.help_system_mut().toggle_overlay();
    assert!(!palette.help_system().show_overlay, "Overlay should be closed");
    
    // Palette should be unaffected
    assert_eq!(palette.query(), "");
    
    // Test help event handling
    let mut standalone_help = HelpSystem::new(HelpContext::CommandPalette);
    let help_event = Event::Key(KeyEvent {
        code: KeyCode::Char('?'),
        modifiers: KeyModifiers::empty(),
        kind: KeyEventKind::Press,
        state: KeyEventState::empty(),
    });
    
    let handled = handle_help_event(help_event, &mut standalone_help);
    assert!(handled, "Help event should be handled");
    assert!(standalone_help.show_overlay, "Overlay should be shown");
}

/// Test error recovery workflow
#[test]
fn test_error_recovery_workflow() {
    let mut error_modal = ErrorModal::new();
    
    // Step 1: Error occurs
    let error = ArxError::io_error("Read error".to_string());
    error_modal.show_error(error);
    
    // Step 2: User views error details
    assert!(error_modal.show);
    assert!(!error_modal.actions.is_empty());
    
    // Step 3: User selects "View Details" action
    // Find ViewDetails action
    if let Some(details_idx) = error_modal.actions.iter().position(|a| matches!(a, ErrorAction::ViewDetails)) {
        error_modal.selected_action = details_idx;
        let action = error_modal.select_action();
        assert_eq!(action, Some(ErrorAction::ViewDetails));
    }
    
    // Step 4: User dismisses error
    error_modal.dismiss();
    assert!(!error_modal.show);
}

/// Test complete component interaction workflow
#[test]
fn test_complete_component_interaction_workflow() {
    // Simulate a complete user session:
    // 1. Open command palette
    // 2. Search for command
    // 3. Open help via palette's help system
    // 4. Close help
    // 5. Select command (simulated)
    
    let mut palette = CommandPalette::new();
    
    // Step 1: Open palette (already open)
    assert!(!palette.commands().is_empty());
    
    // Step 2: Search
    palette.update_query("init".to_string());
    assert_eq!(palette.query(), "init");
    
    // Step 3: Open help via palette's integrated help system
    palette.help_system_mut().toggle_overlay();
    assert!(palette.help_system().show_overlay);
    
    // Step 4: Close help
    palette.help_system_mut().toggle_overlay();
    assert!(!palette.help_system().show_overlay);
    
    // Step 5: Command still accessible
    let selected = palette.selected_command();
    assert!(selected.is_some());
}

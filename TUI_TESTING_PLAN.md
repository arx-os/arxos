# TUI Testing Plan - Complete Unit & Integration Testing

**Created:** January 2025  
**Status:** Ready for Implementation  
**Coverage Target:** >90% (per project standards)

---

## Overview

This document outlines the complete testing strategy for all Terminal User Interface (TUI) components in ArxOS. The TUI system has been refactored into modular components, and this plan covers unit tests for each module as well as integration tests for complete workflows.

---

## Test Organization

Following ArxOS conventions, tests will use **descriptive prefixes** for categorization:

- **`tui_*`** - TUI integration tests
- **`tui_unit_*`** - TUI unit tests (if needed in tests/ directory)
- Unit tests in `src/ui/*/` modules (inline tests)

---

## Module Structure Overview

```
src/ui/
├── help/                    # Contextual help system
│   ├── types.rs
│   ├── content.rs
│   ├── shortcuts.rs
│   ├── render.rs
│   └── events.rs
├── command_palette/         # Command search and execution
│   ├── types.rs
│   ├── commands.rs
│   ├── palette.rs
│   ├── render.rs
│   └── handler.rs
├── workspace_manager/       # Multi-building workspace management
│   ├── types.rs
│   ├── discovery.rs
│   ├── manager.rs
│   ├── render.rs
│   └── handler.rs
├── export/                  # View export functionality
│   ├── format.rs
│   ├── colors.rs
│   ├── text.rs
│   ├── ansi.rs
│   ├── html.rs
│   ├── markdown.rs
│   └── buffer.rs
├── theme_manager.rs         # Theme management
├── error_modal.rs           # Error modal dialogs
├── error_integration.rs     # Error modal helpers
├── mouse.rs                 # Mouse support
├── terminal.rs               # Terminal manager
├── theme.rs                 # Theme definitions
├── layouts.rs               # Layout utilities
└── widgets/                 # Reusable widgets
    ├── status_badge.rs
    └── summary_card.rs
```

---

## 1. Help System Tests (`src/ui/help/`)

### 1.1 Types Module (`types.rs`)

**Unit Tests:**
- [ ] `test_help_system_new()` - Verify HelpSystem initialization
- [ ] `test_help_system_toggle_overlay()` - Toggle help overlay state
- [ ] `test_help_system_toggle_cheat_sheet()` - Toggle cheat sheet state
- [ ] `test_help_system_set_context()` - Change help context
- [ ] `test_help_context_equality()` - HelpContext enum equality
- [ ] `test_shortcut_category_equality()` - ShortcutCategory enum equality

**Test File:** `src/ui/help/types.rs` (inline `#[cfg(test)]`)

---

### 1.2 Content Module (`content.rs`)

**Unit Tests:**
- [ ] `test_get_context_help_all_contexts()` - Verify help content for all 12 contexts
- [ ] `test_equipment_browser_help()` - Equipment browser help content
- [ ] `test_room_explorer_help()` - Room explorer help content
- [ ] `test_status_dashboard_help()` - Status dashboard help content
- [ ] `test_search_browser_help()` - Search browser help content
- [ ] `test_watch_dashboard_help()` - Watch dashboard help content
- [ ] `test_config_wizard_help()` - Config wizard help content
- [ ] `test_ar_pending_manager_help()` - AR pending manager help content
- [ ] `test_diff_viewer_help()` - Diff viewer help content
- [ ] `test_health_dashboard_help()` - Health dashboard help content
- [ ] `test_command_palette_help()` - Command palette help content
- [ ] `test_interactive_3d_help()` - Interactive 3D help content
- [ ] `test_general_help()` - General help content
- [ ] `test_help_content_structure()` - Verify help content has proper structure (title, sections, etc.)

**Test File:** `src/ui/help/content.rs` (inline `#[cfg(test)]`)

---

### 1.3 Shortcuts Module (`shortcuts.rs`)

**Unit Tests:**
- [ ] `test_get_all_shortcuts()` - Verify all shortcuts are returned
- [ ] `test_shortcuts_by_category()` - Verify shortcuts grouped by category
- [ ] `test_shortcut_categories_coverage()` - All 5 categories have shortcuts
- [ ] `test_shortcut_structure()` - Each shortcut has key, description, category
- [ ] `test_shortcut_no_empty_fields()` - No empty keys or descriptions

**Test File:** `src/ui/help/shortcuts.rs` (inline `#[cfg(test)]`)

---

### 1.4 Render Module (`render.rs`)

**Unit Tests:**
- [ ] `test_render_help_overlay()` - Render help overlay widget
- [ ] `test_render_help_overlay_all_contexts()` - Render for all contexts
- [ ] `test_render_shortcut_cheat_sheet()` - Render cheat sheet
- [ ] `test_render_shortcut_cheat_sheet_filtered()` - Filter shortcuts by query
- [ ] `test_render_shortcut_cheat_sheet_by_category()` - Filter by category
- [ ] `test_render_shortcut_cheat_sheet_empty()` - Empty shortcut list
- [ ] `test_help_overlay_styling()` - Verify theme colors applied
- [ ] `test_cheat_sheet_styling()` - Verify theme colors applied

**Test File:** `src/ui/help/render.rs` (inline `#[cfg(test)]`)

**Integration Tests:**
- [ ] `test_help_overlay_rendering_integration()` - Full render with terminal
- [ ] `test_cheat_sheet_rendering_integration()` - Full render with terminal

**Test File:** `tests/tui_help_integration_tests.rs`

---

### 1.5 Events Module (`events.rs`)

**Unit Tests:**
- [ ] `test_handle_help_event_question_mark()` - Toggle with `?`
- [ ] `test_handle_help_event_h_key()` - Toggle with `h` (non-Ctrl)
- [ ] `test_handle_help_event_ctrl_h()` - Toggle cheat sheet with `Ctrl+H`
- [ ] `test_handle_help_event_esc_close()` - Close help with Esc
- [ ] `test_handle_help_event_q_close()` - Close help with `q`
- [ ] `test_handle_help_event_other_keys()` - Other keys return false
- [ ] `test_handle_help_event_mouse_ignored()` - Mouse events ignored

**Test File:** `src/ui/help/events.rs` (inline `#[cfg(test)]`)

---

## 2. Command Palette Tests (`src/ui/command_palette/`)

### 2.1 Types Module (`types.rs`)

**Unit Tests:**
- [ ] `test_command_category_names()` - All categories have names
- [ ] `test_command_category_icons()` - All categories have icons
- [ ] `test_command_entry_structure()` - CommandEntry has all fields
- [ ] `test_command_category_equality()` - CommandCategory equality

**Test File:** `src/ui/command_palette/types.rs` (inline `#[cfg(test)]`)

---

### 2.2 Commands Module (`commands.rs`)

**Unit Tests:**
- [ ] `test_load_commands()` - Load all commands
- [ ] `test_command_count()` - Verify expected number of commands
- [ ] `test_commands_by_category()` - Commands exist for all categories
- [ ] `test_command_structure()` - Each command has name, full_command, description
- [ ] `test_no_duplicate_commands()` - No duplicate command names
- [ ] `test_building_commands()` - Building category commands
- [ ] `test_equipment_commands()` - Equipment category commands
- [ ] `test_room_commands()` - Room category commands
- [ ] `test_git_commands()` - Git category commands
- [ ] `test_ar_commands()` - AR category commands
- [ ] `test_all_categories_represented()` - All 13 categories have commands

**Test File:** `src/ui/command_palette/commands.rs` (inline `#[cfg(test)]`)

---

### 2.3 Palette Module (`palette.rs`)

**Unit Tests:**
- [ ] `test_palette_new()` - Create new palette
- [ ] `test_palette_initial_state()` - Initial state correct
- [ ] `test_palette_update_query()` - Update search query
- [ ] `test_palette_filter_commands()` - Filter commands by query
- [ ] `test_palette_filter_fuzzy_matching()` - Fuzzy matching works
- [ ] `test_palette_filter_by_name()` - Filter by command name
- [ ] `test_palette_filter_by_description()` - Filter by description
- [ ] `test_palette_filter_by_full_command()` - Filter by full command
- [ ] `test_palette_empty_query_shows_all()` - Empty query shows all
- [ ] `test_palette_selected_command()` - Get selected command
- [ ] `test_palette_next()` - Move selection down
- [ ] `test_palette_previous()` - Move selection up
- [ ] `test_palette_wraps_selection()` - Selection wraps at boundaries
- [ ] `test_palette_reset_selection_on_filter()` - Reset selection when filtering

**Test File:** `src/ui/command_palette/palette.rs` (inline `#[cfg(test)]`)

---

### 2.4 Render Module (`render.rs`)

**Unit Tests:**
- [ ] `test_render_command_palette()` - Render palette widget
- [ ] `test_render_empty_search()` - Render with empty search
- [ ] `test_render_with_query()` - Render with search query
- [ ] `test_render_filtered_commands()` - Render filtered command list
- [ ] `test_render_no_results()` - Render when no commands match
- [ ] `test_render_command_items()` - Command items formatted correctly
- [ ] `test_render_command_categories()` - Category icons displayed
- [ ] `test_render_footer_info()` - Footer shows command count

**Test File:** `src/ui/command_palette/render.rs` (inline `#[cfg(test)]`)

**Integration Tests:**
- [ ] `test_command_palette_full_render()` - Full palette rendering
- [ ] `test_command_palette_help_overlay()` - Help overlay integration

**Test File:** `tests/tui_command_palette_integration_tests.rs`

---

### 2.5 Handler Module (`handler.rs`)

**Unit Tests:**
- [ ] `test_handle_command_palette_esc()` - Close with Esc
- [ ] `test_handle_command_palette_q()` - Close with `q`
- [ ] `test_handle_command_palette_enter()` - Select command with Enter
- [ ] `test_handle_command_palette_arrow_keys()` - Navigate with arrow keys
- [ ] `test_handle_command_palette_type_search()` - Type to search
- [ ] `test_handle_command_palette_backspace()` - Backspace removes characters
- [ ] `test_handle_command_palette_ctrl_p()` - Ctrl+P ignored (already open)
- [ ] `test_handle_command_palette_help()` - Help system integration

**Integration Tests:**
- [ ] `test_command_palette_full_workflow()` - Complete palette workflow
- [ ] `test_command_palette_search_and_select()` - Search and select command
- [ ] `test_command_palette_navigation()` - Full navigation workflow

**Test File:** `tests/tui_command_palette_integration_tests.rs`

---

## 3. Workspace Manager Tests (`src/ui/workspace_manager/`)

### 3.1 Types Module (`types.rs`)

**Unit Tests:**
- [ ] `test_workspace_structure()` - Workspace has all fields
- [ ] `test_workspace_clone()` - Workspace cloning works

**Test File:** `src/ui/workspace_manager/types.rs` (inline `#[cfg(test)]`)

---

### 3.2 Discovery Module (`discovery.rs`)

**Unit Tests:**
- [ ] `test_discover_workspaces()` - Discover workspaces from YAML files
- [ ] `test_discover_workspaces_no_yaml()` - No YAML files found
- [ ] `test_discover_workspaces_current_dir()` - Current directory fallback
- [ ] `test_load_building_description()` - Load description from YAML
- [ ] `test_load_building_description_no_description()` - No description field
- [ ] `test_load_building_description_no_name()` - No name field
- [ ] `test_load_building_description_invalid_yaml()` - Invalid YAML handling
- [ ] `test_workspace_git_repo_detection()` - Git repo detection
- [ ] `test_workspace_name_extraction()` - Name extraction from path

**Test File:** `src/ui/workspace_manager/discovery.rs` (inline `#[cfg(test)]`)

**Integration Tests:**
- [ ] `test_workspace_discovery_integration()` - Real file system discovery
- [ ] `test_workspace_discovery_with_git()` - Discovery with Git repos

**Test File:** `tests/tui_workspace_integration_tests.rs`

---

### 3.3 Manager Module (`manager.rs`)

**Unit Tests:**
- [ ] `test_workspace_manager_new()` - Create new manager
- [ ] `test_workspace_manager_empty()` - Manager with no workspaces
- [ ] `test_workspace_manager_update_query()` - Update search query
- [ ] `test_workspace_manager_filter_by_name()` - Filter by workspace name
- [ ] `test_workspace_manager_filter_by_description()` - Filter by description
- [ ] `test_workspace_manager_selected_workspace()` - Get selected workspace
- [ ] `test_workspace_manager_next()` - Move selection down
- [ ] `test_workspace_manager_previous()` - Move selection up
- [ ] `test_workspace_manager_is_active()` - Check active workspace
- [ ] `test_workspace_manager_active_detection()` - Active workspace detection

**Test File:** `src/ui/workspace_manager/manager.rs` (inline `#[cfg(test)]`)

---

### 3.4 Render Module (`render.rs`)

**Unit Tests:**
- [ ] `test_render_workspace_manager()` - Render workspace manager
- [ ] `test_render_empty_list()` - Render with no workspaces
- [ ] `test_render_active_indicator()` - Active workspace indicator
- [ ] `test_render_workspace_info()` - Workspace information displayed
- [ ] `test_render_git_repo_indicator()` - Git repo indicator
- [ ] `test_render_search_bar()` - Search bar rendering
- [ ] `test_render_footer()` - Footer rendering

**Test File:** `src/ui/workspace_manager/render.rs` (inline `#[cfg(test)]`)

---

### 3.5 Handler Module (`handler.rs`)

**Unit Tests:**
- [ ] `test_handle_workspace_manager_empty()` - Handle empty workspace list
- [ ] `test_handle_workspace_manager_esc()` - Close with Esc
- [ ] `test_handle_workspace_manager_enter()` - Select workspace with Enter
- [ ] `test_handle_workspace_manager_navigation()` - Navigate with arrow keys
- [ ] `test_handle_workspace_manager_search()` - Type to search
- [ ] `test_handle_workspace_manager_ctrl_w()` - Ctrl+W ignored (already open)

**Integration Tests:**
- [ ] `test_workspace_manager_full_workflow()` - Complete workspace manager workflow
- [ ] `test_workspace_manager_switch_workspace()` - Switch between workspaces

**Test File:** `tests/tui_workspace_integration_tests.rs`

---

## 4. Export Module Tests (`src/ui/export/`)

### 4.1 Format Module (`format.rs`)

**Unit Tests:**
- [ ] `test_export_format_all()` - Get all formats
- [ ] `test_export_format_names()` - All formats have names
- [ ] `test_export_format_extensions()` - All formats have extensions
- [ ] `test_export_format_equality()` - Format equality

**Test File:** `src/ui/export/format.rs` (inline `#[cfg(test)]`)

---

### 4.2 Colors Module (`colors.rs`)

**Unit Tests:**
- [ ] `test_color_to_ansi_basic()` - Basic colors to ANSI
- [ ] `test_color_to_ansi_rgb()` - RGB colors to ANSI
- [ ] `test_color_to_ansi_indexed()` - Indexed colors to ANSI
- [ ] `test_color_to_ansi_foreground()` - Foreground color codes
- [ ] `test_color_to_ansi_background()` - Background color codes
- [ ] `test_modifiers_to_ansi()` - Modifiers to ANSI codes
- [ ] `test_modifiers_to_ansi_bold()` - Bold modifier
- [ ] `test_modifiers_to_ansi_italic()` - Italic modifier
- [ ] `test_modifiers_to_ansi_underlined()` - Underlined modifier
- [ ] `test_modifiers_to_ansi_combined()` - Combined modifiers
- [ ] `test_color_to_css_basic()` - Basic colors to CSS
- [ ] `test_color_to_css_rgb()` - RGB colors to CSS
- [ ] `test_color_to_css_indexed()` - Indexed colors to CSS
- [ ] `test_color_to_css_hex_format()` - Hex format validation

**Test File:** `src/ui/export/colors.rs` (inline `#[cfg(test)]`)

---

### 4.3 Text Module (`text.rs`)

**Unit Tests:**
- [ ] `test_export_as_text()` - Export buffer as plain text
- [ ] `test_export_as_text_empty()` - Empty buffer
- [ ] `test_export_as_text_multiline()` - Multi-line text
- [ ] `test_export_as_text_trim_whitespace()` - Trailing whitespace trimmed
- [ ] `test_export_as_text_special_chars()` - Special characters preserved

**Test File:** `src/ui/export/text.rs` (inline `#[cfg(test)]`)

---

### 4.4 ANSI Module (`ansi.rs`)

**Unit Tests:**
- [ ] `test_export_as_ansi()` - Export buffer as ANSI
- [ ] `test_export_as_ansi_colors()` - Color codes included
- [ ] `test_export_as_ansi_reset_codes()` - Reset codes at line end
- [ ] `test_export_as_ansi_modifiers()` - Modifiers applied
- [ ] `test_export_as_ansi_style_changes()` - Style changes handled
- [ ] `test_export_as_ansi_empty_buffer()` - Empty buffer handling

**Test File:** `src/ui/export/ansi.rs` (inline `#[cfg(test)]`)

---

### 4.5 HTML Module (`html.rs`)

**Unit Tests:**
- [ ] `test_export_as_html()` - Export buffer as HTML
- [ ] `test_export_as_html_structure()` - HTML structure correct
- [ ] `test_export_as_html_colors()` - Colors in CSS
- [ ] `test_export_as_html_modifiers()` - Modifiers in CSS
- [ ] `test_export_as_html_escape_chars()` - HTML special chars escaped
- [ ] `test_export_as_html_spans()` - Color spans created
- [ ] `test_export_as_html_empty_buffer()` - Empty buffer handling

**Test File:** `src/ui/export/html.rs` (inline `#[cfg(test)]`)

---

### 4.6 Markdown Module (`markdown.rs`)

**Unit Tests:**
- [ ] `test_export_as_markdown()` - Export buffer as Markdown
- [ ] `test_export_as_markdown_code_block()` - Code block format
- [ ] `test_export_as_markdown_uses_text()` - Uses text export

**Test File:** `src/ui/export/markdown.rs` (inline `#[cfg(test)]`)

---

### 4.7 Buffer Module (`buffer.rs`)

**Unit Tests:**
- [ ] `test_export_buffer_text()` - Export buffer as text format
- [ ] `test_export_buffer_ansi()` - Export buffer as ANSI format
- [ ] `test_export_buffer_html()` - Export buffer as HTML format
- [ ] `test_export_buffer_markdown()` - Export buffer as Markdown format
- [ ] `test_export_buffer_file_write()` - File written successfully
- [ ] `test_export_current_view_error()` - Error message for Ratatui limitation

**Test File:** `src/ui/export/buffer.rs` (inline `#[cfg(test)]`)

**Integration Tests:**
- [ ] `test_export_buffer_integration()` - Full export workflow
- [ ] `test_export_all_formats()` - Export in all formats

**Test File:** `tests/tui_export_integration_tests.rs`

---

## 5. Theme Manager Tests (`src/ui/theme_manager.rs`)

**Unit Tests:**
- [ ] `test_theme_manager_new()` - Create new theme manager
- [ ] `test_theme_manager_set_theme()` - Set theme preset
- [ ] `test_theme_manager_set_custom_theme()` - Set custom theme
- [ ] `test_theme_manager_save_theme()` - Save theme to file
- [ ] `test_theme_manager_load_theme()` - Load theme from file
- [ ] `test_theme_manager_list_saved_themes()` - List saved themes
- [ ] `test_theme_manager_theme_presets()` - All presets available
- [ ] `test_theme_config_serialization()` - Theme config serialization
- [ ] `test_theme_config_deserialization()` - Theme config deserialization
- [ ] `test_theme_manager_color_parsing()` - Color string parsing
- [ ] `test_theme_manager_invalid_theme()` - Invalid theme handling

**Test File:** `src/ui/theme_manager.rs` (inline `#[cfg(test)]`)

**Integration Tests:**
- [ ] `test_theme_manager_persistence()` - Theme persistence workflow
- [ ] `test_theme_manager_load_save_cycle()` - Load/save cycle

**Test File:** `tests/tui_theme_integration_tests.rs`

---

## 6. Error Modal Tests (`src/ui/error_modal.rs`)

**Unit Tests:**
- [ ] `test_error_modal_new()` - Create new error modal
- [ ] `test_error_modal_show_error()` - Show error
- [ ] `test_error_modal_dismiss()` - Dismiss modal
- [ ] `test_error_modal_next_action()` - Navigate to next action
- [ ] `test_error_modal_previous_action()` - Navigate to previous action
- [ ] `test_error_modal_select_action()` - Select action
- [ ] `test_error_modal_actions_by_type()` - Actions based on error type
- [ ] `test_error_action_labels()` - Action labels
- [ ] `test_error_action_keys()` - Action keyboard shortcuts
- [ ] `test_calculate_modal_area()` - Modal area calculation

**Test File:** `src/ui/error_modal.rs` (inline `#[cfg(test)]`)

---

## 7. Error Integration Tests (`src/ui/error_integration.rs`)

**Unit Tests:**
- [ ] `test_render_error_modal_in_frame()` - Render modal in frame
- [ ] `test_handle_error_with_modal()` - Handle error and show modal
- [ ] `test_handle_error_with_modal_arx_error()` - ArxError handling
- [ ] `test_handle_error_with_modal_generic_error()` - Generic error handling
- [ ] `test_process_error_modal_event()` - Process modal events

**Test File:** `src/ui/error_integration.rs` (inline `#[cfg(test)]`)

---

## 8. Mouse Support Tests (`src/ui/mouse.rs`)

**Unit Tests:**
- [ ] `test_parse_mouse_event()` - Parse mouse events
- [ ] `test_is_point_in_rect()` - Point in rectangle check
- [ ] `test_find_clicked_list_item()` - Find clicked list item
- [ ] `test_find_clicked_table_cell()` - Find clicked table cell
- [ ] `test_enable_mouse_support()` - Enable mouse support
- [ ] `test_disable_mouse_support()` - Disable mouse support
- [ ] `test_mouse_action_parsing()` - Mouse action parsing
- [ ] `test_mouse_config()` - Mouse configuration

**Test File:** `src/ui/mouse.rs` (inline `#[cfg(test)]`)

---

## 9. Terminal Manager Tests (`src/ui/terminal.rs`)

**Unit Tests:**
- [ ] `test_terminal_manager_new()` - Create new terminal manager
- [ ] `test_terminal_manager_mouse_enabled()` - Mouse enabled state
- [ ] `test_terminal_manager_poll_event()` - Poll events
- [ ] `test_terminal_manager_terminal()` - Get terminal instance

**Integration Tests:**
- [ ] `test_terminal_manager_full_workflow()` - Complete terminal workflow

**Test File:** `tests/tui_terminal_integration_tests.rs`

---

## 10. Theme Tests (`src/ui/theme.rs`)

**Unit Tests:**
- [ ] `test_theme_new()` - Create new theme
- [ ] `test_theme_default()` - Default theme
- [ ] `test_theme_from_config()` - Theme from config
- [ ] `test_status_color()` - Status color enum

**Test File:** `src/ui/theme.rs` (inline `#[cfg(test)]`)

---

## 11. Layouts Tests (`src/ui/layouts.rs`)

**Unit Tests:**
- [ ] `test_centered_rect()` - Centered rectangle calculation
- [ ] `test_layout_constraints()` - Layout constraint helpers
- [ ] `test_split_layout()` - Layout splitting

**Test File:** `src/ui/layouts.rs` (inline `#[cfg(test)]`)

---

## 12. Widget Tests (`src/ui/widgets/`)

### 12.1 Status Badge (`status_badge.rs`)

**Unit Tests:**
- [ ] `test_status_badge_creation()` - Create status badge
- [ ] `test_status_badge_colors()` - Status colors applied
- [ ] `test_status_badge_rendering()` - Badge rendering

**Test File:** `src/ui/widgets/status_badge.rs` (inline `#[cfg(test)]`)

---

### 12.2 Summary Card (`summary_card.rs`)

**Unit Tests:**
- [ ] `test_summary_card_creation()` - Create summary card
- [ ] `test_summary_card_rendering()` - Card rendering
- [ ] `test_summary_card_data()` - Card data display

**Test File:** `src/ui/widgets/summary_card.rs` (inline `#[cfg(test)]`)

---

## Integration Tests

### Complete TUI Workflows

**Test File:** `tests/tui_workflow_integration_tests.rs`

- [ ] `test_equipment_browser_workflow()` - Complete equipment browser workflow
- [ ] `test_room_explorer_workflow()` - Complete room explorer workflow
- [ ] `test_command_palette_workflow()` - Command palette workflow
- [ ] `test_workspace_manager_workflow()` - Workspace manager workflow
- [ ] `test_help_system_workflow()` - Help system integration
- [ ] `test_error_handling_workflow()` - Error modal workflow
- [ ] `test_theme_switching_workflow()` - Theme switching workflow
- [ ] `test_export_workflow()` - Export workflow
- [ ] `test_mouse_interaction_workflow()` - Mouse interaction workflow

---

### Component Interaction Tests

**Test File:** `tests/tui_component_interaction_tests.rs`

- [ ] `test_help_in_command_palette()` - Help system in command palette
- [ ] `test_help_in_workspace_manager()` - Help system in workspace manager
- [ ] `test_error_modal_in_components()` - Error modal in components
- [ ] `test_theme_consistency()` - Theme consistency across components
- [ ] `test_mouse_support_in_components()` - Mouse support in components

---

### Event Flow Tests

**Test File:** `tests/tui_event_flow_tests.rs`

- [ ] `test_keyboard_event_flow()` - Keyboard event propagation
- [ ] `test_mouse_event_flow()` - Mouse event propagation
- [ ] `test_help_event_interception()` - Help events intercepted correctly
- [ ] `test_error_event_handling()` - Error event handling flow

---

## Test Utilities

### Mock Terminal

Create a mock terminal for testing without actual terminal:

**File:** `tests/tui_test_utils.rs`

```rust
pub struct MockTerminal {
    // Mock terminal implementation
}

impl MockTerminal {
    pub fn new() -> Self { /* ... */ }
    // ... mock methods
}
```

### Test Helpers

- [ ] `create_test_theme()` - Create test theme
- [ ] `create_test_buffer()` - Create test buffer
- [ ] `create_test_frame()` - Create test frame
- [ ] `simulate_key_event()` - Simulate key events
- [ ] `simulate_mouse_event()` - Simulate mouse events

---

## Test Coverage Goals

### Unit Test Coverage
- **Target:** >95% line coverage for all modules
- **Focus Areas:**
  - All public functions
  - All error paths
  - All edge cases
  - All state transitions

### Integration Test Coverage
- **Target:** >90% workflow coverage
- **Focus Areas:**
  - Complete user workflows
  - Component interactions
  - Error recovery
  - State persistence

---

## Running Tests

### Run All TUI Tests
```bash
cargo test --lib ui
```

### Run Specific Module Tests
```bash
# Help system
cargo test --lib help

# Command palette
cargo test --lib command_palette

# Workspace manager
cargo test --lib workspace_manager

# Export
cargo test --lib export
```

### Run Integration Tests
```bash
# All TUI integration tests
cargo test --test tui_

# Specific integration test
cargo test --test tui_help_integration_tests
cargo test --test tui_command_palette_integration_tests
cargo test --test tui_workspace_integration_tests
cargo test --test tui_export_integration_tests
```

### Run with Coverage
```bash
# Install cargo-tarpaulin if needed
cargo install cargo-tarpaulin

# Generate coverage report
cargo tarpaulin --lib --tests --out Html --output-dir coverage
```

---

## Test Dependencies

Add to `Cargo.toml`:

```toml
[dev-dependencies]
# Testing utilities
mockall = "0.12"  # For mocking
tempfile = "3.8"  # For temporary files
assert_matches = "1.5"  # For pattern matching assertions

# Test coverage
criterion = "0.5"  # For benchmarks (if needed)
```

---

## Implementation Priority

### Phase 1: Core Modules (Week 1)
1. Help system (types, content, shortcuts, events)
2. Export (format, colors, text, ansi, html, markdown)
3. Theme manager

### Phase 2: Interactive Components (Week 2)
1. Command palette (all modules)
2. Workspace manager (all modules)
3. Error modal and integration

### Phase 3: Supporting Modules (Week 3)
1. Mouse support
2. Terminal manager
3. Theme and layouts
4. Widgets

### Phase 4: Integration Tests (Week 4)
1. Complete workflows
2. Component interactions
3. Event flow tests

---

## Notes

- All inline unit tests should be in `#[cfg(test)]` modules within each source file
- Integration tests should be in `tests/` directory with `tui_` prefix
- Follow existing test patterns from `tests/README.md`
- Maintain >90% coverage per project standards
- Use descriptive test names that explain what is being tested
- Include both positive and negative test cases
- Test error handling and edge cases
- Mock external dependencies (file system, terminal) where appropriate

---

## Success Criteria

✅ All modules have unit tests  
✅ All public APIs tested  
✅ Integration tests cover main workflows  
✅ Test coverage >90%  
✅ All tests pass  
✅ Tests run in CI/CD  
✅ Test documentation complete

---

**Ready for implementation!** 🚀


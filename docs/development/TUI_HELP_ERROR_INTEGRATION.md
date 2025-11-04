# TUI Help & Error Modal Integration Guide

**Version:** 1.0  
**Date:** January 2025

---

## Overview

This guide explains how to integrate the Help System and Error Modal into TUI components in ArxOS.

---

## Help System Integration

### 1. Add HelpSystem to Component State

```rust
use crate::ui::{HelpSystem, HelpContext};

struct MyComponentState {
    // ... existing fields ...
    help_system: HelpSystem,
}

impl MyComponentState {
    fn new() -> Self {
        Self {
            // ... existing fields ...
            help_system: HelpSystem::new(HelpContext::MyComponent),
        }
    }
}
```

### 2. Render Help Overlay

In your component's render loop:

```rust
use crate::ui::{render_help_overlay, render_shortcut_cheat_sheet, get_all_shortcuts};

terminal.terminal().draw(|frame| {
    // ... render main UI ...
    
    // Render help overlay if enabled
    if state.help_system.show_overlay {
        let help_overlay = render_help_overlay(
            state.help_system.current_context,
            frame.size(),
            &theme,
        );
        frame.render_widget(help_overlay, frame.size());
    }
    
    // Render shortcut cheat sheet if enabled
    if state.help_system.show_cheat_sheet {
        let shortcuts = get_all_shortcuts();
        let cheat_sheet = render_shortcut_cheat_sheet(
            &shortcuts,
            &state.help_system.search_query,
            state.help_system.selected_category,
            &theme,
        );
        frame.render_widget(cheat_sheet, frame.size());
    }
})?;
```

### 3. Handle Help Events

In your event handling:

```rust
use crate::ui::{handle_help_event};
use crossterm::event::{Event, KeyCode, KeyModifiers};

if let Some(event) = terminal.poll_event(Duration::from_millis(100))? {
    // Handle help events first
    if handle_help_event(event.clone(), &mut state.help_system) {
        continue; // Help system handled the event
    }
    
    // Handle cheat sheet toggle
    match event {
        Event::Key(key_event) if key_event.code == KeyCode::Char('h') 
            && key_event.modifiers.contains(KeyModifiers::CONTROL) => {
            state.help_system.toggle_cheat_sheet();
            continue;
        }
        // ... other event handling ...
    }
    
    // Prevent quitting when help is showing
    if (state.help_system.show_overlay || state.help_system.show_cheat_sheet) 
        && key_event.code == KeyCode::Esc {
        state.help_system.show_overlay = false;
        state.help_system.show_cheat_sheet = false;
    } else if key_event.code == KeyCode::Char('q') {
        break; // Quit
    }
}
```

---

## Error Modal Integration

### 1. Add ErrorModal to Component State

```rust
use crate::ui::ErrorModal;

struct MyComponentState {
    // ... existing fields ...
    error_modal: ErrorModal,
}

impl MyComponentState {
    fn new() -> Self {
        Self {
            // ... existing fields ...
            error_modal: ErrorModal::new(),
        }
    }
}
```

### 2. Render Error Modal

In your component's render loop:

```rust
use crate::ui::{render_error_modal_in_frame};

terminal.terminal().draw(|frame| {
    // ... render main UI ...
    
    // Render error modal if showing
    render_error_modal_in_frame(frame, &state.error_modal, &theme);
})?;
```

### 3. Handle Errors and Modal Events

```rust
use crate::ui::{handle_error_with_modal, process_error_modal_event};

// When an error occurs:
match some_operation() {
    Ok(result) => {
        // Handle success
    }
    Err(e) => {
        // Show error modal
        handle_error_with_modal(e, &mut state.error_modal)?;
    }
}

// In event handling:
if let Some(event) = terminal.poll_event(Duration::from_millis(100))? {
    // Handle error modal events first
    if state.error_modal.show {
        if let Some(action) = process_error_modal_event(event, &mut state.error_modal) {
            match action {
                ErrorAction::Retry => {
                    // Retry the operation
                }
                ErrorAction::ViewDetails => {
                    // Show detailed error info
                }
                ErrorAction::ShowHelp => {
                    // Show help related to error
                    state.help_system.toggle_overlay();
                }
                ErrorAction::Dismiss => {
                    state.error_modal.dismiss();
                }
                _ => {}
            }
        }
        continue; // Modal handled the event
    }
    
    // ... other event handling ...
}
```

---

## Complete Example

See `src/commands/equipment/browser.rs` for a complete integration example.

---

## Available Help Contexts

- `HelpContext::EquipmentBrowser`
- `HelpContext::RoomExplorer`
- `HelpContext::StatusDashboard`
- `HelpContext::SearchBrowser`
- `HelpContext::WatchDashboard`
- `HelpContext::ConfigWizard`
- `HelpContext::ArPendingManager`
- `HelpContext::DiffViewer`
- `HelpContext::HealthDashboard`
- `HelpContext::Interactive3D`
- `HelpContext::General`

---

## Keyboard Shortcuts

- **`?` or `h`** - Toggle context-specific help overlay
- **`Ctrl+H`** - Toggle keyboard shortcut cheat sheet
- **`Esc` or `q`** - Close help/cheat sheet

---

## Error Modal Actions

- **Retry** - Attempt to retry the failed operation
- **View Details** - Show detailed error information
- **Show Help** - Display help related to the error
- **Dismiss** - Close the error modal

Error modals automatically determine available actions based on error type.

---

## Best Practices

1. **Always handle help events first** - Before other event processing
2. **Prevent actions when modals are open** - Only allow closing modals
3. **Set appropriate help context** - Use the correct `HelpContext` for your component
4. **Use error modal for all errors** - Don't print errors directly in TUI mode
5. **Provide helpful suggestions** - Use `ArxError` with context for better UX


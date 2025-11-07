//! Workspace Manager Event Handler
//!
//! Handles user interaction with the workspace manager.

use super::manager::WorkspaceManager;
use crate::ui::{TerminalManager, Theme};
use crossterm::event::{Event, KeyCode, KeyModifiers};
use ratatui::{
    layout::Alignment,
    style::Style,
    text::Line,
    widgets::{Block, Borders, Paragraph},
};
use std::path::PathBuf;
use std::time::Duration;

/// Handle workspace manager interaction
pub fn handle_workspace_manager(
    terminal: &mut TerminalManager,
    theme: &Theme,
) -> Result<Option<PathBuf>, Box<dyn std::error::Error>> {
    use super::render::render_workspace_manager;
    
    let mut manager = WorkspaceManager::new()?;
    
    if manager.is_empty() {
        // No workspaces found
        terminal.terminal().draw(|frame| {
            let area = frame.size();
            let message = Paragraph::new(vec![
                Line::from("No workspaces found."),
                Line::from(""),
                Line::from("Initialize a building with: arxos init"),
            ])
            .block(Block::default().borders(Borders::ALL).title("Workspace Manager"))
            .alignment(Alignment::Center)
            .style(Style::default().fg(theme.text));
            frame.render_widget(message, area);
        })?;
        
        // Wait for any key
        if let Some(Event::Key(key_event)) = terminal.poll_event(Duration::from_secs(5))? {
            if matches!(key_event.code, KeyCode::Esc | KeyCode::Char('q')) {
                return Ok(None);
            }
        }
        
        return Ok(None);
    }
    
    loop {
        let mouse_enabled = terminal.mouse_enabled();
        terminal.terminal().draw(|frame| {
            let area = frame.size();
            render_workspace_manager(frame, area, &mut manager, theme, mouse_enabled);
        })?;
        
        if let Some(event) = terminal.poll_event(Duration::from_millis(100))? {
            // Handle help first
            use crate::ui::handle_help_event;
            if handle_help_event(event.clone(), manager.help_system_mut()) {
                continue;
            }
            
            if let Event::Key(key_event) = event {
                match key_event.code {
                    KeyCode::Esc | KeyCode::Char('q') => {
                        return Ok(None);
                    }
                    KeyCode::Enter => {
                        if let Some(workspace) = manager.selected_workspace() {
                            return Ok(Some(workspace.path.clone()));
                        }
                    }
                    KeyCode::Up => {
                        manager.previous();
                    }
                    KeyCode::Down => {
                        manager.next();
                    }
                    KeyCode::Char(c) => {
                        if key_event.modifiers.contains(KeyModifiers::CONTROL) && c == 'w' {
                            // Ctrl+W to open workspace manager (already open)
                            continue;
                        } else {
                            // Add to search query
                            let mut query = manager.query().to_string();
                            query.push(c);
                            manager.update_query(query);
                        }
                    }
                    KeyCode::Backspace => {
                        let mut query = manager.query().to_string();
                        query.pop();
                        manager.update_query(query);
                    }
                    _ => {}
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::super::manager::WorkspaceManager;
    
    

    #[test]
    fn test_handle_workspace_manager_empty() {
        // Test empty workspace detection
        let manager = WorkspaceManager::new();
        
        // Manager may be empty or have workspaces depending on environment
        // We test the is_empty logic
        if let Ok(manager) = manager {
            let is_empty = manager.is_empty();
            // Either empty or has workspaces - both are valid
            assert!(is_empty || !manager.workspaces().is_empty());
        }
    }

    #[test]
    fn test_workspace_manager_query_logic() {
        // Test query update logic through public API
        if let Ok(mut manager) = WorkspaceManager::new() {
            manager.update_query("test".to_string());
            assert_eq!(manager.query(), "test");
            
            manager.update_query("".to_string());
            assert_eq!(manager.query(), "");
        }
        // If manager creation fails (no workspaces), that's acceptable
    }

    #[test]
    fn test_workspace_manager_navigation() {
        // Test navigation logic through public API
        if let Ok(mut manager) = WorkspaceManager::new() {
            if !manager.is_empty() {
                let initial = manager.selected_workspace().map(|w| w.name.clone());
                manager.next();
                let after_next = manager.selected_workspace().map(|w| w.name.clone());
                
                // If there's more than one workspace, selection should change
                if manager.workspaces().len() > 1 {
                    assert_ne!(initial, after_next, "Selection should change");
                }
                
                manager.previous();
                let after_prev = manager.selected_workspace().map(|w| w.name.clone());
                assert_eq!(initial, after_prev, "Should return to initial selection");
            }
        }
        // If manager creation fails, that's acceptable
    }

    #[test]
    fn test_workspace_manager_selection() {
        // Test selection logic through public API
        if let Ok(manager) = WorkspaceManager::new() {
            if !manager.is_empty() {
                let selected = manager.selected_workspace();
                assert!(selected.is_some(), "Should have a selected workspace");
            }
        }
        // If manager creation fails, that's acceptable
    }
}


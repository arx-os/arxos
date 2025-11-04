//! Mouse Support for ArxOS TUI
//!
//! Provides:
//! - Mouse event handling utilities
//! - Click-to-select functionality
//! - Scroll support for lists
//! - Mouse coordinate helpers

use crossterm::event::{Event, MouseButton, MouseEvent, MouseEventKind, KeyModifiers};
use ratatui::layout::Rect;

/// Mouse event types for TUI components
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MouseAction {
    /// Left click at coordinates
    LeftClick { x: u16, y: u16 },
    /// Right click at coordinates
    RightClick { x: u16, y: u16 },
    /// Middle click at coordinates
    MiddleClick { x: u16, y: u16 },
    /// Scroll up
    ScrollUp,
    /// Scroll down
    ScrollDown,
    /// Scroll left
    ScrollLeft,
    /// Scroll right
    ScrollRight,
    /// Mouse drag (movement while button pressed)
    Drag { x: u16, y: u16, button: MouseButton },
    /// Mouse movement (no button pressed)
    Move { x: u16, y: u16 },
}

impl MouseAction {
    /// Get click coordinates
    pub fn position(&self) -> Option<(u16, u16)> {
        match self {
            MouseAction::LeftClick { x, y } |
            MouseAction::RightClick { x, y } |
            MouseAction::MiddleClick { x, y } |
            MouseAction::Drag { x, y, .. } |
            MouseAction::Move { x, y } => Some((*x, *y)),
            _ => None,
        }
    }
    
    /// Check if this is a click action
    pub fn is_click(&self) -> bool {
        matches!(self, MouseAction::LeftClick { .. } | 
                       MouseAction::RightClick { .. } | 
                       MouseAction::MiddleClick { .. })
    }
    
    /// Check if this is a scroll action
    pub fn is_scroll(&self) -> bool {
        matches!(self, MouseAction::ScrollUp | 
                       MouseAction::ScrollDown | 
                       MouseAction::ScrollLeft | 
                       MouseAction::ScrollRight)
    }
}

/// Mouse event handler configuration
#[derive(Debug, Clone)]
pub struct MouseConfig {
    /// Enable mouse support
    pub enabled: bool,
    /// Enable click-to-select
    pub click_to_select: bool,
    /// Enable scroll support
    pub scroll_enabled: bool,
    /// Enable drag support
    pub drag_enabled: bool,
}

impl Default for MouseConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            click_to_select: true,
            scroll_enabled: true,
            drag_enabled: false, // Disabled by default for most components
        }
    }
}

impl MouseConfig {
    /// Create a new mouse config with defaults
    pub fn new() -> Self {
        Self::default()
    }
    
    /// Disable mouse support entirely
    pub fn disabled() -> Self {
        Self {
            enabled: false,
            click_to_select: false,
            scroll_enabled: false,
            drag_enabled: false,
        }
    }
    
    /// Enable all mouse features
    pub fn full() -> Self {
        Self {
            enabled: true,
            click_to_select: true,
            scroll_enabled: true,
            drag_enabled: true,
        }
    }
}

/// Convert crossterm Event to MouseAction if it's a mouse event
pub fn parse_mouse_event(event: &Event, config: &MouseConfig) -> Option<MouseAction> {
    if !config.enabled {
        return None;
    }
    
    match event {
        Event::Mouse(mouse_event) => {
            match mouse_event.kind {
                MouseEventKind::Down(button) => {
                    Some(match button {
                        MouseButton::Left => MouseAction::LeftClick {
                            x: mouse_event.column,
                            y: mouse_event.row,
                        },
                        MouseButton::Right => MouseAction::RightClick {
                            x: mouse_event.column,
                            y: mouse_event.row,
                        },
                        MouseButton::Middle => MouseAction::MiddleClick {
                            x: mouse_event.column,
                            y: mouse_event.row,
                        },
                    })
                }
                MouseEventKind::Up(_) => None, // Ignore mouse up events
                MouseEventKind::Drag(button) if config.drag_enabled => {
                    Some(MouseAction::Drag {
                        x: mouse_event.column,
                        y: mouse_event.row,
                        button,
                    })
                }
                MouseEventKind::Moved => {
                    Some(MouseAction::Move {
                        x: mouse_event.column,
                        y: mouse_event.row,
                    })
                }
                MouseEventKind::ScrollUp if config.scroll_enabled => {
                    Some(MouseAction::ScrollUp)
                }
                MouseEventKind::ScrollDown if config.scroll_enabled => {
                    Some(MouseAction::ScrollDown)
                }
                MouseEventKind::ScrollLeft if config.scroll_enabled => {
                    Some(MouseAction::ScrollLeft)
                }
                MouseEventKind::ScrollRight if config.scroll_enabled => {
                    Some(MouseAction::ScrollRight)
                }
                _ => None,
            }
        }
        _ => None,
    }
}

/// Check if coordinates are within a rectangle
pub fn is_point_in_rect(x: u16, y: u16, rect: Rect) -> bool {
    x >= rect.x && x < rect.x + rect.width &&
    y >= rect.y && y < rect.y + rect.height
}

/// Find which item in a list was clicked
pub fn find_clicked_list_item(
    click_y: u16,
    list_area: Rect,
    item_height: u16,
    offset: usize,
) -> Option<usize> {
    if !is_point_in_rect(list_area.x, click_y, list_area) {
        return None;
    }
    
    // Calculate relative Y position within the list area
    let relative_y = click_y.saturating_sub(list_area.y);
    
    // Calculate which item index this corresponds to
    let item_index = (relative_y / item_height) as usize;
    
    // Add offset for scrolling
    Some(item_index + offset)
}

/// Find which table cell was clicked
pub fn find_clicked_table_cell(
    click_x: u16,
    click_y: u16,
    table_area: Rect,
    column_widths: &[u16],
    row_height: u16,
    header_height: u16,
    row_offset: usize,
) -> Option<(usize, usize)> {
    if !is_point_in_rect(click_x, click_y, table_area) {
        return None;
    }
    
    // Check if click is in header
    if click_y < table_area.y + header_height {
        // Find column in header
        let relative_x = click_x.saturating_sub(table_area.x);
        let mut current_x = 0;
        for (col_idx, &width) in column_widths.iter().enumerate() {
            if relative_x >= current_x && relative_x < current_x + width {
                return Some((0, col_idx)); // Row 0 for header
            }
            current_x += width;
        }
        return None;
    }
    
    // Calculate row
    let relative_y = click_y.saturating_sub(table_area.y + header_height);
    let row_index = (relative_y / row_height) as usize + row_offset;
    
    // Calculate column
    let relative_x = click_x.saturating_sub(table_area.x);
    let mut current_x = 0;
    for (col_idx, &width) in column_widths.iter().enumerate() {
        if relative_x >= current_x && relative_x < current_x + width {
            return Some((row_index, col_idx));
        }
        current_x += width;
    }
    
    None
}

/// Enable mouse support in terminal (call this once at startup)
pub fn enable_mouse_support() -> Result<(), Box<dyn std::error::Error>> {
    use crossterm::execute;
    use crossterm::terminal::{EnterAlternateScreen, LeaveAlternateScreen};
    use crossterm::event::{EnableMouseCapture, DisableMouseCapture};
    use std::io::stdout;
    
    execute!(stdout(), EnableMouseCapture)?;
    Ok(())
}

/// Disable mouse support in terminal (call this on cleanup)
pub fn disable_mouse_support() -> Result<(), Box<dyn std::error::Error>> {
    use crossterm::execute;
    use crossterm::event::DisableMouseCapture;
    use std::io::stdout;
    
    execute!(stdout(), DisableMouseCapture)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crossterm::event::{Event, MouseButton, MouseEvent, MouseEventKind};
    
    #[test]
    fn test_is_point_in_rect() {
        let rect = Rect::new(10, 5, 20, 10);
        
        assert!(is_point_in_rect(15, 8, rect)); // Inside
        assert!(is_point_in_rect(10, 5, rect)); // Top-left corner
        assert!(is_point_in_rect(29, 14, rect)); // Bottom-right corner
        assert!(!is_point_in_rect(9, 5, rect)); // Left of
        assert!(!is_point_in_rect(30, 5, rect)); // Right of
        assert!(!is_point_in_rect(15, 4, rect)); // Above
        assert!(!is_point_in_rect(15, 15, rect)); // Below
    }
    
    #[test]
    fn test_find_clicked_list_item() {
        let list_area = Rect::new(0, 2, 50, 20);
        let item_height = 2;
        let offset = 0;
        
        // Click on first item
        assert_eq!(find_clicked_list_item(2, list_area, item_height, offset), Some(0));
        assert_eq!(find_clicked_list_item(3, list_area, item_height, offset), Some(0));
        
        // Click on second item
        assert_eq!(find_clicked_list_item(4, list_area, item_height, offset), Some(1));
        
        // Click with offset
        assert_eq!(find_clicked_list_item(2, list_area, item_height, 5), Some(5));
        
        // Click outside
        assert_eq!(find_clicked_list_item(1, list_area, item_height, offset), None);
        assert_eq!(find_clicked_list_item(25, list_area, item_height, offset), None);
    }
    
    #[test]
    fn test_parse_mouse_event() {
        let config = MouseConfig::default();
        
        let mouse_event = MouseEvent {
            kind: MouseEventKind::Down(MouseButton::Left),
            column: 10,
            row: 5,
            modifiers: KeyModifiers::empty(),
        };
        let event = Event::Mouse(mouse_event);
        
        let action = parse_mouse_event(&event, &config);
        assert!(action.is_some());
        if let Some(MouseAction::LeftClick { x, y }) = action {
            assert_eq!(x, 10);
            assert_eq!(y, 5);
        } else {
            panic!("Expected LeftClick");
        }
    }
    
    #[test]
    fn test_mouse_action_position() {
        let action = MouseAction::LeftClick { x: 10, y: 5 };
        assert_eq!(action.position(), Some((10, 5)));
        
        let action = MouseAction::ScrollUp;
        assert_eq!(action.position(), None);
    }
    
    #[test]
    fn test_mouse_action_is_click() {
        assert!(MouseAction::LeftClick { x: 0, y: 0 }.is_click());
        assert!(MouseAction::RightClick { x: 0, y: 0 }.is_click());
        assert!(!MouseAction::ScrollUp.is_click());
    }
}


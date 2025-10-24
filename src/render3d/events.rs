//! Interactive 3D Rendering Event System
//!
//! This module provides event handling for interactive 3D rendering,
//! including keyboard and mouse input processing using crossterm.

use crossterm::event::{Event, KeyCode, KeyModifiers, MouseButton, MouseEvent, MouseEventKind};
use std::collections::HashMap;
use std::time::Duration;

/// Interactive events for 3D rendering
#[derive(Debug, Clone, PartialEq)]
pub enum InteractiveEvent {
    /// Keyboard key press
    KeyPress(KeyCode, KeyModifiers),
    /// Mouse click event
    MouseClick(MouseClickEvent),
    /// Mouse movement event
    MouseMove(MouseMoveEvent),
    /// Terminal resize event
    Resize(usize, usize),
    /// Quit/exit event
    Quit,
    /// Custom action event
    Action(Action),
}

/// Mouse click event details
#[derive(Debug, Clone, PartialEq)]
pub struct MouseClickEvent {
    pub button: MouseButton,
    pub x: usize,
    pub y: usize,
    pub modifiers: KeyModifiers,
}

/// Mouse movement event details
#[derive(Debug, Clone, PartialEq)]
pub struct MouseMoveEvent {
    pub x: usize,
    pub y: usize,
    pub modifiers: KeyModifiers,
}

/// Custom actions for interactive rendering
#[derive(Debug, Clone, PartialEq)]
pub enum Action {
    /// Camera movement actions
    CameraMove(CameraAction),
    /// Equipment selection actions
    EquipmentSelect(String),
    /// View mode changes
    ViewModeChange(ViewModeAction),
    /// Floor navigation
    FloorChange(i32),
    /// Zoom operations
    Zoom(ZoomAction),
}

/// Camera movement actions
#[derive(Debug, Clone, PartialEq)]
pub enum CameraAction {
    MoveUp,
    MoveDown,
    MoveLeft,
    MoveRight,
    MoveForward,
    MoveBackward,
    RotateLeft,
    RotateRight,
    RotateUp,
    RotateDown,
    Reset,
}

/// View mode change actions
#[derive(Debug, Clone, PartialEq)]
pub enum ViewModeAction {
    Standard,
    CrossSection,
    Connections,
    Maintenance,
    ToggleRooms,
    ToggleStatus,
    ToggleConnections,
}

/// Zoom actions
#[derive(Debug, Clone, PartialEq)]
pub enum ZoomAction {
    In,
    Out,
    Reset,
}

/// Event handler for interactive 3D rendering
pub struct EventHandler {
    /// Key bindings mapping keys to actions
    key_bindings: HashMap<KeyCode, Action>,
    /// Mouse bindings mapping buttons to actions
    mouse_bindings: HashMap<MouseButton, Action>,
    /// Event processing configuration
    config: EventConfig,
}

/// Event processing configuration
#[derive(Debug, Clone)]
pub struct EventConfig {
    /// Enable mouse support
    pub enable_mouse: bool,
    /// Enable key repeat
    pub enable_key_repeat: bool,
    /// Event polling interval
    pub poll_interval: Duration,
    /// Maximum events per frame
    pub max_events_per_frame: usize,
}

impl EventHandler {
    /// Create a new event handler with default key bindings
    pub fn new() -> Self {
        let mut handler = Self {
            key_bindings: HashMap::new(),
            mouse_bindings: HashMap::new(),
            config: EventConfig::default(),
        };
        
        handler.setup_default_bindings();
        handler
    }

    /// Create event handler with custom configuration
    pub fn with_config(config: EventConfig) -> Self {
        let mut handler = Self {
            key_bindings: HashMap::new(),
            mouse_bindings: HashMap::new(),
            config,
        };
        
        handler.setup_default_bindings();
        handler
    }

    /// Setup default key bindings for 3D navigation
    fn setup_default_bindings(&mut self) {
        // Camera movement
        self.key_bindings.insert(KeyCode::Up, Action::CameraMove(CameraAction::MoveUp));
        self.key_bindings.insert(KeyCode::Down, Action::CameraMove(CameraAction::MoveDown));
        self.key_bindings.insert(KeyCode::Left, Action::CameraMove(CameraAction::MoveLeft));
        self.key_bindings.insert(KeyCode::Right, Action::CameraMove(CameraAction::MoveRight));
        self.key_bindings.insert(KeyCode::Char('w'), Action::CameraMove(CameraAction::MoveForward));
        self.key_bindings.insert(KeyCode::Char('s'), Action::CameraMove(CameraAction::MoveBackward));
        self.key_bindings.insert(KeyCode::Char('a'), Action::CameraMove(CameraAction::RotateLeft));
        self.key_bindings.insert(KeyCode::Char('d'), Action::CameraMove(CameraAction::RotateRight));
        self.key_bindings.insert(KeyCode::Char('q'), Action::CameraMove(CameraAction::RotateUp));
        self.key_bindings.insert(KeyCode::Char('e'), Action::CameraMove(CameraAction::RotateDown));
        self.key_bindings.insert(KeyCode::Char('r'), Action::CameraMove(CameraAction::Reset));

        // Zoom controls
        self.key_bindings.insert(KeyCode::Char('+'), Action::Zoom(ZoomAction::In));
        self.key_bindings.insert(KeyCode::Char('='), Action::Zoom(ZoomAction::In));
        self.key_bindings.insert(KeyCode::Char('-'), Action::Zoom(ZoomAction::Out));
        self.key_bindings.insert(KeyCode::Char('0'), Action::Zoom(ZoomAction::Reset));

        // View mode changes
        self.key_bindings.insert(KeyCode::Char('1'), Action::ViewModeChange(ViewModeAction::Standard));
        self.key_bindings.insert(KeyCode::Char('2'), Action::ViewModeChange(ViewModeAction::CrossSection));
        self.key_bindings.insert(KeyCode::Char('3'), Action::ViewModeChange(ViewModeAction::Connections));
        self.key_bindings.insert(KeyCode::Char('4'), Action::ViewModeChange(ViewModeAction::Maintenance));
        self.key_bindings.insert(KeyCode::Char('t'), Action::ViewModeChange(ViewModeAction::ToggleRooms));
        self.key_bindings.insert(KeyCode::Char('i'), Action::ViewModeChange(ViewModeAction::ToggleStatus));
        self.key_bindings.insert(KeyCode::Char('c'), Action::ViewModeChange(ViewModeAction::ToggleConnections));

        // Floor navigation
        self.key_bindings.insert(KeyCode::PageUp, Action::FloorChange(1));
        self.key_bindings.insert(KeyCode::PageDown, Action::FloorChange(-1));

        // Quit
        self.key_bindings.insert(KeyCode::Esc, Action::CameraMove(CameraAction::Reset));
        self.key_bindings.insert(KeyCode::Char('q'), Action::CameraMove(CameraAction::Reset));
    }

    /// Add custom key binding
    pub fn add_key_binding(&mut self, key: KeyCode, action: Action) {
        self.key_bindings.insert(key, action);
    }

    /// Remove key binding
    pub fn remove_key_binding(&mut self, key: KeyCode) {
        self.key_bindings.remove(&key);
    }

    /// Add custom mouse binding
    pub fn add_mouse_binding(&mut self, button: MouseButton, action: Action) {
        self.mouse_bindings.insert(button, action);
    }

    /// Process a crossterm event and convert to interactive event
    pub fn process_event(&self, event: Event) -> Option<InteractiveEvent> {
        match event {
            Event::Key(key_event) => {
                if let Some(action) = self.key_bindings.get(&key_event.code) {
                    Some(InteractiveEvent::Action(action.clone()))
                } else {
                    Some(InteractiveEvent::KeyPress(key_event.code, key_event.modifiers))
                }
            }
            Event::Mouse(mouse_event) if self.config.enable_mouse => {
                self.process_mouse_event(mouse_event)
            }
            Event::Resize(width, height) => {
                Some(InteractiveEvent::Resize(width as usize, height as usize))
            }
            _ => None,
        }
    }

    /// Process mouse event
    fn process_mouse_event(&self, mouse_event: MouseEvent) -> Option<InteractiveEvent> {
        match mouse_event.kind {
            MouseEventKind::Down(button) => {
                if let Some(action) = self.mouse_bindings.get(&button) {
                    Some(InteractiveEvent::Action(action.clone()))
                } else {
                    Some(InteractiveEvent::MouseClick(MouseClickEvent {
                        button,
                        x: mouse_event.column as usize,
                        y: mouse_event.row as usize,
                        modifiers: mouse_event.modifiers,
                    }))
                }
            }
            MouseEventKind::Up(_) => None, // Ignore mouse up events
            MouseEventKind::Drag(_button) => {
                Some(InteractiveEvent::MouseMove(MouseMoveEvent {
                    x: mouse_event.column as usize,
                    y: mouse_event.row as usize,
                    modifiers: mouse_event.modifiers,
                }))
            }
            MouseEventKind::Moved => {
                Some(InteractiveEvent::MouseMove(MouseMoveEvent {
                    x: mouse_event.column as usize,
                    y: mouse_event.row as usize,
                    modifiers: mouse_event.modifiers,
                }))
            }
            MouseEventKind::ScrollUp => Some(InteractiveEvent::Action(Action::Zoom(ZoomAction::In))),
            MouseEventKind::ScrollDown => Some(InteractiveEvent::Action(Action::Zoom(ZoomAction::Out))),
            MouseEventKind::ScrollLeft | MouseEventKind::ScrollRight => None, // Ignore horizontal scroll
        }
    }

    /// Get event configuration
    pub fn config(&self) -> &EventConfig {
        &self.config
    }

    /// Update event configuration
    pub fn update_config(&mut self, config: EventConfig) {
        self.config = config;
    }

    /// Get help text for all key bindings
    pub fn get_help_text(&self) -> String {
        let mut help = String::new();
        help.push_str("Interactive 3D Controls:\n");
        help.push_str("======================\n\n");
        
        help.push_str("Camera Movement:\n");
        help.push_str("  Arrow Keys    - Move camera\n");
        help.push_str("  W/S           - Move forward/backward\n");
        help.push_str("  A/D           - Rotate left/right\n");
        help.push_str("  Q/E           - Rotate up/down\n");
        help.push_str("  R             - Reset camera\n\n");
        
        help.push_str("Zoom Controls:\n");
        help.push_str("  +/-           - Zoom in/out\n");
        help.push_str("  0             - Reset zoom\n");
        help.push_str("  Mouse Wheel   - Zoom in/out\n\n");
        
        help.push_str("View Modes:\n");
        help.push_str("  1             - Standard view\n");
        help.push_str("  2             - Cross-section view\n");
        help.push_str("  3             - Connections view\n");
        help.push_str("  4             - Maintenance view\n");
        help.push_str("  T             - Toggle rooms\n");
        help.push_str("  I             - Toggle status indicators\n");
        help.push_str("  C             - Toggle connections\n\n");
        
        help.push_str("Navigation:\n");
        help.push_str("  Page Up/Down  - Change floors\n");
        help.push_str("  Mouse Click    - Select equipment\n");
        help.push_str("  ESC/Q          - Quit interactive mode\n\n");
        
        help
    }
}

impl Default for EventConfig {
    fn default() -> Self {
        Self {
            enable_mouse: true,
            enable_key_repeat: true,
            poll_interval: Duration::from_millis(16), // ~60 FPS
            max_events_per_frame: 10,
        }
    }
}

impl Default for EventHandler {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crossterm::event::{KeyEvent, KeyModifiers};

    #[test]
    fn test_event_handler_creation() {
        let handler = EventHandler::new();
        assert!(!handler.key_bindings.is_empty());
        assert!(handler.config.enable_mouse);
    }

    #[test]
    fn test_key_binding_processing() {
        let handler = EventHandler::new();
        
        let key_event = Event::Key(KeyEvent {
            code: KeyCode::Up,
            modifiers: KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        });
        
        let interactive_event = handler.process_event(key_event);
        assert!(interactive_event.is_some());
        
        if let Some(InteractiveEvent::Action(Action::CameraMove(CameraAction::MoveUp))) = interactive_event {
            // Correct action
        } else {
            panic!("Expected MoveUp action");
        }
    }

    #[test]
    fn test_custom_key_binding() {
        let mut handler = EventHandler::new();
        
        handler.add_key_binding(KeyCode::Char('x'), Action::EquipmentSelect("test".to_string()));
        
        let key_event = Event::Key(KeyEvent {
            code: KeyCode::Char('x'),
            modifiers: KeyModifiers::empty(),
            kind: crossterm::event::KeyEventKind::Press,
            state: crossterm::event::KeyEventState::empty(),
        });
        
        let interactive_event = handler.process_event(key_event);
        assert!(interactive_event.is_some());
        
        if let Some(InteractiveEvent::Action(Action::EquipmentSelect(id))) = interactive_event {
            assert_eq!(id, "test");
        } else {
            panic!("Expected EquipmentSelect action");
        }
    }

    #[test]
    fn test_help_text_generation() {
        let handler = EventHandler::new();
        let help_text = handler.get_help_text();
        
        assert!(help_text.contains("Interactive 3D Controls"));
        assert!(help_text.contains("Arrow Keys"));
        assert!(help_text.contains("W/S"));
        assert!(help_text.contains("ESC/Q"));
    }

    #[test]
    fn test_event_config_defaults() {
        let config = EventConfig::default();
        assert!(config.enable_mouse);
        assert!(config.enable_key_repeat);
        assert_eq!(config.poll_interval, Duration::from_millis(16));
        assert_eq!(config.max_events_per_frame, 10);
    }
}

//! Error Modal System for ArxOS TUI
//!
//! Provides:
//! - Modal dialogs for displaying errors
//! - Error suggestions and recovery steps
//! - Action buttons for error handling

use crate::tui::Theme;
use crate::error::ArxError;
use crossterm::event::{Event, KeyCode};
use ratatui::{
    layout::{Alignment, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph},
};

/// Error modal state
pub struct ErrorModal {
    pub show: bool,
    pub error: Option<ArxError>,
    pub selected_action: usize,
    pub actions: Vec<ErrorAction>,
}

/// Available error actions
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ErrorAction {
    Retry,
    Ignore,
    ViewDetails,
    ShowHelp,
    Dismiss,
}

impl ErrorModal {
    pub fn new() -> Self {
        Self {
            show: false,
            error: None,
            selected_action: 0,
            actions: vec![
                ErrorAction::ViewDetails,
                ErrorAction::ShowHelp,
                ErrorAction::Dismiss,
            ],
        }
    }

    pub fn show_error(&mut self, error: ArxError) {
        self.error = Some(error);
        self.show = true;
        self.selected_action = 0;

        // Determine available actions based on error type
        self.actions = match &self.error {
            Some(ArxError::GitOperation { .. }) => {
                vec![
                    ErrorAction::Retry,
                    ErrorAction::ViewDetails,
                    ErrorAction::ShowHelp,
                    ErrorAction::Dismiss,
                ]
            }
            Some(ArxError::Configuration { .. }) => {
                vec![
                    ErrorAction::ViewDetails,
                    ErrorAction::ShowHelp,
                    ErrorAction::Dismiss,
                ]
            }
            Some(ArxError::Validation { .. }) => {
                vec![
                    ErrorAction::ViewDetails,
                    ErrorAction::ShowHelp,
                    ErrorAction::Dismiss,
                ]
            }
            _ => {
                vec![
                    ErrorAction::ViewDetails,
                    ErrorAction::ShowHelp,
                    ErrorAction::Dismiss,
                ]
            }
        };
        self.selected_action = 0;
    }

    pub fn dismiss(&mut self) {
        self.show = false;
        self.error = None;
    }

    pub fn next_action(&mut self) {
        if !self.actions.is_empty() {
            self.selected_action = (self.selected_action + 1) % self.actions.len();
        }
    }

    pub fn previous_action(&mut self) {
        if !self.actions.is_empty() {
            self.selected_action =
                (self.selected_action + self.actions.len() - 1) % self.actions.len();
        }
    }

    pub fn select_action(&mut self) -> Option<ErrorAction> {
        if self.selected_action < self.actions.len() {
            Some(self.actions[self.selected_action].clone())
        } else {
            None
        }
    }
}

impl Default for ErrorModal {
    fn default() -> Self {
        Self::new()
    }
}

impl ErrorAction {
    pub fn label(&self) -> &'static str {
        match self {
            ErrorAction::Retry => "Retry",
            ErrorAction::Ignore => "Ignore",
            ErrorAction::ViewDetails => "View Details",
            ErrorAction::ShowHelp => "Show Help",
            ErrorAction::Dismiss => "Dismiss",
        }
    }

    pub fn key(&self) -> &'static str {
        match self {
            ErrorAction::Retry => "r",
            ErrorAction::Ignore => "i",
            ErrorAction::ViewDetails => "d",
            ErrorAction::ShowHelp => "h",
            ErrorAction::Dismiss => "Esc",
        }
    }
}

/// Calculate centered modal area
pub fn calculate_modal_area(area: Rect) -> Rect {
    let modal_width = (area.width as f32 * 0.8) as u16;
    let modal_height = (area.height as f32 * 0.7) as u16;
    let modal_x = (area.width.saturating_sub(modal_width)) / 2;
    let modal_y = (area.height.saturating_sub(modal_height)) / 2;

    Rect {
        x: area.x + modal_x,
        y: area.y + modal_y,
        width: modal_width,
        height: modal_height,
    }
}

/// Render error modal
pub fn render_error_modal<'a>(
    modal: &'a ErrorModal,
    _area: Rect,
    theme: &'a Theme,
) -> Option<Paragraph<'a>> {
    if !modal.show || modal.error.is_none() {
        return None;
    }

    let error = modal.error.as_ref().unwrap();

    let mut lines = vec![
        Line::from(vec![Span::styled(
            "Error",
            Style::default().fg(Color::Red).add_modifier(Modifier::BOLD),
        )]),
        Line::from(Span::raw("")),
    ];

    // Error message
    let error_message = match error {
        ArxError::IfcProcessing { message, .. } => format!("IFC Processing Error: {}", message),
        ArxError::Configuration { message, .. } => format!("Configuration Error: {}", message),
        ArxError::GitOperation { message, .. } => format!("Git Operation Error: {}", message),
        ArxError::Validation { message, .. } => format!("Validation Error: {}", message),
        ArxError::IoError { message, .. } => format!("IO Error: {}", message),
        ArxError::YamlProcessing { message, .. } => format!("YAML Processing Error: {}", message),
        ArxError::SpatialData { message, .. } => format!("Spatial Data Error: {}", message),
        ArxError::AddressValidation { message, .. } => {
            format!("Address Validation Error: {}", message)
        }
        ArxError::CounterOverflow { counter_name } => format!("Counter Overflow Error: {}", counter_name),
        ArxError::PathInvalid { path, expected } => format!("Path Invalid Error: '{}' (expected: {})", path, expected),
        ArxError::Io(err) => format!("IO Error: {}", err),
        ArxError::Serialization(msg) => format!("Serialization Error: {}", msg),
        ArxError::Git(msg) => format!("Git Error: {}", msg),
        ArxError::Ifc(msg) => format!("IFC Error: {}", msg),
        ArxError::Config(msg) => format!("Configuration Error: {}", msg),
        ArxError::General(msg) => format!("Error: {}", msg),
    };

    lines.push(Line::from(vec![Span::styled(
        error_message,
        Style::default().fg(theme.text),
    )]));
    lines.push(Line::from(Span::raw("")));

    // Suggestions
    let context = error.context();
    if !context.suggestions.is_empty() {
        lines.push(Line::from(vec![Span::styled(
            "Suggestions:",
            Style::default()
                .fg(Color::Yellow)
                .add_modifier(Modifier::BOLD),
        )]));
        for suggestion in &context.suggestions {
            lines.push(Line::from(vec![
                Span::styled("  • ", Style::default().fg(Color::Yellow)),
                Span::styled(suggestion.clone(), Style::default().fg(theme.text)),
            ]));
        }
        lines.push(Line::from(Span::raw("")));
    }

    // Recovery steps
    if !context.recovery_steps.is_empty() {
        lines.push(Line::from(vec![Span::styled(
            "Recovery Steps:",
            Style::default()
                .fg(Color::Cyan)
                .add_modifier(Modifier::BOLD),
        )]));
        for (i, step) in context.recovery_steps.iter().enumerate() {
            lines.push(Line::from(vec![
                Span::styled(format!("  {}. ", i + 1), Style::default().fg(Color::Cyan)),
                Span::styled(step.clone(), Style::default().fg(theme.text)),
            ]));
        }
        lines.push(Line::from(Span::raw("")));
    }

    // Actions
    lines.push(Line::from(vec![Span::styled(
        "Actions:",
        Style::default()
            .fg(theme.accent)
            .add_modifier(Modifier::BOLD),
    )]));
    for (i, action) in modal.actions.iter().enumerate() {
        let is_selected = i == modal.selected_action;
        let prefix = if is_selected { "> " } else { "  " };
        lines.push(Line::from(vec![
            Span::styled(
                prefix.to_string(),
                Style::default().fg(if is_selected {
                    theme.accent
                } else {
                    theme.muted
                }),
            ),
            Span::styled(
                format!("{} ({})", action.label(), action.key()),
                Style::default()
                    .fg(if is_selected {
                        theme.accent
                    } else {
                        theme.text
                    })
                    .add_modifier(if is_selected {
                        Modifier::BOLD
                    } else {
                        Modifier::empty()
                    }),
            ),
        ]));
    }

    lines.push(Line::from(Span::raw("")));
    lines.push(Line::from(vec![Span::styled(
        "Use ↑/↓ to select action, Enter to confirm, Esc to dismiss",
        Style::default().fg(theme.muted),
    )]));

    Some(
        Paragraph::new(lines)
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title("Error")
                    .border_style(Style::default().fg(Color::Red)),
            )
            .alignment(Alignment::Left)
            .style(Style::default().fg(theme.text)),
    )
    // Note: modal_area is calculated but the Paragraph widget doesn't support custom positioning
    // The caller (render_error_modal_in_frame) should use the calculated area for proper centering
}

/// Handle error modal events
pub fn handle_error_modal_event(event: Event, modal: &mut ErrorModal) -> Option<ErrorAction> {
    if !modal.show {
        return None;
    }

    match event {
        Event::Key(key_event) => match key_event.code {
            KeyCode::Esc => {
                modal.dismiss();
                None
            }
            KeyCode::Up | KeyCode::Char('k') => {
                modal.previous_action();
                None
            }
            KeyCode::Down | KeyCode::Char('j') => {
                modal.next_action();
                None
            }
            KeyCode::Enter => modal.select_action(),
            KeyCode::Char('r') => {
                if modal.actions.contains(&ErrorAction::Retry) {
                    Some(ErrorAction::Retry)
                } else {
                    None
                }
            }
            KeyCode::Char('d') => {
                if modal.actions.contains(&ErrorAction::ViewDetails) {
                    Some(ErrorAction::ViewDetails)
                } else {
                    None
                }
            }
            KeyCode::Char('h') => {
                if modal.actions.contains(&ErrorAction::ShowHelp) {
                    Some(ErrorAction::ShowHelp)
                } else {
                    None
                }
            }
            KeyCode::Char('i') => {
                if modal.actions.contains(&ErrorAction::Ignore) {
                    Some(ErrorAction::Ignore)
                } else {
                    None
                }
            }
            _ => None,
        },
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::error::ErrorContext;
    use ratatui::layout::Rect;

    fn create_test_error() -> ArxError {
        ArxError::IoError {
            message: "Test error message".to_string(),
            path: Some("/test/path".to_string()),
        }
    }

    fn create_git_error() -> ArxError {
        ArxError::GitOperation {
            message: "Git operation failed".to_string(),
            context: Some("commit".to_string()),
        }
    }

    fn create_config_error() -> ArxError {
        ArxError::Configuration {
            message: "Configuration error".to_string(),
            details: Some("test_field".to_string()),
        }
    }

    #[test]
    fn test_error_modal_new() {
        let modal = ErrorModal::new();
        assert!(!modal.show, "Should not be shown initially");
        assert!(modal.error.is_none(), "Should have no error initially");
        assert_eq!(modal.selected_action, 0, "Should start at first action");
        assert!(!modal.actions.is_empty(), "Should have default actions");
    }

    #[test]
    fn test_error_modal_show_error() {
        let mut modal = ErrorModal::new();
        let error = create_test_error();

        modal.show_error(error);
        assert!(modal.show, "Should be shown");
        assert!(modal.error.is_some(), "Should have error");
        assert_eq!(modal.selected_action, 0, "Should reset selection");
    }

    #[test]
    fn test_error_modal_dismiss() {
        let mut modal = ErrorModal::new();
        modal.show_error(create_test_error());
        assert!(modal.show, "Should be shown");

        modal.dismiss();
        assert!(!modal.show, "Should be dismissed");
        assert!(modal.error.is_none(), "Should clear error");
    }

    #[test]
    fn test_error_modal_next_action() {
        let mut modal = ErrorModal::new();
        modal.show_error(create_test_error());
        let initial_action = modal.selected_action;

        modal.next_action();
        if modal.actions.len() > 1 {
            assert_ne!(
                modal.selected_action, initial_action,
                "Selection should change"
            );
        }
    }

    #[test]
    fn test_error_modal_previous_action() {
        let mut modal = ErrorModal::new();
        modal.show_error(create_test_error());
        modal.next_action();
        let _after_next = modal.selected_action;

        modal.previous_action();
        assert_eq!(modal.selected_action, 0, "Should wrap to first action");
    }

    #[test]
    fn test_error_modal_select_action() {
        let mut modal = ErrorModal::new();
        modal.show_error(create_test_error());

        let action = modal.select_action();
        assert!(action.is_some(), "Should return an action");
        assert_eq!(
            action.unwrap(),
            modal.actions[0],
            "Should return first action"
        );
    }

    #[test]
    fn test_error_modal_actions_by_type() {
        let mut modal = ErrorModal::new();

        // Git error should have Retry action
        modal.show_error(create_git_error());
        assert!(
            modal.actions.contains(&ErrorAction::Retry),
            "Git error should have Retry action"
        );

        // Config error should not have Retry
        modal.show_error(create_config_error());
        assert!(
            !modal.actions.contains(&ErrorAction::Retry),
            "Config error should not have Retry action"
        );
    }

    #[test]
    fn test_error_action_labels() {
        assert_eq!(ErrorAction::Retry.label(), "Retry");
        assert_eq!(ErrorAction::Ignore.label(), "Ignore");
        assert_eq!(ErrorAction::ViewDetails.label(), "View Details");
        assert_eq!(ErrorAction::ShowHelp.label(), "Show Help");
        assert_eq!(ErrorAction::Dismiss.label(), "Dismiss");
    }

    #[test]
    fn test_error_action_keys() {
        assert_eq!(ErrorAction::Retry.key(), "r");
        assert_eq!(ErrorAction::Ignore.key(), "i");
        assert_eq!(ErrorAction::ViewDetails.key(), "d");
        assert_eq!(ErrorAction::ShowHelp.key(), "h");
        assert_eq!(ErrorAction::Dismiss.key(), "Esc");
    }

    #[test]
    fn test_calculate_modal_area() {
        let area = Rect::new(0, 0, 100, 50);
        let modal_area = calculate_modal_area(area);

        assert_eq!(modal_area.width, 80, "Should be 80% of width");
        assert_eq!(modal_area.height, 35, "Should be 70% of height");
        assert!(modal_area.x > 0, "Should be centered horizontally");
        assert!(modal_area.y > 0, "Should be centered vertically");
    }

    #[test]
    fn test_render_error_modal() {
        let mut modal = ErrorModal::new();
        modal.show_error(create_test_error());
        let theme = Theme::default();
        let area = Rect::new(0, 0, 80, 24);

        let paragraph = render_error_modal(&modal, area, &theme);
        assert!(paragraph.is_some(), "Should render error modal");
    }

    #[test]
    fn test_render_error_modal_not_shown() {
        let modal = ErrorModal::new();
        let theme = Theme::default();
        let area = Rect::new(0, 0, 80, 24);

        let paragraph = render_error_modal(&modal, area, &theme);
        assert!(paragraph.is_none(), "Should not render when not shown");
    }

    #[test]
    fn test_handle_error_modal_event_esc() {
        use crossterm::event::{KeyCode, KeyEvent, KeyEventKind, KeyEventState, KeyModifiers};

        let mut modal = ErrorModal::new();
        modal.show_error(create_test_error());

        let event = Event::Key(KeyEvent {
            code: KeyCode::Esc,
            modifiers: KeyModifiers::empty(),
            kind: KeyEventKind::Press,
            state: KeyEventState::empty(),
        });

        let action = handle_error_modal_event(event, &mut modal);
        assert!(!modal.show, "Should dismiss on Esc");
        assert!(action.is_none());
    }

    #[test]
    fn test_handle_error_modal_event_arrow_keys() {
        use crossterm::event::{KeyCode, KeyEvent, KeyEventKind, KeyEventState, KeyModifiers};

        let mut modal = ErrorModal::new();
        modal.show_error(create_test_error());
        let initial = modal.selected_action;

        let event = Event::Key(KeyEvent {
            code: KeyCode::Down,
            modifiers: KeyModifiers::empty(),
            kind: KeyEventKind::Press,
            state: KeyEventState::empty(),
        });

        handle_error_modal_event(event, &mut modal);
        if modal.actions.len() > 1 {
            assert_ne!(modal.selected_action, initial, "Should move selection down");
        }
    }

    #[test]
    fn test_handle_error_modal_event_enter() {
        use crossterm::event::{KeyCode, KeyEvent, KeyEventKind, KeyEventState, KeyModifiers};

        let mut modal = ErrorModal::new();
        modal.show_error(create_test_error());

        let event = Event::Key(KeyEvent {
            code: KeyCode::Enter,
            modifiers: KeyModifiers::empty(),
            kind: KeyEventKind::Press,
            state: KeyEventState::empty(),
        });

        let action = handle_error_modal_event(event, &mut modal);
        assert!(action.is_some(), "Should return action on Enter");
    }

    #[test]
    fn test_handle_error_modal_event_shortcut_keys() {
        use crossterm::event::{KeyCode, KeyEvent, KeyEventKind, KeyEventState, KeyModifiers};

        let mut modal = ErrorModal::new();
        modal.show_error(create_git_error()); // Has Retry action

        // Test 'r' key for Retry
        let event = Event::Key(KeyEvent {
            code: KeyCode::Char('r'),
            modifiers: KeyModifiers::empty(),
            kind: KeyEventKind::Press,
            state: KeyEventState::empty(),
        });

        let action = handle_error_modal_event(event, &mut modal);
        assert_eq!(
            action,
            Some(ErrorAction::Retry),
            "Should return Retry action"
        );
    }
}

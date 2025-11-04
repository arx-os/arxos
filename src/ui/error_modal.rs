//! Error Modal System for ArxOS TUI
//!
//! Provides:
//! - Modal dialogs for displaying errors
//! - Error suggestions and recovery steps
//! - Action buttons for error handling

use crate::ui::Theme;
use crate::error::{ArxError, ErrorDisplay};
use crossterm::event::{Event, KeyCode};
use ratatui::{
    layout::{Alignment, Constraint, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph},
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
            self.selected_action = (self.selected_action + self.actions.len() - 1) % self.actions.len();
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
    area: Rect,
    theme: &'a Theme,
) -> Option<Paragraph<'a>> {
    if !modal.show || modal.error.is_none() {
        return None;
    }

    let error = modal.error.as_ref().unwrap();

    let mut lines = vec![
        Line::from(vec![
            Span::styled(
                "Error",
                Style::default().fg(Color::Red).add_modifier(Modifier::BOLD),
            ),
        ]),
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
    };

    lines.push(Line::from(vec![
        Span::styled(error_message, Style::default().fg(theme.text)),
    ]));
    lines.push(Line::from(Span::raw("")));

    // Suggestions
    let context = error.context();
    if !context.suggestions.is_empty() {
        lines.push(Line::from(vec![
            Span::styled(
                "Suggestions:",
                Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD),
            ),
        ]));
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
        lines.push(Line::from(vec![
            Span::styled(
                "Recovery Steps:",
                Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD),
            ),
        ]));
        for (i, step) in context.recovery_steps.iter().enumerate() {
            lines.push(Line::from(vec![
                Span::styled(format!("  {}. ", i + 1), Style::default().fg(Color::Cyan)),
                Span::styled(step.clone(), Style::default().fg(theme.text)),
            ]));
        }
        lines.push(Line::from(Span::raw("")));
    }

    // Actions
    lines.push(Line::from(vec![
        Span::styled(
            "Actions:",
            Style::default().fg(theme.accent).add_modifier(Modifier::BOLD),
        ),
    ]));
    for (i, action) in modal.actions.iter().enumerate() {
        let is_selected = i == modal.selected_action;
        let prefix = if is_selected { "> " } else { "  " };
        lines.push(Line::from(vec![
            Span::styled(
                prefix.to_string(),
                Style::default().fg(if is_selected { theme.accent } else { theme.muted }),
            ),
            Span::styled(
                format!("{} ({})", action.label(), action.key()),
                Style::default()
                    .fg(if is_selected { theme.accent } else { theme.text })
                    .add_modifier(if is_selected { Modifier::BOLD } else { Modifier::empty() }),
            ),
        ]));
    }

    lines.push(Line::from(Span::raw("")));
    lines.push(Line::from(vec![
        Span::styled(
            "Use ↑/↓ to select action, Enter to confirm, Esc to dismiss",
            Style::default().fg(theme.muted),
        ),
    ]));

    Some(
        Paragraph::new(lines)
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .title("Error")
                    .border_style(Style::default().fg(Color::Red))
            )
            .alignment(Alignment::Left)
            .style(Style::default().fg(theme.text))
    )
    // Note: modal_area is calculated but the Paragraph widget doesn't support custom positioning
    // The caller (render_error_modal_in_frame) should use the calculated area for proper centering
}

/// Handle error modal events
pub fn handle_error_modal_event(
    event: Event,
    modal: &mut ErrorModal,
) -> Option<ErrorAction> {
    if !modal.show {
        return None;
    }

    match event {
        Event::Key(key_event) => {
            match key_event.code {
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
                KeyCode::Enter => {
                    modal.select_action()
                }
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
            }
        }
        _ => None,
    }
}


//! Error Modal Integration Helpers
//!
//! Provides utilities for integrating error modals into TUI components

use crate::tui::{handle_error_modal_event, render_error_modal, ErrorAction, ErrorModal};
use crate::error::ArxError;
use crossterm::event::Event;
use ratatui::Frame;

/// Helper to render error modal in a frame
pub fn render_error_modal_in_frame(
    frame: &mut Frame,
    modal: &ErrorModal,
    theme: &crate::tui::Theme,
) {
    use crate::tui::error_modal::calculate_modal_area;

    if let Some(error_paragraph) = render_error_modal(modal, frame.size(), theme) {
        // Calculate centered modal area and render there
        let modal_area = calculate_modal_area(frame.size());
        frame.render_widget(error_paragraph, modal_area);
    }
}

/// Helper to handle error and show modal
pub fn handle_error_with_modal(
    error: Box<dyn std::error::Error>,
    modal: &mut ErrorModal,
) -> Result<Option<ErrorAction>, Box<dyn std::error::Error>> {
    // Convert error to ArxError
    // Try to downcast first, otherwise create generic error
    let error_msg = error.to_string();
    let arx_error = if let Ok(arx_err) = error.downcast::<ArxError>() {
        *arx_err
    } else {
        // Create generic ArxError from any error
        ArxError::io_error(error_msg)
    };

    modal.show_error(arx_error);
    Ok(None)
}

/// Helper to process error modal events and return action
pub fn process_error_modal_event(event: Event, modal: &mut ErrorModal) -> Option<ErrorAction> {
    handle_error_modal_event(event, modal)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::error::ErrorContext;
    use ratatui::backend::TestBackend;
    use ratatui::layout::Rect;

    #[test]
    fn test_render_error_modal_in_frame() {
        let _area = Rect::new(0, 0, 80, 24);
        let backend = TestBackend::new(80, 24);
        let mut terminal = ratatui::Terminal::new(backend).unwrap();

        let mut modal = ErrorModal::new();
        modal.show_error(ArxError::IoError {
            message: "Test error".to_string(),
            path: None,
        });

        let theme = crate::tui::Theme::default();

        terminal
            .draw(|frame| {
                render_error_modal_in_frame(frame, &modal, &theme);
            })
            .unwrap();
        // If no panic, rendering succeeded
    }

    #[test]
    fn test_handle_error_with_modal() {
        let mut modal = ErrorModal::new();
        let error = Box::new(ArxError::IoError {
            message: "Test error".to_string(),
            path: None,
        }) as Box<dyn std::error::Error>;

        let result = handle_error_with_modal(error, &mut modal);
        assert!(result.is_ok(), "Should handle error successfully");
        assert!(modal.show, "Modal should be shown");
        assert!(modal.error.is_some(), "Should have error");
    }

    #[test]
    fn test_handle_error_with_modal_arx_error() {
        let mut modal = ErrorModal::new();
        let error = Box::new(ArxError::Configuration {
            message: "Config error".to_string(),
            details: None,
        }) as Box<dyn std::error::Error>;

        let result = handle_error_with_modal(error, &mut modal);
        assert!(result.is_ok());
        assert!(modal.show, "Modal should be shown");
        assert!(modal.error.is_some(), "Should have error");

        // Verify it's a Configuration error
        if let Some(ArxError::Configuration { .. }) = modal.error {
            // Correct type
        } else {
            panic!("Should preserve error type");
        }
    }

    #[test]
    fn test_handle_error_with_modal_generic_error() {
        let mut modal = ErrorModal::new();
        let error = Box::new(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            "File not found",
        )) as Box<dyn std::error::Error>;

        let result = handle_error_with_modal(error, &mut modal);
        assert!(result.is_ok(), "Should handle generic error");
        assert!(modal.show, "Modal should be shown");
        assert!(modal.error.is_some(), "Should convert to ArxError");

        // Generic errors should become Io error
        if let Some(ArxError::Io(_)) = modal.error {
            // Correct conversion
        } else {
            panic!("Generic error should be converted to Io error, got: {:?}", modal.error);
        }
    }

    #[test]
    fn test_process_error_modal_event() {
        use crossterm::event::{KeyCode, KeyEvent, KeyEventKind, KeyEventState, KeyModifiers};

        let mut modal = ErrorModal::new();
        modal.show_error(ArxError::IoError {
            message: "Test".to_string(),
            path: None,
        });

        let event = Event::Key(KeyEvent {
            code: KeyCode::Enter,
            modifiers: KeyModifiers::empty(),
            kind: KeyEventKind::Press,
            state: KeyEventState::empty(),
        });

        let action = process_error_modal_event(event, &mut modal);
        assert!(action.is_some(), "Should return action");
    }
}

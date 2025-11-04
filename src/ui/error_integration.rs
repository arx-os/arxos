//! Error Modal Integration Helpers
//!
//! Provides utilities for integrating error modals into TUI components

use crate::ui::{ErrorModal, ErrorAction, render_error_modal, handle_error_modal_event};
use crate::error::ArxError;
use crossterm::event::Event;
use ratatui::{
    layout::Rect,
    widgets::Paragraph,
    Frame,
};

/// Helper to render error modal in a frame
pub fn render_error_modal_in_frame(
    frame: &mut Frame,
    modal: &ErrorModal,
    theme: &crate::ui::Theme,
) {
    use crate::ui::error_modal::calculate_modal_area;
    
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
pub fn process_error_modal_event(
    event: Event,
    modal: &mut ErrorModal,
) -> Option<ErrorAction> {
    handle_error_modal_event(event, modal)
}


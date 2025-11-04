//! Contextual Help System for ArxOS TUI
//!
//! Provides:
//! - Context-sensitive help overlays
//! - Interactive keyboard shortcut cheat sheet
//! - Help content per screen/context

pub mod types;
pub mod content;
pub mod shortcuts;
pub mod render;
pub mod events;

// Re-export public API
pub use types::{HelpSystem, HelpContext, Shortcut, ShortcutCategory};
pub use content::get_context_help;
pub use shortcuts::get_all_shortcuts;
pub use render::{render_help_overlay, render_shortcut_cheat_sheet};
pub use events::handle_help_event;


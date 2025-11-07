//! Contextual Help System for ArxOS TUI
//!
//! Provides:
//! - Context-sensitive help overlays
//! - Interactive keyboard shortcut cheat sheet
//! - Help content per screen/context

pub mod content;
pub mod events;
pub mod render;
pub mod shortcuts;
pub mod types;

// Re-export public API
pub use content::get_context_help;
pub use events::handle_help_event;
pub use render::{render_help_overlay, render_shortcut_cheat_sheet};
pub use shortcuts::get_all_shortcuts;
pub use types::{HelpContext, HelpSystem, Shortcut, ShortcutCategory};

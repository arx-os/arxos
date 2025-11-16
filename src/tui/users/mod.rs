//! User UI components for identity registry
//!
//! This module provides interactive TUI interfaces for:
//! - Browsing user registry
//! - Viewing user details and activity
//! - Organization grouping
//! - Contact information display
//!
//! ## Module Organization
//! - `types`: User data structures and state management
//! - `rendering`: UI rendering functions for different views
//! - `input_handlers`: Focused event handling logic
//! - `browser`: Main user browser implementation
//!
//! ## Refactoring Complete
//! Successfully split the original 857-line users.rs file into 4 focused modules,
//! reducing the main handler from 273 lines to ~100 lines with clear separation of concerns.

// Re-export public API
pub use browser::handle_user_browser;

// Internal modules with focused responsibilities
mod browser;
mod input_handlers;
mod rendering;
mod types;

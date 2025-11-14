//! ASCII rendering module for 3D building visualization
//!
//! This module provides comprehensive ASCII rendering capabilities including:
//! - Canvas-based rendering with depth buffering
//! - Equipment symbol mapping
//! - Header and legend generation
//! - Multiple output formats (advanced, ASCII art, simple)

mod canvas;
mod characters;
mod renderer;

pub use canvas::{AsciiCanvas, DepthBuffer};
pub use characters::{get_equipment_symbol, LEGEND};
pub use renderer::AsciiRenderer;

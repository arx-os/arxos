//! Pure ASCII Art CAD System for Arxos
//! 
//! This module provides CAD-level drawing capabilities that integrate with
//! the slow-bleed protocol to progressively render building intelligence.

pub mod data_model;
pub mod renderer;
pub mod algorithms;
pub mod commands;
pub mod viewport;

pub use data_model::{Drawing, Layer, Entity, Transform};
pub use renderer::{AsciiRenderer, RenderOptions};
pub use algorithms::{bresenham_line, midpoint_circle};
pub use commands::{Command, CommandParser, CommandMode};
pub use viewport::{Viewport, ViewportState, SnapMode, SnapSettings};
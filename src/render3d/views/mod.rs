//! View-specific rendering for different projection types

pub mod isometric;
pub mod orthographic;
pub mod perspective;
pub mod planar;

// Re-export view rendering functions
pub use isometric::render_isometric_view;
pub use orthographic::render_orthographic_view;
pub use perspective::render_perspective_view;
pub use planar::{render_front_view, render_side_view, render_top_down_view};

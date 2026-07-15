//! Text-based AR Overlay System for Leptos PWA client.
//!
//! Provides hardware camera access, screen label projection coordinates,
//! and the Leptos Overlay HUD component.

pub mod camera;
pub mod label;
pub mod component;

pub use camera::CameraManager;
pub use label::{LabelProjector, ScreenLabel};
pub use component::ArOverlayScreen;

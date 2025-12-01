//! Web frontend module using Leptos
//!
//! This module contains the Progressive Web App (PWA) built with Leptos and WASM.

#[cfg(feature = "web")]
pub mod app;
#[cfg(feature = "web")]
pub mod components;
#[cfg(feature = "web")]
pub mod pages;
#[cfg(feature = "web")]
pub mod wasm_bridge;

#[cfg(feature = "web")]
pub use app::App;

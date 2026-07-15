//! Discovery Layer and AR HUD overlay module.
//!
//! Handles geofenced entity queries, BLE/Marker localizations, HUD state
//! mapping, and task resolution back to the PWA Caching Layer.

pub mod location;
pub mod manager;
pub mod hud;
pub mod resolver;

pub use location::{LocationProvider, MockLocationProvider, LocationContext};
pub use manager::DiscoveryManager;
pub use hud::{HudOverlay, HudTask, SaturationTask, DanglingPoseTask};
pub use resolver::TaskResolver;

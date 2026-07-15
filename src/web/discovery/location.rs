//! Location bootstrapping and localization provider traits.
//!
//! Exposes physical-to-semantic spatial bindings via BLE, DHCP, and AR Markers.

use crate::core::domain::ArxAddress;
use crate::core::spatial::Point3D;

/// Semantic and spatial context of the worker's current location.
#[derive(Clone, Debug)]
pub struct LocationContext {
    /// Semantic prefix representing the active zone (e.g., /building/hq/floor-1/room-101).
    pub current_address: ArxAddress,
    /// Absolute 3D coordinates in the local frame.
    pub coordinates: Point3D,
    /// Confidence of current location context (0.0 to 1.0).
    pub confidence: f64,
}

/// Abstract provider for active client positioning.
pub trait LocationProvider {
    /// Polls or triggers localization via local signals (BLE, SSID, or visual markers).
    fn poll_location(&self) -> Result<LocationContext, String>;
}

/// Mock location provider supporting simulated environment configurations.
pub struct MockLocationProvider {
    pub simulated_address: String,
    pub simulated_coords: Point3D,
}

impl MockLocationProvider {
    pub fn new(address: &str, x: f64, y: f64, z: f64) -> Self {
        Self {
            simulated_address: address.to_string(),
            simulated_coords: Point3D::new(x, y, z),
        }
    }
}

impl LocationProvider for MockLocationProvider {
    fn poll_location(&self) -> Result<LocationContext, String> {
        let addr = ArxAddress::from_path(&self.simulated_address)
            .map_err(|e| format!("Invalid simulated address: {:?}", e))?;

        Ok(LocationContext {
            current_address: addr,
            coordinates: self.simulated_coords,
            confidence: 0.98,
        })
    }
}

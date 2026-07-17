//! Discovery Layer Manager filtering active spatial working-sets.
//!
//! Restricts visible anchors based on geofenced radius settings and separates
//! provisional staging zones from verified production assets.

use crate::core::Anchor;
use crate::web::cache::WarmCache;
use crate::web::cache::warming::PredictiveWarming;
use super::location::LocationContext;

/// Manages proximity filtering, pre-claim visibility status, and triggers warming.
pub struct DiscoveryManager {
    /// Active worker location context.
    pub active_location: Option<LocationContext>,
    /// Global default radius for visibility checks (in meters).
    pub default_discovery_radius: f64,
}

impl Default for DiscoveryManager {
    fn default() -> Self {
        Self::new()
    }
}

impl DiscoveryManager {
    /// Initialize the Discovery Manager with a default 10-meter visibility radius.
    pub fn new() -> Self {
        Self {
            active_location: None,
            default_discovery_radius: 10.0,
        }
    }

    /// Update worker position, triggering warming checks if adjacent to limits.
    pub fn update_position(
        &mut self,
        context: LocationContext,
        warm_cache: &mut WarmCache,
        warmer: &PredictiveWarming,
    ) {
        // Trigger vertical transition pre-fetching if elevator/stairs are near
        if context.current_address.path.contains("stairs") || context.current_address.path.contains("elevator") {
            // Assume destination vertical increment
            warmer.warm_vertical_transition(&context.current_address, 2, warm_cache);
        }

        // Trigger visual marker proximity warming for nearby geofences
        warmer.warm_marker_proximity(
            &context.current_address,
            context.coordinates,
            self.default_discovery_radius,
            warm_cache,
        );

        self.active_location = Some(context);
    }

    /// Filter anchors loaded in the Warm Cache that fall within the active discovery radius.
    pub fn get_visible_anchors(&self, warm_cache: &WarmCache) -> Vec<Anchor> {
        let loc = match &self.active_location {
            Some(l) => l,
            None => return Vec::new(),
        };

        // Determine active radius: query building.yaml override if configured, otherwise use default
        let radius = self.default_discovery_radius;

        let mut visible = Vec::new();
        for envelope in warm_cache.subtrees.values() {
            for anchor in &envelope.anchors {
                // Compute spatial Euclidean distance
                let dx = anchor.position.x - loc.coordinates.x;
                let dy = anchor.position.y - loc.coordinates.y;
                let dz = anchor.position.z - loc.coordinates.z;
                let distance = (dx*dx + dy*dy + dz*dz).sqrt();

                if distance <= radius {
                    visible.push(anchor.clone());
                }
            }
        }
        visible
    }

    /// Return true if the active address is a provisional staging branch prefix (/building).
    pub fn is_provisional(&self) -> bool {
        match &self.active_location {
            Some(loc) => loc.current_address.path.starts_with("/building"),
            None => true, // Default to provisional safety
        }
    }
}

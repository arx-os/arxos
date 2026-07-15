//! In-memory Hot Cache for real-time CPU/GPU spatial tracking loop.
//!
//! Designed for fast queries at 30-60Hz during active AR visual tracking.
//! Strictly bound by WASM heap constraints (~256MB).

use crate::core::Anchor;
use crate::core::spatial::BoundingBox3D;
use std::collections::HashMap;

/// In-memory cache holding active AR trackers, room bounds, and relative transform matrices.
pub struct HotCache {
    /// Active re-localization anchors in the immediate tracking field.
    pub active_anchors: HashMap<String, Anchor>,
    /// Active room UUID the worker is physically standing in.
    pub current_room_id: Option<String>,
    /// Bounding box geometry of the active room.
    pub current_room_bounds: Option<BoundingBox3D>,
    /// System diagnostics tracking memory allocation footprint (estimation).
    pub estimated_memory_bytes: usize,
}

impl HotCache {
    /// Initialize an empty Hot Cache.
    pub fn new() -> Self {
        Self {
            active_anchors: HashMap::new(),
            current_room_id: None,
            current_room_bounds: None,
            estimated_memory_bytes: 0,
        }
    }

    /// Clear the tracking loop memory to release WASM heap space.
    pub fn clear(&mut self) {
        self.active_anchors.clear();
        self.current_room_id = None;
        self.current_room_bounds = None;
        self.estimated_memory_bytes = 0;
    }

    /// Load the tracking neighborhood of anchors into the Hot Cache.
    pub fn load_neighborhood(&mut self, anchors: Vec<Anchor>, room_id: Option<String>, bounds: Option<BoundingBox3D>) {
        self.clear();
        self.current_room_id = room_id;
        self.current_room_bounds = bounds;

        let mut bytes = 0;
        for anchor in anchors {
            // Memory footprint approximation
            bytes += std::mem::size_of::<Anchor>();
            bytes += anchor.id.len() + anchor.name.len();
            bytes += anchor.relative_poses.len() * std::mem::size_of::<crate::core::RelativePose>();
            self.active_anchors.insert(anchor.id.clone(), anchor);
        }

        if self.current_room_bounds.is_some() {
            bytes += std::mem::size_of::<BoundingBox3D>();
        }
        self.estimated_memory_bytes = bytes;
    }

    /// Retrieve an anchor by its ID from the hot memory cache.
    pub fn get_anchor(&self, id: &str) -> Option<&Anchor> {
        self.active_anchors.get(id)
    }

    /// Verify if the hot cache memory footprint satisfies Leptos WASM heap limits.
    pub fn is_memory_within_limits(&self) -> bool {
        // Target execution heap budget is 256MB. We allocate max 10MB to hot anchors/geometry.
        self.estimated_memory_bytes < 10 * 1024 * 1024
    }
}

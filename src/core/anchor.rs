//! Anchor data structure and implementation
//!
//! Anchors represent physical or digital reference points dropped by field workers via AR/PWA.
//! They support recalibration over time, data saturation analysis, and relative poses to other anchors or geometry.

use super::domain::ArxAddress;
use super::types::Position;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Type of reference/target for a relative pose.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum PoseType {
    /// Relative pose to another Anchor.
    AnchorToAnchor,
    /// Relative pose to an Equipment item.
    AnchorToEquipment,
    /// Relative pose to a Room boundary or geometry.
    AnchorToRoom,
    /// Relative pose to an arbitrary 3D point.
    AnchorToPoint,
}

/// Relative pose (transform) to another Anchor or geometrical reference point.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RelativePose {
    /// ID or address of the target entity.
    pub target_id: String,
    /// Type of reference target.
    pub pose_type: PoseType,
    /// Relative translation along X axis (in meters).
    pub x: f64,
    /// Relative translation along Y axis (in meters).
    pub y: f64,
    /// Relative translation along Z axis (in meters).
    pub z: f64,
    /// Roll angle (in radians).
    pub roll: f64,
    /// Pitch angle (in radians).
    pub pitch: f64,
    /// Yaw angle (in radians).
    pub yaw: f64,
}

use std::fmt;
use std::str::FromStr;

/// Reference to an external SLAM or visual feature map.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MapRef {
    /// Git LFS referenced path (stored as lfs://...).
    GitLfs { path: String },
    /// IPFS content-addressed reference (stored as ipfs://...).
    Ipfs { cid: String },
    /// Arweave transaction ID reference (stored as arweave://...).
    Arweave { tx_id: String },
    /// Local file path reference (stored as local://...).
    Local { path: String },
}

impl fmt::Display for MapRef {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MapRef::GitLfs { path } => write!(f, "lfs://{}", path),
            MapRef::Ipfs { cid } => write!(f, "ipfs://{}", cid),
            MapRef::Arweave { tx_id } => write!(f, "arweave://{}", tx_id),
            MapRef::Local { path } => write!(f, "local://{}", path),
        }
    }
}

impl FromStr for MapRef {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if let Some(path) = s.strip_prefix("lfs://") {
            Ok(MapRef::GitLfs { path: path.to_string() })
        } else if let Some(cid) = s.strip_prefix("ipfs://") {
            Ok(MapRef::Ipfs { cid: cid.to_string() })
        } else if let Some(tx_id) = s.strip_prefix("arweave://") {
            Ok(MapRef::Arweave { tx_id: tx_id.to_string() })
        } else if let Some(path) = s.strip_prefix("local://") {
            Ok(MapRef::Local { path: path.to_string() })
        } else {
            Err(format!(
                "Invalid map_ref prefix in '{}'. Must start with lfs://, ipfs://, arweave://, or local://",
                s
            ))
        }
    }
}

impl serde::Serialize for MapRef {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        serializer.serialize_str(&self.to_string())
    }
}

impl<'de> serde::Deserialize<'de> for MapRef {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        MapRef::from_str(&s).map_err(serde::de::Error::custom)
    }
}

/// Represents an AR or spatial anchor dropped in a building.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Anchor {
    /// Unique identifier for the anchor.
    pub id: String,
    /// Human-readable name.
    pub name: String,
    /// Hierarchical address.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub address: Option<ArxAddress>,
    /// 3D spatial position in the local or global coordinate system.
    pub position: Position,
    /// Number of times this anchor has been recalibrated.
    #[serde(default)]
    pub recalibration_count: u32,
    /// Last recalibration timestamp.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_recalibrated_at: Option<DateTime<Utc>>,
    /// Confidence score (0.0 to 1.0) representing the alignment precision.
    pub confidence: f64,
    /// Relative poses to other anchors or geometry.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub relative_poses: Vec<RelativePose>,
    /// Key-value properties metadata.
    #[serde(default, with = "crate::utils::sorted_map")]
    pub properties: HashMap<String, String>,
    /// Reference to external SLAM/feature map.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub map_ref: Option<MapRef>,
}

impl Anchor {
    /// Create a new anchor with default values and generated UUID.
    pub fn new(name: String, position: Position, confidence: f64) -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            name,
            address: None,
            position,
            recalibration_count: 0,
            last_recalibrated_at: None,
            confidence,
            relative_poses: Vec::new(),
            properties: HashMap::new(),
            map_ref: None,
        }
    }

    /// Calculate data saturation for the anchor.
    /// Returns a value between 0.0 (no calibration/data) and 1.0 (fully saturated/stable).
    pub fn data_saturation(&self, dependent_count: usize) -> f64 {
        // 40% weight: recalibration count (reaches max at 5 calibrations)
        let calibration_factor = (self.recalibration_count as f64 / 5.0).min(1.0);
        let calibration_score = calibration_factor * 0.4;

        // 40% weight: confidence score
        let confidence_score = self.confidence.clamp(0.0, 1.0) * 0.4;

        // 20% weight: topological significance (number of dependent entities, reaches max at 3)
        let dependent_factor = (dependent_count as f64 / 3.0).min(1.0);
        let dependent_score = dependent_factor * 0.2;

        calibration_score + confidence_score + dependent_score
    }

    /// Helper to check if anchor is considered fully saturated (stable).
    pub fn is_saturated(&self, dependent_count: usize) -> bool {
        self.data_saturation(dependent_count) >= 0.8
    }

    /// Recalibrate the anchor with new position and confidence.
    pub fn recalibrate(&mut self, new_pos: Position, confidence: f64) {
        self.position = new_pos;
        self.confidence = confidence;
        self.recalibration_count += 1;
        self.last_recalibrated_at = Some(Utc::now());
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_anchor_recalibration() {
        let pos1 = Position { x: 1.0, y: 2.0, z: 3.0, coordinate_system: "local".to_string() };
        let pos2 = Position { x: 1.1, y: 1.9, z: 3.0, coordinate_system: "local".to_string() };

        let mut anchor = Anchor::new("Anchor-1".to_string(), pos1.clone(), 0.9);
        assert_eq!(anchor.recalibration_count, 0);
        assert!(anchor.last_recalibrated_at.is_none());

        anchor.recalibrate(pos2.clone(), 0.95);
        assert_eq!(anchor.recalibration_count, 1);
        assert!(anchor.last_recalibrated_at.is_some());
        assert_eq!(anchor.position, pos2);
        assert_eq!(anchor.confidence, 0.95);
    }

    #[test]
    fn test_anchor_data_saturation() {
        let pos = Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "local".to_string() };
        let mut anchor = Anchor::new("Anchor-1".to_string(), pos, 0.5);

        // Saturation score = (recalibration_count/5)*0.4 + (confidence)*0.4 + (dependent_count/3)*0.2
        // Initial: recalibration=0 (factor=0), confidence=0.5 (score=0.2), dependent_count=0 (factor=0) -> saturation = 0.2
        assert_eq!(anchor.data_saturation(0), 0.2);
        assert!(!anchor.is_saturated(0));

        // Add 5 recalibrations and 1.0 confidence, 3 dependent counts
        for _ in 0..5 {
            anchor.recalibrate(Position { x: 0.0, y: 0.0, z: 0.0, coordinate_system: "local".to_string() }, 1.0);
        }
        // Maxed out recalibration (0.4) + Maxed out confidence (0.4) + 3 dependents (0.2) = 1.0
        assert_eq!(anchor.data_saturation(3), 1.0);
        assert!(anchor.is_saturated(3));
    }

    #[test]
    fn test_map_ref_serialization() {
        let refs = vec![
            MapRef::GitLfs { path: "/.arx/anchors/1.map".to_string() },
            MapRef::Ipfs { cid: "bafybeic".to_string() },
            MapRef::Arweave { tx_id: "ar-tx-123".to_string() },
            MapRef::Local { path: "/tmp/map.bin".to_string() },
        ];

        for r in refs {
            let serialized = serde_json::to_string(&r).unwrap();
            let deserialized: MapRef = serde_json::from_str(&serialized).unwrap();
            assert_eq!(r, deserialized);
        }
    }
}

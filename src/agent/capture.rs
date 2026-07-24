//! Camera frame capture ingest (`capture.from_camera` RPC).
//!
//! Clients may send JPEG frames (base64). Agent stores frames under
//! `imports/captures/`, ensures a floor + room on the durable Building, marks the
//! room `proposed`, and finalizes via the shared ingest spine.
//!
//! **Honesty:** frames only — no depth, no mesh, no point cloud. Room geometry is
//! a placeholder so labeling/review can begin. Not LiDAR / RoomPlan / ARKit.

use std::fs;
use std::path::{Path, PathBuf};

use anyhow::{anyhow, bail, Result};
use base64::{engine::general_purpose, Engine as _};
use chrono::Utc;
use serde::Serialize;

use crate::core::{
    mark_proposed, Building, Floor, Room, RoomType, Wing, PROP_REVIEW_STATUS,
};
use crate::ingest::{finalize_ingest, IngestOptions, IngestSource};
use crate::persistence::{load_building_at, save_building_at, BUILDING_YAML};
use crate::utils::path_safety::PathSafety;

/// Max frames accepted in one capture request.
const MAX_FRAMES: usize = 8;
/// Soft cap per decoded JPEG (~4 MiB) to avoid OOM on pilot laptops.
const MAX_FRAME_BYTES: usize = 4 * 1024 * 1024;

#[derive(Debug, Serialize)]
pub struct CaptureFromCameraResult {
    pub building_name: String,
    pub room_name: String,
    pub yaml_path: String,
    pub capture_dir: String,
    pub frame_count: usize,
    pub floors: usize,
    pub rooms: usize,
    pub equipment: usize,
    pub report_summary: Vec<String>,
    /// What this capture actually produced (honest, for UI).
    pub produced: Vec<String>,
    pub validation_ok: bool,
}

/// Accept camera JPEG frames, persist them, and create/merge a proposed room.
pub fn from_camera(
    repo_root: &Path,
    frames_b64: &[String],
    room_name: Option<&str>,
    floor_name: Option<&str>,
) -> Result<CaptureFromCameraResult> {
    if frames_b64.is_empty() {
        bail!("capture.from_camera requires at least one frame in 'frames'");
    }
    if frames_b64.len() > MAX_FRAMES {
        bail!(
            "capture.from_camera accepts at most {} frames (got {})",
            MAX_FRAMES,
            frames_b64.len()
        );
    }

    let stamp = Utc::now().format("%Y%m%d-%H%M%S").to_string();
    let capture_rel = format!("imports/captures/{}", stamp);
    let capture_dir = repo_root.join(&capture_rel);
    fs::create_dir_all(&capture_dir)?;
    PathSafety::validate_path_for_write(&capture_dir.join("frame_01.jpg"))
        .map_err(|e| anyhow!(e))?;

    let mut saved: Vec<PathBuf> = Vec::with_capacity(frames_b64.len());
    for (i, b64) in frames_b64.iter().enumerate() {
        let raw = strip_data_url_prefix(b64);
        let bytes = general_purpose::STANDARD
            .decode(raw)
            .map_err(|e| anyhow!("Frame {} base64 decode failed: {}", i + 1, e))?;
        if bytes.is_empty() {
            bail!("Frame {} is empty after decode", i + 1);
        }
        if bytes.len() > MAX_FRAME_BYTES {
            bail!(
                "Frame {} exceeds {} bytes after decode",
                i + 1,
                MAX_FRAME_BYTES
            );
        }
        let name = format!("frame_{:02}.jpg", i + 1);
        let path = capture_dir.join(&name);
        fs::write(&path, &bytes).map_err(|e| {
            anyhow!(
                "Failed to write frame {} to {}: {}",
                i + 1,
                path.display(),
                e
            )
        })?;
        saved.push(path);
    }

    // Manifest for operators / future vision pipeline
    let manifest = serde_json::json!({
        "source": "client_jpeg_frames",
        "captured_at": Utc::now().to_rfc3339(),
        "frame_count": saved.len(),
        "frames": saved.iter().map(|p| p.file_name().and_then(|s| s.to_str()).unwrap_or("").to_string()).collect::<Vec<_>>(),
        "geometry": "none — JPEG frames only; room is placeholder for labeling",
        "depth": false,
        "point_cloud": false,
        "mesh": false,
        "note": "not LiDAR/RoomPlan/ARKit — evidence frames only",
    });
    fs::write(
        capture_dir.join("manifest.json"),
        serde_json::to_string_pretty(&manifest)?,
    )?;

    let floor = floor_name
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .unwrap_or("Ground Floor")
        .to_string();

    let room = room_name
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .map(|s| s.to_string())
        .unwrap_or_else(|| format!("Room-{}", stamp));

    let mut building = load_or_bootstrap_building(repo_root)?;

    ensure_floor(&mut building, &floor);
    if room_exists(&building, &room) {
        // Unique name if collision
        let alt = format!("{}-{}", room, &stamp[stamp.len().saturating_sub(6)..]);
        add_camera_room(&mut building, &floor, &alt, &capture_rel, saved.len())?;
        return finalize_and_save(
            repo_root,
            building,
            &alt,
            &floor,
            &capture_rel,
            saved.len(),
        );
    }

    add_camera_room(&mut building, &floor, &room, &capture_rel, saved.len())?;
    finalize_and_save(
        repo_root,
        building,
        &room,
        &floor,
        &capture_rel,
        saved.len(),
    )
}

fn strip_data_url_prefix(s: &str) -> &str {
    if let Some(idx) = s.find("base64,") {
        &s[idx + "base64,".len()..]
    } else {
        s.trim()
    }
}

fn load_or_bootstrap_building(repo_root: &Path) -> Result<Building> {
    let yaml = repo_root.join(BUILDING_YAML);
    if yaml.exists() {
        load_building_at(repo_root)
            .map_err(|e| anyhow!("Failed to load {}: {}", BUILDING_YAML, e))
    } else {
        let mut b = Building::new(
            "Camera Capture".into(),
            repo_root
                .file_name()
                .and_then(|s| s.to_str())
                .unwrap_or("capture")
                .to_string(),
        );
        b.add_floor(Floor::new("Ground Floor".into(), 0));
        Ok(b)
    }
}

fn ensure_floor(building: &mut Building, floor_name: &str) {
    if building.floors.iter().any(|f| f.name == floor_name) {
        return;
    }
    let level = building.floors.len() as i32;
    building.add_floor(Floor::new(floor_name.to_string(), level));
}

fn room_exists(building: &Building, name: &str) -> bool {
    building.get_all_rooms().iter().any(|r| r.name == name)
}

fn add_camera_room(
    building: &mut Building,
    floor_name: &str,
    room_name: &str,
    capture_rel: &str,
    frame_count: usize,
) -> Result<()> {
    let floor = building
        .floors
        .iter_mut()
        .find(|f| f.name == floor_name)
        .ok_or_else(|| anyhow!("floor '{}' missing after ensure", floor_name))?;

    if floor.wings.is_empty() {
        floor.add_wing(Wing::new("Main".into()));
    }
    let wing = floor
        .wings
        .first_mut()
        .ok_or_else(|| anyhow!("no wing on floor '{}'", floor_name))?;

    let mut room = Room::new(room_name.to_string(), RoomType::Other("captured".into()));
    mark_proposed(&mut room.properties);
    room.properties
        .insert("capture_source".into(), "camera".into());
    room.properties
        .insert("capture_frames".into(), frame_count.to_string());
    room.properties
        .insert("capture_dir".into(), capture_rel.to_string());
    room.properties.insert(
        "capture_note".into(),
        "JPEG frames only; no depth/mesh; placeholder room for labeling".into(),
    );
    // Ensure review_status key is explicit (mark_proposed already sets it)
    let _ = room.properties.get(PROP_REVIEW_STATUS);

    wing.add_room(room);
    Ok(())
}

fn finalize_and_save(
    repo_root: &Path,
    building: Building,
    room_name: &str,
    floor_name: &str,
    capture_rel: &str,
    frame_count: usize,
) -> Result<CaptureFromCameraResult> {
    let mut result = finalize_ingest(
        building,
        IngestSource::Text,
        IngestOptions {
            validate: true,
            existing: None,
            policy: None,
        },
    );

    result.report.warn(
        "camera_capture",
        format!(
            "Stored {} JPEG frame(s) under {}; created proposed room '{}' (no geometry from camera)",
            frame_count, capture_rel, room_name
        ),
    );
    result.report.warn(
        "camera_capture_limits",
        "Browser capture cannot produce LiDAR/RoomPlan mesh; frames are evidence only until a vision path exists.",
    );

    if result.validation.has_errors() {
        return Err(anyhow!(
            "capture.from_camera validation failed; refusing to write {}: {}",
            BUILDING_YAML,
            result.summary_lines().join("; ")
        ));
    }

    let report_summary = result.summary_lines();
    let building = result.building;
    let floors = building.floors.len();
    let rooms = building.get_all_rooms().len();
    let equipment = building.get_all_equipment().len();
    let name = building.name.clone();

    save_building_at(repo_root, &building)
        .map_err(|e| anyhow!("Failed to write {}: {}", BUILDING_YAML, e))?;

    let produced = vec![
        format!("{} JPEG frame(s) on disk at {}", frame_count, capture_rel),
        "manifest.json (capture metadata)".to_string(),
        format!(
            "proposed room '{}' on floor '{}' (placeholder geometry)",
            room_name, floor_name
        ),
        "building.yaml updated via validate/finalize spine".into(),
        "No depth map, point cloud, or mesh from browser camera".into(),
    ];

    Ok(CaptureFromCameraResult {
        building_name: name,
        room_name: room_name.to_string(),
        yaml_path: BUILDING_YAML.to_string(),
        capture_dir: capture_rel.to_string(),
        frame_count,
        floors,
        rooms,
        equipment,
        report_summary,
        produced,
        validation_ok: true,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{Building, Floor};
    use crate::persistence::save_building_at;
    use crate::yaml::BuildingYamlSerializer;
    use tempfile::tempdir;

    fn tiny_jpeg_b64() -> String {
        // Minimal SOI/EOI-ish bytes (not a JPEG decoder check — storage only)
        general_purpose::STANDARD.encode([0xFFu8, 0xD8, 0xFF, 0xD9, 1, 2, 3, 4])
    }

    fn seed_pilot(dir: &std::path::Path) {
        let mut b = Building::new("Pilot".into(), "/pilot".into());
        b.add_floor(Floor::new("Ground Floor".into(), 0));
        save_building_at(dir, &b).unwrap();
    }

    #[test]
    fn from_camera_creates_proposed_room_and_frames() {
        let dir = tempdir().unwrap();
        seed_pilot(dir.path());

        let frames = vec![tiny_jpeg_b64(), tiny_jpeg_b64()];
        let got = from_camera(dir.path(), &frames, Some("Living Room"), None).unwrap();
        assert_eq!(got.room_name, "Living Room");
        assert_eq!(got.frame_count, 2);
        assert!(got.rooms >= 1);
        assert!(got.validation_ok);
        assert!(!got.produced.is_empty());

        let cap = dir.path().join(&got.capture_dir);
        assert!(cap.join("frame_01.jpg").exists());
        assert!(cap.join("frame_02.jpg").exists());
        assert!(cap.join("manifest.json").exists());

        let loaded = load_building_at(dir.path()).unwrap();
        let room = loaded
            .get_all_rooms()
            .into_iter()
            .find(|r| r.name == "Living Room")
            .expect("room");
        assert_eq!(
            room.properties.get("capture_source").map(String::as_str),
            Some("camera")
        );
        assert_eq!(
            room.properties.get(PROP_REVIEW_STATUS).map(String::as_str),
            Some("proposed")
        );
        assert_eq!(
            room.properties.get("capture_frames").map(String::as_str),
            Some("2")
        );
        assert!(room
            .properties
            .get("capture_dir")
            .is_some_and(|d| d.starts_with("imports/captures/")));
    }

    #[test]
    fn from_camera_yaml_round_trip_preserves_provenance() {
        let dir = tempdir().unwrap();
        seed_pilot(dir.path());

        from_camera(dir.path(), &[tiny_jpeg_b64()], Some("Den"), Some("Ground Floor")).unwrap();

        // Reload via serializer path used by CLI / Git SSOT readers
        let yaml_path = dir.path().join(BUILDING_YAML);
        let yaml = std::fs::read_to_string(&yaml_path).unwrap();
        assert!(yaml.contains("capture_source"));
        assert!(yaml.contains("camera"));
        assert!(yaml.contains("review_status"));
        assert!(yaml.contains("proposed"));
        assert!(yaml.contains("Den"));

        let reloaded = BuildingYamlSerializer::deserialize_building(&yaml)
            .expect("deserialize_building after capture");
        let room = reloaded
            .get_all_rooms()
            .into_iter()
            .find(|r| r.name == "Den")
            .expect("Den after YAML round-trip");
        assert_eq!(
            room.properties.get("capture_source").map(String::as_str),
            Some("camera")
        );
        assert_eq!(
            room.properties.get(PROP_REVIEW_STATUS).map(String::as_str),
            Some("proposed")
        );
    }

    #[test]
    fn from_camera_rejects_empty_frames() {
        let dir = tempdir().unwrap();
        let err = from_camera(dir.path(), &[], None, None).unwrap_err();
        assert!(err.to_string().contains("at least one"));
    }

    #[test]
    fn from_camera_rejects_too_many_frames() {
        let dir = tempdir().unwrap();
        seed_pilot(dir.path());
        let frames: Vec<String> = (0..=MAX_FRAMES).map(|_| tiny_jpeg_b64()).collect();
        let err = from_camera(dir.path(), &frames, None, None).unwrap_err();
        assert!(err.to_string().contains("at most"));
    }

    #[test]
    fn from_camera_rejects_bad_base64() {
        let dir = tempdir().unwrap();
        seed_pilot(dir.path());
        let err = from_camera(dir.path(), &["%%%not-base64%%%".into()], None, None).unwrap_err();
        assert!(err.to_string().to_ascii_lowercase().contains("base64"));
    }

    #[test]
    fn from_camera_rejects_oversized_frame() {
        let dir = tempdir().unwrap();
        seed_pilot(dir.path());
        let big = vec![0u8; MAX_FRAME_BYTES + 1];
        let b64 = general_purpose::STANDARD.encode(&big);
        let err = from_camera(dir.path(), &[b64], None, None).unwrap_err();
        assert!(err.to_string().contains("exceeds"));
    }

    #[test]
    fn from_camera_accepts_data_url_prefix() {
        let dir = tempdir().unwrap();
        seed_pilot(dir.path());
        let raw = tiny_jpeg_b64();
        let data_url = format!("data:image/jpeg;base64,{}", raw);
        let got = from_camera(dir.path(), &[data_url], Some("Kitchen"), None).unwrap();
        assert_eq!(got.room_name, "Kitchen");
        assert_eq!(got.frame_count, 1);
    }

    #[test]
    fn from_camera_renames_on_room_collision() {
        let dir = tempdir().unwrap();
        seed_pilot(dir.path());
        from_camera(dir.path(), &[tiny_jpeg_b64()], Some("Study"), None).unwrap();
        let second = from_camera(dir.path(), &[tiny_jpeg_b64()], Some("Study"), None).unwrap();
        assert_ne!(second.room_name, "Study");
        assert!(second.room_name.starts_with("Study-"));
        let loaded = load_building_at(dir.path()).unwrap();
        let names: Vec<_> = loaded
            .get_all_rooms()
            .into_iter()
            .map(|r| r.name.clone())
            .collect();
        assert!(names.iter().any(|n| n == "Study"));
        assert!(names.iter().any(|n| n.starts_with("Study-") && n != "Study"));
    }

    #[test]
    fn from_camera_bootstraps_when_no_yaml() {
        let dir = tempdir().unwrap();
        // No building.yaml — should still create proposed room + SSOT
        let got = from_camera(dir.path(), &[tiny_jpeg_b64()], Some("Office"), None).unwrap();
        assert_eq!(got.room_name, "Office");
        assert!(dir.path().join(BUILDING_YAML).exists());
        let loaded = load_building_at(dir.path()).unwrap();
        assert!(loaded.get_all_rooms().iter().any(|r| r.name == "Office"));
    }

    #[test]
    fn from_camera_default_room_name_uses_timestamp_prefix() {
        let dir = tempdir().unwrap();
        seed_pilot(dir.path());
        let got = from_camera(dir.path(), &[tiny_jpeg_b64()], None, None).unwrap();
        assert!(
            got.room_name.starts_with("Room-"),
            "expected Room-… default, got {}",
            got.room_name
        );
    }
}

//! Structured field RPCs (`field.label`, `field.accept_room`).
//!
//! Builds quoted text DSL server-side and applies via the same spine as `edit.apply`.
//! Prefer these over free-form `edit.apply` scripts from peripheral clients.

use std::path::Path;

use anyhow::{anyhow, Result};
use serde::Serialize;
use serde_json::Value;

use crate::agent::edit::{apply_edit, EditApplyResult};
use crate::ingest::{
    accept_room_script, create_room_and_label_script, label_equipment_script,
    mark_equipment_proposed_script,
};

/// Protocol version advertised by `session.hello` (additive within v1).
pub const PROTOCOL_VERSION: u32 = 1;

#[derive(Debug, Serialize)]
pub struct SessionHello {
    pub protocol_version: u32,
    pub role: &'static str,
    pub transports: Vec<&'static str>,
    pub field_methods: Vec<&'static str>,
    pub notes: Vec<&'static str>,
}

pub fn session_hello() -> SessionHello {
    SessionHello {
        protocol_version: PROTOCOL_VERSION,
        role: "capture_node_agent",
        transports: vec!["http_rpc", "websocket"],
        field_methods: vec![
            "session.hello",
            "building.get",
            "building.validate",
            "lidar.import",
            "field.label",
            "field.accept_room",
            "edit.apply",
            "git.status",
            "git.commit",
            "ifc.export",
        ],
        notes: vec![
            "Prefer field.label / field.accept_room over free-form edit.apply from mobile clients",
            "HTTP POST /rpc is supported and recommended for request/response lab clients",
            "WebSocket /ws remains available for streaming clients",
            "Capture path A: file LiDAR via lidar.import (no in-app RoomPlan required)",
        ],
    }
}

/// Label equipment as proposed; create proposed room if missing.
pub fn field_label(repo_root: &Path, params: &Value) -> Result<EditApplyResult> {
    let room = params
        .get("room")
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow!("field.label requires string 'room'"))?;
    let equipment = params
        .get("equipment")
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow!("field.label requires string 'equipment'"))?;

    // Optional override; default electrical for field switch/panel labels.
    let _eq_type = params
        .get("equipment_type")
        .and_then(|v| v.as_str())
        .unwrap_or("electrical");

    let script = label_equipment_script(room, equipment)?;
    match apply_edit(repo_root, &script) {
        Ok(r) => Ok(r),
        Err(e) => {
            let msg = e.to_string();
            if is_room_not_found(&msg) {
                let create = create_room_and_label_script(room, equipment)?;
                apply_edit(repo_root, &create)
            } else if is_already_exists(&msg) {
                let stamp = mark_equipment_proposed_script(equipment)?;
                apply_edit(repo_root, &stamp)
            } else {
                Err(e)
            }
        }
    }
}

pub fn field_accept_room(repo_root: &Path, params: &Value) -> Result<EditApplyResult> {
    let room = params
        .get("room")
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow!("field.accept_room requires string 'room'"))?;
    let script = accept_room_script(room)?;
    apply_edit(repo_root, &script)
}

fn is_room_not_found(message: &str) -> bool {
    let m = message.to_ascii_lowercase();
    m.contains("room") && (m.contains("not found") || m.contains("does not exist"))
}

fn is_already_exists(message: &str) -> bool {
    message.to_ascii_lowercase().contains("already")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::{Building, Floor};
    use crate::persistence::save_building_at;
    use serde_json::json;
    use tempfile::tempdir;

    #[test]
    fn field_label_creates_room_when_missing() {
        let dir = tempdir().unwrap();
        let mut b = Building::new("Field Lab".into(), "/field".into());
        b.add_floor(Floor::new("Ground Floor".into(), 0));
        save_building_at(dir.path(), &b).unwrap();

        let got = field_label(
            dir.path(),
            &json!({"room": "Room 1", "equipment": "Light Switch"}),
        )
        .unwrap();
        assert!(got.rooms >= 1);
        assert!(got.equipment >= 1);
        assert!(got.applied >= 2);
    }

    #[test]
    fn field_accept_room_sets_status() {
        let dir = tempdir().unwrap();
        let mut b = Building::new("Field Lab".into(), "/field".into());
        b.add_floor(Floor::new("Ground Floor".into(), 0));
        save_building_at(dir.path(), &b).unwrap();
        field_label(
            dir.path(),
            &json!({"room": "Lab", "equipment": "panel-1"}),
        )
        .unwrap();
        let got = field_accept_room(dir.path(), &json!({"room": "Lab"})).unwrap();
        assert!(got.applied >= 1);
    }
}

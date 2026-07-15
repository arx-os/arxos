use std::path::PathBuf;
use std::sync::{Arc, Mutex};

use anyhow::Result;
use serde_json::Value;

use crate::agent::auth::{ensure_capability, TokenState};
use crate::agent::protocol::{
    JsonRpcError, JsonRpcRequest, JsonRpcResponse, AUTH_ERROR, INTERNAL_ERROR, INVALID_PARAMS,
    METHOD_NOT_FOUND,
};
use crate::agent::{building, collab, files, git, ifc};

pub struct AgentState {
    pub repo_root: PathBuf,
    pub token: Arc<Mutex<TokenState>>,
}

pub async fn dispatch(state: Arc<AgentState>, request: JsonRpcRequest) -> JsonRpcResponse {
    let id = request.id.clone();
    let method = request.method.as_str();
    let params = request.params.unwrap_or(Value::Null);

    // 1. Check capabilities
    let capabilities = {
        let token_guard = state.token.lock().unwrap();
        token_guard.capabilities().to_vec()
    };

    if let Err(e) = ensure_capability(method, &capabilities) {
        return JsonRpcResponse::error(id, AUTH_ERROR, format!("Permission denied: {}", e), None);
    }

    // 2. Dispatch to handler
    let result = match method {
        "git.status" => handle_git_status(&state.repo_root),
        "git.diff" => handle_git_diff(&state.repo_root, params),
        "git.commit" => handle_git_commit(&state, params),
        "files.read" => handle_files_read(&state.repo_root, params),
        "building.get" => handle_building_get(&state.repo_root),
        "ifc.import" => handle_ifc_import(&state.repo_root, params),
        "ifc.export" => handle_ifc_export(&state.repo_root, params),
        "collab.sync" => handle_collab_sync(params).await,
        "claim.list_pending" => handle_claim_list_pending(&state.repo_root),
        "claim.review" => handle_claim_review(&state.repo_root, params),
        "claim.get_status" => handle_claim_get_status(&state.repo_root, params),
        _ => Err(anyhow::anyhow!("Method not found")),
    };

    match result {
        Ok(value) => JsonRpcResponse::success(id, value),
        Err(e) => {
            let msg = e.to_string();
            if msg == "Method not found" {
                JsonRpcResponse::error(id, METHOD_NOT_FOUND, msg, None)
            } else {
                JsonRpcResponse::error(id, INTERNAL_ERROR, msg, None)
            }
        }
    }
}

fn handle_git_status(root: &std::path::Path) -> Result<Value> {
    let summary = git::status(root)?;
    Ok(serde_json::to_value(summary)?)
}

fn handle_git_diff(root: &std::path::Path, params: Value) -> Result<Value> {
    let commit = params.get("commit").and_then(|v| v.as_str());
    let file = params.get("file").and_then(|v| v.as_str());

    let diff = git::diff(root, commit, file)?;
    Ok(serde_json::to_value(diff)?)
}

fn handle_git_commit(state: &AgentState, params: Value) -> Result<Value> {
    let message = params
        .get("message")
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow::anyhow!("Missing 'message' parameter"))?;

    let stage_all = params
        .get("stageAll")
        .and_then(|v| v.as_bool())
        .unwrap_or(false);

    // Get the DID key from the current token state
    let did_key = {
        let token = state.token.lock().unwrap();
        token.value().to_string()
    };

    let result = git::commit(&state.repo_root, message, stage_all, &did_key)?;
    Ok(serde_json::to_value(result)?)
}

fn handle_files_read(root: &std::path::Path, params: Value) -> Result<Value> {
    let path = params
        .get("path")
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow::anyhow!("Missing 'path' parameter"))?;

    let content = files::read_file(root, path)?;
    Ok(serde_json::to_value(content)?)
}

fn handle_building_get(root: &std::path::Path) -> Result<Value> {
    let result = building::get_building(root)?;
    Ok(serde_json::to_value(result)?)
}

fn handle_ifc_import(root: &std::path::Path, params: Value) -> Result<Value> {
    let filename = params
        .get("filename")
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow::anyhow!("Missing 'filename' parameter"))?;

    let data_base64 = params
        .get("data")
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow::anyhow!("Missing 'data' parameter"))?;

    let result = ifc::import_ifc(root, filename, data_base64)?;
    Ok(serde_json::to_value(result)?)
}

fn handle_ifc_export(root: &std::path::Path, params: Value) -> Result<Value> {
    let filename = params
        .get("filename")
        .and_then(|v| v.as_str())
        .map(|s| s.to_string());
    let delta = params
        .get("delta")
        .and_then(|v| v.as_bool())
        .unwrap_or(false);
    let approved_only = params
        .get("approved_only")
        .and_then(|v| v.as_bool())
        .unwrap_or(false);

    // Edge RPC only — same IFCExporter spine as CLI; delta rejected.
    let result = ifc::export_ifc_with_options(root, filename, delta, approved_only)?;
    Ok(serde_json::to_value(result)?)
}

async fn handle_collab_sync(params: Value) -> Result<Value> {
    let messages_val = params
        .get("messages")
        .ok_or_else(|| anyhow::anyhow!("Missing 'messages' parameter"))?;

    let messages: Vec<collab::CollabMessage> = serde_json::from_value(messages_val.clone())
        .map_err(|e| anyhow::anyhow!("Invalid messages format: {}", e))?;

    let config =
        collab::load_config()?.ok_or_else(|| anyhow::anyhow!("Collaboration config not found"))?;

    let token = collab::github_token()?.unwrap_or_default();

    let outcome = collab::sync_messages(&messages, &config, &token).await?;
    Ok(serde_json::to_value(outcome)?)
}

fn handle_claim_list_pending(root: &std::path::Path) -> Result<Value> {
    use crate::agent::claim::GraceWindowManager;
    use crate::yaml::BuildingYamlSerializer;
    let manager = GraceWindowManager::new();
    let pending = manager.list_pending_contributions(root.to_str().unwrap()).map_err(map_grace_error)?;
    
    let list: Vec<Value> = pending.into_iter().map(|(idx, content)| {
        let (building_id, address, contributor, summary, timestamp) = match BuildingYamlSerializer::deserialize(&content) {
            Ok(data) => {
                let building = data.into_building();
                let building_id = building.id.clone();
                let address = building.address.as_ref().map(|a| a.to_string()).unwrap_or_else(|| building.path.clone());
                let contributor = building.metadata.as_ref()
                    .and_then(|m| m.properties.get("contributor").cloned())
                    .unwrap_or_else(|| "0x7099...3f75".to_string());
                let floors = building.floors.len();
                let rooms = building.get_all_rooms().len();
                let equipment = building.get_all_equipment().len();
                let summary = format!("{} floors, {} rooms, {} equipment", floors, rooms, equipment);
                let timestamp = building.updated_at.timestamp() as u64;
                (building_id, address, contributor, summary, timestamp)
            }
            Err(_) => {
                ("unknown".to_string(), "unknown".to_string(), "unknown".to_string(), "Invalid YAML contribution".to_string(), chrono::Utc::now().timestamp() as u64)
            }
        };

        serde_json::json!({
            "index": idx,
            "building_id": building_id,
            "address": address,
            "contributor": contributor,
            "summary": summary,
            "estimated_reward": "500.0 $AXD",
            "timestamp": timestamp,
            "status": "WaitingForReview",
            "content": content
        })
    }).collect();

    Ok(serde_json::to_value(list)?)
}

fn handle_claim_review(root: &std::path::Path, params: Value) -> Result<Value> {
    use crate::agent::claim::GraceWindowManager;
    
    let building_id = params.get("building_id")
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow::anyhow!("Missing building_id"))?;
    let index = params.get("index")
        .and_then(|v| v.as_u64())
        .ok_or_else(|| anyhow::anyhow!("Missing index"))? as usize;
    let approve = params.get("approve")
        .and_then(|v| v.as_bool())
        .ok_or_else(|| anyhow::anyhow!("Missing approve"))?;
    let owner_address = params.get("owner_address")
        .and_then(|v| v.as_str())
        .unwrap_or("0x1234567890abcdef");
    let live = params.get("live")
        .and_then(|v| v.as_bool())
        .unwrap_or(false);

    let mut manager = GraceWindowManager::new();
    manager.register_active_claim(building_id.to_string(), 14);

    let (state, receipt) = manager.review_pending_contribution(
        root.to_str().unwrap(),
        building_id,
        index,
        approve,
        owner_address,
        live,
    ).map_err(map_grace_error)?;

    Ok(serde_json::json!({
        "status": format!("{:?}", state),
        "receipt": receipt
    }))
}

fn handle_claim_get_status(_root: &std::path::Path, params: Value) -> Result<Value> {
    use crate::agent::claim::GraceWindowManager;
    
    let building_id = params.get("building_id")
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow::anyhow!("Missing building_id"))?;

    let mut manager = GraceWindowManager::new();
    manager.register_active_claim(building_id.to_string(), 14);
    
    let active = manager.is_in_grace_window(building_id);
    
    Ok(serde_json::json!({
        "building_id": building_id,
        "grace_window_active": active,
        "claim_grace_period_days": 14,
        "status": if active { "WaitingForReview" } else { "Expired" }
    }))
}

fn map_grace_error(e: String) -> anyhow::Error {
    anyhow::anyhow!(e)
}

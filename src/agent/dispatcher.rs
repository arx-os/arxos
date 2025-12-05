use std::path::PathBuf;
use std::sync::{Arc, Mutex};

use anyhow::Result;
use serde_json::Value;

use crate::agent::auth::{ensure_capability, TokenState};
use crate::agent::protocol::{
    JsonRpcError, JsonRpcRequest, JsonRpcResponse, AUTH_ERROR, INTERNAL_ERROR, INVALID_PARAMS,
    METHOD_NOT_FOUND,
};
use crate::agent::{collab, files, git, ifc};
use crate::hardware::HardwareManager;

pub struct AgentState {
    pub repo_root: PathBuf,
    pub token: Arc<Mutex<TokenState>>,
    pub hardware: Arc<HardwareManager>,
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
        return JsonRpcResponse::error(
            id,
            AUTH_ERROR,
            format!("Permission denied: {}", e),
            None,
        );
    }

    // 2. Dispatch to handler
    let result = match method {
        "git.status" => handle_git_status(&state.repo_root),
        "git.diff" => handle_git_diff(&state.repo_root, params),
        "git.commit" => handle_git_commit(&state, params),
        "files.read" => handle_files_read(&state.repo_root, params),
        "ifc.import" => handle_ifc_import(&state.repo_root, params),
        "ifc.export" => handle_ifc_export(&state.repo_root, params),
        "collab.sync" => handle_collab_sync(params).await,
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
    let filename = params.get("filename").and_then(|v| v.as_str()).map(|s| s.to_string());
    let delta = params.get("delta").and_then(|v| v.as_bool()).unwrap_or(false);

    let result = ifc::export_ifc(root, filename, delta)?;
    Ok(serde_json::to_value(result)?)
}

async fn handle_collab_sync(params: Value) -> Result<Value> {
    let messages_val = params
        .get("messages")
        .ok_or_else(|| anyhow::anyhow!("Missing 'messages' parameter"))?;
        
    let messages: Vec<collab::CollabMessage> = serde_json::from_value(messages_val.clone())
        .map_err(|e| anyhow::anyhow!("Invalid messages format: {}", e))?;

    let config = collab::load_config()?
        .ok_or_else(|| anyhow::anyhow!("Collaboration config not found"))?;
        
    let token = collab::github_token()?;

    let outcome = collab::sync_messages(&messages, &config, &token).await?;
    Ok(serde_json::to_value(outcome)?)
}

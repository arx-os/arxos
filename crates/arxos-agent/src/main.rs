use std::{
    env,
    net::SocketAddr,
    sync::{Arc, RwLock},
    time::SystemTime,
};

use anyhow::{anyhow, Context};
use axum::{
    extract::{ws::Message, Query, State, WebSocketUpgrade},
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::get,
    Json, Router,
};
use clap::{Parser, ValueEnum};
use futures_util::{SinkExt, StreamExt};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use tracing::{info, warn};

mod auth;
mod collab;
mod files;
mod git;
mod ifc;
mod workspace;

#[derive(Parser, Debug)]
#[command(
    name = "arxos-agent",
    version,
    about = "Local companion agent for the ArxOS PWA"
)]
struct Options {
    /// Hostname or IP address to bind (defaults to loopback)
    #[arg(long, default_value = "127.0.0.1")]
    host: String,

    /// Port to listen on
    #[arg(long, default_value_t = 8787)]
    port: u16,

    /// DID:key token required for authentication
    #[arg(long)]
    token: Option<String>,

    /// Log output format
    #[arg(long, value_enum, default_value = "compact")]
    log_format: LogFormat,
}

#[derive(Clone)]
struct AgentState {
    token_state: Arc<RwLock<auth::TokenState>>,
    default_capabilities: Arc<Vec<String>>,
}

#[derive(Debug, Deserialize)]
struct WsQuery {
    token: Option<String>,
}

#[derive(Debug, Deserialize)]
struct AgentRequest {
    #[serde(default)]
    id: Option<String>,
    action: String,
    #[serde(default)]
    payload: Value,
}

#[derive(Debug, Serialize)]
struct AgentResponse {
    id: Option<String>,
    status: ResponseStatus,
    payload: serde_json::Value,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "lowercase")]
enum ResponseStatus {
    Ok,
    Error,
}

#[derive(Debug, Deserialize)]
struct GitDiffParams {
    #[serde(default)]
    commit: Option<String>,
    #[serde(default)]
    file: Option<String>,
}

#[derive(Debug, Deserialize)]
struct GitCommitParams {
    message: String,
    #[serde(default)]
    stage_all: bool,
}

#[derive(Debug, Deserialize)]
struct FileReadParams {
    path: String,
}

#[derive(Debug, Deserialize)]
struct IfcImportParams {
    filename: String,
    data: String,
}

#[derive(Debug, Deserialize)]
struct IfcExportParams {
    #[serde(default)]
    filename: Option<String>,
    #[serde(default)]
    delta: bool,
}

#[derive(Debug, Deserialize)]
struct AuthRotateParams {
    #[serde(default)]
    capabilities: Option<Vec<String>>,
}

#[derive(Debug, Deserialize)]
struct AuthNegotiateParams {
    #[serde(default)]
    requested: Vec<String>,
}

#[derive(Clone, Debug, ValueEnum)]
enum LogFormat {
    Compact,
    Json,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let options = Options::parse();

    init_tracing(options.log_format.clone());

    let token = options
        .token
        .or_else(|| env::var("ARXOS_AGENT_TOKEN").ok())
        .filter(|value| value.starts_with("did:key:"))
        .unwrap_or_else(|| {
            let generated = auth::generate_did_key();
            warn!(
                "No DID token supplied, generated ephemeral credential: {generated}. \
                Pass --token or ARXOS_AGENT_TOKEN to provide your own."
            );
            generated
        });

    let capabilities = default_capabilities();
    let token_state = Arc::new(RwLock::new(auth::TokenState::new(
        token.clone(),
        capabilities.clone(),
    )));
    let state = Arc::new(AgentState {
        token_state: token_state.clone(),
        default_capabilities: Arc::new(capabilities.clone()),
    });

    let router = Router::new()
        .route("/health", get(health_handler))
        .route("/capabilities", get(capabilities_handler))
        .route("/ws", get(ws_handler))
        .with_state(state.clone());

    let address: SocketAddr = format!("{}:{}", options.host, options.port).parse()?;
    let listener = tokio::net::TcpListener::bind(address)
        .await
        .with_context(|| format!("Failed to bind {address}"))?;

    info!(
        "ArxOS agent listening on ws://{}:{} (token: {})",
        options.host, options.port, token
    );

    axum::serve(
        listener,
        router.into_make_service_with_connect_info::<SocketAddr>(),
    )
    .with_graceful_shutdown(shutdown_signal())
    .await?;

    Ok(())
}

fn init_tracing(format: LogFormat) {
    let env_filter = tracing_subscriber::EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| "arxos_agent=info,axum::rejection=trace".into());

    match format {
        LogFormat::Compact => {
            tracing_subscriber::fmt()
                .with_env_filter(env_filter)
                .with_target(false)
                .compact()
                .init();
        }
        LogFormat::Json => {
            tracing_subscriber::fmt()
                .with_env_filter(env_filter)
                .with_target(false)
                .json()
                .flatten_event(true)
                .init();
        }
    }
}

fn default_capabilities() -> Vec<String> {
    vec![
        "system.health".into(),
        "git.status".into(),
        "git.diff".into(),
        "git.commit".into(),
        "files.read".into(),
        "ifc.import".into(),
        "ifc.export".into(),
        "auth.manage".into(),
        "collab.sync".into(),
        "collab.config".into(),
    ]
}

async fn health_handler() -> impl IntoResponse {
    Json(serde_json::json!({
        "status": "ok",
        "version": env!("CARGO_PKG_VERSION"),
        "timestamp": SystemTime::now().duration_since(SystemTime::UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or_default()
    }))
}

async fn capabilities_handler(State(state): State<Arc<AgentState>>) -> impl IntoResponse {
    let token_snapshot = state.token_state.read().unwrap();
    Json(serde_json::json!({
        "active": token_snapshot.capabilities(),
        "default": state.default_capabilities.as_ref(),
        "version": env!("CARGO_PKG_VERSION"),
        "rotated_at": token_snapshot.last_rotated().to_rfc3339(),
    }))
}

async fn ws_handler(
    ws: WebSocketUpgrade,
    Query(query): Query<WsQuery>,
    State(state): State<Arc<AgentState>>,
    axum::extract::ConnectInfo(addr): axum::extract::ConnectInfo<SocketAddr>,
) -> Response {
    match validate_token(&state, query.token.as_deref()) {
        Ok(()) => ws.on_upgrade(move |socket| async move {
            info!("WebSocket client connected from {}", addr);
            if let Err(error) = handle_socket(socket, state.clone()).await {
                warn!("WebSocket session error: {error:?}");
            }
        }),
        Err(status) => status.into_response(),
    }
}

fn validate_token(state: &AgentState, provided: Option<&str>) -> Result<(), StatusCode> {
    let current = state.token_state.read().unwrap();
    match provided {
        Some(token) if token == current.value() => Ok(()),
        _ => Err(StatusCode::UNAUTHORIZED),
    }
}

async fn handle_socket(
    socket: axum::extract::ws::WebSocket,
    state: Arc<AgentState>,
) -> anyhow::Result<()> {
    let (mut sender, mut receiver) = socket.split();

    let token_snapshot = state.token_state.read().unwrap().clone();
    sender
        .send(Message::Text(serde_json::to_string(&AgentResponse {
            id: None,
            status: ResponseStatus::Ok,
            payload: serde_json::json!({
                "message": "connected",
                "version": env!("CARGO_PKG_VERSION"),
                "capabilities": token_snapshot.capabilities(),
                "rotated_at": token_snapshot.last_rotated().to_rfc3339(),
            }),
        })?))
        .await?;

    while let Some(message) = receiver.next().await {
        match message {
            Ok(Message::Text(text)) => {
                let response = match process_request(state.clone(), text).await {
                    Ok(response) => response,
                    Err(error) => AgentResponse {
                        id: None,
                        status: ResponseStatus::Error,
                        payload: serde_json::json!({ "error": error.to_string() }),
                    },
                };

                sender
                    .send(Message::Text(serde_json::to_string(&response)?))
                    .await?;
            }
            Ok(Message::Close(_)) => {
                info!("Client requested close");
                break;
            }
            Ok(Message::Ping(p)) => {
                sender.send(Message::Pong(p)).await?;
            }
            Ok(_) => { /* ignore binary messages for now */ }
            Err(error) => {
                warn!("WebSocket receive error: {error}");
                break;
            }
        }
    }

    Ok(())
}

async fn process_request(state: Arc<AgentState>, payload: String) -> anyhow::Result<AgentResponse> {
    let request: AgentRequest = serde_json::from_str(&payload)?;
    let token_snapshot = state.token_state.read().unwrap().clone();

    if let Err(error) =
        auth::ensure_capability(request.action.as_str(), token_snapshot.capabilities())
    {
        return Ok(AgentResponse {
            id: request.id,
            status: ResponseStatus::Error,
            payload: serde_json::json!({ "error": error.to_string() }),
        });
    }

    let result = match request.action.as_str() {
        "ping" => Ok(serde_json::json!({
            "pong": true,
            "timestamp": SystemTime::now().duration_since(SystemTime::UNIX_EPOCH)
                .map(|d| d.as_secs()).unwrap_or_default()
        })),
        "version" => Ok(serde_json::json!({
            "agent": env!("CARGO_PKG_VERSION"),
            "capabilities": token_snapshot.capabilities(),
        })),
        "capabilities" => Ok(serde_json::json!({
            "capabilities": token_snapshot.capabilities(),
            "default": state.default_capabilities.as_ref(),
            "rotated_at": token_snapshot.last_rotated().to_rfc3339(),
        })),
        "git.status" => {
            let repo_root = workspace::detect_repo_root()?;
            let status = git::status(&repo_root)?;
            Ok(serde_json::to_value(status)?)
        }
        "git.diff" => {
            let params: GitDiffParams = serde_json::from_value(request.payload.clone())?;
            let repo_root = workspace::detect_repo_root()?;
            let diff = git::diff(&repo_root, params.commit.as_deref(), params.file.as_deref())?;
            Ok(serde_json::to_value(diff)?)
        }
        "git.commit" => {
            let params: GitCommitParams = serde_json::from_value(request.payload.clone())?;
            let repo_root = workspace::detect_repo_root()?;
            let result = git::commit(
                &repo_root,
                &params.message,
                params.stage_all,
                token_snapshot.value(),
            )?;
            Ok(serde_json::to_value(result)?)
        }
        "files.read" => {
            let params: FileReadParams = serde_json::from_value(request.payload.clone())?;
            let repo_root = workspace::detect_repo_root()?;
            let content = files::read_file(&repo_root, &params.path)?;
            Ok(serde_json::to_value(content)?)
        }
        "ifc.import" => {
            let params: IfcImportParams = serde_json::from_value(request.payload.clone())?;
            let repo_root = workspace::detect_repo_root()?;
            let result = ifc::import_ifc(&repo_root, &params.filename, &params.data)?;
            Ok(serde_json::to_value(result)?)
        }
        "ifc.export" => {
            let params: IfcExportParams = serde_json::from_value(request.payload.clone())?;
            let repo_root = workspace::detect_repo_root()?;
            let result = ifc::export_ifc(&repo_root, params.filename, params.delta)?;
            Ok(serde_json::to_value(result)?)
        }
        "collab.config.get" => {
            let config = collab::load_config()?;
            Ok(serde_json::json!({ "config": config }))
        }
        "collab.config.set" => {
            let config: collab::CollabConfig = serde_json::from_value(request.payload.clone())?;
            let stored = collab::save_config(&config)?;
            Ok(serde_json::json!({ "config": stored }))
        }
        "collab.sync" => {
            let params: collab::SyncRequest = serde_json::from_value(request.payload.clone())?;
            let config = collab::load_config()?
                .ok_or_else(|| anyhow!("Collaboration target is not configured"))?;
            let token = collab::github_token()?;
            let outcome = collab::sync_messages(&params.messages, &config, &token).await?;
            Ok(serde_json::to_value(outcome)?)
        }
        "auth.rotate" => {
            let params: AuthRotateParams = serde_json::from_value(request.payload.clone())?;
            let requested = params
                .capabilities
                .unwrap_or_else(|| state.default_capabilities.as_ref().clone());
            let (granted, denied) =
                auth::filter_capabilities(state.default_capabilities.as_ref(), &requested);
            let capabilities = if granted.is_empty() {
                state.default_capabilities.as_ref().clone()
            } else {
                granted.clone()
            };

            let new_token = auth::generate_did_key();
            let rotated_at = {
                let mut guard = state.token_state.write().unwrap();
                guard.rotate(new_token.clone(), capabilities.clone());
                guard.last_rotated()
            };

            info!(
                event = "token_rotated",
                denied = denied.len(),
                "Token rotated"
            );
            Ok(serde_json::json!({
                "token": new_token,
                "capabilities": capabilities,
                "denied": denied,
                "rotated_at": rotated_at.to_rfc3339(),
            }))
        }
        "auth.negotiate" => {
            let params: AuthNegotiateParams = serde_json::from_value(request.payload.clone())?;
            let (granted, denied) =
                auth::filter_capabilities(state.default_capabilities.as_ref(), &params.requested);
            let granted = if params.requested.is_empty() {
                state.default_capabilities.as_ref().clone()
            } else {
                granted
            };

            {
                let mut guard = state.token_state.write().unwrap();
                guard.update_capabilities(granted.clone());
            }

            info!(
                event = "capabilities_negotiated",
                granted = granted.len(),
                denied = denied.len()
            );
            Ok(serde_json::json!({
                "granted": granted,
                "denied": denied,
            }))
        }
        other => Err(anyhow!("Unsupported action: {}", other)),
    };

    match result {
        Ok(payload) => Ok(AgentResponse {
            id: request.id,
            status: ResponseStatus::Ok,
            payload,
        }),
        Err(error) => Ok(AgentResponse {
            id: request.id,
            status: ResponseStatus::Error,
            payload: serde_json::json!({ "error": error.to_string() }),
        }),
    }
}

async fn shutdown_signal() {
    let ctrl_c = async {
        tokio::signal::ctrl_c()
            .await
            .expect("failed to install CTRL+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .expect("failed to install signal handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }

    info!("Shutting down ArxOS agent...");
}

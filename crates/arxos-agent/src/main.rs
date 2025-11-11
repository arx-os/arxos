use std::{env, net::SocketAddr, sync::Arc, time::SystemTime};

use anyhow::Context;
use axum::{
    extract::{ws::Message, Query, State, WebSocketUpgrade},
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::get,
    Json, Router,
};
use clap::Parser;
use futures_util::{SinkExt, StreamExt};
use serde::{Deserialize, Serialize};
use tracing::{info, warn};
use uuid::Uuid;

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
}

#[derive(Clone)]
struct AgentState {
    expected_token: String,
    capabilities: Arc<Vec<String>>,
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
    _payload: serde_json::Value,
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

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let options = Options::parse();

    init_tracing();

    let token = options
        .token
        .or_else(|| env::var("ARXOS_AGENT_TOKEN").ok())
        .filter(|value| value.starts_with("did:key:"))
        .unwrap_or_else(|| {
            let generated = format!("did:key:z{}", Uuid::new_v4().to_string().replace('-', ""));
            warn!(
                "No DID token supplied, generated ephemeral credential: {generated}. \
                Pass --token or ARXOS_AGENT_TOKEN to provide your own."
            );
            generated
        });

    let state = Arc::new(AgentState {
        expected_token: token.clone(),
        capabilities: Arc::new(default_capabilities()),
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

fn init_tracing() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "arxos_agent=info,axum::rejection=trace".into()),
        )
        .with_target(false)
        .compact()
        .init();
}

fn default_capabilities() -> Vec<String> {
    vec![
        "system.health".to_string(),
        "git.status".to_string(),
        "git.commit".to_string(),
        "files.read".to_string(),
        "files.write".to_string(),
        "ifc.diff".to_string(),
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
    Json(serde_json::json!({
        "capabilities": state.capabilities.as_ref(),
        "version": env!("CARGO_PKG_VERSION")
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
    match provided {
        Some(token) if token == state.expected_token => Ok(()),
        _ => Err(StatusCode::UNAUTHORIZED),
    }
}

async fn handle_socket(
    socket: axum::extract::ws::WebSocket,
    state: Arc<AgentState>,
) -> anyhow::Result<()> {
    let (mut sender, mut receiver) = socket.split();
    let state_clone = state.clone();

    // Send greeting
    sender
        .send(Message::Text(serde_json::to_string(&AgentResponse {
            id: None,
            status: ResponseStatus::Ok,
            payload: serde_json::json!({
                "message": "connected",
                "version": env!("CARGO_PKG_VERSION"),
                "capabilities": state_clone.capabilities.as_ref()
            }),
        })?))
        .await?;

    while let Some(message) = receiver.next().await {
        match message {
            Ok(Message::Text(text)) => {
                let response =
                    process_request(&state, text).unwrap_or_else(|error| AgentResponse {
                        id: None,
                        status: ResponseStatus::Error,
                        payload: serde_json::json!({ "error": error.to_string() }),
                    });
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

fn process_request(state: &AgentState, payload: String) -> Result<AgentResponse, anyhow::Error> {
    let request: AgentRequest = serde_json::from_str(&payload)?;
    let response_payload = match request.action.as_str() {
        "ping" => serde_json::json!({
            "pong": true,
            "timestamp": SystemTime::now().duration_since(SystemTime::UNIX_EPOCH)
                .map(|d| d.as_secs()).unwrap_or_default()
        }),
        "version" => serde_json::json!({
            "agent": env!("CARGO_PKG_VERSION"),
            "capabilities": state.capabilities.as_ref(),
        }),
        "capabilities" => serde_json::json!({
            "capabilities": state.capabilities.as_ref(),
        }),
        other => {
            return Ok(AgentResponse {
                id: request.id,
                status: ResponseStatus::Error,
                payload: serde_json::json!({
                    "error": format!("Unsupported action: {}", other)
                }),
            });
        }
    };

    Ok(AgentResponse {
        id: request.id,
        status: ResponseStatus::Ok,
        payload: response_payload,
    })
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

//! WebSocket server implementation

#[cfg(feature = "agent")]
use std::{
    net::SocketAddr,
    sync::{Arc, Mutex, atomic::Ordering},
};

#[cfg(feature = "agent")]
#[cfg(feature = "agent")]
use crate::agent::{
    auth::{generate_did_key, TokenState},
    dispatcher::{dispatch, AgentState},
    protocol::{JsonRpcRequest, JsonRpcResponse, PARSE_ERROR},
    workspace::detect_repo_root,
};
#[cfg(feature = "agent")]
use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        Query, State,
    },
    http::{HeaderMap, StatusCode},
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
#[cfg(feature = "agent")]
use serde::Deserialize;

#[cfg(feature = "agent")]
#[derive(Deserialize)]
pub struct AuthParams {
    pub token: Option<String>,
}

#[cfg(feature = "agent")]
pub async fn start_agent() -> Result<(), Box<dyn std::error::Error>> {
    // A. Setup structured logging
    let filter = tracing_subscriber::EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info"));
    let (filter_layer, reload_handle) = tracing_subscriber::reload::Layer::new(filter);

    let use_json = std::env::var("LOG_FORMAT")
        .map(|v| v.to_lowercase() == "json")
        .unwrap_or(false);

    use tracing_subscriber::prelude::*;
    if use_json {
        let _ = tracing_subscriber::registry()
            .with(filter_layer)
            .with(tracing_subscriber::fmt::layer().json())
            .try_init();
    } else {
        let _ = tracing_subscriber::registry()
            .with(filter_layer)
            .with(tracing_subscriber::fmt::layer())
            .try_init();
    }

    tracing::info!("🤖 ArxOS Agent starting...");

    // 1. Detect Repository Root
    let repo_root = detect_repo_root()?;
    tracing::info!(repo_root = %repo_root.display(), "Detected repository root");

    // 2. Generate Root Token
    let root_token = generate_did_key();
    let all_capabilities = vec![
        "git.status".to_string(),
        "git.diff".to_string(),
        "git.commit".to_string(),
        "files.read".to_string(),
        "building.get".to_string(),
        "ifc.import".to_string(),
        "ifc.export".to_string(),
        "collab.sync".to_string(),
        "auth.manage".to_string(),
    ];

    let token_state = TokenState::new(root_token.clone(), all_capabilities);
    let metrics = Arc::new(crate::agent::observability::AgentMetrics::new());
    let state = Arc::new(AgentState {
        repo_root: repo_root.clone(),
        token: Arc::new(Mutex::new(token_state)),
        metrics: metrics.clone(),
        reload_handle: Some(reload_handle.clone()),
    });

    // Spawn log watcher
    crate::agent::observability::spawn_log_level_watcher(repo_root.clone(), reload_handle);

    println!("\n🔑 ROOT TOKEN: {}\n", root_token);
    tracing::info!("⚠️  Keep this token secret! You will need it to connect.");
    tracing::info!("ℹ️  Hardware/BACnet drivers not included in this build (revisit later).");

    // 3. Setup Router
    let app = Router::new()
        .route("/ws", get(ws_handler))
        .route("/rpc", post(rpc_handler))
        .route("/api/status", get(http_agent_status))
        .route("/api/claims/status", get(http_claims_status))
        .route("/metrics", get(http_prometheus_metrics))
        .route("/api/claims/staging", get(http_claims_staging))
        .route("/api/claims/:id/approve", post(http_claim_approve))
        .route("/api/claims/:id/reject", post(http_claim_reject))
        .with_state(state.clone());

    // 4. Start File Watchers
    let export_state = state.clone();
    tokio::spawn(async move {
        if let Err(e) = run_auto_export_watcher(export_state).await {
            eprintln!("❌ Auto-export watcher error: {}", e);
        }
    });

    let import_state = state.clone();
    tokio::spawn(async move {
        if let Err(e) = run_auto_import_watcher(import_state).await {
            eprintln!("❌ Auto-import watcher error: {}", e);
        }
    });

    // 5. Start P2P Local Discovery
    crate::agent::discovery::start_discovery(root_token.clone(), 8787);

    // 6. Start WebSocket Server
    let port: u16 = 8787;
    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    println!("📡 Server listening on http://{}", addr);
    print_iphone_connect_hints(&root_token, port);
    println!(
        "ℹ️  Agent is edge bridging only (WebSocket/SSH). \
         Official IFC export for pilots: `arx export --format ifc`."
    );
    println!(
        "🔍 Auto-export convenience: watching for YAML changes (full export, not official)...\n"
    );

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}

/// Field-facing connect card for iPhone PWA on the same LAN/hotspot (Batch A P0.2).
#[cfg(feature = "agent")]
fn print_iphone_connect_hints(token: &str, port: u16) {
    let ips = guess_lan_ips();
    println!("┌─────────────────────────────────────────────────────────────");
    println!("│ iPhone / PWA connect (same Wi-Fi or personal hotspot)");
    println!("│ 1) Serve PWA over http:// (not https) so ws:// is allowed");
    println!("│ 2) In PWA header set Agent host to laptop LAN IP:{port}");
    if ips.is_empty() {
        println!("│    (could not auto-detect LAN IP — run: ipconfig getifaddr en0");
        println!("│     or: hostname -I / ip -4 addr)");
        println!("│    Example host field: 192.168.1.20:{port}");
    } else {
        for ip in &ips {
            println!("│    Agent host: {ip}:{port}");
            println!("│    WebSocket:  ws://{ip}:{port}/ws?token=<token>");
        }
    }
    println!("│ 3) Paste ROOT TOKEN into PWA Agent token field");
    println!("│ 4) Tap Connect → header should show ● Online");
    println!("│ Token (copy once): {token}");
    println!("│ Docs: docs/iphone-field-loop.md");
    println!("└─────────────────────────────────────────────────────────────");
}

/// Best-effort default-route IPv4 for field hints (no extra deps).
#[cfg(feature = "agent")]
fn guess_lan_ips() -> Vec<String> {
    let mut out = Vec::new();
    if let Ok(socket) = std::net::UdpSocket::bind("0.0.0.0:0") {
        // Does not send traffic; used only to discover the egress interface address.
        if socket.connect("8.8.8.8:80").is_ok() {
            if let Ok(addr) = socket.local_addr() {
                let ip = addr.ip();
                if !ip.is_loopback() {
                    out.push(ip.to_string());
                }
            }
        }
    }
    out
}

#[cfg(feature = "agent")]
fn check_auth(headers: &HeaderMap, query_token: Option<&str>, state: &AgentState) -> bool {
    let token_str = if let Some(bearer) = headers
        .get("Authorization")
        .and_then(|h| h.to_str().ok())
        .and_then(|s| s.strip_prefix("Bearer "))
    {
        Some(bearer.to_string())
    } else {
        query_token.map(|s| s.to_string())
    };

    if let Some(token) = token_str {
        let guard = state.token.lock().unwrap();
        guard.value() == token
    } else {
        false
    }
}

#[cfg(feature = "agent")]
#[derive(Deserialize)]
pub struct HttpClaimReviewRequest {
    pub owner_address: String,
    pub live: Option<bool>,
}

#[cfg(feature = "agent")]
#[derive(serde::Serialize)]
struct ClaimStagingDto {
    index: usize,
    building_id: String,
    address: String,
    contributor: String,
    summary: String,
    estimated_reward: String,
    timestamp: u64,
    status: String,
    content: String,
}

#[cfg(feature = "agent")]
pub async fn http_claims_staging(
    headers: HeaderMap,
    Query(params): Query<AuthParams>,
    State(state): State<Arc<AgentState>>,
) -> impl IntoResponse {
    if !check_auth(&headers, params.token.as_deref(), &state) {
        return (StatusCode::UNAUTHORIZED, "Unauthorized").into_response();
    }

    use crate::agent::claim::GraceWindowManager;
    use crate::yaml::BuildingYamlSerializer;

    let manager = GraceWindowManager::new();
    let repo_str = match state.repo_root.to_str() {
        Some(s) => s,
        None => return (StatusCode::INTERNAL_SERVER_ERROR, "Invalid repo path").into_response(),
    };

    let pending = match manager.list_pending_contributions(repo_str) {
        Ok(p) => p,
        Err(e) => return (StatusCode::INTERNAL_SERVER_ERROR, e).into_response(),
    };

    let mut dtos = Vec::new();
    for (idx, content) in pending {
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

        dtos.push(ClaimStagingDto {
            index: idx,
            building_id,
            address,
            contributor,
            summary,
            estimated_reward: "500.0 $AXD".to_string(),
            timestamp,
            status: "WaitingForReview".to_string(),
            content,
        });
    }

    Json(dtos).into_response()
}

#[cfg(feature = "agent")]
pub async fn http_claim_approve(
    headers: HeaderMap,
    Query(params): Query<AuthParams>,
    axum::extract::Path(id): axum::extract::Path<usize>,
    State(state): State<Arc<AgentState>>,
    Json(body): Json<HttpClaimReviewRequest>,
) -> impl IntoResponse {
    if !check_auth(&headers, params.token.as_deref(), &state) {
        state.metrics.record_error();
        return (StatusCode::UNAUTHORIZED, "Unauthorized").into_response();
    }

    use crate::agent::claim::GraceWindowManager;
    let mut manager = GraceWindowManager::new();

    let repo_str = match state.repo_root.to_str() {
        Some(s) => s,
        None => {
            state.metrics.record_error();
            return (StatusCode::INTERNAL_SERVER_ERROR, "Invalid repo path").into_response();
        }
    };
    let building = match crate::persistence::load_building_at(&state.repo_root) {
        Ok(b) => b,
        Err(e) => {
            state.metrics.record_error();
            return (StatusCode::INTERNAL_SERVER_ERROR, format!("Failed to load building: {}", e)).into_response();
        }
    };
    let building_id = building.id.clone();

    manager.register_active_claim(building_id.clone(), 14);

    let live_mode = body.live.unwrap_or(false);

    match manager.review_pending_contribution(
        repo_str,
        &building_id,
        id,
        true, // Approve
        &body.owner_address,
        live_mode,
    ) {
        Ok((claim_state, receipt)) => {
            state.metrics.record_claim_processed(true, 500.0);
            Json(serde_json::json!({
                "status": format!("{:?}", claim_state),
                "receipt": receipt
            })).into_response()
        }
        Err(e) => {
            state.metrics.record_error();
            (StatusCode::BAD_REQUEST, e).into_response()
        }
    }
}

#[cfg(feature = "agent")]
pub async fn http_claim_reject(
    headers: HeaderMap,
    Query(params): Query<AuthParams>,
    axum::extract::Path(id): axum::extract::Path<usize>,
    State(state): State<Arc<AgentState>>,
) -> impl IntoResponse {
    if !check_auth(&headers, params.token.as_deref(), &state) {
        state.metrics.record_error();
        return (StatusCode::UNAUTHORIZED, "Unauthorized").into_response();
    }

    use crate::agent::claim::GraceWindowManager;
    let mut manager = GraceWindowManager::new();

    let repo_str = match state.repo_root.to_str() {
        Some(s) => s,
        None => {
            state.metrics.record_error();
            return (StatusCode::INTERNAL_SERVER_ERROR, "Invalid repo path").into_response();
        }
    };
    let building = match crate::persistence::load_building_at(&state.repo_root) {
        Ok(b) => b,
        Err(e) => {
            state.metrics.record_error();
            return (StatusCode::INTERNAL_SERVER_ERROR, format!("Failed to load building: {}", e)).into_response();
        }
    };
    let building_id = building.id.clone();

    manager.register_active_claim(building_id.clone(), 14);

    match manager.review_pending_contribution(
        repo_str,
        &building_id,
        id,
        false, // Reject
        "0x0000000000000000000000000000000000000000",
        false,
    ) {
        Ok((claim_state, receipt)) => {
            state.metrics.record_claim_processed(false, 0.0);
            Json(serde_json::json!({
                "status": format!("{:?}", claim_state),
                "receipt": receipt
            })).into_response()
        }
        Err(e) => {
            state.metrics.record_error();
            (StatusCode::BAD_REQUEST, e).into_response()
        }
    }
}

#[cfg(feature = "agent")]
async fn ws_handler(
    ws: WebSocketUpgrade,
    headers: HeaderMap,
    Query(params): Query<AuthParams>,
    State(state): State<Arc<AgentState>>,
) -> impl IntoResponse {
    if !check_auth(&headers, params.token.as_deref(), &state) {
        return (
            StatusCode::UNAUTHORIZED,
            "Unauthorized: Invalid or missing token",
        )
            .into_response();
    }

    ws.on_upgrade(|socket| handle_socket(socket, state))
}

#[cfg(feature = "agent")]
async fn rpc_handler(
    headers: HeaderMap,
    Query(params): Query<AuthParams>,
    State(state): State<Arc<AgentState>>,
    Json(request): Json<JsonRpcRequest>,
) -> impl IntoResponse {
    if !check_auth(&headers, params.token.as_deref(), &state) {
        return (
            StatusCode::UNAUTHORIZED,
            "Unauthorized: Invalid or missing token",
        )
            .into_response();
    }

    let response = dispatch(state, request).await;
    Json(response).into_response()
}

#[cfg(feature = "agent")]
async fn handle_socket(mut socket: WebSocket, state: Arc<AgentState>) {
    struct WsGuard(Arc<AgentState>);
    impl Drop for WsGuard {
        fn drop(&mut self) {
            self.0.metrics.active_ws_clients.fetch_sub(1, Ordering::SeqCst);
            tracing::info!(active = self.0.metrics.active_ws_clients.load(Ordering::SeqCst), "WebSocket client disconnected");
        }
    }
    state.metrics.active_ws_clients.fetch_add(1, Ordering::SeqCst);
    let _guard = WsGuard(state.clone());
    tracing::info!(active = state.metrics.active_ws_clients.load(Ordering::SeqCst), "WebSocket client connected");

    while let Some(msg) = socket.recv().await {
        let msg = match msg {
            Ok(msg) => msg,
            Err(e) => {
                tracing::error!(error = %e, "WebSocket socket error");
                return;
            }
        };

        match msg {
            Message::Text(text) => {
                // Parse JSON-RPC Request
                let response = match serde_json::from_str::<JsonRpcRequest>(&text) {
                    Ok(request) => dispatch(state.clone(), request).await,
                    Err(e) => JsonRpcResponse::error(
                        None,
                        PARSE_ERROR,
                        format!("Invalid JSON: {}", e),
                        None,
                    ),
                };

                // Send Response
                if let Ok(resp_text) = serde_json::to_string(&response) {
                    if let Err(e) = socket.send(Message::Text(resp_text)).await {
                        tracing::error!(error = %e, "Failed to send WebSocket response");
                        return;
                    }
                }
            }
            Message::Close(_) => {
                return;
            }
            _ => {}
        }
    }
}

#[cfg(feature = "agent")]
#[derive(serde::Serialize)]
struct AgentStatusDto {
    status: String,
    uptime_seconds: u64,
    active_ws_clients: usize,
    cache_stats: CacheStatsDto,
}

#[cfg(feature = "agent")]
#[derive(serde::Serialize)]
struct CacheStatsDto {
    warm_cache_size: usize,
}

#[cfg(feature = "agent")]
pub async fn http_agent_status(
    headers: HeaderMap,
    Query(params): Query<AuthParams>,
    State(state): State<Arc<AgentState>>,
) -> impl IntoResponse {
    if !check_auth(&headers, params.token.as_deref(), &state) {
        state.metrics.record_error();
        return (StatusCode::UNAUTHORIZED, "Unauthorized").into_response();
    }

    let uptime = state.metrics.start_time.elapsed().as_secs();
    let cache_size = 0; // Static placeholder or simple count of active connections

    let status = AgentStatusDto {
        status: "healthy".to_string(),
        uptime_seconds: uptime,
        active_ws_clients: state.metrics.active_ws_clients.load(Ordering::SeqCst),
        cache_stats: CacheStatsDto {
            warm_cache_size: cache_size,
        },
    };

    Json(status).into_response()
}

#[cfg(feature = "agent")]
#[derive(serde::Serialize)]
struct ClaimsStatusDto {
    claims_processed: usize,
    claims_approved: usize,
    claims_rejected: usize,
    rewards_distributed_axd: f64,
}

#[cfg(feature = "agent")]
pub async fn http_claims_status(
    headers: HeaderMap,
    Query(params): Query<AuthParams>,
    State(state): State<Arc<AgentState>>,
) -> impl IntoResponse {
    if !check_auth(&headers, params.token.as_deref(), &state) {
        state.metrics.record_error();
        return (StatusCode::UNAUTHORIZED, "Unauthorized").into_response();
    }

    let axd = if let Ok(val) = state.metrics.rewards_distributed_axd.lock() {
        *val
    } else {
        0.0
    };

    let status = ClaimsStatusDto {
        claims_processed: state.metrics.claims_processed.load(Ordering::SeqCst),
        claims_approved: state.metrics.claims_approved.load(Ordering::SeqCst),
        claims_rejected: state.metrics.claims_rejected.load(Ordering::SeqCst),
        rewards_distributed_axd: axd,
    };

    Json(status).into_response()
}

#[cfg(feature = "agent")]
pub async fn http_prometheus_metrics(
    headers: HeaderMap,
    Query(params): Query<AuthParams>,
    State(state): State<Arc<AgentState>>,
) -> impl IntoResponse {
    if !check_auth(&headers, params.token.as_deref(), &state) {
        state.metrics.record_error();
        return (StatusCode::UNAUTHORIZED, "Unauthorized").into_response();
    }

    let axd = if let Ok(val) = state.metrics.rewards_distributed_axd.lock() {
        *val
    } else {
        0.0
    };

    let uptime = state.metrics.start_time.elapsed().as_secs();

    let metrics_text = format!(
        "# HELP arx_agent_uptime_seconds The uptime of the ArxOS agent in seconds.\n\
         # TYPE arx_agent_uptime_seconds gauge\n\
         arx_agent_uptime_seconds {}\n\
         # HELP arx_agent_active_ws_clients The number of active WebSocket client connections.\n\
         # TYPE arx_agent_active_ws_clients gauge\n\
         arx_agent_active_ws_clients {}\n\
         # HELP arx_agent_claims_processed_total The total number of staging claims processed.\n\
         # TYPE arx_agent_claims_processed_total counter\n\
         arx_agent_claims_processed_total {}\n\
         # HELP arx_agent_claims_approved_total The total number of staging claims approved.\n\
         # TYPE arx_agent_claims_approved_total counter\n\
         arx_agent_claims_approved_total {}\n\
         # HELP arx_agent_claims_rejected_total The total number of staging claims rejected.\n\
         # TYPE arx_agent_claims_rejected_total counter\n\
         arx_agent_claims_rejected_total {}\n\
         # HELP arx_agent_rewards_distributed_axd_total The total AXD token rewards distributed by the agent.\n\
         # TYPE arx_agent_rewards_distributed_axd_total counter\n\
         arx_agent_rewards_distributed_axd_total {:.2}\n\
         # HELP arx_agent_errors_total The total number of errors encountered by the agent.\n\
         # TYPE arx_agent_errors_total counter\n\
         arx_agent_errors_total {}\n",
        uptime,
        state.metrics.active_ws_clients.load(Ordering::SeqCst),
        state.metrics.claims_processed.load(Ordering::SeqCst),
        state.metrics.claims_approved.load(Ordering::SeqCst),
        state.metrics.claims_rejected.load(Ordering::SeqCst),
        axd,
        state.metrics.errors_encountered.load(Ordering::SeqCst)
    );

    (
        [(axum::http::header::CONTENT_TYPE, "text/plain; version=0.0.4")],
        metrics_text
    ).into_response()
}

#[cfg(feature = "agent")]
async fn run_auto_export_watcher(state: Arc<AgentState>) -> Result<(), Box<dyn std::error::Error>> {
    use std::time::Duration;

    let watcher = crate::agent::watcher::FileWatcher::new(
        &state.repo_root,
        vec!["yaml".to_string(), "yml".to_string()],
    )?;
    println!("👀 Watching {} for YAML changes", state.repo_root.display());

    loop {
        // Check for changes every 500ms
        tokio::time::sleep(Duration::from_millis(500)).await;

        if let Some(changed_path) = watcher.check_for_changes() {
            println!("📝 Detected change: {}", changed_path.display());
            println!(
                "🔄 Auto-exporting IFC (full export via export::ifc; convenience only — \
                 official pilot handoffs use `arx export --format ifc`)..."
            );

            // delta=false: same spine as CLI; no alternate delta semantics.
            match crate::agent::ifc::export_ifc(&state.repo_root, None, false) {
                Ok(result) => {
                    println!(
                        "✅ Auto-export complete: {} ({} bytes)",
                        result.filename, result.size_bytes
                    );
                }
                Err(e) => {
                    eprintln!("❌ Auto-export failed: {}", e);
                }
            }
        }
    }
}

#[cfg(feature = "agent")]
async fn run_auto_import_watcher(state: Arc<AgentState>) -> Result<(), Box<dyn std::error::Error>> {
    use std::time::Duration;

    let watcher =
        crate::agent::watcher::FileWatcher::new(&state.repo_root, vec!["ifc".to_string()])?;
    println!(
        "👀 Watching {} for new IFC files",
        state.repo_root.display()
    );

    loop {
        tokio::time::sleep(Duration::from_millis(1000)).await;

        if let Some(changed_path) = watcher.check_for_changes() {
            println!("🏗️  Detected new/modified IFC: {}", changed_path.display());
            println!("🔄 Auto-importing using native engine...");

            match crate::agent::ifc::import_ifc_local(&state.repo_root, &changed_path) {
                Ok(result) => {
                    println!(
                        "✅ Auto-import complete: {} ({} floors, {} equipment)",
                        result.building_name, result.floors, result.equipment
                    );
                }
                Err(e) => {
                    eprintln!("❌ Auto-import failed: {}", e);
                }
            }
        }
    }
}

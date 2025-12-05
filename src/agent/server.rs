//! WebSocket server implementation

#[cfg(feature = "agent")]
use std::{net::SocketAddr, sync::{Arc, Mutex}};

#[cfg(feature = "agent")]
use axum::{
    extract::{
        ws::{Message, WebSocket, WebSocketUpgrade},
        State, Query,
    },
    http::{StatusCode, HeaderMap},
    response::IntoResponse,
    routing::get,
    Router,
};
#[cfg(feature = "agent")]
use serde::Deserialize;
#[cfg(feature = "agent")]


#[cfg(feature = "agent")]
use crate::agent::{
    auth::{generate_did_key, TokenState},
    dispatcher::{dispatch, AgentState},
    protocol::{JsonRpcRequest, PARSE_ERROR, JsonRpcResponse},
    workspace::detect_repo_root,
};

#[cfg(feature = "agent")]
#[derive(Deserialize)]
struct AuthParams {
    token: Option<String>,
}

#[cfg(feature = "agent")]
pub async fn start_agent() -> Result<(), Box<dyn std::error::Error>> {
    println!("🤖 ArxOS Agent starting...");

    // 1. Detect Repository Root
    let repo_root = detect_repo_root()?;
    println!("📂 Repository Root: {}", repo_root.display());

    // 2. Generate Root Token
    let root_token = generate_did_key();
    let all_capabilities = vec![
        "git.status".to_string(),
        "git.diff".to_string(),
        "git.commit".to_string(),
        "files.read".to_string(),
        "ifc.import".to_string(),
        "ifc.export".to_string(),
        "collab.sync".to_string(),
        "auth.manage".to_string(),
    ];
    
    let token_state = TokenState::new(root_token.clone(), all_capabilities);
    let state = Arc::new(AgentState {
        repo_root,
        token: Arc::new(Mutex::new(token_state)),
    });

    println!("\\n🔑 ROOT TOKEN: {}\\n", root_token);
    println!("⚠️  Keep this token secret! You will need it to connect.");

    // 3. Setup Router
    let app = Router::new()
        .route("/ws", get(ws_handler))
        .with_state(state.clone());

    // 4. Start File Watcher for Auto-Export
    let watcher_state = state.clone();
    tokio::spawn(async move {
        if let Err(e) = run_auto_export_watcher(watcher_state).await {
            eprintln!("❌ File watcher error: {}", e);
        }
    });

    // 5. Start WebSocket Server
    let addr = SocketAddr::from(([127, 0, 0, 1], 8787));
    println!("📡 WebSocket server listening on ws://{}", addr);
    println!("🔍 Auto-export enabled: watching for YAML changes...\\n");

    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}

#[cfg(feature = "agent")]
async fn ws_handler(
    ws: WebSocketUpgrade,
    headers: HeaderMap,
    Query(params): Query<AuthParams>,
    State(state): State<Arc<AgentState>>,
) -> impl IntoResponse {
    // Extract token from Header (Bearer) or Query Param
    let token_str = if let Some(bearer) = headers
        .get("Authorization")
        .and_then(|h| h.to_str().ok())
        .and_then(|s| s.strip_prefix("Bearer ")) 
    {
        Some(bearer.to_string())
    } else {
        params.token
    };

    // Validate Token
    let valid = if let Some(token) = token_str {
        let guard = state.token.lock().unwrap();
        guard.value() == token
    } else {
        false
    };

    if !valid {
        return (StatusCode::UNAUTHORIZED, "Unauthorized: Invalid or missing token").into_response();
    }

    ws.on_upgrade(|socket| handle_socket(socket, state))
}

#[cfg(feature = "agent")]
async fn handle_socket(mut socket: WebSocket, state: Arc<AgentState>) {
    while let Some(msg) = socket.recv().await {
        let msg = match msg {
            Ok(msg) => msg,
            Err(e) => {
                eprintln!("Socket error: {}", e);
                return;
            }
        };

        match msg {
            Message::Text(text) => {
                // Parse JSON-RPC Request
                let response = match serde_json::from_str::<JsonRpcRequest>(&text) {
                    Ok(request) => {
                        dispatch(state.clone(), request).await
                    }
                    Err(e) => {
                        JsonRpcResponse::error(
                            None, 
                            PARSE_ERROR, 
                            format!("Invalid JSON: {}", e), 
                            None
                        )
                    }
                };

                // Send Response
                if let Ok(resp_text) = serde_json::to_string(&response) {
                    if let Err(e) = socket.send(Message::Text(resp_text)).await {
                        eprintln!("Failed to send response: {}", e);
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
async fn run_auto_export_watcher(state: Arc<AgentState>) -> Result<(), Box<dyn std::error::Error>> {
    use crate::agent::{watcher::FileWatcher, ifc};
    use std::time::Duration;

    let watcher = FileWatcher::new(&state.repo_root)?;
    println!("👀 Watching {} for YAML changes", state.repo_root.display());

    loop {
        // Check for changes every 500ms
        tokio::time::sleep(Duration::from_millis(500)).await;

        if let Some(changed_path) = watcher.check_for_changes() {
            println!("📝 Detected change: {}", changed_path.display());
            println!("🔄 Auto-exporting IFC (delta mode)...");

            match ifc::export_ifc(&state.repo_root, None, true) {
                Ok(result) => {
                    println!("✅ Auto-export complete: {} ({} bytes)", result.filename, result.size_bytes);
                }
                Err(e) => {
                    eprintln!("❌ Auto-export failed: {}", e);
                }
            }
        }
    }
}
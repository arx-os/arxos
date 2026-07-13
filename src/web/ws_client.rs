//! Browser WebSocket client for the local ArxOS agent (feature `web`).
//!
//! Host defaults to `127.0.0.1:8787` for laptop-local use. For iPhone on the same
//! Wi-Fi/hotspot, set host to the laptop LAN address (e.g. `192.168.1.20:8787`).

use futures::channel::oneshot;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::cell::RefCell;
use std::collections::HashMap;
use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast;
use web_sys::{ErrorEvent, MessageEvent, WebSocket};

const STORAGE_TOKEN: &str = "agent_token";
const STORAGE_HOST: &str = "agent_host";
const DEFAULT_HOST: &str = "127.0.0.1:8787";

// JSON-RPC Request structure
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct JsonRpcRequest {
    pub jsonrpc: String,
    pub method: String,
    pub params: Option<Value>,
    pub id: Option<Value>,
}

// JSON-RPC Response structure
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct JsonRpcResponse {
    pub jsonrpc: String,
    pub result: Option<Value>,
    pub error: Option<JsonRpcError>,
    pub id: Option<Value>,
}

// JSON-RPC Error structure
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct JsonRpcError {
    pub code: i32,
    pub message: String,
    pub data: Option<Value>,
}

thread_local! {
    static WS_CONNECTION: RefCell<Option<WebSocket>> = RefCell::new(None);
    static PENDING_RESPONSES: RefCell<HashMap<String, oneshot::Sender<Result<Value, String>>>> = RefCell::new(HashMap::new());
    static REQUEST_ID_COUNTER: RefCell<u64> = RefCell::new(0);
    /// Last successful connect host (session); also mirrored in localStorage.
    static LAST_HOST: RefCell<String> = RefCell::new(DEFAULT_HOST.to_string());
    static LAST_ERROR: RefCell<Option<String>> = RefCell::new(None);
}

fn with_local_storage<F, R>(f: F) -> Option<R>
where
    F: FnOnce(web_sys::Storage) -> R,
{
    let window = web_sys::window()?;
    let storage = window.local_storage().ok().flatten()?;
    Some(f(storage))
}

/// Retrieve the saved DID token from browser's local storage
pub fn get_saved_token() -> Option<String> {
    with_local_storage(|storage| storage.get_item(STORAGE_TOKEN).ok().flatten()).flatten()
}

/// Saved agent host (`host:port`), defaulting to loopback for laptop-local PWA.
pub fn get_saved_agent_host() -> String {
    with_local_storage(|storage| storage.get_item(STORAGE_HOST).ok().flatten())
        .flatten()
        .filter(|s| !s.trim().is_empty())
        .unwrap_or_else(|| DEFAULT_HOST.to_string())
}

/// Persist agent host for next session.
pub fn save_agent_host(host: &str) {
    let normalized = normalize_agent_host(host);
    LAST_HOST.with(|h| *h.borrow_mut() = normalized.clone());
    let _ = with_local_storage(|storage| storage.set_item(STORAGE_HOST, &normalized));
}

/// Host used for the current/last connection attempt.
pub fn current_agent_host() -> String {
    LAST_HOST.with(|h| {
        let cur = h.borrow().clone();
        if cur.is_empty() {
            get_saved_agent_host()
        } else {
            cur
        }
    })
}

/// Last connection error message (if any).
pub fn last_connection_error() -> Option<String> {
    LAST_ERROR.with(|e| e.borrow().clone())
}

fn set_last_error(msg: Option<String>) {
    LAST_ERROR.with(|e| *e.borrow_mut() = msg);
}

/// Normalize user input to `host:port` (no scheme/path).
///
/// Accepts `192.168.1.5`, `192.168.1.5:8787`, `ws://192.168.1.5:8787/ws`, etc.
pub fn normalize_agent_host(raw: &str) -> String {
    let mut s = raw.trim().to_string();
    if s.is_empty() {
        return DEFAULT_HOST.to_string();
    }
    // Strip scheme
    if let Some(rest) = s.strip_prefix("ws://") {
        s = rest.to_string();
    } else if let Some(rest) = s.strip_prefix("wss://") {
        s = rest.to_string();
    } else if let Some(rest) = s.strip_prefix("http://") {
        s = rest.to_string();
    } else if let Some(rest) = s.strip_prefix("https://") {
        s = rest.to_string();
    }
    // Strip path/query
    if let Some(idx) = s.find('/') {
        s.truncate(idx);
    }
    if let Some(idx) = s.find('?') {
        s.truncate(idx);
    }
    s = s.trim().trim_end_matches('/').to_string();
    if s.is_empty() {
        return DEFAULT_HOST.to_string();
    }
    // Add default port if missing (skip if IPv6 bracket form with port — keep simple for pilot)
    if !s.contains(':') {
        s = format!("{}:8787", s);
    }
    s
}

/// Check if WebSocket is currently connected and open
pub fn is_connected() -> bool {
    WS_CONNECTION.with(|conn| {
        if let Some(ws) = conn.borrow().as_ref() {
            ws.ready_state() == WebSocket::OPEN
        } else {
            false
        }
    })
}

/// Connect using saved host (or default) and the given token.
pub async fn connect_to_agent_async(token: &str) -> Result<(), String> {
    let host = get_saved_agent_host();
    connect_to_agent_at(&host, token).await
}

/// Connect to agent at `host` (`host:port`) with DID token.
pub async fn connect_to_agent_at(host: &str, token: &str) -> Result<(), String> {
    let host = normalize_agent_host(host);
    if token.trim().is_empty() {
        let err = "Agent token is empty".to_string();
        set_last_error(Some(err.clone()));
        return Err(err);
    }

    // Clear any previous connection
    WS_CONNECTION.with(|conn| {
        if let Some(ws) = conn.borrow_mut().take() {
            let _ = ws.close();
        }
    });
    PENDING_RESPONSES.with(|pending| pending.borrow_mut().clear());

    let url = format!("ws://{}/ws?token={}", host, token.trim());
    LAST_HOST.with(|h| *h.borrow_mut() = host.clone());

    let ws = WebSocket::new(&url).map_err(|e| {
        let msg = format!("Failed to create WebSocket to {}: {:?}", host, e);
        set_last_error(Some(msg.clone()));
        msg
    })?;

    let (tx, rx) = oneshot::channel::<Result<(), String>>();
    let mut tx_open = Some(tx);

    let onopen_callback = Closure::wrap(Box::new(move |_| {
        if let Some(tx) = tx_open.take() {
            let _ = tx.send(Ok(()));
        }
    }) as Box<dyn FnMut(JsValue)>);
    ws.set_onopen(Some(onopen_callback.as_ref().unchecked_ref()));
    onopen_callback.forget();

    let (err_tx, err_rx) = oneshot::channel::<Result<(), String>>();
    let mut tx_err = Some(err_tx);

    let onerror_callback = Closure::wrap(Box::new(move |e: ErrorEvent| {
        if let Some(tx) = tx_err.take() {
            let _ = tx.send(Err(format!("WebSocket connection error: {:?}", e)));
        }
    }) as Box<dyn FnMut(ErrorEvent)>);
    ws.set_onerror(Some(onerror_callback.as_ref().unchecked_ref()));
    onerror_callback.forget();

    let onmessage_callback = Closure::wrap(Box::new(move |e: MessageEvent| {
        if let Some(text) = e.data().as_string() {
            if let Ok(response) = serde_json::from_str::<JsonRpcResponse>(&text) {
                if let Some(id_val) = response.id {
                    let id_str = match id_val {
                        Value::String(s) => s,
                        Value::Number(n) => n.to_string(),
                        _ => return,
                    };

                    PENDING_RESPONSES.with(|pending| {
                        if let Some(tx) = pending.borrow_mut().remove(&id_str) {
                            if let Some(error) = response.error {
                                let _ = tx.send(Err(error.message));
                            } else {
                                let result_val = response.result.unwrap_or(Value::Null);
                                let _ = tx.send(Ok(result_val));
                            }
                        }
                    });
                }
            }
        }
    }) as Box<dyn FnMut(MessageEvent)>);
    ws.set_onmessage(Some(onmessage_callback.as_ref().unchecked_ref()));
    onmessage_callback.forget();

    let onclose_callback = Closure::wrap(Box::new(move |_| {
        WS_CONNECTION.with(|conn| *conn.borrow_mut() = None);
        PENDING_RESPONSES.with(|pending| pending.borrow_mut().clear());
    }) as Box<dyn FnMut(JsValue)>);
    ws.set_onclose(Some(onclose_callback.as_ref().unchecked_ref()));
    onclose_callback.forget();

    // Cache the connection
    WS_CONNECTION.with(|conn| *conn.borrow_mut() = Some(ws));

    // Persist host + token
    save_agent_host(&host);
    let _ = with_local_storage(|storage| storage.set_item(STORAGE_TOKEN, token.trim()));

    let result = tokio::select! {
        open_res = rx => {
            match open_res {
                Ok(Ok(())) => Ok(()),
                _ => Err(format!("WebSocket to {} failed to open", host)),
            }
        }
        err_res = err_rx => {
            match err_res {
                Ok(Err(e)) => Err(e),
                _ => Err("Error during connection setup".to_string()),
            }
        }
    };

    match &result {
        Ok(()) => set_last_error(None),
        Err(e) => set_last_error(Some(e.clone())),
    }
    result
}

/// Send a JSON-RPC request to the local agent daemon
pub async fn send_rpc(method: &str, params: Value) -> Result<Value, String> {
    let ws = WS_CONNECTION
        .with(|conn| conn.borrow().clone())
        .ok_or_else(|| "WebSocket is not connected. Connect to the agent first.".to_string())?;

    if ws.ready_state() != WebSocket::OPEN {
        return Err("WebSocket connection is not open. Try reconnecting.".to_string());
    }

    let request_id = REQUEST_ID_COUNTER.with(|counter| {
        let mut val = counter.borrow_mut();
        *val += 1;
        val.to_string()
    });

    let (tx, rx) = oneshot::channel();
    PENDING_RESPONSES.with(|pending| {
        pending.borrow_mut().insert(request_id.clone(), tx);
    });

    let request = JsonRpcRequest {
        jsonrpc: "2.0".to_string(),
        method: method.to_string(),
        params: Some(params),
        id: Some(Value::String(request_id.clone())),
    };

    let serialized = serde_json::to_string(&request)
        .map_err(|e| format!("Failed to serialize request: {}", e))?;

    ws.send_with_str(&serialized).map_err(|e| {
        PENDING_RESPONSES.with(|pending| {
            pending.borrow_mut().remove(&request_id);
        });
        format!("Failed to send message: {:?}", e)
    })?;

    rx.await
        .map_err(|_| "Communication channel closed".to_string())?
}

/// Try to automatically connect using the cached host + token
pub async fn try_auto_connect() -> Result<(), String> {
    if let Some(token) = get_saved_token() {
        let host = get_saved_agent_host();
        connect_to_agent_at(&host, &token).await
    } else {
        Err("No saved agent token found".to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::normalize_agent_host;

    #[test]
    fn normalize_adds_default_port() {
        assert_eq!(normalize_agent_host("192.168.1.5"), "192.168.1.5:8787");
    }

    #[test]
    fn normalize_strips_ws_scheme_and_path() {
        assert_eq!(
            normalize_agent_host("ws://10.0.0.2:8787/ws?token=x"),
            "10.0.0.2:8787"
        );
    }

    #[test]
    fn normalize_empty_is_default() {
        assert_eq!(normalize_agent_host("  "), "127.0.0.1:8787");
    }
}

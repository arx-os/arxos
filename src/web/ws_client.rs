use futures::channel::oneshot;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::cell::RefCell;
use std::collections::HashMap;
use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast;
use web_sys::{ErrorEvent, MessageEvent, WebSocket};

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
}

/// Retrieve the saved DID token from browser's local storage
pub fn get_saved_token() -> Option<String> {
    if let Some(window) = web_sys::window() {
        if let Ok(Some(storage)) = window.local_storage() {
            if let Ok(Some(token)) = storage.get_item("agent_token") {
                return Some(token);
            }
        }
    }
    None
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

/// Connect asynchronously to the local agent daemon
pub async fn connect_to_agent_async(token: &str) -> Result<(), String> {
    // Clear any previous connection
    WS_CONNECTION.with(|conn| {
        if let Some(ws) = conn.borrow_mut().take() {
            let _ = ws.close();
        }
    });
    PENDING_RESPONSES.with(|pending| pending.borrow_mut().clear());

    let url = format!("ws://127.0.0.1:8787/ws?token={}", token);
    let ws = WebSocket::new(&url).map_err(|e| format!("Failed to create WebSocket: {:?}", e))?;

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

    // Save token to localStorage
    if let Some(window) = web_sys::window() {
        if let Ok(Some(storage)) = window.local_storage() {
            let _ = storage.set_item("agent_token", token);
        }
    }

    tokio::select! {
        open_res = rx => {
            match open_res {
                Ok(Ok(())) => Ok(()),
                _ => Err("WebSocket connection failed to open".to_string()),
            }
        }
        err_res = err_rx => {
            match err_res {
                Ok(Err(e)) => Err(e),
                _ => Err("Error during connection setup".to_string()),
            }
        }
    }
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

/// Try to automatically connect using the cached local token
pub async fn try_auto_connect() -> Result<(), String> {
    if let Some(token) = get_saved_token() {
        connect_to_agent_async(&token).await
    } else {
        Err("No saved agent token found".to_string())
    }
}

// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{CustomMenuItem, Menu, Submenu, Manager};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use reqwest;

#[derive(Debug, Serialize, Deserialize)]
struct DrawingSession {
    session_id: String,
    drawing_id: String,
    name: String,
    precision_level: String,
    collaboration_enabled: bool,
}

#[derive(Debug, Serialize, Deserialize)]
struct CreateSessionRequest {
    name: String,
    precision_level: Option<String>,
    collaboration_enabled: bool,
}

#[tauri::command]
async fn create_drawing_session(request: CreateSessionRequest) -> Result<DrawingSession, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .post("http://localhost:8000/api/v1/svgx/session/create")
        .json(&request)
        .send()
        .await
        .map_err(|e| format!("Failed to create session: {}", e))?;
    
    let session: DrawingSession = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    
    Ok(session)
}

#[tauri::command]
async fn join_drawing_session(session_id: String, client_id: String) -> Result<DrawingSession, String> {
    let client = reqwest::Client::new();
    
    let request = serde_json::json!({
        "session_id": session_id,
        "client_id": client_id
    });
    
    let response = client
        .post("http://localhost:8000/api/v1/svgx/session/join")
        .json(&request)
        .send()
        .await
        .map_err(|e| format!("Failed to join session: {}", e))?;
    
    let session: DrawingSession = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    
    Ok(session)
}

#[tauri::command]
async fn save_svgx_file(path: String, content: String) -> Result<(), String> {
    fs::write(&path, content)
        .map_err(|e| format!("Failed to save file: {}", e))?;
    Ok(())
}

#[tauri::command]
async fn load_svgx_file(path: String) -> Result<String, String> {
    fs::read_to_string(&path)
        .map_err(|e| format!("Failed to load file: {}", e))
}

#[tauri::command]
async fn export_drawing_session(session_id: String, format: String) -> Result<String, String> {
    let client = reqwest::Client::new();
    
    let request = serde_json::json!({
        "format": format
    });
    
    let response = client
        .post(format!("http://localhost:8000/api/v1/svgx/session/{}/export", session_id))
        .json(&request)
        .send()
        .await
        .map_err(|e| format!("Failed to export session: {}", e))?;
    
    let result: serde_json::Value = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    
    Ok(result["file_url"].as_str().unwrap_or("").to_string())
}

#[tauri::command]
async fn get_session_info(session_id: String) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .get(format!("http://localhost:8000/api/v1/svgx/session/{}/info", session_id))
        .send()
        .await
        .map_err(|e| format!("Failed to get session info: {}", e))?;
    
    let result: serde_json::Value = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    
    Ok(result)
}

#[tauri::command]
async fn check_svgx_engine_health() -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();
    
    let response = client
        .get("http://localhost:8000/api/v1/svgx/health")
        .send()
        .await
        .map_err(|e| format!("Failed to check SVGX Engine health: {}", e))?;
    
    let result: serde_json::Value = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    
    Ok(result)
}

fn main() {
    let quit = CustomMenuItem::new("quit".to_string(), "Quit");
    let close = CustomMenuItem::new("close".to_string(), "Close");
    let file_menu = Submenu::new("File", Menu::new().add_item(quit).add_item(close));
    let menu = Menu::new().add_submenu(file_menu);

    tauri::Builder::default()
        .menu(menu)
        .invoke_handler(tauri::generate_handler![
            create_drawing_session,
            join_drawing_session,
            save_svgx_file,
            load_svgx_file,
            export_drawing_session,
            get_session_info,
            check_svgx_engine_health
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
} 
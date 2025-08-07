// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

// Project data structure
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ProjectData {
    pub id: String,
    pub name: String,
    pub description: String,
    pub created_at: String,
    pub last_modified: String,
    pub objects: Vec<serde_json::Value>,
    pub constraints: Vec<serde_json::Value>,
    pub settings: HashMap<String, serde_json::Value>,
}

mod commands {
    use super::*;

    /// Read file from native file system
    #[tauri::command]
    pub async fn read_file(path: String) -> Result<String, String> {
        match tokio::fs::read_to_string(&path).await {
            Ok(content) => Ok(content),
            Err(e) => Err(format!("Failed to read file: {}", e)),
        }
    }

    /// Write file to native file system
    #[tauri::command]
    pub async fn write_file(path: String, content: String) -> Result<(), String> {
        match tokio::fs::write(&path, content).await {
            Ok(_) => Ok(()),
            Err(e) => Err(format!("Failed to write file: {}", e)),
        }
    }

    /// Get system information
    #[tauri::command]
    pub async fn get_system_info() -> Result<HashMap<String, String>, String> {
        let mut info = HashMap::new();

        info.insert("platform".to_string(), std::env::consts::OS.to_string());
        info.insert("arch".to_string(), std::env::consts::ARCH.to_string());
        info.insert("app_version".to_string(), env!("CARGO_PKG_VERSION").to_string());

        Ok(info)
    }
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            commands::read_file,
            commands::write_file,
            commands::get_system_info
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

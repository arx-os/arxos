// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use std::collections::HashMap;
use tauri::{Manager, Window};
use tokio::fs as tokio_fs;
use notify::{Watcher, RecursiveMode, watcher};
use std::sync::mpsc;
use std::time::Duration;

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

// File operation results
#[derive(Debug, Serialize, Deserialize)]
pub struct FileOperationResult {
    pub success: bool,
    pub message: String,
    pub data: Option<String>,
}

// Export formats
#[derive(Debug, Serialize, Deserialize)]
pub enum ExportFormat {
    DXF,
    IFC,
    PDF,
    SVG,
    GLTF,
}

/// Read file from native file system
#[tauri::command]
pub async fn read_file(path: String) -> Result<String, String> {
    match tokio_fs::read_to_string(&path).await {
        Ok(content) => Ok(content),
        Err(e) => Err(format!("Failed to read file: {}", e)),
    }
}

/// Write file to native file system
#[tauri::command]
pub async fn write_file(path: String, content: String) -> Result<(), String> {
    // Create directory if it doesn't exist
    if let Some(parent) = Path::new(&path).parent() {
        if !parent.exists() {
            tokio_fs::create_dir_all(parent).await
                .map_err(|e| format!("Failed to create directory: {}", e))?;
        }
    }
    
    match tokio_fs::write(&path, content).await {
        Ok(_) => Ok(()),
        Err(e) => Err(format!("Failed to write file: {}", e)),
    }
}

/// Watch file for changes
#[tauri::command]
pub async fn watch_file(path: String, window: Window) -> Result<(), String> {
    let (tx, rx) = mpsc::channel();
    
    let mut watcher = watcher(tx, notify::Config::default())
        .map_err(|e| format!("Failed to create file watcher: {}", e))?;
    
    watcher.watch(&path, RecursiveMode::NonRecursive)
        .map_err(|e| format!("Failed to watch file: {}", e))?;
    
    // Spawn watcher in background
    std::thread::spawn(move || {
        for res in rx {
            match res {
                Ok(_) => {
                    // Emit file changed event to frontend
                    let _ = window.emit("file-changed", "File changed externally");
                }
                Err(e) => eprintln!("Watch error: {:?}", e),
            }
        }
    });
    
    Ok(())
}

/// Export project to DXF format
#[tauri::command]
pub async fn export_to_dxf(path: String, project_data: ProjectData) -> Result<(), String> {
    let dxf_content = generate_dxf_content(&project_data)?;
    
    match tokio_fs::write(&path, dxf_content).await {
        Ok(_) => Ok(()),
        Err(e) => Err(format!("Failed to export DXF: {}", e)),
    }
}

/// Export project to IFC format
#[tauri::command]
pub async fn export_to_ifc(path: String, project_data: ProjectData) -> Result<(), String> {
    let ifc_content = generate_ifc_content(&project_data)?;
    
    match tokio_fs::write(&path, ifc_content).await {
        Ok(_) => Ok(()),
        Err(e) => Err(format!("Failed to export IFC: {}", e)),
    }
}

/// Export project to PDF format
#[tauri::command]
pub async fn export_to_pdf(path: String, project_data: ProjectData) -> Result<(), String> {
    let pdf_content = generate_pdf_content(&project_data)?;
    
    match tokio_fs::write(&path, pdf_content).await {
        Ok(_) => Ok(()),
        Err(e) => Err(format!("Failed to export PDF: {}", e)),
    }
}

/// Generate DXF content from project data
fn generate_dxf_content(project_data: &ProjectData) -> Result<String, String> {
    let mut dxf_lines = vec![
        "0".to_string(),
        "SECTION".to_string(),
        "2".to_string(),
        "HEADER".to_string(),
        "9".to_string(),
        "$ACADVER".to_string(),
        "1".to_string(),
        "AC1021".to_string(),
        "0".to_string(),
        "ENDSEC".to_string(),
        "0".to_string(),
        "SECTION".to_string(),
        "2".to_string(),
        "ENTITIES".to_string(),
    ];
    
    // Convert project objects to DXF entities
    for object in &project_data.objects {
        if let Some(obj_type) = object.get("type").and_then(|v| v.as_str()) {
            match obj_type {
                "line" => {
                    if let (Some(start), Some(end)) = (
                        object.get("startPoint"),
                        object.get("endPoint")
                    ) {
                        let start_x = start.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let start_y = start.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let end_x = end.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let end_y = end.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        
                        dxf_lines.extend_from_slice(&[
                            "0".to_string(),
                            "LINE".to_string(),
                            "8".to_string(),
                            "0".to_string(),
                            "10".to_string(),
                            format!("{:.6}", start_x),
                            "20".to_string(),
                            format!("{:.6}", start_y),
                            "11".to_string(),
                            format!("{:.6}", end_x),
                            "21".to_string(),
                            format!("{:.6}", end_y),
                        ]);
                    }
                }
                "circle" => {
                    if let (Some(center), Some(radius)) = (
                        object.get("center"),
                        object.get("radius")
                    ) {
                        let center_x = center.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let center_y = center.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let radius_val = radius.as_f64().unwrap_or(1.0);
                        
                        dxf_lines.extend_from_slice(&[
                            "0".to_string(),
                            "CIRCLE".to_string(),
                            "8".to_string(),
                            "0".to_string(),
                            "10".to_string(),
                            format!("{:.6}", center_x),
                            "20".to_string(),
                            format!("{:.6}", center_y),
                            "40".to_string(),
                            format!("{:.6}", radius_val),
                        ]);
                    }
                }
                "rectangle" => {
                    if let (Some(start), Some(end)) = (
                        object.get("startPoint"),
                        object.get("endPoint")
                    ) {
                        let start_x = start.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let start_y = start.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let end_x = end.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let end_y = end.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        
                        // Create rectangle as polyline
                        dxf_lines.extend_from_slice(&[
                            "0".to_string(),
                            "POLYLINE".to_string(),
                            "8".to_string(),
                            "0".to_string(),
                            "66".to_string(),
                            "1".to_string(),
                            "0".to_string(),
                            "VERTEX".to_string(),
                            "8".to_string(),
                            "0".to_string(),
                            "10".to_string(),
                            format!("{:.6}", start_x),
                            "20".to_string(),
                            format!("{:.6}", start_y),
                            "0".to_string(),
                            "VERTEX".to_string(),
                            "8".to_string(),
                            "0".to_string(),
                            "10".to_string(),
                            format!("{:.6}", end_x),
                            "20".to_string(),
                            format!("{:.6}", start_y),
                            "0".to_string(),
                            "VERTEX".to_string(),
                            "8".to_string(),
                            "0".to_string(),
                            "10".to_string(),
                            format!("{:.6}", end_x),
                            "20".to_string(),
                            format!("{:.6}", end_y),
                            "0".to_string(),
                            "VERTEX".to_string(),
                            "8".to_string(),
                            "0".to_string(),
                            "10".to_string(),
                            format!("{:.6}", start_x),
                            "20".to_string(),
                            format!("{:.6}", end_y),
                            "0".to_string(),
                            "SEQEND".to_string(),
                        ]);
                    }
                }
                _ => {
                    // Handle other object types
                    println!("Unsupported object type: {}", obj_type);
                }
            }
        }
    }
    
    dxf_lines.extend_from_slice(&[
        "0".to_string(),
        "ENDSEC".to_string(),
        "0".to_string(),
        "EOF".to_string(),
    ]);
    
    Ok(dxf_lines.join("\n"))
}

/// Generate IFC content from project data
fn generate_ifc_content(project_data: &ProjectData) -> Result<String, String> {
    let mut ifc_lines = vec![
        "ISO-10303-21;".to_string(),
        "HEADER;".to_string(),
        "FILE_DESCRIPTION(('ArxIDE IFC Export'),'2;1');".to_string(),
        "FILE_NAME('{}','{}',('ArxIDE'),('Arxos Team'),'','','');".to_string(),
        "FILE_SCHEMA(('IFC4'));".to_string(),
        "ENDSEC;".to_string(),
        "DATA;".to_string(),
    ];
    
    // Generate IFC entities for each object
    for (index, object) in project_data.objects.iter().enumerate() {
        if let Some(obj_type) = object.get("type").and_then(|v| v.as_str()) {
            match obj_type {
                "line" => {
                    if let (Some(start), Some(end)) = (
                        object.get("startPoint"),
                        object.get("endPoint")
                    ) {
                        let start_x = start.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let start_y = start.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let start_z = start.get("z").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let end_x = end.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let end_y = end.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let end_z = end.get("z").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        
                        let line_id = index + 1;
                        ifc_lines.push(format!("#{} = IFCCARTESIANPOINT(({:.6},{:.6},{:.6}));", line_id * 3 - 2, start_x, start_y, start_z));
                        ifc_lines.push(format!("#{} = IFCCARTESIANPOINT(({:.6},{:.6},{:.6}));", line_id * 3 - 1, end_x, end_y, end_z));
                        ifc_lines.push(format!("#{} = IFCLINE('#{}','#{}');", line_id * 3, line_id * 3 - 2, line_id * 3 - 1));
                    }
                }
                "circle" => {
                    if let (Some(center), Some(radius)) = (
                        object.get("center"),
                        object.get("radius")
                    ) {
                        let center_x = center.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let center_y = center.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let center_z = center.get("z").and_then(|v| v.as_f64()).unwrap_or(0.0);
                        let radius_val = radius.as_f64().unwrap_or(1.0);
                        
                        let circle_id = index + 1;
                        ifc_lines.push(format!("#{} = IFCCARTESIANPOINT(({:.6},{:.6},{:.6}));", circle_id * 3 - 2, center_x, center_y, center_z));
                        ifc_lines.push(format!("#{} = IFCAXIS2PLACEMENT3D('#{}',$,IFCDIRECTION((0.,0.,1.)));", circle_id * 3 - 1, circle_id * 3 - 2));
                        ifc_lines.push(format!("#{} = IFCCIRCLE($,{:.6});", circle_id * 3, radius_val));
                    }
                }
                _ => {
                    // Handle other object types
                    println!("Unsupported object type for IFC: {}", obj_type);
                }
            }
        }
    }
    
    ifc_lines.push("ENDSEC;".to_string());
    ifc_lines.push("END-ISO-10303-21;".to_string());
    
    Ok(ifc_lines.join("\n"))
}

/// Generate PDF content from project data
fn generate_pdf_content(project_data: &ProjectData) -> Result<String, String> {
    // This would integrate with a PDF library like printpdf or lopdf
    // For now, return a simple text representation
    let mut pdf_content = format!(
        "ArxIDE Project: {}\nDescription: {}\nCreated: {}\nLast Modified: {}\n\nObjects: {}\nConstraints: {}\n",
        project_data.name,
        project_data.description,
        project_data.created_at,
        project_data.last_modified,
        project_data.objects.len(),
        project_data.constraints.len()
    );
    
    // Add object details
    for (index, object) in project_data.objects.iter().enumerate() {
        if let Some(obj_type) = object.get("type").and_then(|v| v.as_str()) {
            pdf_content.push_str(&format!("{}. Type: {}\n", index + 1, obj_type));
        }
    }
    
    Ok(pdf_content)
}

/// Get system information
#[tauri::command]
pub async fn get_system_info() -> Result<HashMap<String, String>, String> {
    let mut info = HashMap::new();
    
    info.insert("platform".to_string(), std::env::consts::OS.to_string());
    info.insert("arch".to_string(), std::env::consts::ARCH.to_string());
    info.insert("app_version".to_string(), env!("CARGO_PKG_VERSION").to_string());
    
    // Get available memory
    if let Ok(mem_info) = sysinfo::System::new_all() {
        info.insert("total_memory".to_string(), format!("{} MB", mem_info.total_memory() / 1024 / 1024));
        info.insert("available_memory".to_string(), format!("{} MB", mem_info.available_memory() / 1024 / 1024));
    }
    
    Ok(info)
}

/// Show native system notification
#[tauri::command]
pub async fn show_notification(title: String, body: String) -> Result<(), String> {
    #[cfg(target_os = "macos")]
    {
        use std::process::Command;
        let _ = Command::new("osascript")
            .args(&[
                "-e",
                &format!("display notification \"{}\" with title \"{}\"", body, title)
            ])
            .output();
    }
    
    #[cfg(target_os = "windows")]
    {
        use std::process::Command;
        let _ = Command::new("powershell")
            .args(&[
                "-Command",
                &format!("New-BurntToastNotification -Text \"{}\" -Title \"{}\"", body, title)
            ])
            .output();
    }
    
    #[cfg(target_os = "linux")]
    {
        use std::process::Command;
        let _ = Command::new("notify-send")
            .args(&[&title, &body])
            .output();
    }
    
    Ok(())
}

/// Batch process multiple files
#[tauri::command]
pub async fn batch_process_files(files: Vec<String>, operation: String) -> Result<Vec<String>, String> {
    let mut results = Vec::new();
    
    for file_path in files {
        match operation.as_str() {
            "export_dxf" => {
                // Read SVGX file and export to DXF
                match tokio_fs::read_to_string(&file_path).await {
                    Ok(content) => {
                        if let Ok(project_data) = serde_json::from_str::<ProjectData>(&content) {
                            let output_path = file_path.replace(".svgx", ".dxf");
                            if let Ok(_) = export_to_dxf(output_path.clone(), project_data).await {
                                results.push(format!("Exported {} to DXF", file_path));
                            } else {
                                results.push(format!("Failed to export {} to DXF", file_path));
                            }
                        }
                    }
                    Err(e) => {
                        results.push(format!("Failed to read {}: {}", file_path, e));
                    }
                }
            }
            "export_ifc" => {
                // Read SVGX file and export to IFC
                match tokio_fs::read_to_string(&file_path).await {
                    Ok(content) => {
                        if let Ok(project_data) = serde_json::from_str::<ProjectData>(&content) {
                            let output_path = file_path.replace(".svgx", ".ifc");
                            if let Ok(_) = export_to_ifc(output_path.clone(), project_data).await {
                                results.push(format!("Exported {} to IFC", file_path));
                            } else {
                                results.push(format!("Failed to export {} to IFC", file_path));
                            }
                        }
                    }
                    Err(e) => {
                        results.push(format!("Failed to read {}: {}", file_path, e));
                    }
                }
            }
            _ => {
                results.push(format!("Unknown operation: {}", operation));
            }
        }
    }
    
    Ok(results)
}

/// Get recent files list
#[tauri::command]
pub async fn get_recent_files() -> Result<Vec<String>, String> {
    // This would read from a configuration file or database
    // For now, return an empty list
    Ok(Vec::new())
}

/// Add file to recent files
#[tauri::command]
pub async fn add_recent_file(file_path: String) -> Result<(), String> {
    // This would write to a configuration file or database
    println!("Added to recent files: {}", file_path);
    Ok(())
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            read_file,
            write_file,
            watch_file,
            export_to_dxf,
            export_to_ifc,
            export_to_pdf,
            get_system_info,
            show_notification,
            batch_process_files,
            get_recent_files,
            add_recent_file
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
} 
//! JNI bindings for Android
//!
//! This module provides Java Native Interface (JNI) bindings for Android.

use jni::JNIEnv;
use jni::objects::{JClass, JString};
use jni::sys::{jstring, jboolean};
use std::os::raw::c_char;

use crate::mobile_ffi::{MobileError, RoomInfo, EquipmentInfo};

/// Convert Rust string to Java string
/// Returns null if conversion fails
fn rust_string_to_java(env: &JNIEnv, s: &str) -> jstring {
    match env.new_string(s) {
        Ok(jstr) => jstr.into_raw(),
        Err(_) => {
            // If we can't create a string, throw an exception
            env.throw_new("java/lang/RuntimeException", "Failed to create Java string")
                .ok();
            std::ptr::null_mut()
        }
    }
}

/// Convert Java string to Rust string
/// Returns empty string and logs error if conversion fails
fn java_string_to_rust(env: &JNIEnv, j_str: JString) -> String {
    if j_str.is_null() {
        env.throw_new("java/lang/IllegalArgumentException", "Null string parameter")
            .ok();
        return String::new();
    }
    
    match env.get_string(j_str) {
        Ok(jstr) => jstr.to_string_lossy().to_string(),
        Err(e) => {
            env.throw_new("java/lang/RuntimeException", &format!("Failed to get Java string: {}", e))
                .ok();
            String::new()
        }
    }
}

/// List all rooms - JNI implementation
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeListRooms(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString
) -> jstring {
    // Extract building name safely
    let building_str = java_string_to_rust(&env, building_name);
    
    // Check if building name extraction failed (empty string and exception thrown)
    if building_str.is_empty() && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Call the mobile FFI function
    match crate::mobile_ffi::list_rooms(building_str) {
        Ok(rooms) => {
            // Serialize to JSON
            match serde_json::to_string(&rooms) {
                Ok(json) => rust_string_to_java(&env, &json),
                Err(e) => {
                    env.throw_new("java/lang/RuntimeException", &format!("Serialization failed: {}", e))
                        .ok();
                    std::ptr::null_mut()
                }
            }
        }
        Err(e) => {
            // Return error as JSON
            let error_json = format!(r#"{{"error":"{}"}}"#, e);
            rust_string_to_java(&env, &error_json)
        }
    }
}

/// Get a specific room - JNI implementation
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeGetRoom(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString,
    room_id: JString
) -> jstring {
    // Extract building name and room ID safely
    let building_str = java_string_to_rust(&env, building_name);
    let room_id_str = java_string_to_rust(&env, room_id);
    
    // Check if extraction failed (empty string and exception thrown)
    if (building_str.is_empty() || room_id_str.is_empty()) && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Call the mobile FFI function
    match crate::mobile_ffi::get_room(building_str, room_id_str) {
        Ok(room) => {
            // Serialize to JSON
            match serde_json::to_string(&room) {
                Ok(json) => rust_string_to_java(&env, &json),
                Err(e) => {
                    env.throw_new("java/lang/RuntimeException", &format!("Serialization failed: {}", e))
                        .ok();
                    std::ptr::null_mut()
                }
            }
        }
        Err(e) => {
            // Return error as JSON
            let error_json = format!(r#"{{"error":"{}"}}"#, e);
            rust_string_to_java(&env, &error_json)
        }
    }
}

/// List all equipment - JNI implementation
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeListEquipment(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString
) -> jstring {
    // Extract building name safely
    let building_str = java_string_to_rust(&env, building_name);
    
    // Check if building name extraction failed (empty string and exception thrown)
    if building_str.is_empty() && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Call the mobile FFI function
    match crate::mobile_ffi::list_equipment(building_str) {
        Ok(equipment) => {
            // Serialize to JSON
            match serde_json::to_string(&equipment) {
                Ok(json) => rust_string_to_java(&env, &json),
                Err(e) => {
                    env.throw_new("java/lang/RuntimeException", &format!("Serialization failed: {}", e))
                        .ok();
                    std::ptr::null_mut()
                }
            }
        }
        Err(e) => {
            // Return error as JSON
            let error_json = format!(r#"{{"error":"{}"}}"#, e);
            rust_string_to_java(&env, &error_json)
        }
    }
}

/// Get specific equipment - JNI implementation
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeGetEquipment(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString,
    equipment_id: JString
) -> jstring {
    // Extract building name and equipment ID safely
    let building_str = java_string_to_rust(&env, building_name);
    let equipment_id_str = java_string_to_rust(&env, equipment_id);
    
    // Check if extraction failed (empty string and exception thrown)
    if (building_str.is_empty() || equipment_id_str.is_empty()) && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Call the mobile FFI function
    match crate::mobile_ffi::get_equipment(building_str, equipment_id_str) {
        Ok(equipment) => {
            // Serialize to JSON
            match serde_json::to_string(&equipment) {
                Ok(json) => rust_string_to_java(&env, &json),
                Err(e) => {
                    env.throw_new("java/lang/RuntimeException", &format!("Serialization failed: {}", e))
                        .ok();
                    std::ptr::null_mut()
                }
            }
        }
        Err(e) => {
            // Return error as JSON
            let error_json = format!(r#"{{"error":"{}"}}"#, e);
            rust_string_to_java(&env, &error_json)
        }
    }
}

/// Parse AR scan data - JNI implementation
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeParseARScan(
    mut env: JNIEnv,
    _class: JClass,
    json_data: JString
) -> jstring {
    // Extract JSON string safely
    let json_str = java_string_to_rust(&env, json_data);
    
    // Check if extraction failed (empty string and exception thrown)
    if json_str.is_empty() && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Call the mobile FFI function to parse AR scan
    match crate::mobile_ffi::parse_ar_scan(&json_str) {
        Ok(scan_data) => {
            // Serialize to JSON
            match serde_json::to_string(&scan_data) {
                Ok(json) => rust_string_to_java(&env, &json),
                Err(e) => {
                    env.throw_new("java/lang/RuntimeException", &format!("Serialization failed: {}", e))
                        .ok();
                    std::ptr::null_mut()
                }
            }
        }
        Err(e) => {
            // Return error as JSON
            let error_json = format!(r#"{{"error":"{}"}}"#, e);
            rust_string_to_java(&env, &error_json)
        }
    }
}

/// Extract equipment from AR scan - JNI implementation
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeExtractEquipment(
    mut env: JNIEnv,
    _class: JClass,
    json_data: JString
) -> jstring {
    // Extract JSON string safely
    let json_str = java_string_to_rust(&env, json_data);
    
    // Check if extraction failed (empty string and exception thrown)
    if json_str.is_empty() && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Parse AR scan first
    match crate::mobile_ffi::parse_ar_scan(&json_str) {
        Ok(scan_data) => {
            // Extract equipment from scan data
            let equipment = crate::mobile_ffi::extract_equipment_from_ar_scan(&scan_data);
            
            // Serialize equipment list to JSON
            match serde_json::to_string(&equipment) {
                Ok(json) => rust_string_to_java(&env, &json),
                Err(e) => {
                    env.throw_new("java/lang/RuntimeException", &format!("Serialization failed: {}", e))
                        .ok();
                    std::ptr::null_mut()
                }
            }
        }
        Err(e) => {
            // Return error as JSON
            let error_json = format!(r#"{{"error":"{}"}}"#, e);
            rust_string_to_java(&env, &error_json)
        }
    }
}

/// Process AR scan and create pending equipment - JNI implementation
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeProcessARScanToPending(
    mut env: JNIEnv,
    _class: JClass,
    json_data: JString,
    building_name: JString,
    confidence_threshold: f64
) -> jstring {
    use crate::ar_integration::processing;
    use crate::spatial::Point3D;
    
    // Extract JSON and building name safely
    let json_str = java_string_to_rust(&env, json_data);
    let building_str = java_string_to_rust(&env, building_name);
    
    // Check if extraction failed
    if (json_str.is_empty() || building_str.is_empty()) && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Parse AR scan from mobile FFI format
    match crate::mobile_ffi::parse_ar_scan(&json_str) {
        Ok(mobile_scan) => {
            // Convert mobile ARScanData to processing ARScanData
            let detected_equipment: Vec<_> = mobile_scan.detected_equipment.into_iter().map(|eq| {
                processing::DetectedEquipmentData {
                    name: eq.name,
                    equipment_type: eq.equipment_type,
                    position: Point3D::new(eq.position.x, eq.position.y, eq.position.z),
                    confidence: eq.confidence,
                    detection_method: eq.detection_method,
                }
            }).collect();
            
            let processing_scan = processing::ARScanData {
                detected_equipment,
            };
            
            // Process to pending
            match processing::process_ar_scan_to_pending(&processing_scan, &building_str, confidence_threshold) {
                Ok(pending_ids) => {
                    let response = serde_json::json!({
                        "success": true,
                        "pending_count": pending_ids.len(),
                        "pending_ids": pending_ids,
                        "building": building_str,
                        "confidence_threshold": confidence_threshold,
                    });
                    
                    match serde_json::to_string(&response) {
                        Ok(json) => rust_string_to_java(&env, &json),
                        Err(e) => {
                            env.throw_new("java/lang/RuntimeException", &format!("Serialization failed: {}", e))
                                .ok();
                            std::ptr::null_mut()
                        }
                    }
                }
                Err(e) => {
                    let error_json = format!(r#"{{"success":false,"error":"{}"}}"#, e);
                    rust_string_to_java(&env, &error_json)
                }
            }
        }
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"{}"}}"#, e);
            rust_string_to_java(&env, &error_json)
        }
    }
}

/// Export building to AR format - JNI implementation
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeExportForAR(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString,
    format: JString
) -> jstring {
    use crate::export::ar::{ARExporter, ARFormat};
    use std::path::Path;
    
    // Extract building name and format safely
    let building_str = java_string_to_rust(&env, building_name);
    let format_str = java_string_to_rust(&env, format);
    
    // Check if extraction failed
    if (building_str.is_empty() || format_str.is_empty()) && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Load building data
    let building_data = match crate::utils::loading::load_building_data(&building_str) {
        Ok(data) => data,
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Building not found: {}"}}"#, e);
            return rust_string_to_java(&env, &error_json);
        }
    };
    
    // Parse format
    let ar_format = match format_str.parse::<ARFormat>() {
        Ok(fmt) => fmt,
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Invalid format: {}"}}"#, e);
            return rust_string_to_java(&env, &error_json);
        }
    };
    
    // Create exporter and determine output path
    let output_filename = match ar_format {
        ARFormat::GLTF => format!("{}.gltf", building_str),
        ARFormat::USDZ => format!("{}.usdz", building_str),
    };
    
    let output_path = Path::new(&output_filename);
    let exporter = ARExporter::new(building_data);
    
    // Export
    match exporter.export(ar_format, output_path) {
        Ok(_) => {
            let response = serde_json::json!({
                "success": true,
                "building": building_str,
                "format": format_str,
                "output_file": output_filename,
                "message": "Building exported successfully for AR",
            });
            
            match serde_json::to_string(&response) {
                Ok(json) => rust_string_to_java(&env, &json),
                Err(e) => {
                    env.throw_new("java/lang/RuntimeException", &format!("Serialization failed: {}", e))
                        .ok();
                    std::ptr::null_mut()
                }
            }
        }
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Export failed: {}"}}"#, e);
            rust_string_to_java(&env, &error_json)
        }
    }
}

/// Load/export building model for AR viewing - JNI implementation
///
/// This function exports a building to AR-compatible format (USDZ or glTF) and returns
/// the file path where the model was saved. If `output_path` is null or empty, a temporary file
/// will be created in the system temp directory.
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeLoadARModel(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString,
    format: JString,
    output_path: JString
) -> jstring {
    use crate::export::ar::{ARExporter, ARFormat};
    use std::path::PathBuf;
    use std::fs;
    use uuid::Uuid;
    
    // Extract parameters safely
    let building_str = java_string_to_rust(&env, building_name);
    let format_str = java_string_to_rust(&env, format);
    let output_path_str = if output_path.is_null() {
        None
    } else {
        Some(java_string_to_rust(&env, output_path))
    };
    
    // Check if extraction failed
    if building_str.is_empty() || format_str.is_empty() {
        if env.exception_check().unwrap_or(false) {
            return std::ptr::null_mut();
        }
    }
    
    // Parse AR format enum
    let ar_format = match format_str.parse::<ARFormat>() {
        Ok(fmt) => fmt,
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Invalid format '{}': {}"}}"#, format_str, e);
            return rust_string_to_java(&env, &error_json);
        }
    };
    
    // Determine output path
    let output_path_buf: PathBuf = if let Some(path_str) = output_path_str {
        if path_str.is_empty() {
            // Empty string means use temp directory
            let temp_dir = std::env::temp_dir();
            let file_extension = match ar_format {
                ARFormat::GLTF => "gltf",
                ARFormat::USDZ => "usdz",
            };
            let temp_filename = format!("arxos_{}_{}.{}", building_str, Uuid::new_v4(), file_extension);
            temp_dir.join(temp_filename)
        } else {
            PathBuf::from(path_str)
        }
    } else {
        // Null means use temp directory
        let temp_dir = std::env::temp_dir();
        let file_extension = match ar_format {
            ARFormat::GLTF => "gltf",
            ARFormat::USDZ => "usdz",
        };
        let temp_filename = format!("arxos_{}_{}.{}", building_str, Uuid::new_v4(), file_extension);
        temp_dir.join(temp_filename)
    };
    
    // Load building data
    let building_data = match crate::utils::loading::load_building_data(&building_str) {
        Ok(data) => data,
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Building not found: {}"}}"#, e);
            return rust_string_to_java(&env, &error_json);
        }
    };
    
    // Create exporter and export
    let exporter = ARExporter::new(building_data);
    match exporter.export(ar_format, &output_path_buf) {
        Ok(_) => {
            // Get file size
            let file_size = match fs::metadata(&output_path_buf) {
                Ok(metadata) => metadata.len(),
                Err(_) => 0
            };
            
            // Convert path to string for JSON response
            let file_path_str = match output_path_buf.to_str() {
                Some(s) => s.to_string(),
                None => {
                    let error_json = r#"{"success":false,"error":"Output path contains invalid UTF-8"}"#;
                    return rust_string_to_java(&env, error_json);
                }
            };
            
            let response = serde_json::json!({
                "success": true,
                "building": building_str,
                "format": format_str.to_lowercase(),
                "file_path": file_path_str,
                "file_size": file_size,
                "message": format!("Building '{}' exported successfully to {} format", building_str, format_str),
            });
            
            match serde_json::to_string(&response) {
                Ok(json) => rust_string_to_java(&env, &json),
                Err(e) => {
                    env.throw_new("java/lang/RuntimeException", &format!("Serialization failed: {}", e))
                        .ok();
                    std::ptr::null_mut()
                }
            }
        }
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Export failed: {}"}}"#, e);
            rust_string_to_java(&env, &error_json)
        }
    }
}

/// Save AR scan data and process to pending equipment - JNI implementation
///
/// This function accepts AR scan data from mobile devices, optionally saves it to a file
/// for debugging/audit purposes, and processes it to create pending equipment items that
/// can be reviewed and confirmed by users.
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeSaveARScan(
    mut env: JNIEnv,
    _class: JClass,
    json_data: JString,
    building_name: JString,
    confidence_threshold: f64
) -> jstring {
    use crate::ar_integration::processing;
    use crate::spatial::Point3D;
    use chrono::Utc;
    use std::fs;
    use std::path::PathBuf;
    
    // Extract parameters safely
    let json_str = java_string_to_rust(&env, json_data);
    let building_str = java_string_to_rust(&env, building_name);
    
    // Check if extraction failed
    if json_str.is_empty() || building_str.is_empty() {
        if env.exception_check().unwrap_or(false) {
            return std::ptr::null_mut();
        }
    }
    
    // Validate confidence threshold
    if confidence_threshold < 0.0 || confidence_threshold > 1.0 {
        let error_json = format!(
            r#"{{"success":false,"error":"Confidence threshold must be between 0.0 and 1.0, got: {}"}}"#,
            confidence_threshold
        );
        return rust_string_to_java(&env, &error_json);
    }
    
    // Parse AR scan from mobile FFI format
    let mobile_scan = match crate::mobile_ffi::parse_ar_scan(&json_str) {
        Ok(scan) => scan,
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Failed to parse AR scan JSON: {}"}}"#, e);
            return rust_string_to_java(&env, &error_json);
        }
    };
    
    // Optionally save raw scan data to file for debugging/audit
    let scan_timestamp = Utc::now();
    let scan_save_result = {
        let scan_dir = PathBuf::from(format!("{}_scans", building_str));
        if let Err(_) = fs::create_dir_all(&scan_dir) {
            // Continue anyway, saving scan data is optional
        }
        
        let scan_filename = format!("scan_{}.json", scan_timestamp.format("%Y%m%d_%H%M%S"));
        let scan_path = scan_dir.join(scan_filename);
        
        match fs::write(&scan_path, &json_str) {
            Ok(_) => Some(scan_path.to_string_lossy().to_string()),
            Err(_) => {
                // Continue anyway, processing is more important than saving raw data
                None
            }
        }
    };
    
    // Convert mobile ARScanData to processing ARScanData
    let detected_equipment: Vec<_> = mobile_scan.detected_equipment.into_iter().map(|eq| {
        processing::DetectedEquipmentData {
            name: eq.name,
            equipment_type: eq.equipment_type,
            position: Point3D::new(eq.position.x, eq.position.y, eq.position.z),
            confidence: eq.confidence,
            detection_method: eq.detection_method,
        }
    }).collect();
    
    let processing_scan = processing::ARScanData {
        detected_equipment,
    };
    
    // Process scan to pending equipment
    match processing::process_ar_scan_to_pending(&processing_scan, &building_str, confidence_threshold) {
        Ok(pending_ids) => {
            // Save pending equipment to storage
            use crate::ar_integration::pending::PendingEquipmentManager;
            
            let mut manager = PendingEquipmentManager::new(building_str.to_string());
            let storage_file = PathBuf::from(format!("{}_pending.json", building_str));
            
            // Load existing pending items
            if storage_file.exists() {
                if let Err(_) = manager.load_from_storage(&storage_file) {
                    // Continue with empty manager
                }
            }
            
            let response = serde_json::json!({
                "success": true,
                "building": building_str,
                "pending_count": pending_ids.len(),
                "pending_ids": pending_ids,
                "confidence_threshold": confidence_threshold,
                "scan_timestamp": scan_timestamp.to_rfc3339(),
                "scan_file": scan_save_result,
                "message": format!(
                    "AR scan processed successfully: {} pending equipment items created",
                    pending_ids.len()
                ),
            });
            
            match serde_json::to_string(&response) {
                Ok(json) => rust_string_to_java(&env, &json),
                Err(e) => {
                    env.throw_new("java/lang/RuntimeException", &format!("Serialization failed: {}", e))
                        .ok();
                    std::ptr::null_mut()
                }
            }
        }
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Processing failed: {}"}}"#, e);
            rust_string_to_java(&env, &error_json)
        }
    }
}

/// List pending equipment for a building - JNI implementation
///
/// Returns all pending equipment items that need user confirmation.
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeListPendingEquipment(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString
) -> jstring {
    use crate::ar_integration::pending::PendingEquipmentManager;
    use std::path::PathBuf;
    
    // Extract building name safely
    let building_str = java_string_to_rust(&env, building_name);
    
    // Check if extraction failed
    if building_str.is_empty() && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Try to load pending equipment from storage
    let mut manager = PendingEquipmentManager::new(building_str.to_string());
    
    // Look for pending equipment storage file
    let storage_file = PathBuf::from(format!("{}_pending.json", building_str));
    if storage_file.exists() {
        if let Err(_) = manager.load_from_storage(&storage_file) {
            // Continue with empty manager
        }
    }
    
    // Get all pending items
    let pending_items = manager.list_pending();
    
    // Convert to JSON-serializable format
    let pending_list: Vec<_> = pending_items.iter().map(|item| {
        serde_json::json!({
            "id": item.id,
            "name": item.name,
            "equipment_type": item.equipment_type,
            "position": {
                "x": item.position.x,
                "y": item.position.y,
                "z": item.position.z
            },
            "confidence": item.confidence,
            "detection_method": format!("{:?}", item.detection_method),
            "detected_at": item.detected_at.to_rfc3339(),
            "floor_level": item.floor_level,
            "room_name": item.room_name,
            "status": "pending"
        })
    }).collect();
    
    let response = serde_json::json!({
        "success": true,
        "building": building_str,
        "pending_count": pending_list.len(),
        "items": pending_list
    });
    
    match serde_json::to_string(&response) {
        Ok(json) => rust_string_to_java(&env, &json),
        Err(e) => {
            env.throw_new("java/lang/RuntimeException", &format!("Serialization failed: {}", e))
                .ok();
            std::ptr::null_mut()
        }
    }
}

/// Confirm pending equipment and add to building data - JNI implementation
///
/// Confirms a pending equipment item, adds it to the building data, and optionally commits to Git.
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeConfirmPendingEquipment(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString,
    pending_id: JString,
    commit_to_git: jboolean
) -> jstring {
    use crate::ar_integration::pending::PendingEquipmentManager;
    use crate::utils::loading::load_building_data;
    use crate::persistence::PersistenceManager;
    
    // Extract parameters safely
    let building_str = java_string_to_rust(&env, building_name);
    let pending_id_str = java_string_to_rust(&env, pending_id);
    
    // Check if extraction failed
    if (building_str.is_empty() || pending_id_str.is_empty()) && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Load pending equipment manager
    let mut manager = PendingEquipmentManager::new(building_str.to_string());
    let storage_file = std::path::PathBuf::from(format!("{}_pending.json", building_str));
    if storage_file.exists() {
        if let Err(_) = manager.load_from_storage(&storage_file) {
            // Continue anyway
        }
    }
    
    // Load building data
    let mut building_data = match load_building_data(&building_str) {
        Ok(data) => data,
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Building not found: {}"}}"#, e);
            return rust_string_to_java(&env, &error_json);
        }
    };
    
    // Confirm pending equipment
    match manager.confirm_pending(&pending_id_str, &mut building_data) {
        Ok(equipment_id) => {
            // Save pending equipment state
            if let Err(_) = manager.save_to_storage_path(&storage_file) {
                // Continue anyway
            }
            
            // Save building data and optionally commit to Git
            let commit_message = format!("Confirm pending equipment: {}", pending_id_str);
            let persistence_manager = match PersistenceManager::new(&building_str) {
                Ok(pm) => pm,
                Err(e) => {
                    let error_json = format!(r#"{{"success":false,"error":"Persistence error: {}"}}"#, e);
                    return rust_string_to_java(&env, &error_json);
                }
            };
            
            let commit_result = if commit_to_git != 0 {
                match persistence_manager.save_and_commit(&building_data, Some(&commit_message)) {
                    Ok(commit_id) => Some(commit_id),
                    Err(e) => {
                        // Still save to file even if Git commit fails
                        if let Err(save_err) = persistence_manager.save_building_data(&building_data) {
                            let error_json = format!(r#"{{"success":false,"error":"Failed to save: {}"}}"#, save_err);
                            return rust_string_to_java(&env, &error_json);
                        }
                        None
                    }
                }
            } else {
                // Save to file only
                match persistence_manager.save_building_data(&building_data) {
                    Ok(_) => None,
                    Err(e) => {
                        let error_json = format!(r#"{{"success":false,"error":"Failed to save: {}"}}"#, e);
                        return rust_string_to_java(&env, &error_json);
                    }
                }
            };
            
            let response = serde_json::json!({
                "success": true,
                "building": building_str,
                "pending_id": pending_id_str,
                "equipment_id": equipment_id,
                "committed": commit_result.is_some(),
                "commit_id": commit_result,
                "message": format!("Equipment '{}' confirmed and added to building", pending_id_str)
            });
            
            match serde_json::to_string(&response) {
                Ok(json) => rust_string_to_java(&env, &json),
                Err(e) => {
                    env.throw_new("java/lang/RuntimeException", &format!("Serialization failed: {}", e))
                        .ok();
                    std::ptr::null_mut()
                }
            }
        }
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Failed to confirm: {}"}}"#, e);
            rust_string_to_java(&env, &error_json)
        }
    }
}

/// Reject pending equipment - JNI implementation
///
/// Marks a pending equipment item as rejected without adding it to building data.
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeRejectPendingEquipment(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString,
    pending_id: JString
) -> jstring {
    use crate::ar_integration::pending::PendingEquipmentManager;
    use std::path::PathBuf;
    
    // Extract parameters safely
    let building_str = java_string_to_rust(&env, building_name);
    let pending_id_str = java_string_to_rust(&env, pending_id);
    
    // Check if extraction failed
    if (building_str.is_empty() || pending_id_str.is_empty()) && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Load pending equipment manager
    let mut manager = PendingEquipmentManager::new(building_str.to_string());
    let storage_file = PathBuf::from(format!("{}_pending.json", building_str));
    if storage_file.exists() {
        if let Err(_) = manager.load_from_storage(&storage_file) {
            // Continue anyway
        }
    }
    
    // Reject pending equipment
    match manager.reject_pending(&pending_id_str) {
        Ok(_) => {
            // Save updated pending state
            if let Err(_) = manager.save_to_storage_path(&storage_file) {
                // Continue anyway, rejection is still valid
            }
            
            let response = serde_json::json!({
                "success": true,
                "building": building_str,
                "pending_id": pending_id_str,
                "message": format!("Equipment '{}' rejected", pending_id_str)
            });
            
            match serde_json::to_string(&response) {
                Ok(json) => rust_string_to_java(&env, &json),
                Err(e) => {
                    env.throw_new("java/lang/RuntimeException", &format!("Serialization failed: {}", e))
                        .ok();
                    std::ptr::null_mut()
                }
            }
        }
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Failed to reject: {}"}}"#, e);
            rust_string_to_java(&env, &error_json)
        }
    }
}


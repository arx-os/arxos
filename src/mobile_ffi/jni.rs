//! JNI bindings for Android
//!
//! This module provides Java Native Interface (JNI) bindings for Android.

use jni::JNIEnv;
use jni::objects::{JClass, JString};
use jni::sys::{jstring, jboolean};
use std::os::raw::c_char;
use std::ffi::{CStr, CString};

use crate::mobile_ffi::{MobileError, RoomInfo, EquipmentInfo};

// External C FFI function declarations
extern "C" {
    fn arxos_request_user_registration(
        building_name: *const c_char,
        email: *const c_char,
        name: *const c_char,
        organization: *const c_char,
        role: *const c_char,
        phone: *const c_char,
        device_info: *const c_char,
        app_version: *const c_char,
    ) -> *mut c_char;
    
    fn arxos_check_registration_status(
        building_name: *const c_char,
        email: *const c_char,
    ) -> *mut c_char;
    
    fn arxos_check_gpg_available() -> *mut c_char;
    
    fn arxos_get_gpg_fingerprint(email: *const c_char) -> *mut c_char;
    
    fn arxos_configure_git_signing(
        building_name: *const c_char,
        key_id: *const c_char,
    ) -> *mut c_char;
    
    fn arxos_free_string(ptr: *mut c_char);
}

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
            match processing::process_ar_scan_to_pending(&processing_scan, &building_str, confidence_threshold, None) {
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
    user_email: JString,  // NEW: User email from mobile app (can be null for backward compatibility)
    confidence_threshold: f64
) -> jstring {
    use std::ffi::CString;
    use crate::mobile_ffi::ffi::arxos_save_ar_scan;
    
    // Extract parameters safely
    let json_str = java_string_to_rust(&env, json_data);
    let building_str = java_string_to_rust(&env, building_name);
    
    // Extract user_email (optional - can be null)
    let user_email_str = if user_email.is_null() {
        String::new()
    } else {
        java_string_to_rust(&env, user_email)
    };
    
    // Check if extraction failed
    if json_str.is_empty() || building_str.is_empty() {
        if env.exception_check().unwrap_or(false) {
            return std::ptr::null_mut();
        }
    }
    
    // Convert to C strings for FFI call
    let json_cstr = match CString::new(json_str) {
        Ok(s) => s,
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Failed to create C string from JSON: {}"}}"#, e);
            return rust_string_to_java(&env, &error_json);
        }
    };
    
    let building_cstr = match CString::new(building_str) {
        Ok(s) => s,
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Failed to create C string from building name: {}"}}"#, e);
            return rust_string_to_java(&env, &error_json);
        }
    };
    
    // Create user_email C string (can be null for backward compatibility)
    let user_email_cstr = if user_email_str.is_empty() {
        None
    } else {
        match CString::new(user_email_str) {
            Ok(s) => Some(s),
            Err(_) => None, // If conversion fails, pass null (backward compatible)
        }
    };
    
    // Call C FFI function
    let result_ptr = arxos_save_ar_scan(
        json_cstr.as_ptr(),
        building_cstr.as_ptr(),
        user_email_cstr.as_ref().map(|s| s.as_ptr()).unwrap_or(std::ptr::null()),
        confidence_threshold
    );
    
    // Handle result
    if result_ptr.is_null() {
        let error_json = r#"{"success":false,"error":"FFI call returned null pointer"}"#;
        return rust_string_to_java(&env, error_json);
    }
    
    // Convert C string result to Rust string
    let result_str = match std::ffi::CStr::from_ptr(result_ptr).to_str() {
        Ok(s) => s.to_string(),
        Err(_) => {
            // Free the string even if conversion failed
            crate::mobile_ffi::ffi::arxos_free_string(result_ptr);
            let error_json = r#"{"success":false,"error":"Failed to convert result to string"}"#;
            return rust_string_to_java(&env, error_json);
        }
    };
    
    // Free the C string
    crate::mobile_ffi::ffi::arxos_free_string(result_ptr);
    
    // Return result to Java
    rust_string_to_java(&env, &result_str)
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
    user_email: JString,  // NEW: User email from mobile app (can be null for backward compatibility)
    commit_to_git: jboolean
) -> jstring {
    use std::ffi::CString;
    use crate::mobile_ffi::ffi::arxos_confirm_pending_equipment;
    
    // Extract parameters safely
    let building_str = java_string_to_rust(&env, building_name);
    let pending_id_str = java_string_to_rust(&env, pending_id);
    
    // Extract user_email (optional - can be null)
    let user_email_str = if user_email.is_null() {
        String::new()
    } else {
        java_string_to_rust(&env, user_email)
    };
    
    // Check if extraction failed
    if (building_str.is_empty() || pending_id_str.is_empty()) && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Convert to C strings for FFI call
    let building_cstr = match CString::new(building_str) {
        Ok(s) => s,
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Failed to create C string from building name: {}"}}"#, e);
            return rust_string_to_java(&env, &error_json);
        }
    };
    
    let pending_id_cstr = match CString::new(pending_id_str) {
        Ok(s) => s,
        Err(e) => {
            let error_json = format!(r#"{{"success":false,"error":"Failed to create C string from pending ID: {}"}}"#, e);
            return rust_string_to_java(&env, &error_json);
        }
    };
    
    // Create user_email C string (can be null for backward compatibility)
    let user_email_cstr = if user_email_str.is_empty() {
        None
    } else {
        match CString::new(user_email_str) {
            Ok(s) => Some(s),
            Err(_) => None, // If conversion fails, pass null (backward compatible)
        }
    };
    
    // Call C FFI function
    let result_ptr = arxos_confirm_pending_equipment(
        building_cstr.as_ptr(),
        pending_id_cstr.as_ptr(),
        user_email_cstr.as_ref().map(|s| s.as_ptr()).unwrap_or(std::ptr::null()),
        commit_to_git as i32
    );
    
    // Handle result
    if result_ptr.is_null() {
        let error_json = r#"{"success":false,"error":"FFI call returned null pointer"}"#;
        return rust_string_to_java(&env, error_json);
    }
    
    // Convert C string result to Rust string
    let result_str = match std::ffi::CStr::from_ptr(result_ptr).to_str() {
        Ok(s) => s.to_string(),
        Err(_) => {
            // Free the string even if conversion failed
            crate::mobile_ffi::ffi::arxos_free_string(result_ptr);
            let error_json = r#"{"success":false,"error":"Failed to convert result to string"}"#;
            return rust_string_to_java(&env, error_json);
        }
    };
    
    // Free the C string
    crate::mobile_ffi::ffi::arxos_free_string(result_ptr);
    
    // Return result to Java
    rust_string_to_java(&env, &result_str)
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

/// Request user registration from mobile app - JNI implementation
///
/// Creates a pending user registration request that will be reviewed by an admin.
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeRequestUserRegistration(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString,
    email: JString,
    name: JString,
    organization: JString,
    role: JString,
    phone: JString,
    device_info: JString,
    app_version: JString,
) -> jstring {
    // Extract parameters safely
    let building_str = java_string_to_rust(&env, building_name);
    let email_str = java_string_to_rust(&env, email);
    let name_str = java_string_to_rust(&env, name);
    let organization_str = java_string_to_rust(&env, organization);
    let role_str = java_string_to_rust(&env, role);
    let phone_str = java_string_to_rust(&env, phone);
    let device_info_str = java_string_to_rust(&env, device_info);
    let app_version_str = java_string_to_rust(&env, app_version);
    
    // Check if extraction failed
    if (building_str.is_empty() || email_str.is_empty() || name_str.is_empty()) && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Convert to C strings for FFI call
    let building_cstr = match CString::new(building_str) {
        Ok(s) => s,
        Err(_) => {
            env.throw_new("java/lang/IllegalArgumentException", "Invalid building name")
                .ok();
            return std::ptr::null_mut();
        }
    };
    
    let email_cstr = match CString::new(email_str) {
        Ok(s) => s,
        Err(_) => {
            env.throw_new("java/lang/IllegalArgumentException", "Invalid email")
                .ok();
            return std::ptr::null_mut();
        }
    };
    
    let name_cstr = match CString::new(name_str) {
        Ok(s) => s,
        Err(_) => {
            env.throw_new("java/lang/IllegalArgumentException", "Invalid name")
                .ok();
            return std::ptr::null_mut();
        }
    };
    
    // Optional parameters - can be null if empty
    let organization_cstr = if organization_str.is_empty() {
        std::ptr::null()
    } else {
        match CString::new(organization_str) {
            Ok(s) => s.into_raw(),
            Err(_) => std::ptr::null(),
        }
    };
    
    let role_cstr = if role_str.is_empty() {
        std::ptr::null()
    } else {
        match CString::new(role_str) {
            Ok(s) => s.into_raw(),
            Err(_) => std::ptr::null(),
        }
    };
    
    let phone_cstr = if phone_str.is_empty() {
        std::ptr::null()
    } else {
        match CString::new(phone_str) {
            Ok(s) => s.into_raw(),
            Err(_) => std::ptr::null(),
        }
    };
    
    let device_info_cstr = if device_info_str.is_empty() {
        std::ptr::null()
    } else {
        match CString::new(device_info_str) {
            Ok(s) => s.into_raw(),
            Err(_) => std::ptr::null(),
        }
    };
    
    let app_version_cstr = if app_version_str.is_empty() {
        std::ptr::null()
    } else {
        match CString::new(app_version_str) {
            Ok(s) => s.into_raw(),
            Err(_) => std::ptr::null(),
        }
    };
    
    // Call C FFI function
    let result_ptr = unsafe {
        arxos_request_user_registration(
            building_cstr.as_ptr(),
            email_cstr.as_ptr(),
            name_cstr.as_ptr(),
            organization_cstr,
            role_cstr,
            phone_cstr,
            device_info_cstr,
            app_version_cstr,
        )
    };
    
    // Free optional CStrings if we created them
    if !organization_cstr.is_null() {
        let _ = unsafe { CString::from_raw(organization_cstr) };
    }
    if !role_cstr.is_null() {
        let _ = unsafe { CString::from_raw(role_cstr) };
    }
    if !phone_cstr.is_null() {
        let _ = unsafe { CString::from_raw(phone_cstr) };
    }
    if !device_info_cstr.is_null() {
        let _ = unsafe { CString::from_raw(device_info_cstr) };
    }
    if !app_version_cstr.is_null() {
        let _ = unsafe { CString::from_raw(app_version_cstr) };
    }
    
    if result_ptr.is_null() {
        let error_json = r#"{"success":false,"error":"FFI call returned null pointer"}"#;
        return rust_string_to_java(&env, error_json);
    }
    
    let result_string = unsafe { CStr::from_ptr(result_ptr).to_string_lossy().to_string() };
    unsafe { arxos_free_string(result_ptr) };
    
    rust_string_to_java(&env, &result_string)
}

/// Check registration status for a mobile user - JNI implementation
///
/// Returns the current status of a user's registration request.
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeCheckRegistrationStatus(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString,
    email: JString,
) -> jstring {
    // Extract parameters safely
    let building_str = java_string_to_rust(&env, building_name);
    let email_str = java_string_to_rust(&env, email);
    
    // Check if extraction failed
    if (building_str.is_empty() || email_str.is_empty()) && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Convert to C strings for FFI call
    let building_cstr = match CString::new(building_str) {
        Ok(s) => s,
        Err(_) => {
            env.throw_new("java/lang/IllegalArgumentException", "Invalid building name")
                .ok();
            return std::ptr::null_mut();
        }
    };
    
    let email_cstr = match CString::new(email_str) {
        Ok(s) => s,
        Err(_) => {
            env.throw_new("java/lang/IllegalArgumentException", "Invalid email")
                .ok();
            return std::ptr::null_mut();
        }
    };
    
    // Call C FFI function
    let result_ptr = unsafe {
        arxos_check_registration_status(
            building_cstr.as_ptr(),
            email_cstr.as_ptr(),
        )
    };
    
    if result_ptr.is_null() {
        let error_json = r#"{"success":false,"error":"FFI call returned null pointer"}"#;
        return rust_string_to_java(&env, error_json);
    }
    
    let result_string = unsafe { CStr::from_ptr(result_ptr).to_string_lossy().to_string() };
    unsafe { arxos_free_string(result_ptr) };
    
    rust_string_to_java(&env, &result_string)
}

/// Check if GPG is available on the system - JNI implementation
///
/// Returns whether GPG is installed and available for use.
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeCheckGpgAvailable(
    mut env: JNIEnv,
    _class: JClass,
) -> jstring {
    // Call C FFI function
    let result_ptr = unsafe {
        arxos_check_gpg_available()
    };
    
    if result_ptr.is_null() {
        let error_json = r#"{"success":false,"error":"FFI call returned null pointer"}"#;
        return rust_string_to_java(&env, error_json);
    }
    
    let result_string = unsafe { CStr::from_ptr(result_ptr).to_string_lossy().to_string() };
    unsafe { arxos_free_string(result_ptr) };
    
    rust_string_to_java(&env, &result_string)
}

/// Get GPG key fingerprint for a user's email - JNI implementation
///
/// Looks up the GPG key fingerprint associated with the given email address.
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeGetGpgFingerprint(
    mut env: JNIEnv,
    _class: JClass,
    email: JString,
) -> jstring {
    // Extract parameters safely
    let email_str = java_string_to_rust(&env, email);
    
    // Check if extraction failed
    if email_str.is_empty() && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Convert to C string for FFI call
    let email_cstr = match CString::new(email_str) {
        Ok(s) => s,
        Err(_) => {
            env.throw_new("java/lang/IllegalArgumentException", "Invalid email")
                .ok();
            return std::ptr::null_mut();
        }
    };
    
    // Call C FFI function
    let result_ptr = unsafe {
        arxos_get_gpg_fingerprint(email_cstr.as_ptr())
    };
    
    if result_ptr.is_null() {
        let error_json = r#"{"success":false,"error":"FFI call returned null pointer"}"#;
        return rust_string_to_java(&env, error_json);
    }
    
    let result_string = unsafe { CStr::from_ptr(result_ptr).to_string_lossy().to_string() };
    unsafe { arxos_free_string(result_ptr) };
    
    rust_string_to_java(&env, &result_string)
}

/// Configure Git signing key for a repository - JNI implementation
///
/// Sets the user.signingkey Git configuration for the building repository.
///
/// # Safety
/// This function is called from JNI and must follow JNI conventions
#[no_mangle]
pub unsafe extern "system" fn Java_com_arxos_mobile_service_ArxOSCoreJNI_nativeConfigureGitSigning(
    mut env: JNIEnv,
    _class: JClass,
    building_name: JString,
    key_id: JString,
) -> jstring {
    // Extract parameters safely
    let building_str = java_string_to_rust(&env, building_name);
    let key_id_str = java_string_to_rust(&env, key_id);
    
    // Check if extraction failed
    if (building_str.is_empty() || key_id_str.is_empty()) && env.exception_check().unwrap_or(false) {
        return std::ptr::null_mut();
    }
    
    // Convert to C strings for FFI call
    let building_cstr = match CString::new(building_str) {
        Ok(s) => s,
        Err(_) => {
            env.throw_new("java/lang/IllegalArgumentException", "Invalid building name")
                .ok();
            return std::ptr::null_mut();
        }
    };
    
    let key_id_cstr = match CString::new(key_id_str) {
        Ok(s) => s,
        Err(_) => {
            env.throw_new("java/lang/IllegalArgumentException", "Invalid key ID")
                .ok();
            return std::ptr::null_mut();
        }
    };
    
    // Call C FFI function
    let result_ptr = unsafe {
        arxos_configure_git_signing(
            building_cstr.as_ptr(),
            key_id_cstr.as_ptr(),
        )
    };
    
    if result_ptr.is_null() {
        let error_json = r#"{"success":false,"error":"FFI call returned null pointer"}"#;
        return rust_string_to_java(&env, error_json);
    }
    
    let result_string = unsafe { CStr::from_ptr(result_ptr).to_string_lossy().to_string() };
    unsafe { arxos_free_string(result_ptr) };
    
    rust_string_to_java(&env, &result_string)
}


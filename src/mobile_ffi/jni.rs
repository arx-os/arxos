//! JNI bindings for Android
//!
//! This module provides Java Native Interface (JNI) bindings for Android.

use jni::JNIEnv;
use jni::objects::{JClass, JString};
use jni::sys::jstring;
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


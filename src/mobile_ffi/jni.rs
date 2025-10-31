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


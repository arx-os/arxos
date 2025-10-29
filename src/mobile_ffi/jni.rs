//! JNI bindings for Android
//!
//! This module provides Java Native Interface (JNI) bindings for Android.

use jni::JNIEnv;
use jni::objects::{JClass, JString, JObject};
use jni::sys::{jstring, jobject, jobjectArray};
use std::ffi::{CString, CStr};
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
    
    // For now, return JSON error indicating JNI implementation is pending
    // TODO: Implement actual room listing once JNI integration is complete
    let error_json = format!(r#"{{"error":"JNI implementation pending","building":"{}"}}"#, building_str);
    rust_string_to_java(&env, &error_json)
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
    let error_json = r#"{"error":"JNI implementation pending"}"#;
    rust_string_to_java(&env, error_json)
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
    let error_json = r#"{"error":"JNI implementation pending"}"#;
    rust_string_to_java(&env, error_json)
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
    let error_json = r#"{"error":"JNI implementation pending"}"#;
    rust_string_to_java(&env, error_json)
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
    let error_json = r#"{"error":"JNI implementation pending"}"#;
    rust_string_to_java(&env, error_json)
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
    let error_json = r#"{"error":"JNI implementation pending"}"#;
    rust_string_to_java(&env, error_json)
}


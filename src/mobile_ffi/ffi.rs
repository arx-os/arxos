//! C FFI bindings for mobile applications
//!
//! This module provides C-compatible function exports for iOS and Android.

use std::ffi::{CString, CStr};
use std::os::raw::c_char;
use serde_json;
use log::warn;

use crate::mobile_ffi::MobileError;

/// FFI error code enumeration
#[repr(C)]
pub enum ArxOSErrorCode {
    Success = 0,
    NotFound = 1,
    InvalidData = 2,
    IoError = 3,
    Unknown = 99,
}

/// Create a safe C string from a Rust string, with fallback on null bytes
fn create_safe_c_string(s: String) -> *mut c_char {
    match CString::new(s.clone()) {
        Ok(cstr) => cstr.into_raw(),
        Err(_) => {
            warn!("CString creation failed (null byte detected), sanitizing string");
            // Replace null bytes and try again
            let sanitized: Vec<u8> = s.into_bytes().into_iter()
                .filter(|&b| b != 0)
                .collect();
            match CString::new(sanitized) {
                Ok(cstr) => cstr.into_raw(),
                Err(_) => {
                    // Final fallback - static error string
                    warn!("Failed to sanitize string even after removing null bytes, using fallback");
                    CString::new(r#"{"error":"internal encoding error"}"#)
                        .expect("Fallback error string must be valid")
                        .into_raw()
                }
            }
        }
    }
}

/// Create a C-compatible JSON string from a result
fn create_json_response<T: serde::Serialize>(result: Result<T, MobileError>) -> *mut c_char {
    match result {
        Ok(data) => {
            match serde_json::to_string(&data) {
                Ok(json) => create_safe_c_string(json),
                Err(e) => {
                    warn!("Failed to serialize response: {}", e);
                    create_safe_c_string(r#"{"error":"serialization failed"}"#.to_string())
                }
            }
        }
        Err(e) => {
            warn!("FFI error: {:?}", e);
            create_safe_c_string(format!(r#"{{"error":"{}"}}"#, e))
        }
    }
}

/// Create an error response string
fn create_error_response(error: MobileError) -> *mut c_char {
    warn!("FFI error: {:?}", error);
    create_safe_c_string(format!(r#"{{"error":"{}"}}"#, error))
}

/// Free a C string allocated by ArxOS
///
/// # Safety
/// This function must only be called with pointers returned from ArxOS FFI functions
#[no_mangle]
pub unsafe extern "C" fn arxos_free_string(ptr: *mut c_char) {
    if !ptr.is_null() {
        let _ = CString::from_raw(ptr);
    }
}

/// Get the last error code from the last operation
#[no_mangle]
pub extern "C" fn arxos_last_error() -> i32 {
    // Returns Success as this is a per-operation error tracking system
    ArxOSErrorCode::Success as i32
}

/// Get the last error message
#[no_mangle]
pub extern "C" fn arxos_last_error_message() -> *mut c_char {
    // Returns empty string as error details are in JSON response
    // Empty string is always safe for CString
    CString::new("")
        .expect("Empty string must always be valid for CString")
        .into_raw()
}

/// List all rooms in a building
///
/// # Safety
/// The building_name parameter must be a valid UTF-8 null-terminated string
#[no_mangle]
pub unsafe extern "C" fn arxos_list_rooms(building_name: *const c_char) -> *mut c_char {
    if building_name.is_null() {
        warn!("arxos_list_rooms: null building_name");
        return create_error_response(MobileError::InvalidData("Null building_name".to_string()));
    }
    
    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_list_rooms: invalid UTF-8 in building_name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8".to_string()));
        }
    };

    let result = crate::mobile_ffi::list_rooms(building_str.to_string());
    create_json_response(result)
}

/// Get a specific room by ID
///
/// # Safety
/// The building_name and room_id parameters must be valid UTF-8 null-terminated strings
#[no_mangle]
pub unsafe extern "C" fn arxos_get_room(
    building_name: *const c_char,
    room_id: *const c_char
) -> *mut c_char {
    if building_name.is_null() {
        warn!("arxos_get_room: null building_name");
        return create_error_response(MobileError::InvalidData("Null building_name".to_string()));
    }
    
    if room_id.is_null() {
        warn!("arxos_get_room: null room_id");
        return create_error_response(MobileError::InvalidData("Null room_id".to_string()));
    }
    
    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_get_room: invalid UTF-8 in building_name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in building_name".to_string()));
        }
    };
    
    let room_id_str = match CStr::from_ptr(room_id).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_get_room: invalid UTF-8 in room_id");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in room_id".to_string()));
        }
    };
    
    let result = crate::mobile_ffi::get_room(building_str.to_string(), room_id_str.to_string());
    create_json_response(result)
}

/// List all equipment in a building
///
/// # Safety
/// The building_name parameter must be a valid UTF-8 null-terminated string
#[no_mangle]
pub unsafe extern "C" fn arxos_list_equipment(building_name: *const c_char) -> *mut c_char {
    if building_name.is_null() {
        warn!("arxos_list_equipment: null building_name");
        return create_error_response(MobileError::InvalidData("Null building_name".to_string()));
    }
    
    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_list_equipment: invalid UTF-8 in building_name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8".to_string()));
        }
    };
    
    let result = crate::mobile_ffi::list_equipment(building_str.to_string());
    create_json_response(result)
}

/// Get a specific equipment item by ID
///
/// # Safety
/// The building_name and equipment_id parameters must be valid UTF-8 null-terminated strings
#[no_mangle]
pub unsafe extern "C" fn arxos_get_equipment(
    building_name: *const c_char,
    equipment_id: *const c_char
) -> *mut c_char {
    if building_name.is_null() {
        warn!("arxos_get_equipment: null building_name");
        return create_error_response(MobileError::InvalidData("Null building_name".to_string()));
    }
    
    if equipment_id.is_null() {
        warn!("arxos_get_equipment: null equipment_id");
        return create_error_response(MobileError::InvalidData("Null equipment_id".to_string()));
    }
    
    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_get_equipment: invalid UTF-8 in building_name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in building_name".to_string()));
        }
    };
    
    let equipment_id_str = match CStr::from_ptr(equipment_id).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_get_equipment: invalid UTF-8 in equipment_id");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in equipment_id".to_string()));
        }
    };
    
    let result = crate::mobile_ffi::get_equipment(building_str.to_string(), equipment_id_str.to_string());
    create_json_response(result)
}

/// Parse AR scan data from JSON string
///
/// Returns parsed AR scan data as JSON
#[no_mangle]
pub unsafe extern "C" fn arxos_parse_ar_scan(json_data: *const c_char) -> *mut c_char {
    if json_data.is_null() {
        warn!("arxos_parse_ar_scan: null json_data");
        return create_error_response(MobileError::InvalidData("Null json_data".to_string()));
    }
    
    let json_str = match CStr::from_ptr(json_data).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_parse_ar_scan: invalid UTF-8");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8".to_string()));
        }
    };

    let result = crate::mobile_ffi::parse_ar_scan(json_str);
    create_json_response(result)
}

/// Process AR scan and extract equipment
///
/// Returns equipment info list as JSON
#[no_mangle]
pub unsafe extern "C" fn arxos_extract_equipment(json_data: *const c_char) -> *mut c_char {
    if json_data.is_null() {
        warn!("arxos_extract_equipment: null json_data");
        return create_error_response(MobileError::InvalidData("Null json_data".to_string()));
    }
    
    let json_str = match CStr::from_ptr(json_data).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_extract_equipment: invalid UTF-8");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8".to_string()));
        }
    };

    // Parse AR scan
    match crate::mobile_ffi::parse_ar_scan(json_str) {
        Ok(scan_data) => {
            // Extract equipment
            let equipment = crate::mobile_ffi::extract_equipment_from_ar_scan(&scan_data);
            
            // Return as JSON
            match serde_json::to_string(&equipment) {
                Ok(json) => create_safe_c_string(json),
                Err(e) => {
                    warn!("Failed to serialize equipment: {}", e);
                    create_safe_c_string(r#"{"error":"serialization failed"}"#.to_string())
                }
            }
        }
        Err(e) => create_error_response(e),
    }
}


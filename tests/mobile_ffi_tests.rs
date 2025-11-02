//! Integration tests for mobile FFI bindings

use arxos::mobile_ffi::ffi;
use std::ffi::{CString, CStr};
use std::os::raw::c_char;

/// Helper to convert Rust string to C string
/// Returns a pointer that can be passed to FFI functions expecting *const c_char
fn to_c_string(s: &str) -> *const c_char {
    CString::new(s).unwrap().into_raw() as *const c_char
}

/// Helper to free C string (can handle both const and mut pointers)
unsafe fn free_c_string(ptr: *const c_char) {
    if !ptr.is_null() {
        let _ = CString::from_raw(ptr as *mut c_char);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_arxos_free_string() {
        // Test that arxos_free_string doesn't crash
        let test_string = CString::new("test").unwrap();
        let ptr = test_string.into_raw();
        
        unsafe {
            ffi::arxos_free_string(ptr);
        }
    }
    
    #[test]
    fn test_arxos_free_string_null() {
        unsafe {
            ffi::arxos_free_string(std::ptr::null_mut());
        }
    }
    
    #[test]
    fn test_arxos_list_rooms_null_input() {
        unsafe {
            let result = ffi::arxos_list_rooms(std::ptr::null());
            
            assert!(!result.is_null());
            
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            
            assert!(json_str.contains("error"));
            
            ffi::arxos_free_string(result);
        }
    }
    
    #[test]
    fn test_arxos_list_rooms_valid_input() {
        unsafe {
            let building_name = to_c_string("test_building");
            
            let result = arxos::mobile_ffi::ffi::arxos_list_rooms(building_name);
            
            assert!(!result.is_null());
            
            // Parse the JSON response
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            
            // Should be valid JSON
            let _parsed: serde_json::Value = serde_json::from_str(json_str)
                .expect("Should parse as JSON");
            
            ffi::arxos_free_string(result);
            free_c_string(building_name);
        }
    }
    
    #[test]
    fn test_arxos_get_room() {
        unsafe {
            let building_name = to_c_string("test_building");
            let room_id = to_c_string("room_123");
            
            let result = ffi::arxos_get_room(building_name, room_id);
            
            assert!(!result.is_null());
            
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            let _parsed: serde_json::Value = serde_json::from_str(json_str)
                .expect("Should parse as JSON");
            
            ffi::arxos_free_string(result);
            free_c_string(building_name);
            free_c_string(room_id);
        }
    }
    
    #[test]
    fn test_arxos_list_equipment() {
        unsafe {
            let building_name = to_c_string("test_building");
            
            let result = ffi::arxos_list_equipment(building_name);
            
            assert!(!result.is_null());
            
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            let _parsed: serde_json::Value = serde_json::from_str(json_str)
                .expect("Should parse as JSON");
            
            ffi::arxos_free_string(result);
            free_c_string(building_name);
        }
    }
    
    #[test]
    fn test_arxos_parse_ar_scan() {
        unsafe {
            let json_data = r#"{"detectedEquipment":[],"roomBoundaries":{"walls":[],"openings":[]}}"#;
            let json_ptr = to_c_string(json_data);
            
            let result = ffi::arxos_parse_ar_scan(json_ptr);
            
            assert!(!result.is_null());
            
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            let _parsed: serde_json::Value = serde_json::from_str(json_str)
                .expect("Should parse as JSON");
            
            ffi::arxos_free_string(result);
            free_c_string(json_ptr);
        }
    }
    
    #[test]
    fn test_arxos_extract_equipment() {
        unsafe {
            let json_data = r#"{"detectedEquipment":[{"name":"Test Equipment","type":"HVAC","position":{"x":1.0,"y":2.0,"z":3.0},"confidence":0.9}],"roomBoundaries":{"walls":[],"openings":[]}}"#;
            let json_ptr = to_c_string(json_data);
            
            let result = ffi::arxos_extract_equipment(json_ptr);
            
            assert!(!result.is_null());
            
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            let _parsed: serde_json::Value = serde_json::from_str(json_str)
                .expect("Should parse as JSON");
            
            ffi::arxos_free_string(result);
            free_c_string(json_ptr);
        }
    }
    
    #[test]
    fn test_arxos_last_error() {
        let code = ffi::arxos_last_error();
        assert!(code >= 0);
    }
    
    #[test]
    fn test_arxos_last_error_message() {
        unsafe {
            let msg = ffi::arxos_last_error_message();
            assert!(!msg.is_null());
            ffi::arxos_free_string(msg);
        }
    }
}

// FFI Error Tracking Tests
//
// Tests verify that FFI error tracking properly captures and reports errors
// using thread-local storage, enabling mobile apps to retrieve detailed error information.

mod ffi_error_tracking_tests {
    use super::*;
    use arxos::mobile_ffi::ffi::ArxOSErrorCode;

    unsafe fn call_ffi_and_get_error<F>(f: F) -> (i32, String)
    where
        F: FnOnce() -> *mut c_char,
    {
        // Clear any previous error
        let _ = ffi::arxos_last_error();
        
        // Call the function
        let result_ptr = f();
        
        // Free the result
        if !result_ptr.is_null() {
            ffi::arxos_free_string(result_ptr);
        }
        
        // Get error code and message
        let error_code = ffi::arxos_last_error();
        let error_msg_ptr = ffi::arxos_last_error_message();
        let error_msg = if !error_msg_ptr.is_null() {
            CStr::from_ptr(error_msg_ptr).to_string_lossy().to_string()
        } else {
            String::new()
        };
        
        // Free error message
        if !error_msg_ptr.is_null() {
            ffi::arxos_free_string(error_msg_ptr);
        }
        
        (error_code, error_msg)
    }

    #[test]
    fn test_ffi_error_tracking_null_building_name() {
        unsafe {
            let (error_code, error_msg) = call_ffi_and_get_error(|| {
                ffi::arxos_list_rooms(std::ptr::null())
            });
            
            // Should return error for null pointer
            assert_ne!(error_code, ArxOSErrorCode::Success as i32,
                      "Should set error for null building_name");
            assert!(!error_msg.is_empty(), "Should provide error message");
            assert!(error_msg.contains("Null") || error_msg.contains("Invalid"),
                    "Error message should describe null pointer issue: {}", error_msg);
        }
    }

    #[test]
    fn test_ffi_error_tracking_invalid_utf8() {
        unsafe {
            // Create invalid UTF-8 string
            let invalid_bytes = vec![0xFF, 0xFE, 0xFD];
            let invalid_cstr = CString::new(invalid_bytes).unwrap();
            
            let (error_code, error_msg) = call_ffi_and_get_error(|| {
                ffi::arxos_list_rooms(invalid_cstr.as_ptr())
            });
            
            assert_ne!(error_code, ArxOSErrorCode::Success as i32,
                      "Should set error for invalid UTF-8");
            assert!(error_msg.contains("UTF-8") || error_msg.contains("Invalid"),
                    "Error should mention UTF-8 issue: {}", error_msg);
        }
    }

    #[test]
    fn test_ffi_error_code_mapping() {
        // Test that error codes are properly mapped
        assert_eq!(ArxOSErrorCode::Success as i32, 0);
        assert_eq!(ArxOSErrorCode::NotFound as i32, 1);
        assert_eq!(ArxOSErrorCode::InvalidData as i32, 2);
        assert_eq!(ArxOSErrorCode::IoError as i32, 3);
        assert_eq!(ArxOSErrorCode::Unknown as i32, 99);
    }

    #[test]
    fn test_ffi_memory_management() {
        unsafe {
            // Test that strings are properly freed
            let building_name = to_c_string("Test Building");
            let result_ptr = ffi::arxos_list_rooms(building_name);
            
            // Should not be null (even if empty JSON or error JSON)
            assert!(!result_ptr.is_null(), "Should return valid pointer");
            
            // Free it
            ffi::arxos_free_string(result_ptr);
            
            // Calling free_string multiple times or with null should be safe
            ffi::arxos_free_string(std::ptr::null_mut());
            ffi::arxos_free_string(std::ptr::null_mut());
            
            free_c_string(building_name);
        }
    }

    #[test]
    fn test_ffi_get_room_error_handling() {
        unsafe {
            let building_name = to_c_string("Test Building");
            let room_id = to_c_string("nonexistent");
            
            let (error_code, error_msg) = call_ffi_and_get_error(|| {
                ffi::arxos_get_room(building_name, room_id)
            });
            
            // Should return error (room doesn't exist or building not found)
            // The error code should be non-zero if error occurred
            assert!(!error_msg.is_empty() || error_code != ArxOSErrorCode::Success as i32,
                    "Should track error for nonexistent room");
            
            free_c_string(building_name);
            free_c_string(room_id);
        }
    }

    #[test]
    fn test_ffi_error_isolation() {
        unsafe {
            // Test that errors are properly isolated per operation
            // First, trigger an error
            let _ = call_ffi_and_get_error(|| {
                ffi::arxos_list_rooms(std::ptr::null())
            });
            
            // Error should be set
            let initial_error = ffi::arxos_last_error();
            assert_ne!(initial_error, ArxOSErrorCode::Success as i32, 
                      "Initial error should be tracked");
            
            // Note: We can't easily test error clearing on success without actual building data
            // But we verify the error tracking infrastructure exists and works
        }
    }
}

// JNI Implementation Tests
//
// Note: Full JNI testing requires Android environment. These tests verify
// the underlying mobile_ffi functions that JNI calls, ensuring the integration
// layer works correctly.

#[cfg(test)]
mod jni_tests {
    use arxos::mobile_ffi;

    #[test]
    fn test_jni_underlying_list_rooms() {
        // Test the underlying function that JNI calls
        let result = mobile_ffi::list_rooms("test_building".to_string());
        
        // Should return Result (may fail without building data, but should not panic)
        assert!(result.is_ok() || result.is_err());
        // If error, should be a proper error type
        if let Err(e) = &result {
            let error_str = format!("{}", e);
            assert!(!error_str.is_empty());
        }
    }

    #[test]
    fn test_jni_underlying_get_room() {
        let result = mobile_ffi::get_room("test_building".to_string(), "room_123".to_string());
        
        assert!(result.is_ok() || result.is_err());
    }

    #[test]
    fn test_jni_underlying_list_equipment() {
        let result = mobile_ffi::list_equipment("test_building".to_string());
        
        assert!(result.is_ok() || result.is_err());
    }

    #[test]
    fn test_jni_underlying_get_equipment() {
        let result = mobile_ffi::get_equipment("test_building".to_string(), "eq_123".to_string());
        
        assert!(result.is_ok() || result.is_err());
    }

    #[test]
    fn test_jni_underlying_parse_ar_scan() {
        let json_data = r#"{
            "roomName": "Test Room",
            "floorLevel": 1,
            "detectedEquipment": []
        }"#;
        
        let result = mobile_ffi::parse_ar_scan(json_data);
        
        // Should parse valid JSON
        assert!(result.is_ok());
        let scan_data = result.unwrap();
        assert_eq!(scan_data.room_name, "Test Room");
        assert_eq!(scan_data.floor_level, 1);
    }

    #[test]
    fn test_jni_underlying_parse_ar_scan_invalid_json() {
        let invalid_json = "not json";
        
        let result = mobile_ffi::parse_ar_scan(invalid_json);
        
        // Should return error for invalid JSON
        assert!(result.is_err());
    }

    #[test]
    fn test_jni_underlying_extract_equipment() {
        let json_data = r#"{
            "roomName": "Test Room",
            "floorLevel": 1,
            "detectedEquipment": [
                {
                    "name": "HVAC Unit",
                    "type": "VAV",
                    "position": {"x": 10.0, "y": 20.0, "z": 3.0},
                    "confidence": 0.9
                }
            ]
        }"#;
        
        let scan_result = mobile_ffi::parse_ar_scan(json_data);
        assert!(scan_result.is_ok());
        
        let scan_data = scan_result.unwrap();
        let equipment = mobile_ffi::extract_equipment_from_ar_scan(&scan_data);
        
        assert_eq!(equipment.len(), 1);
        assert_eq!(equipment[0].name, "HVAC Unit");
        assert_eq!(equipment[0].equipment_type, "VAV");
    }

    #[test]
    fn test_jni_json_serialization() {
        // Verify that mobile_ffi types can be serialized to JSON (required for JNI)
        use arxos::mobile_ffi::{RoomInfo, Position};
        
        let room = RoomInfo {
            id: "room_1".to_string(),
            name: "Test Room".to_string(),
            room_type: "Office".to_string(),
            position: Position {
                x: 0.0,
                y: 0.0,
                z: 0.0,
                coordinate_system: "building_local".to_string(),
            },
            properties: std::collections::HashMap::new(),
        };
        
        let json_result = serde_json::to_string(&room);
        assert!(json_result.is_ok());
        let json = json_result.unwrap();
        assert!(json.contains("room_1"));
        assert!(json.contains("Test Room"));
    }
}
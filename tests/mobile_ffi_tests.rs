//! Integration tests for mobile FFI bindings

use arxos::mobile_ffi::ffi;
use std::ffi::{CString, CStr};
use std::os::raw::c_char;

/// Helper to convert Rust string to C string
fn to_c_string(s: &str) -> *const c_char {
    CString::new(s).unwrap().into_raw()
}

/// Helper to free C string
unsafe fn free_c_string(ptr: *mut c_char) {
    if !ptr.is_null() {
        let _ = CString::from_raw(ptr);
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
        let msg = ffi::arxos_last_error_message();
        assert!(!msg.is_null());
        ffi::arxos_free_string(msg);
    }
}

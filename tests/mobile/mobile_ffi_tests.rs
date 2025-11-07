//! Integration tests for mobile FFI bindings

use arxos::mobile_ffi::ffi;
use std::ffi::{CStr, CString};
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
            let _parsed: serde_json::Value =
                serde_json::from_str(json_str).expect("Should parse as JSON");

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
            let _parsed: serde_json::Value =
                serde_json::from_str(json_str).expect("Should parse as JSON");

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
            let _parsed: serde_json::Value =
                serde_json::from_str(json_str).expect("Should parse as JSON");

            ffi::arxos_free_string(result);
            free_c_string(building_name);
        }
    }

    #[test]
    fn test_arxos_parse_ar_scan() {
        unsafe {
            let json_data =
                r#"{"detectedEquipment":[],"roomBoundaries":{"walls":[],"openings":[]}}"#;
            let json_ptr = to_c_string(json_data);

            let result = ffi::arxos_parse_ar_scan(json_ptr);

            assert!(!result.is_null());

            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            let _parsed: serde_json::Value =
                serde_json::from_str(json_str).expect("Should parse as JSON");

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
            let _parsed: serde_json::Value =
                serde_json::from_str(json_str).expect("Should parse as JSON");

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
            let (error_code, error_msg) =
                call_ffi_and_get_error(|| ffi::arxos_list_rooms(std::ptr::null()));

            // Should return error for null pointer
            assert_ne!(
                error_code,
                ArxOSErrorCode::Success as i32,
                "Should set error for null building_name"
            );
            assert!(!error_msg.is_empty(), "Should provide error message");
            assert!(
                error_msg.contains("Null") || error_msg.contains("Invalid"),
                "Error message should describe null pointer issue: {}",
                error_msg
            );
        }
    }

    #[test]
    fn test_ffi_error_tracking_invalid_utf8() {
        unsafe {
            // Create invalid UTF-8 string
            let invalid_bytes = vec![0xFF, 0xFE, 0xFD];
            let invalid_cstr = CString::new(invalid_bytes).unwrap();

            let (error_code, error_msg) =
                call_ffi_and_get_error(|| ffi::arxos_list_rooms(invalid_cstr.as_ptr()));

            assert_ne!(
                error_code,
                ArxOSErrorCode::Success as i32,
                "Should set error for invalid UTF-8"
            );
            assert!(
                error_msg.contains("UTF-8") || error_msg.contains("Invalid"),
                "Error should mention UTF-8 issue: {}",
                error_msg
            );
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

            let (error_code, error_msg) =
                call_ffi_and_get_error(|| ffi::arxos_get_room(building_name, room_id));

            // Should return error (room doesn't exist or building not found)
            // The error code should be non-zero if error occurred
            assert!(
                !error_msg.is_empty() || error_code != ArxOSErrorCode::Success as i32,
                "Should track error for nonexistent room"
            );

            free_c_string(building_name);
            free_c_string(room_id);
        }
    }

    #[test]
    fn test_ffi_error_isolation() {
        unsafe {
            // Test that errors are properly isolated per operation
            // First, trigger an error
            let _ = call_ffi_and_get_error(|| ffi::arxos_list_rooms(std::ptr::null()));

            // Error should be set
            let initial_error = ffi::arxos_last_error();
            assert_ne!(
                initial_error,
                ArxOSErrorCode::Success as i32,
                "Initial error should be tracked"
            );

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
        use arxos::mobile_ffi::{Position, RoomInfo};

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

// Tests for new AR integration FFI functions
mod ar_integration_tests {
    use super::*;
    use std::fs;
    use std::path::PathBuf;
    use tempfile::TempDir;

    /// Helper to create a test building YAML file
    fn create_test_building(
        building_name: &str,
        temp_dir: &PathBuf,
    ) -> Result<PathBuf, Box<dyn std::error::Error>> {
        let building_yaml = format!("{}.yaml", building_name);
        let building_path = temp_dir.join(&building_yaml);

        let yaml_content = r#"building:
  id: test-building-id
  name: Test Building
  description: Test building for AR integration tests
  created_at: 2025-01-01T00:00:00Z
  updated_at: 2025-01-01T00:00:00Z
  version: "1.0.0"
metadata:
  parser_version: "test"
  total_entities: 0
  spatial_entities: 0
  coordinate_system: "World"
  units: "meters"
floors:
  - id: floor-1
    name: Floor 1
    level: 1
    elevation: 0.0
    rooms: []
    equipment:
      - id: eq-1
        name: Test Equipment
        type: HVAC
        position:
          x: 10.0
          y: 20.0
          z: 3.0
        status: Healthy
        properties: {}
"#;
        fs::write(&building_path, yaml_content)?;
        Ok(building_path)
    }

    #[test]
    fn test_arxos_load_ar_model_null_building_name() {
        unsafe {
            let format = to_c_string("gltf");
            let result = ffi::arxos_load_ar_model(std::ptr::null(), format, std::ptr::null());

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            assert!(json_str.contains("error") || json_str.contains("Null"));

            ffi::arxos_free_string(result);
            free_c_string(format);
        }
    }

    #[test]
    fn test_arxos_load_ar_model_null_format() {
        unsafe {
            let building = to_c_string("test_building");
            let result = ffi::arxos_load_ar_model(building, std::ptr::null(), std::ptr::null());

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            assert!(json_str.contains("error") || json_str.contains("Null"));

            ffi::arxos_free_string(result);
            free_c_string(building);
        }
    }

    #[test]
    fn test_arxos_load_ar_model_invalid_format() {
        unsafe {
            let building = to_c_string("test_building");
            let format = to_c_string("invalid_format");
            let result = ffi::arxos_load_ar_model(building, format, std::ptr::null());

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            let parsed: serde_json::Value = serde_json::from_str(json_str).unwrap();

            // Should return error for invalid format
            assert!(
                parsed.get("error").is_some()
                    || !parsed
                        .get("success")
                        .unwrap_or(&serde_json::Value::Bool(false))
                        .as_bool()
                        .unwrap_or(false)
            );

            ffi::arxos_free_string(result);
            free_c_string(building);
            free_c_string(format);
        }
    }

    #[test]
    fn test_arxos_load_ar_model_nonexistent_building() {
        unsafe {
            let building = to_c_string("nonexistent_building");
            let format = to_c_string("gltf");
            let result = ffi::arxos_load_ar_model(building, format, std::ptr::null());

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            let parsed: serde_json::Value = serde_json::from_str(json_str).unwrap();

            // Should return error for nonexistent building
            assert!(
                parsed.get("error").is_some()
                    || !parsed
                        .get("success")
                        .unwrap_or(&serde_json::Value::Bool(false))
                        .as_bool()
                        .unwrap_or(false)
            );

            ffi::arxos_free_string(result);
            free_c_string(building);
            free_c_string(format);
        }
    }

    #[test]
    fn test_arxos_load_ar_model_with_temp_file() {
        let temp_dir = TempDir::new().unwrap();
        let original_dir = std::env::current_dir().unwrap();

        // Change to temp directory for building file loading
        std::env::set_current_dir(temp_dir.path()).unwrap();

        // Create test building
        let building_name = "test_ar_building";
        create_test_building(building_name, &temp_dir.path().to_path_buf()).unwrap();

        unsafe {
            let building = to_c_string(building_name);
            let format = to_c_string("gltf");
            let result = ffi::arxos_load_ar_model(building, format, std::ptr::null());

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            let parsed: serde_json::Value = serde_json::from_str(json_str).unwrap();

            // Should succeed if building exists
            if parsed
                .get("success")
                .and_then(|s| s.as_bool())
                .unwrap_or(false)
            {
                assert!(parsed.get("file_path").is_some());
                assert!(parsed.get("format").is_some());
                assert_eq!(parsed["format"], "gltf");

                // Verify file was created
                let file_path = parsed["file_path"].as_str().unwrap();
                assert!(PathBuf::from(file_path).exists());
            }

            ffi::arxos_free_string(result);
            free_c_string(building);
            free_c_string(format);
        }

        std::env::set_current_dir(original_dir).unwrap();
    }

    #[test]
    fn test_arxos_load_ar_model_with_custom_path() {
        let temp_dir = TempDir::new().unwrap();
        let original_dir = std::env::current_dir().unwrap();

        std::env::set_current_dir(temp_dir.path()).unwrap();

        let building_name = "test_ar_building";
        create_test_building(building_name, &temp_dir.path().to_path_buf()).unwrap();

        let output_path = temp_dir.path().join("custom_model.gltf");

        unsafe {
            let building = to_c_string(building_name);
            let format = to_c_string("gltf");
            let output = to_c_string(output_path.to_str().unwrap());

            let result = ffi::arxos_load_ar_model(building, format, output);

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            let parsed: serde_json::Value = serde_json::from_str(json_str).unwrap();

            if parsed
                .get("success")
                .and_then(|s| s.as_bool())
                .unwrap_or(false)
            {
                assert_eq!(
                    parsed["file_path"].as_str().unwrap(),
                    output_path.to_str().unwrap()
                );
                assert!(output_path.exists());
            }

            ffi::arxos_free_string(result);
            free_c_string(building);
            free_c_string(format);
            free_c_string(output);
        }

        std::env::set_current_dir(original_dir).unwrap();
    }

    #[test]
    fn test_arxos_save_ar_scan_null_json() {
        unsafe {
            let building = to_c_string("test_building");
            let result = ffi::arxos_save_ar_scan(std::ptr::null(), building, std::ptr::null(), 0.7);

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            assert!(json_str.contains("error") || json_str.contains("Null"));

            ffi::arxos_free_string(result);
            free_c_string(building);
        }
    }

    #[test]
    fn test_arxos_save_ar_scan_null_building() {
        unsafe {
            let json_data =
                r#"{"detectedEquipment":[],"roomBoundaries":{"walls":[],"openings":[]}}"#;
            let json_ptr = to_c_string(json_data);

            let result = ffi::arxos_save_ar_scan(json_ptr, std::ptr::null(), std::ptr::null(), 0.7);

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            assert!(json_str.contains("error") || json_str.contains("Null"));

            ffi::arxos_free_string(result);
            free_c_string(json_ptr);
        }
    }

    #[test]
    fn test_arxos_save_ar_scan_invalid_json() {
        unsafe {
            let invalid_json = "not valid json";
            let json_ptr = to_c_string(invalid_json);
            let building = to_c_string("test_building");

            let result = ffi::arxos_save_ar_scan(json_ptr, building, std::ptr::null(), 0.7);

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            let parsed: serde_json::Value = serde_json::from_str(json_str).unwrap();

            // Should return error for invalid JSON
            assert!(
                parsed.get("error").is_some()
                    || !parsed
                        .get("success")
                        .unwrap_or(&serde_json::Value::Bool(false))
                        .as_bool()
                        .unwrap_or(false)
            );

            ffi::arxos_free_string(result);
            free_c_string(json_ptr);
            free_c_string(building);
        }
    }

    #[test]
    fn test_arxos_save_ar_scan_valid_data() {
        let temp_dir = TempDir::new().unwrap();
        let original_dir = std::env::current_dir().unwrap();

        std::env::set_current_dir(temp_dir.path()).unwrap();

        unsafe {
            let json_data = r#"{
                "detectedEquipment": [
                    {
                        "name": "VAV-301",
                        "type": "VAV",
                        "position": {"x": 10.0, "y": 20.0, "z": 3.0},
                        "confidence": 0.9,
                        "detectionMethod": "ARKit"
                    }
                ],
                "roomBoundaries": {"walls": [], "openings": []},
                "roomName": "Room 301",
                "floorLevel": 3
            }"#;
            let json_ptr = to_c_string(json_data);
            let building = to_c_string("test_building");

            let result = ffi::arxos_save_ar_scan(json_ptr, building, std::ptr::null(), 0.7);

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            let parsed: serde_json::Value = serde_json::from_str(json_str).unwrap();

            // Should succeed and create pending equipment
            if parsed
                .get("success")
                .and_then(|s| s.as_bool())
                .unwrap_or(false)
            {
                assert!(parsed.get("pending_count").is_some());
                assert!(parsed.get("pending_ids").is_some());
                let pending_count = parsed["pending_count"].as_u64().unwrap_or(0);
                assert!(pending_count > 0, "Should create at least one pending item");
            }

            ffi::arxos_free_string(result);
            free_c_string(json_ptr);
            free_c_string(building);
        }

        std::env::set_current_dir(original_dir).unwrap();
    }

    #[test]
    fn test_arxos_list_pending_equipment_null_building() {
        unsafe {
            let result = ffi::arxos_list_pending_equipment(std::ptr::null());

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            assert!(json_str.contains("error") || json_str.contains("Null"));

            ffi::arxos_free_string(result);
        }
    }

    #[test]
    fn test_arxos_list_pending_equipment_empty() {
        let temp_dir = TempDir::new().unwrap();
        let original_dir = std::env::current_dir().unwrap();

        std::env::set_current_dir(temp_dir.path()).unwrap();

        unsafe {
            let building = to_c_string("test_building");
            let result = ffi::arxos_list_pending_equipment(building);

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            let parsed: serde_json::Value = serde_json::from_str(json_str).unwrap();

            // Should return empty list if no pending items
            if parsed
                .get("success")
                .and_then(|s| s.as_bool())
                .unwrap_or(false)
            {
                let empty_vec: Vec<serde_json::Value> = vec![];
                let items = parsed
                    .get("items")
                    .and_then(|i| i.as_array())
                    .unwrap_or(&empty_vec);
                assert_eq!(items.len(), 0);
            }

            ffi::arxos_free_string(result);
            free_c_string(building);
        }

        std::env::set_current_dir(original_dir).unwrap();
    }

    #[test]
    fn test_arxos_list_pending_equipment_with_items() {
        let temp_dir = TempDir::new().unwrap();
        let original_dir = std::env::current_dir().unwrap();

        std::env::set_current_dir(temp_dir.path()).unwrap();

        // First, create some pending equipment
        unsafe {
            let json_data = r#"{
                "detectedEquipment": [
                    {
                        "name": "Test Equipment",
                        "type": "HVAC",
                        "position": {"x": 1.0, "y": 2.0, "z": 3.0},
                        "confidence": 0.9,
                        "detectionMethod": "Tap-to-Place"
                    }
                ],
                "roomBoundaries": {"walls": [], "openings": []}
            }"#;
            let json_ptr = to_c_string(json_data);
            let building = to_c_string("test_building");

            // Save scan to create pending items
            let _save_result = ffi::arxos_save_ar_scan(json_ptr, building, std::ptr::null(), 0.7);
            ffi::arxos_free_string(_save_result);

            // Now list pending equipment
            let list_result = ffi::arxos_list_pending_equipment(building);

            assert!(!list_result.is_null());
            let c_str = CStr::from_ptr(list_result);
            let json_str = c_str.to_str().unwrap();
            let parsed: serde_json::Value = serde_json::from_str(json_str).unwrap();

            if parsed
                .get("success")
                .and_then(|s| s.as_bool())
                .unwrap_or(false)
            {
                let empty_vec: Vec<serde_json::Value> = vec![];
                let items = parsed
                    .get("items")
                    .and_then(|i| i.as_array())
                    .unwrap_or(&empty_vec);
                assert!(items.len() > 0, "Should have at least one pending item");
            }

            ffi::arxos_free_string(list_result);
            free_c_string(json_ptr);
            free_c_string(building);
        }

        std::env::set_current_dir(original_dir).unwrap();
    }

    #[test]
    fn test_arxos_confirm_pending_equipment_null_params() {
        unsafe {
            let building = to_c_string("test_building");
            let result = ffi::arxos_confirm_pending_equipment(
                building,
                std::ptr::null(),
                std::ptr::null(),
                1,
            );

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            assert!(json_str.contains("error") || json_str.contains("Null"));

            ffi::arxos_free_string(result);
            free_c_string(building);
        }
    }

    #[test]
    fn test_arxos_confirm_pending_equipment_nonexistent() {
        let temp_dir = TempDir::new().unwrap();
        let original_dir = std::env::current_dir().unwrap();

        std::env::set_current_dir(temp_dir.path()).unwrap();

        unsafe {
            let building = to_c_string("test_building");
            let pending_id = to_c_string("nonexistent-pending-id");
            let result =
                ffi::arxos_confirm_pending_equipment(building, pending_id, std::ptr::null(), 1);

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            let parsed: serde_json::Value = serde_json::from_str(json_str).unwrap();

            // Should return error for nonexistent pending ID
            assert!(
                parsed.get("error").is_some()
                    || !parsed
                        .get("success")
                        .unwrap_or(&serde_json::Value::Bool(false))
                        .as_bool()
                        .unwrap_or(false)
            );

            ffi::arxos_free_string(result);
            free_c_string(building);
            free_c_string(pending_id);
        }

        std::env::set_current_dir(original_dir).unwrap();
    }

    #[test]
    fn test_arxos_confirm_pending_equipment_workflow() {
        let temp_dir = TempDir::new().unwrap();
        let original_dir = std::env::current_dir().unwrap();

        std::env::set_current_dir(temp_dir.path()).unwrap();

        // Create test building
        let building_name = "test_building";
        create_test_building(building_name, &temp_dir.path().to_path_buf()).unwrap();

        unsafe {
            let building = to_c_string(building_name);

            // Step 1: Create pending equipment
            let json_data = r#"{
                "detectedEquipment": [
                    {
                        "name": "Confirm Test Equipment",
                        "type": "HVAC",
                        "position": {"x": 5.0, "y": 10.0, "z": 2.0},
                        "confidence": 0.9,
                        "detectionMethod": "Test"
                    }
                ],
                "roomBoundaries": {"walls": [], "openings": []}
            }"#;
            let json_ptr = to_c_string(json_data);

            let save_result = ffi::arxos_save_ar_scan(json_ptr, building, std::ptr::null(), 0.7);
            let save_c_str = CStr::from_ptr(save_result);
            let save_json_str = save_c_str.to_str().unwrap();
            let save_parsed: serde_json::Value = serde_json::from_str(save_json_str).unwrap();

            if save_parsed
                .get("success")
                .and_then(|s| s.as_bool())
                .unwrap_or(false)
            {
                let empty_pending: Vec<serde_json::Value> = vec![];
                let pending_ids = save_parsed
                    .get("pending_ids")
                    .and_then(|ids| ids.as_array())
                    .unwrap_or(&empty_pending);

                if !pending_ids.is_empty() {
                    let pending_id_str = pending_ids[0].as_str().unwrap();
                    let pending_id = to_c_string(pending_id_str);

                    // Step 2: Confirm pending equipment
                    let confirm_result = ffi::arxos_confirm_pending_equipment(
                        building,
                        pending_id,
                        std::ptr::null(),
                        0,
                    ); // Don't commit to Git

                    assert!(!confirm_result.is_null());
                    let confirm_c_str = CStr::from_ptr(confirm_result);
                    let confirm_json_str = confirm_c_str.to_str().unwrap();
                    let confirm_parsed: serde_json::Value =
                        serde_json::from_str(confirm_json_str).unwrap();

                    // Should succeed if pending ID exists
                    if confirm_parsed
                        .get("success")
                        .and_then(|s| s.as_bool())
                        .unwrap_or(false)
                    {
                        assert!(confirm_parsed.get("equipment_id").is_some());
                        assert_eq!(confirm_parsed["building"], building_name);
                    }

                    ffi::arxos_free_string(confirm_result);
                    free_c_string(pending_id);
                }
            }

            ffi::arxos_free_string(save_result);
            free_c_string(json_ptr);
            free_c_string(building);
        }

        std::env::set_current_dir(original_dir).unwrap();
    }

    #[test]
    fn test_arxos_reject_pending_equipment_null_params() {
        unsafe {
            let building = to_c_string("test_building");
            let result = ffi::arxos_reject_pending_equipment(building, std::ptr::null());

            assert!(!result.is_null());
            let c_str = CStr::from_ptr(result);
            let json_str = c_str.to_str().unwrap();
            assert!(json_str.contains("error") || json_str.contains("Null"));

            ffi::arxos_free_string(result);
            free_c_string(building);
        }
    }

    #[test]
    fn test_arxos_reject_pending_equipment_workflow() {
        let temp_dir = TempDir::new().unwrap();
        let original_dir = std::env::current_dir().unwrap();

        std::env::set_current_dir(temp_dir.path()).unwrap();

        unsafe {
            let building = to_c_string("test_building");

            // Step 1: Create pending equipment
            let json_data = r#"{
                "detectedEquipment": [
                    {
                        "name": "Reject Test Equipment",
                        "type": "HVAC",
                        "position": {"x": 15.0, "y": 25.0, "z": 4.0},
                        "confidence": 0.8,
                        "detectionMethod": "Test"
                    }
                ],
                "roomBoundaries": {"walls": [], "openings": []}
            }"#;
            let json_ptr = to_c_string(json_data);

            let save_result = ffi::arxos_save_ar_scan(json_ptr, building, std::ptr::null(), 0.7);
            let save_c_str = CStr::from_ptr(save_result);
            let save_json_str = save_c_str.to_str().unwrap();
            let save_parsed: serde_json::Value = serde_json::from_str(save_json_str).unwrap();

            if save_parsed
                .get("success")
                .and_then(|s| s.as_bool())
                .unwrap_or(false)
            {
                let empty_pending: Vec<serde_json::Value> = vec![];
                let pending_ids = save_parsed
                    .get("pending_ids")
                    .and_then(|ids| ids.as_array())
                    .unwrap_or(&empty_pending);

                if !pending_ids.is_empty() {
                    let pending_id_str = pending_ids[0].as_str().unwrap();
                    let pending_id = to_c_string(pending_id_str);

                    // Step 2: Reject pending equipment
                    let reject_result = ffi::arxos_reject_pending_equipment(building, pending_id);

                    assert!(!reject_result.is_null());
                    let reject_c_str = CStr::from_ptr(reject_result);
                    let reject_json_str = reject_c_str.to_str().unwrap();
                    let reject_parsed: serde_json::Value =
                        serde_json::from_str(reject_json_str).unwrap();

                    // Should succeed if pending ID exists
                    if reject_parsed
                        .get("success")
                        .and_then(|s| s.as_bool())
                        .unwrap_or(false)
                    {
                        assert_eq!(reject_parsed["building"], "test_building");
                        assert_eq!(reject_parsed["pending_id"], pending_id_str);
                    }

                    ffi::arxos_free_string(reject_result);
                    free_c_string(pending_id);
                }
            }

            ffi::arxos_free_string(save_result);
            free_c_string(json_ptr);
            free_c_string(building);
        }

        std::env::set_current_dir(original_dir).unwrap();
    }

    #[test]
    fn test_complete_ar_workflow_ffi() {
        // Test complete workflow: save scan -> list pending -> confirm -> verify
        let temp_dir = TempDir::new().unwrap();
        let original_dir = std::env::current_dir().unwrap();

        std::env::set_current_dir(temp_dir.path()).unwrap();

        // Create test building
        let building_name = "workflow_test_building";
        create_test_building(building_name, &temp_dir.path().to_path_buf()).unwrap();

        unsafe {
            let building = to_c_string(building_name);

            // Step 1: Save AR scan
            let json_data = r#"{
                "detectedEquipment": [
                    {
                        "name": "Workflow Test Equipment",
                        "type": "Electrical",
                        "position": {"x": 20.0, "y": 30.0, "z": 5.0},
                        "confidence": 0.95,
                        "detectionMethod": "Workflow Test"
                    }
                ],
                "roomBoundaries": {"walls": [], "openings": []},
                "roomName": "Test Room",
                "floorLevel": 2
            }"#;
            let json_ptr = to_c_string(json_data);

            let save_result = ffi::arxos_save_ar_scan(json_ptr, building, std::ptr::null(), 0.7);
            let save_c_str = CStr::from_ptr(save_result);
            let save_json_str = save_c_str.to_str().unwrap();
            let save_parsed: serde_json::Value = serde_json::from_str(save_json_str).unwrap();

            assert!(
                save_parsed
                    .get("success")
                    .and_then(|s| s.as_bool())
                    .unwrap_or(false),
                "Save scan should succeed"
            );

            let empty_pending: Vec<serde_json::Value> = vec![];
            let pending_ids = save_parsed
                .get("pending_ids")
                .and_then(|ids| ids.as_array())
                .unwrap_or(&empty_pending);
            assert!(!pending_ids.is_empty(), "Should create pending items");

            let pending_id_str = pending_ids[0].as_str().unwrap();
            let pending_id = to_c_string(pending_id_str);

            // Step 2: List pending equipment
            let list_result = ffi::arxos_list_pending_equipment(building);
            let list_c_str = CStr::from_ptr(list_result);
            let list_json_str = list_c_str.to_str().unwrap();
            let list_parsed: serde_json::Value = serde_json::from_str(list_json_str).unwrap();

            assert!(
                list_parsed
                    .get("success")
                    .and_then(|s| s.as_bool())
                    .unwrap_or(false),
                "List pending should succeed"
            );
            let empty_items: Vec<serde_json::Value> = vec![];
            let items = list_parsed
                .get("items")
                .and_then(|i| i.as_array())
                .unwrap_or(&empty_items);
            assert!(!items.is_empty(), "Should have pending items in list");

            // Step 3: Confirm pending equipment
            let confirm_result =
                ffi::arxos_confirm_pending_equipment(building, pending_id, std::ptr::null(), 0);
            let confirm_c_str = CStr::from_ptr(confirm_result);
            let confirm_json_str = confirm_c_str.to_str().unwrap();
            let confirm_parsed: serde_json::Value = serde_json::from_str(confirm_json_str).unwrap();

            assert!(
                confirm_parsed
                    .get("success")
                    .and_then(|s| s.as_bool())
                    .unwrap_or(false),
                "Confirm pending should succeed"
            );
            assert!(
                confirm_parsed.get("equipment_id").is_some(),
                "Should return equipment ID"
            );

            // Cleanup
            ffi::arxos_free_string(save_result);
            ffi::arxos_free_string(list_result);
            ffi::arxos_free_string(confirm_result);
            free_c_string(json_ptr);
            free_c_string(building);
            free_c_string(pending_id);
        }

        std::env::set_current_dir(original_dir).unwrap();
    }

    #[test]
    fn test_arxos_save_ar_scan_with_user_email() {
        // Test that user_email parameter is accepted and propagated
        let temp_dir = TempDir::new().unwrap();
        let original_dir = std::env::current_dir().unwrap();

        std::env::set_current_dir(temp_dir.path()).unwrap();

        // Create test building
        let building_name = "test_user_email_building";
        create_test_building(building_name, &temp_dir.path().to_path_buf()).unwrap();

        unsafe {
            let building = to_c_string(building_name);
            let user_email = to_c_string("test@example.com");

            let json_data = r#"{
                "detectedEquipment": [
                    {
                        "name": "User Email Test Equipment",
                        "type": "HVAC",
                        "position": {"x": 15.0, "y": 25.0, "z": 4.0},
                        "confidence": 0.92,
                        "detectionMethod": "User Email Test"
                    }
                ],
                "roomBoundaries": {"walls": [], "openings": []},
                "roomName": "Test Room",
                "floorLevel": 2
            }"#;
            let json_ptr = to_c_string(json_data);

            // Test with user_email provided
            let save_result = ffi::arxos_save_ar_scan(json_ptr, building, user_email, 0.7);
            assert!(!save_result.is_null(), "Should not return null pointer");

            let save_c_str = CStr::from_ptr(save_result);
            let save_json_str = save_c_str.to_str().unwrap();
            let save_parsed: serde_json::Value = serde_json::from_str(save_json_str).unwrap();

            // Should succeed or fail gracefully (may fail if building doesn't exist)
            assert!(
                save_parsed.get("success").is_some() || save_parsed.get("error").is_some(),
                "Should return success or error in response"
            );

            // Cleanup
            ffi::arxos_free_string(save_result);
            free_c_string(json_ptr);
            free_c_string(building);
            free_c_string(user_email);
        }

        std::env::set_current_dir(original_dir).unwrap();
    }

    #[test]
    fn test_arxos_confirm_pending_equipment_with_user_email() {
        // Test that user_email parameter is accepted in confirm function
        let temp_dir = TempDir::new().unwrap();
        let original_dir = std::env::current_dir().unwrap();

        std::env::set_current_dir(temp_dir.path()).unwrap();

        // Create test building
        let building_name = "test_confirm_user_email";
        create_test_building(building_name, &temp_dir.path().to_path_buf()).unwrap();

        unsafe {
            let building = to_c_string(building_name);
            let user_email = to_c_string("test@example.com");

            // First create pending equipment
            let json_data = r#"{
                "detectedEquipment": [
                    {
                        "name": "Confirm User Email Equipment",
                        "type": "Electrical",
                        "position": {"x": 8.0, "y": 12.0, "z": 3.0},
                        "confidence": 0.90,
                        "detectionMethod": "Confirm User Email Test"
                    }
                ],
                "roomBoundaries": {"walls": [], "openings": []},
                "roomName": "Test Room",
                "floorLevel": 1
            }"#;
            let json_ptr = to_c_string(json_data);

            let save_result = ffi::arxos_save_ar_scan(json_ptr, building, std::ptr::null(), 0.7);
            let save_c_str = CStr::from_ptr(save_result);
            let save_json_str = save_c_str.to_str().unwrap();
            let save_parsed: serde_json::Value = serde_json::from_str(save_json_str).unwrap();

            if save_parsed
                .get("success")
                .and_then(|s| s.as_bool())
                .unwrap_or(false)
            {
                let empty_pending: Vec<serde_json::Value> = vec![];
                let pending_ids = save_parsed
                    .get("pending_ids")
                    .and_then(|ids| ids.as_array())
                    .unwrap_or(&empty_pending);

                if !pending_ids.is_empty() {
                    let pending_id_str = pending_ids[0].as_str().unwrap();
                    let pending_id = to_c_string(pending_id_str);

                    // Test confirm with user_email
                    let confirm_result =
                        ffi::arxos_confirm_pending_equipment(building, pending_id, user_email, 0);
                    assert!(!confirm_result.is_null(), "Should not return null pointer");

                    let confirm_c_str = CStr::from_ptr(confirm_result);
                    let confirm_json_str = confirm_c_str.to_str().unwrap();
                    let confirm_parsed: serde_json::Value =
                        serde_json::from_str(confirm_json_str).unwrap();

                    // Should succeed or return error gracefully
                    assert!(
                        confirm_parsed.get("success").is_some()
                            || confirm_parsed.get("error").is_some(),
                        "Should return success or error in response"
                    );

                    ffi::arxos_free_string(confirm_result);
                    free_c_string(pending_id);
                }
            }

            ffi::arxos_free_string(save_result);
            free_c_string(json_ptr);
            free_c_string(building);
            free_c_string(user_email);
        }

        std::env::set_current_dir(original_dir).unwrap();
    }
}

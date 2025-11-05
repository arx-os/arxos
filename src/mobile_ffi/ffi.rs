//! C FFI bindings for mobile applications
//!
//! This module provides C-compatible function exports for iOS and Android.

use std::ffi::{CString, CStr};
use std::os::raw::c_char;
use std::cell::RefCell;
use serde_json;
use log::{warn, info};

use crate::mobile_ffi::MobileError;

/// FFI error code enumeration
#[repr(C)]
#[derive(Clone, Copy)]
pub enum ArxOSErrorCode {
    Success = 0,
    NotFound = 1,
    InvalidData = 2,
    IoError = 3,
    Unknown = 99,
}

thread_local! {
    static LAST_ERROR: RefCell<Option<(ArxOSErrorCode, String)>> = const { RefCell::new(None) };
}

/// Set the last error in thread-local storage
fn set_last_error(code: ArxOSErrorCode, message: String) {
    LAST_ERROR.with(|e| {
        *e.borrow_mut() = Some((code, message));
    });
}

/// Clear the last error (call on successful operations)
fn clear_last_error() {
    LAST_ERROR.with(|e| {
        *e.borrow_mut() = None;
    });
}

/// Convert MobileError to ArxOSErrorCode
fn mobile_error_to_code(error: &MobileError) -> ArxOSErrorCode {
    match error {
        MobileError::NotFound(_) => ArxOSErrorCode::NotFound,
        MobileError::InvalidData(_) => ArxOSErrorCode::InvalidData,
        MobileError::IoError(_) => ArxOSErrorCode::IoError,
    }
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
            clear_last_error(); // Clear error on success
            match serde_json::to_string(&data) {
                Ok(json) => create_safe_c_string(json),
                Err(e) => {
                    warn!("Failed to serialize response: {}", e);
                    let error_msg = format!("Serialization failed: {}", e);
                    set_last_error(ArxOSErrorCode::IoError, error_msg.clone());
                    create_safe_c_string(r#"{"error":"serialization failed"}"#.to_string())
                }
            }
        }
        Err(e) => {
            warn!("FFI error: {:?}", e);
            let error_msg = format!("{}", e);
            let error_code = mobile_error_to_code(&e);
            set_last_error(error_code, error_msg.clone());
            create_safe_c_string(format!(r#"{{"error":"{}"}}"#, e))
        }
    }
}

// Game system FFI functions

/// Load a PR for review (game mode)
///
/// Returns JSON with PR summary including validation results
#[no_mangle]
pub unsafe extern "C" fn arxos_load_pr(
    pr_id: *const c_char,
    pr_dir: *const c_char,
    building_name: *const c_char,
) -> *mut c_char {
    use crate::game::pr_game::PRReviewGame;
    use std::path::Path;
    
    if pr_id.is_null() || building_name.is_null() {
        set_last_error(ArxOSErrorCode::InvalidData, "Null pointer provided".to_string());
        return create_safe_c_string(r#"{"error":"null pointer"}"#.to_string());
    }

    let pr_id_str = match CStr::from_ptr(pr_id).to_str() {
        Ok(s) => s,
        Err(_) => {
            set_last_error(ArxOSErrorCode::InvalidData, "Invalid PR ID string".to_string());
            return create_safe_c_string(r#"{"error":"invalid pr_id"}"#.to_string());
        }
    };

    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            set_last_error(ArxOSErrorCode::InvalidData, "Invalid building name string".to_string());
            return create_safe_c_string(r#"{"error":"invalid building_name"}"#.to_string());
        }
    };

    // Determine PR directory
    let pr_dir_path = if pr_dir.is_null() {
        Path::new("prs").join(format!("pr_{}", pr_id_str))
    } else {
        match CStr::from_ptr(pr_dir).to_str() {
            Ok(s) => Path::new(s).to_path_buf(),
            Err(_) => {
                set_last_error(ArxOSErrorCode::InvalidData, "Invalid PR directory string".to_string());
                return create_safe_c_string(r#"{"error":"invalid pr_dir"}"#.to_string());
            }
        }
    };

    // Load PR review game
    match PRReviewGame::new(pr_id_str, &pr_dir_path) {
        Ok(mut review_game) => {
            // Validate PR
            review_game.validate_pr();
            let summary = review_game.get_validation_summary();

            // Get game state for equipment list
            let game_state = review_game.game_state();
            let equipment: Vec<serde_json::Value> = game_state.placements.iter().map(|p| {
                serde_json::json!({
                    "id": p.equipment.id,
                    "name": p.equipment.name,
                    "type": format!("{:?}", p.equipment.equipment_type),
                    "position": {
                        "x": p.equipment.position.x,
                        "y": p.equipment.position.y,
                        "z": p.equipment.position.z,
                    },
                    "validation": {
                        "is_valid": p.constraint_validation.is_valid,
                        "violations": p.constraint_validation.violations.len(),
                    }
                })
            }).collect();

            let response = serde_json::json!({
                "pr_id": pr_id_str,
                "building": building_str,
                "total_items": summary.total_items,
                "valid_items": summary.valid_items,
                "items_with_violations": summary.items_with_violations,
                "total_violations": summary.total_violations,
                "critical_violations": summary.critical_violations,
                "warnings": summary.warnings,
                "equipment": equipment,
            });

            clear_last_error();
            create_safe_c_string(serde_json::to_string(&response).unwrap_or_else(|_| r#"{"error":"serialization failed"}"#.to_string()))
        }
        Err(e) => {
            warn!("Failed to load PR: {}", e);
            set_last_error(ArxOSErrorCode::NotFound, format!("PR not found: {}", e));
            create_safe_c_string(format!(r#"{{"error":"failed to load pr: {}"}}"#, e))
        }
    }
}

/// Validate equipment placement against constraints
///
/// Returns JSON validation result with violations and suggestions
#[no_mangle]
pub unsafe extern "C" fn arxos_validate_constraints(
    equipment_json: *const c_char,
    constraints_json: *const c_char,
) -> *mut c_char {
    use crate::game::{ConstraintSystem, GameState, GameMode};
    use crate::game::types::GameEquipmentPlacement;
    use crate::core::{Equipment, EquipmentType, Position};
    use std::collections::HashMap;

    if equipment_json.is_null() {
        set_last_error(ArxOSErrorCode::InvalidData, "Null equipment_json".to_string());
        return create_safe_c_string(r#"{"error":"null equipment_json"}"#.to_string());
    }

    let equipment_str = match CStr::from_ptr(equipment_json).to_str() {
        Ok(s) => s,
        Err(_) => {
            set_last_error(ArxOSErrorCode::InvalidData, "Invalid equipment JSON".to_string());
            return create_safe_c_string(r#"{"error":"invalid equipment_json"}"#.to_string());
        }
    };

    // Parse equipment JSON
    let equipment_data: serde_json::Value = match serde_json::from_str(equipment_str) {
        Ok(d) => d,
        Err(e) => {
            set_last_error(ArxOSErrorCode::InvalidData, format!("Failed to parse equipment JSON: {}", e));
            return create_safe_c_string(format!(r#"{{"error":"parse error: {}"}}"#, e));
        }
    };

    // Create equipment from JSON
    let name = equipment_data.get("name")
        .and_then(|v| v.as_str())
        .unwrap_or("Unknown")
        .to_string();

    let eq_type_str = equipment_data.get("type")
        .and_then(|v| v.as_str())
        .unwrap_or("Other");

    let equipment_type = match eq_type_str {
        "HVAC" => EquipmentType::HVAC,
        "Electrical" => EquipmentType::Electrical,
        "AV" => EquipmentType::AV,
        "Plumbing" => EquipmentType::Plumbing,
        "Network" => EquipmentType::Network,
        _ => EquipmentType::Other(eq_type_str.to_string()),
    };

    let pos_data = match equipment_data.get("position") {
        Some(p) => p,
        None => {
            set_last_error(ArxOSErrorCode::InvalidData, "Missing position in equipment JSON".to_string());
            return create_safe_c_string(r#"{"error":"missing position"}"#.to_string());
        }
    };
    let x = pos_data.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0);
    let y = pos_data.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0);
    let z = pos_data.get("z").and_then(|v| v.as_f64()).unwrap_or(0.0);

    let name_clone = name.clone();
    let equipment = Equipment {
        id: equipment_data.get("id")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string())
            .unwrap_or_else(|| uuid::Uuid::new_v4().to_string()),
        name: name_clone.clone(),
        path: format!("/equipment/{}", name_clone.to_lowercase().replace(" ", "-")),
        address: None,
        equipment_type,
        position: Position {
            x,
            y,
            z,
            coordinate_system: "building_local".to_string(),
        },
        properties: HashMap::new(),
        status: crate::core::EquipmentStatus::Active,
        room_id: None,
    };

    // Create placement
    let placement = GameEquipmentPlacement {
        equipment,
        ifc_entity_id: None,
        ifc_entity_type: None,
        ifc_placement_chain: None,
        ifc_original_properties: HashMap::new(),
        game_action: crate::game::types::GameAction::Placed,
        constraint_validation: crate::game::types::ValidationResult::default(),
    };

    // Load constraints if provided
    let constraint_system = if !constraints_json.is_null() {
        match CStr::from_ptr(constraints_json).to_str() {
            Ok(json_str) => {
                match ConstraintSystem::load_from_json(json_str) {
                    Ok(system) => {
                        info!("Successfully loaded constraints from JSON");
                        system
                    }
                    Err(e) => {
                        warn!("Failed to parse constraints JSON: {} - using empty constraint system", e);
                        ConstraintSystem::new()
                    }
                }
            }
            Err(_) => {
                warn!("Failed to convert constraints JSON C string to Rust string - using empty constraint system");
                ConstraintSystem::new()
            }
        }
    } else {
        ConstraintSystem::new()
    };

    // Validate
    let game_state = GameState::new(GameMode::Planning);
    let validation_result = constraint_system.validate_placement(&placement, &game_state);

    // Build response
    let violations: Vec<serde_json::Value> = validation_result.violations.iter().map(|v| {
        serde_json::json!({
            "constraint_id": v.constraint_id,
            "type": format!("{:?}", v.constraint_type),
            "severity": format!("{:?}", v.severity),
            "message": v.message,
            "suggestion": v.suggestion,
        })
    }).collect();

    let response = serde_json::json!({
        "is_valid": validation_result.is_valid,
        "violations": violations,
        "warnings": validation_result.warnings,
    });

    clear_last_error();
    create_safe_c_string(serde_json::to_string(&response).unwrap_or_else(|_| r#"{"error":"serialization failed"}"#.to_string()))
}

/// Get game plan from planning session
///
/// Returns JSON with plan data, placements, and validation summary
#[no_mangle]
pub unsafe extern "C" fn arxos_get_game_plan(
    session_id: *const c_char,
    building_name: *const c_char,
) -> *mut c_char {
    use crate::game::planning::PlanningGame;

    if building_name.is_null() {
        set_last_error(ArxOSErrorCode::InvalidData, "Null pointer provided".to_string());
        return create_safe_c_string(r#"{"error":"null pointer"}"#.to_string());
    }

    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            set_last_error(ArxOSErrorCode::InvalidData, "Invalid building name".to_string());
            return create_safe_c_string(r#"{"error":"invalid building_name"}"#.to_string());
        }
    };

    // Parse session_id if provided
    // Currently, PlanningGame creates a new session each time.
    // The session_id parameter is accepted for API compatibility.
    // Session persistence functionality uses this parameter when available.
    let _session_id = if !session_id.is_null() {
        CStr::from_ptr(session_id).to_str().ok()
    } else {
        None
    };

    match PlanningGame::new(building_str) {
        Ok(planning_game) => {
            let game_state = planning_game.game_state();
            let summary = planning_game.get_validation_summary();

            let placements: Vec<serde_json::Value> = game_state.placements.iter().map(|p| {
                serde_json::json!({
                    "id": p.equipment.id,
                    "name": p.equipment.name,
                    "type": format!("{:?}", p.equipment.equipment_type),
                    "position": {
                        "x": p.equipment.position.x,
                        "y": p.equipment.position.y,
                        "z": p.equipment.position.z,
                    },
                    "validation": {
                        "is_valid": p.constraint_validation.is_valid,
                        "violations": p.constraint_validation.violations.len(),
                    }
                })
            }).collect();

            let response = serde_json::json!({
                "session_id": planning_game.session_id(),
                "building": building_str,
                "placements": placements,
                "validation_summary": {
                    "total_placements": summary.total_placements,
                    "valid_placements": summary.valid_placements,
                    "invalid_placements": summary.invalid_placements,
                    "total_violations": summary.total_violations,
                    "critical_violations": summary.critical_violations,
                    "warnings": summary.warnings,
                    "score": summary.score,
                }
            });

            clear_last_error();
            create_safe_c_string(serde_json::to_string(&response).unwrap_or_else(|_| r#"{"error":"serialization failed"}"#.to_string()))
        }
        Err(e) => {
            warn!("Failed to get game plan: {}", e);
            set_last_error(ArxOSErrorCode::NotFound, format!("Failed to load plan: {}", e));
            create_safe_c_string(format!(r#"{{"error":"failed to load plan: {}"}}"#, e))
        }
    }
}

/// Create an error response string
fn create_error_response(error: MobileError) -> *mut c_char {
    warn!("FFI error: {:?}", error);
    let error_msg = format!("{}", error);
    let error_code = mobile_error_to_code(&error);
    set_last_error(error_code, error_msg.clone());
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
    LAST_ERROR.with(|e| {
        e.borrow()
            .as_ref()
            .map(|(code, _)| *code as i32)
            .unwrap_or(ArxOSErrorCode::Success as i32)
    })
}

/// Get the last error message
#[no_mangle]
pub extern "C" fn arxos_last_error_message() -> *mut c_char {
    LAST_ERROR.with(|e| {
        e.borrow()
            .as_ref()
            .map(|(_, msg)| create_safe_c_string(msg.clone()))
            .unwrap_or_else(|| {
                // Return empty string if no error
                CString::new("")
                    .expect("Empty string must always be valid for CString")
                    .into_raw()
            })
    })
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
                Ok(json) => {
                    clear_last_error(); // Clear error on success
                    create_safe_c_string(json)
                }
                Err(e) => {
                    warn!("Failed to serialize equipment: {}", e);
                    let error_msg = format!("Serialization failed: {}", e);
                    set_last_error(ArxOSErrorCode::IoError, error_msg.clone());
                    create_safe_c_string(r#"{"error":"serialization failed"}"#.to_string())
                }
            }
        }
        Err(e) => create_error_response(e),
    }
}

/// Process AR scan and create pending equipment items
///
/// # Arguments
/// * `json_data` - JSON string of AR scan data from mobile
/// * `building_name` - Name of building for context
/// * `confidence_threshold` - Minimum confidence (0.0-1.0) to create pending items
///
/// Returns JSON with pending equipment IDs and details
#[no_mangle]
pub unsafe extern "C" fn arxos_process_ar_scan_to_pending(
    json_data: *const c_char,
    building_name: *const c_char,
    confidence_threshold: f64,
) -> *mut c_char {
    use crate::ar_integration::processing;
    use crate::spatial::Point3D;
    
    if json_data.is_null() || building_name.is_null() {
        warn!("arxos_process_ar_scan_to_pending: null parameter");
        return create_error_response(MobileError::InvalidData("Null parameter".to_string()));
    }
    
    let json_str = match CStr::from_ptr(json_data).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_process_ar_scan_to_pending: invalid UTF-8 in JSON");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in JSON".to_string()));
        }
    };
    
    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_process_ar_scan_to_pending: invalid UTF-8 in building name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in building name".to_string()));
        }
    };
    
    // Parse AR scan from mobile FFI format
    match crate::mobile_ffi::parse_ar_scan(json_str) {
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
            match processing::process_ar_scan_to_pending(&processing_scan, building_str, confidence_threshold, None) {
                Ok(pending_ids) => {
                    let response = serde_json::json!({
                        "success": true,
                        "pending_count": pending_ids.len(),
                        "pending_ids": pending_ids,
                        "building": building_str,
                        "confidence_threshold": confidence_threshold,
                    });
                    
                    clear_last_error();
                    match serde_json::to_string(&response) {
                        Ok(json) => create_safe_c_string(json),
                        Err(e) => {
                            warn!("Failed to serialize response: {}", e);
                            create_error_response(MobileError::IoError(format!("Serialization error: {}", e)))
                        }
                    }
                }
                Err(e) => {
                    warn!("Failed to process AR scan: {}", e);
                    create_error_response(MobileError::IoError(format!("Processing failed: {}", e)))
                }
            }
        }
        Err(e) => {
            warn!("Failed to parse AR scan: {}", e);
            create_error_response(e)
        }
    }
}

/// Export building to AR-compatible format
///
/// # Arguments
/// * `building_name` - Name of building to export
/// * `format` - Export format: "gltf" or "usdz"
///
/// Returns JSON with export status and file path
#[no_mangle]
pub unsafe extern "C" fn arxos_export_for_ar(
    building_name: *const c_char,
    format: *const c_char,
) -> *mut c_char {
    use crate::export::ar::{ARExporter, ARFormat};
    use std::path::Path;
    
    if building_name.is_null() || format.is_null() {
        warn!("arxos_export_for_ar: null parameter");
        return create_error_response(MobileError::InvalidData("Null parameter".to_string()));
    }
    
    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_export_for_ar: invalid UTF-8 in building name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8".to_string()));
        }
    };
    
    let format_str = match CStr::from_ptr(format).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_export_for_ar: invalid UTF-8 in format");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in format".to_string()));
        }
    };
    
    // Load building data
    let building_data = match crate::utils::loading::load_building_data(building_str) {
        Ok(data) => data,
        Err(e) => {
            warn!("Failed to load building data: {}", e);
            return create_error_response(MobileError::NotFound(format!("Building not found: {}", e)));
        }
    };
    
    // Parse format
    let ar_format = match format_str.parse::<ARFormat>() {
        Ok(fmt) => fmt,
        Err(e) => {
            warn!("Invalid AR format: {}", e);
            return create_error_response(MobileError::InvalidData(format!("Invalid format: {}", e)));
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
            
            clear_last_error();
            match serde_json::to_string(&response) {
                Ok(json) => create_safe_c_string(json),
                Err(e) => {
                    warn!("Failed to serialize response: {}", e);
                    create_error_response(MobileError::IoError(format!("Serialization error: {}", e)))
                }
            }
        }
        Err(e) => {
            warn!("Failed to export building: {}", e);
            create_error_response(MobileError::IoError(format!("Export failed: {}", e)))
        }
    }
}

/// Load/export building model for AR viewing
///
/// This function exports a building to AR-compatible format (USDZ or glTF) and returns
/// the file path where the model was saved. If `output_path` is null, a temporary file
/// will be created in the system temp directory.
///
/// # Arguments
/// * `building_name` - Name of building to export
/// * `format` - Export format: "usdz" or "gltf" (case-insensitive)
/// * `output_path` - Optional path where model should be saved (null for temp file)
///
/// # Returns
/// JSON string with:
/// ```json
/// {
///   "success": true,
///   "building": "building_name",
///   "format": "usdz",
///   "file_path": "/path/to/model.usdz",
///   "file_size": 12345,
///   "message": "Model exported successfully"
/// }
/// ```
///
/// # Safety
/// This function is FFI-safe and handles null pointers gracefully.
#[no_mangle]
pub unsafe extern "C" fn arxos_load_ar_model(
    building_name: *const c_char,
    format: *const c_char,
    output_path: *const c_char,
) -> *mut c_char {
    use crate::export::ar::{ARExporter, ARFormat};
    use std::path::PathBuf;
    use std::fs;
    use uuid::Uuid;
    
    // Validate required parameters
    if building_name.is_null() || format.is_null() {
        warn!("arxos_load_ar_model: null parameter");
        return create_error_response(MobileError::InvalidData("Null parameter".to_string()));
    }
    
    // Parse building name
    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_load_ar_model: invalid UTF-8 in building name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in building name".to_string()));
        }
    };
    
    // Parse format
    let format_str = match CStr::from_ptr(format).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_load_ar_model: invalid UTF-8 in format");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in format".to_string()));
        }
    };
    
    // Parse AR format enum
    let ar_format = match format_str.parse::<ARFormat>() {
        Ok(fmt) => fmt,
        Err(e) => {
            warn!("arxos_load_ar_model: invalid AR format: {}", e);
            return create_error_response(MobileError::InvalidData(format!("Invalid format '{}': {}", format_str, e)));
        }
    };
    
    // Determine output path
    let output_path_buf: PathBuf = if output_path.is_null() {
        // Create temporary file in system temp directory
        let temp_dir = std::env::temp_dir();
        let file_extension = match ar_format {
            ARFormat::GLTF => "gltf",
            ARFormat::USDZ => "usdz",
        };
        let temp_filename = format!("arxos_{}_{}.{}", building_str, Uuid::new_v4(), file_extension);
        temp_dir.join(temp_filename)
    } else {
        // Use provided path
        match CStr::from_ptr(output_path).to_str() {
            Ok(s) => PathBuf::from(s),
            Err(_) => {
                warn!("arxos_load_ar_model: invalid UTF-8 in output_path");
                return create_error_response(MobileError::InvalidData("Invalid UTF-8 in output_path".to_string()));
            }
        }
    };
    
    // Load building data
    let building_data = match crate::utils::loading::load_building_data(building_str) {
        Ok(data) => data,
        Err(e) => {
            warn!("arxos_load_ar_model: failed to load building data: {}", e);
            return create_error_response(MobileError::NotFound(format!("Building '{}' not found: {}", building_str, e)));
        }
    };
    
    // Create exporter and export
    let exporter = ARExporter::new(building_data);
    match exporter.export(ar_format, &output_path_buf) {
        Ok(_) => {
            // Get file size
            let file_size = match fs::metadata(&output_path_buf) {
                Ok(metadata) => metadata.len(),
                Err(e) => {
                    warn!("arxos_load_ar_model: failed to get file metadata: {}", e);
                    // Continue with 0 size, not critical
                    0
                }
            };
            
            // Convert path to string for JSON response
            let file_path_str = match output_path_buf.to_str() {
                Some(s) => s.to_string(),
                None => {
                    warn!("arxos_load_ar_model: output path contains invalid UTF-8");
                    return create_error_response(MobileError::IoError("Output path contains invalid UTF-8".to_string()));
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
            
            clear_last_error();
            match serde_json::to_string(&response) {
                Ok(json) => {
                    info!("arxos_load_ar_model: successfully exported building '{}' to {}", building_str, file_path_str);
                    create_safe_c_string(json)
                }
                Err(e) => {
                    warn!("arxos_load_ar_model: failed to serialize response: {}", e);
                    create_error_response(MobileError::IoError(format!("Serialization error: {}", e)))
                }
            }
        }
        Err(e) => {
            warn!("arxos_load_ar_model: failed to export building: {}", e);
            create_error_response(MobileError::IoError(format!("Export failed: {}", e)))
        }
    }
}

/// Save AR scan data and process to pending equipment
///
/// This function accepts AR scan data from mobile devices, optionally saves it to a file
/// for debugging/audit purposes, and processes it to create pending equipment items that
/// can be reviewed and confirmed by users.
///
/// # Arguments
/// * `json_data` - JSON string containing AR scan data (see ARScanData structure)
/// * `building_name` - Name of building for context
/// * `confidence_threshold` - Minimum confidence score (0.0-1.0) to create pending items
///
/// # Returns
/// JSON string with:
/// ```json
/// {
///   "success": true,
///   "building": "building_name",
///   "pending_count": 3,
///   "pending_ids": ["pending-1", "pending-2", "pending-3"],
///   "confidence_threshold": 0.7,
///   "scan_timestamp": "2025-11-03T14:30:00Z",
///   "message": "AR scan processed successfully"
/// }
/// ```
///
/// # Safety
/// This function is FFI-safe and handles null pointers gracefully.
#[no_mangle]
pub unsafe extern "C" fn arxos_save_ar_scan(
    json_data: *const c_char,
    building_name: *const c_char,
    user_email: *const c_char,  // NEW: User email from mobile app (can be null for backward compatibility)
    confidence_threshold: f64,
) -> *mut c_char {
    use crate::ar_integration::processing;
    use crate::spatial::Point3D;
    use chrono::Utc;
    use std::fs;
    use std::path::PathBuf;
    
    // Validate required parameters
    if json_data.is_null() || building_name.is_null() {
        warn!("arxos_save_ar_scan: null parameter");
        return create_error_response(MobileError::InvalidData("Null parameter".to_string()));
    }
    
    // Parse user_email (optional for backward compatibility)
    let user_email_str = if user_email.is_null() {
        // Fallback to config email
        crate::config::get_config_or_default().user.email.clone()
    } else {
        match CStr::from_ptr(user_email).to_str() {
            Ok(s) => s.to_string(),
            Err(_) => {
                warn!("arxos_save_ar_scan: invalid UTF-8 in user_email, using config email");
                crate::config::get_config_or_default().user.email.clone()
            }
        }
    };
    let user_email_opt = if user_email_str.is_empty() { None } else { Some(user_email_str) };
    // Validate confidence threshold
    if confidence_threshold < 0.0 || confidence_threshold > 1.0 {
        warn!("arxos_save_ar_scan: invalid confidence_threshold: {}", confidence_threshold);
        return create_error_response(MobileError::InvalidData(
            format!("Confidence threshold must be between 0.0 and 1.0, got: {}", confidence_threshold)
        ));
    }
    
    // Parse JSON data
    let json_str = match CStr::from_ptr(json_data).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_save_ar_scan: invalid UTF-8 in JSON data");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in JSON data".to_string()));
        }
    };
    
    // Parse building name
    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_save_ar_scan: invalid UTF-8 in building name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in building name".to_string()));
        }
    };
    
    // Parse AR scan from mobile FFI format
    let mobile_scan = match crate::mobile_ffi::parse_ar_scan(json_str) {
        Ok(scan) => scan,
        Err(e) => {
            warn!("arxos_save_ar_scan: failed to parse AR scan JSON: {}", e);
            return create_error_response(e);
        }
    };
    
    // Optionally save raw scan data to file for debugging/audit
    // Save to: {building_name}_scans/{timestamp}.json
    let scan_timestamp = Utc::now();
    let scan_save_result = {
        let scan_dir = PathBuf::from(format!("{}_scans", building_str));
        if let Err(e) = fs::create_dir_all(&scan_dir) {
            warn!("arxos_save_ar_scan: failed to create scan directory: {}", e);
            // Continue anyway, saving scan data is optional
        }
        
        let scan_filename = format!("scan_{}.json", scan_timestamp.format("%Y%m%d_%H%M%S"));
        let scan_path = scan_dir.join(scan_filename);
        
        match fs::write(&scan_path, json_str) {
            Ok(_) => {
                info!("arxos_save_ar_scan: saved raw scan data to {:?}", scan_path);
                Some(scan_path.to_string_lossy().to_string())
            }
            Err(e) => {
                warn!("arxos_save_ar_scan: failed to save scan data to file: {}", e);
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
    match processing::process_ar_scan_to_pending(&processing_scan, building_str, confidence_threshold, user_email_opt.clone()) {
        Ok(pending_ids) => {
            // Save pending equipment to storage for later review
            use crate::ar_integration::pending::PendingEquipmentManager;
            use std::path::PathBuf;
            
            let mut manager = PendingEquipmentManager::new(building_str.to_string());
            let storage_file = PathBuf::from(format!("{}_pending.json", building_str));
            
            // Load existing pending items
            if storage_file.exists() {
                if let Err(e) = manager.load_from_storage(&storage_file) {
                    warn!("arxos_save_ar_scan: failed to load existing pending items: {}", e);
                }
            }
            
            // Save pending equipment to storage
            // The pending equipment manager persists items to disk automatically.
            // The pending IDs are included in the response for immediate client access.
            // The list_pending_equipment function will load all pending items from persistent storage.
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
            
            clear_last_error();
            match serde_json::to_string(&response) {
                Ok(json) => {
                    info!(
                        "arxos_save_ar_scan: successfully processed AR scan for building '{}', created {} pending items",
                        building_str,
                        pending_ids.len()
                    );
                    create_safe_c_string(json)
                }
                Err(e) => {
                    warn!("arxos_save_ar_scan: failed to serialize response: {}", e);
                    create_error_response(MobileError::IoError(format!("Serialization error: {}", e)))
                }
            }
        }
        Err(e) => {
            warn!("arxos_save_ar_scan: failed to process AR scan: {}", e);
            create_error_response(MobileError::IoError(format!("Processing failed: {}", e)))
        }
    }
}

/// List pending equipment for a building
///
/// Returns all pending equipment items that need user confirmation.
///
/// # Arguments
/// * `building_name` - Name of building
///
/// # Returns
/// JSON string with pending equipment list
#[no_mangle]
pub unsafe extern "C" fn arxos_list_pending_equipment(
    building_name: *const c_char,
) -> *mut c_char {
    use crate::ar_integration::pending::PendingEquipmentManager;
    use std::path::PathBuf;
    
    if building_name.is_null() {
        warn!("arxos_list_pending_equipment: null building_name parameter");
        return create_error_response(MobileError::InvalidData("Null building_name parameter".to_string()));
    }
    
    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_list_pending_equipment: invalid UTF-8 in building_name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in building_name".to_string()));
        }
    };
    
    // Try to load pending equipment from storage
    let mut manager = PendingEquipmentManager::new(building_str.to_string());
    
    // Look for pending equipment storage file
    let storage_file = PathBuf::from(format!("{}_pending.json", building_str));
    if storage_file.exists() {
        if let Err(e) = manager.load_from_storage(&storage_file) {
            warn!("arxos_list_pending_equipment: failed to load from storage: {}", e);
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
        "pending_items": pending_list
    });
    
    clear_last_error();
    match serde_json::to_string(&response) {
        Ok(json) => {
            info!("arxos_list_pending_equipment: returned {} pending items", pending_list.len());
            create_safe_c_string(json)
        }
        Err(e) => {
            warn!("arxos_list_pending_equipment: failed to serialize response: {}", e);
            create_error_response(MobileError::IoError(format!("Serialization error: {}", e)))
        }
    }
}

/// Confirm pending equipment and add to building data
///
/// Confirms a pending equipment item, adds it to the building data, and optionally commits to Git.
///
/// # Arguments
/// * `building_name` - Name of building
/// * `pending_id` - ID of pending equipment to confirm
/// * `user_email` - User email from mobile app (can be null for backward compatibility)
/// * `commit_to_git` - Whether to commit changes to Git (1 = yes, 0 = no)
///
/// # Returns
/// JSON string with confirmation result
#[no_mangle]
pub unsafe extern "C" fn arxos_confirm_pending_equipment(
    building_name: *const c_char,
    pending_id: *const c_char,
    user_email: *const c_char,  // NEW: User email from mobile app (can be null for backward compatibility)
    commit_to_git: i32,
) -> *mut c_char {
    use crate::ar_integration::pending::PendingEquipmentManager;
    use crate::utils::loading::load_building_data;
    use crate::persistence::PersistenceManager;
    
    if building_name.is_null() || pending_id.is_null() {
        warn!("arxos_confirm_pending_equipment: null parameter");
        return create_error_response(MobileError::InvalidData("Null parameter".to_string()));
    }
    
    // Parse user_email (optional for backward compatibility)
    let user_email_str = if user_email.is_null() {
        // Fallback to config email
        crate::config::get_config_or_default().user.email.clone()
    } else {
        match CStr::from_ptr(user_email).to_str() {
            Ok(s) => s.to_string(),
            Err(_) => {
                warn!("arxos_confirm_pending_equipment: invalid UTF-8 in user_email, using config email");
                crate::config::get_config_or_default().user.email.clone()
            }
        }
    };
    let user_email_opt = if user_email_str.is_empty() { None } else { Some(user_email_str.as_str()) };
    
    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_confirm_pending_equipment: invalid UTF-8 in building_name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in building_name".to_string()));
        }
    };
    
    let pending_id_str = match CStr::from_ptr(pending_id).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_confirm_pending_equipment: invalid UTF-8 in pending_id");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in pending_id".to_string()));
        }
    };
    
    // Load pending equipment manager
    let mut manager = PendingEquipmentManager::new(building_str.to_string());
    let storage_file = std::path::PathBuf::from(format!("{}_pending.json", building_str));
    if storage_file.exists() {
        if let Err(e) = manager.load_from_storage(&storage_file) {
            warn!("arxos_confirm_pending_equipment: failed to load pending equipment: {}", e);
        }
    }
    
    // Load building data
    let mut building_data = match load_building_data(building_str) {
        Ok(data) => data,
        Err(e) => {
            warn!("arxos_confirm_pending_equipment: failed to load building data: {}", e);
            return create_error_response(MobileError::NotFound(format!("Building '{}' not found: {}", building_str, e)));
        }
    };
    
    // Get pending equipment to retrieve stored user_email (for attribution fallback)
    // Clone the user_email before calling confirm_pending (which borrows manager mutably)
    let stored_user_email = manager.get_pending(pending_id_str)
        .and_then(|p| p.user_email.clone());
    
    // Prefer provided user_email, fall back to stored user_email from scan
    let attribution_email = user_email_opt.or_else(|| stored_user_email.as_ref().map(|e| e.as_str()));
    
    // Confirm pending equipment
    match manager.confirm_pending(pending_id_str, &mut building_data) {
        Ok(equipment_id) => {
            // Save pending equipment state
            if let Err(e) = manager.save_to_storage_path(&storage_file) {
                warn!("arxos_confirm_pending_equipment: failed to save pending state: {}", e);
            }
            
            // Save building data and optionally commit to Git
            let commit_message = format!("Confirm pending equipment: {}", pending_id_str);
            let persistence_manager = match PersistenceManager::new(building_str) {
                Ok(pm) => pm,
                Err(e) => {
                    warn!("arxos_confirm_pending_equipment: failed to create persistence manager: {}", e);
                    return create_error_response(MobileError::IoError(format!("Persistence error: {}", e)));
                }
            };
            
            let commit_result = if commit_to_git != 0 {
                match persistence_manager.save_and_commit_with_user(&building_data, Some(&commit_message), attribution_email) {
                    Ok(commit_id) => Some(commit_id),
                    Err(e) => {
                        warn!("arxos_confirm_pending_equipment: failed to commit to Git: {}", e);
                        // Still save to file even if Git commit fails
                        if let Err(save_err) = persistence_manager.save_building_data(&building_data) {
                            warn!("arxos_confirm_pending_equipment: failed to save building data: {}", save_err);
                            return create_error_response(MobileError::IoError(format!("Failed to save: {}", save_err)));
                        }
                        None
                    }
                }
            } else {
                // Save to file only
                match persistence_manager.save_building_data(&building_data) {
                    Ok(_) => None,
                    Err(e) => {
                        warn!("arxos_confirm_pending_equipment: failed to save building data: {}", e);
                        return create_error_response(MobileError::IoError(format!("Failed to save: {}", e)));
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
            
            clear_last_error();
            match serde_json::to_string(&response) {
                Ok(json) => {
                    info!("arxos_confirm_pending_equipment: confirmed {} as {}", pending_id_str, equipment_id);
                    create_safe_c_string(json)
                }
                Err(e) => {
                    warn!("arxos_confirm_pending_equipment: failed to serialize response: {}", e);
                    create_error_response(MobileError::IoError(format!("Serialization error: {}", e)))
                }
            }
        }
        Err(e) => {
            warn!("arxos_confirm_pending_equipment: failed to confirm pending equipment: {}", e);
            create_error_response(MobileError::NotFound(format!("Failed to confirm: {}", e)))
        }
    }
}

/// Request user registration from mobile app
///
/// Creates a pending user registration request that will be reviewed by an admin.
///
/// # Arguments
/// * `building_name` - Name of building (repository)
/// * `email` - User's email address
/// * `name` - User's full name
/// * `organization` - Organization (optional, can be null)
/// * `role` - Role (optional, can be null)
/// * `phone` - Phone number (optional, can be null)
/// * `device_info` - Device information (optional, can be null)
/// * `app_version` - App version (optional, can be null)
///
/// # Returns
/// JSON string with request result (includes request_id and status)
///
/// # Safety
/// This function is FFI-safe and handles null pointers gracefully.
#[no_mangle]
pub unsafe extern "C" fn arxos_request_user_registration(
    building_name: *const c_char,
    email: *const c_char,
    name: *const c_char,
    organization: *const c_char,
    role: *const c_char,
    phone: *const c_char,
    device_info: *const c_char,
    app_version: *const c_char,
) -> *mut c_char {
    use crate::identity::PendingUserRequest;
    use crate::commands::git_ops::find_git_repository;
    
    // Validate required parameters
    if building_name.is_null() || email.is_null() || name.is_null() {
        warn!("arxos_request_user_registration: null required parameter");
        return create_error_response(MobileError::InvalidData("Null required parameter".to_string()));
    }
    
    // Parse building name
    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_request_user_registration: invalid UTF-8 in building_name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in building_name".to_string()));
        }
    };
    
    // Parse email
    let email_str = match CStr::from_ptr(email).to_str() {
        Ok(s) => s.to_string(),
        Err(_) => {
            warn!("arxos_request_user_registration: invalid UTF-8 in email");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in email".to_string()));
        }
    };
    
    // Parse name
    let name_str = match CStr::from_ptr(name).to_str() {
        Ok(s) => s.to_string(),
        Err(_) => {
            warn!("arxos_request_user_registration: invalid UTF-8 in name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in name".to_string()));
        }
    };
    
    // Parse optional parameters
    let organization_str = if organization.is_null() {
        None
    } else {
        CStr::from_ptr(organization).to_str().ok().map(|s| s.to_string())
    };
    
    let role_str = if role.is_null() {
        None
    } else {
        CStr::from_ptr(role).to_str().ok().map(|s| s.to_string())
    };
    
    let phone_str = if phone.is_null() {
        None
    } else {
        CStr::from_ptr(phone).to_str().ok().map(|s| s.to_string())
    };
    
    let device_info_str = if device_info.is_null() {
        None
    } else {
        CStr::from_ptr(device_info).to_str().ok().map(|s| s.to_string())
    };
    
    let app_version_str = if app_version.is_null() {
        None
    } else {
        CStr::from_ptr(app_version).to_str().ok().map(|s| s.to_string())
    };
    
    // Find Git repository
    let repo_path = match find_git_repository() {
        Ok(Some(path)) => std::path::PathBuf::from(path),
        Ok(None) => {
            warn!("arxos_request_user_registration: not in a Git repository");
            return create_error_response(MobileError::NotFound(
                "Not in a Git repository. User registration requires a Git repository.".to_string()
            ));
        }
        Err(e) => {
            warn!("arxos_request_user_registration: failed to find Git repository: {}", e);
            return create_error_response(MobileError::IoError(format!("Failed to find repository: {}", e)));
        }
    };
    
    // Load pending registry
    let mut pending_registry = match crate::identity::PendingUserRegistry::load(&repo_path) {
        Ok(registry) => registry,
        Err(e) => {
            warn!("arxos_request_user_registration: failed to load pending registry: {}", e);
            return create_error_response(MobileError::IoError(format!("Failed to load registry: {}", e)));
        }
    };
    
    // Create pending request
    let request = PendingUserRequest::new(
        email_str.clone(),
        name_str,
        organization_str,
        role_str,
        phone_str,
        device_info_str,
        app_version_str,
    );
    
    let request_id = request.id.clone();
    
    // Add request to registry
    match pending_registry.add_request(request) {
        Ok(_) => {
            // Save registry
            if let Err(e) = pending_registry.save() {
                warn!("arxos_request_user_registration: failed to save registry: {}", e);
                return create_error_response(MobileError::IoError(format!("Failed to save registry: {}", e)));
            }
            
            // Stage to Git
            let config = crate::git::GitConfigManager::load_from_arx_config_or_env();
            if let Ok(mut git_manager) = crate::git::BuildingGitManager::new(
                &repo_path.to_string_lossy(),
                building_str,
                config
            ) {
                if let Err(e) = git_manager.stage_file("pending-users.yaml") {
                    warn!("arxos_request_user_registration: failed to stage file: {}", e);
                    // Continue anyway - file is saved
                }
            }
            
            let response = serde_json::json!({
                "success": true,
                "request_id": request_id,
                "email": email_str,
                "status": "pending",
                "message": "Registration request submitted. Waiting for admin approval."
            });
            
            clear_last_error();
            match serde_json::to_string(&response) {
                Ok(json) => {
                    info!("arxos_request_user_registration: request submitted for {}", email_str);
                    create_safe_c_string(json)
                }
                Err(e) => {
                    warn!("arxos_request_user_registration: failed to serialize response: {}", e);
                    create_error_response(MobileError::IoError(format!("Serialization error: {}", e)))
                }
            }
        }
        Err(e) => {
            warn!("arxos_request_user_registration: failed to add request: {}", e);
            create_error_response(MobileError::InvalidData(format!("Failed to add request: {}", e)))
        }
    }
}

/// Check registration status for a mobile user
///
/// Returns the current status of a user's registration request.
///
/// # Arguments
/// * `building_name` - Name of building (repository)
/// * `email` - User's email address
///
/// # Returns
/// JSON string with registration status (pending, approved, denied, registered, or not_found)
///
/// # Safety
/// This function is FFI-safe and handles null pointers gracefully.
#[no_mangle]
pub unsafe extern "C" fn arxos_check_registration_status(
    building_name: *const c_char,
    email: *const c_char,
) -> *mut c_char {
    use crate::commands::git_ops::find_git_repository;
    
    // Validate required parameters
    if building_name.is_null() || email.is_null() {
        warn!("arxos_check_registration_status: null required parameter");
        return create_error_response(MobileError::InvalidData("Null required parameter".to_string()));
    }
    
    // Parse parameters
    let _building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_check_registration_status: invalid UTF-8 in building_name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in building_name".to_string()));
        }
    };
    
    let email_str = match CStr::from_ptr(email).to_str() {
        Ok(s) => s.to_string(),
        Err(_) => {
            warn!("arxos_check_registration_status: invalid UTF-8 in email");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in email".to_string()));
        }
    };
    
    // Find Git repository
    let repo_path = match find_git_repository() {
        Ok(Some(path)) => std::path::PathBuf::from(path),
        Ok(None) => {
            return create_error_response(MobileError::NotFound(
                "Not in a Git repository".to_string()
            ));
        }
        Err(e) => {
            warn!("arxos_check_registration_status: failed to find Git repository: {}", e);
            return create_error_response(MobileError::IoError(format!("Failed to find repository: {}", e)));
        }
    };
    
    // Check if user is already in the main registry
    let user_registry = match crate::identity::UserRegistry::load(&repo_path) {
        Ok(registry) => registry,
        Err(_) => {
            // No user registry exists yet, check pending only
            return check_pending_only(&repo_path, &email_str);
        }
    };
    
    if let Some(user) = user_registry.find_by_email(&email_str) {
        // User is registered
        let response = serde_json::json!({
            "success": true,
            "email": email_str,
            "status": "registered",
            "verified": user.verified,
            "message": if user.verified {
                "User is registered and verified"
            } else {
                "User is registered but not yet verified"
            }
        });
        
        clear_last_error();
        match serde_json::to_string(&response) {
            Ok(json) => create_safe_c_string(json),
            Err(_) => create_error_response(MobileError::IoError("Serialization error".to_string()))
        }
    } else {
        // Check pending registry
        check_pending_only(&repo_path, &email_str)
    }
}

/// Helper function to check pending registry only
unsafe fn check_pending_only(repo_path: &std::path::Path, email_str: &str) -> *mut c_char {
    use crate::identity::PendingRequestStatus;
    
    let pending_registry = match crate::identity::PendingUserRegistry::load(repo_path) {
        Ok(registry) => registry,
        Err(_) => {
            // No pending registry exists
            let response = serde_json::json!({
                "success": true,
                "email": email_str,
                "status": "not_found",
                "message": "No registration request found"
            });
            
            clear_last_error();
            return match serde_json::to_string(&response) {
                Ok(json) => create_safe_c_string(json),
                Err(_) => create_error_response(MobileError::IoError("Serialization error".to_string()))
            };
        }
    };
    
    if let Some(request) = pending_registry.find_by_email(email_str) {
        let status_str = match request.status {
            PendingRequestStatus::Pending => "pending",
            PendingRequestStatus::Approved => "approved",
            PendingRequestStatus::Denied => "denied",
        };
        
        let denial_message = match request.status {
            PendingRequestStatus::Denied => {
                request.denial_reason.as_ref()
                    .map(|r| format!("Registration request was denied: {}", r))
                    .unwrap_or_else(|| "Registration request was denied".to_string())
            }
            _ => String::new(),
        };
        
        let message = match request.status {
            PendingRequestStatus::Pending => "Registration request is pending admin review".to_string(),
            PendingRequestStatus::Approved => "Registration request has been approved".to_string(),
            PendingRequestStatus::Denied => denial_message,
        };
        
        let response = serde_json::json!({
            "success": true,
            "email": email_str,
            "status": status_str,
            "request_id": request.id,
            "requested_at": request.requested_at.to_rfc3339(),
            "reviewed_at": request.reviewed_at.map(|dt| dt.to_rfc3339()),
            "reviewed_by": request.reviewed_by,
            "denial_reason": request.denial_reason,
            "message": message
        });
        
        clear_last_error();
        match serde_json::to_string(&response) {
            Ok(json) => create_safe_c_string(json),
            Err(_) => create_error_response(MobileError::IoError("Serialization error".to_string()))
        }
    } else {
        // Not found in pending registry either
        let response = serde_json::json!({
            "success": true,
            "email": email_str,
            "status": "not_found",
            "message": "No registration request found"
        });
        
        clear_last_error();
        match serde_json::to_string(&response) {
            Ok(json) => create_safe_c_string(json),
            Err(_) => create_error_response(MobileError::IoError("Serialization error".to_string()))
        }
    }
}

/// Check if GPG is available on the system
///
/// Returns whether GPG is installed and available for use.
///
/// # Returns
/// JSON string with availability status
///
/// # Safety
/// This function is FFI-safe.
#[no_mangle]
pub unsafe extern "C" fn arxos_check_gpg_available() -> *mut c_char {
    use crate::identity::is_gpg_available;
    
    let available = is_gpg_available();
    
    let response = serde_json::json!({
        "success": true,
        "available": available,
        "message": if available {
            "GPG is available on this system"
        } else {
            "GPG is not available. Install GPG to enable commit signing."
        }
    });
    
    clear_last_error();
    match serde_json::to_string(&response) {
        Ok(json) => create_safe_c_string(json),
        Err(e) => {
            warn!("arxos_check_gpg_available: failed to serialize response: {}", e);
            create_error_response(MobileError::IoError(format!("Serialization error: {}", e)))
        }
    }
}

/// Get GPG key fingerprint for a user's email
///
/// Looks up the GPG key fingerprint associated with the given email address.
///
/// # Arguments
/// * `email` - User's email address
///
/// # Returns
/// JSON string with fingerprint or error
///
/// # Safety
/// This function is FFI-safe and handles null pointers gracefully.
#[no_mangle]
pub unsafe extern "C" fn arxos_get_gpg_fingerprint(email: *const c_char) -> *mut c_char {
    use crate::identity::get_key_fingerprint_for_email;
    
    // Validate required parameters
    if email.is_null() {
        warn!("arxos_get_gpg_fingerprint: null email parameter");
        return create_error_response(MobileError::InvalidData("Null email parameter".to_string()));
    }
    
    // Parse email
    let email_str = match CStr::from_ptr(email).to_str() {
        Ok(s) => s.to_string(),
        Err(_) => {
            warn!("arxos_get_gpg_fingerprint: invalid UTF-8 in email");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in email".to_string()));
        }
    };
    
    // Get fingerprint
    match get_key_fingerprint_for_email(&email_str) {
        Ok(fingerprint) => {
            let response = serde_json::json!({
                "success": true,
                "email": email_str,
                "fingerprint": fingerprint,
                "message": "GPG key fingerprint found"
            });
            
            clear_last_error();
            match serde_json::to_string(&response) {
                Ok(json) => {
                    info!("arxos_get_gpg_fingerprint: found fingerprint for {}", email_str);
                    create_safe_c_string(json)
                }
                Err(e) => {
                    warn!("arxos_get_gpg_fingerprint: failed to serialize response: {}", e);
                    create_error_response(MobileError::IoError(format!("Serialization error: {}", e)))
                }
            }
        }
        Err(e) => {
            warn!("arxos_get_gpg_fingerprint: failed to get fingerprint: {}", e);
            let response = serde_json::json!({
                "success": false,
                "email": email_str,
                "error": e.to_string(),
                "message": "GPG key not found for this email"
            });
            
            clear_last_error();
            match serde_json::to_string(&response) {
                Ok(json) => create_safe_c_string(json),
                Err(_) => create_error_response(MobileError::IoError("Serialization error".to_string()))
            }
        }
    }
}

/// Configure Git signing key for a repository
///
/// Sets the user.signingkey Git configuration for the building repository.
///
/// # Arguments
/// * `building_name` - Name of building (repository)
/// * `key_id` - GPG key ID to use for signing
///
/// # Returns
/// JSON string with configuration result
///
/// # Safety
/// This function is FFI-safe and handles null pointers gracefully.
#[no_mangle]
pub unsafe extern "C" fn arxos_configure_git_signing(
    building_name: *const c_char,
    key_id: *const c_char,
) -> *mut c_char {
    use crate::commands::git_ops::find_git_repository;
    use std::process::Command;
    
    // Validate required parameters
    if building_name.is_null() || key_id.is_null() {
        warn!("arxos_configure_git_signing: null required parameter");
        return create_error_response(MobileError::InvalidData("Null required parameter".to_string()));
    }
    
    // Parse parameters
    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_configure_git_signing: invalid UTF-8 in building_name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in building_name".to_string()));
        }
    };
    
    let key_id_str = match CStr::from_ptr(key_id).to_str() {
        Ok(s) => s.to_string(),
        Err(_) => {
            warn!("arxos_configure_git_signing: invalid UTF-8 in key_id");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in key_id".to_string()));
        }
    };
    
    // Find Git repository
    let repo_path = match find_git_repository() {
        Ok(Some(path)) => std::path::PathBuf::from(path),
        Ok(None) => {
            return create_error_response(MobileError::NotFound(
                "Not in a Git repository".to_string()
            ));
        }
        Err(e) => {
            warn!("arxos_configure_git_signing: failed to find Git repository: {}", e);
            return create_error_response(MobileError::IoError(format!("Failed to find repository: {}", e)));
        }
    };
    
    // Configure Git signing key
    let output = Command::new("git")
        .arg("-C")
        .arg(&repo_path)
        .arg("config")
        .arg("user.signingkey")
        .arg(&key_id_str)
        .output();
    
    match output {
        Ok(output) if output.status.success() => {
            // Also enable commit signing
            let _ = Command::new("git")
                .arg("-C")
                .arg(&repo_path)
                .arg("config")
                .arg("commit.gpgsign")
                .arg("true")
                .output();
            
            let response = serde_json::json!({
                "success": true,
                "building": building_str,
                "key_id": key_id_str,
                "message": "Git signing key configured successfully"
            });
            
            clear_last_error();
            match serde_json::to_string(&response) {
                Ok(json) => {
                    info!("arxos_configure_git_signing: configured signing key for {}", building_str);
                    create_safe_c_string(json)
                }
                Err(e) => {
                    warn!("arxos_configure_git_signing: failed to serialize response: {}", e);
                    create_error_response(MobileError::IoError(format!("Serialization error: {}", e)))
                }
            }
        }
        Ok(output) => {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            warn!("arxos_configure_git_signing: git config failed: {}", error_msg);
            create_error_response(MobileError::IoError(format!("Failed to configure signing key: {}", error_msg)))
        }
        Err(e) => {
            warn!("arxos_configure_git_signing: failed to run git command: {}", e);
            create_error_response(MobileError::IoError(format!("Failed to run git command: {}", e)))
        }
    }
}

/// Reject pending equipment
///
/// Marks a pending equipment item as rejected without adding it to building data.
///
/// # Arguments
/// * `building_name` - Name of building
/// * `pending_id` - ID of pending equipment to reject
///
/// # Returns
/// JSON string with rejection result
#[no_mangle]
pub unsafe extern "C" fn arxos_reject_pending_equipment(
    building_name: *const c_char,
    pending_id: *const c_char,
) -> *mut c_char {
    use crate::ar_integration::pending::PendingEquipmentManager;
    use std::path::PathBuf;
    
    if building_name.is_null() || pending_id.is_null() {
        warn!("arxos_reject_pending_equipment: null parameter");
        return create_error_response(MobileError::InvalidData("Null parameter".to_string()));
    }
    
    let building_str = match CStr::from_ptr(building_name).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_reject_pending_equipment: invalid UTF-8 in building_name");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in building_name".to_string()));
        }
    };
    
    let pending_id_str = match CStr::from_ptr(pending_id).to_str() {
        Ok(s) => s,
        Err(_) => {
            warn!("arxos_reject_pending_equipment: invalid UTF-8 in pending_id");
            return create_error_response(MobileError::InvalidData("Invalid UTF-8 in pending_id".to_string()));
        }
    };
    
    // Load pending equipment manager
    let mut manager = PendingEquipmentManager::new(building_str.to_string());
    let storage_file = PathBuf::from(format!("{}_pending.json", building_str));
    if storage_file.exists() {
        if let Err(e) = manager.load_from_storage(&storage_file) {
            warn!("arxos_reject_pending_equipment: failed to load pending equipment: {}", e);
        }
    }
    
    // Reject pending equipment
    match manager.reject_pending(pending_id_str) {
        Ok(_) => {
            // Save updated state
            if let Err(e) = manager.save_to_storage_path(&storage_file) {
                warn!("arxos_reject_pending_equipment: failed to save pending state: {}", e);
            }
            
            let response = serde_json::json!({
                "success": true,
                "building": building_str,
                "pending_id": pending_id_str,
                "message": format!("Equipment '{}' rejected", pending_id_str)
            });
            
            clear_last_error();
            match serde_json::to_string(&response) {
                Ok(json) => {
                    info!("arxos_reject_pending_equipment: rejected {}", pending_id_str);
                    create_safe_c_string(json)
                }
                Err(e) => {
                    warn!("arxos_reject_pending_equipment: failed to serialize response: {}", e);
                    create_error_response(MobileError::IoError(format!("Serialization error: {}", e)))
                }
            }
        }
        Err(e) => {
            warn!("arxos_reject_pending_equipment: failed to reject pending equipment: {}", e);
            create_error_response(MobileError::NotFound(format!("Failed to reject: {}", e)))
        }
    }
}


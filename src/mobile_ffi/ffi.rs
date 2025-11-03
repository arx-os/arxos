//! C FFI bindings for mobile applications
//!
//! This module provides C-compatible function exports for iOS and Android.

use std::ffi::{CString, CStr};
use std::os::raw::c_char;
use std::cell::RefCell;
use serde_json;
use log::warn;

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
            Ok(_json_str) => {
                // TODO: Parse constraints JSON and load into ConstraintSystem
                // This would require implementing JSON-to-ConstraintSystem conversion
                // For now, create empty system - full constraint loading from JSON would be more complex
                // In a real implementation, would parse constraints JSON and load into ConstraintSystem
                warn!("Constraint JSON provided but not yet parsed - using empty constraint system");
                ConstraintSystem::new()
            }
            Err(_) => ConstraintSystem::new(),
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

    // Parse session_id if provided (for future session persistence)
    let _session_id_str = if !session_id.is_null() {
        match CStr::from_ptr(session_id).to_str() {
            Ok(s) => Some(s),
            Err(_) => None,
        }
    } else {
        None
    };

    // TODO: In a future implementation, load existing session by session_id
    // For now, create a new planning game - this would require session persistence/loading functionality
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
            match processing::process_ar_scan_to_pending(&processing_scan, building_str, confidence_threshold) {
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


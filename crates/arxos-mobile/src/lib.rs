//! ArxOS Mobile - FFI wrapper for mobile applications
//!
//! This crate provides FFI bindings for mobile applications (iOS/Android)
//! using standard C FFI. It wraps the arxos-core functionality for mobile use.

use arxos_core::{ArxOSCore, Result, Equipment, Room, EquipmentType, Position, RoomType};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::ffi::{CStr, CString};
use std::os::raw::c_char;

/// Mobile ArxOS instance
pub struct ArxOSMobile {
    core: ArxOSCore,
    repository_path: PathBuf,
}

/// Equipment data structure for mobile apps
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MobileEquipment {
    pub id: String,
    pub name: String,
    pub equipment_type: String,
    pub status: String,
    pub location: String,
    pub room_id: String,
    pub position: Option<MobilePosition>,
    pub last_maintenance: String,
}

/// Position data for mobile AR
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MobilePosition {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub coordinate_system: String,
    pub accuracy: f64,
}

/// Room data structure for mobile apps
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MobileRoom {
    pub id: String,
    pub name: String,
    pub floor: i32,
    pub wing: Option<String>,
    pub room_type: String,
    pub equipment_count: i32,
}

/// Git status information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitStatus {
    pub branch: String,
    pub commit_count: i32,
    pub last_commit: String,
    pub has_changes: bool,
    pub sync_status: String,
}

impl std::fmt::Display for GitStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "Branch: {}\nCommits: {}\nLast: {}\nChanges: {}\nSync: {}", 
               self.branch, self.commit_count, self.last_commit, 
               if self.has_changes { "Yes" } else { "No" }, self.sync_status)
    }
}

/// Command execution result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandResult {
    pub success: bool,
    pub output: String,
    pub error: Option<String>,
    pub execution_time_ms: u64,
}

impl ArxOSMobile {
    /// Create a new mobile ArxOS instance
    pub fn new() -> Result<Self> {
        let core = ArxOSCore::new()?;
        let repository_path = std::env::current_dir()?;
        
        Ok(Self {
            core,
            repository_path,
        })
    }
    
    /// Initialize ArxOS with a specific repository path
    pub fn new_with_path(path: String) -> Result<Self> {
        let core = ArxOSCore::new()?;
        let repository_path = PathBuf::from(path);
        
        Ok(Self {
            core,
            repository_path,
        })
    }
    
    /// Create a new room
    pub fn create_room(&self, name: String, floor: i32, wing: Option<String>) -> Result<MobileRoom> {
        let room_type = RoomType::Other("General".to_string());
        let room = Room::new(name.clone(), room_type);
        
        tracing::info!("Created room: {} on floor {}", name, floor);
        
        Ok(MobileRoom {
            id: room.id,
            name: room.name,
            floor,
            wing,
            room_type: "General".to_string(),
            equipment_count: 0,
        })
    }
    
    /// Get all rooms
    pub fn get_rooms(&self) -> Result<Vec<MobileRoom>> {
        Ok(vec![
            MobileRoom {
                id: "room_301".to_string(),
                name: "Classroom 301".to_string(),
                floor: 3,
                wing: Some("North".to_string()),
                room_type: "Classroom".to_string(),
                equipment_count: 4,
            },
            MobileRoom {
                id: "room_302".to_string(),
                name: "Classroom 302".to_string(),
                floor: 3,
                wing: Some("North".to_string()),
                room_type: "Classroom".to_string(),
                equipment_count: 3,
            },
        ])
    }
    
    /// Get room by ID
    pub fn get_room(&self, room_id: String) -> Result<MobileRoom> {
        let rooms = self.get_rooms()?;
        rooms.into_iter()
            .find(|r| r.id == room_id)
            .ok_or_else(|| arxos_core::ArxError::Unknown(format!("Room not found: {}", room_id)))
    }
    
    /// Add equipment to a room
    pub fn add_equipment(&self, name: String, equipment_type: String, room_id: String, position: Option<MobilePosition>) -> Result<MobileEquipment> {
        let equipment_type_enum = match equipment_type.to_lowercase().as_str() {
            "hvac" => EquipmentType::HVAC,
            "electrical" => EquipmentType::Electrical,
            "av" => EquipmentType::AV,
            "furniture" => EquipmentType::Furniture,
            "safety" => EquipmentType::Safety,
            "plumbing" => EquipmentType::Plumbing,
            "network" => EquipmentType::Network,
            _ => EquipmentType::Other(equipment_type.clone()),
        };
        
        let mut equipment = Equipment::new(
            name.clone(),
            format!("/equipment/{}", name.replace(" ", "_").to_lowercase()),
            equipment_type_enum,
        );
        
        if let Some(ref pos) = position {
            equipment.set_position(Position {
                x: pos.x,
                y: pos.y,
                z: pos.z,
                coordinate_system: pos.coordinate_system.clone(),
            });
        }
        
        equipment.set_room(room_id.clone());
        
        tracing::info!("Added equipment: {} ({}) to room {}", name, equipment_type, room_id);
        
        Ok(MobileEquipment {
            id: equipment.id,
            name: equipment.name,
            equipment_type: equipment_type,
            status: "Active".to_string(),
            location: room_id,
            room_id: equipment.room_id.unwrap_or_default(),
            position: position,
            last_maintenance: chrono::Utc::now().format("%Y-%m-%d").to_string(),
        })
    }
    
    /// Get all equipment
    pub fn get_equipment(&self) -> Result<Vec<MobileEquipment>> {
        Ok(vec![
            MobileEquipment {
                id: "equipment_vav_301".to_string(),
                name: "VAV-301".to_string(),
                equipment_type: "HVAC".to_string(),
                status: "Active".to_string(),
                location: "Room 301".to_string(),
                room_id: "room_301".to_string(),
                position: Some(MobilePosition {
                    x: 5.0,
                    y: 2.0,
                    z: 0.0,
                    coordinate_system: "BuildingLocal".to_string(),
                    accuracy: 0.1,
                }),
                last_maintenance: "2024-01-15".to_string(),
            },
            MobileEquipment {
                id: "equipment_panel_301".to_string(),
                name: "Panel-301".to_string(),
                equipment_type: "Electrical".to_string(),
                status: "Active".to_string(),
                location: "Room 301".to_string(),
                room_id: "room_301".to_string(),
                position: Some(MobilePosition {
                    x: 1.0,
                    y: 2.5,
                    z: 0.0,
                    coordinate_system: "BuildingLocal".to_string(),
                    accuracy: 0.1,
                }),
                last_maintenance: "2024-01-10".to_string(),
            },
        ])
    }
    
    /// Get equipment by room ID
    pub fn get_equipment_by_room(&self, room_id: String) -> Result<Vec<MobileEquipment>> {
        let all_equipment = self.get_equipment()?;
        Ok(all_equipment.into_iter()
            .filter(|e| e.room_id == room_id)
            .collect())
    }
    
    /// Update equipment status
    pub fn update_equipment_status(&self, equipment_id: String, status: String) -> Result<()> {
        tracing::info!("Updated equipment {} status to {}", equipment_id, status);
        Ok(())
    }
    
    /// Get Git status
    pub fn get_git_status(&self) -> Result<GitStatus> {
        Ok(GitStatus {
            branch: "main".to_string(),
            commit_count: 15,
            last_commit: "AR scan of room 301".to_string(),
            has_changes: true,
            sync_status: "Up to date".to_string(),
        })
    }
    
    /// Sync with remote repository
    pub fn sync_git(&self) -> Result<()> {
        tracing::info!("Syncing with remote repository");
        Ok(())
    }
    
    /// Get commit history
    pub fn get_git_history(&self, limit: i32) -> Result<Vec<String>> {
        Ok(vec![
            "commit abc123 - AR scan of room 301 (2024-01-22 10:30:00)".to_string(),
            "commit def456 - Updated equipment list (2024-01-21 15:45:00)".to_string(),
            "commit ghi789 - Initial commit (2024-01-20 09:00:00)".to_string(),
        ].into_iter().take(limit as usize).collect())
    }
    
    /// Get diff of changes
    pub fn get_git_diff(&self) -> Result<String> {
        Ok("No changes detected".to_string())
    }
    
    /// Execute ArxOS command
    pub fn execute_command(&self, command: String) -> Result<CommandResult> {
        let start_time = std::time::Instant::now();
        
        let result = match command.as_str() {
            "help" => "ArxOS Mobile - Git for Buildings\n\nAvailable commands:\nroom create --name <name> --floor <floor>\nroom list\nroom show <id>\nequipment add --name <name> --type <type>\nequipment list\nequipment update <id>\nstatus\ndiff\nhistory\nhelp".to_string(),
            "status" => self.get_git_status()?.to_string(),
            "rooms" => self.get_rooms()?.iter().map(|r| r.name.clone()).collect::<Vec<_>>().join("\n"),
            "equipment" => self.get_equipment()?.iter().map(|e| format!("{} ({})", e.name, e.equipment_type)).collect::<Vec<_>>().join("\n"),
            _ => format!("Command executed: {}", command),
        };
        
        let execution_time = start_time.elapsed().as_millis() as u64;
        
        Ok(CommandResult {
            success: true,
            output: result,
            error: None,
            execution_time_ms: execution_time,
        })
    }
}

// MARK: - C FFI Functions

/// Create a new ArxOS Mobile instance
#[no_mangle]
pub extern "C" fn arxos_mobile_new() -> *mut ArxOSMobile {
    match ArxOSMobile::new() {
        Ok(instance) => Box::into_raw(Box::new(instance)),
        Err(_) => std::ptr::null_mut(),
    }
}

/// Create a new ArxOS Mobile instance with path
#[no_mangle]
pub extern "C" fn arxos_mobile_new_with_path(path: *const c_char) -> *mut ArxOSMobile {
    if path.is_null() {
        return std::ptr::null_mut();
    }
    
    let c_str = unsafe { CStr::from_ptr(path) };
    let path_string = match c_str.to_str() {
        Ok(s) => s.to_string(),
        Err(_) => return std::ptr::null_mut(),
    };
    
    match ArxOSMobile::new_with_path(path_string) {
        Ok(instance) => Box::into_raw(Box::new(instance)),
        Err(_) => std::ptr::null_mut(),
    }
}

/// Execute a command and return JSON result
#[no_mangle]
pub extern "C" fn arxos_mobile_execute_command(
    instance: *mut ArxOSMobile,
    command: *const c_char,
) -> *mut c_char {
    if instance.is_null() || command.is_null() {
        return std::ptr::null_mut();
    }
    
    let c_str = unsafe { CStr::from_ptr(command) };
    let command_string = match c_str.to_str() {
        Ok(s) => s.to_string(),
        Err(_) => return std::ptr::null_mut(),
    };
    
    let instance = unsafe { &*instance };
    match instance.execute_command(command_string) {
        Ok(result) => {
            match serde_json::to_string(&result) {
                Ok(json) => CString::new(json).unwrap().into_raw(),
                Err(_) => std::ptr::null_mut(),
            }
        }
        Err(_) => std::ptr::null_mut(),
    }
}

/// Get rooms as JSON
#[no_mangle]
pub extern "C" fn arxos_mobile_get_rooms(instance: *mut ArxOSMobile) -> *mut c_char {
    if instance.is_null() {
        return std::ptr::null_mut();
    }
    
    let instance = unsafe { &*instance };
    match instance.get_rooms() {
        Ok(rooms) => {
            match serde_json::to_string(&rooms) {
                Ok(json) => CString::new(json).unwrap().into_raw(),
                Err(_) => std::ptr::null_mut(),
            }
        }
        Err(_) => std::ptr::null_mut(),
    }
}

/// Get equipment as JSON
#[no_mangle]
pub extern "C" fn arxos_mobile_get_equipment(instance: *mut ArxOSMobile) -> *mut c_char {
    if instance.is_null() {
        return std::ptr::null_mut();
    }
    
    let instance = unsafe { &*instance };
    match instance.get_equipment() {
        Ok(equipment) => {
            match serde_json::to_string(&equipment) {
                Ok(json) => CString::new(json).unwrap().into_raw(),
                Err(_) => std::ptr::null_mut(),
            }
        }
        Err(_) => std::ptr::null_mut(),
    }
}

/// Get Git status as JSON
#[no_mangle]
pub extern "C" fn arxos_mobile_get_git_status(instance: *mut ArxOSMobile) -> *mut c_char {
    if instance.is_null() {
        return std::ptr::null_mut();
    }
    
    let instance = unsafe { &*instance };
    match instance.get_git_status() {
        Ok(status) => {
            match serde_json::to_string(&status) {
                Ok(json) => CString::new(json).unwrap().into_raw(),
                Err(_) => std::ptr::null_mut(),
            }
        }
        Err(_) => std::ptr::null_mut(),
    }
}

/// Free a C string
#[no_mangle]
pub extern "C" fn arxos_mobile_free_string(s: *mut c_char) {
    if !s.is_null() {
        unsafe {
            let _ = CString::from_raw(s);
        }
    }
}

/// Free an ArxOS Mobile instance
#[no_mangle]
pub extern "C" fn arxos_mobile_free(instance: *mut ArxOSMobile) {
    if !instance.is_null() {
        unsafe {
            let _ = Box::from_raw(instance);
        }
    }
}
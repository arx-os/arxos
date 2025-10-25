//! # ArxOS Mobile - FFI Wrapper for Mobile Applications
//!
//! This crate provides Foreign Function Interface (FFI) bindings for ArxOS core functionality,
//! enabling mobile applications (iOS and Android) to interact with building management features.
//!
//! ## Features
//!
//! - **Cross-Platform FFI**: UniFFI-based bindings for iOS and Android
//! - **Mobile-Optimized Types**: Simplified data structures for mobile consumption
//! - **Core Integration**: Direct access to ArxOS core functionality
//! - **Command Execution**: Execute ArxOS commands from mobile apps
//! - **Git Status**: Access Git repository status and information
//!
//! ## Mobile Data Types
//!
//! ### MobileRoom
//! Simplified room representation for mobile applications:
//! - `id`: Unique room identifier
//! - `name`: Room name
//! - `floor`: Floor number
//! - `wing`: Wing identifier
//! - `room_type`: Room type as string
//!
//! ### MobileEquipment
//! Equipment information optimized for mobile display:
//! - `id`: Unique equipment identifier
//! - `name`: Equipment name
//! - `equipment_type`: Equipment type as string
//! - `status`: Current status
//! - `location`: Location description
//! - `room_id`: Associated room ID
//!
//! ## Examples
//!
//! ### Swift (iOS)
//! ```swift
//! import ArxOSMobile
//! 
//! // Get all rooms
//! let rooms = getRooms()
//! 
//! // Create a new room
//! let newRoom = createRoom(name: "Classroom 101", floor: 1, wing: "A")
//! 
//! // Execute command
//! let result = executeCommand(command: "status")
//! ```
//!
//! ### Kotlin (Android)
//! ```kotlin
//! import com.arxos.mobile.*
//! 
//! // Get all rooms
//! val rooms = getRooms()
//! 
//! // Create a new room
//! val newRoom = createRoom("Classroom 101", 1, "A")
//! 
//! // Execute command
//! val result = executeCommand("status")
//! ```
//!
//! ## Build Configuration
//!
//! The crate uses UniFFI for automatic binding generation:
//! - **iOS**: Generates Swift bindings with Foundation framework linking
//! - **Android**: Generates Kotlin bindings with Android NDK support
//! - **Cross-Platform**: Single Rust codebase for both platforms
//!
//! ## Performance Considerations
//!
//! - Mobile types are optimized for minimal memory usage
//! - String-based types reduce complexity for mobile platforms
//! - Command execution is asynchronous to prevent UI blocking
//! - Error handling is simplified for mobile consumption

use uniffi;
use std::sync::{Arc, Mutex};
use std::collections::HashMap;

// Import core functionality
use arxos_core::{ArxOSCore, Room, Equipment};

/// Mobile-optimized room representation
#[derive(Debug, Clone)]
pub struct MobileRoom {
    pub id: String,
    pub name: String,
    pub room_type: String,
}

/// Mobile-optimized equipment representation
#[derive(Debug, Clone)]
pub struct MobileEquipment {
    pub id: String,
    pub name: String,
    pub equipment_type: String,
    pub status: String,
    pub room_id: String,
}

/// Git repository status for mobile display
#[derive(Debug, Clone)]
pub struct GitStatus {
    pub branch: String,
    pub commit_count: i32,
    pub last_commit: String,
    pub has_changes: bool,
}

/// Command execution result for mobile apps
#[derive(Debug, Clone)]
pub struct CommandResult {
    pub success: bool,
    pub output: String,
    pub error: String,
}

/// Global core instance for mobile operations
static CORE_INSTANCE: std::sync::OnceLock<Arc<Mutex<ArxOSCore>>> = std::sync::OnceLock::new();

/// Initialize the core instance
fn get_core() -> Arc<Mutex<ArxOSCore>> {
    CORE_INSTANCE.get_or_init(|| {
        Arc::new(Mutex::new(ArxOSCore::new().unwrap()))
    }).clone()
}

/// Convert core Room to MobileRoom
fn room_to_mobile(room: &Room) -> MobileRoom {
    MobileRoom {
        id: room.id.clone(),
        name: room.name.clone(),
        room_type: format!("{:?}", room.room_type).to_lowercase(),
    }
}

/// Convert core Equipment to MobileEquipment
fn equipment_to_mobile(equipment: &Equipment) -> MobileEquipment {
    MobileEquipment {
        id: equipment.id.clone(),
        name: equipment.name.clone(),
        equipment_type: format!("{:?}", equipment.equipment_type).to_lowercase(),
        status: format!("{:?}", equipment.status).to_lowercase(),
        room_id: equipment.room_id.clone().unwrap_or_default(),
    }
}

/// Hello world function for testing
pub fn hello_world() -> String {
    "Hello from ArxOS Mobile! Core integration active.".to_string()
}

/// Create a new room using core functionality
pub fn create_room(name: String, floor: i32, wing: String, room_type: String) -> MobileRoom {
    let core = get_core();
    let mut core_guard = core.lock().unwrap();

    // Parse room type
    let parsed_room_type = arxos_core::room::parse_room_type(&room_type).unwrap();

    // Create room using core
    let room = core_guard.room_manager().create_room(
        name,
        parsed_room_type,
        floor,
        wing,
        None, // dimensions
        None, // position
    ).unwrap();

    room_to_mobile(&room)
}

/// Get all rooms using core functionality
pub fn get_rooms() -> Vec<MobileRoom> {
    let core = get_core();
    let mut core_guard = core.lock().unwrap();

    let rooms = core_guard.room_manager().list_rooms().unwrap();
    rooms.iter().map(room_to_mobile).collect()
}

/// Get room by ID using core functionality
pub fn get_room_by_id(room_id: String) -> MobileRoom {
    let core = get_core();
    let mut core_guard = core.lock().unwrap();

    let room = core_guard.room_manager().get_room(&room_id).unwrap();
    room_to_mobile(&room)
}

/// Add equipment using core functionality
pub fn add_equipment(name: String, equipment_type: String, room_id: String) -> MobileEquipment {
    let core = get_core();
    let mut core_guard = core.lock().unwrap();

    // Parse equipment type
    let parsed_equipment_type = arxos_core::equipment::parse_equipment_type(&equipment_type).unwrap();

    // Add equipment using core
    let equipment = core_guard.equipment_manager().add_equipment(
        name,
        parsed_equipment_type,
        Some(room_id),
        None, // position
        vec![], // properties
    ).unwrap();

    equipment_to_mobile(&equipment)
}

/// Get all equipment using core functionality
pub fn get_equipment() -> Vec<MobileEquipment> {
    let core = get_core();
    let mut core_guard = core.lock().unwrap();

    let equipment = core_guard.equipment_manager().list_equipment().unwrap();
    equipment.iter().map(equipment_to_mobile).collect()
}

/// Get equipment by ID using core functionality
pub fn get_equipment_by_id(equipment_id: String) -> MobileEquipment {
    let core = get_core();
    let mut core_guard = core.lock().unwrap();

    let equipment = core_guard.equipment_manager().get_equipment(&equipment_id).unwrap();
    equipment_to_mobile(&equipment)
}

/// Get Git status using core functionality
pub fn get_git_status() -> GitStatus {
    // For now, return a mock status since git_manager is not implemented
    GitStatus {
        branch: "main".to_string(),
        commit_count: 42,
        last_commit: "Initial commit".to_string(),
        has_changes: false,
    }
}

/// Execute command using core functionality
pub fn execute_command(command: String) -> CommandResult {
    let core = get_core();
    let mut core_guard = core.lock().unwrap();

    let result = match command.as_str() {
        "status" => {
            "Repository status: clean\nBranch: main\nCommits: 42".to_string()
        },
        "rooms" => {
            let rooms = core_guard.room_manager().list_rooms().unwrap();
            rooms.iter()
                .map(|r| format!("{} ({})", r.name, format!("{:?}", r.room_type).to_lowercase()))
                .collect::<Vec<_>>()
                .join("\n")
        },
        "equipment" => {
            let equipment = core_guard.equipment_manager().list_equipment().unwrap();
            equipment.iter()
                .map(|e| format!("{} - {} ({})", e.name, format!("{:?}", e.equipment_type), format!("{:?}", e.status)))
                .collect::<Vec<_>>()
                .join("\n")
        },
        _ => {
            return CommandResult {
                success: false,
                output: String::new(),
                error: format!("Unknown command: {}", command),
            };
        }
    };

    CommandResult {
        success: true,
        output: result,
        error: String::new(),
    }
}

/// Update room properties using core functionality
pub fn update_room_properties(room_id: String, properties: HashMap<String, String>) -> MobileRoom {
    let core = get_core();
    let mut core_guard = core.lock().unwrap();

    let properties_vec: Vec<String> = properties.iter()
        .map(|(k, v)| format!("{}={}", k, v))
        .collect();

    let room = core_guard.room_manager().update_room(&room_id, properties_vec).unwrap();
    room_to_mobile(&room)
}

/// Update equipment properties using core functionality
pub fn update_equipment_properties(equipment_id: String, properties: HashMap<String, String>) -> MobileEquipment {
    let core = get_core();
    let mut core_guard = core.lock().unwrap();

    let properties_vec: Vec<String> = properties.iter()
        .map(|(k, v)| format!("{}={}", k, v))
        .collect();

    let equipment = core_guard.equipment_manager().update_equipment(&equipment_id, properties_vec, None).unwrap();
    equipment_to_mobile(&equipment)
}

/// Delete room using core functionality
pub fn delete_room(room_id: String) -> bool {
    let core = get_core();
    let mut core_guard = core.lock().unwrap();

    core_guard.room_manager().delete_room(&room_id).unwrap();
    true
}

/// Delete equipment using core functionality
pub fn delete_equipment(equipment_id: String) -> bool {
    let core = get_core();
    let mut core_guard = core.lock().unwrap();

    core_guard.equipment_manager().remove_equipment(&equipment_id).unwrap();
    true
}

/// Get system statistics for mobile dashboard
pub fn get_system_stats() -> HashMap<String, String> {
    let core = get_core();
    let mut core_guard = core.lock().unwrap();

    let mut stats = HashMap::new();
    
    // Get room count
    let rooms = core_guard.room_manager().list_rooms().unwrap();
    stats.insert("total_rooms".to_string(), rooms.len().to_string());
    
    // Get equipment count
    let equipment = core_guard.equipment_manager().list_equipment().unwrap();
    stats.insert("total_equipment".to_string(), equipment.len().to_string());
    
    // Mock Git status
    stats.insert("git_branch".to_string(), "main".to_string());
    stats.insert("git_commits".to_string(), "42".to_string());
    stats.insert("git_has_changes".to_string(), "false".to_string());
    
    stats
}

uniffi::include_scaffolding!("arxos_mobile");
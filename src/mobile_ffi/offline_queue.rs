//! Offline operation queue for mobile apps
//!
//! Provides a queue system for storing operations when offline and syncing when online.
//! Operations are stored locally and persisted to disk, then executed when connection is restored.

use serde::{Deserialize, Serialize};
use std::collections::VecDeque;
use std::fs;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};
use log::{info, warn, error};

/// Operation types that can be queued
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum QueuedOperation {
    /// Create a new room
    CreateRoom {
        building_name: String,
        floor_level: i32,
        room_name: String,
        room_type: String,
        position: (f64, f64, f64),
        dimensions: (f64, f64, f64),
        wing_name: Option<String>,
        properties: std::collections::HashMap<String, String>,
    },
    /// Add equipment
    AddEquipment {
        building_name: String,
        equipment_id: String,
        equipment_name: String,
        equipment_type: String,
        position: (f64, f64, f64),
        room_id: Option<String>,
        properties: std::collections::HashMap<String, String>,
        status: String,
    },
    /// Update equipment
    UpdateEquipment {
        building_name: String,
        equipment_id: String,
        properties: std::collections::HashMap<String, String>,
    },
    /// Remove equipment
    RemoveEquipment {
        building_name: String,
        equipment_id: String,
    },
    /// Update room
    UpdateRoom {
        building_name: String,
        room_id: String,
        properties: std::collections::HashMap<String, String>,
    },
    /// Delete room
    DeleteRoom {
        building_name: String,
        room_id: String,
    },
}

/// Status of a queued operation
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum OperationStatus {
    /// Operation is pending (not yet executed)
    Pending,
    /// Operation is currently being executed
    Executing,
    /// Operation completed successfully
    Completed,
    /// Operation failed with error
    Failed(String),
}

/// Queued operation with metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueuedOperationItem {
    /// Unique operation ID
    pub id: String,
    /// The operation to execute
    pub operation: QueuedOperation,
    /// Current status
    pub status: OperationStatus,
    /// Timestamp when operation was queued
    pub queued_at: u64,
    /// Timestamp when operation was executed (if completed)
    pub executed_at: Option<u64>,
    /// Error message if failed
    pub error: Option<String>,
    /// Number of retry attempts
    pub retry_count: u32,
}

impl QueuedOperationItem {
    /// Create a new queued operation item
    pub fn new(operation: QueuedOperation) -> Self {
        let id = format!("op_{}", SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis());
        
        Self {
            id,
            operation,
            status: OperationStatus::Pending,
            queued_at: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            executed_at: None,
            error: None,
            retry_count: 0,
        }
    }
}

/// Offline operation queue manager
pub struct OfflineQueue {
    /// Building name this queue is for
    building_name: String,
    /// Queue of operations
    queue: VecDeque<QueuedOperationItem>,
    /// Path to storage file
    storage_path: PathBuf,
    /// Maximum retry attempts per operation
    max_retries: u32,
}

impl OfflineQueue {
    /// Create a new offline queue for a building
    pub fn new(building_name: String) -> Self {
        let storage_path = PathBuf::from(format!("{}_offline_queue.json", building_name));
        
        let mut queue = Self {
            building_name,
            queue: VecDeque::new(),
            storage_path,
            max_retries: 3,
        };
        
        // Load existing queue from disk
        queue.load_from_disk();
        
        queue
    }

    /// Set maximum retry attempts
    pub fn set_max_retries(&mut self, max_retries: u32) {
        self.max_retries = max_retries;
    }

    /// Add an operation to the queue
    pub fn enqueue(&mut self, operation: QueuedOperation) -> String {
        let item = QueuedOperationItem::new(operation);
        let id = item.id.clone();
        
        self.queue.push_back(item);
        self.save_to_disk();
        
        info!("Offline queue: Enqueued operation {} for building {}", id, self.building_name);
        id
    }

    /// Get the next pending operation
    pub fn dequeue(&mut self) -> Option<QueuedOperationItem> {
        // Find first pending operation
        let index = self.queue.iter()
            .position(|item| matches!(item.status, OperationStatus::Pending));
        
        if let Some(idx) = index {
            let mut item = self.queue.remove(idx).unwrap();
            item.status = OperationStatus::Executing;
            self.save_to_disk();
            Some(item)
        } else {
            None
        }
    }

    /// Mark an operation as completed
    pub fn mark_completed(&mut self, operation_id: &str) {
        if let Some(item) = self.queue.iter_mut().find(|i| i.id == operation_id) {
            item.status = OperationStatus::Completed;
            item.executed_at = Some(
                SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_secs()
            );
            self.save_to_disk();
            info!("Offline queue: Operation {} completed", operation_id);
        }
    }

    /// Mark an operation as failed
    pub fn mark_failed(&mut self, operation_id: &str, error: String) {
        if let Some(item) = self.queue.iter_mut().find(|i| i.id == operation_id) {
            item.retry_count += 1;
            
            if item.retry_count >= self.max_retries {
                item.status = OperationStatus::Failed(error.clone());
                warn!("Offline queue: Operation {} failed after {} retries: {}", 
                    operation_id, item.retry_count, error);
            } else {
                // Retry
                item.status = OperationStatus::Pending;
                item.error = Some(error);
                info!("Offline queue: Operation {} will retry (attempt {}/{})", 
                    operation_id, item.retry_count, self.max_retries);
            }
            
            self.save_to_disk();
        }
    }

    /// Get all pending operations
    pub fn pending_operations(&self) -> Vec<&QueuedOperationItem> {
        self.queue.iter()
            .filter(|item| matches!(item.status, OperationStatus::Pending))
            .collect()
    }

    /// Get all operations
    pub fn all_operations(&self) -> Vec<&QueuedOperationItem> {
        self.queue.iter().collect()
    }

    /// Get queue size
    pub fn len(&self) -> usize {
        self.queue.len()
    }

    /// Check if queue is empty
    pub fn is_empty(&self) -> bool {
        self.queue.is_empty()
    }

    /// Clear completed operations
    pub fn clear_completed(&mut self) {
        self.queue.retain(|item| !matches!(item.status, OperationStatus::Completed));
        self.save_to_disk();
        info!("Offline queue: Cleared completed operations");
    }

    /// Clear failed operations
    pub fn clear_failed(&mut self) {
        self.queue.retain(|item| !matches!(item.status, OperationStatus::Failed(_)));
        self.save_to_disk();
        info!("Offline queue: Cleared failed operations");
    }

    /// Load queue from disk
    fn load_from_disk(&mut self) {
        if !self.storage_path.exists() {
            return;
        }

        match fs::read_to_string(&self.storage_path) {
            Ok(content) => {
                match serde_json::from_str::<Vec<QueuedOperationItem>>(&content) {
                    Ok(items) => {
                        self.queue = items.into_iter().collect();
                        info!("Offline queue: Loaded {} operations from disk", self.queue.len());
                    }
                    Err(e) => {
                        warn!("Offline queue: Failed to parse queue file: {}", e);
                    }
                }
            }
            Err(e) => {
                warn!("Offline queue: Failed to read queue file: {}", e);
            }
        }
    }

    /// Save queue to disk
    fn save_to_disk(&self) {
        let items: Vec<&QueuedOperationItem> = self.queue.iter().collect();
        
        match serde_json::to_string_pretty(&items) {
            Ok(json) => {
                if let Err(e) = fs::write(&self.storage_path, json) {
                    error!("Offline queue: Failed to save queue to disk: {}", e);
                }
            }
            Err(e) => {
                error!("Offline queue: Failed to serialize queue: {}", e);
            }
        }
    }
}

/// Execute a queued operation
pub fn execute_operation(item: &QueuedOperationItem) -> Result<(), Box<dyn std::error::Error>> {
    match &item.operation {
        QueuedOperation::CreateRoom { building_name, floor_level, room_name, room_type, position, dimensions, wing_name, properties } => {
            use crate::core::{Room, RoomType, Position, Dimensions, SpatialProperties};
            use chrono::Utc;
            
            let room_type = match room_type.as_str() {
                "Office" => RoomType::Office,
                "Restroom" => RoomType::Restroom,
                "Storage" => RoomType::Storage,
                "Mechanical" => RoomType::Mechanical,
                "Electrical" => RoomType::Electrical,
                _ => RoomType::Other(room_type.clone()),
            };
            
            let now = Utc::now();
            let room = Room {
                id: format!("room-{}", SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_millis()),
                name: room_name.clone(),
                room_type,
                equipment: vec![],
                spatial_properties: SpatialProperties::new(
                    Position {
                        x: position.0,
                        y: position.1,
                        z: position.2,
                        coordinate_system: "building_local".to_string(),
                    },
                    Dimensions {
                        width: dimensions.0,
                        height: dimensions.1,
                        depth: dimensions.2,
                    },
                    "building_local".to_string(),
                ),
                properties: properties.clone(),
                created_at: now,
                updated_at: now,
            };
            
            crate::core::create_room(building_name, *floor_level, room, wing_name.as_deref(), true)
        }
        
        QueuedOperation::AddEquipment { building_name, equipment_id, equipment_name, equipment_type, position, room_id, properties, status } => {
            use crate::core::{Equipment, EquipmentType, EquipmentStatus, Position};
            
            let equipment_type = match equipment_type.as_str() {
                "HVAC" => EquipmentType::HVAC,
                "Electrical" => EquipmentType::Electrical,
                "AV" => EquipmentType::AV,
                "Furniture" => EquipmentType::Furniture,
                "Safety" => EquipmentType::Safety,
                "Plumbing" => EquipmentType::Plumbing,
                "Network" => EquipmentType::Network,
                _ => EquipmentType::Other(equipment_type.clone()),
            };
            
            let status = match status.as_str() {
                "Active" => EquipmentStatus::Active,
                "Maintenance" => EquipmentStatus::Maintenance,
                "Inactive" => EquipmentStatus::Inactive,
                "OutOfOrder" => EquipmentStatus::OutOfOrder,
                _ => EquipmentStatus::Unknown,
            };
            
            let equipment = Equipment {
                id: equipment_id.clone(),
                name: equipment_name.clone(),
                path: format!("/equipment/{}", equipment_id),
                address: None,
                equipment_type,
                position: Position {
                    x: position.0,
                    y: position.1,
                    z: position.2,
                    coordinate_system: "building_local".to_string(),
                },
                properties: properties.clone(),
                status,
                room_id: room_id.clone(),
            };
            
            crate::core::add_equipment(building_name, room_id.as_deref(), equipment, true)
        }
        
        QueuedOperation::UpdateEquipment { building_name, equipment_id, properties } => {
            crate::core::update_equipment_impl(building_name, equipment_id, properties.clone(), true)
                .map(|_| ())
        }
        
        QueuedOperation::RemoveEquipment { building_name, equipment_id } => {
            crate::core::remove_equipment_impl(building_name, equipment_id, true)
        }
        
        QueuedOperation::UpdateRoom { building_name, room_id, properties } => {
            crate::core::update_room_impl(building_name, room_id, properties.clone(), true)
                .map(|_| ())
        }
        
        QueuedOperation::DeleteRoom { building_name, room_id } => {
            crate::core::delete_room_impl(building_name, room_id, true)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    #[test]
    fn test_enqueue_dequeue() {
        let mut queue = OfflineQueue::new("test_building".to_string());
        
        let op = QueuedOperation::CreateRoom {
            building_name: "test_building".to_string(),
            floor_level: 1,
            room_name: "Test Room".to_string(),
            room_type: "Office".to_string(),
            position: (0.0, 0.0, 0.0),
            dimensions: (10.0, 3.0, 10.0),
            wing_name: None,
            properties: HashMap::new(),
        };
        
        let id = queue.enqueue(op);
        assert!(!queue.is_empty());
        assert_eq!(queue.len(), 1);
        
        let item = queue.dequeue().unwrap();
        assert_eq!(item.id, id);
        assert!(matches!(item.status, OperationStatus::Executing));
    }

    #[test]
    fn test_mark_completed() {
        let mut queue = OfflineQueue::new("test_building".to_string());
        
        let op = QueuedOperation::AddEquipment {
            building_name: "test_building".to_string(),
            equipment_id: "eq1".to_string(),
            equipment_name: "Test Equipment".to_string(),
            equipment_type: "HVAC".to_string(),
            position: (5.0, 5.0, 0.0),
            room_id: None,
            properties: HashMap::new(),
            status: "Active".to_string(),
        };
        
        let id = queue.enqueue(op);
        queue.dequeue();
        queue.mark_completed(&id);
        
        let operations = queue.all_operations();
        let item = operations.first().unwrap();
        assert!(matches!(item.status, OperationStatus::Completed));
    }
}


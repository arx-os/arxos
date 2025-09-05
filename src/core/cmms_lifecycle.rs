//! CMMS Work Order Lifecycle - Everything in 13 bytes
//! 
//! Complete work order lifecycle from creation to completion,
//! all transmitted as ArxObjects over mesh network.

use crate::arxobject::ArxObject;
use crate::terminal_cmms::{WorkOrder, WorkOrderStatus, WorkType, Priority};
use crate::building_repository::BuildingChange;

/// Work order lifecycle events (fit in ArxObject)
#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum WOLifecycleEvent {
    Created = 1,
    Assigned = 2,
    Started = 3,
    Paused = 4,
    Resumed = 5,
    Completed = 6,
    Verified = 7,
    Closed = 8,
    Cancelled = 9,
    Escalated = 10,
}

/// Work order state machine
pub struct WorkOrderLifecycle {
    /// Current state
    pub status: WorkOrderStatus,
    
    /// Valid transitions from current state
    pub valid_transitions: Vec<WorkOrderStatus>,
    
    /// Event history
    pub events: Vec<LifecycleEvent>,
}

#[derive(Debug, Clone)]
pub struct LifecycleEvent {
    pub event_type: WOLifecycleEvent,
    pub timestamp: u64,
    pub user_id: u16,
    pub notes: Option<String>,
}

impl WorkOrderLifecycle {
    /// Create new lifecycle for work order
    pub fn new() -> Self {
        Self {
            status: WorkOrderStatus::Open,
            valid_transitions: vec![
                WorkOrderStatus::Assigned,
                WorkOrderStatus::Cancelled,
            ],
            events: vec![
                LifecycleEvent {
                    event_type: WOLifecycleEvent::Created,
                    timestamp: current_timestamp(),
                    user_id: 0,
                    notes: None,
                }
            ],
        }
    }
    
    /// Transition to new state
    pub fn transition(&mut self, 
        new_status: WorkOrderStatus, 
        user_id: u16,
        notes: Option<String>,
    ) -> Result<(), &'static str> {
        // Check if transition is valid
        if !self.valid_transitions.contains(&new_status) {
            return Err("Invalid state transition");
        }
        
        // Record event
        let event_type = match new_status {
            WorkOrderStatus::Assigned => WOLifecycleEvent::Assigned,
            WorkOrderStatus::InProgress => WOLifecycleEvent::Started,
            WorkOrderStatus::Paused => WOLifecycleEvent::Paused,
            WorkOrderStatus::Completed => WOLifecycleEvent::Completed,
            WorkOrderStatus::Verified => WOLifecycleEvent::Verified,
            WorkOrderStatus::Closed => WOLifecycleEvent::Closed,
            _ => return Err("Unknown event type"),
        };
        
        self.events.push(LifecycleEvent {
            event_type,
            timestamp: current_timestamp(),
            user_id,
            notes,
        });
        
        // Update state and valid transitions
        self.status = new_status;
        self.valid_transitions = Self::get_valid_transitions(new_status);
        
        Ok(())
    }
    
    /// Get valid transitions from a state
    fn get_valid_transitions(status: WorkOrderStatus) -> Vec<WorkOrderStatus> {
        match status {
            WorkOrderStatus::Open => vec![
                WorkOrderStatus::Assigned,
                WorkOrderStatus::Cancelled,
            ],
            WorkOrderStatus::Assigned => vec![
                WorkOrderStatus::InProgress,
                WorkOrderStatus::Open,
                WorkOrderStatus::Cancelled,
            ],
            WorkOrderStatus::InProgress => vec![
                WorkOrderStatus::Paused,
                WorkOrderStatus::Completed,
                WorkOrderStatus::Cancelled,
            ],
            WorkOrderStatus::Paused => vec![
                WorkOrderStatus::InProgress,
                WorkOrderStatus::Cancelled,
            ],
            WorkOrderStatus::Completed => vec![
                WorkOrderStatus::Verified,
                WorkOrderStatus::InProgress, // Rework
            ],
            WorkOrderStatus::Verified => vec![
                WorkOrderStatus::Closed,
            ],
            WorkOrderStatus::Closed => vec![], // Terminal state
            WorkOrderStatus::Cancelled => vec![], // Terminal state
        }
    }
    
    /// Encode lifecycle event as ArxObject
    pub fn event_to_arxobject(
        wo_id: u16,
        event: &LifecycleEvent,
        building_id: u16,
    ) -> ArxObject {
        ArxObject {
            building_id,
            object_type: 0xF9, // Lifecycle event type
            x: wo_id,
            y: u16::from_le_bytes([event.event_type as u8, 0]),
            z: event.user_id,
            properties: [
                ((event.timestamp >> 24) & 0xFF) as u8,
                ((event.timestamp >> 16) & 0xFF) as u8,
                ((event.timestamp >> 8) & 0xFF) as u8,
                (event.timestamp & 0xFF) as u8,
            ],
        }
    }
    
    /// Decode lifecycle event from ArxObject
    pub fn event_from_arxobject(obj: &ArxObject) -> Option<(u16, LifecycleEvent)> {
        if obj.object_type != 0xF9 {
            return None;
        }
        
        let wo_id = obj.x;
        let event = LifecycleEvent {
            event_type: match (((obj.y as u16) & 0x00FF) as u8) {
                1 => WOLifecycleEvent::Created,
                2 => WOLifecycleEvent::Assigned,
                3 => WOLifecycleEvent::Started,
                4 => WOLifecycleEvent::Paused,
                5 => WOLifecycleEvent::Resumed,
                6 => WOLifecycleEvent::Completed,
                7 => WOLifecycleEvent::Verified,
                8 => WOLifecycleEvent::Closed,
                9 => WOLifecycleEvent::Cancelled,
                10 => WOLifecycleEvent::Escalated,
                _ => return None,
            },
            timestamp: u32::from_be_bytes(obj.properties) as u64,
            user_id: obj.z,
            notes: None, // Notes stored separately if needed
        };
        
        Some((wo_id, event))
    }
}

/// Work order assignment packet
#[derive(Debug, Clone, Copy)]
pub struct WOAssignment {
    pub wo_id: u16,
    pub tech_id: u16,
    pub priority: Priority,
    pub due_hours: u8,
}

impl WOAssignment {
    /// Encode as ArxObject
    pub fn to_arxobject(&self, building_id: u16) -> ArxObject {
        ArxObject {
            building_id,
            object_type: 0xF8, // Assignment type
            x: self.wo_id,
            y: self.tech_id,
            z: u16::from_le_bytes([self.priority as u8, self.due_hours]),
            properties: [0; 4], // Reserved
        }
    }
    
    /// Decode from ArxObject
    pub fn from_arxobject(obj: &ArxObject) -> Option<Self> {
        if obj.object_type != 0xF8 {
            return None;
        }
        
        Some(Self {
            wo_id: obj.x as u16,
            tech_id: obj.y as u16,
            priority: match (((obj.z as u16) & 0x00FF) as u8) {
                1 => Priority::Low,
                2 => Priority::Medium,
                3 => Priority::High,
                4 => Priority::Critical,
                5 => Priority::Emergency,
                _ => return None,
            },
            due_hours: (((obj.z as u16) >> 8) & 0x00FF) as u8,
        })
    }
}

/// Work order completion packet
#[derive(Debug, Clone, Copy)]
pub struct WOCompletion {
    pub wo_id: u16,
    pub tech_id: u16,
    pub changes_made: u8,
    pub time_spent_minutes: u16,
    pub parts_used: u8,
}

impl WOCompletion {
    /// Encode as ArxObject
    pub fn to_arxobject(&self, building_id: u16) -> ArxObject {
        ArxObject {
            building_id,
            object_type: 0xF7, // Completion type
            x: self.wo_id,
            y: self.tech_id,
            z: self.time_spent_minutes,
            properties: [
                self.changes_made,
                self.parts_used,
                0,
                0,
            ],
        }
    }
    
    /// Decode from ArxObject  
    pub fn from_arxobject(obj: &ArxObject) -> Option<Self> {
        if obj.object_type != 0xF7 {
            return None;
        }
        
        Some(Self {
            wo_id: obj.x,
            tech_id: obj.y,
            changes_made: obj.properties[0],
            time_spent_minutes: obj.z,
            parts_used: obj.properties[1],
        })
    }
}

/// Complete work order flow in 13-byte packets
pub fn demo_complete_lifecycle() {
    println!("\n📦 Work Order Lifecycle in 13 Bytes\n");
    
    println!("Complete flow over mesh network:");
    println!("════════════════════════════════\n");
    
    // 1. Creation
    println!("1️⃣ CREATE (Facility Manager)");
    let wo = WorkOrder {
        wo_id: 0x0042,
        work_type: WorkType::Corrective,
        priority: Priority::High,
        assigned_to: None,
        location: crate::terminal_cmms::Location {
            building_id: 0x0001,
            room: 203,
            equipment_id: Some(0x1234),
        },
        status: WorkOrderStatus::Open,
        session: crate::terminal_cmms::TerminalSession::new(0),
        branch_name: "wo-0042".to_string(),
        created_at: current_timestamp(),
        due_date: current_timestamp() + 14400, // 4 hours
    };
    
    let create_packet = wo.to_arxobject();
    println!("   Packet: {:02X?}", &create_packet.to_bytes()[0..8]);
    println!("   Size: 13 bytes");
    println!("   Status: OPEN\n");
    
    // 2. Assignment
    println!("2️⃣ ASSIGN (Dispatch)");
    let assignment = WOAssignment {
        wo_id: 0x0042,
        tech_id: 0x0100, // Tech's user ID
        priority: Priority::High,
        due_hours: 4,
    };
    
    let assign_packet = assignment.to_arxobject(0x0001);
    println!("   Packet: {:02X?}", &assign_packet.to_bytes()[0..8]);
    println!("   Tech: 0x{:04X}", assignment.tech_id);
    println!("   Due: {} hours\n", assignment.due_hours);
    
    // 3. Start work
    println!("3️⃣ START (Technician)");
    let mut lifecycle = WorkOrderLifecycle::new();
    lifecycle.transition(WorkOrderStatus::InProgress, 0x0100, 
        Some("Starting work".to_string())).unwrap();
    
    let start_event = &lifecycle.events.last().unwrap();
    let start_packet = WorkOrderLifecycle::event_to_arxobject(
        0x0042, start_event, 0x0001
    );
    println!("   Packet: {:02X?}", &start_packet.to_bytes()[0..8]);
    println!("   Status: IN PROGRESS");
    println!("   Branch: wo-0042 created\n");
    
    // 4. Complete work
    println!("4️⃣ COMPLETE (Technician)");
    let completion = WOCompletion {
        wo_id: 0x0042,
        tech_id: 0x0100,
        changes_made: 3,
        time_spent_minutes: 45,
        parts_used: 1,
    };
    
    let complete_packet = completion.to_arxobject(0x0001);
    println!("   Packet: {:02X?}", &complete_packet.to_bytes()[0..8]);
    println!("   Changes: {}", completion.changes_made);
    println!("   Time: {} min", completion.time_spent_minutes);
    println!("   Parts: {}\n", completion.parts_used);
    
    // 5. Verify and close
    println!("5️⃣ VERIFY & CLOSE (Manager)");
    lifecycle.transition(WorkOrderStatus::Verified, 0x0001, 
        Some("Work verified".to_string())).unwrap();
    lifecycle.transition(WorkOrderStatus::Closed, 0x0001, None).unwrap();
    
    let close_event = &lifecycle.events.last().unwrap();
    let close_packet = WorkOrderLifecycle::event_to_arxobject(
        0x0042, close_event, 0x0001
    );
    println!("   Packet: {:02X?}", &close_packet.to_bytes()[0..8]);
    println!("   Status: CLOSED");
    println!("   Branch: Merged to main\n");
    
    println!("Total data transmitted:");
    println!("  5 packets × 13 bytes = 65 bytes");
    println!("  Complete work order lifecycle!");
}

/// Show state machine
pub fn demo_state_machine() {
    println!("\n🔄 Work Order State Machine\n");
    
    println!("Valid state transitions:");
    println!("═══════════════════════\n");
    
    println!("OPEN");
    println!(" ├→ ASSIGNED");
    println!(" └→ CANCELLED\n");
    
    println!("ASSIGNED");
    println!(" ├→ IN_PROGRESS");
    println!(" ├→ OPEN (unassign)");
    println!(" └→ CANCELLED\n");
    
    println!("IN_PROGRESS");
    println!(" ├→ PAUSED");
    println!(" ├→ COMPLETED");
    println!(" └→ CANCELLED\n");
    
    println!("PAUSED");
    println!(" ├→ IN_PROGRESS (resume)");
    println!(" └→ CANCELLED\n");
    
    println!("COMPLETED");
    println!(" ├→ VERIFIED");
    println!(" └→ IN_PROGRESS (rework)\n");
    
    println!("VERIFIED");
    println!(" └→ CLOSED\n");
    
    println!("CLOSED / CANCELLED");
    println!(" (terminal states)\n");
    
    println!("Each transition:");
    println!("  • Validates state machine rules");
    println!("  • Records event with timestamp");
    println!("  • Transmits as 13-byte packet");
    println!("  • Updates branch status");
}

/// Scheduled maintenance
pub fn demo_scheduled_maintenance() {
    println!("\n📅 Scheduled Maintenance\n");
    
    println!("Daily schedule generation:");
    println!("═════════════════════════\n");
    
    println!("Every morning at 6:00 AM:");
    println!("1. Check maintenance schedule");
    println!("2. Generate work orders for due tasks");
    println!("3. Assign based on tech availability");
    println!("4. Send via mesh network\n");
    
    println!("Example schedule:");
    println!("┌────────────────────────────────────┐");
    println!("│ Monday Maintenance Schedule        │");
    println!("├────────────────────────────────────┤");
    println!("│ WO#0101 - HVAC Filter (Monthly)   │");
    println!("│   → Tech: Auto-assign              │");
    println!("│   → Due: EOD                       │");
    println!("│                                    │");
    println!("│ WO#0102 - Fire Extinguisher Check │");
    println!("│   → Tech: Safety team              │");
    println!("│   → Due: This week                │");
    println!("│                                    │");
    println!("│ WO#0103 - Generator Test          │");
    println!("│   → Tech: Electrical               │");
    println!("│   → Due: Today (Critical)         │");
    println!("└────────────────────────────────────┘\n");
    
    println!("Auto-generated as 13-byte packets:");
    println!("  3 work orders = 39 bytes total");
    println!("  Transmitted at 6:00 AM");
    println!("  Techs receive on arrival");
}

fn current_timestamp() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs()
}
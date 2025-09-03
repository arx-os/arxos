//! Terminal-based CMMS (Computerized Maintenance Management System)
//! 
//! Work orders are just terminal sessions. Each tab = one work order.
//! Everything in ASCII, everything in 13 bytes over mesh.

use crate::arxobject::ArxObject;
use crate::building_repository::BuildingBranch;
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

/// Work Order as a terminal session
#[derive(Debug, Clone)]
pub struct WorkOrder {
    /// Work order ID (fits in 2 bytes)
    pub wo_id: u16,
    
    /// Type of work
    pub work_type: WorkType,
    
    /// Priority level
    pub priority: Priority,
    
    /// Assigned technician
    pub assigned_to: Option<u16>, // User ID
    
    /// Location in building
    pub location: Location,
    
    /// Status
    pub status: WorkOrderStatus,
    
    /// Terminal session state
    pub session: TerminalSession,
    
    /// Associated branch for changes
    pub branch_name: String,
    
    /// Created/updated timestamps
    pub created_at: u64,
    pub due_date: u64,
}

#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum WorkType {
    Preventive = 1,      // Scheduled maintenance
    Corrective = 2,      // Fix something broken  
    Emergency = 3,       // Urgent repair
    Inspection = 4,      // Routine inspection
    Installation = 5,    // New equipment
    Upgrade = 6,         // System improvement
}

#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum Priority {
    Low = 1,
    Medium = 2,
    High = 3,
    Critical = 4,
    Emergency = 5,
}

#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum WorkOrderStatus {
    Open = 1,
    Assigned = 2,
    InProgress = 3,
    Paused = 4,
    Completed = 5,
    Verified = 6,
    Closed = 7,
}

#[derive(Debug, Clone)]
pub struct Location {
    pub building_id: u16,
    pub room: u16,
    pub equipment_id: Option<u16>,
}

/// Terminal session for a work order
#[derive(Debug, Clone)]
pub struct TerminalSession {
    /// Session ID (tab number)
    pub tab_id: u8,
    
    /// Terminal buffer (what's displayed)
    pub buffer: Vec<String>,
    
    /// Command history
    pub history: Vec<String>,
    
    /// Current context (where in building)
    pub context: WorkContext,
    
    /// Session active
    pub active: bool,
}

#[derive(Debug, Clone)]
pub struct WorkContext {
    pub current_room: u16,
    pub viewing: Vec<ArxObject>,
    pub changes_made: usize,
}

impl WorkOrder {
    /// Create work order from 13-byte ArxObject
    pub fn from_arxobject(obj: &ArxObject) -> Option<Self> {
        if obj.object_type != 0xFA { // Work order type
            return None;
        }
        
        Some(Self {
            wo_id: obj.x,
            work_type: unsafe { std::mem::transmute((obj.y & 0xFF) as u8) },
            priority: unsafe { std::mem::transmute((obj.y >> 8) as u8) },
            assigned_to: if obj.z > 0 { Some(obj.z) } else { None },
            location: Location {
                building_id: obj.building_id,
                room: u16::from_le_bytes([obj.properties[0], obj.properties[1]]),
                equipment_id: {
                    let id = u16::from_le_bytes([obj.properties[2], obj.properties[3]]);
                    if id > 0 { Some(id) } else { None }
                },
            },
            status: WorkOrderStatus::Open,
            session: TerminalSession::new(0),
            branch_name: format!("wo-{:04x}", obj.x),
            created_at: current_timestamp(),
            due_date: current_timestamp() + 86400, // 24 hours default
        })
    }
    
    /// Encode as ArxObject for mesh transmission
    pub fn to_arxobject(&self) -> ArxObject {
        ArxObject {
            building_id: self.location.building_id,
            object_type: 0xFA, // Work order type
            x: self.wo_id,
            y: u16::from_le_bytes([self.work_type as u8, self.priority as u8]),
            z: self.assigned_to.unwrap_or(0),
            properties: [
                (self.location.room & 0xFF) as u8,
                (self.location.room >> 8) as u8,
                (self.location.equipment_id.unwrap_or(0) & 0xFF) as u8,
                (self.location.equipment_id.unwrap_or(0) >> 8) as u8,
            ],
        }
    }
}

impl TerminalSession {
    fn new(tab_id: u8) -> Self {
        Self {
            tab_id,
            buffer: Vec::new(),
            history: Vec::new(),
            context: WorkContext {
                current_room: 0,
                viewing: Vec::new(),
                changes_made: 0,
            },
            active: true,
        }
    }
    
    /// Render work order as ASCII terminal
    pub fn render(&self, wo: &WorkOrder) -> String {
        let mut output = String::new();
        
        // Header
        output.push_str(&format!("╔══════════════════════════════════════════╗\n"));
        output.push_str(&format!("║ Work Order #{:04X}    Tab {}              ║\n", wo.wo_id, self.tab_id));
        output.push_str(&format!("╚══════════════════════════════════════════╝\n\n"));
        
        // Work order details
        output.push_str(&format!("Type:     {:?}\n", wo.work_type));
        output.push_str(&format!("Priority: {:?}\n", wo.priority));
        output.push_str(&format!("Status:   {:?}\n", wo.status));
        output.push_str(&format!("Location: Room {}\n", wo.location.room));
        
        if let Some(equip) = wo.location.equipment_id {
            output.push_str(&format!("Equipment: #{:04X}\n", equip));
        }
        
        output.push_str(&format!("Branch:   {}\n", wo.branch_name));
        output.push_str(&format!("Changes:  {}\n", self.context.changes_made));
        
        output.push_str("\n─────────────────────────────────────────\n\n");
        
        // Session buffer
        for line in self.buffer.iter().rev().take(20) {
            output.push_str(line);
            output.push('\n');
        }
        
        output.push_str("\n> ");
        
        output
    }
}

/// CMMS Manager - handles all work orders
pub struct TerminalCMMS {
    /// All work orders
    work_orders: HashMap<u16, WorkOrder>,
    
    /// Active terminal sessions (tabs)
    sessions: Vec<TerminalSession>,
    
    /// Current active tab
    active_tab: u8,
    
    /// Scheduled maintenance
    schedule: MaintenanceSchedule,
}

/// Maintenance schedule
pub struct MaintenanceSchedule {
    /// Preventive maintenance tasks
    preventive: Vec<ScheduledTask>,
    
    /// Recurring tasks
    recurring: Vec<RecurringTask>,
}

#[derive(Debug, Clone)]
pub struct ScheduledTask {
    pub equipment_id: u16,
    pub task_type: WorkType,
    pub due_date: u64,
    pub frequency_days: u16,
    pub last_completed: Option<u64>,
}

#[derive(Debug, Clone)]
pub struct RecurringTask {
    pub name: String,
    pub equipment_pattern: String, // e.g., "all_hvac", "thermostats"
    pub frequency_days: u16,
    pub work_type: WorkType,
}

impl TerminalCMMS {
    pub fn new() -> Self {
        Self {
            work_orders: HashMap::new(),
            sessions: Vec::new(),
            active_tab: 0,
            schedule: MaintenanceSchedule {
                preventive: Vec::new(),
                recurring: Vec::new(),
            },
        }
    }
    
    /// Create new work order (opens new tab)
    pub fn create_work_order(
        &mut self,
        work_type: WorkType,
        priority: Priority,
        location: Location,
    ) -> u16 {
        let wo_id = (self.work_orders.len() as u16) + 1;
        let tab_id = self.sessions.len() as u8;
        
        let mut wo = WorkOrder {
            wo_id,
            work_type,
            priority,
            assigned_to: None,
            location,
            status: WorkOrderStatus::Open,
            session: TerminalSession::new(tab_id),
            branch_name: format!("wo-{:04x}", wo_id),
            created_at: current_timestamp(),
            due_date: match priority {
                Priority::Emergency => current_timestamp() + 3600,     // 1 hour
                Priority::Critical => current_timestamp() + 14400,     // 4 hours
                Priority::High => current_timestamp() + 86400,         // 24 hours
                Priority::Medium => current_timestamp() + 259200,      // 3 days
                Priority::Low => current_timestamp() + 604800,         // 7 days
            },
        };
        
        wo.session.buffer.push(format!("Work Order #{:04X} created", wo_id));
        wo.session.buffer.push(format!("Branch: {}", wo.branch_name));
        wo.session.buffer.push("─────────────────────".to_string());
        
        self.sessions.push(wo.session.clone());
        self.work_orders.insert(wo_id, wo);
        
        wo_id
    }
    
    /// Switch between tabs
    pub fn switch_tab(&mut self, tab: u8) -> Result<(), &'static str> {
        if tab as usize >= self.sessions.len() {
            return Err("Tab does not exist");
        }
        
        self.active_tab = tab;
        Ok(())
    }
    
    /// Execute command in active tab
    pub fn execute_command(&mut self, command: &str) -> String {
        let wo_id = self.get_active_wo_id();
        
        if let Some(wo) = self.work_orders.get_mut(&wo_id) {
            wo.session.history.push(command.to_string());
            
            let response = match command {
                "status" => format!("Status: {:?}", wo.status),
                "start" => {
                    wo.status = WorkOrderStatus::InProgress;
                    wo.session.context.changes_made = 0;
                    "Work started. Recording changes in branch.".to_string()
                }
                "complete" => {
                    wo.status = WorkOrderStatus::Completed;
                    format!("Work completed. {} changes made.", wo.session.context.changes_made)
                }
                cmd if cmd.starts_with("note ") => {
                    let note = &cmd[5..];
                    wo.session.buffer.push(format!("📝 {}", note));
                    "Note added".to_string()
                }
                cmd if cmd.starts_with("show ") => {
                    self.show_equipment(&cmd[5..])
                }
                "changes" => {
                    format!("{} changes in branch {}", 
                        wo.session.context.changes_made, wo.branch_name)
                }
                _ => "Unknown command. Try: status, start, complete, note, show, changes".to_string(),
            };
            
            wo.session.buffer.push(format!("> {}", command));
            wo.session.buffer.push(response.clone());
            
            response
        } else {
            "No active work order".to_string()
        }
    }
    
    fn get_active_wo_id(&self) -> u16 {
        // Find work order for active tab
        self.work_orders.values()
            .find(|wo| wo.session.tab_id == self.active_tab)
            .map(|wo| wo.wo_id)
            .unwrap_or(0)
    }
    
    fn show_equipment(&self, equipment: &str) -> String {
        // Simulate showing equipment details
        format!("Equipment: {}\nStatus: Operational\nLast service: 30 days ago", equipment)
    }
    
    /// Generate daily work orders from schedule
    pub fn generate_scheduled_work_orders(&mut self) {
        let now = current_timestamp();
        
        for task in &self.schedule.preventive {
            if task.due_date <= now {
                let wo_id = self.create_work_order(
                    task.task_type,
                    Priority::Medium,
                    Location {
                        building_id: 0x0042,
                        room: 0,
                        equipment_id: Some(task.equipment_id),
                    },
                );
                
                if let Some(wo) = self.work_orders.get_mut(&wo_id) {
                    wo.session.buffer.push("📅 Scheduled maintenance task".to_string());
                }
            }
        }
    }
}

/// Terminal UI for CMMS
pub fn render_cmms_terminal(cmms: &TerminalCMMS) -> String {
    let mut output = String::new();
    
    // Tab bar
    output.push_str("┌");
    for i in 0..cmms.sessions.len() {
        if i == cmms.active_tab as usize {
            output.push_str(&format!("─[Tab {}]─", i));
        } else {
            output.push_str(&format!("──Tab {}──", i));
        }
    }
    output.push_str("─[+]─┐\n");
    
    // Active work order
    let wo_id = cmms.get_active_wo_id();
    if let Some(wo) = cmms.work_orders.get(&wo_id) {
        output.push_str(&wo.session.render(wo));
    } else {
        output.push_str("No active work order\n");
    }
    
    output
}

/// Demo: Multiple work orders as tabs
pub fn demo_terminal_cmms() {
    println!("\n📋 Terminal CMMS Demo\n");
    
    println!("Tech opens terminal on phone:");
    println!("════════════════════════════\n");
    
    println!("$ arx cmms");
    println!();
    
    println!("┌─[Tab 0]──Tab 1────Tab 2──[+]─┐");
    println!("║ Work Order #0001    Tab 0     ║");
    println!("╚═══════════════════════════════╝\n");
    
    println!("Type:     Corrective");
    println!("Priority: High");
    println!("Status:   InProgress");
    println!("Location: Room 203");
    println!("Equipment: Thermostat #0042");
    println!("Branch:   wo-0001");
    println!("Changes:  3\n");
    
    println!("─────────────────────────────────\n");
    
    println!("> start");
    println!("Work started. Recording changes in branch.\n");
    
    println!("> show thermostat");
    println!("Thermostat #0042");
    println!("Status: Failing");
    println!("Temp: 68°F (should be 72°F)\n");
    
    println!("> note Sensor failing, needs replacement");
    println!("📝 Note added\n");
    
    println!("> complete");
    println!("Work completed. 3 changes made.\n");
    
    println!("> _");
    
    println!("\nPress Ctrl+Tab to switch work orders");
    println!("Press Ctrl+N for new work order");
    println!("Press Ctrl+S to submit changes");
}

/// Show how this is better than traditional CMMS
pub fn demo_why_terminal_cmms() {
    println!("\n🎯 Why Terminal CMMS Works\n");
    
    println!("Traditional CMMS:");
    println!("  • Complex web interfaces");
    println!("  • Requires internet");
    println!("  • Slow on mobile");
    println!("  • Expensive licenses");
    println!("  • Training required");
    println!();
    
    println!("ArxOS Terminal CMMS:");
    println!("  • Simple ASCII interface");
    println!("  • Works over mesh (no internet)");
    println!("  • Fast on any device");
    println!("  • Free and open source");
    println!("  • Commands are intuitive");
    println!();
    
    println!("Work Order as 13 bytes:");
    let wo = WorkOrder {
        wo_id: 0x0042,
        work_type: WorkType::Corrective,
        priority: Priority::High,
        assigned_to: Some(0x0100),
        location: Location {
            building_id: 0x0001,
            room: 203,
            equipment_id: Some(0x1234),
        },
        status: WorkOrderStatus::InProgress,
        session: TerminalSession::new(0),
        branch_name: "wo-0042".to_string(),
        created_at: current_timestamp(),
        due_date: current_timestamp() + 86400,
    };
    
    let packet = wo.to_arxobject();
    println!("  {:02X?}", packet.to_bytes());
    println!();
    
    println!("That's a complete work order!");
}

fn current_timestamp() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs()
}
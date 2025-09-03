//! Work Order Tab Management - Multiple simultaneous work orders
//! 
//! Each work order is a terminal tab. Techs can have multiple
//! work orders open simultaneously, just like browser tabs.

use crate::terminal_cmms::{WorkOrder, WorkOrderStatus, WorkType, Priority};
use crate::building_repository::BuildingRepository;
use std::collections::HashMap;

/// Terminal with multiple work order tabs
pub struct WorkOrderTerminal {
    /// All tabs
    pub tabs: Vec<WorkOrderTab>,
    
    /// Active tab index
    pub active_tab: usize,
    
    /// Terminal dimensions
    pub width: usize,
    pub height: usize,
    
    /// Tab shortcuts
    pub shortcuts: HashMap<String, usize>,
}

/// Individual work order tab
#[derive(Debug, Clone)]
pub struct WorkOrderTab {
    /// Tab ID
    pub id: usize,
    
    /// Work order
    pub work_order: WorkOrder,
    
    /// Tab title (short description)
    pub title: String,
    
    /// Terminal buffer for this tab
    pub buffer: TerminalBuffer,
    
    /// Command prompt
    pub prompt: String,
    
    /// Tab state
    pub state: TabState,
}

#[derive(Debug, Clone)]
pub enum TabState {
    Active,      // Currently being worked on
    Background,  // Open but not active
    Suspended,   // Paused work
    Completed,   // Ready to close
}

/// Terminal buffer for a tab
#[derive(Debug, Clone)]
pub struct TerminalBuffer {
    /// Display lines
    pub lines: Vec<String>,
    
    /// Scroll position
    pub scroll: usize,
    
    /// Command history
    pub history: Vec<String>,
    
    /// History position
    pub history_pos: usize,
    
    /// Input buffer
    pub input: String,
}

impl WorkOrderTerminal {
    pub fn new() -> Self {
        Self {
            tabs: Vec::new(),
            active_tab: 0,
            width: 80,
            height: 24,
            shortcuts: HashMap::new(),
        }
    }
    
    /// Open new work order tab
    pub fn open_tab(&mut self, work_order: WorkOrder) -> usize {
        let tab_id = self.tabs.len();
        let title = format!("WO#{:04X}", work_order.wo_id);
        
        let mut buffer = TerminalBuffer::new();
        buffer.lines.push(format!("═══ Work Order #{:04X} ═══", work_order.wo_id));
        buffer.lines.push(format!("Type: {:?}", work_order.work_type));
        buffer.lines.push(format!("Priority: {:?}", work_order.priority));
        buffer.lines.push(format!("Location: Room {}", work_order.location.room));
        buffer.lines.push("─────────────────────".to_string());
        buffer.lines.push("Type 'help' for commands".to_string());
        buffer.lines.push("".to_string());
        
        let tab = WorkOrderTab {
            id: tab_id,
            work_order,
            title: title.clone(),
            buffer,
            prompt: format!("wo#{:04x}> ", work_order.wo_id),
            state: TabState::Active,
        };
        
        // Add shortcut
        self.shortcuts.insert(format!("{}", tab_id + 1), tab_id);
        self.shortcuts.insert(title, tab_id);
        
        self.tabs.push(tab);
        self.active_tab = tab_id;
        
        tab_id
    }
    
    /// Switch to tab
    pub fn switch_tab(&mut self, tab: usize) -> Result<(), &'static str> {
        if tab >= self.tabs.len() {
            return Err("Tab does not exist");
        }
        
        // Suspend current tab
        if self.active_tab < self.tabs.len() {
            self.tabs[self.active_tab].state = TabState::Background;
        }
        
        // Activate new tab
        self.active_tab = tab;
        self.tabs[tab].state = TabState::Active;
        
        Ok(())
    }
    
    /// Close tab
    pub fn close_tab(&mut self, tab: usize) -> Result<(), &'static str> {
        if tab >= self.tabs.len() {
            return Err("Tab does not exist");
        }
        
        // Check if work order is completed
        if !matches!(self.tabs[tab].work_order.status, 
                    WorkOrderStatus::Completed | WorkOrderStatus::Closed) {
            return Err("Complete work order before closing tab");
        }
        
        self.tabs.remove(tab);
        
        // Adjust active tab if needed
        if self.active_tab >= self.tabs.len() && !self.tabs.is_empty() {
            self.active_tab = self.tabs.len() - 1;
        }
        
        Ok(())
    }
    
    /// Execute command in active tab
    pub fn execute_command(&mut self, input: &str) -> String {
        if self.tabs.is_empty() {
            return "No tabs open. Use 'new' to create work order.".to_string();
        }
        
        let tab = &mut self.tabs[self.active_tab];
        tab.buffer.history.push(input.to_string());
        
        // Parse command
        let parts: Vec<&str> = input.split_whitespace().collect();
        if parts.is_empty() {
            return String::new();
        }
        
        let response = match parts[0] {
            // Tab management
            "tab" | "t" => {
                if parts.len() > 1 {
                    match self.switch_to_tab_by_ref(parts[1]) {
                        Ok(()) => format!("Switched to tab {}", self.active_tab),
                        Err(e) => e.to_string(),
                    }
                } else {
                    self.list_tabs()
                }
            }
            "close" => {
                match self.close_tab(self.active_tab) {
                    Ok(()) => "Tab closed".to_string(),
                    Err(e) => e.to_string(),
                }
            }
            
            // Work order commands
            "start" => {
                tab.work_order.status = WorkOrderStatus::InProgress;
                tab.buffer.lines.push("✓ Work started".to_string());
                "Recording changes in branch".to_string()
            }
            "pause" => {
                tab.work_order.status = WorkOrderStatus::Paused;
                tab.state = TabState::Suspended;
                "Work paused. Tab suspended.".to_string()
            }
            "resume" => {
                tab.work_order.status = WorkOrderStatus::InProgress;
                tab.state = TabState::Active;
                "Work resumed".to_string()
            }
            "complete" => {
                tab.work_order.status = WorkOrderStatus::Completed;
                tab.state = TabState::Completed;
                tab.buffer.lines.push("✓ Work completed".to_string());
                "Ready for review. Use 'submit' to create merge request.".to_string()
            }
            "submit" => {
                if matches!(tab.work_order.status, WorkOrderStatus::Completed) {
                    "Creating merge request from branch...".to_string()
                } else {
                    "Complete work order before submitting".to_string()
                }
            }
            
            // Information commands
            "status" | "s" => {
                format!("Status: {:?}\nTab: {:?}", 
                    tab.work_order.status, tab.state)
            }
            "info" | "i" => {
                self.show_work_order_info(self.active_tab)
            }
            
            // Notes and documentation
            "note" | "n" => {
                if parts.len() > 1 {
                    let note = parts[1..].join(" ");
                    tab.buffer.lines.push(format!("📝 {}", note));
                    "Note added".to_string()
                } else {
                    "Usage: note <text>".to_string()
                }
            }
            
            // Help
            "help" | "?" => {
                self.show_help()
            }
            
            _ => format!("Unknown command: {}. Type 'help' for commands.", parts[0]),
        };
        
        // Add to buffer
        tab.buffer.lines.push(format!("{} {}", tab.prompt, input));
        tab.buffer.lines.push(response.clone());
        tab.buffer.input.clear();
        
        response
    }
    
    fn switch_to_tab_by_ref(&mut self, reference: &str) -> Result<(), &'static str> {
        // Try as number
        if let Ok(num) = reference.parse::<usize>() {
            return self.switch_tab(num - 1); // 1-indexed for users
        }
        
        // Try as shortcut
        if let Some(&tab) = self.shortcuts.get(reference) {
            return self.switch_tab(tab);
        }
        
        Err("Tab not found")
    }
    
    fn list_tabs(&self) -> String {
        let mut output = String::new();
        output.push_str("Open tabs:\n");
        
        for (i, tab) in self.tabs.iter().enumerate() {
            let marker = if i == self.active_tab { "▶" } else { " " };
            let status_icon = match tab.work_order.status {
                WorkOrderStatus::Open => "○",
                WorkOrderStatus::InProgress => "◐",
                WorkOrderStatus::Paused => "⏸",
                WorkOrderStatus::Completed => "✓",
                _ => " ",
            };
            
            output.push_str(&format!("{} {} [{}] {} - {:?}\n",
                marker, i + 1, status_icon, tab.title, tab.work_order.work_type));
        }
        
        output
    }
    
    fn show_work_order_info(&self, tab_idx: usize) -> String {
        if tab_idx >= self.tabs.len() {
            return "Invalid tab".to_string();
        }
        
        let tab = &self.tabs[tab_idx];
        let wo = &tab.work_order;
        
        format!(
            "Work Order #{:04X}\n\
             Type: {:?}\n\
             Priority: {:?}\n\
             Status: {:?}\n\
             Location: Room {}\n\
             Branch: {}\n\
             Created: {} minutes ago",
            wo.wo_id,
            wo.work_type,
            wo.priority,
            wo.status,
            wo.location.room,
            wo.branch_name,
            (current_timestamp() - wo.created_at) / 60
        )
    }
    
    fn show_help(&self) -> String {
        "Work Order Commands:\n\
         start     - Begin work\n\
         pause     - Pause work\n\
         resume    - Resume work\n\
         complete  - Mark complete\n\
         submit    - Submit changes\n\
         note TEXT - Add note\n\
         \n\
         Tab Commands:\n\
         tab N     - Switch to tab N\n\
         tab       - List all tabs\n\
         close     - Close current tab\n\
         \n\
         Shortcuts:\n\
         Ctrl+Tab  - Next tab\n\
         Ctrl+N    - New work order\n\
         Ctrl+W    - Close tab".to_string()
    }
}

impl TerminalBuffer {
    fn new() -> Self {
        Self {
            lines: Vec::new(),
            scroll: 0,
            history: Vec::new(),
            history_pos: 0,
            input: String::new(),
        }
    }
}

/// Render terminal with tabs
pub fn render_tabbed_terminal(terminal: &WorkOrderTerminal) -> String {
    let mut output = String::new();
    
    // Tab bar
    output.push_str("┌");
    for (i, tab) in terminal.tabs.iter().enumerate() {
        let status = match tab.work_order.status {
            WorkOrderStatus::InProgress => "●",
            WorkOrderStatus::Paused => "⏸",
            WorkOrderStatus::Completed => "✓",
            _ => " ",
        };
        
        if i == terminal.active_tab {
            output.push_str(&format!("═[{} {}]═", status, tab.title));
        } else {
            output.push_str(&format!("──{} {}──", status, tab.title));
        }
    }
    output.push_str("─[+]─┐\n");
    
    // Active tab content
    if terminal.active_tab < terminal.tabs.len() {
        let tab = &terminal.tabs[terminal.active_tab];
        
        // Show last N lines that fit in terminal
        let start = if tab.buffer.lines.len() > terminal.height - 3 {
            tab.buffer.lines.len() - (terminal.height - 3)
        } else {
            0
        };
        
        for line in &tab.buffer.lines[start..] {
            output.push_str(line);
            output.push('\n');
        }
        
        // Input line
        output.push_str(&format!("{} {}", tab.prompt, tab.buffer.input));
    }
    
    output
}

/// Demo multiple simultaneous work orders
pub fn demo_multiple_work_orders() {
    println!("\n🗂️ Multiple Work Orders Demo\n");
    
    println!("Tech has 3 work orders open:");
    println!("═══════════════════════════\n");
    
    println!("┌═[● WO#0001]═──✓ WO#0002────⏸ WO#0003──[+]─┐");
    println!("║ Work Order #0001              Tab 1        ║");
    println!("║ Type: Corrective                           ║");
    println!("║ Priority: High                             ║");
    println!("║ Status: InProgress                         ║");
    println!("║ Location: Room 203                         ║");
    println!("║                                            ║");
    println!("║ 10:15> start                               ║");
    println!("║ Recording changes in branch                ║");
    println!("║                                            ║");
    println!("║ 10:18> note Thermostat sensor failing     ║");
    println!("║ 📝 Thermostat sensor failing              ║");
    println!("║                                            ║");
    println!("║ 10:22> tab 2                               ║");
    println!("║ Switched to tab 2                          ║");
    println!("║                                            ║");
    println!("║ wo#0001> _                                 ║");
    println!("└────────────────────────────────────────────┘");
    println!();
    
    println!("Tab Status:");
    println!("  Tab 1: WO#0001 - HVAC repair (IN PROGRESS)");
    println!("  Tab 2: WO#0002 - Filter change (COMPLETED)");
    println!("  Tab 3: WO#0003 - Inspection (PAUSED)");
    println!();
    
    println!("Keyboard shortcuts:");
    println!("  Ctrl+Tab    Next tab");
    println!("  Ctrl+1/2/3  Jump to tab");
    println!("  Ctrl+W      Close tab");
    println!("  Ctrl+N      New work order");
}

/// Show workflow
pub fn demo_tab_workflow() {
    println!("\n📋 Tab-Based Workflow\n");
    
    println!("Morning: Tech receives 5 work orders");
    println!("════════════════════════════════════\n");
    
    println!("1. Opens terminal, all 5 WOs appear as tabs");
    println!("2. Starts with highest priority (Tab 1)");
    println!("3. Needs parts for Tab 1, pauses it");
    println!("4. Switches to Tab 2, completes it");
    println!("5. Submits Tab 2 changes");
    println!("6. Closes Tab 2");
    println!("7. Moves to Tab 3");
    println!("8. Gets call about emergency");
    println!("9. Opens new tab (Ctrl+N) for emergency");
    println!("10. Handles emergency in new tab");
    println!("11. Returns to Tab 1 when parts arrive");
    println!();
    
    println!("Benefits:");
    println!("  • Context switching is instant");
    println!("  • Each WO has its own branch");
    println!("  • Can pause/resume anytime");
    println!("  • History per tab");
    println!("  • Changes isolated");
}

fn current_timestamp() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs()
}
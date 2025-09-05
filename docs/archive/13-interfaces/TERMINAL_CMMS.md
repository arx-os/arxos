# ArxOS Terminal CMMS - Work Orders as Tabs

## The Insight

CMMS doesn't need to be fancy. Work orders are just terminal sessions. Each work order = one tab. Technicians can have multiple tabs open simultaneously, switching between them instantly. Everything in ASCII, everything in 13 bytes.

## Why This Works

### Traditional CMMS
- Complex web interfaces
- Requires constant internet
- Expensive licenses ($50-500/user/month)
- Slow on mobile devices
- Extensive training required
- Megabytes of data transfer

### ArxOS Terminal CMMS
- Simple ASCII terminal
- Works over 900MHz mesh (no internet)
- Free and open source
- Fast on any device (even flip phones)
- Intuitive commands
- 13 bytes per operation

## How It Works

### 1. Work Order Creation
```bash
Manager creates work order:
$ arx wo new --type corrective --priority high --room 203

Work Order #0042 created
Branch: wo-0042
Tab: Opens automatically
```

### 2. Tech Receives Work Order
Tech's terminal shows:
```
┌═[● WO#0042]═──○ WO#0043────○ WO#0044──[+]─┐
║ Work Order #0042            Tab 1          ║
║ Type: Corrective                           ║
║ Priority: High                             ║
║ Status: Open                               ║
║ Location: Room 203                         ║
║ Equipment: Thermostat #1234                ║
║                                            ║
║ wo#0042> _                                 ║
└────────────────────────────────────────────┘
```

### 3. Multiple Tabs = Multiple Work Orders

Tech can have several work orders open:
```
Tab 1: WO#0042 - Thermostat repair (IN PROGRESS)
Tab 2: WO#0043 - Filter change (OPEN)
Tab 3: WO#0044 - Inspection (PAUSED)

Ctrl+Tab to switch
Ctrl+N for new
Ctrl+W to close completed
```

### 4. Working in a Tab

Each tab is a full terminal session:
```
wo#0042> start
✓ Work started. Recording changes in branch wo-0042

wo#0042> show thermostat
Thermostat #1234
Status: Failing
Current: 68°F
Target: 72°F

wo#0042> note Sensor failing, needs replacement
📝 Note added

wo#0042> complete
✓ Work completed. 3 changes recorded.

wo#0042> submit
Creating merge request from branch wo-0042...
MR#142 created for review
```

## Tab Management

### Keyboard Shortcuts
- `Ctrl+Tab` - Next tab
- `Ctrl+Shift+Tab` - Previous tab
- `Ctrl+1/2/3...` - Jump to tab N
- `Ctrl+N` - New work order
- `Ctrl+W` - Close tab (if completed)
- `Ctrl+S` - Submit changes

### Tab Commands
```bash
tab         # List all tabs
tab 2       # Switch to tab 2
tab close   # Close current tab
tab new     # New work order tab
```

### Tab Status Icons
- `○` Open (not started)
- `●` In Progress (active work)
- `⏸` Paused (waiting)
- `✓` Completed (ready to close)
- `!` Urgent (needs attention)

## Work Order Lifecycle

### States & Transitions
```
OPEN → ASSIGNED → IN_PROGRESS → COMPLETED → VERIFIED → CLOSED
         ↓            ↓  ↑           ↓
     CANCELLED     PAUSED        IN_PROGRESS
                                  (rework)
```

### Each State Change = 13 Bytes
```rust
ArxObject {
    building_id: 0x0001,    // 2 bytes
    object_type: 0xF9,      // 1 byte (lifecycle)
    x: wo_id,               // 2 bytes
    y: [event|user],        // 2 bytes
    z: timestamp,           // 2 bytes
    properties: [details]   // 4 bytes
}
```

## Complete Flow Example

### Morning: Tech Arrives
```
$ arx cmms
Loading work orders...

5 work orders for today:
  1. WO#0042 - Thermostat (HIGH)
  2. WO#0043 - Filters (MEDIUM)
  3. WO#0044 - Inspection (LOW)
  4. WO#0045 - Outlet (MEDIUM)
  5. WO#0046 - Light (LOW)

Opening all as tabs...
```

### Working Through Orders
```
[Tab 1 Active]
wo#0042> start
wo#0042> [work happens]
wo#0042> pause  # Need parts

[Ctrl+Tab to Tab 2]
wo#0043> start
wo#0043> [complete filter change]
wo#0043> complete
wo#0043> submit

[Tab 2 closes after merge]
[Ctrl+Tab to Tab 3]
wo#0044> start
```

### Emergency Interruption
```
[Phone rings - emergency in Room 105]

Ctrl+N  # New tab
wo#0047> type emergency
wo#0047> room 105
wo#0047> start
wo#0047> [fix emergency]
wo#0047> complete
wo#0047> submit

[Return to other tabs]
```

## Scheduled Maintenance

### Automatic Generation
Every morning at 6 AM:
```rust
for task in scheduled_tasks {
    if task.due_today() {
        create_work_order(task)
        assign_to_tech(task.tech_type)
        send_via_mesh()
    }
}
```

### Recurring Tasks
```
Daily:
  - Safety walkthrough
  - Generator check

Weekly:
  - HVAC filter inspection
  - Emergency light test

Monthly:
  - Fire extinguisher check
  - Full equipment inspection

Quarterly:
  - Deep cleaning
  - Preventive maintenance
```

## Data Structure

### Work Order (13 bytes)
```rust
ArxObject {
    building_id: 0x0001,        // Building
    object_type: 0xFA,          // Work order
    x: wo_id,                   // WO number
    y: [type|priority],         // Type & priority
    z: assigned_to,             // Tech ID
    properties: [location]      // Room/equipment
}
```

### Assignment (13 bytes)
```rust
ArxObject {
    building_id: 0x0001,
    object_type: 0xF8,          // Assignment
    x: wo_id,                   // WO number
    y: tech_id,                 // Assigned to
    z: [priority|hours],        // Priority & due
    properties: [reserved]
}
```

### Completion (13 bytes)
```rust
ArxObject {
    building_id: 0x0001,
    object_type: 0xF7,          // Completion
    x: wo_id,                   // WO number
    y: tech_id,                 // Completed by
    z: time_spent,              // Minutes
    properties: [changes|parts] // Details
}
```

## Mobile Experience

### On Phone Terminal
```
╔════════════════════════╗
║ ArxOS CMMS            ║
║                       ║
║ [1]WO#42 [2]WO#43 [+] ║
║                       ║
║ WO#0042               ║
║ Thermostat Repair     ║
║ Room 203              ║
║                       ║
║ > start               ║
║ Work started          ║
║                       ║
║ > note Bad sensor     ║
║ 📝 Note added        ║
║                       ║
║ > _                   ║
╚════════════════════════╝
[Tab][Cmds][←][→][Send]
```

### Works on:
- iPhone/Android (native terminal)
- Tablets (multiple tabs visible)
- Flip phones (SMS commands)
- Radios (voice to text)

## Benefits

### For Technicians
- **Multiple work orders open** - No context switching delay
- **Full history per tab** - See what you did
- **Offline work** - No internet needed
- **Branch protection** - Can't break anything
- **Simple commands** - start, pause, complete

### For Managers
- **Real-time visibility** - See all open tabs/WOs
- **Branch review** - Approve changes before merge
- **Automatic scheduling** - Daily WO generation
- **Cost tracking** - Time and parts per WO
- **No training** - It's just a terminal

### For Schools
- **Free** - No licensing costs
- **Simple** - Janitors can use it
- **Reliable** - Works during outages
- **Integrated** - Same system as access control
- **Efficient** - 13 bytes vs megabytes

## The Magic

Traditional CMMS requires:
- Web servers
- Databases
- Internet
- Complex UI
- Training
- $$$$

ArxOS Terminal CMMS:
- Terminal tabs
- 13-byte packets
- Mesh network
- ASCII interface
- Intuitive
- Free

**Each work order is just a terminal tab with a branch.**

Simple. Practical. Brilliant.
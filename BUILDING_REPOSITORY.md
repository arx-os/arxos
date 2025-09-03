# ArxOS Building Repository - Git for Buildings

## The Concept

Buildings have a **main branch** that represents the truth - what's actually installed and configured. When contractors arrive, they don't modify main directly. Instead, they get a **branch** - an isolated workspace where they can propose changes. Once complete, their changes are reviewed and merged by facility management.

This is Git version control for physical infrastructure.

## Why This Matters

### The Problem
- Contractors directly modifying building systems
- No review before changes become "reality"
- Multiple contractors creating conflicts
- No audit trail of who changed what
- Can't rollback bad changes

### The Solution
- **Main branch** = protected truth
- **Contractor branches** = isolated workspaces
- **Merge requests** = proposed changes
- **Review process** = quality control
- **Full history** = complete audit trail

## How It Works

### 1. Contractor Arrives (SMS Access + Branch)
```bash
$ grant 555-0100 hvac 8h --branch
✅ SMS sent to 555-0100
✅ Created branch: hvac-repair-2024-01-15
✅ Branch expires: 8 hours
```

The contractor receives:
```
🏢 West High Building Access

Code: K7M3X9
Branch: hvac-repair-2024-01-15
Valid: 8 hours

You're working in an isolated branch.
Changes must be approved before merging.
```

### 2. Contractor Works in Branch

The contractor's radio/app shows they're in a branch:
```
📍 Branch: hvac-repair-2024-01-15
👤 User: HVAC Tech
⏱️ Expires: 6h remaining

Query: Show thermostats
[Returns objects from BRANCH, not main]
```

When they make changes:
```
Action: Replace thermostat-203
Reason: Unit failing
Status: ✅ Changed in branch (not in main)
```

### 3. Branch Isolation

What the contractor sees:
- Their own branch with their changes
- Can freely experiment and modify
- Changes don't affect production

What others see:
- Main branch (unchanged)
- Their own branches (if any)
- NOT the contractor's changes

### 4. Creating Merge Request

When work is complete:
```
$ arx submit-changes
Creating merge request from hvac-repair-2024-01-15

Title: Replace failed thermostat Room 203
Changes:
  🔧 Modify thermostat-203
  📝 Add inspection note
  ➕ Install new sensor

Submit? [Y/n]: Y
✅ Merge Request #42 created
```

### 5. Manager Reviews

```bash
$ arx review MR-42
```

```
═══════════════════════════════════════════════
 Merge Request #42
 Author: HVAC Tech (555-0100)
 Branch: hvac-repair-2024-01-15
═══════════════════════════════════════════════

CHANGES:
🔧 Modify Thermostat
   Location: Room 203
   Before: 68°F (failing sensor)
   After: 72°F (new unit)
   Cost: $300

📝 Inspection Note
   "Old unit 7 years old, warranty expired"

Risk: LOW
Total Cost: $300

[A]pprove [R]eject [C]omment [D]etails

Choice: A
✅ Approved - merging to main
```

### 6. Merge to Main

Once approved:
```
Merging branch hvac-repair-2024-01-15 → main
  ✓ Thermostat-203 updated
  ✓ Inspection note added
  ✓ Work order WO-2024-0142 generated
  ✓ Branch deleted
  ✓ Contractor notified via SMS

New commit: 0xAB3D2F89
Main branch updated successfully
```

## Branch Types

### Contractor Branch
- Full read access
- Write access to their branch only
- Changes require approval
- Auto-expires

### Inspector Branch
- Full read access
- Annotation only (no modifications)
- Findings require review
- Compliance tracking

### Emergency Branch
- Full read/write access
- Changes apply immediately
- Still tracked for audit
- Auto-expires after emergency

### Maintenance Branch
- Scheduled maintenance window
- Pre-approved changes
- Still reviewed after completion
- Historical record

## Data Structure (13 bytes!)

### Branch ID Packet
```rust
ArxObject {
    building_id: 0x0042,        // 2 bytes
    object_type: 0xFD,          // 1 byte (branch)
    x: branch_number,           // 2 bytes
    y: [session|type],          // 2 bytes
    z: expires_hours,           // 2 bytes
    properties: [reserved]      // 4 bytes
}
```

### Change Proposal Packet
```rust
ArxObject {
    building_id: 0x0042,        // 2 bytes
    object_type: 0xFC,          // 1 byte (change)
    x: object_id,               // 2 bytes
    y: [change_type|reason],    // 2 bytes
    z: severity,                // 2 bytes
    properties: [new_value]     // 4 bytes
}
```

## Real-World Scenarios

### Scenario 1: Routine Maintenance
```
Morning: HVAC tech arrives for monthly service
1. Gets branch via SMS
2. Inspects all units in branch
3. Marks 3 filters for replacement
4. Adjusts 2 thermostats
5. Submits merge request
6. Manager approves
7. Changes merged to main
8. Maintenance logged
```

### Scenario 2: Multiple Contractors
```
9:00 - HVAC tech in branch-17
9:15 - Electrician in branch-18
9:30 - Plumber in branch-19

All working simultaneously without conflicts!

10:00 - Manager reviews 3 merge requests
10:15 - Approves HVAC and plumber
10:20 - Requests changes from electrician
10:30 - Electrician resubmits
10:35 - All changes merged
```

### Scenario 3: Emergency Override
```
Fire alarm triggered!
- Fire marshal gets emergency branch
- All changes apply immediately to main
- Doors unlocked → instant
- HVAC stopped → instant
- Lights on → instant
- Still tracked in branch history
```

### Scenario 4: Rejected Changes
```
Contractor proposes: Delete camera-5

Manager reviews:
  ❌ Cannot delete security equipment
  Comment: "Camera required for compliance"
  Status: REJECTED

Contractor notified:
  "MR-99 rejected: Cannot delete security equipment"
```

## Benefits

### For Facility Managers
- **Control**: Review all changes before they're real
- **Visibility**: See exactly what contractors did
- **Safety**: Can't accidentally break critical systems
- **Audit**: Complete history of all changes

### For Contractors
- **Freedom**: Work without fear of breaking things
- **Clarity**: Know changes need approval
- **Documentation**: Work is recorded
- **Protection**: Can't be blamed for others' changes

### For Building Owners
- **Integrity**: Building data stays consistent
- **Compliance**: Full audit trail
- **Cost Control**: Review costs before approval
- **Quality**: Bad changes never reach production

## Integration with SMS Access

The complete flow:
```
1. grant 555-0100 hvac 8h --branch
   ↓
2. SMS: "Code: K7M3X9, Branch: hvac-repair-42"
   ↓
3. Contractor activates via SMS reply
   ↓
4. Automatic branch creation
   ↓
5. Work in isolated branch
   ↓
6. Submit changes for review
   ↓
7. Manager approves/rejects
   ↓
8. Merge to main (if approved)
   ↓
9. SMS confirmation to contractor
```

## The Magic

**Git's power, building's simplicity:**
- Version control for physical infrastructure
- Branches for contractor isolation
- Merge requests for change review
- 13-byte packets over mesh network
- No cloud required

## Implementation

All of this works over 900MHz LoRa mesh:
- Branch operations: 13 bytes each
- Change proposals: 13 bytes each
- Merge requests: 13 bytes × n changes
- Reviews: 13 bytes for approval

Total overhead for complete Git-like version control: **Kilobytes, not megabytes**

## Summary

> "Buildings should have version control just like code."

With ArxOS Building Repository:
- **Main branch** protects the truth
- **Contractor branches** enable safe work
- **Merge requests** require approval
- **Full history** provides audit trail
- **13 bytes** makes it work over mesh

This isn't just data management - it's **building integrity management**.
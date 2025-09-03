//! Merge Review System - Human-friendly change review
//! 
//! Shows building changes in a way facility managers understand.
//! Not code diffs, but "what's changing in my building."

use crate::arxobject::{ArxObject, object_types};
use crate::building_repository::{BuildingChange, MergeRequest, Severity};
use crate::branch_mesh_protocol::{ChangeProposal, ChangeType, ReasonCode};

/// Human-readable diff of building changes
pub struct BuildingDiff {
    /// Summary of changes
    pub summary: DiffSummary,
    
    /// Detailed changes by category
    pub changes_by_system: Vec<SystemChanges>,
    
    /// Risk assessment
    pub risk_level: RiskLevel,
    
    /// Cost implications
    pub estimated_cost: Option<f32>,
}

#[derive(Debug)]
pub struct DiffSummary {
    pub total_changes: usize,
    pub additions: usize,
    pub modifications: usize,
    pub deletions: usize,
    pub annotations: usize,
}

#[derive(Debug)]
pub struct SystemChanges {
    pub system_name: String,
    pub changes: Vec<HumanReadableChange>,
}

#[derive(Debug)]
pub struct HumanReadableChange {
    pub icon: char,
    pub description: String,
    pub location: String,
    pub severity: Severity,
    pub before: Option<String>,
    pub after: Option<String>,
}

#[derive(Debug, Clone, Copy)]
pub enum RiskLevel {
    Low,
    Medium,
    High,
    Critical,
}

/// Merge review interface
pub struct MergeReviewer;

impl MergeReviewer {
    /// Generate human-readable diff
    pub fn generate_diff(mr: &MergeRequest) -> BuildingDiff {
        let mut additions = 0;
        let mut modifications = 0;
        let mut deletions = 0;
        let mut annotations = 0;
        
        let mut hvac_changes = Vec::new();
        let mut electrical_changes = Vec::new();
        let mut safety_changes = Vec::new();
        let mut other_changes = Vec::new();
        
        for change in &mr.changes {
            match change {
                BuildingChange::Add { object, reason, .. } => {
                    additions += 1;
                    let readable = Self::format_add(object, reason);
                    Self::categorize_change(object.object_type, readable, 
                        &mut hvac_changes, &mut electrical_changes, 
                        &mut safety_changes, &mut other_changes);
                }
                BuildingChange::Modify { old, new, reason, .. } => {
                    modifications += 1;
                    let readable = Self::format_modify(old, new, reason);
                    Self::categorize_change(new.object_type, readable,
                        &mut hvac_changes, &mut electrical_changes,
                        &mut safety_changes, &mut other_changes);
                }
                BuildingChange::Remove { object, reason, .. } => {
                    deletions += 1;
                    let readable = Self::format_remove(object, reason);
                    Self::categorize_change(object.object_type, readable,
                        &mut hvac_changes, &mut electrical_changes,
                        &mut safety_changes, &mut other_changes);
                }
                BuildingChange::Annotate { note, severity, .. } => {
                    annotations += 1;
                    let readable = Self::format_annotate(note, *severity);
                    other_changes.push(readable);
                }
            }
        }
        
        let mut systems = Vec::new();
        
        if !hvac_changes.is_empty() {
            systems.push(SystemChanges {
                system_name: "HVAC System".to_string(),
                changes: hvac_changes,
            });
        }
        
        if !electrical_changes.is_empty() {
            systems.push(SystemChanges {
                system_name: "Electrical System".to_string(),
                changes: electrical_changes,
            });
        }
        
        if !safety_changes.is_empty() {
            systems.push(SystemChanges {
                system_name: "Safety Systems".to_string(),
                changes: safety_changes,
            });
        }
        
        if !other_changes.is_empty() {
            systems.push(SystemChanges {
                system_name: "Other".to_string(),
                changes: other_changes,
            });
        }
        
        BuildingDiff {
            summary: DiffSummary {
                total_changes: mr.changes.len(),
                additions,
                modifications,
                deletions,
                annotations,
            },
            changes_by_system: systems,
            risk_level: Self::assess_risk(&mr.changes),
            estimated_cost: Self::estimate_cost(&mr.changes),
        }
    }
    
    fn format_add(object: &ArxObject, reason: &str) -> HumanReadableChange {
        HumanReadableChange {
            icon: '➕',
            description: format!("Install new {}", Self::object_name(object.object_type)),
            location: Self::format_location(object),
            severity: Severity::Info,
            before: None,
            after: Some(reason.to_string()),
        }
    }
    
    fn format_modify(old: &ArxObject, new: &ArxObject, reason: &str) -> HumanReadableChange {
        HumanReadableChange {
            icon: '🔧',
            description: format!("Modify {}", Self::object_name(new.object_type)),
            location: Self::format_location(new),
            severity: Severity::Warning,
            before: Some(Self::format_state(old)),
            after: Some(Self::format_state(new)),
        }
    }
    
    fn format_remove(object: &ArxObject, reason: &str) -> HumanReadableChange {
        HumanReadableChange {
            icon: '❌',
            description: format!("Remove {}", Self::object_name(object.object_type)),
            location: Self::format_location(object),
            severity: Severity::Critical,
            before: Some(Self::format_state(object)),
            after: Some(format!("Removed: {}", reason)),
        }
    }
    
    fn format_annotate(note: &str, severity: Severity) -> HumanReadableChange {
        HumanReadableChange {
            icon: '📝',
            description: "Inspection note".to_string(),
            location: "Multiple locations".to_string(),
            severity,
            before: None,
            after: Some(note.to_string()),
        }
    }
    
    fn categorize_change(
        obj_type: u8,
        change: HumanReadableChange,
        hvac: &mut Vec<HumanReadableChange>,
        electrical: &mut Vec<HumanReadableChange>,
        safety: &mut Vec<HumanReadableChange>,
        other: &mut Vec<HumanReadableChange>,
    ) {
        match obj_type {
            9 | 10 => hvac.push(change), // HVAC_VENT, THERMOSTAT
            6 | 7 | 8 | 11 => electrical.push(change), // Electrical
            12 | 13 | 14 => safety.push(change), // Emergency, camera, sensor
            _ => other.push(change),
        }
    }
    
    fn object_name(obj_type: u8) -> &'static str {
        match obj_type {
            0 => "Wall",
            1 => "Floor", 
            2 => "Ceiling",
            3 => "Door",
            4 => "Window",
            5 => "Column",
            6 => "Outlet",
            7 => "Switch",
            8 => "Light",
            9 => "HVAC Vent",
            10 => "Thermostat",
            11 => "Electrical Panel",
            12 => "Emergency Exit",
            13 => "Camera",
            14 => "Motion Sensor",
            _ => "Equipment",
        }
    }
    
    fn format_location(obj: &ArxObject) -> String {
        format!("Room {} ({}, {})", 
            obj.building_id % 1000,
            obj.x / 1000,
            obj.y / 1000
        )
    }
    
    fn format_state(obj: &ArxObject) -> String {
        match obj.object_type {
            10 => format!("{}°F", obj.properties[0]), // Thermostat
            8 => {
                if obj.properties[0] > 0 {
                    "On".to_string()
                } else {
                    "Off".to_string()
                }
            }
            _ => format!("State: {:?}", obj.properties),
        }
    }
    
    fn assess_risk(changes: &[BuildingChange]) -> RiskLevel {
        let mut risk_score = 0;
        
        for change in changes {
            match change {
                BuildingChange::Remove { object, .. } => {
                    // Removing safety equipment is high risk
                    if matches!(object.object_type, 12 | 13 | 14) {
                        risk_score += 10;
                    } else {
                        risk_score += 3;
                    }
                }
                BuildingChange::Modify { new, .. } => {
                    // Modifying electrical is medium risk
                    if matches!(new.object_type, 11) {
                        risk_score += 5;
                    } else {
                        risk_score += 1;
                    }
                }
                _ => risk_score += 1,
            }
        }
        
        match risk_score {
            0..=5 => RiskLevel::Low,
            6..=10 => RiskLevel::Medium,
            11..=20 => RiskLevel::High,
            _ => RiskLevel::Critical,
        }
    }
    
    fn estimate_cost(changes: &[BuildingChange]) -> Option<f32> {
        let mut cost = 0.0;
        
        for change in changes {
            match change {
                BuildingChange::Add { object, .. } => {
                    cost += match object.object_type {
                        10 => 300.0, // Thermostat
                        9 => 150.0,  // HVAC Vent
                        8 => 75.0,   // Light
                        6 => 50.0,   // Outlet
                        _ => 100.0,
                    };
                }
                BuildingChange::Modify { .. } => {
                    cost += 50.0; // Labor cost
                }
                _ => {}
            }
        }
        
        if cost > 0.0 {
            Some(cost)
        } else {
            None
        }
    }
}

/// Display diff in terminal
pub fn display_diff(diff: &BuildingDiff) {
    println!("\n📊 Merge Request Review");
    println!("═══════════════════════════════════════\n");
    
    // Summary
    println!("Summary:");
    println!("  Total changes: {}", diff.summary.total_changes);
    println!("  ➕ Additions: {}", diff.summary.additions);
    println!("  🔧 Modifications: {}", diff.summary.modifications);
    println!("  ❌ Deletions: {}", diff.summary.deletions);
    println!("  📝 Annotations: {}", diff.summary.annotations);
    println!();
    
    // Risk assessment
    println!("Risk Level: {:?}", diff.risk_level);
    if let Some(cost) = diff.estimated_cost {
        println!("Estimated Cost: ${:.2}", cost);
    }
    println!();
    
    // Changes by system
    for system in &diff.changes_by_system {
        println!("{}:", system.system_name);
        println!("─────────────────────────");
        
        for change in &system.changes {
            println!("{} {}", change.icon, change.description);
            println!("   Location: {}", change.location);
            
            if let Some(before) = &change.before {
                println!("   Before: {}", before);
            }
            if let Some(after) = &change.after {
                println!("   After: {}", after);
            }
            println!();
        }
    }
}

/// Interactive review CLI
pub fn demo_interactive_review() {
    println!("\n⚡ Interactive Merge Review Demo\n");
    
    println!("$ arx review MR-42");
    println!();
    
    println!("═══════════════════════════════════════════");
    println!(" Merge Request #42");
    println!(" Author: HVAC Tech (555-0100)");
    println!(" Branch: hvac-repair-2024-01-15");
    println!(" Created: 2 hours ago");
    println!("═══════════════════════════════════════════\n");
    
    println!("📊 Changes Summary:");
    println!("  3 changes proposed");
    println!("  Risk: MEDIUM");
    println!("  Cost: $450.00");
    println!();
    
    println!("HVAC System:");
    println!("─────────────");
    println!("🔧 Modify Thermostat");
    println!("   Location: Room 203 (20, 30)");
    println!("   Before: 68°F");
    println!("   After: 72°F");
    println!("   ✓ Within normal range");
    println!();
    
    println!("❌ Remove HVAC Vent");
    println!("   Location: Room 203 (25, 30)");
    println!("   Before: Active");
    println!("   After: Removed: Damaged beyond repair");
    println!("   ⚠️ Requires replacement!");
    println!();
    
    println!("➕ Install new HVAC Vent");
    println!("   Location: Room 203 (25, 30)");
    println!("   After: New high-efficiency unit");
    println!("   ✓ Energy savings expected");
    println!();
    
    println!("─────────────────────────────────────");
    println!("Actions:");
    println!("  [A]pprove  [R]eject  [C]omment  [M]odify");
    println!();
    println!("Your choice: A");
    println!();
    println!("✅ Merge Request APPROVED");
    println!("   Changes will be applied to main branch");
    println!("   Work order generated: WO-2024-0142");
    println!("   Contractor notified via SMS");
}

/// Show why this is better than direct modification
pub fn demo_why_branches_matter() {
    println!("\n🏆 Why Building Branches Matter\n");
    
    println!("Scenario: Multiple contractors, same day");
    println!("════════════════════════════════════════\n");
    
    println!("WITHOUT branches (chaos):");
    println!("  9:00 - HVAC tech changes thermostat");
    println!("  9:15 - Electrician doesn't see change (cache)");
    println!("  9:30 - Electrician turns off power");
    println!("  9:45 - HVAC tech's work fails");
    println!("  10:00 - Inspector sees inconsistent state");
    println!("  Result: 🔥 Confusion and rework");
    println!();
    
    println!("WITH branches (organized):");
    println!("  9:00 - HVAC tech works in branch #17");
    println!("  9:15 - Electrician works in branch #18");
    println!("  9:30 - Both complete work independently");
    println!("  10:00 - Manager reviews both MRs:");
    println!("         • Sees potential conflict");
    println!("         • Merges HVAC first");
    println!("         • Then merges electrical");
    println!("  Result: ✅ Controlled, reviewed changes");
    println!();
    
    println!("Benefits:");
    println!("  • No accidental damage");
    println!("  • Complete audit trail");
    println!("  • Can rollback mistakes");
    println!("  • Multiple contractors work simultaneously");
    println!("  • Manager maintains control");
}
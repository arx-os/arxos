// AR integration command handlers

use crate::cli::{ArCommands, PendingCommands};
use crate::ar_integration::pending::PendingEquipmentManager;
use crate::persistence::PersistenceManager;
use crate::utils::loading;
use log::info;

/// Handle AR integration commands
pub fn handle_ar_command(subcommand: ArCommands) -> Result<(), Box<dyn std::error::Error>> {
    match subcommand {
        ArCommands::Pending { subcommand } => handle_pending_command(subcommand),
    }
}

/// Handle pending equipment commands
fn handle_pending_command(command: PendingCommands) -> Result<(), Box<dyn std::error::Error>> {
    match command {
        PendingCommands::List { building, floor, verbose } => {
            handle_pending_list_command(&building, floor, verbose)
        }
        PendingCommands::Confirm { pending_id, building, commit } => {
            handle_pending_confirm_command(&pending_id, &building, commit)
        }
        PendingCommands::Reject { pending_id } => {
            handle_pending_reject_command(&pending_id)
        }
        PendingCommands::BatchConfirm { pending_ids, building, commit } => {
            handle_pending_batch_confirm_command(pending_ids, &building, commit)
        }
    }
}

/// Handle the AR integrate command
pub fn handle_ar_integrate_command(
    scan_file: String,
    room: String,
    floor: i32,
    building: String,
    commit: bool,
    message: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("📱 Integrating AR scan data for room: {} on floor: {}", room, floor);
    
    // Load existing building data
    let building_data = loading::load_building_data(&building)?;
    
    // Read AR scan data file
    println!("📄 Reading AR scan data from: {}", scan_file);
    let scan_data_bytes = std::fs::read(&scan_file)?;
    
    // Convert mobile AR data to ARScanData
    let ar_scan_data = crate::ar_integration::convert_mobile_ar_data(scan_data_bytes, room.clone(), floor)?;
    
    // Integrate AR scan data
    let mut integrator = crate::ar_integration::ARDataIntegrator::new(building_data);
    let integration_result = integrator.integrate_ar_scan(ar_scan_data)?;
    
    // Display integration results
    println!("🔄 AR Integration Results:");
    println!("  📦 Equipment added: {}", integration_result.equipment_added);
    println!("  🔄 Equipment updated: {}", integration_result.equipment_updated);
    println!("  🏠 Rooms updated: {}", integration_result.rooms_updated);
    println!("  ⚠️  Conflicts resolved: {}", integration_result.conflicts_resolved);
    
    // Get updated building data
    let updated_building_data = integrator.get_building_data();
    
    // Save updated building data
    let output_file = format!("{}-updated.yaml", building);
    let yaml_content = serde_yaml::to_string(&updated_building_data)?;
    std::fs::write(&output_file, yaml_content)?;
    println!("💾 Updated building data saved to: {}", output_file);
    
    // Commit to Git if requested
    if commit {
        let commit_message = message.unwrap_or_else(|| {
            format!("Integrate AR scan for room {} on floor {}", room, floor)
        });
        
        println!("📝 Committing changes to Git: {}", commit_message);
        
        // Add files to Git
        let output = std::process::Command::new("git")
            .args(&["add", &output_file])
            .output()?;
        
        if !output.status.success() {
            return Err(format!("Failed to add files to Git: {}", String::from_utf8_lossy(&output.stderr)).into());
        }
        
        // Commit changes
        let output = std::process::Command::new("git")
            .args(&["commit", "-m", &commit_message])
            .output()?;
        
        if !output.status.success() {
            return Err(format!("Failed to commit changes: {}", String::from_utf8_lossy(&output.stderr)).into());
        }
        
        println!("✅ Changes committed to Git");
    }
    
    println!("✅ AR integration completed");
    Ok(())
}

/// Handle list pending equipment command
fn handle_pending_list_command(building: &str, floor: Option<i32>, verbose: bool) -> Result<(), Box<dyn std::error::Error>> {
    println!("📋 Listing pending equipment for building: {}", building);
    
    let manager = PendingEquipmentManager::new(building.to_string());
    let pending_items = manager.list_pending();
    
    if pending_items.is_empty() {
        println!("   No pending equipment found");
        return Ok(());
    }
    
    println!("\n   Found {} pending equipment item(s):\n", pending_items.len());
    
    for (i, item) in pending_items.iter().enumerate() {
        if let Some(floor_filter) = floor {
            if item.floor_level != floor_filter {
                continue;
            }
        }
        
        println!("   {}. {}", i + 1, item.name);
        if verbose {
            println!("      ID: {}", item.id);
            println!("      Type: {}", item.equipment_type);
            println!("      Position: ({:.2}, {:.2}, {:.2})", item.position.x, item.position.y, item.position.z);
            println!("      Floor: {}", item.floor_level);
            if let Some(ref room) = item.room_name {
                println!("      Room: {}", room);
            }
            println!("      Confidence: {:.2}", item.confidence);
            println!("      Detected: {}", item.detected_at.format("%Y-%m-%d %H:%M:%S"));
        } else {
            println!("      Floor: {} | Confidence: {:.2}", item.floor_level, item.confidence);
        }
    }
    
    println!("\n✅ Listing completed");
    Ok(())
}

/// Handle confirm pending equipment command
fn handle_pending_confirm_command(pending_id: &str, building: &str, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    info!("Confirming pending equipment: {} for building: {}", pending_id, building);
    println!("✅ Confirming pending equipment: {}", pending_id);
    
    let mut manager = PendingEquipmentManager::new(building.to_string());
    let persistence = PersistenceManager::new(building)?;
    
    // Load current building data
    let mut building_data = persistence.load_building_data()?;
    
    // Confirm the pending equipment
    let equipment_id = manager.confirm_pending(pending_id, &mut building_data)?;
    
    println!("   Created equipment: {}", equipment_id);
    
    // Save and commit if requested
    if commit {
        let commit_message = format!("Confirm pending equipment: {}", pending_id);
        persistence.save_and_commit(&building_data, Some(&commit_message))?;
        info!("Changes committed to Git");
        println!("✅ Changes committed to Git");
    } else {
        persistence.save_building_data(&building_data)?;
        println!("💡 Use --commit flag to commit changes to Git");
    }
    
    Ok(())
}

/// Handle reject pending equipment command
fn handle_pending_reject_command(pending_id: &str) -> Result<(), Box<dyn std::error::Error>> {
    info!("Rejecting pending equipment: {}", pending_id);
    println!("❌ Rejecting pending equipment: {}", pending_id);
    
    let mut manager = PendingEquipmentManager::new("default".to_string());
    manager.reject_pending(pending_id)?;
    
    println!("✅ Pending equipment rejected");
    Ok(())
}

/// Handle batch confirm pending equipment command
fn handle_pending_batch_confirm_command(pending_ids: Vec<String>, building: &str, commit: bool) -> Result<(), Box<dyn std::error::Error>> {
    info!("Batch confirming {} pending equipment items", pending_ids.len());
    println!("✅ Batch confirming {} pending equipment items", pending_ids.len());
    
    let mut manager = PendingEquipmentManager::new(building.to_string());
    let persistence = PersistenceManager::new(building)?;
    
    // Load current building data
    let mut building_data = persistence.load_building_data()?;
    
    // Batch confirm the pending equipment
    let pending_id_refs: Vec<&str> = pending_ids.iter().map(|s| s.as_str()).collect();
    let equipment_ids = manager.batch_confirm(pending_id_refs, &mut building_data)?;
    
    println!("   Created {} equipment item(s)", equipment_ids.len());
    
    // Save and commit if requested
    if commit {
        let commit_message = format!("Batch confirm {} pending equipment items", equipment_ids.len());
        persistence.save_and_commit(&building_data, Some(&commit_message))?;
        info!("Changes committed to Git");
        println!("✅ Changes committed to Git");
    } else {
        persistence.save_building_data(&building_data)?;
        println!("💡 Use --commit flag to commit changes to Git");
    }
    
    Ok(())
}

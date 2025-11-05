//! IFC Sync command handler
//! 
//! Handles continuous synchronization between YAML building data and IFC files,
//! with support for delta exports and watch mode (daemon).

use crate::yaml;
use crate::export::ifc::{IFCExporter, IFCSyncState};
use crate::utils::loading;
use crate::utils::path_safety::PathSafety;
use std::path::{Path, PathBuf};
use log::{info, warn};

/// Handle the sync command
/// 
/// # Arguments
/// * `ifc_file` - Path to IFC file (required)
/// * `watch` - Enable watch mode (daemon)
/// * `delta` - Export only changes (default if sync state exists)
pub fn handle_sync(ifc_file: Option<String>, watch: bool, delta: bool) -> Result<(), Box<dyn std::error::Error>> {
    // Determine IFC file path
    let ifc_path = if let Some(path) = ifc_file {
        PathBuf::from(path)
    } else {
        // Try to find building.yaml and infer IFC path
        let yaml_files = loading::find_yaml_files()?;
        if yaml_files.is_empty() {
            return Err("No IFC file specified and no building data found. Use --ifc <path> to specify IFC file.".into());
        }
        
        // Infer IFC path from YAML filename
        let yaml_file = yaml_files.first()
            .ok_or("No YAML files found to sync")?;
        let ifc_name = yaml_file
            .replace(".yaml", ".ifc")
            .replace(".yml", ".ifc");
        PathBuf::from(ifc_name)
    };
    
    println!("🔄 Syncing YAML → IFC: {}", ifc_path.display());
    
    // Load building data
    let building_data = load_current_building_data()?;
    
    // Load sync state
    let sync_state_path = IFCSyncState::default_path();
    let mut sync_state = IFCSyncState::load(&sync_state_path)
        .unwrap_or_else(|| {
            info!("No previous sync state found, creating new state");
            IFCSyncState::new(ifc_path.clone())
        });
    
    // Update sync state IFC file path if different
    if sync_state.ifc_file_path != ifc_path {
        sync_state.ifc_file_path = ifc_path.clone();
    }
    
    // Create exporter
    let exporter = IFCExporter::new(building_data.clone());
    
    // Perform sync
    if watch {
        // Watch mode - continuous sync
        println!("👀 Watch mode enabled - monitoring for changes...");
        println!("💡 Press Ctrl+C to stop");
        handle_watch_mode(exporter, &ifc_path, &mut sync_state, &sync_state_path)?;
    } else {
        // One-time sync
        let use_delta = delta || sync_state.last_export_timestamp != chrono::DateTime::UNIX_EPOCH;
        
        if use_delta {
            println!("📊 Delta mode: exporting only changes");
            exporter.export_delta(Some(&sync_state), &ifc_path)?;
        } else {
            println!("📤 Full export mode: exporting all data");
            exporter.export(&ifc_path)?;
        }
        
        // Update sync state
        let (equipment_paths, rooms_paths) = exporter.collect_universal_paths();
        sync_state.update_after_export(equipment_paths, rooms_paths);
        sync_state.save(&sync_state_path)?;
        
        println!("✅ Sync completed successfully");
        println!("   IFC file: {}", ifc_path.display());
        println!("   Sync state saved to: {}", sync_state_path.display());
    }
    
    Ok(())
}

/// Load building data from current directory
fn load_current_building_data() -> Result<yaml::BuildingData, Box<dyn std::error::Error>> {
    let yaml_files = loading::find_yaml_files()?;
    
    if yaml_files.is_empty() {
        return Err("No YAML files found. Please run 'arx import <ifc_file>' first to generate building data.".into());
    }
    
    let yaml_file = yaml_files.first()
        .ok_or("No YAML files found to sync")?;
    
    println!("📄 Loading building data from: {}", yaml_file);
    
    let base_dir = std::env::current_dir()
        .map_err(|e| format!("Failed to get current directory: {}", e))?;
    
    let yaml_content = PathSafety::read_file_safely(
        Path::new(yaml_file),
        &base_dir
    )
    .map_err(|e| format!("Failed to read YAML file '{}': {}", yaml_file, e))?;
    
    let building_data: yaml::BuildingData = serde_yaml::from_str(&yaml_content)
        .map_err(|e| format!("Failed to parse YAML file '{}': {}", yaml_file, e))?;
    
    Ok(building_data)
}

/// Handle watch mode (daemon) for continuous synchronization
fn handle_watch_mode(
    exporter: IFCExporter,
    ifc_path: &Path,
    sync_state: &mut IFCSyncState,
    sync_state_path: &Path,
) -> Result<(), Box<dyn std::error::Error>> {
    use notify::{Watcher, RecommendedWatcher, RecursiveMode, EventKind};
    use std::sync::mpsc;
    use std::time::Duration;
    
    // Find building.yaml file to watch
    let yaml_files = loading::find_yaml_files()?;
    let yaml_file = yaml_files.first()
        .ok_or("No YAML files found to watch")?;
    let watch_path = Path::new(yaml_file);
    
    println!("👀 Watching: {}", watch_path.display());
    
    // Create channel for file events
    let (tx, rx) = mpsc::channel();
    
    // Create watcher
    let mut watcher: RecommendedWatcher = notify::recommended_watcher(tx)?;
    watcher.watch(watch_path, RecursiveMode::NonRecursive)?;
    
    // Debounce timer - wait for events to settle before processing
    let debounce_duration = Duration::from_secs(2);
    let mut last_event_time = None;
    
    loop {
        match rx.recv_timeout(Duration::from_millis(500)) {
            Ok(Ok(event)) => {
                match event.kind {
                    EventKind::Modify(_) | EventKind::Create(_) => {
                        last_event_time = Some(std::time::Instant::now());
                        info!("File change detected: {:?}", event.paths);
                    }
                    _ => {}
                }
            }
            Ok(Err(e)) => {
                warn!("Watch error: {}", e);
            }
            Err(mpsc::RecvTimeoutError::Timeout) => {
                // Check if we should process after debounce
                if let Some(event_time) = last_event_time {
                    if event_time.elapsed() >= debounce_duration {
                        // Process changes
                        match process_sync_cycle(&exporter, ifc_path, sync_state, sync_state_path) {
                            Ok(_) => {
                                println!("✅ Sync cycle completed");
                                last_event_time = None;
                            }
                            Err(e) => {
                                warn!("Sync cycle failed: {}", e);
                                // Continue watching despite errors
                            }
                        }
                    }
                }
            }
            Err(mpsc::RecvTimeoutError::Disconnected) => {
                return Err("File watcher disconnected".into());
            }
        }
    }
}

/// Process a single sync cycle
fn process_sync_cycle(
    _exporter: &IFCExporter,
    ifc_path: &Path,
    sync_state: &mut IFCSyncState,
    sync_state_path: &Path,
) -> Result<(), Box<dyn std::error::Error>> {
    // Reload building data
    let building_data = load_current_building_data()?;
    
    // Create new exporter with updated data
    // Note: We can't easily update the exporter's internal state, so we create a new one
    // This is a limitation - in production, we'd want a more efficient approach
    let current_exporter = IFCExporter::new(building_data);
    
    // Check if we should use delta mode
    let use_delta = sync_state.last_export_timestamp != chrono::DateTime::UNIX_EPOCH;
    
    if use_delta {
        info!("Processing delta sync");
        current_exporter.export_delta(Some(sync_state), ifc_path)?;
    } else {
        info!("Processing full sync");
        current_exporter.export(ifc_path)?;
    }
    
    // Update sync state
    let (equipment_paths, rooms_paths) = current_exporter.collect_universal_paths();
    sync_state.update_after_export(equipment_paths, rooms_paths);
    sync_state.save(sync_state_path)?;
    
    Ok(())
}


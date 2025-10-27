// Sensor processing command handlers

use std::path::PathBuf;
use log::{info, warn};

/// Handle the process sensors command
pub fn handle_process_sensors_command(
    sensor_dir: &str,
    building: &str,
    commit: bool,
    _watch: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    info!("📡 Processing sensor data from: {}", sensor_dir);
    println!("📡 Processing sensor data from: {}", sensor_dir);
    println!("   Building: {}", building);
    
    let config = crate::hardware::SensorIngestionConfig {
        data_directory: PathBuf::from(sensor_dir),
        ..crate::hardware::SensorIngestionConfig::default()
    };
    
    let ingestion = crate::hardware::SensorIngestionService::new(config);
    let mut updater = crate::hardware::EquipmentStatusUpdater::new(building)?;
    
    // Process once
    match ingestion.process_all_sensor_files() {
        Ok(sensor_data_list) => {
            info!("Processing {} sensor data files...", sensor_data_list.len());
            println!("   Processing {} sensor data files...", sensor_data_list.len());
            
            let mut success_count = 0;
            let mut error_count = 0;
            
            for sensor_data in sensor_data_list {
                match updater.process_sensor_data(&sensor_data) {
                    Ok(result) => {
                        info!("Updated equipment {}: {} → {}", 
                             result.equipment_id, result.old_status, result.new_status);
                        println!("   ✅ Updated {}: {} → {}", 
                                 result.equipment_id, result.old_status, result.new_status);
                        success_count += 1;
                    }
                    Err(e) => {
                        warn!("Error processing sensor {}: {}", 
                             sensor_data.metadata.sensor_id, e);
                        println!("   ⚠️  Error processing {}: {}", 
                                 sensor_data.metadata.sensor_id, e);
                        error_count += 1;
                    }
                }
            }
            
            println!("\n📊 Processing Summary:");
            println!("   ✅ Successful: {}", success_count);
            println!("   ⚠️  Errors: {}", error_count);
            
            // Save updated building data
            info!("Saving updated building data to YAML");
            println!("\n💾 Saving updated building data...");
            
            // The EquipmentStatusUpdater already saves in process_sensor_data,
            // but we also want to ensure the final state is committed
            if commit {
                let commit_message = format!("Update equipment status from sensor data: {} successful, {} errors", 
                    success_count, error_count);
                updater.commit_changes(&commit_message)?;
                info!("Changes committed to Git with message: {}", commit_message);
                println!("✅ Changes committed to Git");
            } else {
                println!("💡 Use --commit flag to commit changes to Git");
            }
        }
        Err(e) => {
            warn!("Error processing sensor files: {}", e);
            println!("⚠️  Error processing sensor files: {}", e);
            return Err(format!("Sensor processing failed: {}", e).into());
        }
    }
    
    info!("Sensor processing completed successfully");
    println!("✅ Sensor processing completed");
    Ok(())
}

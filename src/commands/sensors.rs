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

/// Handle the sensors HTTP server command
#[cfg(feature = "async-sensors")]
pub fn handle_sensors_http_command(
    building: &str,
    host: &str,
    port: u16,
) -> Result<(), Box<dyn std::error::Error>> {
    use std::sync::Arc;
    use tokio::sync::RwLock;
    use std::path::PathBuf;
    
    info!("🌐 Starting sensor HTTP ingestion server");
    println!("🌐 Starting sensor HTTP ingestion server");
    println!("   Building: {}", building);
    println!("   Listening on: http://{}:{}", host, port);
    
    let config = crate::hardware::SensorIngestionConfig {
        data_directory: PathBuf::from("./sensor-data"),
        ..crate::hardware::SensorIngestionConfig::default()
    };
    
    let ingestion_service = Arc::new(RwLock::new(crate::hardware::SensorIngestionService::new(config)));
    
    println!("\n✅ Server started! Waiting for sensor data...");
    println!("   POST sensor data to: http://{}:{}/sensors/ingest", host, port);
    println!("   Health check: http://{}:{}/sensors/health\n", host, port);
    
    // Start server (this blocks until server stops)
    let rt = tokio::runtime::Runtime::new()?;
    rt.block_on(crate::hardware::start_sensor_http_server(host, port, building.to_string(), ingestion_service))?;
    
    Ok(())
}

#[cfg(not(feature = "async-sensors"))]
pub fn handle_sensors_http_command(
    _building: &str,
    _host: &str,
    _port: u16,
) -> Result<(), Box<dyn std::error::Error>> {
    eprintln!("❌ Error: HTTP sensor server requires async-sensors feature");
    eprintln!("💡 Compile with: cargo build --features async-sensors");
    Err("HTTP server not available without async-sensors feature".into())
}

/// Handle the sensors MQTT subscriber command
#[cfg(feature = "async-sensors")]
pub fn handle_sensors_mqtt_command(
    building: &str,
    broker: &str,
    port: u16,
    username: Option<&str>,
    password: Option<&str>,
    topics: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    use crate::hardware::{MqttClientConfig, EquipmentStatusUpdater};
    
    info!("🔌 Starting sensor MQTT subscriber");
    println!("🔌 Starting sensor MQTT subscriber");
    println!("   Building: {}", building);
    println!("   Broker: {}:{}", broker, port);
    
    // Parse topics from comma-separated string
    let topic_list: Vec<String> = topics.split(',').map(|s| s.trim().to_string()).collect();
    
    // Create MQTT config
    let mqtt_config = MqttClientConfig {
        broker_url: broker.to_string(),
        broker_port: port,
        client_id: format!("arxos_sensor_client_{}", uuid::Uuid::new_v4()),
        username: username.map(|s| s.to_string()),
        password: password.map(|s| s.to_string()),
        topics: topic_list.clone(),
    };
    
    println!("   Subscribing to topics: {:?}", topic_list);
    println!("\n✅ MQTT subscriber started! Waiting for sensor data...");
    
    // Create equipment status updater wrapped in Arc<RwLock> for shared mutable access
    use std::sync::Arc;
    use tokio::sync::RwLock;
    
    let updater = Arc::new(RwLock::new(EquipmentStatusUpdater::new(building)?));
    
    // Define callback for processing incoming sensor data
    let callback_updater = Arc::clone(&updater);
    let callback = move |sensor_data: crate::hardware::SensorData| -> Result<(), String> {
        // Process sensor data and update equipment status
        let rt = tokio::runtime::Handle::current();
        rt.block_on(async {
            let mut updater = callback_updater.write().await;
            match updater.process_sensor_data(&sensor_data) {
                Ok(result) => {
                    info!("Updated equipment {}: {} → {}", 
                         result.equipment_id, result.old_status, result.new_status);
                    println!("   ✅ Updated {}: {} → {}", 
                             result.equipment_id, result.old_status, result.new_status);
                    Ok(())
                }
                Err(e) => {
                    warn!("Error processing sensor {}: {}", sensor_data.metadata.sensor_id, e);
                    Err(format!("Error processing sensor data: {}", e))
                }
            }
        })
    };
    
    // Start MQTT subscriber (this blocks)
    let rt = tokio::runtime::Runtime::new()?;
    rt.block_on(crate::hardware::start_mqtt_subscriber(mqtt_config, callback))?;
    
    Ok(())
}

#[cfg(not(feature = "async-sensors"))]
pub fn handle_sensors_mqtt_command(
    _building: &str,
    _broker: &str,
    _port: u16,
    _username: Option<&str>,
    _password: Option<&str>,
    _topics: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    eprintln!("❌ Error: MQTT sensor subscriber requires async-sensors feature");
    eprintln!("💡 Compile with: cargo build --features async-sensors");
    Err("MQTT subscriber not available without async-sensors feature".into())
}

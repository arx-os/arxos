//! HTTP server for hardware sensor data ingestion
//!
//! This module provides an HTTP REST API endpoint for receiving sensor data
//! from IoT devices via POST requests.

use super::{SensorData, HardwareError, EquipmentStatusUpdater};
use axum::{
    extract::State,
    http::StatusCode,
    response::Json,
    routing::post,
    Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;
use log::{info, warn, error};

/// HTTP response for sensor data ingestion
#[derive(Debug, Serialize, Deserialize)]
pub struct SensorIngestionResponse {
    pub success: bool,
    pub message: String,
    pub sensor_id: Option<String>,
    pub timestamp: Option<String>,
}

/// Service state for the HTTP server
#[derive(Clone)]
pub struct SensorHttpService {
    pub ingestion_service: Arc<RwLock<super::SensorIngestionService>>,
    pub building_name: String,
}

/// Create the HTTP router for sensor data ingestion
pub fn create_sensor_router(state: SensorHttpService) -> Router {
    Router::new()
        .route("/sensors/ingest", post(ingest_sensor_data))
        .route("/sensors/health", post(health_check))
        .with_state(state)
}

/// Health check endpoint
async fn health_check() -> Result<Json<SensorIngestionResponse>, StatusCode> {
    Ok(Json(SensorIngestionResponse {
        success: true,
        message: "Sensor ingestion service is healthy".to_string(),
        sensor_id: None,
        timestamp: None,
    }))
}

/// Ingest sensor data from HTTP POST request
async fn ingest_sensor_data(
    State(service): State<SensorHttpService>,
    Json(sensor_data): Json<SensorData>,
) -> Result<Json<SensorIngestionResponse>, StatusCode> {
    info!("Received sensor data ingestion request for sensor: {}", sensor_data.metadata.sensor_id);
    
    // Validate sensor data
    let ingestion_service = service.ingestion_service.read().await;
    if !ingestion_service.validate_sensor_data(&sensor_data) {
        warn!("Invalid sensor data received from: {}", sensor_data.metadata.sensor_id);
        return Err(StatusCode::BAD_REQUEST);
    }
    drop(ingestion_service); // Release lock before potentially long-running operation
    
    // Process sensor data and update equipment status
    // Create equipment status updater for this building
    let mut status_updater = match EquipmentStatusUpdater::new(&service.building_name) {
        Ok(updater) => updater,
        Err(e) => {
            error!("Failed to create equipment status updater for building '{}': {}", 
                   service.building_name, e);
            return Err(StatusCode::INTERNAL_SERVER_ERROR);
        }
    };
    
    // Process sensor data and update equipment status
    match status_updater.process_sensor_data(&sensor_data) {
        Ok(update_result) => {
            info!("Successfully processed sensor data and updated equipment status: {} → {} (equipment: {})", 
                  update_result.old_status, update_result.new_status, update_result.equipment_id);
            
            let message = if update_result.alerts.is_empty() {
                format!(
                    "Successfully ingested sensor data and updated equipment '{}': {} → {}", 
                    update_result.equipment_id, 
                    update_result.old_status,
                    update_result.new_status
                )
            } else {
                format!(
                    "Successfully ingested sensor data and updated equipment '{}': {} → {} ({} alerts generated)", 
                    update_result.equipment_id, 
                    update_result.old_status,
                    update_result.new_status,
                    update_result.alerts.len()
                )
            };
            
            Ok(Json(SensorIngestionResponse {
                success: true,
                message,
                sensor_id: Some(sensor_data.metadata.sensor_id),
                timestamp: Some(update_result.timestamp),
            }))
        }
        Err(e) => {
            error!("Failed to process sensor data from '{}': {}", 
                   sensor_data.metadata.sensor_id, e);
            
            // Return appropriate error code based on error type
            let status_code = match e {
                HardwareError::MappingError { .. } => StatusCode::NOT_FOUND,
                HardwareError::InvalidFormat { .. } => StatusCode::BAD_REQUEST,
                _ => StatusCode::INTERNAL_SERVER_ERROR,
            };
            
            Err(status_code)
        }
    }
}

/// Start the HTTP server for sensor data ingestion
pub async fn start_sensor_http_server(
    host: &str,
    port: u16,
    building_name: String,
    ingestion_service: Arc<RwLock<super::SensorIngestionService>>,
) -> Result<(), HardwareError> {
    let state = SensorHttpService {
        ingestion_service,
        building_name,
    };
    
    let app = create_sensor_router(state);
    
    let addr = format!("{}:{}", host, port);
    info!("Starting sensor HTTP ingestion server on {}", addr);
    
    let listener = tokio::net::TcpListener::bind(&addr)
        .await
        .map_err(|e| HardwareError::IoError(std::io::Error::other(format!("Failed to bind to {}: {}", addr, e))))?;
    
    info!("Sensor HTTP ingestion server listening on {}", addr);
    
    axum::serve(listener, app)
        .await
        .map_err(|e| HardwareError::IoError(std::io::Error::other(format!("Server error: {}", e))))?;
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hardware::{SensorIngestionService, SensorIngestionConfig};
    use std::collections::HashMap;
    use tempfile::TempDir;
    
    fn create_test_sensor_data() -> SensorData {
        SensorData {
            api_version: "arxos.io/v1".to_string(),
            kind: "SensorData".to_string(),
            metadata: crate::hardware::SensorMetadata {
                sensor_id: "test_sensor_001".to_string(),
                sensor_type: "temperature".to_string(),
                room_path: Some("/building/3/301".to_string()),
                timestamp: "2024-01-15T10:30:00Z".to_string(),
                source: "test".to_string(),
                building_id: Some("test_building".to_string()),
                equipment_id: Some("HVAC-301".to_string()),
                extra: HashMap::new(),
            },
            data: crate::hardware::SensorDataValues {
                values: {
                    let mut map = HashMap::new();
                    map.insert("temperature".to_string(), serde_yaml::Value::Number(serde_yaml::Number::from(72)));
                    map
                },
            },
            alerts: vec![],
            arxos: None,
        }
    }
    
    #[tokio::test]
    async fn test_health_check() {
        let response = health_check().await.unwrap();
        assert!(response.0.success);
        assert!(response.0.message.contains("healthy"));
    }
    
    #[tokio::test]
    async fn test_validate_sensor_data() {
        let temp_dir = TempDir::new().unwrap();
        let config = SensorIngestionConfig {
            data_directory: temp_dir.path().to_path_buf(),
            ..Default::default()
        };
        let ingestion_service = Arc::new(RwLock::new(SensorIngestionService::new(config)));
        
        let sensor_data = create_test_sensor_data();
        
        // Should validate successfully
        let valid = ingestion_service.read().await.validate_sensor_data(&sensor_data);
        assert!(valid);
    }
    
    #[tokio::test]
    async fn test_ingest_sensor_data_valid() {
        let temp_dir = TempDir::new().unwrap();
        let config = SensorIngestionConfig {
            data_directory: temp_dir.path().to_path_buf(),
            ..Default::default()
        };
        let ingestion_service = Arc::new(RwLock::new(SensorIngestionService::new(config)));
        let state = SensorHttpService {
            ingestion_service,
            building_name: "test_building".to_string(),
        };
        
        let sensor_data = create_test_sensor_data();
        let response = ingest_sensor_data(State(state), Json(sensor_data)).await.unwrap();
        
        assert!(response.0.success);
        assert_eq!(response.0.sensor_id, Some("test_sensor_001".to_string()));
    }
    
    #[tokio::test]
    async fn test_ingest_sensor_data_invalid() {
        let temp_dir = TempDir::new().unwrap();
        let config = SensorIngestionConfig {
            data_directory: temp_dir.path().to_path_buf(),
            ..Default::default()
        };
        let ingestion_service = Arc::new(RwLock::new(SensorIngestionService::new(config)));
        let state = SensorHttpService {
            ingestion_service,
            building_name: "test_building".to_string(),
        };
        
        // Create invalid sensor data (missing required fields)
        let invalid_data = SensorData {
            api_version: String::new(),
            kind: String::new(),
            metadata: crate::hardware::SensorMetadata {
                sensor_id: String::new(),
                sensor_type: String::new(),
                room_path: None,
                timestamp: "2024-01-15T10:30:00Z".to_string(),
                source: "test".to_string(),
                building_id: None,
                equipment_id: None,
                extra: HashMap::new(),
            },
            data: crate::hardware::SensorDataValues {
                values: HashMap::new(),
            },
            alerts: vec![],
            arxos: None,
        };
        
        let result = ingest_sensor_data(State(state), Json(invalid_data)).await;
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), StatusCode::BAD_REQUEST);
    }
}


//! Simple REST API for ArxOS Building Intelligence
//! 
//! Provides HTTP endpoints for querying ArxObjects and building data

use crate::arxobject_simple::{ArxObject, ObjectCategory, object_types};
use crate::persistence_simple::ArxObjectDatabase;
use crate::ply_parser_simple::SimplePlyParser;
use serde::{Serialize, Deserialize};
use std::sync::{Arc, Mutex};
use std::convert::Infallible;

/// API Server configuration
#[derive(Clone)]
pub struct ApiConfig {
    pub port: u16,
    pub database_path: String,
    pub max_results: usize,
}

impl Default for ApiConfig {
    fn default() -> Self {
        Self {
            port: 3000,
            database_path: "building.db".to_string(),
            max_results: 1000,
        }
    }
}

/// JSON response for ArxObject
#[derive(Serialize, Deserialize)]
pub struct ArxObjectJson {
    pub building_id: u16,
    pub object_type: String,
    pub object_type_hex: String,
    pub category: String,
    pub position: Position,
    pub properties: Vec<u8>,
}

/// Position in both millimeters and meters
#[derive(Serialize, Deserialize)]
pub struct Position {
    pub x_mm: u16,
    pub y_mm: u16,
    pub z_mm: u16,
    pub x_m: f32,
    pub y_m: f32,
    pub z_m: f32,
}

/// Response for spatial queries
#[derive(Serialize, Deserialize)]
pub struct SpatialQueryResponse {
    pub query_type: String,
    pub count: usize,
    pub objects: Vec<ArxObjectJson>,
}

/// Response for nearest query
#[derive(Serialize, Deserialize)]
pub struct NearestQueryResponse {
    pub count: usize,
    pub objects: Vec<NearestObject>,
}

#[derive(Serialize, Deserialize)]
pub struct NearestObject {
    pub object: ArxObjectJson,
    pub distance_m: f32,
}

/// Statistics response
#[derive(Serialize, Deserialize)]
pub struct StatsResponse {
    pub total_objects: usize,
    pub building_count: usize,
    pub type_distribution: Vec<TypeCount>,
}

#[derive(Serialize, Deserialize)]
pub struct TypeCount {
    pub object_type: String,
    pub category: String,
    pub count: i64,
}

/// Error response
#[derive(Serialize, Deserialize)]
pub struct ErrorResponse {
    pub error: String,
    pub message: String,
}

/// API State shared across handlers
pub struct ApiState {
    pub db: Arc<Mutex<ArxObjectDatabase>>,
    pub config: ApiConfig,
}

impl ApiState {
    pub fn new(config: ApiConfig) -> Result<Self, Box<dyn std::error::Error>> {
        let db = ArxObjectDatabase::open(&config.database_path)?;
        Ok(Self {
            db: Arc::new(Mutex::new(db)),
            config,
        })
    }
}

/// Convert ArxObject to JSON representation
fn arxobject_to_json(obj: &ArxObject) -> ArxObjectJson {
    let (x_m, y_m, z_m) = obj.position_meters();
    let category = ObjectCategory::from_type(obj.object_type);
    
    ArxObjectJson {
        building_id: obj.building_id,
        object_type: object_type_name(obj.object_type),
        object_type_hex: format!("0x{:02X}", obj.object_type),
        category: format!("{:?}", category),
        position: Position {
            x_mm: obj.x,
            y_mm: obj.y,
            z_mm: obj.z,
            x_m,
            y_m,
            z_m,
        },
        properties: obj.properties.to_vec(),
    }
}

/// Get human-readable name for object type
fn object_type_name(type_code: u8) -> String {
    match type_code {
        object_types::OUTLET => "Outlet",
        object_types::LIGHT_SWITCH => "Light Switch",
        object_types::THERMOSTAT => "Thermostat",
        object_types::LIGHT => "Light",
        object_types::HVAC_VENT => "HVAC Vent",
        object_types::SMOKE_DETECTOR => "Smoke Detector",
        object_types::FIRE_ALARM => "Fire Alarm",
        object_types::EMERGENCY_EXIT => "Emergency Exit",
        object_types::CAMERA => "Camera",
        object_types::MOTION_SENSOR => "Motion Sensor",
        object_types::LEAK => "Leak Detector",
        object_types::FLOOR => "Floor",
        object_types::WALL => "Wall",
        object_types::CEILING => "Ceiling",
        object_types::DOOR => "Door",
        object_types::WINDOW => "Window",
        _ => "Unknown",
    }.to_string()
}

// === Warp HTTP Handlers ===
// Note: These would be implemented with warp or actix-web in production
// For now, showing the handler signatures and logic

/// GET /api/objects/building/{building_id}
pub fn get_building_objects(state: Arc<ApiState>, building_id: u16) 
    -> Result<impl warp::Reply, Infallible> {
    let db = state.db.lock().unwrap();
    
    match db.get_building_objects(building_id) {
        Ok(objects) => {
            let json_objects: Vec<ArxObjectJson> = objects
                .iter()
                .take(state.config.max_results)
                .map(arxobject_to_json)
                .collect();
            
            let response = SpatialQueryResponse {
                query_type: "building".to_string(),
                count: json_objects.len(),
                objects: json_objects,
            };
            
            Ok(warp::reply::json(&response))
        }
        Err(e) => {
            let error = ErrorResponse {
                error: "database_error".to_string(),
                message: e.to_string(),
            };
            Ok(warp::reply::json(&error))
        }
    }
}

/// GET /api/objects/radius?x={x}&y={y}&z={z}&radius={r}
pub fn get_objects_in_radius(
    state: Arc<ApiState>,
    x: f32, y: f32, z: f32, radius: f32
) -> Result<impl warp::Reply, Infallible> {
    let db = state.db.lock().unwrap();
    
    match db.find_within_radius(x, y, z, radius) {
        Ok(objects) => {
            let json_objects: Vec<ArxObjectJson> = objects
                .iter()
                .take(state.config.max_results)
                .map(arxobject_to_json)
                .collect();
            
            let response = SpatialQueryResponse {
                query_type: format!("radius_{:.1}m", radius),
                count: json_objects.len(),
                objects: json_objects,
            };
            
            Ok(warp::reply::json(&response))
        }
        Err(e) => {
            let error = ErrorResponse {
                error: "database_error".to_string(),
                message: e.to_string(),
            };
            Ok(warp::reply::json(&error))
        }
    }
}

/// GET /api/objects/box?min_x={}&min_y={}&min_z={}&max_x={}&max_y={}&max_z={}
pub fn get_objects_in_box(
    state: Arc<ApiState>,
    min_x: f32, min_y: f32, min_z: f32,
    max_x: f32, max_y: f32, max_z: f32
) -> Result<impl warp::Reply, Infallible> {
    let db = state.db.lock().unwrap();
    
    match db.find_in_box(min_x, min_y, min_z, max_x, max_y, max_z) {
        Ok(objects) => {
            let json_objects: Vec<ArxObjectJson> = objects
                .iter()
                .take(state.config.max_results)
                .map(arxobject_to_json)
                .collect();
            
            let response = SpatialQueryResponse {
                query_type: "bounding_box".to_string(),
                count: json_objects.len(),
                objects: json_objects,
            };
            
            Ok(warp::reply::json(&response))
        }
        Err(e) => {
            let error = ErrorResponse {
                error: "database_error".to_string(),
                message: e.to_string(),
            };
            Ok(warp::reply::json(&error))
        }
    }
}

/// GET /api/objects/nearest?x={x}&y={y}&z={z}&limit={n}
pub fn get_nearest_objects(
    state: Arc<ApiState>,
    x: f32, y: f32, z: f32, limit: usize
) -> Result<impl warp::Reply, Infallible> {
    let db = state.db.lock().unwrap();
    
    match db.find_nearest(x, y, z, limit.min(state.config.max_results)) {
        Ok(results) => {
            let objects: Vec<NearestObject> = results
                .iter()
                .map(|(obj, distance)| NearestObject {
                    object: arxobject_to_json(obj),
                    distance_m: *distance,
                })
                .collect();
            
            let response = NearestQueryResponse {
                count: objects.len(),
                objects,
            };
            
            Ok(warp::reply::json(&response))
        }
        Err(e) => {
            let error = ErrorResponse {
                error: "database_error".to_string(),
                message: e.to_string(),
            };
            Ok(warp::reply::json(&error))
        }
    }
}

/// GET /api/objects/floor/{building_id}/{floor_height}
pub fn get_floor_objects(
    state: Arc<ApiState>,
    building_id: u16,
    floor_height: f32
) -> Result<impl warp::Reply, Infallible> {
    let db = state.db.lock().unwrap();
    
    match db.find_on_floor(building_id, floor_height, 1.5) {
        Ok(objects) => {
            let json_objects: Vec<ArxObjectJson> = objects
                .iter()
                .take(state.config.max_results)
                .map(arxobject_to_json)
                .collect();
            
            let response = SpatialQueryResponse {
                query_type: format!("floor_{:.1}m", floor_height),
                count: json_objects.len(),
                objects: json_objects,
            };
            
            Ok(warp::reply::json(&response))
        }
        Err(e) => {
            let error = ErrorResponse {
                error: "database_error".to_string(),
                message: e.to_string(),
            };
            Ok(warp::reply::json(&error))
        }
    }
}

/// GET /api/stats
pub fn get_stats(state: Arc<ApiState>) -> Result<impl warp::Reply, Infallible> {
    let db = state.db.lock().unwrap();
    
    match db.get_stats() {
        Ok(stats) => {
            let type_distribution: Vec<TypeCount> = stats.type_distribution
                .iter()
                .map(|(type_code, count)| TypeCount {
                    object_type: object_type_name(*type_code),
                    category: format!("{:?}", ObjectCategory::from_type(*type_code)),
                    count: *count,
                })
                .collect();
            
            let response = StatsResponse {
                total_objects: stats.total_objects,
                building_count: stats.building_count,
                type_distribution,
            };
            
            Ok(warp::reply::json(&response))
        }
        Err(e) => {
            let error = ErrorResponse {
                error: "database_error".to_string(),
                message: e.to_string(),
            };
            Ok(warp::reply::json(&error))
        }
    }
}

/// POST /api/upload/ply
pub async fn upload_ply(
    state: Arc<ApiState>,
    building_id: u16,
    bytes: bytes::Bytes
) -> Result<impl warp::Reply, Infallible> {
    // Save temporary file
    let temp_path = format!("/tmp/arxos_upload_{}.ply", uuid::Uuid::new_v4());
    
    if let Err(e) = std::fs::write(&temp_path, &bytes) {
        let error = ErrorResponse {
            error: "file_error".to_string(),
            message: e.to_string(),
        };
        return Ok(warp::reply::json(&error));
    }
    
    // Parse PLY to ArxObjects
    let parser = SimplePlyParser::new();
    match parser.parse_to_arxobjects(&temp_path, building_id) {
        Ok(objects) => {
            // Insert into database
            let mut db = state.db.lock().unwrap();
            match db.insert_batch(&objects) {
                Ok(count) => {
                    // Clean up temp file
                    let _ = std::fs::remove_file(&temp_path);
                    
                    let response = serde_json::json!({
                        "success": true,
                        "message": format!("Inserted {} ArxObjects", count),
                        "count": count,
                        "building_id": building_id,
                    });
                    
                    Ok(warp::reply::json(&response))
                }
                Err(e) => {
                    let _ = std::fs::remove_file(&temp_path);
                    let error = ErrorResponse {
                        error: "database_error".to_string(),
                        message: e.to_string(),
                    };
                    Ok(warp::reply::json(&error))
                }
            }
        }
        Err(e) => {
            let _ = std::fs::remove_file(&temp_path);
            let error = ErrorResponse {
                error: "parse_error".to_string(),
                message: e.to_string(),
            };
            Ok(warp::reply::json(&error))
        }
    }
}

/// Health check endpoint
pub fn health() -> Result<impl warp::Reply, Infallible> {
    Ok(warp::reply::json(&serde_json::json!({
        "status": "healthy",
        "service": "arxos-api",
        "version": "0.1.0",
    })))
}
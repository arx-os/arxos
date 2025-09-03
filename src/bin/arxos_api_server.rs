//! ArxOS REST API Server
//! 
//! HTTP server for building intelligence queries

use arxos_core::persistence_simple::ArxObjectDatabase;
use arxos_core::arxobject_simple::{ArxObject, ObjectCategory, object_types};
use arxos_core::ply_parser_simple::SimplePlyParser;
use warp::{Filter, Reply, Rejection};
use serde::{Serialize, Deserialize};
use std::sync::{Arc, Mutex};
use std::convert::Infallible;
use std::env;

/// JSON response for ArxObject
#[derive(Serialize, Deserialize)]
struct ArxObjectJson {
    building_id: u16,
    object_type: String,
    object_type_hex: String,
    category: String,
    position: Position,
    properties: Vec<u8>,
}

#[derive(Serialize, Deserialize)]
struct Position {
    x_mm: u16,
    y_mm: u16,
    z_mm: u16,
    x_m: f32,
    y_m: f32,
    z_m: f32,
}

#[derive(Serialize, Deserialize)]
struct SpatialQueryResponse {
    query_type: String,
    count: usize,
    objects: Vec<ArxObjectJson>,
}

#[derive(Serialize, Deserialize)]
struct NearestQueryResponse {
    count: usize,
    objects: Vec<NearestObject>,
}

#[derive(Serialize, Deserialize)]
struct NearestObject {
    object: ArxObjectJson,
    distance_m: f32,
}

#[derive(Serialize, Deserialize)]
struct StatsResponse {
    total_objects: usize,
    building_count: usize,
    type_distribution: Vec<TypeCount>,
}

#[derive(Serialize, Deserialize)]
struct TypeCount {
    object_type: String,
    category: String,
    count: i64,
}

#[derive(Serialize, Deserialize)]
struct ErrorResponse {
    error: String,
    message: String,
}

type SharedDb = Arc<Mutex<ArxObjectDatabase>>;

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

#[tokio::main]
async fn main() {
    let args: Vec<String> = env::args().collect();
    
    let db_path = if args.len() > 1 {
        args[1].clone()
    } else {
        "building.db".to_string()
    };
    
    let port = if args.len() > 2 {
        args[2].parse().unwrap_or(3000)
    } else {
        3000
    };
    
    println!("ArxOS REST API Server");
    println!("====================");
    println!("Database: {}", db_path);
    println!("Port: {}", port);
    println!();
    
    // Initialize database
    let db = match ArxObjectDatabase::open(&db_path) {
        Ok(db) => Arc::new(Mutex::new(db)),
        Err(e) => {
            eprintln!("Failed to open database: {}", e);
            std::process::exit(1);
        }
    };
    
    // Clone for use in handlers
    let db_filter = warp::any().map(move || db.clone());
    
    // GET /health
    let health = warp::path("health")
        .and(warp::get())
        .map(|| {
            warp::reply::json(&serde_json::json!({
                "status": "healthy",
                "service": "arxos-api",
                "version": "0.1.0",
            }))
        });
    
    // GET /api/stats
    let stats = warp::path!("api" / "stats")
        .and(warp::get())
        .and(db_filter.clone())
        .map(|db: SharedDb| {
            let db = db.lock().unwrap();
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
                    
                    warp::reply::json(&response)
                }
                Err(e) => {
                    let error = ErrorResponse {
                        error: "database_error".to_string(),
                        message: e.to_string(),
                    };
                    warp::reply::json(&error)
                }
            }
        });
    
    // GET /api/objects/building/{id}
    let building_objects = warp::path!("api" / "objects" / "building" / u16)
        .and(warp::get())
        .and(db_filter.clone())
        .map(|building_id: u16, db: SharedDb| {
            let db = db.lock().unwrap();
            match db.get_building_objects(building_id) {
                Ok(objects) => {
                    let json_objects: Vec<ArxObjectJson> = objects
                        .iter()
                        .take(1000)
                        .map(arxobject_to_json)
                        .collect();
                    
                    let response = SpatialQueryResponse {
                        query_type: "building".to_string(),
                        count: json_objects.len(),
                        objects: json_objects,
                    };
                    
                    warp::reply::json(&response)
                }
                Err(e) => {
                    let error = ErrorResponse {
                        error: "database_error".to_string(),
                        message: e.to_string(),
                    };
                    warp::reply::json(&error)
                }
            }
        });
    
    // GET /api/objects/radius?x={x}&y={y}&z={z}&radius={r}
    let radius_query = warp::path!("api" / "objects" / "radius")
        .and(warp::get())
        .and(warp::query::<std::collections::HashMap<String, String>>())
        .and(db_filter.clone())
        .map(|params: std::collections::HashMap<String, String>, db: SharedDb| {
            let x = params.get("x").and_then(|s| s.parse::<f32>().ok()).unwrap_or(0.0);
            let y = params.get("y").and_then(|s| s.parse::<f32>().ok()).unwrap_or(0.0);
            let z = params.get("z").and_then(|s| s.parse::<f32>().ok()).unwrap_or(0.0);
            let radius = params.get("radius").and_then(|s| s.parse::<f32>().ok()).unwrap_or(1.0);
            
            let db = db.lock().unwrap();
            match db.find_within_radius(x, y, z, radius) {
                Ok(objects) => {
                    let json_objects: Vec<ArxObjectJson> = objects
                        .iter()
                        .take(1000)
                        .map(arxobject_to_json)
                        .collect();
                    
                    let response = SpatialQueryResponse {
                        query_type: format!("radius_{:.1}m", radius),
                        count: json_objects.len(),
                        objects: json_objects,
                    };
                    
                    warp::reply::json(&response)
                }
                Err(e) => {
                    let error = ErrorResponse {
                        error: "database_error".to_string(),
                        message: e.to_string(),
                    };
                    warp::reply::json(&error)
                }
            }
        });
    
    // GET /api/objects/nearest?x={x}&y={y}&z={z}&limit={n}
    let nearest_query = warp::path!("api" / "objects" / "nearest")
        .and(warp::get())
        .and(warp::query::<std::collections::HashMap<String, String>>())
        .and(db_filter.clone())
        .map(|params: std::collections::HashMap<String, String>, db: SharedDb| {
            let x = params.get("x").and_then(|s| s.parse::<f32>().ok()).unwrap_or(0.0);
            let y = params.get("y").and_then(|s| s.parse::<f32>().ok()).unwrap_or(0.0);
            let z = params.get("z").and_then(|s| s.parse::<f32>().ok()).unwrap_or(0.0);
            let limit = params.get("limit").and_then(|s| s.parse::<usize>().ok()).unwrap_or(10);
            
            let db = db.lock().unwrap();
            match db.find_nearest(x, y, z, limit.min(100)) {
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
                    
                    warp::reply::json(&response)
                }
                Err(e) => {
                    let error = ErrorResponse {
                        error: "database_error".to_string(),
                        message: e.to_string(),
                    };
                    warp::reply::json(&error)
                }
            }
        });
    
    // GET /api/objects/floor/{building_id}/{floor_num}
    let floor_objects = warp::path!("api" / "objects" / "floor" / u16 / u8)
        .and(warp::get())
        .and(db_filter.clone())
        .map(|building_id: u16, floor_num: u8, db: SharedDb| {
            let floor_height = floor_num as f32 * 3.0; // 3 meters per floor
            
            let db = db.lock().unwrap();
            match db.find_on_floor(building_id, floor_height, 1.5) {
                Ok(objects) => {
                    let json_objects: Vec<ArxObjectJson> = objects
                        .iter()
                        .take(1000)
                        .map(arxobject_to_json)
                        .collect();
                    
                    let response = SpatialQueryResponse {
                        query_type: format!("floor_{}", floor_num),
                        count: json_objects.len(),
                        objects: json_objects,
                    };
                    
                    warp::reply::json(&response)
                }
                Err(e) => {
                    let error = ErrorResponse {
                        error: "database_error".to_string(),
                        message: e.to_string(),
                    };
                    warp::reply::json(&error)
                }
            }
        });
    
    // Combine all routes
    let routes = health
        .or(stats)
        .or(building_objects)
        .or(radius_query)
        .or(nearest_query)
        .or(floor_objects)
        .with(warp::cors().allow_any_origin());
    
    println!("Starting server on http://0.0.0.0:{}", port);
    println!();
    println!("API Endpoints:");
    println!("  GET /health                                     - Health check");
    println!("  GET /api/stats                                  - Database statistics");
    println!("  GET /api/objects/building/{id}                  - Get all objects in building");
    println!("  GET /api/objects/radius?x=X&y=Y&z=Z&radius=R   - Find objects within radius");
    println!("  GET /api/objects/nearest?x=X&y=Y&z=Z&limit=N   - Find N nearest objects");
    println!("  GET /api/objects/floor/{building}/{floor_num}  - Get objects on specific floor");
    println!();
    println!("Ready to serve building intelligence queries!");
    
    warp::serve(routes)
        .run(([0, 0, 0, 0], port))
        .await;
}
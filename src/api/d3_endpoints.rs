//! D3.js-compatible API endpoints
//! 
//! These endpoints serve data in formats optimized for D3.js data binding,
//! ensuring smooth visualization updates and transitions.

use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::Json,
    Router,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value as JsonValue};
use std::sync::Arc;
use uuid::Uuid;

use crate::{
    database::Database,
    visualization::D3HierarchyNode,
};

/// Query parameters for D3 data requests
#[derive(Debug, Deserialize)]
pub struct D3QueryParams {
    /// Maximum depth for hierarchical data
    pub max_depth: Option<u32>,
    
    /// Include real-time state
    pub include_state: Option<bool>,
    
    /// Time range for historical data
    pub from_timestamp: Option<i64>,
    pub to_timestamp: Option<i64>,
    
    /// Aggregation level
    pub granularity: Option<String>,
}

/// D3.js-compatible endpoints router
pub fn d3_routes() -> Router<Arc<Database>> {
    Router::new()
        .route("/buildings/:id/d3/hierarchy", axum::routing::get(get_hierarchy))
        .route("/buildings/:id/d3/treemap", axum::routing::get(get_treemap))
        .route("/buildings/:id/d3/sunburst", axum::routing::get(get_sunburst))
        .route("/buildings/:id/d3/force-graph", axum::routing::get(get_force_graph))
        .route("/buildings/:id/d3/connections", axum::routing::get(get_connections))
        .route("/buildings/:id/d3/sankey", axum::routing::get(get_sankey))
        .route("/buildings/:id/d3/heatmap", axum::routing::get(get_heatmap))
        .route("/buildings/:id/d3/rating-arc", axum::routing::get(get_rating_arc))
        .route("/buildings/:id/d3/rating-history", axum::routing::get(get_rating_history))
        .route("/buildings/:id/d3/geo", axum::routing::get(get_geo_data))
        .route("/d3/scales/health", axum::routing::get(get_health_scale))
        .route("/d3/scales/grade", axum::routing::get(get_grade_scale))
}

/// Get building hierarchy for tree visualizations
async fn get_hierarchy(
    Path(building_id): Path<String>,
    Query(params): Query<D3QueryParams>,
    State(db): State<Arc<Database>>,
) -> Result<Json<JsonValue>, StatusCode> {
    // Build hierarchical structure from flat objects
    // TODO: Implement database method for building objects
    let objects: Vec<crate::models::BuildingObject> = vec![];
    
    // Convert paths to hierarchy
    let mut root = D3HierarchyNode {
        id: building_id.clone(),
        name: "Building".to_string(),
        node_type: "building".to_string(),
        value: 0.0,
        health: 0.0,
        rating_contribution: 1.0,
        children: vec![],
        properties: json!({}),
        state: crate::visualization::NodeState {
            status: "active".to_string(),
            needs_repair: false,
            activity_level: 0.0,
            last_updated: chrono::Utc::now().timestamp(),
            change_type: None,
        },
    };
    
    // Build tree from paths
    for obj in objects {
        add_to_hierarchy(&mut root, &obj);
    }
    
    // Calculate aggregated values
    calculate_hierarchy_values(&mut root);
    
    Ok(Json(serde_json::to_value(root).unwrap()))
}

/// Get treemap-specific data
async fn get_treemap(
    Path(building_id): Path<String>,
    State(db): State<Arc<Database>>,
) -> Result<Json<JsonValue>, StatusCode> {
    let hierarchy = get_hierarchy_data(&db, &building_id).await?;
    
    // Flatten for treemap with size values
    let treemap_data = json!({
        "name": "root",
        "children": flatten_for_treemap(hierarchy)
    });
    
    Ok(Json(treemap_data))
}

/// Get sunburst-specific data
async fn get_sunburst(
    Path(building_id): Path<String>,
    State(db): State<Arc<Database>>,
) -> Result<Json<JsonValue>, StatusCode> {
    let hierarchy = get_hierarchy_data(&db, &building_id).await?;
    
    // Add path strings for sunburst
    let sunburst_data = add_sunburst_paths(hierarchy);
    
    Ok(Json(sunburst_data))
}

/// Get force-directed graph of connections
async fn get_force_graph(
    Path(building_id): Path<String>,
    State(db): State<Arc<Database>>,
) -> Result<Json<JsonValue>, StatusCode> {
    // Get objects and their connections
    // TODO: Implement database method for building objects
    let objects: Vec<crate::models::BuildingObject> = vec![];
    
    // Build nodes
    let nodes: Vec<JsonValue> = objects.iter().map(|obj| {
        json!({
            "id": obj.id,
            "label": obj.name,
            "group": obj.object_type,
            "radius": calculate_node_radius(&obj),
            "health": obj.health,
            "fx": obj.location.as_ref().map(|l| l.x),
            "fy": obj.location.as_ref().map(|l| l.y)
        })
    }).collect();
    
    // Build links based on connections
    let links = build_connection_links(&objects);
    
    // Simulation parameters
    let simulation = json!({
        "charge_strength": -300,
        "link_distance": 50,
        "collision_radius": 10,
        "alpha_decay": 0.01
    });
    
    Ok(Json(json!({
        "nodes": nodes,
        "links": links,
        "simulation": simulation
    })))
}

/// Get connection graph for system relationships
async fn get_connections(
    Path(building_id): Path<String>,
    State(db): State<Arc<Database>>,
) -> Result<Json<JsonValue>, StatusCode> {
    // Similar to force graph but focuses on system connections
    get_force_graph(Path(building_id), State(db)).await
}

/// Get Sankey diagram data for token/value flows
async fn get_sankey(
    Path(building_id): Path<String>,
    Query(params): Query<D3QueryParams>,
    State(db): State<Arc<Database>>,
) -> Result<Json<JsonValue>, StatusCode> {
    // Get contribution and token flow data
    // TODO: Implement database method for token flows
    let flows = TokenFlow {
        contributors: vec![],
        areas: vec![],
        transactions: vec![],
    };
    
    // Build Sankey nodes and links
    let mut nodes = vec![];
    let mut links = vec![];
    
    // Contributors as source nodes
    for contributor in &flows.contributors {
        nodes.push(json!({
            "id": contributor.id,
            "name": contributor.name,
            "category": "contributor"
        }));
    }
    
    // Building areas as intermediate nodes
    for area in &flows.areas {
        nodes.push(json!({
            "id": area.id,
            "name": area.name,
            "category": "area"
        }));
    }
    
    // Token pools as sink nodes
    nodes.push(json!({
        "id": "reward_pool",
        "name": "Reward Pool",
        "category": "pool"
    }));
    
    // Build links from flows
    for flow in &flows.transactions {
        links.push(json!({
            "source": flow.from,
            "target": flow.to,
            "value": flow.amount,
            "flow_type": flow.flow_type
        }));
    }
    
    Ok(Json(json!({
        "nodes": nodes,
        "links": links
    })))
}

/// Get heatmap data for contribution patterns
async fn get_heatmap(
    Path(building_id): Path<String>,
    Query(params): Query<D3QueryParams>,
    State(db): State<Arc<Database>>,
) -> Result<Json<JsonValue>, StatusCode> {
    let granularity = params.granularity.as_deref().unwrap_or("hour");
    
    // Get contribution data
    // TODO: Implement database method for contributions
    let contributions: Vec<Contribution> = vec![];
    
    // Aggregate into heatmap grid
    let mut grid = vec![];
    
    match granularity {
        "hour" => {
            // Hour x Day heatmap
            for hour in 0..24 {
                for day in 0..7 {
                    let value = contributions.iter()
                        .filter(|c| {
                            c.hour == hour && c.weekday == day
                        })
                        .count() as f64;
                    
                    grid.push(json!({
                        "x": hour,
                        "y": day_name(day),
                        "value": value,
                        "details": {}
                    }));
                }
            }
        },
        "day" => {
            // Day x Week heatmap
            for day in 0..30 {
                for week in 0..4 {
                    let value = contributions.iter()
                        .filter(|c| {
                            // Simplified for placeholder
                            false
                        })
                        .count() as f64;
                    
                    grid.push(json!({
                        "x": day,
                        "y": format!("Week {}", week + 1),
                        "value": value,
                        "details": {}
                    }));
                }
            }
        },
        _ => {}
    }
    
    Ok(Json(json!({
        "grid": grid,
        "time_range": {
            "start": params.from_timestamp.unwrap_or(0),
            "end": params.to_timestamp.unwrap_or(chrono::Utc::now().timestamp()),
            "granularity": granularity
        }
    })))
}

/// Get rating arc diagram data
async fn get_rating_arc(
    Path(building_id): Path<String>,
    State(db): State<Arc<Database>>,
) -> Result<Json<JsonValue>, StatusCode> {
    // TODO: Implement database method for building rating
    let rating = crate::rating::models::BiltRating {
        building_id: building_id.clone(),
        current_grade: "0m".to_string(),
        numeric_score: 50.0,
        components: crate::rating::models::RatingComponents::default(),
        last_updated: chrono::Utc::now(),
        version: 1,
    };
    
    // Convert components to arc data
    let component_values = vec![
        ("Structure", rating.components.structure_score, "physical"),
        ("Inventory", rating.components.inventory_score, "physical"),
        ("Metadata", rating.components.metadata_score, "digital"),
        ("Sensors", rating.components.sensors_score, "digital"),
        ("History", rating.components.history_score, "temporal"),
        ("Quality", rating.components.quality_score, "validation"),
        ("Activity", rating.components.activity_score, "temporal"),
    ];
    
    let arcs: Vec<JsonValue> = component_values.iter().enumerate().map(|(i, (name, value, category))| {
        let start_angle = (i as f64 / component_values.len() as f64) * std::f64::consts::PI * 2.0;
        let end_angle = ((i + 1) as f64 / component_values.len() as f64) * std::f64::consts::PI * 2.0;
        
        json!({
            "startAngle": start_angle,
            "endAngle": end_angle,
            "innerRadius": 50,
            "outerRadius": 50 + (value * 0.5),
            "value": value,
            "name": name,
            "category": category,
            "padAngle": 0.02
        })
    }).collect();
    
    Ok(Json(json!({
        "arcs": arcs,
        "center": {
            "grade": rating.current_grade,
            "score": rating.numeric_score
        }
    })))
}

/// Get rating history for time series
async fn get_rating_history(
    Path(building_id): Path<String>,
    Query(params): Query<D3QueryParams>,
    State(db): State<Arc<Database>>,
) -> Result<Json<JsonValue>, StatusCode> {
    // TODO: Implement database method for rating history
    let history: Vec<RatingHistoryItem> = vec![];
    
    // Format for D3 time series
    let data_points: Vec<JsonValue> = history.iter().map(|h| {
        json!({
            "timestamp": h.timestamp,
            "score": h.score,
            "grade": h.grade,
            "components": h.components,
            "trigger_event": h.trigger_event
        })
    }).collect();
    
    // Include current rating
    // TODO: Implement database method for current rating
    let current = crate::rating::models::BiltRating {
        building_id: building_id.clone(),
        current_grade: "0m".to_string(),
        numeric_score: 50.0,
        components: crate::rating::models::RatingComponents::default(),
        last_updated: chrono::Utc::now(),
        version: 1,
    };
    
    Ok(Json(json!({
        "current": {
            "score": current.numeric_score,
            "grade": current.current_grade,
            "momentum": calculate_momentum(&history)
        },
        "history": data_points,
        "statistics": {
            "min": history.iter().map(|h| h.score).fold(f64::INFINITY, f64::min),
            "max": history.iter().map(|h| h.score).fold(f64::NEG_INFINITY, f64::max),
            "average": if history.is_empty() { 0.0 } else { history.iter().map(|h| h.score).sum::<f64>() / history.len() as f64 }
        }
    })))
}

/// Get geographic data for map visualizations
async fn get_geo_data(
    Path(building_id): Path<String>,
    State(db): State<Arc<Database>>,
) -> Result<Json<JsonValue>, StatusCode> {
    // TODO: Implement database method for building geo data
    let building_data = GeoBuildingData {
        geometry: json!({}),
        name: "Building".to_string(),
        bilt_grade: "0m".to_string(),
        bilt_score: 50.0,
        total_objects: 0,
        active_contributors: 0,
        market_value: 0.0,
    };
    
    // Convert to GeoJSON
    let geojson = json!({
        "type": "Feature",
        "geometry": building_data.geometry,
        "properties": {
            "id": building_id,
            "name": building_data.name,
            "bilt_grade": building_data.bilt_grade,
            "bilt_score": building_data.bilt_score,
            "total_objects": building_data.total_objects,
            "active_contributors": building_data.active_contributors,
            "market_value": building_data.market_value
        }
    });
    
    Ok(Json(geojson))
}

/// Get health color scale configuration
async fn get_health_scale() -> Json<JsonValue> {
    Json(json!({
        "domain": [0, 25, 50, 75, 100],
        "range": ["#d32f2f", "#f57c00", "#fbc02d", "#689f38", "#388e3c"],
        "interpolate": "lab"
    }))
}

/// Get BILT grade color scale configuration
async fn get_grade_scale() -> Json<JsonValue> {
    Json(json!({
        "domain": [
            "0z", "0y", "0x", "0w", "0v", "0u", "0t", "0s", "0r", "0q",
            "0p", "0o", "0n", "0m", "1z", "1y", "1x", "1w", "1v",
            "1u", "1t", "1s", "1r", "1q", "1p", "1A"
        ],
        "range": [
            "#2c003e", "#3d0e5a", "#4e1c76", "#5f2a92", "#7038ae",
            "#8146ca", "#9254e6", "#a362ff", "#a872ff", "#ad82ff",
            "#b292ff", "#b7a2ff", "#bcb2ff", "#c1c2ff", "#c6d2ff",
            "#cbdfff", "#d0ecff", "#d5f9ff", "#daffff", "#dfffef",
            "#e4ffdf", "#e9ffcf", "#eeffbf", "#f3ffaf", "#f8ff9f",
            "#fdff8f"
        ],
        "interpolate": "hsl"
    }))
}

// Helper functions

fn add_to_hierarchy(root: &mut D3HierarchyNode, obj: &crate::models::BuildingObject) {
    // Parse path and build hierarchy
    let path_parts: Vec<&str> = obj.path.trim_start_matches('/').split('/').collect();
    
    let mut current = root;
    for (i, part) in path_parts.iter().enumerate() {
        let is_leaf = i == path_parts.len() - 1;
        
        if is_leaf {
            // Add as leaf node
            current.children.push(D3HierarchyNode {
                id: obj.id.to_string(),
                name: part.to_string(),
                node_type: obj.object_type.clone(),
                value: 1.0,  // Each object has value 1
                health: obj.health as f64,
                rating_contribution: calculate_rating_contribution(obj),
                children: vec![],
                properties: serde_json::to_value(&obj.properties).unwrap(),
                state: crate::visualization::NodeState {
                    status: obj.status.clone(),
                    needs_repair: obj.needs_repair,
                    activity_level: 0.0,
                    last_updated: obj.last_updated.timestamp(),
                    change_type: None,
                },
            });
        } else {
            // Find or create intermediate node
            let node_id = path_parts[0..=i].join("/");
            if let Some(child) = current.children.iter_mut().find(|c| c.name == *part) {
                current = child;
            } else {
                current.children.push(D3HierarchyNode {
                    id: node_id,
                    name: part.to_string(),
                    node_type: "container".to_string(),
                    value: 0.0,
                    health: 100.0,
                    rating_contribution: 0.0,
                    children: vec![],
                    properties: json!({}),
                    state: crate::visualization::NodeState {
                        status: "active".to_string(),
                        needs_repair: false,
                        activity_level: 0.0,
                        last_updated: chrono::Utc::now().timestamp(),
                        change_type: None,
                    },
                });
                current = current.children.last_mut().unwrap();
            }
        }
    }
}

fn calculate_hierarchy_values(node: &mut D3HierarchyNode) {
    if node.children.is_empty() {
        return;
    }
    
    // Recursively calculate children first
    for child in &mut node.children {
        calculate_hierarchy_values(child);
    }
    
    // Aggregate from children
    let total_value: f64 = node.children.iter().map(|c| c.value).sum();
    let avg_health: f64 = node.children.iter().map(|c| c.health).sum::<f64>() 
        / node.children.len() as f64;
    
    node.value += total_value;
    node.health = avg_health;
}

fn calculate_rating_contribution(obj: &crate::models::BuildingObject) -> f64 {
    let mut contribution = 0.0;
    
    // Has location data
    if obj.location.is_some() {
        contribution += 0.2;
    }
    
    // Has properties
    if !obj.properties.is_null() {
        contribution += 0.3;
    }
    
    // Good health
    contribution += (obj.health as f64 / 100.0) * 0.3;
    
    // Not needing repair
    if !obj.needs_repair {
        contribution += 0.2;
    }
    
    contribution
}

fn calculate_node_radius(obj: &crate::models::BuildingObject) -> f64 {
    let base_radius = 5.0;
    let health_factor = obj.health as f64 / 100.0;
    let importance_factor = if obj.needs_repair { 1.5 } else { 1.0 };
    
    base_radius * health_factor * importance_factor
}

fn build_connection_links(objects: &[crate::models::BuildingObject]) -> Vec<JsonValue> {
    let mut links = vec![];
    
    // Build links based on path hierarchy
    for obj in objects {
        let path_parts: Vec<&str> = obj.path.trim_start_matches('/').split('/').collect();
        if path_parts.len() > 1 {
            // Link to parent
            let parent_path = path_parts[0..path_parts.len()-1].join("/");
            if let Some(parent) = objects.iter().find(|o| o.path.contains(&parent_path)) {
                links.push(json!({
                    "source": parent.id.to_string(),
                    "target": obj.id.to_string(),
                    "strength": 1.0,
                    "link_type": "hierarchy"
                }));
            }
        }
    }
    
    links
}

fn day_name(day: u32) -> &'static str {
    match day {
        0 => "Mon",
        1 => "Tue",
        2 => "Wed",
        3 => "Thu",
        4 => "Fri",
        5 => "Sat",
        6 => "Sun",
        _ => "Unknown"
    }
}

fn calculate_momentum(history: &[RatingHistoryItem]) -> f64 {
    if history.len() < 2 {
        return 0.0;
    }
    
    // Calculate trend over recent history
    let recent = &history[history.len().saturating_sub(10)..];
    let first = recent.first().unwrap().score;
    let last = recent.last().unwrap().score;
    
    (last - first) / first * 100.0
}

// Placeholder structures and functions
#[derive(Debug, Clone, Serialize, Deserialize)]
struct RatingHistoryItem {
    timestamp: i64,
    score: f64,
    grade: String,
    components: JsonValue,
    trigger_event: Option<String>,
}

#[derive(Debug, Clone)]
struct TokenFlow {
    contributors: Vec<Contributor>,
    areas: Vec<Area>,
    transactions: Vec<Transaction>,
}

#[derive(Debug, Clone)]
struct Contributor {
    id: String,
    name: String,
}

#[derive(Debug, Clone)]
struct Area {
    id: String,
    name: String,
}

#[derive(Debug, Clone)]
struct Transaction {
    from: String,
    to: String,
    amount: f64,
    flow_type: String,
}

#[derive(Debug, Clone)]
struct Contribution {
    timestamp: i64,
    hour: u32,
    weekday: u32,
}

#[derive(Debug, Clone)]
struct GeoBuildingData {
    geometry: JsonValue,
    name: String,
    bilt_grade: String,
    bilt_score: f64,
    total_objects: u64,
    active_contributors: u64,
    market_value: f64,
}

// Placeholder functions for complex operations
async fn get_hierarchy_data(db: &Arc<Database>, building_id: &str) -> Result<D3HierarchyNode, StatusCode> {
    todo!("Implement hierarchy data fetching")
}

fn flatten_for_treemap(hierarchy: D3HierarchyNode) -> Vec<JsonValue> {
    todo!("Implement treemap flattening")
}

fn add_sunburst_paths(hierarchy: D3HierarchyNode) -> JsonValue {
    todo!("Implement sunburst path addition")
}
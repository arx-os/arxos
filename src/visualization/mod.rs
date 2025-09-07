//! D3.js-Compatible Data Structures for Visualization
//! 
//! ArxOS data models are designed to bind directly to D3.js visualizations,
//! enabling real-time, data-driven building representations.

use serde::{Deserialize, Serialize};
use serde_json::Value as JsonValue;

/// D3.js-compatible hierarchical data structure for building objects
/// Maps directly to d3.hierarchy() for tree/sunburst/treemap visualizations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct D3HierarchyNode {
    /// Unique identifier for data binding (d3 .data() key)
    pub id: String,
    
    /// Display name for labels
    pub name: String,
    
    /// Node type for styling/behavior
    pub node_type: String,
    
    /// Numeric value for sizing (area, radius, etc.)
    pub value: f64,
    
    /// Health score 0-100 for color scales
    pub health: f64,
    
    /// BILT contribution to parent's rating
    pub rating_contribution: f64,
    
    /// Direct children for hierarchy
    pub children: Vec<D3HierarchyNode>,
    
    /// Properties for detail views/tooltips
    pub properties: JsonValue,
    
    /// Real-time state for animations
    pub state: NodeState,
}

/// Real-time state for D3.js transitions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeState {
    /// Current operational status
    pub status: String,
    
    /// Needs repair flag for highlighting
    pub needs_repair: bool,
    
    /// Activity level for pulse animations (0-100)
    pub activity_level: f64,
    
    /// Last update timestamp for fade effects
    pub last_updated: i64,
    
    /// Change type for enter/update/exit patterns
    pub change_type: Option<String>,
}

/// D3.js scale-compatible BILT rating data
/// Maps to d3.scaleOrdinal() for grade colors and d3.scaleLinear() for scores
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct D3BiltRating {
    /// Building identifier for data join
    pub building_id: String,
    
    /// Ordinal grade for color scales (0z-1A)
    pub grade: String,
    
    /// Linear score for position/size scales (0-100)
    pub score: f64,
    
    /// Component scores for radial/spider charts
    pub components: Vec<ComponentScore>,
    
    /// Historical data points for line charts
    pub history: Vec<RatingDataPoint>,
    
    /// Rating momentum for directional indicators
    pub momentum: f64,
}

/// Component score for multi-dimensional visualizations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComponentScore {
    /// Component name for axis labels
    pub name: String,
    
    /// Score value for radial distance (0-100)
    pub value: f64,
    
    /// Weight for importance sizing
    pub weight: f64,
    
    /// Color category for grouping
    pub category: String,
}

/// Time-series data point for temporal visualizations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RatingDataPoint {
    /// Unix timestamp for x-axis
    pub timestamp: i64,
    
    /// Score value for y-axis
    pub score: f64,
    
    /// Grade for categorical encoding
    pub grade: String,
    
    /// Event that triggered change
    pub trigger_event: Option<String>,
}

/// Force-directed graph data for connection visualizations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct D3ForceGraph {
    /// Nodes for force simulation
    pub nodes: Vec<ForceNode>,
    
    /// Links between nodes
    pub links: Vec<ForceLink>,
    
    /// Simulation parameters
    pub simulation: SimulationParams,
}

/// Node in force-directed layout
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ForceNode {
    /// Unique identifier
    pub id: String,
    
    /// Display label
    pub label: String,
    
    /// Node category for coloring
    pub group: String,
    
    /// Node radius based on importance
    pub radius: f64,
    
    /// Fixed position (optional)
    pub fx: Option<f64>,
    pub fy: Option<f64>,
    
    /// Current health/status
    pub health: f64,
}

/// Link in force-directed layout
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ForceLink {
    /// Source node ID
    pub source: String,
    
    /// Target node ID
    pub target: String,
    
    /// Link strength/weight
    pub strength: f64,
    
    /// Link type for styling
    pub link_type: String,
    
    /// Flow direction indicator
    pub directed: bool,
}

/// D3.js force simulation parameters
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimulationParams {
    pub charge_strength: f64,
    pub link_distance: f64,
    pub collision_radius: f64,
    pub alpha_decay: f64,
}

/// Sankey diagram data for flow visualizations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct D3SankeyData {
    /// Nodes in the flow
    pub nodes: Vec<SankeyNode>,
    
    /// Flow links with values
    pub links: Vec<SankeyLink>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SankeyNode {
    pub id: String,
    pub name: String,
    pub category: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SankeyLink {
    pub source: String,
    pub target: String,
    pub value: f64,
    pub flow_type: String,
}

/// Geographic data for map visualizations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct D3GeoBuilding {
    /// Building identifier
    pub id: String,
    
    /// GeoJSON geometry
    pub geometry: JsonValue,
    
    /// Properties for choropleth
    pub properties: GeoBuildingProps,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeoBuildingProps {
    pub name: String,
    pub bilt_grade: String,
    pub bilt_score: f64,
    pub total_objects: u64,
    pub active_contributors: u64,
    pub market_value: f64,
}

/// Real-time stream data for live visualizations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct D3StreamData {
    /// Event identifier
    pub id: String,
    
    /// Timestamp for x-axis
    pub timestamp: i64,
    
    /// Category for color/grouping
    pub category: String,
    
    /// Magnitude for y-axis
    pub value: f64,
    
    /// Optional detail for tooltips
    pub detail: Option<String>,
}

/// Contribution heatmap data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct D3HeatmapData {
    /// Grid of contribution intensity
    pub grid: Vec<HeatmapCell>,
    
    /// Time range for filtering
    pub time_range: TimeRange,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HeatmapCell {
    pub x: String,  // Hour or day
    pub y: String,  // Contributor or area
    pub value: f64, // Contribution count/value
    pub details: JsonValue,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimeRange {
    pub start: i64,
    pub end: i64,
    pub granularity: String, // "hour", "day", "week"
}

impl D3HierarchyNode {
    /// Convert flat building objects to D3 hierarchy
    pub fn from_building_objects(objects: Vec<crate::models::BuildingObject>) -> Self {
        // This would build the hierarchical structure from flat paths
        // e.g., /electrical/circuits/2/outlet_2A becomes nested structure
        todo!("Implement hierarchy building")
    }
    
    /// Calculate total value recursively
    pub fn total_value(&self) -> f64 {
        let children_value: f64 = self.children.iter()
            .map(|c| c.total_value())
            .sum();
        self.value + children_value
    }
    
    /// Generate D3-compatible JSON
    pub fn to_d3_json(&self) -> JsonValue {
        serde_json::to_value(self).unwrap()
    }
}

impl D3BiltRating {
    /// Convert to D3.js arc diagram data
    pub fn to_arc_data(&self) -> JsonValue {
        let arcs: Vec<JsonValue> = self.components.iter().map(|c| {
            serde_json::json!({
                "startAngle": 0,
                "endAngle": (c.value / 100.0) * std::f64::consts::PI * 2.0,
                "innerRadius": 50,
                "outerRadius": 50 + (c.weight * 50.0),
                "value": c.value,
                "name": c.name,
                "category": c.category
            })
        }).collect();
        
        serde_json::json!({ "arcs": arcs })
    }
    
    /// Generate grade color scale data
    pub fn grade_color_scale() -> JsonValue {
        serde_json::json!({
            "domain": ["0z", "0y", "0x", "0w", "0v", "0u", "0t", "0s", "0r", "0q", 
                       "0p", "0o", "0n", "0m", "1z", "1y", "1x", "1w", "1v", 
                       "1u", "1t", "1s", "1r", "1q", "1p", "1A"],
            "range": [
                "#2c003e", "#3d0e5a", "#4e1c76", "#5f2a92", "#7038ae",
                "#8146ca", "#9254e6", "#a362ff", "#a872ff", "#ad82ff",
                "#b292ff", "#b7a2ff", "#bcb2ff", "#c1c2ff", "#c6d2ff",
                "#cbdfff", "#d0ecff", "#d5f9ff", "#daffff", "#dfffef",
                "#e4ffdf", "#e9ffcf", "#eeffbf", "#f3ffaf", "#f8ff9f",
                "#fdff8f"
            ]
        })
    }
}

/// Event for real-time D3.js updates
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct D3UpdateEvent {
    /// Type of update for transition selection
    pub update_type: String,
    
    /// Affected element IDs for data binding
    pub element_ids: Vec<String>,
    
    /// New data to bind
    pub data: JsonValue,
    
    /// Transition parameters
    pub transition: TransitionParams,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransitionParams {
    pub duration_ms: u32,
    pub easing: String,
    pub delay_ms: u32,
}

/// Service for generating D3.js-compatible data
pub struct D3DataService {
    database: std::sync::Arc<crate::database::Database>,
}

impl D3DataService {
    /// Get building hierarchy for tree visualization
    pub async fn get_building_hierarchy(&self, building_id: &str) -> Result<D3HierarchyNode, anyhow::Error> {
        // Fetch objects and build hierarchy
        todo!("Implement hierarchy fetching")
    }
    
    /// Stream real-time updates for live visualizations
    pub async fn stream_updates(&self, building_id: &str) -> impl futures::Stream<Item = D3UpdateEvent> {
        // Subscribe to events and transform to D3 updates
        todo!("Implement event streaming")
    }
    
    /// Get force graph of object connections
    pub async fn get_connection_graph(&self, building_id: &str) -> Result<D3ForceGraph, anyhow::Error> {
        // Build graph from object relationships
        todo!("Implement connection graph")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_hierarchy_value_calculation() {
        let root = D3HierarchyNode {
            id: "root".to_string(),
            name: "Building".to_string(),
            node_type: "building".to_string(),
            value: 100.0,
            health: 75.0,
            rating_contribution: 1.0,
            children: vec![
                D3HierarchyNode {
                    id: "floor1".to_string(),
                    name: "Floor 1".to_string(),
                    node_type: "floor".to_string(),
                    value: 50.0,
                    health: 80.0,
                    rating_contribution: 0.5,
                    children: vec![],
                    properties: serde_json::json!({}),
                    state: NodeState {
                        status: "active".to_string(),
                        needs_repair: false,
                        activity_level: 60.0,
                        last_updated: 0,
                        change_type: None,
                    },
                },
            ],
            properties: serde_json::json!({}),
            state: NodeState {
                status: "active".to_string(),
                needs_repair: false,
                activity_level: 70.0,
                last_updated: 0,
                change_type: None,
            },
        };
        
        assert_eq!(root.total_value(), 150.0);
    }
    
    #[test]
    fn test_bilt_arc_data() {
        let rating = D3BiltRating {
            building_id: "test".to_string(),
            grade: "0m".to_string(),
            score: 65.0,
            components: vec![
                ComponentScore {
                    name: "Structure".to_string(),
                    value: 70.0,
                    weight: 0.8,
                    category: "physical".to_string(),
                },
            ],
            history: vec![],
            momentum: 0.5,
        };
        
        let arc_data = rating.to_arc_data();
        assert!(arc_data["arcs"].is_array());
    }
}
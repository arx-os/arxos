//! Core CAD data model for geometric entities

use serde::{Deserialize, Serialize};

/// Root structure representing an entire CAD drawing
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Drawing {
    pub layers: Vec<Layer>,
    pub active_layer: usize,
    pub units: DrawingUnits,
    pub bounds: BoundingBox,
    pub metadata: DrawingMetadata,
}

/// Metadata for building intelligence integration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DrawingMetadata {
    pub building_id: u16,
    pub floor_level: i8,
    pub created_at: u64,
    pub last_modified: u64,
    pub arxos_version: String,
}

/// Drawing units (for building context)
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum DrawingUnits {
    Millimeters,
    Meters,
    Feet,
    Inches,
}

/// Bounding box for spatial queries
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct BoundingBox {
    pub min: Point2D,
    pub max: Point2D,
}

/// A layer containing entities
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Layer {
    pub name: String,
    pub is_visible: bool,
    pub is_locked: bool,
    pub color: LayerColor,
    pub entities: Vec<Entity>,
}

/// Layer colors for ASCII rendering
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum LayerColor {
    Default,
    Electrical,  // For electrical systems
    HVAC,        // For HVAC systems  
    Plumbing,    // For plumbing
    Structural,  // For walls, beams
    Furniture,   // For equipment, furniture
    Annotation,  // For dimensions, labels
}

/// Geometric entities that can be drawn
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Entity {
    Line(Line),
    Circle(Circle),
    Arc(Arc),
    Rectangle(Rectangle),
    Polyline(Polyline),
    Text(Text),
    ArxObject(ArxObjectRef),  // Reference to mesh object
    Dimension(Dimension),
    Hatch(Hatch),
}

/// 2D point with f64 precision
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Point2D {
    pub x: f64,
    pub y: f64,
}

/// Line segment
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Line {
    pub start: Point2D,
    pub end: Point2D,
    pub style: LineStyle,
}

/// Line styles for different systems
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum LineStyle {
    Solid,
    Dashed,
    Dotted,
    CenterLine,
    Hidden,
    Phantom,
}

/// Circle
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Circle {
    pub center: Point2D,
    pub radius: f64,
}

/// Arc segment
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Arc {
    pub center: Point2D,
    pub radius: f64,
    pub start_angle: f64,  // Radians
    pub end_angle: f64,    // Radians
}

/// Rectangle
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Rectangle {
    pub origin: Point2D,
    pub width: f64,
    pub height: f64,
}

/// Polyline (connected line segments)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Polyline {
    pub points: Vec<Point2D>,
    pub is_closed: bool,
}

/// Text annotation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Text {
    pub position: Point2D,
    pub content: String,
    pub height: f64,
    pub rotation: f64,  // Radians
}

/// Reference to an ArxObject from the mesh
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct ArxObjectRef {
    pub object_id: u16,
    pub position: Point2D,
    pub symbol_type: ArxSymbol,
}

/// Symbols for ArxObjects in CAD view
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum ArxSymbol {
    Outlet,
    Switch,
    Thermostat,
    Sensor,
    AccessPoint,
    Camera,
    Panel,
    Custom(char),
}

/// Dimension for measurements
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Dimension {
    pub start: Point2D,
    pub end: Point2D,
    pub text_position: Point2D,
    pub dimension_type: DimensionType,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum DimensionType {
    Linear,
    Aligned,
    Angular,
    Radial,
}

/// Hatch pattern for filled areas
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Hatch {
    pub boundary: Polyline,
    pub pattern: HatchPattern,
    pub scale: f64,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum HatchPattern {
    Solid,
    Lines,
    Dots,
    CrossHatch,
    Concrete,
    Insulation,
}

/// Transformation matrix for entity manipulation
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Transform {
    pub translation: Point2D,
    pub rotation: f64,      // Radians
    pub scale: Point2D,
}

impl Drawing {
    pub fn new() -> Self {
        Self {
            layers: vec![Layer::new("0")],
            active_layer: 0,
            units: DrawingUnits::Millimeters,
            bounds: BoundingBox {
                min: Point2D { x: 0.0, y: 0.0 },
                max: Point2D { x: 1000.0, y: 1000.0 },
            },
            metadata: DrawingMetadata {
                building_id: 0,
                floor_level: 0,
                created_at: 0,
                last_modified: 0,
                arxos_version: "0.1.0".to_string(),
            },
        }
    }
    
    /// Add an entity to the active layer
    pub fn add_entity(&mut self, entity: Entity) {
        if let Some(layer) = self.layers.get_mut(self.active_layer) {
            if !layer.is_locked {
                layer.entities.push(entity);
                self.update_bounds();
            }
        }
    }
    
    /// Update drawing bounds based on entities
    fn update_bounds(&mut self) {
        // In full implementation, scan all entities to find min/max
    }
    
    /// Get all visible entities across layers
    pub fn visible_entities(&self) -> Vec<&Entity> {
        self.layers
            .iter()
            .filter(|l| l.is_visible)
            .flat_map(|l| l.entities.iter())
            .collect()
    }
}

impl Layer {
    pub fn new(name: &str) -> Self {
        Self {
            name: name.to_string(),
            is_visible: true,
            is_locked: false,
            color: LayerColor::Default,
            entities: Vec::new(),
        }
    }
}

impl Point2D {
    pub fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }
    
    pub fn distance_to(&self, other: &Point2D) -> f64 {
        ((other.x - self.x).powi(2) + (other.y - self.y).powi(2)).sqrt()
    }
    
    pub fn midpoint(&self, other: &Point2D) -> Point2D {
        Point2D {
            x: (self.x + other.x) / 2.0,
            y: (self.y + other.y) / 2.0,
        }
    }
}

impl Entity {
    /// Get bounding box for the entity
    pub fn bounding_box(&self) -> BoundingBox {
        match self {
            Entity::Line(line) => BoundingBox {
                min: Point2D {
                    x: line.start.x.min(line.end.x),
                    y: line.start.y.min(line.end.y),
                },
                max: Point2D {
                    x: line.start.x.max(line.end.x),
                    y: line.start.y.max(line.end.y),
                },
            },
            Entity::Circle(circle) => BoundingBox {
                min: Point2D {
                    x: circle.center.x - circle.radius,
                    y: circle.center.y - circle.radius,
                },
                max: Point2D {
                    x: circle.center.x + circle.radius,
                    y: circle.center.y + circle.radius,
                },
            },
            Entity::Rectangle(rect) => BoundingBox {
                min: rect.origin,
                max: Point2D {
                    x: rect.origin.x + rect.width,
                    y: rect.origin.y + rect.height,
                },
            },
            // Add other entity types
            _ => BoundingBox {
                min: Point2D { x: 0.0, y: 0.0 },
                max: Point2D { x: 0.0, y: 0.0 },
            },
        }
    }
}
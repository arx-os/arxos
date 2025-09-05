//! ASCII rendering pipeline for CAD entities

use std::collections::HashMap;
use crate::cad::{
    data_model::{Drawing, Entity, LayerColor, LineStyle, ArxSymbol, HatchPattern},
    algorithms::{bresenham_line, midpoint_circle, draw_arc, draw_rectangle, draw_polyline, GridPoint},
};

/// ASCII character buffer for terminal display
pub struct AsciiCanvas {
    pub width: usize,
    pub height: usize,
    pub buffer: Vec<Vec<Cell>>,
    pub viewport: Viewport,
}

/// Individual cell in the canvas
#[derive(Clone, Debug)]
pub struct Cell {
    pub char: char,
    pub depth: u8,     // Z-order for overlapping
    pub layer: usize,  // Layer index
}

/// Viewport for panning and zooming
#[derive(Clone, Debug)]
pub struct Viewport {
    pub center_x: f64,
    pub center_y: f64,
    pub scale: f64,  // Pixels per drawing unit
    pub aspect_ratio: f64,  // Terminal character aspect ratio
}

/// Rendering options
#[derive(Clone, Debug)]
pub struct RenderOptions {
    pub show_grid: bool,
    pub show_axes: bool,
    pub show_dimensions: bool,
    pub antialiasing: bool,
    pub char_set: CharacterSet,
}

/// Character sets for different rendering styles
#[derive(Clone, Debug)]
pub enum CharacterSet {
    Simple,    // Basic ASCII: - | + / \ * o
    Extended,  // Unicode box drawing: ─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼
    Shaded,    // Gradient shading: ░ ▒ ▓ █
    Technical, // CAD-specific symbols
}

/// Main ASCII renderer
pub struct AsciiRenderer {
    pub canvas: AsciiCanvas,
    pub options: RenderOptions,
    char_map: CharacterMap,
}

/// Maps geometric features to ASCII characters
struct CharacterMap {
    horizontal: char,
    vertical: char,
    diagonal_up: char,
    diagonal_down: char,
    corner_tl: char,
    corner_tr: char,
    corner_bl: char,
    corner_br: char,
    cross: char,
    t_up: char,
    t_down: char,
    t_left: char,
    t_right: char,
    point: char,
    circle: char,
}

impl AsciiRenderer {
    pub fn new(width: usize, height: usize) -> Self {
        let canvas = AsciiCanvas::new(width, height);
        let options = RenderOptions::default();
        let char_map = CharacterMap::from_set(&options.char_set);
        
        Self {
            canvas,
            options,
            char_map,
        }
    }
    
    /// Render a complete drawing
    pub fn render(&mut self, drawing: &Drawing) {
        self.canvas.clear();
        
        // Render grid if enabled
        if self.options.show_grid {
            self.render_grid();
        }
        
        // Render axes if enabled
        if self.options.show_axes {
            self.render_axes();
        }
        
        // Render all visible entities
        for (layer_idx, layer) in drawing.layers.iter().enumerate() {
            if !layer.is_visible {
                continue;
            }
            
            for entity in &layer.entities {
                self.render_entity(entity, layer_idx, &layer.color);
            }
        }
        
        // Post-process for line intersections
        self.process_intersections();
    }
    
    /// Render a single entity
    fn render_entity(&mut self, entity: &Entity, layer_idx: usize, color: &LayerColor) {
        match entity {
            Entity::Line(line) => {
                let points = bresenham_line(line.start, line.end);
                let char = self.get_line_char(&points, &line.style);
                self.draw_points(&points, char, layer_idx);
            }
            Entity::Circle(circle) => {
                let points = midpoint_circle(circle.center, circle.radius);
                self.draw_points(&points, self.char_map.circle, layer_idx);
            }
            Entity::Arc(arc) => {
                let points = draw_arc(arc.center, arc.radius, arc.start_angle, arc.end_angle);
                self.draw_points(&points, self.char_map.circle, layer_idx);
            }
            Entity::Rectangle(rect) => {
                let points = draw_rectangle(rect.origin, rect.width, rect.height);
                self.draw_points(&points, self.char_map.horizontal, layer_idx);
            }
            Entity::Polyline(poly) => {
                let points = draw_polyline(&poly.points, poly.is_closed);
                self.draw_points(&points, self.char_map.horizontal, layer_idx);
            }
            Entity::Text(text) => {
                self.render_text(&text.content, text.position, layer_idx);
            }
            Entity::ArxObject(arx_ref) => {
                self.render_arx_object(arx_ref, layer_idx);
            }
            Entity::Dimension(dim) => {
                self.render_dimension(dim, layer_idx);
            }
            Entity::Hatch(hatch) => {
                self.render_hatch(hatch, layer_idx);
            }
        }
    }
    
    /// Get appropriate character for a line based on its angle
    fn get_line_char(&self, points: &[GridPoint], style: &LineStyle) -> char {
        if points.len() < 2 {
            return self.char_map.point;
        }
        
        let dx = points[points.len() - 1].x - points[0].x;
        let dy = points[points.len() - 1].y - points[0].y;
        
        // Determine line character based on angle
        if dy == 0 {
            match style {
                LineStyle::Solid => self.char_map.horizontal,
                LineStyle::Dashed => '-',
                LineStyle::Dotted => '·',
                _ => self.char_map.horizontal,
            }
        } else if dx == 0 {
            match style {
                LineStyle::Solid => self.char_map.vertical,
                LineStyle::Dashed => '¦',
                LineStyle::Dotted => ':',
                _ => self.char_map.vertical,
            }
        } else if dx * dy > 0 {
            self.char_map.diagonal_down
        } else {
            self.char_map.diagonal_up
        }
    }
    
    /// Draw points to canvas with Z-buffering
    fn draw_points(&mut self, points: &[GridPoint], char: char, layer_idx: usize) {
        for point in points {
            let (canvas_x, canvas_y) = self.canvas.world_to_canvas(point);
            
            if canvas_x < self.canvas.width && canvas_y < self.canvas.height {
                let cell = &mut self.canvas.buffer[canvas_y][canvas_x];
                
                // Z-buffer check (lower layer = higher priority)
                if layer_idx as u8 <= cell.depth {
                    cell.char = char;
                    cell.depth = layer_idx as u8;
                    cell.layer = layer_idx;
                }
            }
        }
    }
    
    /// Render text at position
    fn render_text(&mut self, text: &str, position: crate::cad::data_model::Point2D, layer_idx: usize) {
        let grid_point = GridPoint {
            x: position.x.round() as i32,
            y: position.y.round() as i32,
        };
        
        let (start_x, start_y) = self.canvas.world_to_canvas(&grid_point);
        
        for (i, ch) in text.chars().enumerate() {
            let x = start_x + i;
            if x < self.canvas.width && start_y < self.canvas.height {
                self.canvas.buffer[start_y][x] = Cell {
                    char: ch,
                    depth: layer_idx as u8,
                    layer: layer_idx,
                };
            }
        }
    }
    
    /// Render ArxObject symbol
    fn render_arx_object(&mut self, arx_ref: &crate::cad::data_model::ArxObjectRef, layer_idx: usize) {
        let symbol = match arx_ref.symbol_type {
            ArxSymbol::Outlet => "⊡",
            ArxSymbol::Switch => "⊟",
            ArxSymbol::Thermostat => "⊞",
            ArxSymbol::Sensor => "◉",
            ArxSymbol::AccessPoint => "@",
            ArxSymbol::Camera => "◎",
            ArxSymbol::Panel => "⊞",
            ArxSymbol::Custom(c) => return self.render_text(&c.to_string(), arx_ref.position, layer_idx),
        };
        
        self.render_text(symbol, arx_ref.position, layer_idx);
    }
    
    /// Render dimension lines
    fn render_dimension(&mut self, dim: &crate::cad::data_model::Dimension, layer_idx: usize) {
        // Draw dimension line
        let points = bresenham_line(dim.start, dim.end);
        self.draw_points(&points, self.char_map.horizontal, layer_idx);
        
        // Calculate and render dimension text
        let distance = dim.start.distance_to(&dim.end);
        let text = format!("{:.1}", distance);
        self.render_text(&text, dim.text_position, layer_idx);
    }
    
    /// Render hatch pattern
    fn render_hatch(&mut self, hatch: &crate::cad::data_model::Hatch, layer_idx: usize) {
        let boundary_points = draw_polyline(&hatch.boundary.points, hatch.boundary.is_closed);
        
        // Simple fill for now - in full implementation, use pattern
        let fill_char = match hatch.pattern {
            HatchPattern::Solid => '█',
            HatchPattern::Lines => '═',
            HatchPattern::Dots => '·',
            HatchPattern::CrossHatch => '╬',
            HatchPattern::Concrete => '▓',
            HatchPattern::Insulation => '≈',
        };
        
        // Draw boundary
        self.draw_points(&boundary_points, fill_char, layer_idx);
    }
    
    /// Render background grid
    fn render_grid(&mut self) {
        let grid_spacing = 10.0 * self.canvas.viewport.scale;
        let grid_char = '·';
        
        for y in 0..self.canvas.height {
            for x in 0..self.canvas.width {
                if x % grid_spacing.round() as usize == 0 && 
                   y % grid_spacing.round() as usize == 0 {
                    self.canvas.buffer[y][x] = Cell {
                        char: grid_char,
                        depth: 255,  // Background layer
                        layer: 0,
                    };
                }
            }
        }
    }
    
    /// Render coordinate axes
    fn render_axes(&mut self) {
        let center_x = self.canvas.width / 2;
        let center_y = self.canvas.height / 2;
        
        // X-axis
        for x in 0..self.canvas.width {
            self.canvas.buffer[center_y][x] = Cell {
                char: self.char_map.horizontal,
                depth: 254,
                layer: 0,
            };
        }
        
        // Y-axis
        for y in 0..self.canvas.height {
            self.canvas.buffer[y][center_x] = Cell {
                char: self.char_map.vertical,
                depth: 254,
                layer: 0,
            };
        }
        
        // Origin
        self.canvas.buffer[center_y][center_x] = Cell {
            char: self.char_map.cross,
            depth: 254,
            layer: 0,
        };
    }
    
    /// Process line intersections to use appropriate junction characters
    fn process_intersections(&mut self) {
        // Scan for intersections and replace with junction characters
        for y in 1..self.canvas.height - 1 {
            for x in 1..self.canvas.width - 1 {
                let neighbors = self.get_neighbors(x, y);
                if let Some(junction) = self.determine_junction(&neighbors) {
                    self.canvas.buffer[y][x].char = junction;
                }
            }
        }
    }
    
    /// Get neighboring cells
    fn get_neighbors(&self, x: usize, y: usize) -> [bool; 8] {
        [
            self.is_line_char(x, y - 1),     // North
            self.is_line_char(x + 1, y - 1), // NE
            self.is_line_char(x + 1, y),     // East
            self.is_line_char(x + 1, y + 1), // SE
            self.is_line_char(x, y + 1),     // South
            self.is_line_char(x - 1, y + 1), // SW
            self.is_line_char(x - 1, y),     // West
            self.is_line_char(x - 1, y - 1), // NW
        ]
    }
    
    /// Check if cell contains a line character
    fn is_line_char(&self, x: usize, y: usize) -> bool {
        if x >= self.canvas.width || y >= self.canvas.height {
            return false;
        }
        
        let ch = self.canvas.buffer[y][x].char;
        ch == self.char_map.horizontal ||
        ch == self.char_map.vertical ||
        ch == self.char_map.diagonal_up ||
        ch == self.char_map.diagonal_down
    }
    
    /// Determine junction character based on neighbors
    fn determine_junction(&self, neighbors: &[bool; 8]) -> Option<char> {
        let n = neighbors[0];
        let e = neighbors[2];
        let s = neighbors[4];
        let w = neighbors[6];
        
        match (n, e, s, w) {
            (true, true, true, true) => Some(self.char_map.cross),
            (true, true, false, false) => Some(self.char_map.corner_bl),
            (true, false, false, true) => Some(self.char_map.corner_br),
            (false, true, true, false) => Some(self.char_map.corner_tl),
            (false, false, true, true) => Some(self.char_map.corner_tr),
            (true, true, true, false) => Some(self.char_map.t_left),
            (true, true, false, true) => Some(self.char_map.t_down),
            (true, false, true, true) => Some(self.char_map.t_right),
            (false, true, true, true) => Some(self.char_map.t_up),
            _ => None,
        }
    }
    
    /// Convert canvas to string for display
    pub fn to_string(&self) -> String {
        let mut output = String::new();
        
        for row in &self.canvas.buffer {
            for cell in row {
                output.push(cell.char);
            }
            output.push('\n');
        }
        
        output
    }
}

impl AsciiCanvas {
    pub fn new(width: usize, height: usize) -> Self {
        let buffer = vec![vec![Cell::default(); width]; height];
        let viewport = Viewport {
            center_x: width as f64 / 2.0,
            center_y: height as f64 / 2.0,
            scale: 1.0,
            aspect_ratio: 2.0,  // Terminal chars are ~2x tall
        };
        
        Self {
            width,
            height,
            buffer,
            viewport,
        }
    }
    
    pub fn clear(&mut self) {
        for row in &mut self.buffer {
            for cell in row {
                *cell = Cell::default();
            }
        }
    }
    
    /// Convert world coordinates to canvas coordinates
    pub fn world_to_canvas(&self, point: &GridPoint) -> (usize, usize) {
        let x = ((point.x as f64 - self.viewport.center_x) * self.viewport.scale + self.width as f64 / 2.0) as usize;
        let y = ((point.y as f64 - self.viewport.center_y) * self.viewport.scale * self.viewport.aspect_ratio + self.height as f64 / 2.0) as usize;
        (x, y)
    }
}

impl Default for Cell {
    fn default() -> Self {
        Self {
            char: ' ',
            depth: 255,
            layer: 0,
        }
    }
}

impl Default for RenderOptions {
    fn default() -> Self {
        Self {
            show_grid: false,
            show_axes: true,
            show_dimensions: true,
            antialiasing: false,
            char_set: CharacterSet::Extended,
        }
    }
}

impl CharacterMap {
    fn from_set(set: &CharacterSet) -> Self {
        match set {
            CharacterSet::Simple => Self {
                horizontal: '-',
                vertical: '|',
                diagonal_up: '/',
                diagonal_down: '\\',
                corner_tl: '+',
                corner_tr: '+',
                corner_bl: '+',
                corner_br: '+',
                cross: '+',
                t_up: '+',
                t_down: '+',
                t_left: '+',
                t_right: '+',
                point: '*',
                circle: 'o',
            },
            CharacterSet::Extended => Self {
                horizontal: '─',
                vertical: '│',
                diagonal_up: '╱',
                diagonal_down: '╲',
                corner_tl: '┌',
                corner_tr: '┐',
                corner_bl: '└',
                corner_br: '┘',
                cross: '┼',
                t_up: '┴',
                t_down: '┬',
                t_left: '┤',
                t_right: '├',
                point: '●',
                circle: '○',
            },
            CharacterSet::Shaded => Self {
                horizontal: '▬',
                vertical: '▮',
                diagonal_up: '░',
                diagonal_down: '▒',
                corner_tl: '▓',
                corner_tr: '▓',
                corner_bl: '▓',
                corner_br: '▓',
                cross: '█',
                t_up: '█',
                t_down: '█',
                t_left: '█',
                t_right: '█',
                point: '█',
                circle: '●',
            },
            CharacterSet::Technical => Self {
                horizontal: '═',
                vertical: '║',
                diagonal_up: '╱',
                diagonal_down: '╲',
                corner_tl: '╔',
                corner_tr: '╗',
                corner_bl: '╚',
                corner_br: '╝',
                cross: '╬',
                t_up: '╩',
                t_down: '╦',
                t_left: '╣',
                t_right: '╠',
                point: '◆',
                circle: '◯',
            },
        }
    }
}
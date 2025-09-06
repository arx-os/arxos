//! Simple 2D ASCII Renderer - Fast top-down views

use crate::arxobject::{ArxObject, object_types};
use crate::rendering::AsciiRenderer;
use std::collections::HashMap;

pub struct Simple2DRenderer {
    width: usize,
    height: usize,
    grid: Vec<Vec<char>>,
}

impl Simple2DRenderer {
    pub fn new(width: usize, height: usize) -> Self {
        Self {
            width,
            height,
            grid: vec![vec![' '; width]; height],
        }
    }
    
    fn clear(&mut self) {
        for row in &mut self.grid {
            row.fill(' ');
        }
    }
}

impl AsciiRenderer for Simple2DRenderer {
    fn render(&mut self, objects: &[ArxObject]) -> String {
        self.clear();
        
        // Find bounds
        let (mut min_x, mut max_x) = (i16::MAX, i16::MIN);
        let (mut min_y, mut max_y) = (i16::MAX, i16::MIN);
        
        for obj in objects {
            min_x = min_x.min(obj.x);
            max_x = max_x.max(obj.x);
            min_y = min_y.min(obj.y);
            max_y = max_y.max(obj.y);
        }
        
        // Map objects to grid
        for obj in objects {
            let x = if max_x > min_x {
                ((obj.x - min_x) as f32 / (max_x - min_x) as f32 * (self.width - 1) as f32) as usize
            } else { self.width / 2 };
            
            let y = if max_y > min_y {
                ((obj.y - min_y) as f32 / (max_y - min_y) as f32 * (self.height - 1) as f32) as usize
            } else { self.height / 2 };
            
            if x < self.width && y < self.height {
                self.grid[y][x] = match obj.object_type {
                    t if t == object_types::WALL => '█',
                    t if t == object_types::FLOOR => '.',
                    t if t == object_types::DOOR => '┃',
                    t if t == object_types::OUTLET => 'o',
                    _ => '░',
                };
            }
        }
        
        // Convert to string
        self.grid.iter()
            .map(|row| row.iter().collect::<String>())
            .collect::<Vec<_>>()
            .join("\n")
    }
    
    fn name(&self) -> &'static str {
        "Simple 2D ASCII Renderer"
    }
    
    fn use_case(&self) -> &'static str {
        "Fast top-down floor plans and overviews"
    }
}
//! ASCII renderer for game world

use crate::progressive_renderer::ProgressiveRenderer;
use super::world::World;

/// Game-specific renderer
pub struct GameRenderer {
    progressive: ProgressiveRenderer,
}

impl GameRenderer {
    pub fn new() -> Self {
        Self {
            progressive: ProgressiveRenderer::new(),
        }
    }
    
    pub fn render(&self, world: &World) -> String {
        world.render_view()
    }
}
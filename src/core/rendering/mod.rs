//! Unified Rendering Module for ArxOS
//! 
//! All ASCII rendering approaches in one organized module

pub mod ascii_2d;
pub mod ascii_3d;
pub mod cinematic;
pub mod rasterizer;

use crate::arxobject::ArxObject;

/// Common trait for all ASCII renderers
pub trait AsciiRenderer {
    /// Render ArxObjects to ASCII art
    fn render(&mut self, objects: &[ArxObject]) -> String;
    
    /// Get renderer name
    fn name(&self) -> &'static str;
    
    /// Get recommended use case
    fn use_case(&self) -> &'static str;
}

/// Rendering quality levels
pub enum RenderQuality {
    Draft,      // Fast, basic
    Standard,   // Balanced
    Cinematic,  // High quality, slow
}

/// Unified renderer that can switch between approaches
pub struct UnifiedRenderer {
    quality: RenderQuality,
    width: usize,
    height: usize,
}

impl UnifiedRenderer {
    pub fn new(width: usize, height: usize, quality: RenderQuality) -> Self {
        Self { quality, width, height }
    }
    
    pub fn render(&mut self, objects: &[ArxObject]) -> String {
        match self.quality {
            RenderQuality::Draft => {
                let mut renderer = ascii_2d::Simple2DRenderer::new(self.width, self.height);
                renderer.render(objects)
            },
            RenderQuality::Standard => {
                let mut renderer = ascii_3d::Perspective3DRenderer::new(self.width, self.height);
                renderer.render(objects)
            },
            RenderQuality::Cinematic => {
                let mut renderer = cinematic::CinematicRenderer::new(self.width, self.height);
                renderer.render(objects)
            },
        }
    }
}
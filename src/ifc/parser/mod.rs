//! Custom IFC Parser for ArxOS
//! 
//! This module provides a high-performance, lossless, and Git-friendly 
//! implementation of the ISO-10303-21 (STEP) format for IFC data.

pub mod lexer;
pub mod registry;
pub mod resolver;
pub mod geometry;
pub mod mesh;

pub use lexer::StepLexer;
pub use registry::EntityRegistry;
pub use resolver::IfcResolver;

//! Re-export of [`arxos_core::BuildingLocator`] for networking callers.

use crate::error::{NetError, Result};

pub use arxos_core::BuildingLocator;

/// Parse `arx://bldg/<id>?controllers=...&inbox=...`
pub fn parse_arx_uri(s: &str) -> Result<BuildingLocator> {
    BuildingLocator::parse(s).map_err(|e| NetError::Protocol(e.to_string()))
}

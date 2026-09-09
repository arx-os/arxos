//! `arx://` locator FFI.

use crate::ArxosError;

#[derive(Debug, Clone)]
pub struct FfiBuildingLocator {
    pub building_id: String,
    pub controllers: Vec<String>,
    pub inbox: Option<String>,
}

/// Parse `arx://bldg/<id>?controllers=&inbox=`.
pub fn parse_building_locator(uri: String) -> Result<FfiBuildingLocator, ArxosError> {
    let loc = arxos_core::BuildingLocator::parse(&uri).map_err(|e| ArxosError::InvalidInput {
        message: e.to_string(),
    })?;
    Ok(FfiBuildingLocator {
        building_id: loc.building_id.to_string(),
        controllers: loc.controllers.iter().map(|k| k.to_string()).collect(),
        inbox: loc.inbox,
    })
}

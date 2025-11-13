//! Helper utilities for deriving canonical building identifiers from IFC data.

use crate::utils::string::{normalize_label, slugify};

/// Canonical identifiers for a building extracted from IFC metadata.
#[derive(Debug, Clone)]
pub(crate) struct BuildingIdentifiers {
    /// Human readable building name (as displayed in CLI/UI).
    pub display_name: String,
    /// Lowercase slug suitable for filenames and path segments.
    pub slug: String,
}

impl BuildingIdentifiers {
    /// Build a `/building/<slug>` path segment consistent with ArxAddress.
    pub fn canonical_path(&self) -> String {
        format!("/building/{}", self.slug)
    }
}

/// Derive canonical building identifiers from the optional IFC label and a
/// required fallback (typically the IFC entity id).
pub(crate) fn derive_building_identifiers(
    raw_label: Option<&str>,
    fallback: &str,
) -> BuildingIdentifiers {
    let normalised_label = raw_label
        .map(normalize_label)
        .filter(|label| !label.is_empty() && !label.eq_ignore_ascii_case("unknown"));

    let fallback_label = {
        let cleaned = normalize_label(fallback);
        if cleaned.is_empty() {
            "Building".to_string()
        } else {
            cleaned
        }
    };

    let display_name = normalised_label.unwrap_or_else(|| fallback_label.clone());

    let mut slug = slugify(&display_name);
    if slug.is_empty() {
        slug = slugify(&fallback_label);
    }
    if slug.is_empty() {
        slug = "building".to_string();
    }

    BuildingIdentifiers {
        display_name,
        slug,
    }
}

#[cfg(test)]
mod tests {
    use super::derive_building_identifiers;

    #[test]
    fn derive_identifiers_prefers_label() {
        let ids = derive_building_identifiers(Some("Main Tower"), "#42");
        assert_eq!(ids.display_name, "Main Tower");
        assert_eq!(ids.slug, "main-tower");
        assert_eq!(ids.canonical_path(), "/building/main-tower");
    }

    #[test]
    fn derive_identifiers_falls_back_to_guid() {
        let ids = derive_building_identifiers(Some(""), "#42");
        assert_eq!(ids.display_name, "#42");
        assert_eq!(ids.slug, "42");
    }

    #[test]
    fn derive_identifiers_handles_unknown_label() {
        let ids = derive_building_identifiers(Some("Unknown"), "HQ-East");
        assert_eq!(ids.display_name, "HQ-East");
        assert_eq!(ids.slug, "hq-east");
    }
}


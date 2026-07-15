//! Shared import orchestration for IFC and LiDAR.

use std::path::Path;

use anyhow::{anyhow, Context, Result};

use crate::core::{Building, BuildingMetadata};
use crate::ifc::mapping::{merge_building_with_policy, FidelityLevel, LossReport, MergePolicy};
use crate::ifc::IFCProcessor;
use crate::spatial::lidar::LidarPipeline;
use crate::validation::{validate_building, BuildingValidationReport};
use crate::yaml::BuildingYamlSerializer;

/// Which adapter produced the incoming model.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IngestSource {
    Ifc,
    Lidar,
    /// Text / AR command script edits (in-place; no hierarchy replace).
    Text,
}

impl IngestSource {
    pub fn merge_policy(self) -> MergePolicy {
        match self {
            IngestSource::Ifc => MergePolicy::ifc(),
            IngestSource::Lidar => MergePolicy::lidar(),
            // Text edits are applied in-place; merge only if caller supplies existing
            IngestSource::Text => MergePolicy::lidar(),
        }
    }

    pub fn tag(self) -> &'static str {
        match self {
            IngestSource::Ifc => "ifc",
            IngestSource::Lidar => "lidar",
            IngestSource::Text => "text",
        }
    }
}

/// Options for finalize / file import helpers.
#[derive(Debug, Clone, Default)]
pub struct IngestOptions {
    /// When true, run [`validate_building`] after merge.
    pub validate: bool,
    /// Optional existing building to merge into (e.g. loaded from YAML).
    pub existing: Option<Building>,
    /// Override merge policy; defaults from source.
    pub policy: Option<MergePolicy>,
}

/// Outcome of a shared ingest path.
#[derive(Debug, Clone)]
pub struct IngestResult {
    pub building: Building,
    pub source: IngestSource,
    pub report: LossReport,
    pub validation: BuildingValidationReport,
}

impl IngestResult {
    pub fn summary_lines(&self) -> Vec<String> {
        let mut lines = self.report.summary_lines();
        lines.extend(self.validation.summary_lines());
        lines
    }
}

/// Merge (optional), attach source metadata tags, validate.
pub fn finalize_ingest(
    mut building: Building,
    source: IngestSource,
    options: IngestOptions,
) -> IngestResult {
    let policy = options.policy.unwrap_or_else(|| source.merge_policy());
    let mut report = LossReport::new(FidelityLevel::L2);

    if let Some(existing) = options.existing {
        let merge = merge_building_with_policy(&existing, building, &policy);
        report.merge = Some(merge.stats);
        report.warnings.extend(merge.warnings);
        building = merge.building;
    }

    promote_equipment_anchors(&mut building);

    // Tag source on metadata
    let tag = source.tag();
    if let Some(meta) = &mut building.metadata {
        if !meta.tags.iter().any(|t| t == tag) {
            meta.tags.push(tag.to_string());
        }
    }

    let validation = if options.validate {
        validate_building(&building)
    } else {
        BuildingValidationReport::default()
    };

    // Surface validation errors as loss-report warnings for a single summary stream
    for v in validation.errors() {
        report.warn(
            v.rule_id.clone(),
            format!("validation error: {}", v.message),
        );
    }
    for v in validation.warnings() {
        report.warn(
            v.rule_id.clone(),
            format!("validation warning: {}", v.message),
        );
    }

    IngestResult {
        building,
        source,
        report,
        validation,
    }
}

/// Parse IFC at `path`, optionally merge with `existing_yaml` or sibling YAML, validate.
pub fn import_ifc_path(
    path: &Path,
    existing_yaml: Option<&Path>,
    strict: bool,
    validate: bool,
) -> Result<IngestResult> {
    crate::resource_limits::check_file_size(
        path,
        crate::resource_limits::max_ifc_bytes(),
        "IFC",
    )?;

    let processor = IFCProcessor::new();
    let path_str = path
        .to_str()
        .ok_or_else(|| anyhow!("Invalid IFC path encoding"))?;
    let parsed = processor
        .parse_native(path_str, strict)
        .with_context(|| format!("native IFC parse failed for {}", path.display()))?;

    let mut building = parsed.building;
    let base_report = parsed.report;

    building.metadata = Some(BuildingMetadata {
        source_file: Some(path.display().to_string()),
        parser_version: env!("CARGO_PKG_VERSION").to_string(),
        total_entities: parsed.stats.total_entities,
        spatial_entities: parsed.stats.spatial_entities,
        coordinate_system: "building_local".to_string(),
        units: "meters".to_string(),
        tags: vec!["ifc".to_string()],
        properties: Default::default(),
    });

    let existing = load_existing_yaml(existing_yaml)?;

    let mut result = finalize_ingest(
        building,
        IngestSource::Ifc,
        IngestOptions {
            validate,
            existing,
            policy: Some(MergePolicy::ifc()),
        },
    );

    // Prepend parse-time warnings
    let mut warnings = base_report.warnings;
    warnings.append(&mut result.report.warnings);
    result.report.warnings = warnings;
    if result.report.merge.is_none() {
        result.report.merge = base_report.merge;
    }

    Ok(result)
}

/// Run LiDAR pipeline, optionally merge with existing YAML, validate.
pub fn import_lidar_path(
    path: &Path,
    existing_yaml: Option<&Path>,
    voxel_size: f64,
    light_mode: bool,
    validate: bool,
) -> Result<IngestResult> {
    crate::resource_limits::check_file_size(
        path,
        crate::resource_limits::max_lidar_bytes(),
        "LiDAR",
    )?;

    let pipeline = LidarPipeline::new(voxel_size, light_mode);
    let building = pipeline
        .process(path)
        .with_context(|| format!("LiDAR pipeline failed for {}", path.display()))?;

    let existing = load_existing_yaml(existing_yaml)?;

    Ok(finalize_ingest(
        building,
        IngestSource::Lidar,
        IngestOptions {
            validate,
            existing,
            policy: Some(MergePolicy::lidar()),
        },
    ))
}

fn load_existing_yaml(path: Option<&Path>) -> Result<Option<Building>> {
    let Some(path) = path else {
        return Ok(None);
    };
    if !path.exists() {
        return Ok(None);
    }
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("read existing YAML {}", path.display()))?;
    let building = BuildingYamlSerializer::deserialize_building(&content)
        .map_err(|e| anyhow!("deserialize existing YAML {}: {}", path.display(), e))?;
    Ok(Some(building))
}

fn promote_equipment_anchors(building: &mut crate::core::Building) {
    use crate::core::{Anchor, EquipmentType};

    fn is_ar_anchor(eq: &crate::core::Equipment) -> bool {
        match &eq.equipment_type {
            EquipmentType::Other(name) => name == "AR_Anchor" || name.to_uppercase().contains("ANCHOR") || name.to_uppercase().contains("MARKER"),
            _ => false,
        }
    }

    fn convert_eq_to_anchor(eq: crate::core::Equipment) -> Anchor {
        let confidence = eq.properties.get("confidence")
            .and_then(|s| s.parse::<f64>().ok())
            .unwrap_or(1.0);
        let recalibration_count = eq.properties.get("recalibration_count")
            .and_then(|s| s.parse::<u32>().ok())
            .unwrap_or(0);

        Anchor {
            id: eq.id,
            name: eq.name,
            address: eq.address,
            position: eq.position,
            recalibration_count,
            last_recalibrated_at: None,
            confidence,
            relative_poses: Vec::new(),
            properties: eq.properties,
            map_ref: None,
        }
    }

    for floor in &mut building.floors {
        let mut floor_anchors = Vec::new();
        floor.equipment.retain(|eq| {
            if is_ar_anchor(eq) {
                floor_anchors.push(convert_eq_to_anchor(eq.clone()));
                false
            } else {
                true
            }
        });
        floor.anchors.extend(floor_anchors);

        for wing in &mut floor.wings {
            let mut wing_anchors = Vec::new();
            wing.equipment.retain(|eq| {
                if is_ar_anchor(eq) {
                    wing_anchors.push(convert_eq_to_anchor(eq.clone()));
                    false
                } else {
                    true
                }
            });
            wing.anchors.extend(wing_anchors);

            for room in &mut wing.rooms {
                let mut room_anchors = Vec::new();
                room.equipment.retain(|eq| {
                    if is_ar_anchor(eq) {
                        room_anchors.push(convert_eq_to_anchor(eq.clone()));
                        false
                    } else {
                        true
                    }
                });
                room.anchors.extend(room_anchors);
            }
        }
    }
}

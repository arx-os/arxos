//! Capture commands.

use std::collections::BTreeMap;
use std::fs;
use std::str::FromStr;

use anyhow::{Context, Result};
use arxos_core::capture::{AnnotationCapture, PointCloudCapture, SpaceCapture};
use arxos_core::object::{BuildingId, Pose};
use arxos_core::repository::BuildingRepository;

use crate::args::{CaptureCommands, Cli};

pub fn run(cli: &Cli, command: CaptureCommands) -> Result<()> {
    match command {
        CaptureCommands::Space {
            building_id,
            name,
            x,
            y,
            z,
            quiet,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let mut repo = BuildingRepository::open(&cli.store, &bid)?;
            let res = repo.capture_space(&SpaceCapture {
                entity_id: None,
                name,
                pose: Pose {
                    position: [x, y, z],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
                bounds: None,
                floor: None,
                properties: BTreeMap::new(),
            })?;
            if quiet {
                println!("{}", res.cid);
            } else {
                println!("cid={}", res.cid);
                println!("type={}", res.object_type);
            }
        }
        CaptureCommands::Annotation {
            building_id,
            text,
            x,
            y,
            z,
            quiet,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let mut repo = BuildingRepository::open(&cli.store, &bid)?;
            let res = repo.capture_annotation(&AnnotationCapture::new(
                text,
                Pose {
                    position: [x, y, z],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
            ))?;
            if quiet {
                println!("{}", res.cid);
            } else {
                println!("cid={}", res.cid);
                println!("type={}", res.object_type);
            }
        }
        CaptureCommands::PointCloud {
            building_id,
            file,
            x,
            y,
            z,
            quiet,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let mut repo = BuildingRepository::open(&cli.store, &bid)?;
            let pose = Pose {
                position: [x, y, z],
                orientation: [0.0, 0.0, 0.0, 1.0],
            };
            let capture = if let Some(path) = file {
                let bytes = fs::read(&path).with_context(|| format!("read {}", path.display()))?;
                let mut properties = BTreeMap::new();
                properties.insert("format".into(), "xyz_f32_le".into());
                properties.insert("source".into(), "file".into());
                PointCloudCapture {
                    pose,
                    bounds: None,
                    points_xyz_f32_le: bytes,
                    properties,
                }
            } else {
                // Synthetic 2×2 m room floor sample (for CI / no device).
                let mut pts = Vec::new();
                for i in 0..5 {
                    for j in 0..5 {
                        pts.push([i as f32 * 0.5, 0.0, j as f32 * 0.5]);
                    }
                }
                PointCloudCapture::from_xyz(&pts, pose, None)
            };
            let point_count = capture.point_count();
            let res = repo.capture_point_cloud(&capture)?;
            if quiet {
                println!("{}", res.cid);
            } else {
                println!("cid={}", res.cid);
                println!("type={}", res.object_type);
                println!("points={point_count}");
            }
        }
        CaptureCommands::Simulate {
            building_id,
            name,
            text,
            dx,
            dz,
            sigma_mm,
            commit,
            message,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let mut repo = BuildingRepository::open(&cli.store, &bid)?;
            let geom = arxos_core::hall_four_walls([dx, 0.0, dz], sigma_mm);
            let created = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_secs())
                .unwrap_or(0);
            let mut mapped = arxos_core::map_roomplan(&geom, created)?;
            mapped.set_sigma_mm(sigma_mm);
            if let arxos_core::object::ObjectBody::Space(ref mut s) = mapped.space.body {
                s.name = Some(name);
            }
            let staged = repo.ingest_mapped_roomplan(mapped)?;
            println!("space={}", staged.space);
            println!("surfaces={}", staged.surfaces.len());
            let ann = repo.capture_annotation(&AnnotationCapture::new(
                text,
                Pose {
                    position: [1.2, 1.4, 1.1],
                    orientation: [0.0, 0.0, 0.0, 1.0],
                },
            ))?;
            println!("annotation={}", ann.cid);
            if commit {
                let res = repo.commit(message.or_else(|| Some("simulate facts".into())))?;
                println!("root_cid={}", res.root_cid);
                println!("object_count={}", res.object_count);
            } else {
                println!(
                    "pending={} (use building commit to finish)",
                    repo.record().pending.len()
                );
            }
        }
    }
    Ok(())
}

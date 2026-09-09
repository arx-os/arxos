//! Spatial index commands.

use std::str::FromStr;

use anyhow::Result;
use arxos_core::object::BuildingId;
use arxos_core::repository::BuildingRepository;
use arxos_core::spatial::QueryVolume;
use arxos_core::Cid;

use crate::args::{Cli, SpatialCommands};

pub fn run(cli: &Cli, command: SpatialCommands) -> Result<()> {
    match command {
        SpatialCommands::Build {
            building_id,
            commit,
            message,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let mut repo = BuildingRepository::open(&cli.store, &bid)?;
            if commit {
                // No pending changes required — recommit head set with fresh index.
                // Stage nothing; commit rebuilds index from head+pending.
                let res = repo.commit_with_options(
                    message.or_else(|| Some("rebuild spatial index".into())),
                    true,
                )?;
                println!("root_cid={}", res.root_cid);
                println!("object_count={}", res.object_count);
                if let Some(root) = repo.load_head_root()? {
                    println!(
                        "spatial_index_root={}",
                        root.spatial_index_root
                            .map(|c| c.to_string())
                            .unwrap_or_else(|| "none".into())
                    );
                }
            } else {
                let idx = repo.rebuild_spatial_index()?;
                println!(
                    "spatial_index_root={}",
                    idx.map(|c| c.to_string()).unwrap_or_else(|| "none".into())
                );
                println!("(use --commit to attach index to a new root)");
            }
        }
        SpatialCommands::Query {
            building_id,
            min_x,
            min_y,
            min_z,
            max_x,
            max_y,
            max_z,
            json,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let repo = BuildingRepository::open_read(&cli.store, &bid)?;
            let volume = QueryVolume::from_min_max([min_x, min_y, min_z], [max_x, max_y, max_z]);
            let hits = repo.query_volume(&volume)?;
            if json {
                let v: Vec<_> = hits
                    .iter()
                    .map(|h| {
                        serde_json::json!({
                            "cid": h.object.to_string(),
                            "bounds": h.bounds.as_ref().map(|b| {
                                serde_json::json!({"min": b.min, "max": b.max})
                            }),
                        })
                    })
                    .collect();
                println!("{}", serde_json::to_string_pretty(&v)?);
            } else {
                println!("hits={}", hits.len());
                for h in hits {
                    println!("{}", h.object);
                }
            }
        }
        SpatialCommands::Load {
            building_id,
            min_x,
            min_y,
            min_z,
            max_x,
            max_y,
            max_z,
            limit,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let mut repo = BuildingRepository::open_read(&cli.store, &bid)?;
            let volume = QueryVolume::from_min_max([min_x, min_y, min_z], [max_x, max_y, max_z]);
            let n = repo.load_region(&volume, limit)?;
            println!("loaded={n}");
            println!("cache_len={}", repo.working_set().cache_len());
        }
        SpatialCommands::LoadFloor {
            building_id,
            floor_cid,
            limit,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let floor = Cid::from_str(&floor_cid)?;
            let mut repo = BuildingRepository::open_read(&cli.store, &bid)?;
            let n = repo.load_floor(&floor, limit)?;
            println!("loaded={n}");
            println!("cache_len={}", repo.working_set().cache_len());
        }
    }
    Ok(())
}

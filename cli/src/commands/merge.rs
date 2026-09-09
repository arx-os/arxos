//! Merge commands.

use std::str::FromStr;

use anyhow::Result;
use arxos_core::merge::plan_merge;
use arxos_core::object::BuildingId;
use arxos_core::repository::BuildingRepository;
use arxos_core::root::RootBody;
use arxos_core::store::ObjectStore;
use arxos_core::Cid;

use crate::args::{Cli, MergeCommands};

pub fn run(cli: &Cli, command: MergeCommands) -> Result<()> {
    match command {
        MergeCommands::Plan { root_a, root_b } => {
            let a = Cid::from_str(&root_a)?;
            let b = Cid::from_str(&root_b)?;
            let peek = ObjectStore::open(&cli.store)?;
            let obj = peek.get(&a)?;
            let bid = RootBody::from_object(&obj)?.building_id.clone();
            drop(peek);
            let repo = BuildingRepository::open_read(&cli.store, &bid)?;
            let plan = plan_merge(&repo, a, b)?;
            println!("building_id={}", plan.building_id);
            println!("union_size={}", plan.union_size);
            println!("would_dedupe={}", plan.would_dedupe);
        }
        MergeCommands::Apply {
            building_id,
            other_root,
            message,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let other = Cid::from_str(&other_root)?;
            let mut repo = BuildingRepository::open(&cli.store, &bid)?;
            let res = repo.merge_root(other, message)?;
            println!("root_cid={}", res.root_cid);
            println!("object_count={}", res.object_count);
            println!("deduped_annotations={}", res.deduped_annotations);
            println!(
                "spatial_index_root={}",
                res.spatial_index_root
                    .map(|c| c.to_string())
                    .unwrap_or_else(|| "none".into())
            );
            println!("parents={},{}", res.parents.0, res.parents.1);
        }
    }
    Ok(())
}

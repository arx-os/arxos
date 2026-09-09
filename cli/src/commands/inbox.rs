//! Contributor inbox commands (list / apply / reject).

use std::str::FromStr;

use anyhow::{bail, Result};
use arxos_core::object::BuildingId;
use arxos_core::repository::BuildingRepository;
use arxos_core::CtlRequest;

use crate::args::{Cli, InboxCommands};
use crate::ctl::{inbox_ctl, print_ctl_apply};

pub fn run(cli: &Cli, command: InboxCommands) -> Result<()> {
    match command {
        InboxCommands::List { building_id, json } => {
            let bid = BuildingId::from_str(&building_id)?;
            let repo = BuildingRepository::open_read(&cli.store, &bid)?;
            let file = repo.inbox_list()?;
            if json {
                println!("{}", serde_json::to_string_pretty(&file)?);
            } else {
                println!("building_id={bid}");
                println!(
                    "head_root={}",
                    repo.head_root()
                        .map(|c| c.to_string())
                        .unwrap_or_else(|| "none".into())
                );
                println!("pending={}", file.pending.len());
                for e in &file.pending {
                    println!(
                        "  {}  author={}  received={}",
                        e.cid, e.author_hex, e.received_unix
                    );
                }
            }
        }
        InboxCommands::Apply {
            building_id,
            cids,
            quiet,
            local,
            via,
        } => {
            let cid_list = cids.as_ref().map(|s| {
                s.split(',')
                    .map(|p| p.trim().to_string())
                    .filter(|p| !p.is_empty())
                    .collect::<Vec<_>>()
            });
            let reply = inbox_ctl(
                &cli.store,
                CtlRequest {
                    op: "inbox_apply".into(),
                    building_id: Some(building_id.clone()),
                    cids: cid_list,
                },
                local,
                via.as_deref(),
            )?;
            print_ctl_apply(&reply, quiet)?;
        }
        InboxCommands::Reject {
            building_id,
            cids,
            local,
            via,
        } => {
            let cid_list: Vec<String> = cids
                .split(',')
                .map(|p| p.trim().to_string())
                .filter(|p| !p.is_empty())
                .collect();
            let reply = inbox_ctl(
                &cli.store,
                CtlRequest {
                    op: "inbox_reject".into(),
                    building_id: Some(building_id),
                    cids: Some(cid_list),
                },
                local,
                via.as_deref(),
            )?;
            if !reply.ok {
                bail!("{}", reply.error.unwrap_or_else(|| "reject failed".into()));
            }
            println!("rejected={}", reply.rejected.unwrap_or(0));
        }
    }
    Ok(())
}

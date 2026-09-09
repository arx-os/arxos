//! CLI-side inbox control: Unix socket if serve holds the store, else in-process open.

use std::collections::BTreeSet;
use std::str::FromStr;

use anyhow::{bail, Context, Result};
use arxos_core::object::BuildingId;
use arxos_core::repository::BuildingRepository;
use arxos_core::{ctl_send, Cid, CtlRequest};

pub fn parse_cid_set(cids: Option<&str>) -> Result<Option<BTreeSet<Cid>>> {
    let Some(s) = cids else {
        return Ok(None);
    };
    let mut set = BTreeSet::new();
    for part in s.split(',') {
        let part = part.trim();
        if part.is_empty() {
            continue;
        }
        set.insert(Cid::from_str(part).with_context(|| format!("invalid cid: {part}"))?);
    }
    Ok(Some(set))
}

/// Prefer the serve control socket when it accepts; otherwise in-process open.
pub fn inbox_ctl(
    store: &std::path::Path,
    req: CtlRequest,
    local: bool,
    via: Option<&str>,
) -> Result<arxos_core::CtlReply> {
    let via_serve = via
        .map(|s| s.eq_ignore_ascii_case("serve"))
        .unwrap_or(false);
    if local && via_serve {
        bail!("--local and --via serve are mutually exclusive");
    }
    if via_serve {
        return ctl_send(store, &req).with_context(|| {
            format!(
                "serve control socket {} (is `net serve` running?)",
                arxos_core::serve_sock_path(store).display()
            )
        });
    }
    if !local && arxos_core::serve_ctl_path_exists(store) {
        match ctl_send(store, &req) {
            Ok(r) => return Ok(r),
            Err(_) => {
                // Stale sock: fall through to in-process open (serve is down).
            }
        }
    }
    let bid = req
        .building_id
        .as_deref()
        .ok_or_else(|| anyhow::anyhow!("building_id required"))?;
    let bid = BuildingId::from_str(bid)?;
    let mut repo = BuildingRepository::open(store, &bid).with_context(|| {
        format!(
            "open building {bid} (store may be locked by net serve; omit --local to use the control socket)"
        )
    })?;
    match req.op.as_str() {
        "inbox_apply" => {
            let joined = req.cids.as_ref().map(|v| v.join(","));
            let only = parse_cid_set(joined.as_deref())?;
            let res = repo.inbox_apply(only.as_ref())?;
            Ok(arxos_core::CtlReply {
                ok: true,
                error: None,
                root_cid: Some(res.commit.root_cid.to_string()),
                object_count: Some(res.commit.object_count),
                applied: Some(res.applied.len() as u64),
                pending: None,
                rejected: None,
                buildings: None,
            })
        }
        "inbox_reject" => {
            let joined = req.cids.as_ref().map(|v| v.join(","));
            let set = parse_cid_set(joined.as_deref())?
                .ok_or_else(|| anyhow::anyhow!("--cids is required"))?;
            let n = repo.inbox_reject(&set)?;
            Ok(arxos_core::CtlReply {
                ok: true,
                error: None,
                root_cid: None,
                object_count: None,
                applied: None,
                pending: None,
                rejected: Some(n),
                buildings: None,
            })
        }
        other => bail!("local path does not handle op {other}"),
    }
}

pub fn print_ctl_apply(reply: &arxos_core::CtlReply, quiet: bool) -> Result<()> {
    if !reply.ok {
        bail!(
            "{}",
            reply.error.clone().unwrap_or_else(|| "apply failed".into())
        );
    }
    if quiet {
        if let Some(c) = &reply.root_cid {
            println!("{c}");
        }
    } else {
        if let Some(c) = &reply.root_cid {
            println!("root_cid={c}");
        }
        if let Some(n) = reply.applied {
            println!("applied={n}");
        }
        if let Some(n) = reply.object_count {
            println!("object_count={n}");
        }
    }
    Ok(())
}

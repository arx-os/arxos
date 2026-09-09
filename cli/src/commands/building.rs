//! Building + entity + slice commands.

use std::collections::BTreeMap;
use std::str::FromStr;

use anyhow::{bail, Context, Result};
use arxos_core::object::{BuildingId, ObjectBody, Pose};
use arxos_core::repository::BuildingRepository;
use arxos_core::root::RootBody;
use arxos_core::store::ObjectStore;
use arxos_core::{BuildingLocator, EntityId, PublicKey};

use crate::args::{BuildingCommands, Cli, EntityCommands};

fn sigma_skip_count(repo: &BuildingRepository) -> u64 {
    let Some(head) = repo.head_root() else {
        return 0;
    };
    let Ok(root_obj) = repo.get_object(&head) else {
        return 0;
    };
    let Ok(root) = RootBody::from_object(&root_obj) else {
        return 0;
    };
    let Ok(state) = arxos_core::BuildingState::from_root(repo, root) else {
        return 0;
    };
    arxos_core::high_sigma_skip_count(&state)
}

fn sigma_skip_line(repo: &BuildingRepository) -> Option<String> {
    let n = sigma_skip_count(repo);
    if n == 0 {
        None
    } else {
        Some(format!(
            "realize_skipped_high_sigma={n} (sigma_mm > {} mm; facts remain in S)",
            arxos_core::SIGMA_EXCLUDE_MM
        ))
    }
}

pub fn run(cli: &Cli, command: BuildingCommands) -> Result<()> {
    match command {
        BuildingCommands::Init { name, quiet } => {
            let repo = BuildingRepository::init(&cli.store, name, None)
                .with_context(|| format!("init building in {}", cli.store.display()))?;
            if quiet {
                println!("{}", repo.building_id());
            } else {
                println!("building_id={}", repo.building_id());
                println!("name={}", repo.record().name.clone().unwrap_or_default());
                println!(
                    "head_root={}",
                    repo.head_root()
                        .map(|c| c.to_string())
                        .unwrap_or_else(|| "none".into())
                );
                println!(
                    "building_object={}",
                    repo.record()
                        .building_object
                        .map(|c| c.to_string())
                        .unwrap_or_else(|| "none".into())
                );
            }
        }
        BuildingCommands::Follow {
            building_id,
            uri,
            name,
            quiet,
        } => {
            let loc = uri.as_deref().map(BuildingLocator::parse).transpose()?;
            let bid = if let Some(id) = building_id {
                BuildingId::from_str(&id)?
            } else if let Some(l) = &loc {
                l.building_id.clone()
            } else {
                bail!("building follow requires a building id or --uri");
            };
            let repo = BuildingRepository::open_or_follow(&cli.store, &bid, name)
                .with_context(|| format!("follow building {bid}"))?;
            if quiet {
                println!("{}", repo.building_id());
            } else {
                println!("building_id={}", repo.building_id());
                println!(
                    "head_root={}",
                    repo.head_root()
                        .map(|c| c.to_string())
                        .unwrap_or_else(|| "none".into())
                );
                println!("note=scratch follow; push Facts with net push --staged; does not own official history");
                if let Some(l) = &loc {
                    if !l.controllers.is_empty() {
                        println!("pinned_controllers={}", l.controllers.len());
                        for k in &l.controllers {
                            println!("  {k}");
                        }
                    }
                    if let Some(t) = &l.inbox {
                        println!("inbox_ticket_len={}", t.len());
                    }
                }
            }
        }
        BuildingCommands::Show { building_id, json } => {
            let bid = BuildingId::from_str(&building_id)?;
            let repo = BuildingRepository::open_read(&cli.store, &bid)?;
            let r = repo.record();
            if json {
                println!(
                    "{}",
                    serde_json::to_string_pretty(&serde_json::json!({
                        "building_id": r.building_id.to_string(),
                        "name": r.name,
                        "head_root": r.head_root.map(|c| c.to_string()),
                        "building_object": r.building_object.map(|c| c.to_string()),
                        "pending": r.pending.iter().map(|c| c.to_string()).collect::<Vec<_>>(),
                        "pending_count": r.pending.len(),
                        "updated": r.updated,
                    }))?
                );
            } else {
                println!("building_id={}", r.building_id);
                println!("name={:?}", r.name);
                println!(
                    "head_root={}",
                    r.head_root
                        .map(|c| c.to_string())
                        .unwrap_or_else(|| "none".into())
                );
                println!("pending={}", r.pending.len());
                for c in &r.pending {
                    println!("  pending {c}");
                }
                if let Ok(keys) = repo.controller_keys() {
                    println!("controllers={}", keys.len());
                    for k in keys {
                        println!("  controller {k}");
                    }
                }
                if let Some(root) = repo.load_head_root()? {
                    println!("head_objects={}", repo.head_object_cids()?.len());
                    println!("head_message={:?}", root.message);
                }
            }
        }
        BuildingCommands::List { json } => {
            let list = BuildingRepository::list_buildings(&cli.store)?;
            if json {
                let v: Vec<_> = list
                    .iter()
                    .map(|r| {
                        serde_json::json!({
                            "building_id": r.building_id.to_string(),
                            "name": r.name,
                            "head_root": r.head_root.map(|c| c.to_string()),
                            "pending_count": r.pending.len(),
                        })
                    })
                    .collect();
                println!("{}", serde_json::to_string_pretty(&v)?);
            } else {
                for r in list {
                    println!(
                        "{}  name={:?}  head={}  pending={}",
                        r.building_id,
                        r.name,
                        r.head_root
                            .map(|c| c.to_string())
                            .unwrap_or_else(|| "-".into()),
                        r.pending.len()
                    );
                }
            }
        }
        BuildingCommands::Commit {
            building_id,
            message,
            quiet,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let mut repo = BuildingRepository::open(&cli.store, &bid)?;
            let res = repo.commit(message)?;
            if quiet {
                println!("{}", res.root_cid);
            } else {
                println!("root_cid={}", res.root_cid);
                println!("building_id={}", res.building_id);
                println!("object_count={}", res.object_count);
                println!(
                    "previous_root={}",
                    res.previous_root
                        .map(|c| c.to_string())
                        .unwrap_or_else(|| "none".into())
                );
            }
        }
        BuildingCommands::Near {
            building_id,
            x,
            y,
            z,
            radius,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let mut repo = BuildingRepository::open_read(&cli.store, &bid)?;
            let origin = Pose {
                position: [x, y, z],
                orientation: [0.0, 0.0, 0.0, 1.0],
            };
            let hits = repo.annotations_near(&origin, radius)?;
            for h in hits {
                println!(
                    "{:.2}m  {}  pose=[{:.2},{:.2},{:.2}]  {}",
                    h.distance_m,
                    h.cid,
                    h.pose.position[0],
                    h.pose.position[1],
                    h.pose.position[2],
                    h.text
                );
            }
        }
        BuildingCommands::AddController {
            building_id,
            pubkey,
            no_commit,
            message,
            quiet,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let pk = PublicKey::from_str(&pubkey)
                .with_context(|| format!("invalid public key: {pubkey}"))?;
            let mut repo = BuildingRepository::open(&cli.store, &bid).with_context(|| {
                format!("open building {bid} (store may be locked by edge serve or another arx process)")
            })?;
            let res = repo.add_controller_key(pk).with_context(|| {
                "add_controller_key failed (caller must be a current controller)"
            })?;
            if !quiet {
                println!("building_object={}", res.cid);
                println!("controllers={}", repo.controller_keys()?.len());
            }
            if !no_commit {
                let commit = repo.commit(message.or_else(|| Some("add controller".into())))?;
                if quiet {
                    println!("{}", commit.root_cid);
                } else {
                    println!("root_cid={}", commit.root_cid);
                    println!("object_count={}", commit.object_count);
                }
            } else if quiet {
                println!("{}", res.cid);
            } else {
                println!("pending (use building commit to finish)");
            }
        }
        BuildingCommands::RemoveController {
            building_id,
            pubkey,
            no_commit,
            message,
            quiet,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let pk = PublicKey::from_str(&pubkey)
                .with_context(|| format!("invalid public key: {pubkey}"))?;
            let mut repo = BuildingRepository::open(&cli.store, &bid).with_context(|| {
                format!("open building {bid} (store may be locked by edge serve or another arx process)")
            })?;
            let res = repo.remove_controller_key(pk).with_context(|| {
                "remove_controller_key failed (unknown key, or would remove last controller)"
            })?;
            if !quiet {
                println!("building_object={}", res.cid);
                println!("controllers={}", repo.controller_keys()?.len());
            }
            if !no_commit {
                let commit = repo.commit(message.or_else(|| Some("remove controller".into())))?;
                if quiet {
                    println!("{}", commit.root_cid);
                } else {
                    println!("root_cid={}", commit.root_cid);
                    println!("object_count={}", commit.object_count);
                }
            } else if quiet {
                println!("{}", res.cid);
            } else {
                println!("pending (use building commit to finish)");
            }
        }
        BuildingCommands::Controllers { building_id, json } => {
            let bid = BuildingId::from_str(&building_id)?;
            let repo = BuildingRepository::open_read(&cli.store, &bid)
                .with_context(|| format!("open building {bid} for read"))?;
            let keys = repo.controller_keys()?;
            if json {
                let v: Vec<_> = keys.iter().map(|k| k.to_string()).collect();
                println!("{}", serde_json::to_string_pretty(&v)?);
            } else {
                println!("building_id={bid}");
                println!("controllers={}", keys.len());
                for k in keys {
                    println!("  {k}");
                }
            }
        }
        BuildingCommands::Status { building_id, json } => {
            let bid = BuildingId::from_str(&building_id)?;
            // Probe exclusive lock without holding a repository session.
            let lock_status = {
                let store = ObjectStore::open(&cli.store)?;
                match store.try_lock_exclusive() {
                    Ok(_g) => "available",
                    Err(_) => "held",
                }
            };
            let repo = BuildingRepository::open_read(&cli.store, &bid).with_context(|| {
                format!("open building {bid} for read (store_lock={lock_status})")
            })?;
            let r = repo.record();
            let controllers = repo.controller_keys().unwrap_or_default();
            let heads = repo.list_entity_heads().unwrap_or_default();
            let mut by_type: BTreeMap<String, u64> = BTreeMap::new();
            for (_, _, ty) in &heads {
                *by_type.entry(ty.to_string()).or_default() += 1;
            }
            let active_n = repo.head_object_cids().map(|c| c.len()).unwrap_or(0);
            let sock = arxos_core::serve_sock_path(&cli.store);
            let sock_up = sock.exists();
            let inbox_pending = arxos_core::load_inbox(&cli.store, &bid)
                .map(|f| f.pending.len())
                .unwrap_or(0);
            if json {
                println!(
                    "{}",
                    serde_json::to_string_pretty(&serde_json::json!({
                        "building_id": bid.to_string(),
                        "name": r.name,
                        "head_root": r.head_root.map(|c| c.to_string()),
                        "active_objects": active_n,
                        "pending": r.pending.len(),
                        "pending_removes": r.pending_removes.len(),
                        "controllers": controllers.len(),
                        "controller_keys": controllers.iter().map(|k| k.to_string()).collect::<Vec<_>>(),
                        "entities": heads.len(),
                        "entities_by_type": by_type,
                        "realize_skipped_high_sigma": sigma_skip_count(&repo),
                        "store_lock": lock_status,
                        "ctl_sock": sock.display().to_string(),
                        "ctl_sock_present": sock_up,
                        "inbox_pending": inbox_pending,
                    }))?
                );
            } else {
                println!("building_id={bid}");
                println!("name={:?}", r.name);
                println!(
                    "head_root={}",
                    r.head_root
                        .map(|c| c.to_string())
                        .unwrap_or_else(|| "none".into())
                );
                println!("active_objects={active_n}");
                println!("pending={}", r.pending.len());
                println!("pending_removes={}", r.pending_removes.len());
                println!("controllers={}", controllers.len());
                println!("entities={}", heads.len());
                for (ty, n) in by_type {
                    println!("  entities.{ty}={n}");
                }
                if let Some(skip) = sigma_skip_line(&repo) {
                    println!("{skip}");
                }
                println!("inbox_pending={inbox_pending}");
                println!("ctl_sock={}", sock.display());
                println!("ctl_sock_present={sock_up}");
                println!("store_lock={lock_status}");
            }
        }
        BuildingCommands::Slice {
            building_id,
            z,
            cell,
            width,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let repo = BuildingRepository::open_read(&cli.store, &bid)
                .with_context(|| format!("open building {bid} for read"))?;
            let head = repo
                .head_root()
                .ok_or_else(|| anyhow::anyhow!("building {bid} has no head root"))?;
            let root_obj = repo.get_object(&head)?;
            let root = RootBody::from_object(&root_obj)?;
            let state = arxos_core::BuildingState::from_root(&repo, root)?;
            let realization = arxos_core::realize(&state)?;
            let mut walls = 0u64;
            let mut openings = 0u64;
            let mut equipment = 0u64;
            for s in &realization.solids {
                match s.kind {
                    arxos_core::SolidKind::Wall | arxos_core::SolidKind::Slab => walls += 1,
                    arxos_core::SolidKind::Opening => openings += 1,
                    arxos_core::SolidKind::Equipment | arxos_core::SolidKind::Run => equipment += 1,
                }
            }
            eprintln!(
                "entities solids={} walls/slabs={walls} openings={openings} equipment={equipment} spaces={} notes={}",
                realization.solids.len(),
                realization.spaces.len(),
                realization.notes.len()
            );
            print!("{}", arxos_core::ascii_slice(&realization, z, cell, width));
        }
    }
    Ok(())
}

pub fn entity(cli: &Cli, command: EntityCommands) -> Result<()> {
    match command {
        EntityCommands::Remove {
            building_id,
            entity_id,
            no_commit,
            message,
            quiet,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let eid = EntityId::from_str(&entity_id)
                .with_context(|| format!("invalid entity id: {entity_id}"))?;
            let mut repo = BuildingRepository::open(&cli.store, &bid).with_context(|| {
                format!("open building {bid} (store may be locked by edge serve or another arx process)")
            })?;
            let n = repo.remove_entity(&eid).with_context(|| "remove_entity")?;
            if n == 0 {
                bail!("no active versions found for entity {eid} (unknown or already removed)");
            }
            if !quiet {
                println!("entity_id={eid}");
                println!("versions_staged_for_removal={n}");
            }
            if !no_commit {
                let commit =
                    repo.commit(message.or_else(|| Some(format!("remove entity {eid}"))))?;
                if quiet {
                    println!("{}", commit.root_cid);
                } else {
                    println!("root_cid={}", commit.root_cid);
                    println!("object_count={}", commit.object_count);
                }
            } else if quiet {
                println!("{n}");
            } else {
                println!("pending (use building commit to finish)");
            }
        }
        EntityCommands::List { building_id, json } => {
            let bid = BuildingId::from_str(&building_id)?;
            let repo = BuildingRepository::open_read(&cli.store, &bid)
                .with_context(|| format!("open building {bid} for read"))?;
            let heads = repo.list_entity_heads()?;
            if json {
                let mut v = Vec::new();
                for (eid, cid, ty) in &heads {
                    let obj = repo.get_object(cid)?;
                    v.push(serde_json::json!({
                        "entity_id": eid.to_string(),
                        "cid": cid.to_string(),
                        "type": ty.to_string(),
                        "extent": obj.extent(),
                        "sigma_mm": obj.sigma_mm(),
                        "support_count": obj.effective_support_count(),
                    }));
                }
                println!("{}", serde_json::to_string_pretty(&v)?);
            } else {
                println!("building_id={bid}");
                println!("entities={}", heads.len());
                if let Some(skip) = sigma_skip_line(&repo) {
                    println!("{skip}");
                }
                for (eid, cid, ty) in heads {
                    let obj = repo.get_object(&cid)?;
                    let mut extra = String::new();
                    if let Some(e) = obj.extent() {
                        extra.push_str(&format!("  extent=[{:.3},{:.3},{:.3}]", e[0], e[1], e[2]));
                    }
                    if let Some(s) = obj.sigma_mm() {
                        extra.push_str(&format!("  sigma_mm={s}"));
                    }
                    let n = obj.effective_support_count();
                    if n > 0 {
                        extra.push_str(&format!("  support={n}"));
                    }
                    println!("  {eid}  {ty}  {cid}{extra}");
                }
            }
        }
        EntityCommands::Show {
            building_id,
            entity_id,
            json,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let eid = EntityId::from_str(&entity_id)
                .with_context(|| format!("invalid entity id: {entity_id}"))?;
            let repo = BuildingRepository::open_read(&cli.store, &bid)
                .with_context(|| format!("open building {bid} for read"))?;
            let heads = repo.list_entity_heads()?;
            let Some((_, cid, ty)) = heads.into_iter().find(|(e, _, _)| e == &eid) else {
                bail!("entity {eid} not found in active set of building {bid}");
            };
            let obj = repo.get_object(&cid)?;
            let created = obj.header.created;
            let author = obj.header.author.map(|a| a.to_string());
            let (name, floor, pose, bounds, kind) = match &obj.body {
                ObjectBody::Space(b) => (
                    b.name.clone(),
                    b.floor.map(|c| c.to_string()),
                    b.pose.clone(),
                    b.bounds.clone(),
                    None,
                ),
                ObjectBody::Floor(b) => (
                    b.name.clone(),
                    None,
                    None,
                    None,
                    Some(format!("level={}", b.level_index)),
                ),
                ObjectBody::Equipment(b) => (
                    b.name.clone(),
                    None,
                    b.pose.clone(),
                    None,
                    b.equipment_kind.clone(),
                ),
                ObjectBody::Surface(b) => (
                    None,
                    None,
                    b.pose.clone(),
                    b.bounds.clone(),
                    b.surface_kind.clone(),
                ),
                ObjectBody::Sensor(b) => (
                    b.name.clone(),
                    None,
                    b.pose.clone(),
                    None,
                    b.sensor_kind.clone(),
                ),
                ObjectBody::Fixture(b) => (
                    b.name.clone(),
                    None,
                    b.pose.clone(),
                    None,
                    b.fixture_kind.clone(),
                ),
                ObjectBody::Opening(b) => {
                    (None, None, b.pose.clone(), None, b.opening_kind.clone())
                }
                ObjectBody::System(b) => (b.name.clone(), None, None, None, b.system_kind.clone()),
                ObjectBody::Circuit(b) => (b.name.clone(), None, None, None, None),
                _ => (None, None, None, None, None),
            };
            if json {
                println!(
                    "{}",
                    serde_json::to_string_pretty(&serde_json::json!({
                        "entity_id": eid.to_string(),
                        "cid": cid.to_string(),
                        "type": ty.to_string(),
                        "created": created,
                        "author": author,
                        "name": name,
                        "floor": floor,
                        "kind": kind,
                        "pose": pose.as_ref().map(|p| serde_json::json!({
                            "position": p.position,
                            "orientation": p.orientation,
                        })),
                        "bounds": bounds.as_ref().map(|b| serde_json::json!({
                            "min": b.min,
                            "max": b.max,
                        })),
                        "extent": obj.extent(),
                        "sigma_mm": obj.sigma_mm(),
                        "support_count": obj.effective_support_count(),
                    }))?
                );
            } else {
                println!("entity_id={eid}");
                println!("cid={cid}");
                println!("type={ty}");
                println!("created={created}");
                if let Some(a) = author {
                    println!("author={a}");
                }
                if let Some(n) = name {
                    println!("name={n}");
                }
                if let Some(k) = kind {
                    println!("kind={k}");
                }
                if let Some(f) = floor {
                    println!("floor={f}");
                }
                if let Some(p) = pose {
                    println!(
                        "pose=[{:.3},{:.3},{:.3}]",
                        p.position[0], p.position[1], p.position[2]
                    );
                }
                if let Some(b) = bounds {
                    println!(
                        "bounds min=[{:.3},{:.3},{:.3}] max=[{:.3},{:.3},{:.3}]",
                        b.min[0], b.min[1], b.min[2], b.max[0], b.max[1], b.max[2]
                    );
                }
                if let Some(e) = obj.extent() {
                    println!("extent=[{:.3},{:.3},{:.3}]", e[0], e[1], e[2]);
                }
                if let Some(s) = obj.sigma_mm() {
                    println!("sigma_mm={s}");
                }
                println!("support_count={}", obj.effective_support_count());
            }
        }
    }
    Ok(())
}

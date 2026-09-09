//! Command dispatch for the `arx` CLI.

use std::collections::BTreeMap;
use std::collections::BTreeSet;
use std::fs;
use std::str::FromStr;
use std::time::Duration;

use anyhow::{bail, Context, Result};
use arxos_core::attest::{AttestationStatement, AttestationVerifier, MockAttestationVerifier};
use arxos_core::capture::{AnnotationCapture, PointCloudCapture, SpaceCapture};
use arxos_core::merge::plan_merge;
use arxos_core::object::{
    AnnotationBody, BlobBody, BuildingBody, BuildingId, Object, ObjectBody, ObjectType, Pose,
};
use arxos_core::repository::BuildingRepository;
use arxos_core::root::{ClosureOptions, RootBody, RootBuilder, RootClosure};
use arxos_core::scoring::score_root;
use arxos_core::spatial::QueryVolume;
use arxos_core::store::ObjectStore;
use arxos_core::verify::verify_root_transition;
use arxos_core::{
    ctl_send, spawn_serve_ctl, wake_ctl, BuildingLocator, Cid, CtlRequest, EntityId, Keypair,
    PublicKey,
};
use arxos_ifc::{export_building_ifc, import_ifc, ExportOptions as IfcExportOptions};
use arxos_networking::sync::{building_ads_from_store, pull_root_with_options, push_facts};
use arxos_networking::{IrohNode, MdnsDiscovery, ObjectTransport};
use arxos_usd::{export_building_usda, import_usda, ExportOptions as UsdExportOptions};

use crate::args::{
    BuildingCommands, CaptureCommands, Cli, Commands, EntityCommands, ExportCommands,
    ImportCommands, InboxCommands, KeyCommands, MergeCommands, NetCommands, ObjectCommands,
    RootCommands, SpatialCommands,
};

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

fn parse_cid_set(cids: Option<&str>) -> Result<Option<BTreeSet<Cid>>> {
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
fn inbox_ctl(
    store: &std::path::Path,
    req: CtlRequest,
    local: bool,
    via: Option<&str>,
) -> Result<arxos_core::CtlReply> {
    let via_serve = via.map(|s| s.eq_ignore_ascii_case("serve")).unwrap_or(false);
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

fn print_ctl_apply(reply: &arxos_core::CtlReply, quiet: bool) -> Result<()> {
    if !reply.ok {
        bail!("{}", reply.error.clone().unwrap_or_else(|| "apply failed".into()));
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

pub async fn run_async(cli: Cli) -> Result<()> {
    match cli.command {
        Commands::Net { command } => match command {
            NetCommands::Status => {
                println!("{}", arxos_networking::status());
            }
            NetCommands::Serve {
                no_mdns,
                ticket_only,
            } => {
                // Exclusive single-writer lock for the serve process lifetime
                // (same discipline as arxos-edge). Refuse if another writer holds it.
                let store = ObjectStore::open(&cli.store)
                    .with_context(|| format!("open store at {}", cli.store.display()))?;
                let _write_lock = store.try_lock_exclusive().with_context(|| {
                    format!(
                        "acquire store write lock on {} (is arx / arxos-edge / another writer running?)",
                        cli.store.display()
                    )
                })?;

                // Flock first, then bind (replace stale sock).
                let (ctl_guard, ctl_stop, ctl_thread) =
                    spawn_serve_ctl(&cli.store).with_context(|| "bind serve control socket")?;
                println!(
                    "ctl_sock={}",
                    arxos_core::serve_sock_path(&cli.store).display()
                );
                if let Ok(st) = ctl_send(
                    &cli.store,
                    &CtlRequest {
                        op: "status".into(),
                        building_id: None,
                        cids: None,
                    },
                ) {
                    if let Some(bs) = &st.buildings {
                        for b in bs {
                            println!(
                                "inbox building={} pending={} head={}",
                                b.building_id,
                                b.pending,
                                b.head_root.as_deref().unwrap_or("none")
                            );
                        }
                    }
                }

                let node = std::sync::Arc::new(
                    IrohNode::bind(&cli.store)
                        .await
                        .with_context(|| format!("bind iroh on {}", cli.store.display()))?,
                );
                node.refresh_buildings().await?;
                let ticket = node.ticket().await?;
                println!("peer_id={}", node.peer_id());
                println!("ticket={ticket}");
                println!("store={}", cli.store.display());
                println!("store_lock=held");
                let ads = building_ads_from_store(&cli.store)?;
                for ad in &ads {
                    println!(
                        "advertise building={} root={} objects={}",
                        ad.building_id, ad.root_cid, ad.object_count
                    );
                }

                let mut mdns_handle = None;
                if !no_mdns {
                    match MdnsDiscovery::new() {
                        Ok(d) => {
                            let instance =
                                format!("arxos-{}", &node.peer_id()[..8.min(node.peer_id().len())]);
                            if let Err(e) =
                                d.announce(&instance, node.peer_id(), 11223, None, &ads)
                            {
                                eprintln!("warning: mDNS announce failed: {e}");
                            } else {
                                println!("mdns=advertising as {instance}");
                                mdns_handle = Some(d);
                            }
                        }
                        Err(e) => eprintln!("warning: mDNS unavailable: {e}"),
                    }
                }

                if ticket_only {
                    if let Some(d) = mdns_handle {
                        let _ = d.shutdown();
                    }
                    ctl_stop.store(true, std::sync::atomic::Ordering::Relaxed);
                    wake_ctl(&cli.store);
                    let _ = ctl_thread.join();
                    drop(ctl_guard);
                    node.close().await;
                    // _write_lock drops here
                    return Ok(());
                }

                println!("serving… (Ctrl-C to stop; store lock held)");
                let accept = {
                    let n = std::sync::Arc::clone(&node);
                    tokio::spawn(async move {
                        if let Err(e) = n.accept_loop().await {
                            eprintln!("accept loop ended: {e}");
                        }
                    })
                };
                // Wait until interrupted.
                tokio::signal::ctrl_c().await?;
                println!("shutting down…");
                accept.abort();
                if let Some(d) = mdns_handle {
                    let _ = d.shutdown();
                }
                ctl_stop.store(true, std::sync::atomic::Ordering::Relaxed);
                wake_ctl(&cli.store);
                let _ = ctl_thread.join();
                drop(ctl_guard);
                node.close().await;
                // _write_lock dropped → flock released
            }
            NetCommands::Push {
                peer,
                uri,
                building,
                staged,
                cids,
            } => {
                let loc = uri.as_deref().map(BuildingLocator::parse).transpose()?;
                let bid = if let Some(b) = building {
                    b
                } else if let Some(l) = &loc {
                    l.building_id.to_string()
                } else {
                    bail!("net push requires --building or --uri");
                };
                let ticket = if let Some(p) = peer {
                    p
                } else if let Some(l) = &loc {
                    l.inbox.clone().ok_or_else(|| {
                        anyhow::anyhow!("uri missing inbox= ticket; pass --peer")
                    })?
                } else {
                    bail!("--peer or --uri inbox= is required");
                };
                if ticket.starts_with("memory:") {
                    bail!("memory: peers are for in-process tests; pass an Iroh ticket from `net serve`");
                }
                let bid_parsed = BuildingId::from_str(&bid)?;
                let repo = BuildingRepository::open_read(&cli.store, &bid_parsed)
                    .with_context(|| {
                        format!("open building {bid} (scratch: `building follow {bid}` first)")
                    })?;
                let mut leaf: Vec<Cid> = Vec::new();
                if staged {
                    leaf.extend(repo.record().pending.iter().copied());
                }
                if let Some(set) = parse_cid_set(cids.as_deref())? {
                    leaf.extend(set);
                }
                if leaf.is_empty() {
                    bail!("nothing to push: pass --staged and/or --cids");
                }
                let mut objects: Vec<(String, Vec<u8>)> = Vec::new();
                let mut seen = BTreeSet::new();
                for cid in &leaf {
                    for dep in arxos_core::repository::referenced_cids(&repo.get_object(cid)?) {
                        if seen.insert(dep) {
                            if let Ok(b) = repo.get_object_bytes(&dep) {
                                objects.push((dep.to_string(), b));
                            }
                        }
                    }
                    if seen.insert(*cid) {
                        objects.push((cid.to_string(), repo.get_object_bytes(cid)?));
                    }
                }
                let leaves: Vec<String> = leaf.iter().map(|c| c.to_string()).collect();
                let author = repo
                    .keypair()
                    .map(|k| k.public_key().to_string())
                    .unwrap_or_default();
                drop(repo);

                let node = IrohNode::bind(&cli.store)
                    .await
                    .with_context(|| format!("bind iroh on {}", cli.store.display()))?;
                let res = push_facts(
                    &node,
                    &ticket,
                    &bid,
                    &objects,
                    &leaves,
                    &author,
                )
                .await?;
                node.close().await;
                println!("building_id={}", res.building_id);
                println!("put_ok={} put_rejected={}", res.put_ok, res.put_rejected);
                println!("accepted={}", res.accepted.len());
                println!("duplicate={}", res.duplicate.len());
                println!("rejected={}", res.rejected.len());
                for r in &res.rejected {
                    println!("  reject {} {}", r.cid, r.reason);
                }
            }
            NetCommands::Fetch {
                peer,
                root,
                building_id,
                set_head,
                allow_untrusted,
                metadata_only,
                trust_controllers,
            } => {
                if metadata_only && set_head {
                    bail!("--metadata-only cannot adopt as head; pass --no-set-head");
                }
                let expected_controllers: Vec<arxos_core::PublicKey> = trust_controllers
                    .iter()
                    .map(|s| {
                        s.parse()
                            .map_err(|e: arxos_core::Error| anyhow::anyhow!("{e}"))
                    })
                    .collect::<anyhow::Result<Vec<_>>>()
                    .context("parse --trust-controllers")?;
                // Ephemeral client node (own store path for outbound).
                let node = IrohNode::bind(&cli.store)
                    .await
                    .context("bind client endpoint")?;
                let result = pull_root_with_options(
                    &node,
                    &peer,
                    &cli.store,
                    &root,
                    building_id.as_deref(),
                    set_head,
                    allow_untrusted,
                    metadata_only,
                    expected_controllers,
                )
                .await
                .context("pull root")?;
                println!("root_cid={}", result.root_cid);
                println!("objects_stored={}", result.objects_stored);
                println!("objects_skipped={}", result.objects_skipped_existing);
                if let Some(adopted) = result.adopted {
                    println!("adopted_head={}", adopted.root_cid);
                    println!("building_id={}", adopted.building_id);
                    println!("object_count={}", adopted.object_count);
                    if adopted.continuity == Some(arxos_core::ContinuityOutcome::FirstTrust)
                    {
                        println!(
                            "warning=first-contact TOFU; pin this replica with --trust-controllers"
                        );
                    }
                }
                node.close().await;
            }
            NetCommands::Publish { peer, building_id } => {
                let mut ads = building_ads_from_store(&cli.store)?;
                if let Some(bid) = &building_id {
                    ads.retain(|a| &a.building_id == bid);
                }
                if ads.is_empty() {
                    bail!("no building heads to publish");
                }
                for ad in &ads {
                    println!(
                        "building={} root={} objects={} name={:?}",
                        ad.building_id, ad.root_cid, ad.object_count, ad.name
                    );
                }
                if let Some(peer_ticket) = peer {
                    let node = IrohNode::bind(&cli.store).await?;
                    for ad in &ads {
                        node.announce_root(
                            &peer_ticket,
                            &ad.building_id,
                            &ad.root_cid,
                            ad.object_count,
                            None,
                        )
                        .await
                        .with_context(|| format!("announce {}", ad.building_id))?;
                        println!("announced {} -> peer", ad.building_id);
                    }
                    node.close().await;
                } else {
                    println!("(no --peer; printed local heads only. Run `net serve` to share.)");
                }
            }
            NetCommands::Peers { timeout, json } => {
                let discovery = MdnsDiscovery::new().context("start mDNS")?;
                discovery.start_browse().context("browse")?;
                println!("browsing mDNS for {timeout}s…");
                let peers = discovery.wait_for_peers(Duration::from_secs(timeout));
                if json {
                    let v: Vec<_> = peers
                        .iter()
                        .map(|p| {
                            serde_json::json!({
                                "instance": p.instance_name,
                                "peer_id": p.peer_id,
                                "ticket": p.ticket,
                                "port": p.port,
                                "buildings": p.buildings.iter().map(|b| {
                                    serde_json::json!({
                                        "building_id": b.building_id,
                                        "root_cid": b.root_cid,
                                        "name": b.name,
                                        "object_count": b.object_count,
                                    })
                                }).collect::<Vec<_>>(),
                            })
                        })
                        .collect();
                    println!("{}", serde_json::to_string_pretty(&v)?);
                } else if peers.is_empty() {
                    println!("(no peers discovered)");
                } else {
                    for p in peers {
                        println!(
                            "{}  peer={}  port={}  buildings={}",
                            p.instance_name,
                            p.peer_id,
                            p.port,
                            p.buildings.len()
                        );
                        for b in &p.buildings {
                            println!(
                                "    {}  root={}  objects={}",
                                b.building_id, b.root_cid, b.object_count
                            );
                        }
                    }
                }
                let _ = discovery.shutdown();
            }
        },
        _ => unreachable!("async_main only for Net"),
    }
    Ok(())
}

pub fn run_sync(cli: Cli) -> Result<()> {
    match cli.command {
        Commands::Version => {
            println!(
                "arx {} (core {})",
                env!("CARGO_PKG_VERSION"),
                arxos_core::version()
            );
            println!("{}", arxos_core::hello("CLI".into()));
        }
        Commands::Key { command } => match command {
            KeyCommands::Generate => {
                // Explicit seed export — this command exists to print secret material.
                let kp = Keypair::generate();
                let seed = kp.seed();
                eprintln!("note: seed is secret key material (explicit export)");
                println!("seed={}", hex::encode(seed.as_ref()));
                println!("public_key={}", kp.public_key());
            }
        },
        Commands::Building { command } => match command {
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
                    let commit =
                        repo.commit(message.or_else(|| Some("remove controller".into())))?;
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
                        arxos_core::SolidKind::Equipment | arxos_core::SolidKind::Run => {
                            equipment += 1
                        }
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
        },
        Commands::Entity { command } => match command {
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
                            extra.push_str(&format!(
                                "  extent=[{:.3},{:.3},{:.3}]",
                                e[0], e[1], e[2]
                            ));
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
                    ObjectBody::System(b) => {
                        (b.name.clone(), None, None, None, b.system_kind.clone())
                    }
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
                        println!(
                            "extent=[{:.3},{:.3},{:.3}]",
                            e[0], e[1], e[2]
                        );
                    }
                    if let Some(s) = obj.sigma_mm() {
                        println!("sigma_mm={s}");
                    }
                    println!("support_count={}", obj.effective_support_count());
                }
            }
        },
        Commands::Inbox { command } => match command {
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
        },
        Commands::Capture { command } => match command {
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
                    let bytes =
                        fs::read(&path).with_context(|| format!("read {}", path.display()))?;
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
        },
        Commands::Object { command } => {
            let store = ObjectStore::open(&cli.store)
                .with_context(|| format!("open store at {}", cli.store.display()))?;
            match command {
                ObjectCommands::Put {
                    r#type,
                    file,
                    text,
                    name,
                    building_id,
                    content_type,
                    sign_seed,
                    quiet,
                } => {
                    let type_str = r#type;
                    let obj_type = ObjectType::from_str(&type_str)
                        .or_else(|_| {
                            // allow "point-cloud-chunk" style
                            ObjectType::from_str(&type_str.replace('-', "_"))
                        })
                        .with_context(|| format!("unknown type: {type_str}"))?;

                    let body = match obj_type {
                        ObjectType::Blob => {
                            let data = if let Some(path) = file {
                                fs::read(&path)
                                    .with_context(|| format!("read {}", path.display()))?
                            } else if let Some(t) = text {
                                t.into_bytes()
                            } else {
                                bail!("blob put requires --file or --text");
                            };
                            ObjectBody::Blob(BlobBody {
                                content_type,
                                data,
                                properties: BTreeMap::new(),
                            })
                        }
                        ObjectType::Annotation => {
                            let t = text.or(file.and_then(|p| fs::read_to_string(p).ok()));
                            ObjectBody::Annotation(AnnotationBody {
                                text: t,
                                transcript: None,
                                media_ref: None,
                                pose: Some(Pose::default()),
                                space: None,
                                properties: BTreeMap::new(),
                            })
                        }
                        ObjectType::Building => {
                            let bid = match &building_id {
                                Some(s) => BuildingId::from_str(s)?,
                                None => BuildingId::new(),
                            };
                            let controllers = if let Some(seed) = &sign_seed {
                                vec![crate::util::keypair_from_seed_hex(seed)?.public_key()]
                            } else {
                                Vec::new()
                            };
                            ObjectBody::Building(BuildingBody {
                                building_id: bid,
                                name,
                                controller_keys: controllers,
                                properties: BTreeMap::new(),
                            })
                        }
                        other => bail!(
                            "CLI put for type '{other}' not implemented in Phase 0; use blob, annotation, or building"
                        ),
                    };

                    let mut obj = Object::new_with_created(body, crate::util::now_secs());
                    if let Some(seed) = sign_seed {
                        let kp = crate::util::keypair_from_seed_hex(&seed)?;
                        obj.sign(&kp)?;
                    }
                    let repo_bid = match &obj.body {
                        ObjectBody::Building(b) => Some(b.building_id.clone()),
                        _ => building_id
                            .as_ref()
                            .map(|s| BuildingId::from_str(s))
                            .transpose()?,
                    };
                    let cid = if let Some(bid) = repo_bid {
                        let repo = BuildingRepository::open_or_follow(&cli.store, &bid, None)
                            .with_context(|| {
                                format!(
                                    "open building {bid} for object put (store may be locked by another process)"
                                )
                            })?;
                        repo.put_object(&obj)?
                    } else {
                        // Debug-only CAS put: no building to attach. Prefer
                        // `arx capture` / `building commit` for domain writes.
                        let _write_lock = store.try_lock_exclusive().with_context(|| {
                            format!(
                                "acquire store write lock on {} (is arx / arxos-edge / another writer running?)",
                                cli.store.display()
                            )
                        })?;
                        store.put(&obj)?
                    };
                    if quiet {
                        println!("{cid}");
                    } else {
                        println!("cid={cid}");
                        println!("type={}", obj.header.object_type);
                        println!("schema_version={}", obj.header.schema_version);
                        if let Some(author) = &obj.header.author {
                            println!("author={author}");
                        }
                    }
                }
                ObjectCommands::Get { cid, out, json } => {
                    let cid = Cid::from_str(&cid)?;
                    let obj = store.get(&cid)?;
                    if let Some(ref path) = out {
                        let bytes = obj.to_canonical_bytes()?;
                        fs::write(path, &bytes)?;
                        if !json {
                            println!("wrote {} bytes to {}", bytes.len(), path.display());
                        }
                    }
                    if json {
                        // Structured summary (not full binary dump)
                        let summary = crate::util::object_summary(&obj, &cid);
                        println!("{}", serde_json::to_string_pretty(&summary)?);
                    } else if out.is_none() {
                        crate::util::print_object(&obj, &cid);
                    }
                }
                ObjectCommands::List => {
                    for cid in store.list_cids()? {
                        let entry = store.index_get(&cid)?;
                        match entry {
                            Some(e) => println!("{cid}  {}  {}B", e.object_type, e.size),
                            None => println!("{cid}"),
                        }
                    }
                }
            }
        }
        Commands::Root { command } => {
            let store = ObjectStore::open(&cli.store)
                .with_context(|| format!("open store at {}", cli.store.display()))?;
            match command {
                RootCommands::Create {
                    building_id,
                    objects,
                    all,
                    previous,
                    message,
                    seed,
                    quiet,
                } => {
                    let kp = crate::util::keypair_from_seed_hex(&seed)?;
                    let bid = BuildingId::from_str(&building_id)?;
                    let mut set = BTreeSet::new();
                    if all {
                        for cid in store.list_cids()? {
                            // Skip existing roots when committing "all" unless explicitly listed
                            if let Ok(obj) = store.get(&cid) {
                                if obj.header.object_type == ObjectType::Root {
                                    continue;
                                }
                            }
                            set.insert(cid);
                        }
                    }
                    for s in objects {
                        set.insert(Cid::from_str(&s)?);
                    }
                    if set.is_empty() {
                        bail!("root must commit to at least one object (pass --object or --all)");
                    }

                    let mut builder =
                        RootBuilder::new(bid.clone(), crate::util::now_secs()).objects(set);
                    if let Some(prev) = previous {
                        builder = builder.previous_root(Cid::from_str(&prev)?);
                    }
                    if let Some(msg) = message {
                        builder = builder.message(msg);
                    }
                    let (root_obj, root_cid) = builder.build_signed(&kp)?;
                    // Fail closed: authors must be building controllers (same as commit/adopt).
                    {
                        let root = RootBody::from_object(&root_obj)?;
                        root.verify_with_store(&store).with_context(|| {
                            "root author authorization failed (seed must be in Building.controller_keys)"
                        })?;
                    }
                    // Debug/interop helper: writes the root through the repository
                    // lock but does **not** advance the building head. Use
                    // `arx building commit` for domain commits.
                    let repo = BuildingRepository::open_or_follow(&cli.store, &bid, None)
                        .with_context(|| {
                            format!(
                                "open building {bid} for root create (store may be locked by another process)"
                            )
                        })?;
                    repo.put_object(&root_obj)?;
                    let root = RootBody::from_object(&root_obj)?;
                    if quiet {
                        println!("{root_cid}");
                    } else {
                        println!("root_cid={root_cid}");
                        println!("building_id={bid}");
                        let active = root.materialize_active_objects(&store)?;
                        println!("objects={}", active.len());
                        println!("authors={}", root.authors.len());
                        if let Some(msg) = &root.message {
                            println!("message={msg}");
                        }
                    }
                }
                RootCommands::Show { cid, json } => {
                    let cid = Cid::from_str(&cid)?;
                    let obj = store.get(&cid)?;
                    let root = RootBody::from_object(&obj).context("object is not a root")?;
                    if let Err(e) = root.verify_with_store(&store) {
                        eprintln!("warning: root verification failed: {e}");
                    }
                    if json {
                        let summary = crate::util::root_summary(root, &cid);
                        println!("{}", serde_json::to_string_pretty(&summary)?);
                    } else {
                        println!("root_cid={cid}");
                        println!("building_id={}", root.building_id);
                        println!(
                            "previous_root={}",
                            root.previous_root
                                .map(|c| c.to_string())
                                .unwrap_or_else(|| "none".into())
                        );
                        println!("timestamp={}", root.timestamp);
                        println!(
                            "spatial_index_root={}",
                            root.spatial_index_root
                                .map(|c| c.to_string())
                                .unwrap_or_else(|| "none".into())
                        );
                        println!(
                            "message={}",
                            root.message.clone().unwrap_or_else(|| "".into())
                        );
                        println!("authors={}", root.authors.len());
                        for (i, a) in root.authors.iter().enumerate() {
                            println!("  author[{i}]={}", a.public_key);
                        }
                        let active = root.materialize_active_objects(&store)?;
                        println!("objects={}", active.len());
                        for o in &active {
                            println!("  {o}");
                        }
                    }
                }
            }
        }
        Commands::Net { .. } => {
            bail!("net commands require async runtime (internal error)");
        }
        Commands::Spatial { command } => match command {
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
                let volume =
                    QueryVolume::from_min_max([min_x, min_y, min_z], [max_x, max_y, max_z]);
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
                let volume =
                    QueryVolume::from_min_max([min_x, min_y, min_z], [max_x, max_y, max_z]);
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
        },
        Commands::Merge { command } => match command {
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
        },
        Commands::Export { command } => match command {
            ExportCommands::Usd {
                building_id,
                out,
                no_points,
            } => {
                let bid = BuildingId::from_str(&building_id)?;
                let opts = UsdExportOptions {
                    include_point_clouds: !no_points,
                    ..UsdExportOptions::default()
                };
                let usda =
                    export_building_usda(&cli.store, &bid, &opts).with_context(|| "usd export")?;
                if let Some(path) = out {
                    fs::write(&path, &usda).with_context(|| format!("write {}", path.display()))?;
                    println!("wrote {} bytes to {}", usda.len(), path.display());
                } else {
                    print!("{usda}");
                }
            }
            ExportCommands::Ifc {
                building_id,
                out,
                project_name,
            } => {
                let bid = BuildingId::from_str(&building_id)?;
                let opts = IfcExportOptions { project_name };
                let ifc =
                    export_building_ifc(&cli.store, &bid, &opts).with_context(|| "ifc export")?;
                if let Some(path) = out {
                    fs::write(&path, &ifc).with_context(|| format!("write {}", path.display()))?;
                    println!("wrote {} bytes to {}", ifc.len(), path.display());
                } else {
                    print!("{ifc}");
                }
            }
        },
        Commands::Score {
            building_id,
            root,
            json,
        } => {
            // Diagnostic only: type-count points are not a payment basis (ADR-001).
            let bid = BuildingId::from_str(&building_id)?;
            let repo = BuildingRepository::open_read(&cli.store, &bid)?;
            let root_cid = match root {
                Some(s) => Cid::from_str(&s)?,
                None => repo
                    .head_root()
                    .ok_or_else(|| anyhow::anyhow!("building has no head root"))?,
            };
            let report = score_root(&repo, &root_cid, &Default::default())?;
            if json {
                println!("{}", serde_json::to_string_pretty(&report)?);
            } else {
                println!("building_id={}", report.building_id);
                println!("root_cid={:?}", report.root_cid);
                println!("policy_version={}", report.policy_version);
                println!("total_objects={}", report.total_objects);
                println!("total_score={:.4}", report.total_score);
                println!("note=diagnostic_only_not_payment_basis");
                for c in &report.contributors {
                    println!(
                        "  author={} score={:.4} objects={} signed_ok={} ann={} clouds={}",
                        c.author.as_deref().unwrap_or("anonymous"),
                        c.score,
                        c.objects,
                        c.signed_valid,
                        c.annotations,
                        c.point_cloud_chunks
                    );
                }
            }
        }
        Commands::Verify { root, json } => {
            let cid = Cid::from_str(&root)?;
            let store = ObjectStore::open(&cli.store)?;
            let closure = RootClosure::collect(&store, &cid, &ClosureOptions::default())?;
            let view = closure.as_read();
            let report = verify_root_transition(&view, &cid)?;
            if json {
                println!("{}", serde_json::to_string_pretty(&report)?);
            } else {
                println!("ok={}", report.ok);
                for f in &report.findings {
                    println!("  [{:?}] {} — {}", f.severity, f.code, f.message);
                }
                if !report.ok {
                    std::process::exit(1);
                }
            }
        }
        Commands::Attest {
            root,
            device_id,
            sign,
        } => {
            let store = ObjectStore::open(&cli.store)?;
            let root_cid = Cid::from_str(&root)?;
            // Ensure subject exists
            let _ = store.get(&root_cid)?;
            let stmt = AttestationStatement::mock(root_cid, &device_id);
            // Diagnostic only: mock is not a production trust path.
            let verdict = MockAttestationVerifier.verify(&stmt)?;
            if !verdict.valid {
                bail!("attestation invalid: {}", verdict.detail);
            }
            let kp = if sign {
                crate::util::load_device_keypair(&cli.store)
            } else {
                None
            };
            let obj = stmt.into_provenance_object(kp.as_ref())?;
            // Debug-only CAS put of a provenance object (not staged onto a building).
            let _write_lock = store.try_lock_exclusive().with_context(|| {
                format!(
                    "acquire store write lock on {} (is arx / arxos-edge / another writer running?)",
                    cli.store.display()
                )
            })?;
            let cid = store.put(&obj)?;
            println!("attest_cid={cid}");
            println!("subject={root}");
            println!("device_id={device_id}");
            println!("kind=mock");
            println!("note=diagnostic_only_not_device_authenticity");
            println!("detail={}", verdict.detail);
        }
        Commands::Import { command } => match command {
            ImportCommands::Usd { file, sign } => {
                if !sign {
                    bail!("unsigned import is not supported; omit --sign=false");
                }
                let text = fs::read_to_string(&file)
                    .with_context(|| format!("read {}", file.display()))?;
                let kp = crate::util::load_device_keypair(&cli.store).ok_or_else(|| {
                    anyhow::anyhow!("refusing unsigned import: missing keys/device.seed")
                })?;
                let res =
                    import_usda(&cli.store, &text, Some(&kp)).with_context(|| "usd import")?;
                println!("building_id={}", res.building_id);
                println!("objects={}", res.object_cids.len());
                println!(
                    "root_cid={}",
                    res.root_cid
                        .map(|c| c.to_string())
                        .unwrap_or_else(|| "none".into())
                );
                if let Some(s) = res.source_root_cid {
                    println!("source_root_cid={s}");
                }
            }
            ImportCommands::Ifc { file, sign } => {
                if !sign {
                    bail!("unsigned import is not supported; omit --sign=false");
                }
                let text = fs::read_to_string(&file)
                    .with_context(|| format!("read {}", file.display()))?;
                let kp = crate::util::load_device_keypair(&cli.store).ok_or_else(|| {
                    anyhow::anyhow!("refusing unsigned import: missing keys/device.seed")
                })?;
                let res =
                    import_ifc(&cli.store, &text, Some(&kp)).with_context(|| "ifc import")?;
                println!("building_id={}", res.building_id);
                println!("objects={}", res.object_cids.len());
                println!(
                    "root_cid={}",
                    res.root_cid
                        .map(|c| c.to_string())
                        .unwrap_or_else(|| "none".into())
                );
                if let Some(s) = res.source_root_cid {
                    println!("source_root_cid={s}");
                }
            }
        },
    }

    Ok(())
}

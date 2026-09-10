//! Networking commands (serve / push / fetch / publish / peers).

use std::collections::BTreeSet;
use std::str::FromStr;
use std::time::Duration;

use anyhow::{bail, Context, Result};
use arxos_core::object::BuildingId;
use arxos_core::repository::BuildingRepository;
use arxos_core::store::ObjectStore;
use arxos_core::{ctl_send, spawn_serve_ctl, wake_ctl, BuildingLocator, Cid, CtlRequest};
use arxos_networking::sync::{building_ads_from_store, pull_root_with_options, push_facts};
use arxos_networking::{IrohNode, MdnsDiscovery, ObjectTransport};

use crate::args::{Cli, NetCommands};
use crate::ctl::parse_cid_set;

pub async fn run(cli: &Cli, command: NetCommands) -> Result<()> {
    match command {
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
            match arxos_core::write_serve_ticket(&cli.store, &ticket) {
                Ok(p) => println!("ticket_file={}", p.display()),
                Err(e) => eprintln!("warning: could not write serve.ticket: {e}"),
            }
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
                        if let Err(e) = d.announce(&instance, node.peer_id(), 11223, None, &ads) {
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
                l.inbox
                    .clone()
                    .ok_or_else(|| anyhow::anyhow!("uri missing inbox= ticket; pass --peer"))?
            } else {
                bail!("--peer or --uri inbox= is required");
            };
            if ticket.starts_with("memory:") {
                bail!(
                    "memory: peers are for in-process tests; pass an Iroh ticket from `net serve`"
                );
            }
            let bid_parsed = BuildingId::from_str(&bid)?;
            let repo =
                BuildingRepository::open_read(&cli.store, &bid_parsed).with_context(|| {
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
            let push_res = push_facts(&node, &ticket, &bid, &objects, &leaves, &author).await;
            node.close().await;
            match push_res {
                Ok(res) => {
                    println!("building_id={}", res.building_id);
                    println!("put_ok={} put_rejected={}", res.put_ok, res.put_rejected);
                    println!("accepted={}", res.accepted.len());
                    println!("duplicate={}", res.duplicate.len());
                    println!("rejected={}", res.rejected.len());
                    for r in &res.rejected {
                        println!("  reject {} {}", r.cid, r.reason);
                    }
                    let incomplete = res.put_rejected > 0 || !res.rejected.is_empty();
                    if staged && !incomplete {
                        match BuildingRepository::open(&cli.store, &bid_parsed) {
                            Ok(mut w) => {
                                let n = w.clear_staged_after_push(&leaf)?;
                                println!("staging_cleared={n}");
                            }
                            Err(e) => {
                                eprintln!("warning: PushFactsOk but could not clear staging: {e}");
                            }
                        }
                    } else if staged {
                        let _ = arxos_core::save_push_retry(&cli.store, &bid_parsed, &leaf);
                        println!("staging=queued (retry with net push --staged)");
                    }
                }
                Err(e) => {
                    if staged {
                        let _ = arxos_core::save_push_retry(&cli.store, &bid_parsed, &leaf);
                    }
                    return Err(e.into());
                }
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
                if adopted.continuity == Some(arxos_core::ContinuityOutcome::FirstTrust) {
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
    }
    Ok(())
}

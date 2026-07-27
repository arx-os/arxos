//! Arxos CLI — Phase 0–2: objects, capture loop, multi-device sync.

use std::collections::BTreeMap;
use std::collections::BTreeSet;
use std::fs;
use std::path::PathBuf;
use std::str::FromStr;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use anyhow::{bail, Context, Result};
use arxos_core::capture::{AnnotationCapture, PointCloudCapture, SpaceCapture};
use arxos_core::merge::plan_merge;
use arxos_core::object::{
    AnnotationBody, BlobBody, BuildingBody, BuildingId, Object, ObjectBody, ObjectType, Pose,
};
use arxos_core::repository::BuildingRepository;
use arxos_core::root::{RootBody, RootBuilder};
use arxos_core::spatial::QueryVolume;
use arxos_core::store::ObjectStore;
use arxos_core::{Cid, Keypair};
use arxos_networking::sync::{building_ads_from_store, pull_root};
use arxos_networking::{IrohNode, MdnsDiscovery, ObjectTransport};
use clap::{Parser, Subcommand};

#[derive(Parser, Debug)]
#[command(name = "arxos", version, about = "Arxos content-addressed building repository tools")]
struct Cli {
    /// Path to the local object store directory.
    #[arg(long, global = true, default_value = ".arxos/store", env = "ARXOS_STORE")]
    store: PathBuf,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Object operations
    Object {
        #[command(subcommand)]
        command: ObjectCommands,
    },
    /// Root (repository state) operations
    Root {
        #[command(subcommand)]
        command: RootCommands,
    },
    /// Key management
    Key {
        #[command(subcommand)]
        command: KeyCommands,
    },
    /// Building repository (Phase 1)
    Building {
        #[command(subcommand)]
        command: BuildingCommands,
    },
    /// Capture into a building working set (Phase 1)
    Capture {
        #[command(subcommand)]
        command: CaptureCommands,
    },
    /// Multi-device networking (Phase 2)
    Net {
        #[command(subcommand)]
        command: NetCommands,
    },
    /// Spatial index & partial load (Phase 3)
    Spatial {
        #[command(subcommand)]
        command: SpatialCommands,
    },
    /// Merge concurrent roots (Phase 3)
    Merge {
        #[command(subcommand)]
        command: MergeCommands,
    },
    /// Print core version / hello
    Version,
}

#[derive(Subcommand, Debug)]
enum SpatialCommands {
    /// Rebuild spatial index for a building head (reports CID; commit to attach)
    Build {
        building_id: String,
        /// Create a new root that attaches the index
        #[arg(long)]
        commit: bool,
        #[arg(long)]
        message: Option<String>,
    },
    /// Query objects intersecting a volume
    Query {
        building_id: String,
        #[arg(long)]
        min_x: f64,
        #[arg(long)]
        min_y: f64,
        #[arg(long)]
        min_z: f64,
        #[arg(long)]
        max_x: f64,
        #[arg(long)]
        max_y: f64,
        #[arg(long)]
        max_z: f64,
        #[arg(long)]
        json: bool,
    },
    /// Partially materialize objects in a volume into the working set
    Load {
        building_id: String,
        #[arg(long)]
        min_x: f64,
        #[arg(long)]
        min_y: f64,
        #[arg(long)]
        min_z: f64,
        #[arg(long)]
        max_x: f64,
        #[arg(long)]
        max_y: f64,
        #[arg(long)]
        max_z: f64,
        /// Max objects to load (0 = unlimited)
        #[arg(long, default_value_t = 0)]
        limit: usize,
    },
    /// Load objects for a floor (by floor object CID)
    LoadFloor {
        building_id: String,
        floor_cid: String,
        #[arg(long, default_value_t = 0)]
        limit: usize,
    },
}

#[derive(Subcommand, Debug)]
enum MergeCommands {
    /// Dry-run merge plan for two root CIDs
    Plan {
        root_a: String,
        root_b: String,
    },
    /// Merge other_root into the building's current head
    Apply {
        building_id: String,
        other_root: String,
        #[arg(long)]
        message: Option<String>,
    },
}

#[derive(Subcommand, Debug)]
enum NetCommands {
    /// Serve the local CAS over Iroh QUIC (and optionally mDNS)
    Serve {
        /// Disable mDNS advertising (on by default)
        #[arg(long, default_value_t = false)]
        no_mdns: bool,
        /// Print ticket and exit accept-loop setup info only (for scripting)
        #[arg(long)]
        ticket_only: bool,
    },
    /// Fetch a root (+ objects) from a peer ticket and store locally
    Fetch {
        /// Peer dial ticket (JSON EndpointAddr from `net serve`)
        #[arg(long)]
        peer: String,
        /// Root CID to pull
        #[arg(long)]
        root: String,
        /// Building id (optional; inferred from root when omitted)
        #[arg(long)]
        building_id: Option<String>,
        /// Adopt pulled root as local head
        #[arg(long, default_value_t = true)]
        set_head: bool,
    },
    /// Refresh advertisements / print current building heads for publish
    Publish {
        /// Optional peer ticket to announce to (best-effort)
        #[arg(long)]
        peer: Option<String>,
        /// Building to announce (all if omitted)
        #[arg(long)]
        building_id: Option<String>,
    },
    /// Browse mDNS for local Arxos peers
    Peers {
        /// How long to wait for discoveries (seconds)
        #[arg(long, default_value_t = 3)]
        timeout: u64,
        #[arg(long)]
        json: bool,
    },
    /// Networking stack status
    Status,
}

#[derive(Subcommand, Debug)]
enum BuildingCommands {
    /// Create a new building repository (CAS + head + device key)
    Init {
        #[arg(long)]
        name: Option<String>,
        #[arg(long)]
        quiet: bool,
    },
    /// Open / show a building by ID
    Show {
        building_id: String,
        #[arg(long)]
        json: bool,
    },
    /// List buildings in the store
    List {
        #[arg(long)]
        json: bool,
    },
    /// Commit pending captures to a new signed root
    Commit {
        building_id: String,
        #[arg(long)]
        message: Option<String>,
        #[arg(long)]
        quiet: bool,
    },
    /// Query annotations near a pose
    Near {
        building_id: String,
        #[arg(long, default_value = "0")]
        x: f64,
        #[arg(long, default_value = "0")]
        y: f64,
        #[arg(long, default_value = "0")]
        z: f64,
        #[arg(long, default_value = "10")]
        radius: f64,
    },
}

#[derive(Subcommand, Debug)]
enum CaptureCommands {
    /// Capture a Space object at a pose
    Space {
        building_id: String,
        #[arg(long)]
        name: Option<String>,
        #[arg(long, default_value = "0")]
        x: f64,
        #[arg(long, default_value = "0")]
        y: f64,
        #[arg(long, default_value = "0")]
        z: f64,
        #[arg(long)]
        quiet: bool,
    },
    /// Capture a text Annotation at a pose
    Annotation {
        building_id: String,
        #[arg(long)]
        text: String,
        #[arg(long, default_value = "0")]
        x: f64,
        #[arg(long, default_value = "0")]
        y: f64,
        #[arg(long, default_value = "0")]
        z: f64,
        #[arg(long)]
        quiet: bool,
    },
    /// Capture a synthetic / file-based point cloud (xyz f32 LE)
    PointCloud {
        building_id: String,
        /// Path to raw xyz f32 LE bytes; if omitted, generates a small synthetic room sample
        #[arg(long)]
        file: Option<PathBuf>,
        #[arg(long, default_value = "0")]
        x: f64,
        #[arg(long, default_value = "0")]
        y: f64,
        #[arg(long, default_value = "0")]
        z: f64,
        #[arg(long)]
        quiet: bool,
    },
    /// Simulate a full RoomPlan-like capture: space + point cloud + annotation
    Simulate {
        building_id: String,
        #[arg(long, default_value = "Simulated Room")]
        name: String,
        #[arg(long, default_value = "simulated note")]
        text: String,
        #[arg(long)]
        commit: bool,
        #[arg(long)]
        message: Option<String>,
    },
}

#[derive(Subcommand, Debug)]
enum ObjectCommands {
    /// Write an object into the store
    Put {
        /// Object type (blob, annotation, building, …)
        #[arg(long, default_value = "blob")]
        r#type: String,

        /// Path to file payload (for blob) or text for annotation
        #[arg(long)]
        file: Option<PathBuf>,

        /// Inline text (annotation or blob utf-8)
        #[arg(long)]
        text: Option<String>,

        /// Building name (when type=building)
        #[arg(long)]
        name: Option<String>,

        /// Building id (when type=building); generated if omitted
        #[arg(long)]
        building_id: Option<String>,

        /// Optional content-type for blob
        #[arg(long)]
        content_type: Option<String>,

        /// Sign with seed hex (32-byte ed25519 seed)
        #[arg(long)]
        sign_seed: Option<String>,

        /// Print only the CID
        #[arg(long)]
        quiet: bool,
    },
    /// Read an object by CID
    Get {
        /// Object CID (b3:… or hex)
        cid: String,

        /// Write raw canonical CBOR to this path
        #[arg(long)]
        out: Option<PathBuf>,

        /// Print JSON summary
        #[arg(long)]
        json: bool,
    },
    /// List CIDs in the store
    List,
}

#[derive(Subcommand, Debug)]
enum RootCommands {
    /// Create a signed root committing to a set of object CIDs
    Create {
        /// Building ID
        #[arg(long)]
        building_id: String,

        /// Object CIDs to include (repeatable)
        #[arg(long = "object")]
        objects: Vec<String>,

        /// Include every object currently in the store
        #[arg(long)]
        all: bool,

        /// Previous root CID
        #[arg(long)]
        previous: Option<String>,

        /// Commit message
        #[arg(long)]
        message: Option<String>,

        /// ed25519 seed hex (32 bytes) used to sign the root
        #[arg(long)]
        seed: String,

        /// Print only the root CID
        #[arg(long)]
        quiet: bool,
    },
    /// Show a root by CID
    Show {
        /// Root object CID
        cid: String,

        /// JSON output
        #[arg(long)]
        json: bool,
    },
}

#[derive(Subcommand, Debug)]
enum KeyCommands {
    /// Generate a new ed25519 keypair (seed + public key)
    Generate,
}

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

fn keypair_from_seed_hex(seed_hex: &str) -> Result<Keypair> {
    let bytes = hex::decode(seed_hex).context("decode seed hex")?;
    if bytes.len() != 32 {
        bail!("seed must be 32 bytes (64 hex chars), got {}", bytes.len());
    }
    let mut seed = [0u8; 32];
    seed.copy_from_slice(&bytes);
    Ok(Keypair::from_seed(seed))
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    // Async net commands need a runtime.
    if matches!(cli.command, Commands::Net { .. }) {
        let rt = tokio::runtime::Runtime::new()?;
        return rt.block_on(async_main(cli));
    }

    sync_main(cli)
}

async fn async_main(cli: Cli) -> Result<()> {
    match cli.command {
        Commands::Net { command } => match command {
            NetCommands::Status => {
                println!("{}", arxos_networking::status());
            }
            NetCommands::Serve {
                no_mdns,
                ticket_only,
            } => {
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
                            let instance = format!(
                                "arxos-{}",
                                &node.peer_id()[..8.min(node.peer_id().len())]
                            );
                            if let Err(e) = d.announce(
                                &instance,
                                node.peer_id(),
                                11223,
                                Some(&ticket),
                                &ads,
                            ) {
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
                    node.close().await;
                    return Ok(());
                }

                println!("serving… (Ctrl-C to stop)");
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
                // Endpoint closes when Arc drops after abort.
            }
            NetCommands::Fetch {
                peer,
                root,
                building_id,
                set_head,
            } => {
                // Ephemeral client node (own store path for outbound).
                let node = IrohNode::bind(&cli.store)
                    .await
                    .context("bind client endpoint")?;
                let result = pull_root(
                    &node,
                    &peer,
                    &cli.store,
                    &root,
                    building_id.as_deref(),
                    set_head,
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
                }
                node.close().await;
            }
            NetCommands::Publish {
                peer,
                building_id,
            } => {
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

fn sync_main(cli: Cli) -> Result<()> {
    match cli.command {
        Commands::Version => {
            println!(
                "arxos {} (core {})",
                env!("CARGO_PKG_VERSION"),
                arxos_core::version()
            );
            println!("{}", arxos_core::hello("CLI".into()));
        }
        Commands::Key { command } => match command {
            KeyCommands::Generate => {
                let kp = Keypair::generate();
                println!("seed={}", hex::encode(kp.seed()));
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
                    println!(
                        "name={}",
                        repo.record().name.clone().unwrap_or_default()
                    );
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
            BuildingCommands::Show {
                building_id,
                json,
            } => {
                let bid = BuildingId::from_str(&building_id)?;
                let repo = BuildingRepository::open(&cli.store, &bid)?;
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
                    if let Some(root) = repo.load_head_root()? {
                        println!("head_objects={}", root.objects.len());
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
                let mut repo = BuildingRepository::open(&cli.store, &bid)?;
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
                    let bytes = fs::read(&path)
                        .with_context(|| format!("read {}", path.display()))?;
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
                commit,
                message,
            } => {
                let bid = BuildingId::from_str(&building_id)?;
                let mut repo = BuildingRepository::open(&cli.store, &bid)?;
                let space = repo.capture_space(&SpaceCapture {
                    name: Some(name),
                    pose: Pose {
                        position: [1.0, 0.0, 1.0],
                        orientation: [0.0, 0.0, 0.0, 1.0],
                    },
                    bounds: None,
                    floor: None,
                    properties: {
                        let mut p = BTreeMap::new();
                        p.insert("source".into(), "simulate".into());
                        p
                    },
                })?;
                println!("space={}", space.cid);
                let mut pts = Vec::new();
                for i in 0..8 {
                    for j in 0..8 {
                        pts.push([i as f32 * 0.25, 0.0, j as f32 * 0.25]);
                    }
                }
                let cloud = repo.capture_point_cloud(&PointCloudCapture::from_xyz(
                    &pts,
                    Pose::default(),
                    None,
                ))?;
                println!("point_cloud={} points={}", cloud.cid, 64);
                let ann = repo.capture_annotation(&AnnotationCapture::new(
                    text,
                    Pose {
                        position: [1.2, 1.4, 1.1],
                        orientation: [0.0, 0.0, 0.0, 1.0],
                    },
                ))?;
                println!("annotation={}", ann.cid);
                if commit {
                    let res = repo.commit(message.or_else(|| Some("simulate capture".into())))?;
                    println!("root_cid={}", res.root_cid);
                    println!("object_count={}", res.object_count);
                } else {
                    println!("pending={} (use building commit to finish)", repo.record().pending.len());
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
                            let bid = match building_id {
                                Some(s) => BuildingId::from_str(&s)?,
                                None => BuildingId::new(),
                            };
                            let controllers = if let Some(seed) = &sign_seed {
                                vec![keypair_from_seed_hex(seed)?.public_key()]
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

                    let mut obj = Object::new_with_created(body, now_secs());
                    if let Some(seed) = sign_seed {
                        let kp = keypair_from_seed_hex(&seed)?;
                        obj.sign(&kp)?;
                    }
                    let cid = store.put(&obj)?;
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
                        let summary = object_summary(&obj, &cid);
                        println!("{}", serde_json::to_string_pretty(&summary)?);
                    } else if out.is_none() {
                        print_object(&obj, &cid);
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
                    let kp = keypair_from_seed_hex(&seed)?;
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

                    let mut builder = RootBuilder::new(bid.clone(), now_secs()).objects(set);
                    if let Some(prev) = previous {
                        builder = builder.previous_root(Cid::from_str(&prev)?);
                    }
                    if let Some(msg) = message {
                        builder = builder.message(msg);
                    }
                    let (root_obj, root_cid) = builder.build_signed(&kp)?;
                    store.put(&root_obj)?;
                    let root = RootBody::from_object(&root_obj)?;
                    if quiet {
                        println!("{root_cid}");
                    } else {
                        println!("root_cid={root_cid}");
                        println!("building_id={bid}");
                        println!("objects={}", root.objects.len());
                        println!("authors={}", root.authors.len());
                        if let Some(msg) = &root.message {
                            println!("message={msg}");
                        }
                    }
                }
                RootCommands::Show { cid, json } => {
                    let cid = Cid::from_str(&cid)?;
                    let obj = store.get(&cid)?;
                    let root = RootBody::from_object(&obj)
                        .context("object is not a root")?;
                    if let Err(e) = root.verify_authors() {
                        eprintln!("warning: signature verify failed: {e}");
                    }
                    if json {
                        let summary = root_summary(root, &cid);
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
                        println!("objects={}", root.objects.len());
                        for o in &root.objects {
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
                        idx.map(|c| c.to_string())
                            .unwrap_or_else(|| "none".into())
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
                let repo = BuildingRepository::open(&cli.store, &bid)?;
                let volume = QueryVolume::from_min_max(
                    [min_x, min_y, min_z],
                    [max_x, max_y, max_z],
                );
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
                let mut repo = BuildingRepository::open(&cli.store, &bid)?;
                let volume = QueryVolume::from_min_max(
                    [min_x, min_y, min_z],
                    [max_x, max_y, max_z],
                );
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
                let mut repo = BuildingRepository::open(&cli.store, &bid)?;
                let n = repo.load_floor(&floor, limit)?;
                println!("loaded={n}");
                println!("cache_len={}", repo.working_set().cache_len());
            }
        },
        Commands::Merge { command } => match command {
            MergeCommands::Plan { root_a, root_b } => {
                let store = ObjectStore::open(&cli.store)?;
                let a = Cid::from_str(&root_a)?;
                let b = Cid::from_str(&root_b)?;
                let plan = plan_merge(&store, a, b)?;
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
    }

    Ok(())
}

fn print_object(obj: &Object, cid: &Cid) {
    println!("cid={cid}");
    println!("type={}", obj.header.object_type);
    println!("schema_version={}", obj.header.schema_version);
    println!("created={}", obj.header.created);
    if let Some(author) = &obj.header.author {
        println!("author={author}");
    }
    println!("signed={}", obj.header.signature.is_some());
    match &obj.body {
        ObjectBody::Blob(b) => {
            println!("content_type={:?}", b.content_type);
            println!("data_len={}", b.data.len());
        }
        ObjectBody::Annotation(a) => {
            println!("text={:?}", a.text);
            println!("pose={:?}", a.pose);
        }
        ObjectBody::Building(b) => {
            println!("building_id={}", b.building_id);
            println!("name={:?}", b.name);
            println!("controllers={}", b.controller_keys.len());
        }
        ObjectBody::Root(r) => {
            println!("building_id={}", r.building_id);
            println!("objects={}", r.objects.len());
        }
        other => {
            println!("body_type={}", other.object_type());
        }
    }
}

fn object_summary(obj: &Object, cid: &Cid) -> serde_json::Value {
    serde_json::json!({
        "cid": cid.to_string(),
        "type": obj.header.object_type.to_string(),
        "schema_version": obj.header.schema_version,
        "created": obj.header.created,
        "author": obj.header.author.map(|a| a.to_string()),
        "signed": obj.header.signature.is_some(),
    })
}

fn root_summary(root: &RootBody, cid: &Cid) -> serde_json::Value {
    serde_json::json!({
        "root_cid": cid.to_string(),
        "building_id": root.building_id.to_string(),
        "previous_root": root.previous_root.map(|c| c.to_string()),
        "timestamp": root.timestamp,
        "message": root.message,
        "spatial_index_root": root.spatial_index_root.map(|c| c.to_string()),
        "authors": root.authors.iter().map(|a| a.public_key.to_string()).collect::<Vec<_>>(),
        "objects": root.objects.iter().map(|c| c.to_string()).collect::<Vec<_>>(),
        "object_count": root.objects.len(),
    })
}

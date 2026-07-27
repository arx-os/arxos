//! Arxos CLI — Phase 0: object put, root create, root show.

use std::collections::BTreeMap;
use std::collections::BTreeSet;
use std::fs;
use std::path::PathBuf;
use std::str::FromStr;
use std::time::{SystemTime, UNIX_EPOCH};

use anyhow::{bail, Context, Result};
use arxos_core::object::{
    AnnotationBody, BlobBody, BuildingBody, BuildingId, Object, ObjectBody, ObjectType, Pose,
};
use arxos_core::root::{RootBody, RootBuilder};
use arxos_core::store::ObjectStore;
use arxos_core::{Cid, Keypair};
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
    /// Print core version / hello
    Version,
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

//! Debug / CAS / score / verify commands.

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::str::FromStr;

use anyhow::{bail, Context, Result};
use arxos_core::attest::{AttestationStatement, AttestationVerifier, MockAttestationVerifier};
use arxos_core::object::{
    AnnotationBody, BlobBody, BuildingBody, BuildingId, Object, ObjectBody, ObjectType, Pose,
};
use arxos_core::repository::BuildingRepository;
use arxos_core::root::{ClosureOptions, RootBody, RootBuilder, RootClosure};
use arxos_core::scoring::score_root;
use arxos_core::store::ObjectStore;
use arxos_core::verify::verify_root_transition;
use arxos_core::{Cid, Keypair};

use crate::args::{Cli, KeyCommands, ObjectCommands, RootCommands};

pub fn version() -> Result<()> {
    println!(
        "arx {} (core {})",
        env!("CARGO_PKG_VERSION"),
        arxos_core::version()
    );
    println!("{}", arxos_core::hello("CLI".into()));
    Ok(())
}

pub fn key(_cli: &Cli, command: KeyCommands) -> Result<()> {
    match command {
        KeyCommands::Generate => {
            // Explicit seed export — this command exists to print secret material.
            let kp = Keypair::generate();
            let seed = kp.seed();
            eprintln!("note: seed is secret key material (explicit export)");
            println!("seed={}", hex::encode(seed.as_ref()));
            println!("public_key={}", kp.public_key());
        }
    }
    Ok(())
}

pub fn object(cli: &Cli, command: ObjectCommands) -> Result<()> {
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
    Ok(())
}

pub fn root(cli: &Cli, command: RootCommands) -> Result<()> {
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

            let mut builder = RootBuilder::new(bid.clone(), crate::util::now_secs()).objects(set);
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
    Ok(())
}

pub fn score(cli: &Cli, building_id: String, root: Option<String>, json: bool) -> Result<()> {
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
    Ok(())
}

pub fn verify(cli: &Cli, root: String, json: bool) -> Result<()> {
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
    Ok(())
}

pub fn attest(cli: &Cli, root: String, device_id: String, sign: bool) -> Result<()> {
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
    Ok(())
}

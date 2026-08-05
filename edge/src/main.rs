//! Arxos edge node — local CAS admin, interop export, and long-running serve.

use std::fs;
use std::path::PathBuf;
use std::str::FromStr;
use std::sync::Arc;

use anyhow::{Context, Result};
use arxos_core::object::BuildingId;
use arxos_core::repository::BuildingRepository;
use arxos_core::store::ObjectStore;
use arxos_ifc::{export_building_ifc, ExportOptions as IfcOpts};
use arxos_usd::{export_building_usda, ExportOptions as UsdOpts};
use clap::{Parser, Subcommand};

#[derive(Parser, Debug)]
#[command(name = "arxos-edge", version, about = "Arxos edge node tools")]
struct Cli {
    #[arg(long, global = true, default_value = ".arxos/store", env = "ARXOS_STORE")]
    store: PathBuf,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Print versions
    Version,
    /// List buildings in the local store
    Buildings,
    /// Export building head as USDA
    ExportUsd {
        building_id: String,
        #[arg(long, short)]
        out: PathBuf,
    },
    /// Export building head as IFC4
    ExportIfc {
        building_id: String,
        #[arg(long, short)]
        out: PathBuf,
        #[arg(long)]
        project_name: Option<String>,
    },
    /// Run as long-lived edge node: exclusive store lock + Iroh serve (+ optional mDNS).
    ///
    /// Holds the store write lock for the process lifetime so CLI writers on the
    /// same path fail closed until this process exits. Survives clean restart
    /// with head metadata intact on disk.
    Serve {
        /// Advertise building heads on the LAN via mDNS.
        #[arg(long, default_value_t = true)]
        mdns: bool,
        /// Instance name for mDNS (default: hostname-derived).
        #[arg(long)]
        instance: Option<String>,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Version => {
            println!(
                "arxos-edge {} (core {} usd {} ifc {})",
                env!("CARGO_PKG_VERSION"),
                arxos_core::version(),
                arxos_usd::version(),
                arxos_ifc::version()
            );
            println!("{}", arxos_core::hello("edge".into()));
        }
        Commands::Buildings => {
            let list = BuildingRepository::list_buildings(&cli.store)?;
            for r in list {
                println!(
                    "{}  name={:?}  head={}",
                    r.building_id,
                    r.name,
                    r.head_root
                        .map(|c| c.to_string())
                        .unwrap_or_else(|| "-".into())
                );
            }
        }
        Commands::ExportUsd { building_id, out } => {
            let bid = BuildingId::from_str(&building_id)?;
            let usda = export_building_usda(&cli.store, &bid, &UsdOpts::default())
                .context("usd export")?;
            fs::write(&out, &usda).with_context(|| format!("write {}", out.display()))?;
            println!("wrote {} bytes to {}", usda.len(), out.display());
        }
        Commands::ExportIfc {
            building_id,
            out,
            project_name,
        } => {
            let bid = BuildingId::from_str(&building_id)?;
            let ifc = export_building_ifc(
                &cli.store,
                &bid,
                &IfcOpts { project_name },
            )
            .context("ifc export")?;
            fs::write(&out, &ifc).with_context(|| format!("write {}", out.display()))?;
            println!("wrote {} bytes to {}", ifc.len(), out.display());
        }
        Commands::Serve { mdns, instance } => {
            run_serve(cli.store, mdns, instance)?;
        }
    }
    Ok(())
}

fn run_serve(store_path: PathBuf, mdns: bool, instance: Option<String>) -> Result<()> {
    let rt = tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()
        .context("tokio runtime")?;
    rt.block_on(async move { serve_async(store_path, mdns, instance).await })
}

async fn serve_async(store_path: PathBuf, mdns: bool, instance: Option<String>) -> Result<()> {
    // Exclusive single-writer lock for the edge process lifetime.
    let store = ObjectStore::open(&store_path).context("open store")?;
    let _write_lock = store
        .try_lock_exclusive()
        .context("acquire store write lock (is another writer running?)")?;

    let node = Arc::new(
        arxos_networking::IrohNode::bind(&store_path)
            .await
            .context("iroh bind")?,
    );
    let ticket = node.ticket().await.context("ticket")?;
    let peer = node.peer_id().to_string();
    println!("arxos-edge serve");
    println!("  store={}", store_path.display());
    println!("  peer={peer}");
    println!("  ticket={ticket}");

    let ads = arxos_networking::building_ads_from_store(&store_path).unwrap_or_default();
    node.set_buildings(ads.clone()).await;
    for ad in &ads {
        println!(
            "  building={} root={} objects={}",
            ad.building_id, ad.root_cid, ad.object_count
        );
    }

    #[cfg(feature = "mdns-announce")]
    let _mdns_guard = if mdns {
        match announce_mdns(&peer, &ticket, &ads, instance.as_deref()) {
            Ok(g) => {
                println!("  mdns=on service={}", arxos_networking::SERVICE_TYPE);
                Some(g)
            }
            Err(e) => {
                eprintln!("  mdns=failed ({e}); continuing without discovery");
                None
            }
        }
    } else {
        println!("  mdns=off");
        None
    };

    #[cfg(not(feature = "mdns-announce"))]
    {
        let _ = (mdns, instance);
        println!("  mdns=disabled (build with mdns-announce feature)");
    }

    let accept = {
        let n = Arc::clone(&node);
        tokio::spawn(async move {
            if let Err(e) = n.accept_loop().await {
                eprintln!("accept loop ended: {e}");
            }
        })
    };

    println!("serving (Ctrl-C to stop); store lock held");
    tokio::signal::ctrl_c()
        .await
        .context("wait for ctrl-c")?;
    println!("shutting down…");
    accept.abort();
    node.close().await;
    // _write_lock dropped → flock released; heads remain on disk.
    Ok(())
}

#[cfg(feature = "mdns-announce")]
fn announce_mdns(
    peer_id: &str,
    ticket: &str,
    ads: &[arxos_networking::BuildingHeadAd],
    instance: Option<&str>,
) -> Result<arxos_networking::MdnsDiscovery> {
    let d = arxos_networking::MdnsDiscovery::new().map_err(|e| anyhow::anyhow!("{e}"))?;
    let name = instance
        .map(|s| s.to_string())
        .unwrap_or_else(|| format!("arxos-edge-{}", &peer_id[..8.min(peer_id.len())]));
    d.announce(&name, peer_id, 0, Some(ticket), ads)
        .map_err(|e| anyhow::anyhow!("{e}"))?;
    Ok(d)
}


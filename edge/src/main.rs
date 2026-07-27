//! Arxos edge node — local CAS admin + interop export for site deployments.
//!
//! Phase 5 will add packaging (Pi-class images) and optional net serve defaults.
//! Phase 4 adds export commands so edge boxes can hand off USD/IFC to CAD tools.

use std::fs;
use std::path::PathBuf;
use std::str::FromStr;

use anyhow::{Context, Result};
use arxos_core::object::BuildingId;
use arxos_core::repository::BuildingRepository;
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
    }
    Ok(())
}

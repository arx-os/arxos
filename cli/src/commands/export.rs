//! Export / import projections (USD, IFC).

use std::fs;
use std::str::FromStr;

use anyhow::{bail, Context, Result};
use arxos_core::object::BuildingId;
use arxos_ifc::{export_building_ifc, import_ifc, ExportOptions as IfcExportOptions};
use arxos_usd::{export_building_usda, import_usda, ExportOptions as UsdExportOptions};

use crate::args::{Cli, ExportCommands, ImportCommands};

pub fn export(cli: &Cli, command: ExportCommands) -> Result<()> {
    match command {
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
            let ifc = export_building_ifc(&cli.store, &bid, &opts).with_context(|| "ifc export")?;
            if let Some(path) = out {
                fs::write(&path, &ifc).with_context(|| format!("write {}", path.display()))?;
                println!("wrote {} bytes to {}", ifc.len(), path.display());
            } else {
                print!("{ifc}");
            }
        }
    }
    Ok(())
}

pub fn import(cli: &Cli, command: ImportCommands) -> Result<()> {
    match command {
        ImportCommands::Usd { file, sign } => {
            if !sign {
                bail!("unsigned import is not supported; omit --sign=false");
            }
            let text =
                fs::read_to_string(&file).with_context(|| format!("read {}", file.display()))?;
            let kp = crate::util::load_device_keypair(&cli.store).ok_or_else(|| {
                anyhow::anyhow!("refusing unsigned import: missing keys/device.seed")
            })?;
            let res = import_usda(&cli.store, &text, Some(&kp)).with_context(|| "usd import")?;
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
            let text =
                fs::read_to_string(&file).with_context(|| format!("read {}", file.display()))?;
            let kp = crate::util::load_device_keypair(&cli.store).ok_or_else(|| {
                anyhow::anyhow!("refusing unsigned import: missing keys/device.seed")
            })?;
            let res = import_ifc(&cli.store, &text, Some(&kp)).with_context(|| "ifc import")?;
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
    }
    Ok(())
}

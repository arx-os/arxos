//! Buyer-side data access: quote + optional $AXD payForAccess.

use super::Command;
use crate::access::build_access_request;
#[cfg(feature = "blockchain")]
use crate::access::{parse_nonce_hex, AccessRequest};
use crate::persistence::{load_building_at, BUILDING_YAML};
use std::error::Error;
use std::path::{Path, PathBuf};

pub struct AccessCommand {
    pub action: AccessAction,
}

pub enum AccessAction {
    /// Write an access request JSON (nonce + building id) for the buyer market.
    Quote {
        building_id: Option<String>,
        amount_axd: u64,
        output: PathBuf,
    },
    /// Pay on-chain via ArxPaymentRouter (requires --features blockchain).
    Pay {
        building_id: Option<String>,
        amount_axd: u64,
        nonce_hex: Option<String>,
        private_key: Option<String>,
        router: Option<String>,
        token: Option<String>,
        rpc_url: Option<String>,
        chain_id: u64,
        request_file: Option<PathBuf>,
    },
}

impl Command for AccessCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        match &self.action {
            AccessAction::Quote {
                building_id,
                amount_axd,
                output,
            } => execute_quote(building_id.as_deref(), *amount_axd, output),
            AccessAction::Pay {
                building_id,
                amount_axd,
                nonce_hex,
                private_key,
                router,
                token,
                rpc_url,
                chain_id,
                request_file,
            } => execute_pay(PayArgs {
                building_id: building_id.clone(),
                amount_axd: *amount_axd,
                nonce_hex: nonce_hex.clone(),
                private_key: private_key.clone(),
                router: router.clone(),
                token: token.clone(),
                rpc_url: rpc_url.clone(),
                chain_id: *chain_id,
                request_file: request_file.clone(),
            }),
        }
    }

    fn name(&self) -> &'static str {
        "access"
    }
}

fn resolve_building_id(explicit: Option<&str>) -> Result<(String, Option<String>), Box<dyn Error>> {
    if let Some(id) = explicit {
        return Ok((id.to_string(), None));
    }
    let building = load_building_at(Path::new("."))
        .map_err(|e| format!("load {} (or pass --building-id): {}", BUILDING_YAML, e))?;
    Ok((building.id.clone(), Some(building.name.clone())))
}

fn execute_quote(
    building_id: Option<&str>,
    amount_axd: u64,
    output: &Path,
) -> Result<(), Box<dyn Error>> {
    let (id, name) = resolve_building_id(building_id)?;
    let req = build_access_request(&id, name.as_deref(), amount_axd);
    println!("🛒 Data access request (buyer market)");
    println!("  {}", req.summary);
    println!("  building_id: {}", req.building_id);
    println!("  amount_axd:  {}", req.amount_axd);
    println!("  nonce:       {}", req.nonce_hex);
    let json = serde_json::to_string_pretty(&req)?;
    std::fs::write(output, json)?;
    println!("✅ Wrote {}", output.display());
    println!(
        "   Pay: arx access pay --request {} --features blockchain (or pass ids + --amount)",
        output.display()
    );
    Ok(())
}

#[cfg_attr(not(feature = "blockchain"), allow(dead_code))]
struct PayArgs {
    building_id: Option<String>,
    amount_axd: u64,
    nonce_hex: Option<String>,
    private_key: Option<String>,
    router: Option<String>,
    token: Option<String>,
    rpc_url: Option<String>,
    chain_id: u64,
    request_file: Option<PathBuf>,
}

#[cfg(feature = "blockchain")]
fn execute_pay(args: PayArgs) -> Result<(), Box<dyn Error>> {
    use crate::blockchain::{
        types::{ChainId, ContractAddresses, NetworkConfig},
        PaymentClient,
    };

    let (building_id, amount, nonce) = if let Some(path) = &args.request_file {
        let raw = std::fs::read_to_string(path)?;
        let req: AccessRequest = serde_json::from_str(&raw)?;
        let n = parse_nonce_hex(&req.nonce_hex).map_err(|e| e.to_string())?;
        (req.building_id, req.amount_axd, n)
    } else {
        let (id, _) = resolve_building_id(args.building_id.as_deref())?;
        let n = if let Some(h) = &args.nonce_hex {
            parse_nonce_hex(h).map_err(|e| e.to_string())?
        } else {
            let req = build_access_request(&id, None, args.amount_axd);
            parse_nonce_hex(&req.nonce_hex).map_err(|e| e.to_string())?
        };
        (id, args.amount_axd, n)
    };

    let key = resolve_key(args.private_key.as_deref())?;
    let router = args
        .router
        .or_else(|| std::env::var("ARX_PAYMENT_ROUTER").ok())
        .ok_or("pay requires --router or ARX_PAYMENT_ROUTER")?;
    let token = args
        .token
        .or_else(|| std::env::var("ARX_TOKEN").ok())
        .ok_or("pay requires --token or ARX_TOKEN")?;

    let addresses = ContractAddresses {
        token,
        registry: std::env::var("ARX_REGISTRY").unwrap_or_default(),
        addresses: std::env::var("ARX_ADDRESSES").unwrap_or_default(),
        oracle: std::env::var("ARX_ORACLE").unwrap_or_default(),
        payment_router: router,
    };
    let mut config = NetworkConfig::local(addresses);
    config.rpc_url = Some(
        args.rpc_url
            .unwrap_or_else(|| "http://127.0.0.1:8545".into()),
    );
    config.chain_id = match args.chain_id {
        8453 => ChainId::BaseMainnet,
        84532 => ChainId::BaseSepolia,
        _ => ChainId::Local,
    };

    let rt = tokio::runtime::Runtime::new()?;
    let client = rt.block_on(PaymentClient::new(config, &key))?;
    println!(
        "💳 Paying {} $AXD for access to building {}",
        amount, building_id
    );
    let receipt = rt.block_on(client.pay_for_access_tokens(&building_id, amount, nonce))?;
    println!("✅ {}", receipt);
    println!("   AccessPaid emitted on-chain; data hosts should gate delivery on this event.");
    Ok(())
}

#[cfg(not(feature = "blockchain"))]
fn execute_pay(_args: PayArgs) -> Result<(), Box<dyn Error>> {
    Err(
        "arx access pay requires rebuilding with --features blockchain \
         (cargo build --features blockchain)"
            .into(),
    )
}

#[cfg(feature = "blockchain")]
fn resolve_key(arg: Option<&str>) -> Result<String, Box<dyn Error>> {
    if let Some(k) = arg {
        if let Ok(from_env) = std::env::var(k) {
            return Ok(from_env.trim().trim_start_matches("0x").to_string());
        }
        return Ok(k.trim().trim_start_matches("0x").to_string());
    }
    if let Ok(k) = std::env::var("ARX_PRIVATE_KEY") {
        return Ok(k.trim().trim_start_matches("0x").to_string());
    }
    Ok("ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80".into())
}

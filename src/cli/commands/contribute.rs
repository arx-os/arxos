//! Build a contribution package from validated building.yaml (reward path).
//!
//! Default: write `contribution.json` (N1).
//! With `--features blockchain`: optional EIP-712 `--sign` and oracle `--submit` (N2–N3).

use super::Command;
use crate::contribution::{build_contribution_package, PackageOptions};
use crate::persistence::{load_building_at, BUILDING_YAML};
use std::error::Error;
use std::path::{Path, PathBuf};

pub struct ContributeCommand {
    pub output: PathBuf,
    pub latitude: Option<f64>,
    pub longitude: Option<f64>,
    pub git_commit: Option<String>,
    pub allow_invalid: bool,
    pub dry_run: bool,
    /// EIP-712 sign package (`blockchain` feature).
    pub sign: bool,
    /// Private key hex or env name when sign/submit.
    pub private_key: Option<String>,
    /// Oracle contract address (sign domain / submit target).
    pub oracle: Option<String>,
    /// Chain id (default 31337 Anvil).
    pub chain_id: u64,
    /// Submit proposeContribution to RPC (requires oracle role + stake).
    pub submit: bool,
    /// Worker wallet that performed the labor.
    pub worker: Option<String>,
    /// Whole $AXD to mint on propose.
    pub amount: u64,
    /// RPC URL for submit.
    pub rpc_url: Option<String>,
}

impl Command for ContributeCommand {
    fn execute(&self) -> Result<(), Box<dyn Error>> {
        let repo_root = Path::new(".");
        let building = load_building_at(repo_root)
            .map_err(|e| format!("load {}: {}", BUILDING_YAML, e))?;

        let git_commit = self.git_commit.clone().or_else(detect_head_commit);

        let opts = PackageOptions {
            latitude: self.latitude.unwrap_or(0.0),
            longitude: self.longitude.unwrap_or(0.0),
            git_commit,
            require_clean_validation: !self.allow_invalid,
        };

        let package = build_contribution_package(&building, opts)
            .map_err(|e| -> Box<dyn Error> { e.into() })?;

        println!("📦 Contribution package (building data labor)");
        println!("  {}", package.summary);
        println!("  building_id:  {}", package.building_id);
        println!("  merkle_root:  {}", package.merkle_root_hex);
        println!("  content_hash: {}", package.content_hash_hex);
        println!(
            "  quality:      accuracy={} completeness={}",
            package.accuracy, package.completeness
        );
        if let Some(ref c) = package.git_commit {
            println!("  git_commit:   {}", c);
        }
        println!("  algorithm:    {}", package.hash_algorithm);

        if self.dry_run && !self.sign && !self.submit {
            println!("Dry run — not writing {}", self.output.display());
            return Ok(());
        }

        if self.sign || self.submit {
            return self.execute_chain(&package);
        }

        if self.dry_run {
            println!("Dry run — not writing {}", self.output.display());
            return Ok(());
        }

        let json = serde_json::to_string_pretty(&package)?;
        std::fs::write(&self.output, json)?;
        println!("✅ Wrote {}", self.output.display());
        println!(
            "   Next: arx contribute --sign (rebuild with --features blockchain) or hand package to oracle."
        );
        Ok(())
    }

    fn name(&self) -> &'static str {
        "contribute"
    }
}

impl ContributeCommand {
    #[cfg(feature = "blockchain")]
    fn execute_chain(
        &self,
        package: &crate::contribution::ContributionPackage,
    ) -> Result<(), Box<dyn Error>> {
        use crate::blockchain::{
            sign_package_offline, NetworkConfig, OracleClient, ProofSigner, ContractAddresses,
            ChainId,
        };

        let key = resolve_private_key(self.private_key.as_deref())?;
        let oracle_addr = self
            .oracle
            .clone()
            .or_else(|| std::env::var("ARX_ORACLE").ok())
            .unwrap_or_else(|| "0x0000000000000000000000000000000000000001".into());

        let signer = ProofSigner::new(&key, self.chain_id, &oracle_addr)
            .map_err(|e| format!("proof signer: {}", e))?;

        let rt = tokio::runtime::Runtime::new()?;
        let signed = rt.block_on(sign_package_offline(
            package,
            &signer,
            self.chain_id,
            &oracle_addr,
        ))?;

        println!("🔏 EIP-712 signed");
        println!("  signer:  {}", signed.signer_address);
        println!("  oracle:  {}", signed.oracle_address);
        println!("  chain:   {}", signed.chain_id);
        println!("  sig:     {}…", &signed.signature_hex[..16.min(signed.signature_hex.len())]);

        let out = if self.output.extension().and_then(|e| e.to_str()) == Some("json")
            && !self.output.to_string_lossy().contains("signed")
        {
            self.output.with_extension("signed.json")
        } else {
            self.output.clone()
        };

        if !self.dry_run {
            let json = serde_json::to_string_pretty(&signed)?;
            std::fs::write(&out, json)?;
            println!("✅ Wrote signed package {}", out.display());
        }

        if self.submit {
            let worker = self
                .worker
                .clone()
                .or_else(|| std::env::var("ARX_WORKER").ok())
                .ok_or("submit requires --worker or ARX_WORKER")?;
            let rpc = self
                .rpc_url
                .clone()
                .unwrap_or_else(|| "http://127.0.0.1:8545".into());

            let addresses = ContractAddresses {
                token: std::env::var("ARX_TOKEN").unwrap_or_default(),
                registry: std::env::var("ARX_REGISTRY").unwrap_or_default(),
                addresses: std::env::var("ARX_ADDRESSES").unwrap_or_default(),
                oracle: oracle_addr,
                payment_router: std::env::var("ARX_PAYMENT_ROUTER").unwrap_or_default(),
            };
            let mut config = NetworkConfig::local(addresses);
            if self.chain_id != ChainId::Local as u64 {
                // keep local rpc override
            }
            config.rpc_url = Some(rpc);
            // chain_id field is enum — map common ids
            config.chain_id = match self.chain_id {
                8453 => ChainId::BaseMainnet,
                84532 => ChainId::BaseSepolia,
                _ => ChainId::Local,
            };

            let client = rt.block_on(OracleClient::new(config, &key))?;
            let receipt = rt.block_on(client.report_from_package(package, &worker, self.amount))?;
            println!("📡 proposeContribution submitted");
            println!("  {}", receipt);
            println!(
                "  Note: mint finalizes after 2-of-3 oracle confirms + 24h delay (contract rules)."
            );
        }

        Ok(())
    }

    #[cfg(not(feature = "blockchain"))]
    fn execute_chain(
        &self,
        _package: &crate::contribution::ContributionPackage,
    ) -> Result<(), Box<dyn Error>> {
        Err(
            "--sign / --submit require rebuilding with --features blockchain \
             (cargo build --features blockchain)"
                .into(),
        )
    }
}

#[cfg(feature = "blockchain")]
fn resolve_private_key(arg: Option<&str>) -> Result<String, Box<dyn Error>> {
    if let Some(k) = arg {
        if let Ok(from_env) = std::env::var(k) {
            return Ok(from_env.trim().trim_start_matches("0x").to_string());
        }
        return Ok(k.trim().trim_start_matches("0x").to_string());
    }
    if let Ok(k) = std::env::var("ARX_PRIVATE_KEY") {
        return Ok(k.trim().trim_start_matches("0x").to_string());
    }
    // Anvil account #0 (local only)
    Ok("ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80".into())
}

fn detect_head_commit() -> Option<String> {
    let repo = git2::Repository::open(".").ok()?;
    let head = repo.head().ok()?;
    let oid = head.peel_to_commit().ok()?.id();
    Some(oid.to_string())
}

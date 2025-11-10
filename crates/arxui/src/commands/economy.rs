use ethers_core::types::{Address, U256};
use serde_json::Value;
use std::fs;
use std::path::Path;
use std::str::FromStr;
use tokio::runtime::Runtime;

use crate::cli::EconomyCommands;
use arxos::{
    ArxoEconomyService, DatasetPublishRequest, EconomyConfig, RevenueDistributionRequest,
    StakingAction, VerificationRequest,
};

const ARXO_DECIMALS: u32 = 18;
const USDC_DECIMALS: u32 = 6;

pub fn handle_economy_command(command: EconomyCommands) -> Result<(), Box<dyn std::error::Error>> {
    let mut config =
        EconomyConfig::from_env().map_err(|e| format!("Failed to load economy config: {e}"))?;

    if matches!(command, EconomyCommands::ShowConfig) {
        let yaml = serde_yaml::to_string(&config)?;
        println!("{yaml}");
        return Ok(());
    }

    let service = ArxoEconomyService::new(config.clone())
        .map_err(|e| format!("Failed to build economy service: {e}"))?;
    config = service.config().clone();
    let rt = build_runtime()?;

    match command {
        EconomyCommands::Verify {
            property_id,
            recipient,
            tax_value,
        } => {
            let recipient = parse_address(&recipient)?;
            let tax_value = parse_integer_amount(&tax_value)?;
            let request = VerificationRequest {
                property_id,
                recipient,
                estimated_tax_value_usd: tax_value,
            };
            let tx_hash = rt
                .block_on(async { service.verify_building(request).await })
                .map_err(|e| format!("Oracle request failed: {e}"))?;
            println!("✅ Submitted verification transaction: {tx_hash:?}");
        }
        EconomyCommands::Stake { amount } => {
            let token_amount = parse_decimal_amount(&amount, ARXO_DECIMALS)?;
            rt.block_on(async {
                service
                    .execute_staking(StakingAction::Stake {
                        amount: token_amount,
                    })
                    .await
            })
            .map_err(|e| format!("Stake failed: {e}"))?;
            println!("✅ Staked {} ARXO", amount);
        }
        EconomyCommands::Unstake { amount } => {
            let token_amount = parse_decimal_amount(&amount, ARXO_DECIMALS)?;
            rt.block_on(async {
                service
                    .execute_staking(StakingAction::Unstake {
                        amount: token_amount,
                    })
                    .await
            })
            .map_err(|e| format!("Unstake failed: {e}"))?;
            println!("✅ Unstaked {} ARXO", amount);
        }
        EconomyCommands::Claim => {
            rt.block_on(async { service.execute_staking(StakingAction::Claim).await })
                .map_err(|e| format!("Claim failed: {e}"))?;
            println!("✅ Claimed staking rewards");
        }
        EconomyCommands::Rewards { address } => {
            let addr = resolve_address(address, &config)?;
            let rewards = rt
                .block_on(async { service.pending_rewards(addr).await })
                .map_err(|e| format!("Failed to fetch rewards: {e}"))?;
            println!(
                "💰 Pending rewards: {} ARXO",
                format_decimal(rewards, ARXO_DECIMALS)
            );
        }
        EconomyCommands::Distribute { usdc_amount } => {
            let amount = parse_decimal_amount(&usdc_amount, USDC_DECIMALS)?;
            let request = RevenueDistributionRequest {
                usdc_amount: amount,
            };
            rt.block_on(async { service.distribute_revenue(request).await })
                .map_err(|e| format!("Distribution failed: {e}"))?;
            println!(
                "✅ Distributed {} USDC through revenue splitter",
                usdc_amount
            );
        }
        EconomyCommands::Publish {
            name,
            payload,
            metadata,
        } => {
            let payload = load_json(&payload)?;
            let metadata = metadata
                .map(|path| load_json(&path))
                .transpose()?
                .unwrap_or_else(|| Value::Object(Default::default()));

            let request = DatasetPublishRequest {
                name: name.clone(),
                payload,
                metadata,
            };

            let gateway = rt
                .block_on(async { service.publish_dataset(request).await })
                .map_err(|e| format!("Publish failed: {e}"))?;

            println!("✅ Dataset '{}' published", name);
            match gateway {
                Some(url) => println!("🔗 Gateway URL: {url}"),
                None => println!("ℹ️  No gateway URL configured; CID stored remotely."),
            }
        }
        EconomyCommands::Balance { address } => {
            let addr = resolve_address(address, &config)?;
            let balance = rt
                .block_on(async { service.token_balance(addr).await })
                .map_err(|e| format!("Failed to fetch balance: {e}"))?;
            println!(
                "🏦 Balance: {} ARXO",
                format_decimal(balance, ARXO_DECIMALS)
            );
        }
        EconomyCommands::TotalValue => {
            let tav = rt
                .block_on(async { service.total_assessed_value().await })
                .map_err(|e| format!("Failed to fetch assessed value: {e}"))?;
            println!("🏛️ Total assessed value: {} USD", tav);
        }
        EconomyCommands::ShowConfig => unreachable!(),
    }

    Ok(())
}

fn build_runtime() -> Result<Runtime, Box<dyn std::error::Error>> {
    tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()
        .map_err(|e| format!("Failed to initialize tokio runtime: {e}").into())
}

fn parse_address(input: &str) -> Result<Address, Box<dyn std::error::Error>> {
    Address::from_str(input).map_err(|e| format!("Invalid address '{input}': {e}").into())
}

fn resolve_address(
    override_addr: Option<String>,
    config: &EconomyConfig,
) -> Result<Address, Box<dyn std::error::Error>> {
    if let Some(addr) = override_addr {
        return parse_address(&addr);
    }

    if let Some(sender) = &config.wallet.default_sender {
        return parse_address(sender);
    }

    Err("No wallet address provided. Use --address or set ARXO_WALLET_SENDER".into())
}

fn parse_integer_amount(value: &str) -> Result<U256, Box<dyn std::error::Error>> {
    U256::from_dec_str(value).map_err(|e| format!("Invalid numeric value '{value}': {e}").into())
}

fn parse_decimal_amount(value: &str, decimals: u32) -> Result<U256, Box<dyn std::error::Error>> {
    let parts: Vec<&str> = value.split('.').collect();
    if parts.len() > 2 {
        return Err(format!("Invalid decimal format '{value}'").into());
    }

    let scale = U256::exp10(decimals as usize);
    let whole = U256::from_dec_str(parts[0])
        .map_err(|e| format!("Invalid numeric value '{value}': {e}"))?;
    let mut result = whole * scale;

    if parts.len() == 2 {
        let mut fraction = parts[1].to_string();
        if fraction.len() > decimals as usize {
            return Err(format!(
                "Too many decimal places in '{value}'. Maximum {decimals} decimals supported."
            )
            .into());
        }
        while fraction.len() < decimals as usize {
            fraction.push('0');
        }
        let frac_value = U256::from_dec_str(&fraction)
            .map_err(|e| format!("Invalid decimal value '{value}': {e}"))?;
        result += frac_value;
    }

    Ok(result)
}

fn format_decimal(value: U256, decimals: u32) -> String {
    if decimals == 0 {
        return value.to_string();
    }

    let scale = U256::exp10(decimals as usize);
    let whole = value / scale;
    let remainder = value % scale;

    if remainder.is_zero() {
        return whole.to_string();
    }

    let mut frac = remainder.to_string();
    if frac.len() < decimals as usize {
        frac = format!("{:0>width$}", frac, width = decimals as usize);
    }
    let frac_trimmed = frac.trim_end_matches('0');
    if frac_trimmed.is_empty() {
        whole.to_string()
    } else {
        format!("{}.{}", whole, frac_trimmed)
    }
}

fn load_json(path: &str) -> Result<Value, Box<dyn std::error::Error>> {
    let path = Path::new(path);
    let data =
        fs::read_to_string(path).map_err(|e| format!("Failed to read {}: {e}", path.display()))?;
    let json: Value = serde_json::from_str(&data)
        .map_err(|e| format!("Invalid JSON in {}: {e}", path.display()))?;
    Ok(json)
}

# ArxOS Blockchain Integration

Rust integration layer for ArxOS smart contracts on Base L2.

## Overview

This module provides high-level Rust APIs for interacting with ArxOS tokenomics contracts:

- **OracleClient**: Report spatial data contributions and trigger ARXO mints
- **PaymentClient**: Execute x402 micropayments for data access
- **ProofSigner**: Generate EIP-712 signatures for contribution verification
- **Contract Bindings**: Type-safe interfaces to Solidity contracts

## Features

Enable in `Cargo.toml`:

```toml
[dependencies]
arxos = { path = ".", features = ["blockchain"] }
```

Or include with agent feature:

```bash
cargo build --features blockchain
```

## Usage Examples

### 1. Report a Contribution (Oracle)

```rust
use arxos::blockchain::{OracleClient, NetworkConfig, ContractAddresses, ChainId};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Configure network
    let config = NetworkConfig::base_mainnet(ContractAddresses {
        token: "0x...".to_string(),
        registry: "0x...".to_string(),
        addresses: "0x...".to_string(),
        oracle: "0x...".to_string(),
        payment_router: "0x...".to_string(),
    });

    // Create oracle client
    let oracle = OracleClient::new(config, "YOUR_PRIVATE_KEY").await?;

    // Report contribution
    let tx = oracle.report_contribution(
        "ps-118",                    // Building ID
        "0xWorkerAddress",           // Worker wallet
        100,                         // 100 ARXO to mint
        merkle_root,                 // Spatial data commitment
        40.7128,                     // Latitude
        -74.0060,                    // Longitude
        1024000,                     // 1 MB data
    ).await?;

    println!("✅ Contribution reported: {}", tx.tx_hash);
    println!("🔗 View on Basescan: {}", oracle.get_tx_url(&tx.tx_hash));

    Ok(())
}
```

### 2. Pay for Data Access (x402)

```rust
use arxos::blockchain::{PaymentClient, NetworkConfig};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let config = NetworkConfig::base_mainnet(addresses);
    let payment_client = PaymentClient::new(config, "YOUR_PRIVATE_KEY").await?;

    // Check balance first
    let balance = payment_client.get_balance().await?;
    println!("💰 Your balance: {} ARXO", balance);

    // Get minimum payment for building
    let minimum = payment_client.get_minimum_payment("ps-118").await?;
    println!("💳 Minimum payment: {} ARXO", minimum);

    // Parse nonce from 402 response
    let nonce = PaymentClient::parse_nonce("0xServerNonceHex")?;

    // Execute payment
    let tx = payment_client.pay_for_access(
        "ps-118",     // Building ID
        0.1,          // 0.1 ARXO
        nonce,        // From server
    ).await?;

    println!("✅ Payment confirmed: {}", tx.tx_hash);

    Ok(())
}
```

### 3. Generate Contribution Proof

```rust
use arxos::blockchain::proof::{ContributionProof, ProofSigner};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Create proof
    let proof = ContributionProof::new(
        merkle_root,
        40.7128,   // NYC latitude
        -74.0060,  // NYC longitude
        "ps-118",
        1024000,   // 1 MB
    );

    // Sign with EIP-712
    let signer = ProofSigner::new(
        "WORKER_PRIVATE_KEY",
        8453,  // Base mainnet
        "0xOracleAddress",
    )?;

    let signature = signer.sign_proof(&proof).await?;
    println!("✍️  Signed proof: {} bytes", signature.len());

    Ok(())
}
```

### 4. CLI Integration

```rust
// In src/cli/commands/contribute.rs
use arxos::blockchain::OracleClient;

pub async fn contribute_command(building_id: &str, data_path: &Path) -> Result<()> {
    // Load blockchain config
    let config = load_blockchain_config()?;
    let oracle = OracleClient::new(config, &get_private_key()?).await?;

    // Process spatial data
    let merkle_root = compute_merkle_root(data_path)?;
    let (lat, lon) = extract_gps_coords(data_path)?;
    let data_size = std::fs::metadata(data_path)?.len();

    // Report contribution
    let tx = oracle.report_contribution(
        building_id,
        &get_worker_address()?,
        calculate_reward(data_size),
        merkle_root,
        lat,
        lon,
        data_size,
    ).await?;

    println!("✅ Contribution submitted!");
    println!("   Transaction: {}", tx.tx_hash);
    println!("   Awaiting 2 oracle confirmations + 24 hour delay");

    Ok(())
}
```

## Configuration

Store contract addresses in `~/.arxos/blockchain.toml`:

```toml
[network]
chain_id = 8453  # Base mainnet
rpc_url = "https://mainnet.base.org"

[contracts]
token = "0x..."
registry = "0x..."
addresses = "0x..."
oracle = "0x..."
payment_router = "0x..."

[wallet]
private_key_path = "~/.arxos/wallet.key"
```

Load with:

```rust
use arxos::blockchain::NetworkConfig;

let config = NetworkConfig::load_from_file("~/.arxos/blockchain.toml")?;
```

## Contract ABIs

Contract bindings are generated from Solidity ABIs in `/contracts/out/`.

To regenerate after contract changes:

```bash
cd contracts
forge build  # Compile contracts
cd ..
cargo build --features blockchain  # Regenerate bindings
```

## Testing

Run blockchain integration tests:

```bash
# Start local Anvil node
anvil

# Deploy contracts to local network
cd contracts
forge script script/Deploy.s.sol --rpc-url http://localhost:8545 --broadcast

# Run Rust tests
cd ..
cargo test --features blockchain test_blockchain
```

## Error Handling

All blockchain operations return `Result<T, anyhow::Error>`:

```rust
match payment_client.pay_for_access("ps-118", 0.1, nonce).await {
    Ok(tx) => println!("✅ Payment successful: {}", tx.tx_hash),
    Err(e) => {
        eprintln!("❌ Payment failed: {}", e);
        if e.to_string().contains("insufficient balance") {
            println!("💡 Top up your ARXO balance first");
        }
    }
}
```

## Gas Optimization

- **Auto-approval**: First payment approves unlimited spending
- **Batch operations**: Group multiple payments in one transaction
- **Gas estimation**: Automatically estimated before transaction

```rust
// Check gas before payment
let gas_estimate = payment_client.estimate_gas("ps-118", 0.1, nonce).await?;
println!("⛽ Estimated gas: {} wei", gas_estimate);
```

## Security

- **Never commit private keys**: Use environment variables
- **Verify addresses**: Always check contract addresses on Basescan
- **Test first**: Use Base Sepolia testnet before mainnet
- **Monitor transactions**: Subscribe to events for payment verification

## Dependencies

```toml
ethers = "2.0"
ethers-contract = "2.0"
ethers-signers = "2.0"
hex = "0.4"
tokio = "1.35"
```

## See Also

- [x402 Protocol Specification](../../docs/x402-protocol.md)
- [Smart Contract Documentation](../../contracts/README.md)
- [Tokenomics Implementation Plan](../../ARXO_TOKENOMICS_IMPLEMENTATION.md)

---

**Built for the ArxOS ecosystem** 🦀⛓️

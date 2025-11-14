//! Economy and token operation commands

use clap::Subcommand;

#[derive(Subcommand)]
pub enum EconomyCommands {
    /// Submit tax verification to mint ARXO
    Verify {
        /// External property identifier (e.g., parcel id)
        #[arg(long)]
        property_id: String,
        /// Recipient wallet address (0x...)
        #[arg(long)]
        recipient: String,
        /// Verified tax value in USD (whole dollars)
        #[arg(long)]
        tax_value: String,
    },
    /// Stake ARXO for revenue shares
    Stake {
        /// Amount of ARXO to stake (whole tokens)
        #[arg(long)]
        amount: String,
    },
    /// Unstake ARXO
    Unstake {
        /// Amount of ARXO to unstake
        #[arg(long)]
        amount: String,
    },
    /// Claim accrued staking rewards
    Claim,
    /// Show pending rewards for an address
    Rewards {
        /// Wallet address to query (defaults to configured wallet)
        #[arg(long)]
        address: Option<String>,
    },
    /// Trigger revenue splitter distribution
    Distribute {
        /// USDC amount to split (whole dollars)
        #[arg(long)]
        usdc_amount: String,
    },
    /// Publish dataset to IPFS/Ocean
    Publish {
        /// Dataset name
        #[arg(long)]
        name: String,
        /// JSON payload file path
        #[arg(long)]
        payload: String,
        /// Optional JSON metadata file path
        #[arg(long)]
        metadata: Option<String>,
    },
    /// Display ARXO balance for an address
    Balance {
        /// Wallet address to query (defaults to configured wallet)
        #[arg(long)]
        address: Option<String>,
    },
    /// Display total assessed value backing ARXO
    TotalValue,
    /// Print resolved economy configuration
    ShowConfig,
}

# ArxOS Tokenomics Smart Contracts

Ethereum smart contracts for the ArxOS ecosystem, implementing the 70/10/10/10 tokenomics model with soulbound identities and x402 micropayments.

## Overview

**Network**: Base L2 (Coinbase)  
**Solidity Version**: 0.8.20  
**Framework**: Foundry

### Core Contracts

1. **ArxAddresses** - Configuration registry for system addresses
2. **ArxRegistry** - Soulbound identity management for workers and buildings  
3. **ArxosToken** - ERC20 token with role-based minting
4. **ArxContributionOracle** - Multi-oracle contribution verification with EIP-712 proofs
5. **ArxPaymentRouter** - x402 micropayment handler with 70/10/10/10 splits

### Tokenomics

Every mint and payment distributes ARXO with an immutable 70/10/10/10 split:

- **70%** → Field Contributor (Worker)
- **10%** → Building Twin Fund (Building Owner)
- **10%** → Maintainers/Open-Source Vault (RPGF)
- **10%** → ArxOS LLC Treasury

---

## Installation

### Prerequisites

- [Foundry](https://book.getfoundry.sh/getting-started/installation)
- [Node.js](https://nodejs.org/) (for TypeScript types)

### Setup

```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Clone repository
git clone https://github.com/arx-os/arxos.git
cd arxos/contracts

# Install dependencies
forge install

# Build contracts
forge build

# Run tests
forge test

# Run tests with gas report
forge test --gas-report
```

---

## Architecture

### Contract Dependencies

```
ArxosToken (ERC20)
    ↑
    ├── ArxContributionOracle (mints)
    └── ArxPaymentRouter (transfers)

ArxRegistry (identities)
    ↑
    ├── ArxContributionOracle (lookups)
    └── ArxPaymentRouter (lookups)

ArxAddresses (config)
    ↑
    ├── ArxContributionOracle (treasury/maintainer)
    └── ArxPaymentRouter (treasury/maintainer)
```

### Key Features

#### Multi-Oracle Consensus
- Requires 2-of-3 oracle confirmations
- 24-hour finalization delay for disputes
- EIP-712 typed signatures for proofs

#### Soulbound Workers
- Non-transferable ERC721 NFTs
- One identity per worker
- Metadata stored on-chain (IPFS CIDs)

#### x402 Protocol Integration
- HTTP 402 Payment Required standard
- On-chain payment verification
- Nonce-based replay protection

---

## Deployment

### Environment Setup

Create `.env` file:

```bash
# Deployment
PRIVATE_KEY=0x...
MAINTAINER_VAULT=0x...  # Gnosis Safe address
TREASURY=0x...          # Treasury wallet

# Base Sepolia Testnet
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org
BASESCAN_API_KEY=...

# Base Mainnet
BASE_MAINNET_RPC_URL=https://mainnet.base.org
```

### Deploy to Testnet

```bash
# Deploy all contracts
forge script script/Deploy.s.sol:DeployArxos \
  --rpc-url $BASE_SEPOLIA_RPC_URL \
  --broadcast \
  --verify

# Verify contracts manually if needed
forge verify-contract <address> ArxosToken \
  --chain-id 84532 \
  --etherscan-api-key $BASESCAN_API_KEY
```

### Deploy to Mainnet

```bash
# Same command, different RPC
forge script script/Deploy.s.sol:DeployArxos \
  --rpc-url $BASE_MAINNET_RPC_URL \
  --broadcast \
  --verify \
  --slow  # Add delays between transactions
```

---

## Usage

### Register a Worker

```solidity
// As contract owner
registry.registerWorker(
    0xWorkerWalletAddress,
    "ipfs://QmMetadataHash"
);
```

### Register a Building

```solidity
// As contract owner
registry.registerBuilding(
    "ps-118",                // Building ID
    0xBuildingOwnerWallet   // Owner address
);
```

### Report a Contribution (Oracle)

```solidity
// Prepare proof
ArxContributionOracle.ContributionProof memory proof = ContributionProof({
    merkleRoot: 0x...,
    locationHash: keccak256(abi.encodePacked(lat, lon, timestamp)),
    buildingHash: keccak256("ps-118"),
    timestamp: block.timestamp,
    dataSize: 1024000  // 1 MB
});

// Worker signs proof (EIP-712)
bytes memory signature = signTypedData(proof, workerPrivateKey);

// Oracle proposes contribution
oracle.proposeContribution(
    "ps-118",      // Building ID
    workerAddress, // Worker
    100 ether,     // 100 ARXO to mint
    proof,
    signature
);

// After 2 confirmations + 24 hours
oracle.finalizeContribution(contributionId);
```

### Pay for Data Access (x402)

```solidity
// User approves ARXO
arxoToken.approve(address(router), 0.1 ether);

// Pay for access
router.payForAccess(
    "ps-118",           // Building ID
    0.1 ether,          // 0.1 ARXO
    0xServerNonce       // From 402 response
);
```

---

## Testing

### Run All Tests

```bash
forge test -vvv
```

### Run Specific Test

```bash
forge test --match-test test_MintContribution -vvv
```

### Coverage Report

```bash
forge coverage
```

### Gas Snapshots

```bash
forge snapshot
```

### Fuzz Testing

```bash
# Run with more iterations
forge test --fuzz-runs 10000
```

---

## Security

### Audits

- [ ] Internal review (Slither, Mythril)
- [ ] Community review (bug bounty)
- [ ] Professional audit (scheduled)

### Bug Bounty

Report vulnerabilities to: security@arxos.io

**Rewards**:
- Critical: 5000 ARXO
- High: 1000 ARXO
- Medium: 500 ARXO

### Known Limitations

1. **Centralized oracle**: V1 uses trusted oracles (evolving to decentralized)
2. **24-hour delay**: Contributions require waiting period
3. **Building ownership**: Single-owner model (V2 will support multi-sig)

---

## Development

### Project Structure

```
contracts/
├── src/
│   ├── ArxAddresses.sol           # Configuration
│   ├── ArxRegistry.sol            # Identity management
│   ├── ArxosToken.sol             # ERC20 token
│   ├── ArxContributionOracle.sol  # Minting logic
│   └── ArxPaymentRouter.sol       # Payment handling
├── test/
│   ├── ArxAddresses.t.sol
│   ├── ArxRegistry.t.sol
│   ├── ArxosToken.t.sol
│   ├── ArxContribution.t.sol
│   ├── ArxPayment.t.sol
│   └── Integration.t.sol
├── script/
│   └── Deploy.s.sol               # Deployment script
├── foundry.toml                   # Foundry config
└── README.md
```

### Add Dependencies

```bash
forge install OpenZeppelin/openzeppelin-contracts@v5.0.2
```

### Update Remappings

Edit `foundry.toml`:

```toml
remappings = [
    "@openzeppelin/contracts/=lib/openzeppelin-contracts/contracts/",
]
```

---

## Governance

### Phase 1: Centralized (Launch)
- ArxOS LLC controls all contracts
- Owner can update system addresses
- Oracle operators are trusted entities

### Phase 2: Multi-sig (6 months)
- Transfer ownership to Gnosis Safe (5-of-9)
- Community signers added
- Snapshot for signaling

### Phase 3: DAO (12 months)
- On-chain governance via ARXO token
- Timelock for sensitive operations
- Emergency pause mechanism

---

## References

- [Foundry Book](https://book.getfoundry.sh/)
- [OpenZeppelin Contracts](https://docs.openzeppelin.com/contracts/5.x/)
- [Base Network Docs](https://docs.base.org/)
- [EIP-712 Spec](https://eips.ethereum.org/EIPS/eip-712)
- [x402 Protocol](../docs/x402-protocol.md)

---

## License

MIT License - see [LICENSE](../LICENSE)

---

## Support

- **Documentation**: https://docs.arxos.io
- **Discord**: https://discord.gg/arxos
- **GitHub**: https://github.com/arx-os/arxos
- **Email**: hello@arxos.io

---

**Built with ❤️ for the building data revolution** 🏗️

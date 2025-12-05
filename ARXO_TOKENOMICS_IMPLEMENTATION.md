# ARXO Tokenomics Implementation Plan

> **Status**: Ready for implementation on Mac with Foundry
> 
> **Date**: 2025-12-05
> 
> **Context**: This document consolidates all planning for implementing the full ARXO tokenomics vision using Foundry (Rust-based tooling) instead of Hardhat.

---

## Table of Contents
1. [Current State Assessment](#current-state-assessment)
2. [Target Tokenomics Specification](#target-tokenomics-specification)
3. [Gap Analysis](#gap-analysis)
4. [Implementation Plan](#implementation-plan)
5. [Technical Architecture](#technical-architecture)
6. [Testing Strategy](#testing-strategy)
7. [Next Steps](#next-steps)

---

## Current State Assessment

### Existing Contracts (`contracts/contracts/`)

1. **ArxosToken.sol** - ERC20 token with oracle-based minting
   - Mints based on "Tax Assessed Value" (USD)
   - 100% of minted tokens go to single recipient
   - Oracle-controlled minting (`onlyOracle`)

2. **ArxStaking.sol** - Staking pool for ARXO rewards
   - Pro-rata reward distribution
   - Uses accumulated reward per share pattern
   - ReentrancyGuard protected

3. **RevenueSplitter.sol** - USDC revenue distribution
   - Splits USDC: 60% stakers, 20% burn, 20% treasury
   - Swaps USDC → ARXO via Uniswap V3
   - Owner-controlled distribution

4. **TaxOracle.sol** - Chainlink oracle client
   - Requests property assessments
   - Triggers minting on fulfillment

### Current Tooling
- **Hardhat** (Node/TypeScript based)
- **OpenZeppelin Contracts** v5.0.2
- **Chainlink Contracts** v1.5.0
- **Uniswap V3 Periphery** v1.4.4

---

## Target Tokenomics Specification

### Core Principles
- **Uncapped Supply**: Infinite minting tied to real-world contributions
- **Contribution-Based**: Minting triggered by verified spatial data uploads, live commands, SDK integrations
- **70/10/10/10 Split**: Mandatory distribution for ALL mints and payments
- **Soulbound Identity**: Field Workers and Buildings have registered wallets
- **x402 Payments**: Micropayments for data access routed through smart contracts

### Distribution Split (Immutable)

Every mint and payment follows:
- **70%** → Field Contributor (Soulbound Worker ID)
- **10%** → Building Twin Fund (Soulbound Building Wallet)
- **10%** → Maintainers/Open-Source Vault (RPGF)
- **10%** → ArxOS LLC Treasury

### Token Standard
- ERC20 on Base (Coinbase L2)
- Gasless transfers via EIP-3009
- Post-quantum ready architecture

---

## Gap Analysis

### Critical Gaps

| Component | Current | Required | Priority |
|-----------|---------|----------|----------|
| **Distribution** | 100% to recipient | 70/10/10/10 split | 🔴 Critical |
| **Identity Registry** | None | Soulbound Worker & Building IDs | 🔴 Critical |
| **Minting Logic** | Tax Value (USD) | Generic Contributions | 🔴 Critical |
| **Payment Router** | None | x402 micropayment settlement | 🔴 Critical |
| **Tooling** | Hardhat (Node/TS) | Foundry (Rust) | 🟡 High |

### Revenue vs Minting Ambiguity

**Current**: `RevenueSplitter` handles USDC with 60/20/20 split

**Spec**: 70/10/10/10 applies to both minting AND access payments

**Resolution**: Keep `RevenueSplitter` for legacy USDC flows, create new `ArxPaymentRouter` for x402 ARXO payments

---

## Implementation Plan

### Phase 1: Foundry Migration

#### Install Foundry (Mac)
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

#### Initialize Foundry Project
```bash
cd contracts
forge init --force
```

#### Migrate Existing Contracts
1. Copy `.sol` files to `src/`
2. Update imports for Foundry structure
3. Install dependencies:
   ```bash
   forge install OpenZeppelin/openzeppelin-contracts
   forge install smartcontractkit/chainlink
   forge install Uniswap/v3-periphery
   ```

### Phase 2: New Contract Development

#### 1. ArxRegistry.sol
**Purpose**: Manage Soulbound identities for Workers and Buildings

```solidity
// Key Functions
function registerWorker(address wallet, string calldata metadata) external onlyOwner
function registerBuilding(string calldata buildingId, address wallet) external onlyOwner
function getWorkerWallet(address worker) external view returns (address)
function getBuildingWallet(string calldata buildingId) external view returns (address)
```

**Features**:
- Emit events for all registrations
- Prevent duplicate registrations
- Owner-controlled (ArxOS LLC initially)

#### 2. ArxContributionOracle.sol
**Purpose**: Verify contributions and trigger 70/10/10/10 mints

```solidity
// Key Functions
function reportContribution(
    string calldata buildingId,
    address worker,
    uint256 amountARXO,
    bytes calldata proof
) external onlyOwner

function _distributeMint(
    address worker,
    address building,
    uint256 totalAmount
) internal
```

**Logic**:
- Verify proof (GPS, Merkle root, device signature)
- Calculate split: 70% worker, 10% building, 10% maintainer, 10% treasury
- Call `ArxosToken.mintBatch()`
- Emit detailed event with all recipients

#### 3. ArxPaymentRouter.sol
**Purpose**: Handle x402 micropayments for data access

```solidity
// Key Functions
function payForAccess(
    string calldata buildingId,
    uint256 amount
) external

function _distributePayment(
    address building,
    uint256 totalAmount
) internal
```

**Logic**:
- Transfer ARXO from user to contract
- Split 70/10/10/10 (70% to Building Wallet for V1 simplicity)
- Emit `AccessPaid` event for x402 gateway
- Support batch payments for efficiency

#### 4. Updated ArxosToken.sol

**Changes**:
- ❌ Remove `mintForBuilding(uint256 taxValueUSD, address recipient)`
- ✅ Add `mint(address to, uint256 amount)` (onlyOracle)
- ✅ Add `mintBatch(address[] calldata recipients, uint256[] calldata amounts)` (onlyOracle)
- ✅ Keep `burn(uint256 amount)` for deflationary mechanics

### Phase 3: Configuration Contracts

#### ArxAddresses.sol (Registry of System Addresses)
```solidity
contract ArxAddresses {
    address public maintainerVault;
    address public treasury;
    
    function setMaintainerVault(address _vault) external onlyOwner
    function setTreasury(address _treasury) external onlyOwner
}
```

---

## Technical Architecture

### Contract Interaction Flow

#### Minting Flow (Contribution Rewards)
```
Off-Chain Oracle (Rust)
    ↓ (verifies GPS, Merkle, signatures)
ArxContributionOracle.reportContribution()
    ↓ (calculates 70/10/10/10)
ArxosToken.mintBatch([worker, building, maintainer, treasury], [amounts])
    ↓
Tokens distributed to 4 recipients
```

#### Payment Flow (x402 Data Access)
```
User (CLI: arxos pull --pay)
    ↓ (approves ARXO)
ArxPaymentRouter.payForAccess(buildingId, amount)
    ↓ (transfers ARXO, splits 70/10/10/10)
[Building, Maintainer, Treasury] receive tokens
    ↓ (emits AccessPaid event)
x402 Gateway releases data
```

### Dependency Graph
```
ArxosToken (ERC20)
    ↑
    ├── ArxContributionOracle (mints)
    ├── ArxPaymentRouter (transfers)
    └── ArxStaking (rewards)

ArxRegistry (identities)
    ↑
    ├── ArxContributionOracle (lookups)
    └── ArxPaymentRouter (lookups)

ArxAddresses (config)
    ↑
    ├── ArxContributionOracle (treasury/maintainer)
    └── ArxPaymentRouter (treasury/maintainer)
```

---

## Testing Strategy

### Foundry Test Structure (`test/`)

#### 1. `ArxRegistry.t.sol`
- Register worker successfully
- Register building successfully
- Prevent duplicate registrations
- Lookup workers and buildings
- Access control (onlyOwner)

#### 2. `ArxContribution.t.sol`
- Report contribution with valid proof
- Verify 70/10/10/10 split on minting
- Check worker receives 70%
- Check building receives 10%
- Check maintainer receives 10%
- Check treasury receives 10%
- Reject invalid proofs
- Access control

#### 3. `ArxPayment.t.sol`
- Pay for access successfully
- Verify 70/10/10/10 split on payment
- Check `AccessPaid` event emission
- Handle insufficient balance
- Handle unregistered buildings

#### 4. `Integration.t.sol`
- Full flow: Register → Contribute → Mint → Pay → Access
- Multiple contributors to same building
- Edge cases (zero amounts, max uint256)

### Running Tests
```bash
forge test -vvv
forge coverage
forge snapshot
```

---

## Next Steps

### On Mac (Immediate)

1. **Install Foundry**
   ```bash
   curl -L https://foundry.paradigm.xyz | bash
   foundryup
   forge --version
   ```

2. **Initialize Project**
   ```bash
   cd ~/path/to/arxos/contracts
   forge init --force
   ```

3. **Install Dependencies**
   ```bash
   forge install OpenZeppelin/openzeppelin-contracts@v5.0.2
   forge install smartcontractkit/chainlink@v1.5.0
   forge install Uniswap/v3-periphery@v1.4.4
   ```

4. **Create Contracts** (in order)
   - `src/ArxAddresses.sol`
   - `src/ArxRegistry.sol`
   - `src/ArxosToken.sol` (update)
   - `src/ArxContributionOracle.sol`
   - `src/ArxPaymentRouter.sol`

5. **Write Tests**
   - `test/ArxRegistry.t.sol`
   - `test/ArxContribution.t.sol`
   - `test/ArxPayment.t.sol`
   - `test/Integration.t.sol`

6. **Verify & Deploy**
   ```bash
   forge test
   forge script script/Deploy.s.sol --rpc-url base --broadcast
   ```

### Off-Chain Integration (Rust)

The existing ArxOS Rust codebase will need to:
1. Generate contribution proofs (GPS, Merkle, signatures)
2. Call `ArxContributionOracle.reportContribution()` via `ethers-rs`
3. Listen for `AccessPaid` events to release data
4. Implement x402 protocol for CLI (`arxos pull --pay`)

---

## Security Considerations

### Audit Checklist
- [ ] Reentrancy protection on all state-changing functions
- [ ] Integer overflow/underflow (Solidity 0.8+ handles this)
- [ ] Access control on privileged functions
- [ ] Event emission for all critical actions
- [ ] Input validation (zero addresses, zero amounts)
- [ ] Gas optimization (batch operations)

### MEV Protection
- **RevenueSplitter**: Add slippage protection for Uniswap swaps (currently `amountOutMinimum: 0`)
- **ArxPaymentRouter**: Consider using TWAP oracle for fair pricing

### Decentralization Path
- Start: ArxOS LLC controls oracles and registries
- Phase 2: Multi-sig for critical functions
- Phase 3: DAO governance via RPGF for maintainer vault
- Phase 4: Decentralized oracle network (Chainlink DON)

---

## Reference Links

- **Foundry Book**: https://book.getfoundry.sh/
- **OpenZeppelin Contracts**: https://docs.openzeppelin.com/contracts/5.x/
- **Chainlink Docs**: https://docs.chain.link/
- **Base Network**: https://docs.base.org/
- **x402 Protocol**: (Spec to be defined)

---

## Questions for Resolution

1. **Building Payment Distribution**: For x402 payments, should the 70% "contributor share" go to:
   - A) The Building Wallet (current plan - simple)
   - B) A staking pool for all past contributors to that building (complex, gas-intensive)
   - C) A separate `BuildingRewardsPool` contract (middle ground)

2. **Proof Format**: What exact format should contribution proofs use?
   - Merkle root + signature?
   - Chainlink Functions for verification?
   - TEE attestation?

3. **Maintainer Vault**: Should this be:
   - A) Simple multisig wallet
   - B) Gnosis Safe with RPGF module
   - C) Custom contract with vesting/voting

4. **Network Choice**: Confirm Base as primary chain, or consider:
   - Arbitrum (has Stylus for native Rust contracts)
   - Polygon (current Hardhat config targets Mumbai)
   - Multi-chain deployment

---

**Ready to build! 🦀🚀**

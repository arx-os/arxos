# ARX Tokenomics & Infrastructure Integration — Design Clarifications
### Version 1.0 — July 28, 2025

---

## 1. ArxLogic Integration Points

### ✅ Validation Scores
- ArxLogic currently calculates validation scores using:
  - **Simulation Pass Rate** (% of objects passing behavioral simulation)
  - **AI Accuracy Rate** (correct label validation by system vs. peer-reviewed ground truth)
  - **System Completion Score** (how many objects are required to complete a system’s behavior)
  - **Error Propagation Score** (how many downstream dependencies are affected)

### 🔢 Complexity Metrics (examples)
| System       | Baseline Complexity Score |
|--------------|---------------------------|
| Electrical   | 1.0                       |
| Plumbing     | 1.2                       |
| HVAC         | 1.5                       |
| Fire Alarm   | 1.7                       |
| Security     | 2.0                       |

### 💰 ARX Minting Logic
- Mint formula proposal:
  `ARX_minted = BaseAmount * ValidationScore * ComplexityMultiplier`
- Example:
  - A fully validated HVAC VAV object (ValidationScore = 1.0, Complexity = 1.5) → mints 1.5 ARX
  - A partially validated electrical outlet (ValidationScore = 0.6, Complexity = 1.0) → mints 0.6 ARX

---

## 2. User Authentication & Wallet Integration

### 👤 Existing User System
- JWT auth + role-based access
- Roles: `contractor`, `school_staff`, `district_admin`, `arxos_support`
- Each user already has a profile and tracked reputation

### 🪙 Wallet Integration Strategy
- Wallets should be integrated into current user profiles (1:1 mapping)
- Each user receives a default wallet on login or onboarding
- Add optional ability to **link external wallets (MetaMask, Ledger)** for advanced users

### 🔄 Role Mapping for Contributors
| Existing Role   | ARX Contributor Type |
|------------------|----------------------|
| contractor       | object_minter        |
| school_staff     | building_uploader    |
| district_admin   | organizational_owner |
| arxos_support    | validator_auditor    |

---

## 3. Revenue Tracking & Payment System

### 💵 Current Revenue Streams
- API usage fees (external vendors)
- CMMS Pro accounts ($30/user/month)
- Future: building data sales, contractor service transaction fees

### 🧮 Categorization for Dividends
| Source                 | Dividend Eligible? | Notes                             |
|------------------------|--------------------|-----------------------------------|
| API Usage              | ✅                 | Counted as institutional access   |
| Data Downloads         | ✅                 | Key dividend pool source          |
| Contractor Services    | ✅                 | Only for on-platform engagements  |
| CMMS Subscription Fees | ❌ (Operational)    | Considered platform revenue       |

### 💳 Current Pricing Models
- Pro CMMS: $30/user/mo
- API data: $0.02/call
- Simulation access: Tiered ($10–$100/mo planned)

---

## 4. Database Migration Strategy

### 🛠️ Current DB
- PostgreSQL (w/ PostGIS extensions)
- Auth, users, buildings, assets, reputation

### 🔗 ARX DB Integration
- Add ARX-related tables to same PostgreSQL instance:
  - `wallets`, `arx_transactions`, `dividend_ledger`, `contributions`
- Use blockchain-indexed keys for ARX events
- Smart contract triggers sync to DB with off-chain indexer

### 🔄 Migration Strategy
- Add wallet address field to `users` table
- Backfill with auto-generated keys for existing users

---

## 5. Testing Infrastructure

### 🧪 Current Stack
- Go: native `testing` package
- Python (SVGX): `pytest`
- Frontend: `Playwright`, `Vitest`

### 🔍 Smart Contract Testing Plan
- Use `Hardhat` + `Chai` for smart contract tests
- Deploy smart contract test runner in **parallel** to main test pipeline
- Use `Ganache`/`Foundry` for local chain simulations
- Add blockchain test outputs to existing CI reports

---

## 6. Deployment Architecture

### ☁️ Current Stack
- Go backend (REST API) on DigitalOcean
- Python SVGX microservices
- PostgreSQL database
- HTMX frontend (HTML/X + Tailwind)

### 🚀 Blockchain Integration Plan
- Deploy smart contracts to:
  - Testnet (Polygon Mumbai / Sepolia)
  - Mainnet (Polygon, Avalanche, or Ethereum L2)
- Run blockchain indexer alongside existing backend
- Add Prometheus/Grafana dashboard for blockchain sync status
- Monitor smart contract events using webhooks + JSON-RPC polling

---

## 🔍 Specific Design Answers

### 🔢 Tokenomics: Base ARX Mint Value
- Start with 1.0 ARX for a fully validated standard object (complexity = 1.0)
- Multiply based on system complexity and validation fidelity

### 👛 Integration Architecture: Wallet Creation
- Auto-create wallet for each user upon login or onboarding
- Allow opt-out or external linking for power users

### 🔬 Testing: Smart Contracts
- Smart contract tests should run in **parallel** CI jobs
- Tagged as `blockchain` test suite

### 🔐 Security: User Auth & Wallets
- Current JWT auth stays intact
- Store wallet private keys **encrypted server-side** (for auto-minted users)
- Allow advanced users to export or bring their own wallets

---

## ✅ Summary

This document ensures the ARX system:
- Integrates cleanly with existing Arxos components
- Stays legally and financially compliant
- Maintains developer and contributor trust through transparency
- Enables rapid prototyping without isolating systems

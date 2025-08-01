
# ARX Hybrid Model: Open Currency with Equal Dividend Distribution

## 🌐 Overview

ARX is a freely tradable cryptocurrency issued through contributions to the Arxos ecosystem. It is minted only through verified work tied to specific `arxobject`s. All ARX holders receive equal dividend payouts as a percentage from all data sales and service transactions across the platform.

This model ensures contributors are rewarded for their work while enabling broad secondary market participation with equal dividend rights.

---

## 🔗 1. On-Chain Dividend Routing: Technical Model

### 🧱 Structure
Each `arxobject` has:
- A **unique hash ID**
- A **mint record** tied to contributor wallet(s)
- A **verification record** from secondary user approval

### 🔄 Smart Contracts

- `ARXToken`: Standard ERC-20 token
- `ArxMintRegistry`: Records the contributor and their associated `arxobject` hash on mint
- `RevenueRouter`: Routes incoming payments (data access/service txs) to the dividend pool
- `DividendVault`: Periodically distributes funds equally to all ARX holders

### 🔐 Key Enforcement Logic
- When ARX is minted, the contributor wallet is bound to the `arxobject` ID
- Secondary user verification is required for minting to proceed
- All platform revenue flows into a single dividend pool
- Dividend payout is distributed equally to all ARX holders regardless of ownership source

---

## 🎯 2. Maintaining Fungibility with Equal Dividend Rights

ARX remains fungible by:
- Ensuring all tokens are **interchangeable** for payment, access, and trade
- All holders receive **equal dividend rights** regardless of how they acquired their tokens
- No distinction between contributor-minted tokens and secondary market tokens

This preserves:
- 🔁 **Free market exchangeability**
- 🧾 **Tax/accounting simplicity**
- 💰 **Equal dividend participation for all holders**

---

## ⚖️ 3. Legal and Investor Viability

### ✅ Benefits
- Contributors are **workers**, not investors
- ARX holders are **currency participants**, not equity holders
- Dividends are framed as **platform revenue sharing**, not profit distributions
- Equal treatment of all token holders

### 🔍 Regulatory Mitigations
- Contributions mint tokens via **provable work**
- Revenue flows are **decentralized and usage-based**
- DAO can be established for platform-wide revenue (if needed)
- No speculative promise: token value derives from **utility + verified work**

---

## 🧩 Summary

| Feature | Description |
|--------|-------------|
| Minting | Only from work tied to `arxobject`s with secondary verification |
| Token | Fully fungible ERC-20 |
| Supply | Unlimited based on objects created |
| Dividends | Equal distribution to all ARX holders |
| Exchangeable | Yes — ARX trades freely on open markets |
| Governance | Optional DAO for treasury/protocol votes |
| Risk Mitigation | Clear separation of labor/reward vs investor/speculation |

---

## ✅ Next Steps

- [ ] Design `ArxMintRegistry` + object hash format
- [ ] Prototype `RevenueRouter` smart contract with equal dividend distribution
- [ ] Define dividend vault payout intervals + mechanisms
- [ ] Implement secondary user verification system
- [ ] Conduct legal review under SEC, EU MiCA, and commodity law

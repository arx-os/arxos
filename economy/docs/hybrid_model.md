
# BILT Hybrid Model: Open Currency with Equal Dividend Distribution

## 🎯 **Overview**

BILT is a freely tradable cryptocurrency issued through contributions to the Arxos ecosystem. It is minted only through verified work tied to specific `arxobject`s. All BILT holders receive equal dividend payouts as a percentage from all data sales and service transactions across the platform.

---

## 🏗️ **Core Architecture**

### **A. Object-Based Minting**
Each `arxobject` has:
- **Unique Hash**: Cryptographic identifier
- **Contributor Wallet**: Address that created the object
- **Validation Score**: ArxLogic AI validation (0.0 to 1.0)
- **Complexity Multiplier**: System type complexity factor
- **Mint Amount**: BILT tokens minted for this object

### **B. Smart Contract Layer**
- `BILTToken`: Standard ERC-20 token
- `ArxMintRegistry`: Records the contributor and their associated `arxobject` hash on mint
- `RevenueRouter`: Routes platform revenue to dividend pool
- `DividendVault`: Periodically distributes funds equally to all BILT holders

### **C. Dividend Distribution**
- When BILT is minted, the contributor wallet is bound to the `arxobject` ID
- Platform revenue from data sales and service transactions flows to dividend pool
- Dividend payout is distributed equally to all BILT holders regardless of ownership source
- No distinction between contributor-minted and secondary market tokens

---

## 💰 **Economic Model**

### **A. Fungibility with Attribution**
BILT remains fungible by:
- **Equal Dividend Rights**: All tokens receive same dividend percentage
- **Free Trading**: Tokens trade freely on open markets
- **No Ownership Tiers**: No special rights for contributor-minted tokens
- **Transparent Attribution**: Public record of which objects contributed to revenue

### **B. Legal Classification**
- BILT holders are **currency participants**, not equity holders
- Contributors are **workers earning for labor**
- Dividends are **platform revenue sharing**
- Clear separation from Arxos equity

---

## 🔄 **Operational Flow**

| Stage | Process | Outcome |
|-------|---------|---------|
| Contribution | User uploads building object | Object gets unique hash |
| Validation | ArxLogic AI + peer verification | Validation score assigned |
| Minting | Only from work tied to `arxobject`s with secondary verification | BILT minted to contributor |
| Revenue | Platform generates revenue from data/service sales | Funds flow to dividend pool |
| Dividends | Equal distribution to all BILT holders | Pro-rata payout to all holders |
| Exchangeable | Yes — BILT trades freely on open markets | Market-driven price discovery |

---

## 🛠️ **Implementation Requirements**

### **A. Smart Contract Development**
- [ ] Design `ArxMintRegistry` + object hash format
- [ ] Implement `BILTToken` with minting controls
- [ ] Create `RevenueRouter` for dividend distribution
- [ ] Deploy `DividendVault` for periodic payouts

### **B. Backend Integration**
- [ ] ArxLogic validation score integration
- [ ] Object hash generation and tracking
- [ ] Revenue attribution algorithms
- [ ] Dividend calculation engine

### **C. Legal Compliance**
- [ ] Worker classification documentation
- [ ] Tax treatment guidelines
- [ ] Regulatory compliance framework
- [ ] Terms of service and risk disclosure

---

## 🎯 **Benefits**

### **For Contributors**
- Immediate reward for quality work
- Ongoing dividends from platform success
- No discrimination based on contribution size

### **For Token Holders**
- Equal dividend rights regardless of source
- Free market trading
- Simple tax treatment

### **For Platform**
- Quality control through AI + verification
- Sustainable economics based on real usage
- Clear regulatory compliance

This hybrid model creates a fair and sustainable ecosystem where quality work is rewarded with both immediate tokens and ongoing platform revenue sharing, while maintaining equal rights for all token holders.

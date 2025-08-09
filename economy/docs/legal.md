# ARX Legal and Financial Architecture
### Version 1.0 — July 28, 2025

---

## 🎯 Objective

Establish a legally compliant and structurally sound financial and token architecture for ARX, the revenue-bearing token issued by Arxos. This document provides clear delineation between ARX and Arxos equity, outlines regulatory strategy, and instructs the software team on what constraints to implement in the system.

---

## 🧱 Legal Classifications

### ARX Token:
- **Type**: Registered Security Token (if dividend-bearing)
- **Structure**: Revenue-linked digital asset
- **Not Equity**: ARX does *not* represent ownership, voting rights, or IP stake in Arxos
- **Regulation**: Subject to U.S. Securities Law (likely under Reg D, Reg A+, or similar)

### Arxos Inc.:
- **Type**: Traditional C-Corp equity (Delaware or equivalent)
- **Shares**: Common and/or preferred stock
- **IPO Eligibility**: Maintained by structurally separating equity and token holders

---

## 🔐 Token Legal Structure

### 🔹 Summary:
> ARX is a non-voting, revenue-linked token that entitles holders to a pro-rata share of platform revenue *only* from building data sales and contractor service transactions.

### 🔹 Legal Language:
> "ARX tokens do not represent ownership of Arxos Inc., but rather a right to receive a proportionate share of revenue derived from verified infrastructure data sales and platform service transactions."

---

## 🔗 Token–Platform Relationship

| Component              | ARX Role                          | Equity Role              |
|------------------------|-----------------------------------|--------------------------|
| Ownership              | ❌ None                           | ✅ Yes                   |
| Voting Rights          | ❌ None                           | ✅ Yes                   |
| Dividend Right         | ✅ Platform revenue share         | ✅ Corporate profits     |
| Transferability        | ✅ Freely traded                  | ⚠️ Restricted pre-IPO   |
| Regulatory Filing      | ✅ Token-based (e.g. Reg A)       | ✅ SEC equity filings    |

---

## 💰 Revenue Participation Mechanism

- Smart contract or escrow distributes dividend to ARX holders.
- Revenue sourced only from:
  - Building data exports and insights
  - On-platform service transactions
- Percentage allocation governed by DAO or board resolution
- No profit sharing from Arxos equity, IP licensing, or VC funding

---

## ⚠️ Compliance Guidelines for Software Team

- Token Minting:
  - Must be tied to verified infrastructure contributions (arxobjects)
  - Cannot be "sold" directly by Arxos — only earned or exchanged

- Token Utility:
  - Usable for: fees, staking, governance (non-equity), premium access
  - Not valid for corporate voting, stockholder rights, or board decisions

- Token Transfer:
  - Freely tradable on licensed ATS (e.g., INX, tZERO)
  - Optional lockups or vesting can be implemented for early contributors

- Dividend Payout:
  - Only from protocol-defined revenue channels
  - Disbursed through audited smart contracts
  - Subject to KYC/AML and withholding obligations per jurisdiction

---

## ✅ Legal Separation Assurance

- Maintain two distinct ledgers:
  - **ARX Registry** (for token holders and dividend metadata)
  - **Equity Cap Table** (for stockholders and corporate governance)

- Two distinct disclosures:
  - ARX: Tokenomics, platform revenue, payout history
  - Arxos Equity: Company performance, financials, IP, legal risks

- Language audits and brand guardrails to prevent marketing confusion

---

## 📎 Additional Recommendations

- Consult securities legal counsel before public launch
- File necessary exemptions or registration with SEC
- Create ARX Terms of Service and Risk Disclosure Statement
- Draft Token Purchase Agreement for future investor sales

---

## 🧠 Strategic Benefits

- Enables hybrid participation model: contributors, investors, and builders
- Allows Arxos to grow independently and pursue IPO or equity funding
- Creates passive income path for early adopters while remaining legally compliant

---

## 📅 Version History

- 1.0 - Initial framework defining ARX as a registered revenue-sharing token, legally distinct from Arxos equity

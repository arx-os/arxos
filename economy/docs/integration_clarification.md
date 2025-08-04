# BILT Tokenomics & Infrastructure Integration — Design Clarifications

## 🎯 **Objective**

Clarify the integration points between BILT tokenomics and existing Arxos infrastructure components, ensuring seamless operation while maintaining legal compliance and technical robustness.

---

## 1. ArxLogic Integration Points

### **A. Validation Score Integration**
- ArxLogic currently calculates validation scores using:
  - Simulation pass rate (0.0 to 1.0)
  - AI accuracy rate (0.0 to 1.0) 
  - System completion score (0.0 to 1.0)
  - Error propagation score (0.0 to 1.0)

### **B. BILT Minting Integration**
- ArxLogic validation scores feed directly into BILT minting
- No changes needed to ArxLogic core functionality
- BILT minting is additive layer on top of existing validation

---

## 2. Role-Based Access Control (RBAC)

### **A. Existing Arxos Roles**
- Roles: `contractor`, `school_staff`, `district_admin`, `arxos_support`
- These roles already exist in Arxos Auth system
- No changes needed to existing role structure

### **B. BILT Contributor Types**
| Existing Role   | BILT Contributor Type |
|----------------|----------------------|
| contractor     | contributor          |
| school_staff   | validator            |
| district_admin | validator_auditor    |
| arxos_support  | validator_auditor    |

### **C. Integration Strategy**
- Map existing Arxos roles to BILT contributor types
- Maintain existing permissions and access controls
- Add BILT-specific permissions as needed

---

## 3. Database Integration

### **A. BILT DB Integration**
- Add BILT-related tables to same PostgreSQL instance:
- `wallets`, `bilt_transactions`, `dividend_ledger`, `contributions`
- Use blockchain-indexed keys for BILT events

### **B. Schema Compatibility**
- Existing Arxos tables remain unchanged
- BILT tables are additive, not modifying
- Shared user authentication and profiles

---

## 4. Revenue Attribution

### **A. Data Sales Attribution**
- When building data is sold, revenue flows to BILT dividend pool
- Attribution based on `arxobject` hashes that contributed to sale
- No changes to existing data sales process

### **B. Service Transaction Attribution**
- Contractor service fees contribute to BILT dividend pool
- Attribution based on service type and building context
- Maintains existing service transaction flow

---

## 5. Technical Implementation

### **A. Smart Contract Integration**
- BILT contracts deployed on same blockchain as Arxos
- Integration through web3.js/ethers.js libraries
- No changes to existing Arxos blockchain operations

### **B. API Integration**
- Add BILT endpoints to existing Arxos API
- Maintain existing API structure and authentication
- BILT endpoints follow same patterns as existing endpoints

---

## 6. Legal Compliance

### **A. Worker Classification**
- Contributors remain classified as workers
- BILT holders are currency participants
- Clear separation maintained between equity and tokens

### **B. Tax Treatment**
- Contributors report BILT as work income
- Holders report dividends as income
- No changes to existing Arxos tax structure

---

## 7. Tokenomics Parameters

### **A. Base BILT Mint Value**
- Start with 1.0 BILT for a fully validated standard object (complexity = 1.0)
- Adjustable through governance or admin controls
- Tied to validation score and complexity multiplier

### **B. Dividend Distribution**
- Monthly or quarterly distribution to all BILT holders
- Equal distribution regardless of token source
- Transparent and auditable process

---

## 8. Integration Benefits

This document ensures the BILT system:
- Integrates cleanly with existing Arxos components
- Maintains legal compliance and worker classification
- Preserves existing user experience and workflows
- Adds value without disrupting current operations


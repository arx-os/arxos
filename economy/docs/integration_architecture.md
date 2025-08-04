# BILT Integration Architecture

## 🎯 **Overview**

This document defines the integration architecture for BILT cryptocurrency functionality with the existing Arxos platform, ensuring seamless operation while maintaining security, performance, and user experience.

---

## 🏗️ **Integration Strategy**

### **1. User Authentication & Wallet Integration**

#### **A. User Profile Extension with Legal Compliance**
```sql
-- Extend existing users table
ALTER TABLE users ADD COLUMN wallet_address VARCHAR(42) UNIQUE;
ALTER TABLE users ADD COLUMN wallet_encrypted_key TEXT;
ALTER TABLE users ADD COLUMN wallet_type VARCHAR(20) DEFAULT 'auto_generated';
ALTER TABLE users ADD COLUMN bilt_balance DECIMAL(20,8) DEFAULT 0.0;
ALTER TABLE users ADD COLUMN last_dividend_claim TIMESTAMP;

-- Legal compliance fields
ALTER TABLE users ADD COLUMN kyc_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN aml_cleared BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN jurisdiction VARCHAR(10);
ALTER TABLE users ADD COLUMN is_equity_holder BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN regulatory_status VARCHAR(50) DEFAULT 'pending';
```

#### **B. Wallet Management Service**
```go
// bilt-backend/services/wallet/wallet_service.go
type WalletService struct {
    db          *sql.DB
    crypto      *CryptoService
    blockchain  *BlockchainService
    logger      *zap.Logger
}

type WalletInfo struct {
    UserID            string    `json:"user_id"`
    WalletAddress     string    `json:"wallet_address"`
    BILTBalance       float64   `json:"bilt_balance"`
    WalletType        string    `json:"wallet_type"`
    KYCVerified       bool      `json:"kyc_verified"`
    AMLCleared        bool      `json:"aml_cleared"`
    Jurisdiction      string    `json:"jurisdiction"`
    IsEquityHolder    bool      `json:"is_equity_holder"`
    RegulatoryStatus  string    `json:"regulatory_status"`
    CreatedAt         time.Time `json:"created_at"`
}

func (ws *WalletService) CreateWalletForUser(userID string) (*WalletInfo, error) {
    // Generate new wallet address
    walletAddress, privateKey := ws.crypto.GenerateWallet()
    
    // Encrypt private key for storage
    encryptedKey := ws.crypto.EncryptPrivateKey(privateKey, userID)
    
    // Store in database
    wallet := &WalletInfo{
        UserID:        userID,
        WalletAddress: walletAddress,
        BILTBalance:   0.0,
        WalletType:    "auto_generated",
        CreatedAt:     time.Now(),
    }
    
    err := ws.db.Exec(`
        UPDATE users 
        SET wallet_address = ?, wallet_encrypted_key = ?, updated_at = NOW()
        WHERE id = ?
    `, walletAddress, encryptedKey, userID)
    
    return wallet, err
}

func (ws *WalletService) GetUserWallet(userID string) (*WalletInfo, error) {
    var wallet WalletInfo
    err := ws.db.QueryRow(`
        SELECT id, wallet_address, bilt_balance, wallet_type, created_at
        FROM users 
        WHERE id = ?
    `, userID).Scan(&wallet.UserID, &wallet.WalletAddress, &wallet.BILTBalance, &wallet.WalletType, &wallet.CreatedAt)
    
    return &wallet, err
}
```

#### **C. Role-Based BILT Integration**
```go
// bilt-backend/services/bilt/role_mapper.go
type BILTRoleMapper struct {
    db *sql.DB
}

var roleMapping = map[string]string{
    "contractor":      "object_minter",
    "school_staff":    "building_uploader", 
    "district_admin":  "organizational_owner",
    "arxos_support":   "validator_auditor",
}

func (rm *BILTRoleMapper) GetBILTContributorType(userRole string) string {
    return roleMapping[userRole]
}

func (rm *BILTRoleMapper) GetMintingPermissions(userRole string) []string {
    permissions := map[string][]string{
        "object_minter":        {"mint_objects", "verify_objects"},
        "building_uploader":    {"upload_buildings", "mint_objects"},
        "organizational_owner": {"mint_objects", "verify_objects", "manage_organization"},
        "validator_auditor":    {"verify_objects", "audit_contributions"},
    }
    
    contributorType := rm.GetBILTContributorType(userRole)
    return permissions[contributorType]
}
```

### **2. BiltLogic Integration Points**

#### **A. Validation Score Integration**
```python
# bilt-backend/services/biltlogic/bilt_integration.py
from bilt_logic import BiltLogicValidator
from bilt_tokenomics import calculate_bilt_mint, calculate_validation_score

class BiltLogicBILTIntegration:
    def __init__(self):
        self.bilt_logic = BiltLogicValidator()
        self.tokenomics = BILTTokenomicsCalculator()
    
    async def validate_and_calculate_mint(self, contribution_data: dict) -> dict:
        """Validate contribution using BiltLogic and calculate BILT mint amount."""
        
        # Run BiltLogic validation
        validation_result = await self.bilt_logic.validate_contribution(contribution_data)
        
        # Extract validation metrics
        validation_metrics = {
            'simulation_pass_rate': validation_result.simulation_pass_rate,
            'ai_accuracy_rate': validation_result.ai_accuracy_rate,
            'system_completion_score': validation_result.system_completion_score,
            'error_propagation_score': validation_result.error_propagation_score
        }
        
        # Calculate validation score
        validation_score = calculate_validation_score(**validation_metrics)
        
        # Get complexity multiplier
        system_type = contribution_data.get('system_type', 'electrical')
        complexity_multiplier = self.tokenomics.get_complexity_multiplier(system_type)
        
        # Calculate BILT mint amount
        bilt_mint_amount = calculate_bilt_mint(
            validation_score=validation_score,
            complexity_multiplier=complexity_multiplier
        )
        
        return {
            'validation_result': validation_result,
            'validation_score': validation_score,
            'complexity_multiplier': complexity_multiplier,
            'bilt_mint_amount': bilt_mint_amount,
            'system_type': system_type
        }
```

#### **B. BiltLogic Event Integration**
```python
# bilt-backend/services/biltlogic/event_handler.py
class BiltLogicEventHandler:
    def __init__(self):
        self.bilt_service = BILTService()
        self.notification_service = NotificationService()
    
    async def handle_validation_complete(self, event: ValidationCompleteEvent):
        """Handle BiltLogic validation completion and trigger BILT minting."""
        
        # Calculate BILT mint amount
        mint_calculation = await self.bilt_service.calculate_mint_amount(event.contribution_data)
        
        if mint_calculation['bilt_mint_amount'] > 0:
            # Mint BILT tokens
            mint_result = await self.bilt_service.mint_tokens(
                user_id=event.user_id,
                bilt_amount=mint_calculation['bilt_mint_amount'],
                contribution_hash=event.contribution_hash,
                validation_score=mint_calculation['validation_score']
            )
            
            # Send notification to user
            await self.notification_service.send_mint_notification(
                user_id=event.user_id,
                bilt_amount=mint_calculation['bilt_mint_amount'],
                validation_score=mint_calculation['validation_score']
            )
```

### **3. Legal Compliance Integration**

#### **A. Compliance Service**
```go
// arx-backend/services/compliance/compliance_service.go
type ComplianceService struct {
    db          *sql.DB
    kycProvider *KYCProvider
    amlProvider *AMLProvider
    logger      *zap.Logger
}

type ComplianceStatus struct {
    UserID           string    `json:"user_id"`
    KYCVerified      bool      `json:"kyc_verified"`
    AMLCleared       bool      `json:"aml_cleared"`
    Jurisdiction     string    `json:"jurisdiction"`
    IsEquityHolder   bool      `json:"is_equity_holder"`
    RegulatoryStatus string    `json:"regulatory_status"`
    LastVerified     time.Time `json:"last_verified"`
}

func (cs *ComplianceService) VerifyKYC(userID string, jurisdiction string) error {
    // Integrate with KYC provider
    kycResult, err := cs.kycProvider.VerifyUser(userID, jurisdiction)
    if err != nil {
        return err
    }
    
    // Update database
    _, err = cs.db.Exec(`
        UPDATE users 
        SET kyc_verified = ?, jurisdiction = ?, regulatory_status = 'verified'
        WHERE id = ?
    `, kycResult.Verified, jurisdiction, userID)
    
    return err
}

func (cs *ComplianceService) ClearAML(userID string) error {
    // Integrate with AML provider
    amlResult, err := cs.amlProvider.CheckUser(userID)
    if err != nil {
        return err
    }
    
    // Update database
    _, err = cs.db.Exec(`
        UPDATE users 
        SET aml_cleared = ?, regulatory_status = 'cleared'
        WHERE id = ?
    `, amlResult.Cleared, userID)
    
    return err
}

func (cs *ComplianceService) RegisterEquityHolder(userID string) error {
    // Mark user as equity holder (cannot participate in token governance)
    _, err := cs.db.Exec(`
        UPDATE users 
        SET is_equity_holder = true, regulatory_status = 'equity_holder'
        WHERE id = ?
    `, userID)
    
    return err
}
```

### **4. Database Integration**

#### **A. BILT Tables Schema**
```sql
-- BILT Wallets table
CREATE TABLE bilt_wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    wallet_address VARCHAR(42) UNIQUE NOT NULL,
    encrypted_private_key TEXT,
    wallet_type VARCHAR(20) DEFAULT 'auto_generated',
    bilt_balance DECIMAL(20,8) DEFAULT 0.0,
    last_dividend_claim TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- BILT Transactions table
CREATE TABLE bilt_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    transaction_hash VARCHAR(66) UNIQUE,
    transaction_type VARCHAR(50) NOT NULL,
    bilt_amount DECIMAL(20,8) NOT NULL,
    contribution_hash VARCHAR(64),
    validation_score DECIMAL(5,4),
    complexity_multiplier DECIMAL(5,4),
    system_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    gas_used INTEGER,
    gas_price DECIMAL(20,8),
    block_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- BILT Contributions table
CREATE TABLE bilt_contributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    contribution_hash VARCHAR(64) UNIQUE NOT NULL,
    object_type VARCHAR(100) NOT NULL,
    system_type VARCHAR(50) NOT NULL,
    validation_score DECIMAL(5,4) NOT NULL,
    complexity_multiplier DECIMAL(5,4) NOT NULL,
    bilt_minted DECIMAL(20,8) NOT NULL,
    verification_status VARCHAR(20) DEFAULT 'pending',
    secondary_verifier_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP
);

-- BILT Dividend Distributions table
CREATE TABLE bilt_dividend_distributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distribution_period VARCHAR(20) NOT NULL,
    total_revenue_pool DECIMAL(20,2) NOT NULL,
    dividend_per_token DECIMAL(20,8) NOT NULL,
    total_bilt_supply DECIMAL(20,8) NOT NULL,
    distributed_amount DECIMAL(20,2) NOT NULL,
    gas_costs DECIMAL(20,2) DEFAULT 0.0,
    efficiency_rate DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- BILT User Dividends table
CREATE TABLE bilt_user_dividends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    distribution_id UUID REFERENCES bilt_dividend_distributions(id),
    bilt_balance_at_distribution DECIMAL(20,8) NOT NULL,
    dividend_amount DECIMAL(20,2) NOT NULL,
    transaction_hash VARCHAR(66),
    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **B. Database Migration Strategy**
```sql
-- Migration: Add BILT fields to existing users table
-- 001_add_bilt_to_users.sql

-- Add BILT-related columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_address VARCHAR(42);
ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_encrypted_key TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_type VARCHAR(20) DEFAULT 'auto_generated';
ALTER TABLE users ADD COLUMN IF NOT EXISTS bilt_balance DECIMAL(20,8) DEFAULT 0.0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_dividend_claim TIMESTAMP;

-- Create indexes for BILT queries
CREATE INDEX IF NOT EXISTS idx_users_wallet_address ON users(wallet_address);
CREATE INDEX IF NOT EXISTS idx_users_bilt_balance ON users(bilt_balance);
CREATE INDEX IF NOT EXISTS idx_users_last_dividend_claim ON users(last_dividend_claim);

-- Backfill existing users with auto-generated wallets
-- This will be done programmatically during the migration process
```

### **4. API Integration**

#### **A. REST API Endpoints**
```go
// bilt-backend/handlers/bilt_handlers.go
type BILTHandler struct {
    walletService    *WalletService
    biltService       *BILTService
    validationService *BiltLogicBILTIntegration
    db               *sql.DB
}

// GET /api/bilt/wallet
func (h *BILTHandler) GetUserWallet(w http.ResponseWriter, r *http.Request) {
    userID := getUserIDFromContext(r.Context())
    
    wallet, err := h.walletService.GetUserWallet(userID)
    if err != nil {
        http.Error(w, "Failed to get wallet", http.StatusInternalServerError)
        return
    }
    
    json.NewEncoder(w).Encode(wallet)
}

// POST /api/bilt/contribute
func (h *BILTHandler) SubmitContribution(w http.ResponseWriter, r *http.Request) {
    var contribution ContributionSubmission
    if err := json.NewDecoder(r.Body).Decode(&contribution); err != nil {
        http.Error(w, "Invalid request body", http.StatusBadRequest)
        return
    }
    
    userID := getUserIDFromContext(r.Context())
    
    // Validate contribution using BiltLogic
    validationResult, err := h.validationService.ValidateAndCalculateMint(contribution)
    if err != nil {
        http.Error(w, "Validation failed", http.StatusBadRequest)
        return
    }
    
    // Mint BILT tokens
    mintResult, err := h.biltService.MintTokens(userID, validationResult)
    if err != nil {
        http.Error(w, "Minting failed", http.StatusInternalServerError)
        return
    }
    
    json.NewEncoder(w).Encode(mintResult)
}

// GET /api/bilt/dividends
func (h *BILTHandler) GetUserDividends(w http.ResponseWriter, r *http.Request) {
    userID := getUserIDFromContext(r.Context())
    
    dividends, err := h.biltService.GetUserDividends(userID)
    if err != nil {
        http.Error(w, "Failed to get dividends", http.StatusInternalServerError)
        return
    }
    
    json.NewEncoder(w).Encode(dividends)
}

// POST /api/bilt/verify
func (h *BILTHandler) VerifyContribution(w http.ResponseWriter, r *http.Request) {
    var verification VerificationRequest
    if err := json.NewDecoder(r.Body).Decode(&verification); err != nil {
        http.Error(w, "Invalid request body", http.StatusBadRequest)
        return
    }
    
    userID := getUserIDFromContext(r.Context())
    
    // Perform secondary verification
    verificationResult, err := h.biltService.VerifyContribution(userID, verification)
    if err != nil {
        http.Error(w, "Verification failed", http.StatusBadRequest)
        return
    }
    
    json.NewEncoder(w).Encode(verificationResult)
}
```

#### **B. WebSocket Integration for Real-time Updates**
```go
// bilt-backend/services/websocket/bilt_websocket.go
type BILTWebSocketHandler struct {
    hub *WebSocketHub
    biltService *BILTService
}

func (h *BILTWebSocketHandler) HandleBILTUpdates(conn *WebSocketConnection) {
    // Subscribe to BILT events
    events := make(chan BILTEvent)
    h.biltService.SubscribeToEvents(conn.UserID, events)
    
    for event := range events {
        conn.SendJSON(event)
    }
}

type BILTEvent struct {
    Type      string      `json:"type"`
    UserID    string      `json:"user_id"`
    Data      interface{} `json:"data"`
    Timestamp time.Time   `json:"timestamp"`
}
```

### **5. Frontend Integration**

#### **A. HTMX Integration**
```html
<!-- bilt-web-frontend/templates/bilt/wallet.html -->
<div class="bilt-wallet-container">
    <div class="wallet-header">
        <h2>BILT Wallet</h2>
        <div class="wallet-address">{{ .WalletAddress }}</div>
    </div>
    
    <div class="wallet-balance">
        <span class="balance-label">BILT Balance:</span>
        <span class="balance-amount">{{ .BILTBalance }}</span>
    </div>
    
    <div class="wallet-actions">
        <button hx-post="/api/arx/claim-dividends" 
                hx-target="#dividend-status"
                class="btn btn-primary">
            Claim Dividends
        </button>
        
        <button hx-get="/api/arx/transactions" 
                hx-target="#transaction-history"
                class="btn btn-secondary">
            View History
        </button>
    </div>
    
    <div id="dividend-status"></div>
    <div id="transaction-history"></div>
</div>
```

#### **B. JavaScript Integration**
```javascript
// arx-web-frontend/static/js/arx-wallet.js
class BILTWallet {
    constructor() {
        this.walletAddress = null;
        this.balance = 0;
        this.initialize();
    }
    
    async initialize() {
        await this.loadWalletInfo();
        this.setupWebSocket();
        this.startBalanceUpdates();
    }
    
    async loadWalletInfo() {
        const response = await fetch('/api/arx/wallet');
        const wallet = await response.json();
        
        this.walletAddress = wallet.wallet_address;
        this.balance = wallet.arx_balance;
        this.updateUI();
    }
    
    setupWebSocket() {
        const ws = new WebSocket(`ws://${window.location.host}/ws/arx`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleBILTEvent(data);
        };
    }
    
    handleBILTEvent(event) {
        switch (event.type) {
            case 'mint_complete':
                this.balance += event.data.bilt_amount;
                this.showNotification(`Minted ${event.data.bilt_amount} BILT!`);
                break;
                
            case 'dividend_distributed':
                this.showNotification(`Dividend distributed: ${event.data.amount} BILT`);
                break;
        }
        
        this.updateUI();
    }
    
    updateUI() {
        document.getElementById('bilt-balance').textContent = this.balance.toFixed(8);
        document.getElementById('wallet-address').textContent = this.walletAddress;
    }
    
    showNotification(message) {
        // Show toast notification
        const toast = document.createElement('div');
        toast.className = 'toast toast-success';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 3000);
    }
}

// Initialize BILT wallet
document.addEventListener('DOMContentLoaded', () => {
    new BILTWallet();
});
```

### **6. Monitoring & Observability**

#### **A. Prometheus Metrics**
```go
// bilt-backend/metrics/bilt_metrics.go
type BILTMetrics struct {
    totalSupply        prometheus.Gauge
    totalMinted        prometheus.Counter
    totalDividends     prometheus.Counter
    activeWallets      prometheus.Gauge
    validationScores   prometheus.Histogram
    mintingDuration    prometheus.Histogram
}

func NewBILTMetrics() *BILTMetrics {
    return &BILTMetrics{
        totalSupply: prometheus.NewGauge(prometheus.GaugeOpts{
            Name: "bilt_total_supply",
            Help: "Total BILT supply",
        }),
        totalMinted: prometheus.NewCounter(prometheus.CounterOpts{
            Name: "bilt_total_minted",
            Help: "Total BILT minted",
        }),
        totalDividends: prometheus.NewCounter(prometheus.CounterOpts{
            Name: "bilt_total_dividends",
            Help: "Total dividends distributed",
        }),
        activeWallets: prometheus.NewGauge(prometheus.GaugeOpts{
            Name: "bilt_active_wallets",
            Help: "Number of active BILT wallets",
        }),
        validationScores: prometheus.NewHistogram(prometheus.HistogramOpts{
            Name: "bilt_validation_scores",
            Help: "Distribution of validation scores",
            Buckets: prometheus.LinearBuckets(0, 0.1, 11),
        }),
        mintingDuration: prometheus.NewHistogram(prometheus.HistogramOpts{
            Name: "bilt_minting_duration_seconds",
            Help: "Time taken to mint BILT tokens",
            Buckets: prometheus.ExponentialBuckets(0.1, 2, 10),
        }),
    }
}
```

#### **B. Grafana Dashboard**
```json
{
  "dashboard": {
    "title": "BILT Token Metrics",
    "panels": [
      {
        "title": "Total BILT Supply",
        "type": "stat",
        "targets": [
          {
            "expr": "bilt_total_supply",
            "legendFormat": "Total Supply"
          }
        ]
      },
      {
        "title": "BILT Minting Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(bilt_total_minted[5m])",
            "legendFormat": "Minting Rate"
          }
        ]
      },
      {
        "title": "Validation Score Distribution",
        "type": "histogram",
        "targets": [
          {
            "expr": "bilt_validation_scores_bucket",
            "legendFormat": "Validation Scores"
          }
        ]
      }
    ]
  }
}
```

---

## ✅ **Integration Checklist**

### **Pre-Integration**
- [ ] Database schema migration scripts created
- [ ] ArxLogic integration points defined
- [ ] User authentication flow updated
- [ ] API endpoints designed and documented
- [ ] Frontend components created
- [ ] Monitoring metrics defined

### **Integration Testing**
- [ ] Wallet creation for existing users
- [ ] ArxLogic validation integration
- [ ] BILT minting flow end-to-end
- [ ] Dividend distribution testing
- [ ] Real-time updates via WebSocket
- [ ] Error handling and rollback procedures

### **Post-Integration**
- [ ] Performance monitoring active
- [ ] Security audit completed
- [ ] User documentation updated
- [ ] Support team trained
- [ ] Backup and recovery procedures tested

This integration architecture ensures BILT functionality seamlessly integrates with the existing Arxos platform while maintaining security, performance, and user experience standards. 
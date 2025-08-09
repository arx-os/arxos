# ARX Integration Architecture

## 🎯 **Overview**

This document defines the integration architecture for ARX cryptocurrency functionality with the existing Arxos platform, ensuring seamless operation while maintaining security, performance, and user experience.

---

## 🏗️ **Integration Strategy**

### **1. User Authentication & Wallet Integration**

#### **A. User Profile Extension with Legal Compliance**
```sql
-- Extend existing users table
ALTER TABLE users ADD COLUMN wallet_address VARCHAR(42) UNIQUE;
ALTER TABLE users ADD COLUMN wallet_encrypted_key TEXT;
ALTER TABLE users ADD COLUMN wallet_type VARCHAR(20) DEFAULT 'auto_generated';
ALTER TABLE users ADD COLUMN arx_balance DECIMAL(20,8) DEFAULT 0.0;
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
// arx-backend/services/wallet/wallet_service.go
type WalletService struct {
    db          *sql.DB
    crypto      *CryptoService
    blockchain  *BlockchainService
    logger      *zap.Logger
}

type WalletInfo struct {
    UserID            string    `json:"user_id"`
    WalletAddress     string    `json:"wallet_address"`
    ARXBalance        float64   `json:"arx_balance"`
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
        ARXBalance:    0.0,
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
        SELECT id, wallet_address, arx_balance, wallet_type, created_at
        FROM users
        WHERE id = ?
    `, userID).Scan(&wallet.UserID, &wallet.WalletAddress, &wallet.ARXBalance, &wallet.WalletType, &wallet.CreatedAt)

    return &wallet, err
}
```

#### **C. Role-Based ARX Integration**
```go
// arx-backend/services/arx/role_mapper.go
type ARXRoleMapper struct {
    db *sql.DB
}

var roleMapping = map[string]string{
    "contractor":      "object_minter",
    "school_staff":    "building_uploader",
    "district_admin":  "organizational_owner",
    "arxos_support":   "validator_auditor",
}

func (rm *ARXRoleMapper) GetARXContributorType(userRole string) string {
    return roleMapping[userRole]
}

func (rm *ARXRoleMapper) GetMintingPermissions(userRole string) []string {
    permissions := map[string][]string{
        "object_minter":        {"mint_objects", "verify_objects"},
        "building_uploader":    {"upload_buildings", "mint_objects"},
        "organizational_owner": {"mint_objects", "verify_objects", "manage_organization"},
        "validator_auditor":    {"verify_objects", "audit_contributions"},
    }

    contributorType := rm.GetARXContributorType(userRole)
    return permissions[contributorType]
}
```

### **2. ArxLogic Integration Points**

#### **A. Validation Score Integration**
```python
# arx-backend/services/arxlogic/arx_integration.py
from arx_logic import ArxLogicValidator
from arx_tokenomics import calculate_arx_mint, calculate_validation_score

class ArxLogicARXIntegration:
    def __init__(self):
        self.arx_logic = ArxLogicValidator()
        self.tokenomics = ARXTokenomicsCalculator()

    async def validate_and_calculate_mint(self, contribution_data: dict) -> dict:
        """Validate contribution using ArxLogic and calculate ARX mint amount."""

        # Run ArxLogic validation
        validation_result = await self.arx_logic.validate_contribution(contribution_data)

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

        # Calculate ARX mint amount
        arx_mint_amount = calculate_arx_mint(
            validation_score=validation_score,
            complexity_multiplier=complexity_multiplier
        )

        return {
            'validation_result': validation_result,
            'validation_score': validation_score,
            'complexity_multiplier': complexity_multiplier,
            'arx_mint_amount': arx_mint_amount,
            'system_type': system_type
        }
```

#### **B. ArxLogic Event Integration**
```python
# arx-backend/services/arxlogic/event_handler.py
class ArxLogicEventHandler:
    def __init__(self):
        self.arx_service = ARXService()
        self.notification_service = NotificationService()

    async def handle_validation_complete(self, event: ValidationCompleteEvent):
        """Handle ArxLogic validation completion and trigger ARX minting."""

        # Calculate ARX mint amount
        mint_calculation = await self.arx_service.calculate_mint_amount(event.contribution_data)

        if mint_calculation['arx_mint_amount'] > 0:
            # Mint ARX tokens
            mint_result = await self.arx_service.mint_tokens(
                user_id=event.user_id,
                arx_amount=mint_calculation['arx_mint_amount'],
                contribution_hash=event.contribution_hash,
                validation_score=mint_calculation['validation_score']
            )

            # Send notification to user
            await self.notification_service.send_mint_notification(
                user_id=event.user_id,
                arx_amount=mint_calculation['arx_mint_amount'],
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

#### **A. ARX Tables Schema**
```sql
-- ARX Wallets table
CREATE TABLE arx_wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    wallet_address VARCHAR(42) UNIQUE NOT NULL,
    encrypted_private_key TEXT,
    wallet_type VARCHAR(20) DEFAULT 'auto_generated',
    arx_balance DECIMAL(20,8) DEFAULT 0.0,
    last_dividend_claim TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ARX Transactions table
CREATE TABLE arx_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    transaction_hash VARCHAR(66) UNIQUE,
    transaction_type VARCHAR(50) NOT NULL,
    arx_amount DECIMAL(20,8) NOT NULL,
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

-- ARX Contributions table
CREATE TABLE arx_contributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    contribution_hash VARCHAR(64) UNIQUE NOT NULL,
    object_type VARCHAR(100) NOT NULL,
    system_type VARCHAR(50) NOT NULL,
    validation_score DECIMAL(5,4) NOT NULL,
    complexity_multiplier DECIMAL(5,4) NOT NULL,
    arx_minted DECIMAL(20,8) NOT NULL,
    verification_status VARCHAR(20) DEFAULT 'pending',
    secondary_verifier_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP
);

-- ARX Dividend Distributions table
CREATE TABLE arx_dividend_distributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    distribution_period VARCHAR(20) NOT NULL,
    total_revenue_pool DECIMAL(20,2) NOT NULL,
    dividend_per_token DECIMAL(20,8) NOT NULL,
    total_arx_supply DECIMAL(20,8) NOT NULL,
    distributed_amount DECIMAL(20,2) NOT NULL,
    gas_costs DECIMAL(20,2) DEFAULT 0.0,
    efficiency_rate DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ARX User Dividends table
CREATE TABLE arx_user_dividends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    distribution_id UUID REFERENCES arx_dividend_distributions(id),
    arx_balance_at_distribution DECIMAL(20,8) NOT NULL,
    dividend_amount DECIMAL(20,2) NOT NULL,
    transaction_hash VARCHAR(66),
    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **B. Database Migration Strategy**
```sql
-- Migration: Add ARX fields to existing users table
-- 001_add_arx_to_users.sql

-- Add ARX-related columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_address VARCHAR(42);
ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_encrypted_key TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_type VARCHAR(20) DEFAULT 'auto_generated';
ALTER TABLE users ADD COLUMN IF NOT EXISTS arx_balance DECIMAL(20,8) DEFAULT 0.0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_dividend_claim TIMESTAMP;

-- Create indexes for ARX queries
CREATE INDEX IF NOT EXISTS idx_users_wallet_address ON users(wallet_address);
CREATE INDEX IF NOT EXISTS idx_users_arx_balance ON users(arx_balance);
CREATE INDEX IF NOT EXISTS idx_users_last_dividend_claim ON users(last_dividend_claim);

-- Backfill existing users with auto-generated wallets
-- This will be done programmatically during the migration process
```

### **4. API Integration**

#### **A. REST API Endpoints**
```go
// arx-backend/handlers/arx_handlers.go
type ARXHandler struct {
    walletService    *WalletService
    arxService       *ARXService
    validationService *ArxLogicARXIntegration
    db               *sql.DB
}

// GET /api/arx/wallet
func (h *ARXHandler) GetUserWallet(w http.ResponseWriter, r *http.Request) {
    userID := getUserIDFromContext(r.Context())

    wallet, err := h.walletService.GetUserWallet(userID)
    if err != nil {
        http.Error(w, "Failed to get wallet", http.StatusInternalServerError)
        return
    }

    json.NewEncoder(w).Encode(wallet)
}

// POST /api/arx/contribute
func (h *ARXHandler) SubmitContribution(w http.ResponseWriter, r *http.Request) {
    var contribution ContributionSubmission
    if err := json.NewDecoder(r.Body).Decode(&contribution); err != nil {
        http.Error(w, "Invalid request body", http.StatusBadRequest)
        return
    }

    userID := getUserIDFromContext(r.Context())

    // Validate contribution using ArxLogic
    validationResult, err := h.validationService.ValidateAndCalculateMint(contribution)
    if err != nil {
        http.Error(w, "Validation failed", http.StatusBadRequest)
        return
    }

    // Mint ARX tokens
    mintResult, err := h.arxService.MintTokens(userID, validationResult)
    if err != nil {
        http.Error(w, "Minting failed", http.StatusInternalServerError)
        return
    }

    json.NewEncoder(w).Encode(mintResult)
}

// GET /api/arx/dividends
func (h *ARXHandler) GetUserDividends(w http.ResponseWriter, r *http.Request) {
    userID := getUserIDFromContext(r.Context())

    dividends, err := h.arxService.GetUserDividends(userID)
    if err != nil {
        http.Error(w, "Failed to get dividends", http.StatusInternalServerError)
        return
    }

    json.NewEncoder(w).Encode(dividends)
}

// POST /api/arx/verify
func (h *ARXHandler) VerifyContribution(w http.ResponseWriter, r *http.Request) {
    var verification VerificationRequest
    if err := json.NewDecoder(r.Body).Decode(&verification); err != nil {
        http.Error(w, "Invalid request body", http.StatusBadRequest)
        return
    }

    userID := getUserIDFromContext(r.Context())

    // Perform secondary verification
    verificationResult, err := h.arxService.VerifyContribution(userID, verification)
    if err != nil {
        http.Error(w, "Verification failed", http.StatusBadRequest)
        return
    }

    json.NewEncoder(w).Encode(verificationResult)
}
```

#### **B. WebSocket Integration for Real-time Updates**
```go
// arx-backend/services/websocket/arx_websocket.go
type ARXWebSocketHandler struct {
    hub *WebSocketHub
    arxService *ARXService
}

func (h *ARXWebSocketHandler) HandleARXUpdates(conn *WebSocketConnection) {
    // Subscribe to ARX events
    events := make(chan ARXEvent)
    h.arxService.SubscribeToEvents(conn.UserID, events)

    for event := range events {
        conn.SendJSON(event)
    }
}

type ARXEvent struct {
    Type      string      `json:"type"`
    UserID    string      `json:"user_id"`
    Data      interface{} `json:"data"`
    Timestamp time.Time   `json:"timestamp"`
}
```

### **5. Frontend Integration**

#### **A. HTMX Integration**
```html
<!-- arx-web-frontend/templates/arx/wallet.html -->
<div class="arx-wallet-container">
    <div class="wallet-header">
        <h2>ARX Wallet</h2>
        <div class="wallet-address">{{ .WalletAddress }}</div>
    </div>

    <div class="wallet-balance">
        <span class="balance-label">ARX Balance:</span>
        <span class="balance-amount">{{ .ARXBalance }}</span>
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
class ARXWallet {
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
            this.handleARXEvent(data);
        };
    }

    handleARXEvent(event) {
        switch (event.type) {
            case 'mint_complete':
                this.balance += event.data.arx_amount;
                this.showNotification(`Minted ${event.data.arx_amount} ARX!`);
                break;

            case 'dividend_distributed':
                this.showNotification(`Dividend distributed: ${event.data.amount} ARX`);
                break;
        }

        this.updateUI();
    }

    updateUI() {
        document.getElementById('arx-balance').textContent = this.balance.toFixed(8);
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

// Initialize ARX wallet
document.addEventListener('DOMContentLoaded', () => {
    new ARXWallet();
});
```

### **6. Monitoring & Observability**

#### **A. Prometheus Metrics**
```go
// arx-backend/metrics/arx_metrics.go
type ARXMetrics struct {
    totalSupply        prometheus.Gauge
    totalMinted        prometheus.Counter
    totalDividends     prometheus.Counter
    activeWallets      prometheus.Gauge
    validationScores   prometheus.Histogram
    mintingDuration    prometheus.Histogram
}

func NewARXMetrics() *ARXMetrics {
    return &ARXMetrics{
        totalSupply: prometheus.NewGauge(prometheus.GaugeOpts{
            Name: "arx_total_supply",
            Help: "Total ARX supply",
        }),
        totalMinted: prometheus.NewCounter(prometheus.CounterOpts{
            Name: "arx_total_minted",
            Help: "Total ARX minted",
        }),
        totalDividends: prometheus.NewCounter(prometheus.CounterOpts{
            Name: "arx_total_dividends",
            Help: "Total dividends distributed",
        }),
        activeWallets: prometheus.NewGauge(prometheus.GaugeOpts{
            Name: "arx_active_wallets",
            Help: "Number of active ARX wallets",
        }),
        validationScores: prometheus.NewHistogram(prometheus.HistogramOpts{
            Name: "arx_validation_scores",
            Help: "Distribution of validation scores",
            Buckets: prometheus.LinearBuckets(0, 0.1, 11),
        }),
        mintingDuration: prometheus.NewHistogram(prometheus.HistogramOpts{
            Name: "arx_minting_duration_seconds",
            Help: "Time taken to mint ARX tokens",
            Buckets: prometheus.ExponentialBuckets(0.1, 2, 10),
        }),
    }
}
```

#### **B. Grafana Dashboard**
```json
{
  "dashboard": {
    "title": "ARX Token Metrics",
    "panels": [
      {
        "title": "Total ARX Supply",
        "type": "stat",
        "targets": [
          {
            "expr": "arx_total_supply",
            "legendFormat": "Total Supply"
          }
        ]
      },
      {
        "title": "ARX Minting Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(arx_total_minted[5m])",
            "legendFormat": "Minting Rate"
          }
        ]
      },
      {
        "title": "Validation Score Distribution",
        "type": "histogram",
        "targets": [
          {
            "expr": "arx_validation_scores_bucket",
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
- [ ] ARX minting flow end-to-end
- [ ] Dividend distribution testing
- [ ] Real-time updates via WebSocket
- [ ] Error handling and rollback procedures

### **Post-Integration**
- [ ] Performance monitoring active
- [ ] Security audit completed
- [ ] User documentation updated
- [ ] Support team trained
- [ ] Backup and recovery procedures tested

This integration architecture ensures ARX functionality seamlessly integrates with the existing Arxos platform while maintaining security, performance, and user experience standards.

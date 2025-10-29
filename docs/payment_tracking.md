# Git-Native Payment Tracking System

## Overview

ArxOS uses **Git commits as payment receipts** to track contributor payouts in a fully decentralized system. No database needed - all payment state is stored in Git repositories.

## Core Principle: Git Commits as Payment Receipts

Each payment creates an immutable Git commit that serves as:
1. **Proof of payment** (what was paid, when, to whom)
2. **Payment state** (marks contributions as "paid")
3. **Audit trail** (full payment history in Git log)

---

## Payment Repository Structure

### Option 1: Contributor-Specific Payment Repos (Recommended)

Each contributor has a payment repo (or branch in their building repo):

```
contributor-payments/
├── receipts/
│   ├── 2024/
│   │   ├── 03-payment-001.yml
│   │   ├── 03-payment-002.yml
│   │   └── 04-payment-001.yml
└── unpaid-contributions.yml  # Generated, not committed
```

**Payment Receipt Format:**
```yaml
# receipts/2024/03-payment-001.yml
payment_id: "pay_abc1234567890"
contributor_id: "user_john_doe"
contributor_repo: "git@github.com:user/building-xyz.git"
period: "2024-03"
amount_usd: 245.50
payment_method: "stripe"
stripe_payout_id: "po_xyz789"
status: "completed"
date_paid: "2024-03-15T14:30:00Z"
contribution_commits:
  - commit: "abc123def456..."
    repo: "git@github.com:user/building-xyz.git"
    contribution_type: "sensor_data"
    period: "2024-03"
  - commit: "def456ghi789..."
    repo: "git@github.com:user/building-xyz.git"
    contribution_type: "ar_scan"
    period: "2024-03"
metadata:
  total_contributions: 15
  sensor_uptime_hours: 720
  scan_quality_score: 0.92
  payment_calculation: |
    base: $200
    quality_bonus: $45.50
    total: $245.50
git_commit: "receipt_commit_sha"
```

---

## Payment Workflow

### Step 1: Calculate Unpaid Contributions

**Query Contributor Repos:**
```rust
// src/depin/payment_tracker.rs
pub struct PaymentTracker {
    git_manager: GitManager,
    payment_repo: String,  // Where payment receipts are stored
}

impl PaymentTracker {
    /// Find all unpaid contributions across all contributor repos
    pub fn find_unpaid_contributions(&self) -> Result<Vec<UnpaidContribution>> {
        // 1. Get list of all contributor repos
        let contributor_repos = self.list_contributor_repos()?;
        
        let mut unpaid = Vec::new();
        
        for repo in contributor_repos {
            // 2. Get all contribution commits from this repo
            let contributions = self.get_contribution_commits(&repo)?;
            
            // 3. Get all payment receipts for this contributor
            let payments = self.get_payment_receipts(&repo)?;
            
            // 4. Find contributions NOT referenced in payment receipts
            for contribution in contributions {
                let is_paid = payments.iter().any(|payment| {
                    payment.contribution_commits.contains(&contribution.commit_hash)
                });
                
                if !is_paid {
                    unpaid.push(UnpaidContribution {
                        contributor_id: repo.contributor_id,
                        commit_hash: contribution.commit_hash,
                        repo: repo.url.clone(),
                        contribution_type: contribution.type_,
                        value_usd: self.calculate_contribution_value(&contribution)?,
                        period: contribution.period,
                    });
                }
            }
        }
        
        Ok(unpaid)
    }
}
```

### Step 2: Generate Payment Batch

**Group by Contributor & Calculate Totals:**
```rust
pub fn generate_payment_batch(&self, unpaid: &[UnpaidContribution]) -> Vec<PaymentBatch> {
    let mut batches = HashMap::new();
    
    // Group unpaid contributions by contributor
    for contribution in unpaid {
        let batch = batches
            .entry(&contribution.contributor_id)
            .or_insert_with(|| PaymentBatch {
                contributor_id: contribution.contributor_id.clone(),
                total_amount: 0.0,
                contributions: Vec::new(),
                contributor_repo: contribution.repo.clone(),
            });
        
        batch.total_amount += contribution.value_usd;
        batch.contributions.push(contribution.clone());
    }
    
    batches.into_values().collect()
}
```

### Step 3: Process Payments

**Stripe/PayPal Integration:**
```rust
pub async fn process_payments(&self, batches: Vec<PaymentBatch>) -> Result<Vec<PaymentResult>> {
    let mut results = Vec::new();
    
    for batch in batches {
        // 1. Get contributor payment info (stored in their repo config)
        let payment_info = self.get_contributor_payment_info(&batch.contributor_id)?;
        
        // 2. Process payment via Stripe/PayPal
        let payment_result = match payment_info.method {
            PaymentMethod::Stripe => {
                self.stripe_client.transfer(
                    payment_info.stripe_account_id,
                    batch.total_amount,
                ).await?
            }
            PaymentMethod::PayPal => {
                self.paypal_client.send_payment(
                    payment_info.paypal_email,
                    batch.total_amount,
                ).await?
            }
        };
        
        // 3. Create payment receipt
        let receipt = PaymentReceipt {
            payment_id: payment_result.payment_id.clone(),
            contributor_id: batch.contributor_id.clone(),
            amount_usd: batch.total_amount,
            payment_method: payment_info.method,
            date_paid: Utc::now(),
            contribution_commits: batch.contributions.iter()
                .map(|c| c.commit_hash.clone())
                .collect(),
            // ... other fields
        };
        
        // 4. Commit payment receipt to Git
        self.commit_payment_receipt(&receipt)?;
        
        results.push(PaymentResult {
            contributor_id: batch.contributor_id,
            payment_id: payment_result.payment_id,
            amount: batch.total_amount,
            status: "completed",
        });
    }
    
    Ok(results)
}
```

### Step 4: Commit Payment Receipt to Git

**Immutable Payment Record:**
```rust
pub fn commit_payment_receipt(&self, receipt: &PaymentReceipt) -> Result<String> {
    // 1. Serialize receipt to YAML
    let yaml_content = serde_yaml::to_string(receipt)?;
    
    // 2. Determine receipt file path
    let file_path = format!(
        "receipts/{}/{:02}-payment-{:03}.yml",
        receipt.date_paid.year(),
        receipt.date_paid.month(),
        self.get_next_receipt_number(receipt.contributor_id)?,
    );
    
    // 3. Write to payment repo
    let repo_path = self.get_payment_repo_path(&receipt.contributor_id)?;
    let full_path = Path::new(&repo_path).join(&file_path);
    
    std::fs::write(&full_path, yaml_content)?;
    
    // 4. Commit to Git
    let git_manager = BuildingGitManager::new(&repo_path, "Payment Receipts", config)?;
    
    let commit_message = format!(
        "Payment receipt: ${:.2} USD to {} via {}",
        receipt.amount_usd,
        receipt.contributor_id,
        receipt.payment_method,
    );
    
    // Stage and commit
    git_manager.stage_file(&file_path)?;
    let commit_hash = git_manager.commit_staged(&commit_message)?;
    
    // 5. Tag commit for easy reference
    git_manager.create_tag(&format!("payment-{}", receipt.payment_id))?;
    
    Ok(commit_hash)
}
```

---

## Payment State Queries

### Check What's Been Paid

```rust
/// Check if a specific contribution has been paid
pub fn is_contribution_paid(&self, commit_hash: &str, contributor_repo: &str) -> bool {
    let payments = self.get_payment_receipts(contributor_repo).unwrap_or_default();
    payments.iter().any(|p| p.contribution_commits.contains(commit_hash))
}

/// Get payment history for a contributor
pub fn get_payment_history(&self, contributor_id: &str) -> Vec<PaymentReceipt> {
    let payment_repo = self.get_payment_repo_path(contributor_id).unwrap();
    self.load_all_receipts(&payment_repo).unwrap_or_default()
}

/// Calculate unpaid balance for a contributor
pub fn calculate_unpaid_balance(&self, contributor_id: &str) -> f64 {
    let unpaid = self.find_unpaid_contributions_by_contributor(contributor_id)
        .unwrap_or_default();
    unpaid.iter().map(|c| c.value_usd).sum()
}
```

---

## Contributor Payment Configuration

Contributors store payment info in their repo config:

```yaml
# .arxos/config.yml (in contributor's building repo)
payment:
  method: "stripe"  # or "paypal"
  stripe_account_id: "acct_xyz789"  # if using Stripe
  paypal_email: "contributor@example.com"  # if using PayPal
  auto_payout: true  # Enable automatic monthly payouts
  minimum_payout: 10.0  # Minimum USD before payout
```

**Privacy:** Payment info stays in contributor's private repo, never shared.

---

## CLI Commands for Contributors

```bash
# Register payment info
arx payment register --method stripe --account-id acct_xyz789

# Check unpaid contributions
arx payment unpaid

# View payment history
arx payment history --contributor user_john_doe

# View specific payment receipt
arx payment receipt --payment-id pay_abc123

# Calculate earnings
arx payment earnings --period 2024-03
```

---

## CLI Commands for Admins (Payout Processing)

```bash
# Find all unpaid contributions
arx payment admin unpaid-summary

# Generate payment batch
arx payment admin generate-batch --period 2024-03

# Process payments (requires payment processor credentials)
arx payment admin process-payments --batch batch-2024-03.json

# Verify payment receipts
arx payment admin verify-receipts --period 2024-03
```

---

## Payment Repository Options

### Option A: Centralized Payment Repo (Simpler)

```
arxos-payments/  # Single Git repo for all payments
├── contributors/
│   ├── user_john_doe/
│   │   └── receipts/
│   └── user_jane_smith/
│       └── receipts/
```

**Pros:**
- Single repo to manage
- Easier to query all payments
- Centralized audit trail

**Cons:**
- Less decentralized
- Single point of failure (repo access)

### Option B: Distributed Payment Receipts (More Decentralized)

Each contributor has receipts in their own repo:

```
contributor-repos/
├── user_john_doe/building-xyz/
│   └── .arxos/payments/
│       └── receipts/
└── user_jane_smith/building-abc/
    └── .arxos/payments/
        └── receipts/
```

**Pros:**
- Fully decentralized
- Contributor owns their payment history
- No central repo needed

**Cons:**
- More complex to query across repos
- Need to discover all contributor repos

**Recommendation:** Start with Option A (centralized), migrate to Option B later if needed.

---

## Preventing Double Payments

### Strategy 1: Git Commit References

Each payment receipt explicitly lists the contribution commits it covers:

```yaml
contribution_commits:
  - "abc123def456..."
  - "def456ghi789..."
```

When checking if a contribution is paid, search all payment receipts for that commit hash.

### Strategy 2: Payment Period Locks

Mark entire payment periods as "processed" once batch is completed:

```yaml
# payments/processed-periods.yml
periods:
  - period: "2024-03"
    processed: true
    processed_date: "2024-03-20T10:00:00Z"
    payment_batch_id: "batch-2024-03-001"
```

### Strategy 3: Idempotent Payment Processing

Payment processor (Stripe/PayPal) handles deduplication:

```rust
// Check if payment already exists in Stripe
if let Some(existing) = self.stripe_client.get_payout(payment_id).await? {
    // Already paid, just create receipt record
    self.commit_payment_receipt(&receipt)?;
    return Ok(existing);
}
```

---

## Payment Calculation Example

```rust
pub fn calculate_contribution_value(&self, contribution: &Contribution) -> Result<f64> {
    match contribution.type_ {
        ContributionType::SensorData => {
            let uptime_hours = contribution.metadata.uptime_hours;
            let data_quality = contribution.metadata.quality_score;
            let base_rate = 0.10; // $0.10 per hour of uptime
            Ok(base_rate * uptime_hours as f64 * data_quality)
        }
        ContributionType::ARScan => {
            let scan_quality = contribution.metadata.confidence_score;
            let equipment_count = contribution.metadata.equipment_count;
            let base_rate = 5.0; // $5 base + $0.50 per equipment
            Ok(base_rate * scan_quality + (0.50 * equipment_count as f64))
        }
        ContributionType::BuildingModel => {
            let equipment_count = contribution.metadata.equipment_count;
            let room_count = contribution.metadata.room_count;
            Ok(2.0 + (0.10 * equipment_count as f64) + (0.05 * room_count as f64))
        }
    }
}
```

---

## Audit & Verification

### Payment Audit Trail

All payments are verifiable via Git:

```bash
# View all payments in a period
git log --all --grep="Payment receipt" --since="2024-03-01"

# Verify a specific payment
arx payment verify --payment-id pay_abc123

# Cross-check Stripe/PayPal with Git receipts
arx payment verify-external --payment-id pay_abc123
```

### Reconciliation

Monthly reconciliation process:

```rust
pub fn reconcile_payments(&self, period: &str) -> Result<ReconciliationReport> {
    // 1. Get all Git payment receipts for period
    let git_receipts = self.get_payment_receipts_for_period(period)?;
    
    // 2. Get all Stripe/PayPal transactions for period
    let processor_transactions = self.payment_processor.get_transactions(period)?;
    
    // 3. Match Git receipts to processor transactions
    let matches = self.match_receipts_to_transactions(git_receipts, processor_transactions)?;
    
    // 4. Report discrepancies
    Ok(ReconciliationReport {
        total_git_receipts: git_receipts.len(),
        total_processor_transactions: processor_transactions.len(),
        matches: matches.len(),
        discrepancies: self.find_discrepancies(matches)?,
    })
}
```

---

## Implementation Phases

### Phase 1: Manual Payment Tracking
- Payment receipts committed manually after Stripe/PayPal payouts
- CLI command: `arx payment record --amount 150.50 --payment-id pay_xyz`
- Contributors can verify their payment history in Git

### Phase 2: Automated Payment Detection
- Script queries Stripe/PayPal API
- Automatically creates payment receipts for confirmed payouts
- CLI command: `arx payment sync --from stripe`

### Phase 3: Full Automated Pipeline
- Monthly cron job calculates unpaid contributions
- Generates payment batch
- Processes payments via Stripe/PayPal
- Commits payment receipts automatically
- Notifies contributors via email

---

## Key Advantages

1. **Fully Decentralized**: No database, all state in Git
2. **Immutable Audit Trail**: Git commits can't be deleted/altered
3. **Transparent**: Contributors can verify their payments
4. **Verifiable**: Cross-check with payment processor records
5. **Simple**: Standard Git operations, no special infrastructure

---

## Summary

**Payment Flow:**
1. Contributions recorded as Git commits
2. Payment processor (Stripe/PayPal) handles actual money transfer
3. Payment receipt committed to Git after successful payment
4. Receipt marks contributions as "paid" (prevents double payment)
5. All payment state queryable from Git commits

**No Database Needed:**
- Contributions = Git commits
- Payments = Git commits (receipts)
- Payment state = Presence of receipt commit referencing contribution

This maintains full decentralization while using standard payment processors (Stripe/PayPal) for actual USD transfers.


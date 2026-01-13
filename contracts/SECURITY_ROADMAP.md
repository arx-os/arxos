# ArxOS Smart Contract Security & Enhancement Roadmap

## Executive Summary
This roadmap addresses critical security vulnerabilities, economic model risks, and gas optimization opportunities identified in the ArxOS tokenomics system. Items are prioritized by risk severity and implementation complexity.

**Immediate non-negotiables (pre-mainnet):**
- Expand oracle set (3-of-5 minimum), add staking/slashing, and rate-limit minting with emergency pause.
- Protect payments with timelocked minimum-price changes and user max-price commitments.
- Book external audit; do not launch mainnet with any critical/high findings outstanding.
- Run full testnet soak with monitoring and anomaly alerts before mainnet.

---

## Phase 1: Critical Security Fixes (MUST HAVE - Pre-Mainnet)

### 1.1 Oracle Collusion Prevention ⚠️ CRITICAL
**Risk**: Two malicious oracles can mint unlimited tokens
**Timeline**: 2-3 weeks
**Dependencies**: None

**Implementation Steps**:
```solidity
// ArxContributionOracle.sol changes:

1. Expand oracle set from 3 to 5+ operators
   - Update MIN_CONFIRMATIONS to 3 (60% majority)
   - Add oracle registration/deregistration functions
   - Implement oracle rotation mechanism

2. Add oracle staking requirement
   - Create OracleStaking.sol contract
   - Require 10,000 ARXO stake per oracle
   - Lock stake for 7-day unbonding period

3. Implement slashing conditions
   - Slash 100% stake for proven collusion
   - Slash 50% stake for failed proof verification
   - Slash 10% stake for excessive downtime
```

**Test Requirements**:
- [ ] Test 3-of-5 consensus scenarios
- [ ] Test oracle stake locking/unlocking
- [ ] Test slashing mechanism with disputes
- [ ] Fuzz test oracle rotation edge cases

**Acceptance Criteria**:
- ✅ No single pair of oracles can approve contributions alone
- ✅ Oracle operators have economic skin in the game
- ✅ Slashing automatically triggered on verified malicious behavior

---

### 1.2 Rate Limiting & Circuit Breakers ⚠️ HIGH
**Risk**: Compromised oracle can drain system instantly
**Timeline**: 1 week
**Dependencies**: None

**Implementation Steps**:
```solidity
// ArxosToken.sol changes:

1. Add per-building daily mint caps
   mapping(address => DailyLimit) public buildingLimits;
   struct DailyLimit {
       uint256 dailyCap;      // e.g., 100,000 ARXO
       uint256 mintedToday;
       uint256 lastResetTime;
   }

2. Add per-worker contribution limits
   mapping(address => uint256) public workerDailyMints;
   uint256 public constant MAX_WORKER_DAILY = 10_000 * 10**18;

3. Add global emergency pause
   bool public paused;
   function emergencyPause() external onlyRole(EMERGENCY_ROLE);
```

**Test Requirements**:
- [ ] Test daily cap enforcement and reset
- [ ] Test emergency pause halts all minting
- [ ] Test worker rate limits across multiple buildings
- [ ] Test cap overflow protection

**Acceptance Criteria**:
- ✅ No building can mint >100k ARXO per day
- ✅ No worker can earn >10k ARXO per day
- ✅ Admin can pause minting within 1 block

---

### 1.3 Payment Front-Running Protection ⚠️ MEDIUM
**Risk**: Building owners can front-run payments with price changes
**Timeline**: 3 days
**Dependencies**: None

**Implementation Steps**:
```solidity
// ArxPaymentRouter.sol changes:

1. Add time-lock on minimum payment changes
   mapping(string => PendingChange) public pendingMinimumChanges;
   struct PendingChange {
       uint256 newMinimum;
       uint256 effectiveTime;
   }
   uint256 public constant CHANGE_DELAY = 1 hours;

2. Add max price increase limit
   uint256 public constant MAX_PRICE_INCREASE = 200; // 200%

3. Include price commitment in payment signature
   function payForAccess(
       string calldata buildingId,
       uint256 amount,
       uint256 maxPrice,  // NEW: user commits to max price
       bytes32 nonce
   )
```

**Test Requirements**:
- [ ] Test time-lock prevents immediate changes
- [ ] Test max increase limit enforcement
- [ ] Test payment with price commitment
- [ ] Test expired commitments revert

**Acceptance Criteria**:
- ✅ Price changes require 1-hour delay
- ✅ Prices cannot increase >200% in single change
- ✅ Users protected from front-running attacks

---

## Phase 2: Economic Model Enhancements (SHOULD HAVE)

### 2.1 Configurable Revenue Splits
**Goal**: Allow different splits per building type/size
**Timeline**: 1 week
**Dependencies**: None

**Implementation Steps**:
```solidity
// ArxContributionOracle.sol changes:

1. Define split configurations
   enum SplitTier { STANDARD, PREMIUM, ENTERPRISE }
   
   struct RevenueConfig {
       uint256 workerBps;      // basis points (7000 = 70%)
       uint256 buildingBps;    // 1000 = 10%
       uint256 maintainerBps;  // 1000 = 10%
       uint256 treasuryBps;    // 1000 = 10%
   }
   
   mapping(SplitTier => RevenueConfig) public splitConfigs;

2. Assign tiers to buildings
   mapping(string => SplitTier) public buildingTiers;

3. Use tier-specific splits in mintContribution
```

**Test Requirements**:
- [ ] Test all tier splits sum to 100%
- [ ] Test tier assignment and updates
- [ ] Test distribution with custom tiers
- [ ] Test tier migration scenarios

**Acceptance Criteria**:
- ✅ 3+ configurable split tiers available
- ✅ Building owners can request tier changes
- ✅ All splits validated to equal 100%

---

### 2.2 Dispute Resolution System
**Goal**: Fair mechanism for resolving contribution disputes
**Timeline**: 2 weeks
**Dependencies**: Oracle staking (1.1)

**Implementation Steps**:
```solidity
// Create ArxDisputeResolver.sol:

1. Define dispute lifecycle
   enum DisputeStatus { PENDING, UNDER_REVIEW, RESOLVED }
   
   struct Dispute {
       bytes32 contributionId;
       address disputer;
       string reason;
       uint256 createdAt;
       DisputeStatus status;
       bool upheld;  // true = dispute valid, worker loses
   }

2. Add evidence submission
   mapping(bytes32 => Evidence[]) public disputeEvidence;
   
3. Implement voting mechanism
   - 3 randomly selected oracles (not involved in original)
   - 2-of-3 majority to uphold dispute
   - 48-hour resolution window

4. Economic consequences
   - If upheld: worker loses payment, disputer gets 10% reward
   - If rejected: disputer slashed 10%, worker compensated
```

**Test Requirements**:
- [ ] Test dispute creation and lifecycle
- [ ] Test evidence submission
- [ ] Test oracle selection randomness
- [ ] Test economic rewards/penalties

**Acceptance Criteria**:
- ✅ Disputes resolved within 48 hours
- ✅ False disputes penalized economically
- ✅ Evidence on-chain or IPFS-pinned

---

### 2.3 Contribution Quality Metrics
**Goal**: Incentivize high-quality data contributions
**Timeline**: 1 week
**Dependencies**: None

**Implementation Steps**:
```solidity
// ArxContributionOracle.sol changes:

1. Add quality scoring
   struct QualityMetrics {
       uint256 dataSize;
       uint256 accuracy;     // 0-100 score
       uint256 completeness; // 0-100 score
       uint256 timeliness;   // age in seconds
   }

2. Scale rewards by quality
   function calculateReward(
       uint256 baseAmount,
       QualityMetrics memory quality
   ) internal pure returns (uint256) {
       uint256 qualityMultiplier = (
           quality.accuracy + 
           quality.completeness
       ) / 2;
       return baseAmount * qualityMultiplier / 100;
   }

3. Track worker reputation
   mapping(address => WorkerStats) public workerStats;
   struct WorkerStats {
       uint256 totalContributions;
       uint256 averageQuality;
       uint256 disputeCount;
   }
```

**Test Requirements**:
- [ ] Test quality score calculations
- [ ] Test reward scaling
- [ ] Test reputation tracking
- [ ] Test edge cases (zero quality, max quality)

**Acceptance Criteria**:
- ✅ High-quality data earns 2x base reward
- ✅ Low-quality data earns 0.5x base reward
- ✅ Worker reputation visible on-chain

---

## Phase 3: Gas Optimization (NICE TO HAVE)

### 3.1 Enable IR Optimizer
**Goal**: Reduce contract sizes by 10-20%
**Timeline**: 2 days
**Dependencies**: None

**Implementation Steps**:
```toml
# foundry.toml changes:

1. Enable IR compilation
   via_ir = true

2. Increase optimizer runs for frequently-called functions
   optimizer_runs = 10000

3. Re-run full test suite
   forge test --gas-report

4. Compare gas costs before/after
```

**Test Requirements**:
- [ ] All 120 tests still pass
- [ ] Gas costs reduced on average
- [ ] No behavioral changes introduced

**Acceptance Criteria**:
- ✅ Contract sizes reduced >10%
- ✅ No test failures
- ✅ Average gas costs reduced >5%

---

### 3.2 Contract Splitting
**Goal**: Split large contracts to reduce deployment costs
**Timeline**: 1 week
**Dependencies**: Phase 3.1

**Implementation Steps**:
```solidity
// Split ArxContributionOracle.sol into:

1. ArxContributionProposer.sol
   - proposeContribution
   - confirmContribution
   - _verifyProof

2. ArxContributionFinalizer.sol
   - finalizeContribution
   - disputeContribution
   - getContribution

3. Update deployment script
   - Deploy both contracts
   - Set mutual permissions
   - Update tests
```

**Test Requirements**:
- [ ] All tests pass with split contracts
- [ ] Cross-contract calls work correctly
- [ ] Gas costs comparable or better
- [ ] Deployment costs reduced

**Acceptance Criteria**:
- ✅ Each contract <20KB (83% of limit)
- ✅ Deployment gas reduced >20%
- ✅ No security regressions

---

### 3.3 Storage Optimization
**Goal**: Reduce storage operations and costs
**Timeline**: 3 days
**Dependencies**: None

**Implementation Steps**:
```solidity
// Optimize storage patterns:

1. Pack structs efficiently
   // BEFORE:
   struct PendingContribution {
       address worker;          // 20 bytes
       address building;        // 20 bytes
       uint256 amount;          // 32 bytes
       uint256 confirmations;   // 32 bytes
       uint256 proposedAt;      // 32 bytes
       bool finalized;          // 1 byte
   }
   
   // AFTER (packed into fewer slots):
   struct PendingContribution {
       address worker;          // slot 0 (20 bytes)
       uint96 confirmations;    // slot 0 (12 bytes) - fits in same slot
       address building;        // slot 1 (20 bytes)
       uint96 proposedAt;       // slot 1 (12 bytes) - timestamp fits in uint96
       uint256 amount;          // slot 2
       bool finalized;          // slot 2 (1 byte) - fits with amount
   }

2. Use uint128 for amounts where safe
   - Max supply fits in uint128
   - Saves 16 bytes per storage slot

3. Batch storage writes
   - Update multiple fields in single operation
   - Use memory struct, then single SSTORE
```

**Test Requirements**:
- [ ] Test struct packing correctness
- [ ] Test overflow scenarios with smaller types
- [ ] Benchmark gas savings
- [ ] Test timestamp compatibility

**Acceptance Criteria**:
- ✅ Storage operations reduced >30%
- ✅ Gas savings >1000 per transaction
- ✅ No overflow vulnerabilities

---

## Phase 4: Monitoring & Observability (OPERATIONAL)

### 4.1 Event Enhancement
**Goal**: Complete audit trail for all state changes
**Timeline**: 2 days
**Dependencies**: None

**Implementation Steps**:
```solidity
// Add comprehensive events:

1. Oracle management events
   event OracleAdded(address indexed oracle, uint256 stake);
   event OracleRemoved(address indexed oracle, uint256 slashed);
   event OracleRotated(address indexed old, address indexed new);

2. Rate limit events
   event DailyLimitReached(address indexed building, uint256 amount);
   event WorkerLimitReached(address indexed worker, uint256 amount);
   event EmergencyPaused(address indexed admin, string reason);

3. Economic events
   event StakeSlashed(address indexed oracle, uint256 amount, string reason);
   event DisputeResolved(bytes32 indexed disputeId, bool upheld);
   event QualityBonusApplied(address indexed worker, uint256 bonus);
```

**Test Requirements**:
- [ ] Verify all events emitted in tests
- [ ] Check event parameter correctness
- [ ] Test event indexing

**Acceptance Criteria**:
- ✅ All state changes emit events
- ✅ Events include all relevant data
- ✅ Indexed parameters optimized for queries

---

### 4.2 On-Chain Analytics
**Goal**: Queryable metrics for monitoring
**Timeline**: 3 days
**Dependencies**: 4.1

**Implementation Steps**:
```solidity
// Add view functions for analytics:

1. System-wide metrics
   function getSystemMetrics() external view returns (
       uint256 totalContributions,
       uint256 totalMinted,
       uint256 activeOracles,
       uint256 activeWorkers,
       uint256 registeredBuildings
   )

2. Building-specific metrics
   function getBuildingMetrics(string calldata buildingId)
       external view returns (
           uint256 totalContributions,
           uint256 totalPayments,
           uint256 averageQuality,
           uint256 activeWorkers
       )

3. Worker-specific metrics
   function getWorkerMetrics(address worker)
       external view returns (
           uint256 totalContributions,
           uint256 totalEarned,
           uint256 averageQuality,
           uint256 disputeRate
       )
```

**Test Requirements**:
- [ ] Test metric calculations
- [ ] Test gas efficiency of views
- [ ] Verify accuracy against events

**Acceptance Criteria**:
- ✅ All metrics queryable on-chain
- ✅ View functions <50k gas
- ✅ Metrics update in real-time

---

## Engineering Best Practices (Apply Across All Phases)

- **TDD-first**: Write failing tests before code; unit + integration + invariants; gas snapshots per PR.
- **Security-in-CI**: Slither + Mythril (or Echidna/Medusa for property tests) on every PR; fail fast on findings.
- **Custom errors & events**: Prefer custom errors over revert strings; emit events for all stateful changes.
- **Controlled upgrades**: If using UUPS, timebox upgrade window (≤6 months) and gate with multisig + timelock.
- **Anomaly detection**: Alert on unusual mint/payment volumes (e.g., >3× 7d avg), auto-trigger review/pause playbook.
- **Invariant testing**: Total supply equals sum of balances; splits always sum to 100%; rate limits cannot be bypassed.

---

## Rollout & Launch Readiness

1) **Weeks 1-3 (Security hardening)**: Oracle staking/slashing, 3-of-5 consensus, mint rate limits, emergency pause, payment timelocks.
2) **Weeks 4-6 (Economics)**: Configurable splits, dispute resolution with penalties, quality-based rewards.
3) **Weeks 7-9 (Optimization)**: Enable IR, storage packing, optional contract splitting; re-run gas + invariants.
4) **Weeks 10-12 (Validation)**: Monitoring/analytics, 4-week testnet soak, external audit fix review; no mainnet until zero critical/high.

**Go/No-Go Checklist** (must all be true before mainnet):
- 7+ independent oracles staked and monitored; 3-of-5 active consensus.
- Emergency pause tested live; rate limits enforced and observable.
- Full test suite (unit/integration/invariants) 100% passing with gas reports.
- External audit completed with zero critical/high; fixes merged and retested.
- Monitoring/alerts live (Tenderly/Defender or equivalent) with runbooks rehearsed.

---

## Implementation Timeline

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│   Week 1-3  │   Week 4-6  │   Week 7-9  │  Week 10-12 │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ Phase 1.1   │ Phase 2.1   │ Phase 3.2   │ Phase 4     │
│ Oracle Fix  │ Rev Splits  │ Contract    │ Monitoring  │
│             │             │ Splitting   │             │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ Phase 1.2   │ Phase 2.2   │ Phase 3.3   │ Security    │
│ Rate Limits │ Disputes    │ Storage Opt │ Audit Prep  │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ Phase 1.3   │ Phase 2.3   │ Phase 3.1   │ Testnet     │
│ Front-run   │ Quality     │ IR Optimizer│ Deployment  │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

**Total Duration**: 12 weeks (3 months)
**Estimated Effort**: 2-3 full-time engineers

---

## Testing Strategy

### Unit Tests (Target: 100% coverage)
- All new functions have corresponding tests
- Edge cases and boundary conditions covered
- Fuzz testing for numeric operations
- Property-based testing for invariants

### Integration Tests
- Multi-contract interaction scenarios
- Full oracle consensus workflows
- End-to-end contribution lifecycle
- Payment flow with splits

### Security Tests
- Attack scenario simulations
- Oracle collusion attempts
- Front-running protection verification
- Rate limit bypass attempts

### Gas Benchmarks
- Before/after comparisons for each optimization
- Worst-case scenario testing
- Gas cost regression tracking

### Testnet Validation
1. **Sepolia Deployment** (Week 10)
   - 1-week stress testing
   - 50+ test contributions
   - Simulate attack scenarios

2. **Base Sepolia Deployment** (Week 11)
   - 1-week production simulation
   - Real oracle operators
   - Real building registrations

3. **Mainnet Launch** (Week 13+)
   - Phased rollout with limits
   - Gradual oracle expansion
   - 24/7 monitoring

---

## Risk Mitigation

### Critical Risks
1. **Smart Contract Bugs**: Professional audit required before mainnet
2. **Oracle Centralization**: Expand to 7+ oracles over first year
3. **Economic Exploits**: Bug bounty program ($100k+ rewards)
4. **Network Congestion**: L2 deployment (Base) mitigates gas spikes

### Contingency Plans
- Multi-sig upgrade capability for first 6 months
- Emergency pause mechanism with DAO override
- Insurance fund (5% of treasury) for critical exploits
- Incident response team on 24/7 standby

---

## Success Metrics

### Phase 1 (Security)
- ✅ 0 critical vulnerabilities in external audit
- ✅ 7-day attack simulation without exploits
- ✅ Emergency pause tested and functional

### Phase 2 (Economics)
- ✅ 95%+ dispute resolution accuracy
- ✅ 3+ revenue split tiers operational
- ✅ Quality scores correlate with oracle assessments

### Phase 3 (Optimization)
- ✅ Average gas costs reduced >15%
- ✅ Contract sizes <85% of limit
- ✅ Deployment costs <0.5 ETH on Base

### Phase 4 (Operations)
- ✅ 99.9% uptime for oracle infrastructure
- ✅ <5 minute incident detection time
- ✅ Complete audit trail for all transactions

---

## Dependencies & Prerequisites

### Technical
- Foundry v0.2.0+
- Solidity 0.8.24+
- OpenZeppelin Contracts v5.0+
- Base L2 RPC endpoint

### Organizational
- 2-3 Solidity engineers (senior level)
- 1 security auditor (continuous review)
- 1 DevOps engineer (testnet/mainnet)
- Legal review for oracle agreements

### External
- Professional audit firm (Trail of Bits, OpenZeppelin, Consensys Diligence)
- Oracle operator agreements (7+ independent entities)
- Insurance provider for smart contract coverage
- Bug bounty platform (Immunefi, Code4rena)

---

## Cost Estimates

### Development Costs
- Engineering: $300k-$450k (3 months, 2-3 engineers)
- Security Audit: $50k-$100k (comprehensive review)
- Bug Bounty: $25k setup + $100k reserves
- Legal: $15k-$25k (oracle agreements, T&Cs)

### Deployment Costs (Base L2)
- Contract Deployment: ~$500-$1000 (5 contracts)
- Testnet Testing: ~$100 (faucet ETH)
- Initial Oracle Stakes: 70k ARXO (7 oracles × 10k each)

### Operational Costs (Annual)
- Oracle Infrastructure: $50k-$75k (hosting, maintenance)
- Monitoring/Alerting: $12k-$18k (Tenderly, OpenZeppelin Defender)
- Ongoing Audits: $25k-$50k (quarterly reviews)

**Total Year 1 Budget**: $500k-$750k

---

## Next Steps

### Immediate Actions (This Week)
1. [ ] Review and approve roadmap with stakeholders
2. [ ] Assemble engineering team
3. [ ] Set up development environment
4. [ ] Create task board (GitHub Projects/Jira)
5. [ ] Schedule security audit firm interviews

### Week 1 Deliverables
1. [ ] Phase 1.1 specification document
2. [ ] Oracle staking contract scaffolding
3. [ ] Test suite expansion plan
4. [ ] Audit RFP sent to 3+ firms

### Month 1 Milestone
- ✅ Phase 1 (Critical Security) complete
- ✅ External audit scheduled
- ✅ Testnet deployment ready

---

**Document Version**: 1.0  
**Last Updated**: December 12, 2025  
**Owner**: ArxOS Core Team  
**Review Cadence**: Weekly during development, monthly post-launch

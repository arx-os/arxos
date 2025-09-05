# BILT Token Economics

> Scope: Economic model, incentives, pricing, and sustainability assumptions. Audience: founders, economics, partnerships.
>
> Owner: Economics/Business Lead.

## Incentivizing Crowd-Sourced Building Intelligence

BILT (Building Intelligence Labor Token) creates sustainable economic incentives for field workers to contribute accurate building data. Unlike cryptocurrency, BILT is a point-based reward system with real-world redemption value, similar to airline miles or credit card rewards.

### 📖 Section Contents

Economics & Strategy:
1. **[BILT Tokenomics](./BILT_TOKENOMICS.md)**
2. **[Platform Revenue Model](./PLATFORM_REVENUE_MODEL.md)**
3. **[Financial Services Reality](./FINANCIAL_SERVICES_REALITY.md)**
4. **[Cost Structure Analysis](./COST_STRUCTURE_ANALYSIS.md)**

## 🎯 Core Economic Principles

### The Problem BILT Solves
```
Traditional Approach:
- Building audit: $5,000-10,000
- One-time snapshot
- Quickly becomes outdated
- No incentive for updates

BILT Approach:
- Continuous updates: $50-100/month
- Always current
- Workers earn while working
- Self-sustaining system
```

### Value Creation Cycle
```
Workers mark objects → Earn BILT → Redeem for value
    ↓                                      ↓
Building gets mapped ← Owners save money ← Better data
```

## 💰 BILT Point Calculation

### Base Point Values

```rust
pub struct BiltRewards {
    // Basic object marking
    pub const BASIC_OBJECT: u32 = 10;          // Outlet, switch, light
    pub const DETAILED_OBJECT: u32 = 20;       // With specifications
    pub const COMPLEX_OBJECT: u32 = 30;        // HVAC, panels, equipment
    
    // Bonus multipliers
    pub const FIRST_MAPPER: f32 = 2.0;         // First to map building
    pub const PROFESSIONAL: f32 = 1.2;         // Licensed professional
    pub const PHOTO_INCLUDED: f32 = 1.1;       // Includes photo
    pub const VERIFIED: f32 = 1.5;             // Verified by another worker
    
    // Special categories
    pub const SAFETY_CRITICAL: u32 = 50;       // Fire extinguisher, exit
    pub const EMERGENCY_SYSTEM: u32 = 75;      // Alarm, sprinkler
    pub const COMPLIANCE_ITEM: u32 = 40;       // Required for codes
}
```

### Calculation Example

```rust
impl BiltCalculator {
    pub fn calculate_reward(markup: &ARMarkup) -> u32 {
        let mut points = match markup.object_type {
            ObjectType::Outlet => BiltRewards::BASIC_OBJECT,
            ObjectType::FireExtinguisher => BiltRewards::SAFETY_CRITICAL,
            ObjectType::HVACUnit => BiltRewards::COMPLEX_OBJECT,
            _ => BiltRewards::BASIC_OBJECT,
        };
        
        // Apply multipliers
        if markup.includes_photo {
            points = (points as f32 * BiltRewards::PHOTO_INCLUDED) as u32;
        }
        
        if markup.user.is_licensed_professional() {
            points = (points as f32 * BiltRewards::PROFESSIONAL) as u32;
        }
        
        if markup.is_first_in_building() {
            points = (points as f32 * BiltRewards::FIRST_MAPPER) as u32;
        }
        
        // Add detail bonuses
        if markup.has_circuit_number() { points += 5; }
        if markup.has_specifications() { points += 5; }
        if markup.has_maintenance_date() { points += 3; }
        
        points
    }
}
```

## 📊 Earning Scenarios

### Typical Daily Earnings

```
Maintenance Worker - Regular Day:
- Morning inspection: 15 outlets (10 pts each) = 150 BILT
- Checked fire equipment: 5 items (50 pts each) = 250 BILT
- Documented HVAC units: 3 units (30 pts each) = 90 BILT
- Verification bonus: 10 items verified = 50 BILT
Total: 540 BILT ≈ $5.40

Electrician - Circuit Mapping:
- Mapped 50 outlets with circuits (20 pts each) = 1,000 BILT
- Professional bonus (1.2x) = 1,200 BILT
- First mapper bonus (2x on 10 items) = +200 BILT
Total: 1,400 BILT ≈ $14.00

Facility Manager - New Building:
- Initial structure scan = 100 BILT
- Mapped 100 objects (avg 15 pts) = 1,500 BILT
- First mapper bonus (2x) = 3,000 BILT
- Photo documentation = +150 BILT
Total: 3,250 BILT ≈ $32.50
```

## 🎁 Redemption Options

### Direct Redemptions

```typescript
interface RedemptionCatalog {
    tools: [
        { item: "Klein Multimeter", bilt: 5000, retail: "$45" },
        { item: "LED Flashlight", bilt: 2000, retail: "$18" },
        { item: "Safety Glasses", bilt: 1000, retail: "$9" },
        { item: "Work Gloves", bilt: 1500, retail: "$13" }
    ],
    
    giftCards: [
        { merchant: "Home Depot", bilt: 1000, value: "$10" },
        { merchant: "Amazon", bilt: 1000, value: "$10" },
        { merchant: "Starbucks", bilt: 500, value: "$5" },
        { merchant: "Gas Station", bilt: 2000, value: "$20" }
    ],
    
    training: [
        { course: "OSHA 10-Hour", bilt: 10000, value: "$89" },
        { course: "EPA Certification", bilt: 15000, value: "$139" },
        { course: "First Aid/CPR", bilt: 7500, value: "$69" }
    ],
    
    charity: [
        { cause: "Local School supplies", bilt: 1000, impact: "$10" },
        { cause: "Habitat for Humanity", bilt: 2500, impact: "$25" },
        { cause: "Red Cross", bilt: 1000, impact: "$10" }
    ]
}
```

### Redemption Process

```swift
class BiltRedemption {
    func redeemReward(userId: String, rewardId: String) -> RedemptionResult {
        // Check balance
        let balance = getUserBalance(userId)
        let cost = getRewardCost(rewardId)
        
        guard balance >= cost else {
            return .insufficientBalance(needed: cost - balance)
        }
        
        // Process redemption
        deductPoints(userId, amount: cost)
        
        switch rewardType {
        case .giftCard:
            return .giftCardCode(generateCode())
        case .physicalItem:
            return .shippingRequired(getShippingForm())
        case .training:
            return .enrollmentLink(getCourseAccess())
        case .charity:
            return .donationConfirmation(getReceipt())
        }
    }
}
```

## 🛡️ Quality Assurance System

### Verification Mechanics

```rust
pub struct VerificationSystem {
    pub fn verify_markup(
        original: &ARMarkup,
        verifier: &User,
        confirmation: &VerificationData
    ) -> VerificationResult {
        // Different person must verify
        if original.user_id == verifier.id {
            return VerificationResult::CannotSelfVerify;
        }
        
        // Check proximity (must be near object)
        if distance(verifier.location, original.position) > 5.0 {
            return VerificationResult::TooFarAway;
        }
        
        // Award points to both parties
        award_points(original.user_id, 15);  // Original mapper
        award_points(verifier.id, 5);        // Verifier
        
        VerificationResult::Success
    }
}
```

### Anti-Gaming Measures

```rust
pub struct AntiFraud {
    // Rate limiting
    const MAX_MARKS_PER_HOUR: u32 = 100;
    const MIN_TIME_BETWEEN_MARKS: Duration = Duration::from_secs(3);
    
    // Geographic validation
    fn validate_position(mark: &ARMarkup) -> bool {
        // Must be within building bounds
        is_within_building(mark.position) &&
        // Must be reasonable height
        mark.position.z < 5000 && // 5 meters
        // Must not overlap existing mark
        !has_duplicate_nearby(mark.position, 0.5) // 50cm radius
    }
    
    // Behavioral analysis
    fn detect_suspicious_pattern(user: &User) -> bool {
        user.marks_per_hour() > 60 ||
        user.average_detail_level() < 0.3 ||
        user.verification_rate() < 0.1
    }
}
```

## 📈 Economic Sustainability

### Funding Sources

```
Building Owners Pay For:
├── Compliance Reports ($50/month)
├── Emergency Access ($25/month)
├── Maintenance Analytics ($30/month)
└── Energy Optimization ($40/month)
Total Revenue: $145/building/month

BILT Costs:
├── Worker Rewards (~$30/month)
├── Redemption Costs (~$25/month)
└── Platform Operations (~$20/month)
Total Costs: $75/building/month

Net Margin: $70/building/month
```

### Scaling Economics

```rust
struct DistrictEconomics {
    schools: 300,
    monthly_revenue_per_school: 145.0,
    monthly_cost_per_school: 75.0,
    
    fn annual_projection(&self) -> FinancialProjection {
        let monthly_profit = self.schools as f64 * 
                           (self.monthly_revenue_per_school - 
                            self.monthly_cost_per_school);
        
        FinancialProjection {
            annual_revenue: self.schools as f64 * 
                          self.monthly_revenue_per_school * 12.0,
            annual_costs: self.schools as f64 * 
                        self.monthly_cost_per_school * 12.0,
            annual_profit: monthly_profit * 12.0,
            break_even_month: 4, // After initial development
        }
    }
}
// Result: $252,000 annual profit on 300 schools
```

## 🎮 Gamification Layers

### Leaderboards

```sql
-- Daily leaderboard
SELECT 
    user_name,
    SUM(bilt_earned) as daily_points,
    COUNT(DISTINCT object_id) as objects_marked,
    AVG(quality_score) as accuracy
FROM user_contributions
WHERE DATE(created_at) = CURRENT_DATE
GROUP BY user_id
ORDER BY daily_points DESC
LIMIT 10;

-- Building completion leaderboard
SELECT 
    building_name,
    COUNT(DISTINCT object_id) as objects_mapped,
    COUNT(DISTINCT user_id) as contributors,
    ROUND(completion_percentage, 1) as percent_complete
FROM building_progress
ORDER BY percent_complete DESC;
```

### Achievement System

```rust
pub enum Achievement {
    // Quantity achievements
    FirstMark,           // First object marked
    TenMarks,           // 10 objects
    HundredMarks,       // 100 objects
    ThousandMarks,      // 1,000 objects
    
    // Quality achievements
    DetailMaster,       // 90% marks include full details
    VerificationHero,   // Verified 50 other marks
    AccuracyExpert,     // 98% accuracy rate
    
    // Special achievements
    SafetyFirst,        // Marked all safety equipment in building
    CircuitTracer,      // Mapped entire electrical circuit
    FirstResponder,     // Mapped critical emergency routes
    WeekendWarrior,     // Worked on weekend
    
    // Social achievements
    TeamPlayer,         // Helped verify team members' marks
    Mentor,            // Trained new user
    BuildingOwner,      // Completed entire building
}

impl Achievement {
    pub fn bilt_bonus(&self) -> u32 {
        match self {
            Achievement::FirstMark => 50,
            Achievement::ThousandMarks => 1000,
            Achievement::SafetyFirst => 500,
            Achievement::BuildingOwner => 2000,
            _ => 100,
        }
    }
}
```

## 💡 Success Metrics

### Worker Satisfaction
- **Daily earnings**: $5-20 in rewards
- **Redemption rate**: 70% of earned BILT redeemed
- **Retention**: 80% active after 3 months
- **NPS Score**: 72 (promoters)

### System Health
- **Cost per building**: $50-75/month
- **Revenue per building**: $145/month
- **Accuracy rate**: 95% verified correct
- **Gaming detection**: <2% fraudulent marks

### Business Impact
- **Compliance cost reduction**: 70%
- **Emergency response improvement**: -5 minutes
- **Maintenance optimization**: 20% cost savings
- **Insurance premium reduction**: 10-15%

---

*"Turning routine work into rewarding work"*
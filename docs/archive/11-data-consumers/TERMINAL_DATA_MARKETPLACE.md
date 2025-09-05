# ArxOS Terminal Data Marketplace

> "If the data is valuable enough, they'll learn the terminal."

## Philosophy

No web dashboards. No pretty graphs. No PowerBI integrations. Just pure, powerful data queries through the terminal. This isn't a bug - it's a feature. It filters for serious buyers who understand the value of real building intelligence.

## Data Buyer Onboarding

```bash
# First time setup
$ arxos account create --type buyer
Enter company: McKinsey & Company
Enter email: john@mckinsey.com
Payment method: [Credit Card/ACH/Wire]

Account created. Check email for verification.

$ arxos verify K7M3X9
✓ Account verified
✓ $10,000 credit line approved
✓ Terminal access granted

Welcome to ArxOS Market Data. Type 'arx help market' to begin.
```

## Query Syntax

### Basic Queries
```bash
# Count queries
$ arx count equipment --type "LED" --region northeast
→ 1,247,892 LED fixtures across 8,234 buildings

$ arx count buildings --type education --state CA
→ 3,421 education buildings in California

$ arx count hvac --age ">15" --region midwest
→ 45,231 HVAC units over 15 years old
```

### Distribution Queries
```bash
# Show distribution of equipment ages
$ arx dist equipment.age --type chiller --region national
```
```
Chiller Age Distribution (n=12,847)
0-5 years:   ████████░░░░░░░░░░░░ 18%
5-10 years:  ████████████░░░░░░░░ 24%
10-15 years: ████████████████░░░░ 31%
15-20 years: ██████████░░░░░░░░░░ 19%
20+ years:   ████░░░░░░░░░░░░░░░░ 8%

Mean: 12.3 years | Median: 11.8 years | σ: 5.2 years
```

### Performance Queries
```bash
# Energy use intensity by building type
$ arx perf eui --type office --size large --region pacific
```
```
Energy Use Intensity - Large Office Buildings, Pacific Region
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sample: 892 buildings | 127.3M sqft

Percentiles (kBtu/sqft/yr):
10th: 42.3  ████░░░░░░░░░░░░░░░░
25th: 48.7  ██████░░░░░░░░░░░░░░
50th: 55.2  ████████████░░░░░░░░  ← Median
75th: 63.8  ████████████████░░░░
90th: 72.1  ██████████████████░░

Best in class: 38.2 (Building ID: ANON-4F2B)
Worst performer: 94.3 (Building ID: ANON-9A1C)
```

### Failure Analysis
```bash
# Equipment failure rates
$ arx failure --equipment "Carrier 30XA" --age 10-15
```
```
Failure Analysis: Carrier 30XA Chiller (10-15 years)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sample: 1,847 units tracked over 5 years

Annual Failure Rate: 8.3%
Mean Time Between Failures: 4.2 years

Common Failure Modes:
1. Compressor failure (34%) - Avg repair: $12,400
2. Control board (22%) - Avg repair: $3,200
3. Refrigerant leak (18%) - Avg repair: $4,800
4. Condenser coil (15%) - Avg repair: $6,100
5. Other (11%)

Maintenance Impact:
- Preventive maintenance reduces failure by 47%
- Units with quarterly PM: 4.4% failure rate
- Units with annual PM only: 11.2% failure rate
```

### Cost Queries
```bash
# Maintenance costs per square foot
$ arx cost maintenance --type school --age mature --detail
```
```
Maintenance Cost Analysis - Mature School Buildings
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sample: 2,341 buildings | 20-50 years old

Cost per sqft/year:
┌─────────────────────────────────────┐
│ HVAC        $0.89  ████████████     │
│ Electrical  $0.45  ██████           │
│ Plumbing    $0.38  █████            │
│ Roofing     $0.34  █████            │
│ Janitorial  $1.20  █████████████████│
│ Grounds     $0.22  ███              │
│ Other       $0.31  ████             │
├─────────────────────────────────────┤
│ TOTAL:      $3.79 per sqft/year    │
└─────────────────────────────────────┘

Trend: ↑ 4.2% YoY inflation-adjusted
```

### Retrofit ROI Queries
```bash
# LED conversion payback analysis
$ arx roi led --building-type office --region northeast --utility-rate 0.12
```
```
LED Retrofit ROI Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Projects analyzed: 423 completed retrofits

Investment: $1.20-2.40 per sqft
Energy Savings: 0.8-1.4 kWh/sqft/year
Simple Payback: 2.8-4.2 years

Distribution of Actual Paybacks:
<2 years:    ███░░░░░░░░░░░░░░░░░ 8%
2-3 years:   ████████████░░░░░░░░ 31%
3-4 years:   ████████████████░░░░ 42%
4-5 years:   ██████░░░░░░░░░░░░░░ 15%
>5 years:    ██░░░░░░░░░░░░░░░░░░ 4%

Best ROI factors:
- High existing wattage (>2W/sqft)
- Long operating hours (>3000 hr/yr)
- Utility incentives available
```

### Compliance Queries
```bash
# Local Law 97 compliance status
$ arx compliance LL97 --city NYC --year 2024
```
```
NYC Local Law 97 Compliance Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Buildings analyzed: 8,234

Compliance Status:
Compliant:       ████████████░░░░░░░░ 58%
Minor upgrades:  ██████░░░░░░░░░░░░░░ 27%
Major upgrades:  ███░░░░░░░░░░░░░░░░░ 11%
Critical:        █░░░░░░░░░░░░░░░░░░░ 4%

Estimated compliance costs:
$0-50K:          ████████░░░░░░░░░░░░ 35%
$50-200K:        ██████████░░░░░░░░░░ 41%
$200K-1M:        ████░░░░░░░░░░░░░░░░ 18%
>$1M:            █░░░░░░░░░░░░░░░░░░░ 6%

Common strategies:
1. Boiler replacement (34% of buildings)
2. BMS upgrade (28%)
3. Envelope improvements (22%)
4. Renewable energy (16%)
```

## Advanced Queries

### Correlation Analysis
```bash
# Correlate maintenance cost with equipment age
$ arx correlate maintenance.cost equipment.age --type school
```
```
Correlation: Maintenance Cost vs Equipment Age
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pearson coefficient: 0.73 (strong positive)
R²: 0.53

    $5│      ●●●●●●●
    $4│    ●●●●●●●●●●●●●
Cost $3│  ●●●●●●●●●●●●●
/sqft$2│●●●●●●●●●●
    $1│●●●●
     $0└──────────────────────
       0  5  10  15  20  25  30
           Equipment Age (years)

Insight: Each year of equipment age adds ~$0.12/sqft
to annual maintenance costs.
```

### Predictive Queries
```bash
# Predict equipment failure probability
$ arx predict failure --equipment "RTU-15ton" --age 12 --maintenance poor
```
```
Failure Prediction: 15-ton Rooftop Unit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model confidence: 87% (based on 4,231 similar units)

Failure Probability:
Next 6 months:  ████████░░░░░░░░░░░░ 38%
Next 12 months: ██████████████░░░░░░ 67%
Next 24 months: ██████████████████░░ 89%

Recommended actions:
1. Immediate compressor inspection ($400)
2. Refrigerant leak test ($200)
3. Control board diagnostic ($300)

Preventive replacement ROI:
- Replace now: $18,000
- Wait for failure: $24,000 (includes downtime)
- Recommendation: Schedule replacement
```

### Export Functions
```bash
# Export data for further analysis
$ arx export hvac.census --format csv --region midwest > hvac_data.csv
Exporting 127,843 HVAC units... done
Cost: $47.20 (charged to account)

$ arx export building.metrics --type office --format json
Exporting 8,923 building metrics... done
Cost: $122.00 (charged to account)
```

## Subscription Tiers

```bash
$ arx account status
```
```
╔══════════════════════════════════════════╗
║  ArxOS Market Data - Account Status      ║
╠══════════════════════════════════════════╣
║  Company: McKinsey & Company             ║
║  Tier: Professional ($25K/year)          ║
║  API Calls: 8,234 / 50,000 this month   ║
║  Export Credits: $1,243 / $5,000        ║
║                                          ║
║  Query History:                          ║
║  - Equipment failure rates    (1hr ago)  ║
║  - Energy benchmarks         (3hr ago)  ║
║  - Retrofit ROI             (1day ago)  ║
║                                          ║
║  Saved Queries: 14                       ║
║  Scheduled Reports: 3                    ║
╚══════════════════════════════════════════╝
```

## Query Builder Assistant
```bash
$ arx assistant
> I need to find all schools in Texas with HVAC over 20 years old

Suggested query:
arx query building.type="education" 
         location.state="TX" 
         equipment.hvac.age>20 
         --show building_id,city,hvac_count,oldest_unit

Run this query? [Y/n]: y

Found 341 buildings matching criteria...
[Results displayed]

> Show me the maintenance costs for these buildings

Suggested query:
arx cost maintenance --filter-previous --percentile 25,50,75

[Results displayed]
```

## Billing & Usage

```bash
$ arx billing summary --month october
```
```
October 2024 Billing Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Base Subscription:        $2,083.33
Query Overages:              $0.00
Export Charges:            $432.10
Custom Reports:            $500.00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total:                   $3,015.43

Top Query Types:
1. Equipment failure rates (34%)
2. Energy benchmarks (22%)
3. Maintenance costs (18%)
4. Compliance analysis (15%)
5. Other (11%)
```

## Why Terminal-Only Works

### For Data Buyers:
1. **Serious Users Only**: If they won't learn basic CLI, they don't need the data
2. **Scriptable**: Integrate into their existing workflows
3. **Fast**: No UI overhead, just raw speed
4. **Precise**: Exactly the query they want, not pre-built dashboards

### For ArxOS:
1. **No UI Maintenance**: One interface to rule them all
2. **Developer-Friendly**: API is the terminal
3. **Lower Costs**: No web hosting, CDN, etc.
4. **Brand Identity**: "We're so hardcore, we're terminal-only"

### The Learning Curve:
```bash
$ arx tutorial market
Welcome to ArxOS Market Data Tutorial

Lesson 1: Basic Queries
Try this: arx count buildings --type office

[User tries]
✓ Great! You found 12,384 office buildings.

Lesson 2: Filtering
Now add a region: arx count buildings --type office --region northeast

[Interactive tutorial continues...]
```

## Sample Customer Profiles

**McKinsey Consultant**: Runs 50 queries/day for client reports
**Insurance Underwriter**: Scheduled reports on equipment failure rates
**REIT Analyst**: Monitors maintenance cost trends across portfolios
**Energy Auditor**: Identifies retrofit opportunities by region
**Government Regulator**: Tracks compliance rates and costs

They all use the terminal. Because the data is worth it.

## The Terminal Advantage

```bash
# This would take 20 clicks in a web UI
$ arx compare eui --type school --year 2020 vs 2024 --region midwest --climate-normalized

# Chain queries with Unix pipes
$ arx list buildings --type hospital --state CA | arx analyze maintenance.cost

# Schedule recurring reports
$ arx schedule "roi led --region northeast" --weekly --email report@company.com

# Create custom aliases
$ alias schoolcost='arx cost maintenance --type school --age mature'
$ schoolcost --region pacific
```

## The Bottom Line

Making enterprise buyers use a terminal is unconventional. But ArxOS data is unconventional - it's real equipment performance from millions of ArxObjects, not surveys or estimates. 

If they want to know that Carrier 30XA chillers actually fail at 8.3% annually after 10 years (not the manufacturer's estimate), they'll type:

```bash
$ arx failure --equipment "Carrier 30XA" --age 10-15
```

And they'll pay $25K-$1M/year for the privilege.

Because nowhere else can they get this data. And a terminal command is a small price to pay for truth.
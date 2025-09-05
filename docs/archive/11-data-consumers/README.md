# Data Consumer Access Guide

> Scope: How third parties access anonymized building intelligence via RF-only gateways, including security and pricing tiers. Audience: partnerships, data consumers, sales engineering.
>
> Owner: Data Partnerships Lead.

## Accessing Building Intelligence Without Internet

Arxos provides multiple methods for data consumers to access building intelligence while maintaining our core promise: **Your data never touches the internet**.

## Access Methods

### 1. Direct Terminal Connection to Mesh Nodes

Data consumers connect directly to mesh nodes via local terminal (USB/Serial/Bluetooth) for queries and data export:

```bash
# Insurance company analyst connects to local mesh gateway
arxos connect /dev/ttyUSB0  # or bluetooth://arxos-gateway
> Connected to Los Angeles CBRE mesh node
> Authorized for anonymized data access

# Query electrical load patterns
arxos query --anonymized "electrical load patterns office buildings"
> Querying 247 office buildings via mesh network...
> Average electrical load: 67% capacity
> Peak usage hours: 9AM-11AM, 2PM-4PM
> Energy efficiency trends: 12% improvement year-over-year

# Export data for analysis
arxos export --anonymized --format=csv --region=west-coast
> Generating anonymized dataset...
> 15,847 buildings included
> Data exported to: /tmp/anonymized_building_data_20250830.csv

# Export directly via terminal (local connection)
arxos download /tmp/*.csv ./data/
```

### 2. Dedicated Data Gateway Nodes

Organizations install Arxos data gateway nodes at their facilities:

```bash
# Connect to company's local gateway node
arxos connect /dev/ttyUSB0  # Physical connection to gateway
> Connected to Arxos data gateway (NYC region)
> Mesh network access: 2,847 buildings online

# Run market intelligence queries
arxos market-intelligence "hvac efficiency northeast region"
> Querying via mesh network (no internet)...
> HVAC efficiency data for 2,847 buildings:
> Average efficiency: 82.3%
> Equipment age distribution: [data table]
> Maintenance cost trends: [data table]
```

### 3. Physical Air-Gapped Transfer

For ultra-sensitive customers requiring maximum security:

```bash
# Arxos team brings encrypted drive to customer site
# Drive connects directly to mesh gateway - no network

arxos export-secure --customer=government-agency --classification=restricted
> Exporting classified building intelligence...
> Data written to encrypted drive
> Drive ready for physical delivery
> No network transmission occurred
```

## Data Consumer Tiers

### Tier 1: Basic Access
- Connect via shared mesh gateways
- Physical access to gateway hardware
- Anonymized data only
- Pay-per-query or monthly subscription

### Tier 2: Premium Partners
- Dedicated mesh gateway at their facility
- Enhanced query permissions
- Detailed (anonymized) datasets
- Custom data exports

### Tier 3: Government/Critical Infrastructure
- Air-gapped physical transfers only
- Highest security classification
- No network access (mesh or internet)
- Premium pricing for ultra-secure access

## Use Cases

### Insurance Risk Assessment

```bash
arxos connect bluetooth://local-arxos-gateway
> Connected to mesh data gateway

# Analyze building risk factors
arxos risk-assessment --building-type=office --region=florida
> Analyzing 1,247 office buildings via mesh...
> Fire risk factors: Low (avg 2.1 violations per building)
> Electrical risk: Medium (23% of buildings at >80% capacity)
> Structural risk: Low (98.7% code compliant)
> Overall risk score: 7.2/10 (acceptable)

# Export for actuarial models
arxos export-risk-data --format=actuarial-tables
> Exporting risk assessment data...
> File ready for download via SCP
```

### Real Estate Market Analysis

```bash
arxos connect /dev/ttyACM0  # USB connection to gateway

# Find comparable properties
arxos comparable-analysis --building-type=retail --sqft-range=5000-20000
> Analyzing 347 retail spaces via mesh network...
> Average electrical capacity: 71%
> HVAC efficiency: 79%
> Foot traffic optimization score: 6.8/10
> Typical build-out costs: $47/sqft

# Download analysis
arxos download-comparables --format=excel
> Market analysis ready for download
```

### Municipal Compliance Monitoring

```bash
arxos connect serial://municipal-arxos-node

# Check building compliance
arxos compliance-check --district=downtown --code=nec-2023
> Checking 847 buildings against NEC 2023...
> Compliant: 762 buildings (89.9%)
> Minor violations: 73 buildings
> Major violations: 12 buildings
> Generating inspection priority list...

# Export violations for field inspections
arxos export-violations --priority=high --format=mobile-app
> High priority violations exported
> Field inspection routes optimized
```

## Data Pricing via Mesh Network

### BILT Token Payments

```bash
# Purchase data credits using BILT tokens
arxos purchase-data --credits=1000 --payment=bilt-tokens
> Purchasing 1000 query credits...
> Payment confirmed via mesh network
> Credits added to account balance

# Use credits for premium queries
arxos query-premium --credits=10 "detailed-electrical-analysis northeast"
> Using 10 credits for premium query...
> Detailed analysis from 4,847 buildings...
> [comprehensive data results]
```

### Traditional Contracts

```bash
# Check contract balance
arxos account-status
> Organization: ABC Insurance Corp
> Contract: Premium Data Access
> Monthly queries remaining: 8,234
> Data export quota: 47GB remaining
> Contract renewal: 2025-09-30
```

## Data Query Examples

### Basic Queries (1 credit each)

```bash
arxos query "outlets per sqft office buildings"
arxos query "average hvac age retail spaces"
arxos query "emergency exit compliance hotels"
```

### Advanced Queries (5-10 credits)

```bash
arxos query-advanced "predictive maintenance schedule all hvac systems"
arxos query-advanced "electrical load forecasting next 30 days"
arxos query-advanced "fire risk scoring with contributing factors"
```

### Custom Reports (50+ credits)

```bash
arxos generate-report --type=portfolio-analysis --buildings=west-coast-offices
arxos generate-report --type=insurance-underwriting --risk-factors=comprehensive
arxos generate-report --type=market-comparables --radius=5mi --detail=high
```

## Security & Privacy

### Data Anonymization

All consumer queries return anonymized data by default:
- Building IDs are hashed
- Exact addresses removed
- Owner information stripped
- Tenant details excluded

### Access Control

```bash
# View your permissions
arxos permissions
> User: insurance-analyst
> Access level: Tier 2 - Premium
> Allowed queries: Anonymized aggregate data
> Regions: Northeast, Southeast
> Export formats: CSV, JSON, Excel
> Rate limit: 100 queries/hour
```

### Audit Trail

```bash
# All queries are logged for compliance
arxos audit-log --days=30
> Last 30 days activity:
> Total queries: 1,234
> Data exported: 127GB
> Credits used: 8,923
> Access locations: [mesh node list]
```

## Network Architecture

```
┌─────────────────────────────────────────┐
│         Data Consumer Office            │
│                                         │
│    ┌──────────────────────────┐        │
│    │  SSH Terminal Client      │        │
│    └────────────┬─────────────┘        │
│                 │                       │
│                 ▼                       │
│    ┌──────────────────────────┐        │
│    │  Local Mesh Gateway Node │        │
│    │  (On building roof)      │        │
│    └────────────┬─────────────┘        │
└─────────────────┼───────────────────────┘
                  │
                  │ LoRa RF Only
                  │ (No Internet)
                  ▼
     ┌───────────────────────────┐
     │   Regional Mesh Network   │
     │  (Thousands of buildings) │
     └───────────────────────────┘
```

## Getting Started

### 1. Request Access

```bash
# Contact Arxos for data access
email: data-access@arxos.io
phone: 1-800-ARXOS-RF

# Or apply via mesh network
arxos apply-for-access --organization="ABC Insurance" --use-case="risk-assessment"
```

### 2. Install Gateway (Premium Tier)

```bash
# Arxos team installs mesh gateway at your facility
# Gateway includes:
- ESP32 mesh node with LoRa radio
- Directional antenna for optimal coverage
- SSH server for secure access
- Local SQLite cache for fast queries
```

### 3. Connect and Query

```bash
# Once approved, connect via SSH
ssh your-username@your-gateway.arxos.mesh

# Start querying building intelligence
arxos help
arxos query "your first query"
```

## Support

For data consumer support:
- SSH Help: `arxos help` within terminal
- Technical Issues: support@arxos.io
- Billing/Credits: billing@arxos.io

## Related

- [Terminal Data Marketplace](./TERMINAL_DATA_MARKETPLACE.md)

---

*Access the world's building intelligence without ever touching the internet*
# ArxOS Data Marketplace

Real-time trading of building intelligence with time-decay pricing.

## Overview

ArxOS creates a futures market for physical reality. Fresh building scans from field workers are auctioned in real-time, with prices decaying over time as data becomes less valuable.

## Architecture

```
Field Scanner → ArxObject (13 bytes) → LoRaWAN → Marketplace → Brokers
```

### Packet Structure (23 bytes total)
- ArxObject: 13 bytes
- Timestamp: 4 bytes  
- Current bid: 2 bytes
- Bidder ID: 2 bytes
- TTL: 2 bytes

## Pricing Model

### Time Decay (Dutch Auction)
- **T+0**: $10 (fresh scan)
- **T+1min**: $5 (50% decay)
- **T+2min**: $2.50
- **T+5min**: $1 (reserve price)

### Regional Multipliers
- Normal: 1x
- Construction zone: 2x
- Natural disaster: 5x
- Emergency inspection: 3x

### Object Type Base Prices
- Door: $0.30
- Window: $0.25
- Column: $0.35
- Wall: $0.15
- Floor: $0.10

## Broker API

Commands fit in single LoRaWAN packets (23 bytes):

```rust
// Subscribe to region + object types
BrokerCommand::subscribe(broker_id, region, object_types)

// Place competitive bid
BrokerCommand::bid(broker_id, building_id, amount)

// Instant purchase at current price
BrokerCommand::instant_buy(broker_id, building_id)
```

## Market Dynamics

### Supply/Demand
- High scanner activity → prices drop
- Backlog > 100 orders → 1.5x multiplier
- Broker competition tracked for win rates

### Revenue Potential
With 130,000 schools as LoRaWAN nodes:
- Coverage: 95% of US population
- Data volume: 10,000+ buildings/month
- Market liquidity: Instant price discovery

## Implementation

```rust
use arxos_core::marketplace::{MarketPacket, DutchAuction, PricingEngine};

// Start auction for new scan
let auction = DutchAuction::new(arxobject, start_price);

// Process broker bid
market.process_bid(building_id, bid_amount, broker_id)?;

// Execute sale
broker_session.execute_purchase(arxobject, final_price)?;
```

## Why It Works

1. **Data is perishable** - Fresh scans worth 10x more than day-old
2. **13-byte packets** - Entire market fits in RF mesh
3. **No internet required** - Can't be intercepted or manipulated
4. **Automatic price discovery** - Dutch auction ensures liquidity

The marketplace turns every field worker into a data producer and every insurance company, real estate firm, and city planner into a competitive bidder for real-time building intelligence.
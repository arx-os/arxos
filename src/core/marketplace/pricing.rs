//! Dynamic Pricing Engine for Building Intelligence Data
//! 
//! Implements supply/demand curves and geographic heat maps

use crate::arxobject::ArxObject;
use std::collections::HashMap;

/// Geographic region identifier (could be ZIP, county, etc.)
pub type RegionId = u32;

/// Pricing engine that adjusts based on market conditions
pub struct PricingEngine {
    /// Base prices by object type
    base_prices: HashMap<u8, f32>,
    /// Regional multipliers (disaster areas, construction zones)
    regional_heat: HashMap<RegionId, f32>,
    /// Supply/demand tracking
    supply_curve: SupplyCurve,
    demand_curve: DemandCurve,
    /// Historical price data for ML predictions
    price_history: Vec<PricePoint>,
}

#[derive(Clone)]
pub struct PricePoint {
    pub timestamp: u64,
    pub region: RegionId,
    pub object_type: u8,
    pub price: f32,
    pub volume: u32,
}

pub struct SupplyCurve {
    /// Current supply rate (objects per hour)
    pub current_rate: f32,
    /// Rolling average over past 24 hours
    pub avg_rate_24h: f32,
    /// Supply elasticity factor
    pub elasticity: f32,
}

pub struct DemandCurve {
    /// Current demand rate (purchases per hour)
    pub current_rate: f32,
    /// Unfilled orders
    pub backlog: u32,
    /// Price sensitivity factor
    pub elasticity: f32,
}

impl PricingEngine {
    pub fn new() -> Self {
        use crate::arxobject::object_types;
        
        let mut base_prices = HashMap::new();
        base_prices.insert(object_types::FLOOR, 10.0);
        base_prices.insert(object_types::WALL, 15.0);
        base_prices.insert(object_types::CEILING, 12.0);
        base_prices.insert(object_types::DOOR, 30.0);
        base_prices.insert(object_types::WINDOW, 25.0);
        base_prices.insert(object_types::COLUMN, 35.0);
        base_prices.insert(object_types::GENERIC, 5.0);

        Self {
            base_prices,
            regional_heat: HashMap::new(),
            supply_curve: SupplyCurve {
                current_rate: 100.0,
                avg_rate_24h: 100.0,
                elasticity: 0.5,
            },
            demand_curve: DemandCurve {
                current_rate: 80.0,
                backlog: 0,
                elasticity: 0.7,
            },
            price_history: Vec::new(),
        }
    }

    /// Calculate real-time price for an ArxObject
    pub fn calculate_price(&self, object: &ArxObject, region: RegionId) -> f32 {
        let base = self.base_prices.get(&object.object_type)
            .copied()
            .unwrap_or(5.0);

        let regional_mult = self.regional_heat.get(&region)
            .copied()
            .unwrap_or(1.0);

        let supply_demand_ratio = self.demand_curve.current_rate / 
            self.supply_curve.current_rate.max(1.0);

        let urgency_mult = if self.demand_curve.backlog > 100 {
            1.5 // High backlog increases prices
        } else if self.demand_curve.backlog > 50 {
            1.2
        } else {
            1.0
        };

        base * regional_mult * supply_demand_ratio * urgency_mult
    }

    /// Update regional heat map based on events
    pub fn update_regional_heat(&mut self, region: RegionId, event: MarketEvent) {
        let current = self.regional_heat.entry(region).or_insert(1.0);
        
        *current = match event {
            MarketEvent::NaturalDisaster => (*current * 5.0).min(10.0),
            MarketEvent::Construction => (*current * 2.0).min(5.0),
            MarketEvent::Inspection => (*current * 1.5).min(3.0),
            MarketEvent::Normal => (*current * 0.95).max(0.5), // Decay toward normal
        };
    }

    /// Update supply/demand curves based on market activity
    pub fn update_market_dynamics(&mut self, supply_delta: f32, demand_delta: f32) {
        // Update supply
        self.supply_curve.current_rate = 
            (self.supply_curve.current_rate + supply_delta).max(0.0);
        
        // Rolling average
        self.supply_curve.avg_rate_24h = 
            self.supply_curve.avg_rate_24h * 0.95 + self.supply_curve.current_rate * 0.05;

        // Update demand
        self.demand_curve.current_rate = 
            (self.demand_curve.current_rate + demand_delta).max(0.0);
    }

    /// Add order to backlog
    pub fn add_to_backlog(&mut self, count: u32) {
        self.demand_curve.backlog += count;
    }

    /// Clear orders from backlog
    pub fn clear_from_backlog(&mut self, count: u32) {
        self.demand_curve.backlog = self.demand_curve.backlog.saturating_sub(count);
    }

    /// Record sale for historical analysis
    pub fn record_sale(&mut self, region: RegionId, object_type: u8, price: f32) {
        self.price_history.push(PricePoint {
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            region,
            object_type,
            price,
            volume: 1,
        });

        // Keep only last 10,000 sales
        if self.price_history.len() > 10_000 {
            self.price_history.remove(0);
        }
    }

    /// Get price prediction based on historical data
    pub fn predict_price(&self, region: RegionId, object_type: u8, hours_ahead: u32) -> f32 {
        // Simple moving average prediction (could be replaced with ML model)
        let relevant_history: Vec<&PricePoint> = self.price_history.iter()
            .filter(|p| p.region == region && p.object_type == object_type)
            .collect();

        if relevant_history.is_empty() {
            return self.base_prices.get(&object_type).copied().unwrap_or(5.0);
        }

        let recent_avg = relevant_history.iter()
            .rev()
            .take(100)
            .map(|p| p.price)
            .sum::<f32>() / relevant_history.len().min(100) as f32;

        // Add time decay factor
        let decay = 0.95_f32.powi(hours_ahead as i32);
        recent_avg * decay
    }
}

/// Market events that affect pricing
pub enum MarketEvent {
    NaturalDisaster,
    Construction,
    Inspection,
    Normal,
}

/// Broker competition tracker
pub struct BrokerCompetition {
    /// Active brokers and their recent bids
    brokers: HashMap<u16, BrokerProfile>,
    /// Winning bid history
    winning_bids: Vec<(u16, f32)>, // broker_id, price
}

pub struct BrokerProfile {
    pub id: u16,
    pub total_purchases: u32,
    pub avg_bid: f32,
    pub win_rate: f32,
    pub specialization: Option<u8>, // Preferred object type
}

impl BrokerCompetition {
    pub fn new() -> Self {
        Self {
            brokers: HashMap::new(),
            winning_bids: Vec::new(),
        }
    }

    /// Record bid outcome
    pub fn record_bid(&mut self, broker_id: u16, bid: f32, won: bool) {
        let broker = self.brokers.entry(broker_id).or_insert(BrokerProfile {
            id: broker_id,
            total_purchases: 0,
            avg_bid: bid,
            win_rate: 0.0,
            specialization: None,
        });

        // Update stats
        let bid_count = broker.total_purchases + 1;
        broker.avg_bid = (broker.avg_bid * broker.total_purchases as f32 + bid) / bid_count as f32;
        
        if won {
            broker.total_purchases += 1;
            self.winning_bids.push((broker_id, bid));
        }

        // Update win rate
        let total_bids = self.winning_bids.iter()
            .filter(|(id, _)| *id == broker_id)
            .count() as f32;
        broker.win_rate = total_bids / bid_count as f32;
    }

    /// Get competitive pricing intel
    pub fn get_competitive_price(&self) -> f32 {
        if self.winning_bids.is_empty() {
            return 50.0; // Default
        }

        // Average of last 10 winning bids
        self.winning_bids.iter()
            .rev()
            .take(10)
            .map(|(_, price)| *price)
            .sum::<f32>() / self.winning_bids.len().min(10) as f32
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_dynamic_pricing() {
        let mut engine = PricingEngine::new();
        let object = ArxObject::new(0x0001, 0x04, 0, 0, 0); // DOOR type
        
        let base_price = engine.calculate_price(&object, 12345);
        assert!(base_price > 0.0);
        
        // Simulate disaster - price should spike
        engine.update_regional_heat(12345, MarketEvent::NaturalDisaster);
        let disaster_price = engine.calculate_price(&object, 12345);
        assert!(disaster_price > base_price * 3.0);
        
        // Add backlog - price should increase
        engine.add_to_backlog(200);
        let backlog_price = engine.calculate_price(&object, 12345);
        assert!(backlog_price > disaster_price);
    }
    
    #[test]
    fn test_broker_competition() {
        let mut competition = BrokerCompetition::new();
        
        competition.record_bid(0x1001, 100.0, true);
        competition.record_bid(0x1002, 90.0, false);
        competition.record_bid(0x1001, 110.0, true);
        competition.record_bid(0x1003, 105.0, false);
        
        let competitive_price = competition.get_competitive_price();
        assert!(competitive_price > 100.0); // Should reflect winning bids
        
        let broker = &competition.brokers[&0x1001];
        assert_eq!(broker.total_purchases, 2);
        assert!(broker.win_rate > 0.5);
    }
}
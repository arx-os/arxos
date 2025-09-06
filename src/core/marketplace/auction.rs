//! Auction Engine for Real-time Building Data
//! 
//! Implements Dutch auction with time-decay pricing

use crate::arxobject::ArxObject;
use std::time::{SystemTime, Duration};

/// Dutch auction - price drops over time to ensure sale
pub struct DutchAuction {
    pub object: ArxObject,
    pub start_price: u32, // cents
    pub reserve_price: u32,
    pub start_time: SystemTime,
    pub duration: Duration,
    pub decay_curve: DecayCurve,
}

#[derive(Clone, Copy)]
pub enum DecayCurve {
    Linear,
    Exponential { half_life: Duration },
    Step { drops: Vec<(Duration, u32)> },
}

impl DutchAuction {
    pub fn new(object: ArxObject, start_price: u32) -> Self {
        Self {
            object,
            start_price,
            reserve_price: start_price / 10, // 10% reserve
            start_time: SystemTime::now(),
            duration: Duration::from_secs(300), // 5 minutes
            decay_curve: DecayCurve::Exponential { 
                half_life: Duration::from_secs(60) // Price halves each minute
            },
        }
    }

    /// Get current price based on elapsed time
    pub fn current_price(&self) -> u32 {
        let elapsed = SystemTime::now()
            .duration_since(self.start_time)
            .unwrap_or(Duration::ZERO);

        if elapsed >= self.duration {
            return self.reserve_price;
        }

        match self.decay_curve {
            DecayCurve::Linear => {
                let progress = elapsed.as_secs() as f64 / self.duration.as_secs() as f64;
                let price_drop = ((self.start_price - self.reserve_price) as f64 * progress) as u32;
                self.start_price - price_drop
            },
            DecayCurve::Exponential { half_life } => {
                let half_lives = elapsed.as_secs() as f64 / half_life.as_secs() as f64;
                let multiplier = 0.5_f64.powf(half_lives);
                let price = (self.start_price as f64 * multiplier) as u32;
                price.max(self.reserve_price)
            },
            DecayCurve::Step { ref drops } => {
                for (threshold, price) in drops {
                    if elapsed < *threshold {
                        return *price;
                    }
                }
                self.reserve_price
            }
        }
    }

    /// Check if auction has expired
    pub fn is_expired(&self) -> bool {
        SystemTime::now().duration_since(self.start_time)
            .unwrap_or(Duration::ZERO) >= self.duration
    }
}

/// Manages multiple concurrent auctions
pub struct AuctionHouse {
    pub active_auctions: Vec<DutchAuction>,
    pub completed_sales: Vec<(ArxObject, u32, u16)>, // object, price, buyer
    pub revenue_total: u64,
}

impl AuctionHouse {
    pub fn new() -> Self {
        Self {
            active_auctions: Vec::new(),
            completed_sales: Vec::new(),
            revenue_total: 0,
        }
    }

    /// List new data on the market
    pub fn list_data(&mut self, object: ArxObject, pricing_tier: PricingTier) {
        let start_price = pricing_tier.calculate_price(&object);
        let auction = DutchAuction::new(object, start_price);
        self.active_auctions.push(auction);
    }

    /// Execute purchase at current price
    pub fn execute_purchase(&mut self, index: usize, buyer_id: u16) -> Result<u32, &'static str> {
        if index >= self.active_auctions.len() {
            return Err("Invalid auction index");
        }

        let auction = &self.active_auctions[index];
        if auction.is_expired() {
            self.active_auctions.remove(index);
            return Err("Auction expired");
        }

        let price = auction.current_price();
        let object = auction.object;
        
        // Complete sale
        self.completed_sales.push((object, price, buyer_id));
        self.revenue_total += price as u64;
        self.active_auctions.remove(index);

        Ok(price)
    }

    /// Clean up expired auctions
    pub fn cleanup_expired(&mut self) {
        self.active_auctions.retain(|auction| !auction.is_expired());
    }

    /// Get market statistics
    pub fn get_stats(&self) -> MarketStats {
        let avg_price = if self.completed_sales.is_empty() {
            0
        } else {
            self.completed_sales.iter()
                .map(|(_, price, _)| *price as u64)
                .sum::<u64>() / self.completed_sales.len() as u64
        } as u32;

        MarketStats {
            active_listings: self.active_auctions.len(),
            total_sales: self.completed_sales.len(),
            revenue_total: self.revenue_total,
            average_price: avg_price,
        }
    }
}

pub struct MarketStats {
    pub active_listings: usize,
    pub total_sales: usize,
    pub revenue_total: u64,
    pub average_price: u32,
}

/// Pricing tiers based on data freshness and completeness
pub enum PricingTier {
    Premium,   // Complete building, <1 hour old
    Standard,  // Partial scan, <1 day old  
    Budget,    // Historical data, >1 day old
}

impl PricingTier {
    pub fn calculate_price(&self, object: &ArxObject) -> u32 {
        use crate::arxobject::object_types;
        
        let base = match object.object_type {
            t if t == object_types::DOOR => 50,
            t if t == object_types::WINDOW => 40,
            t if t == object_types::COLUMN => 60,
            t if t == object_types::WALL => 20,
            _ => 10,
        };

        match self {
            PricingTier::Premium => base * 10,  // 10x for fresh
            PricingTier::Standard => base * 3,   // 3x for recent
            PricingTier::Budget => base,         // Base for old
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;
    
    #[test]
    fn test_dutch_auction_decay() {
        let object = ArxObject::new(0x0001, 0x02, 0, 0, 0);
        let auction = DutchAuction::new(object, 1000);
        
        let initial_price = auction.current_price();
        assert_eq!(initial_price, 1000);
        
        thread::sleep(Duration::from_millis(100));
        let later_price = auction.current_price();
        assert!(later_price < initial_price);
        assert!(later_price >= auction.reserve_price);
    }
    
    #[test]
    fn test_auction_house_operations() {
        let mut house = AuctionHouse::new();
        let object = ArxObject::new(0x0001, 0x02, 0, 0, 0);
        
        house.list_data(object, PricingTier::Premium);
        assert_eq!(house.active_auctions.len(), 1);
        
        let price = house.execute_purchase(0, 0x1001).unwrap();
        assert!(price > 0);
        assert_eq!(house.completed_sales.len(), 1);
        assert_eq!(house.active_auctions.len(), 0);
        
        let stats = house.get_stats();
        assert_eq!(stats.total_sales, 1);
        assert_eq!(stats.revenue_total, price as u64);
    }
}
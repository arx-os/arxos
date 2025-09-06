//! Real-time Data Marketplace for Building Intelligence
//! 
//! Implements time-decay pricing and competitive bidding over RF mesh

pub mod auction;
pub mod pricing;
pub mod broker_api;

use crate::arxobject::ArxObject;
use std::time::{SystemTime, Duration};

/// Market data packet - fits in LoRaWAN payload
#[repr(C, packed)]
pub struct MarketPacket {
    /// ArxObject being traded
    pub object: ArxObject,
    /// Timestamp (seconds since epoch, truncated)
    pub timestamp: u32,
    /// Current highest bid (cents)
    pub bid: u16,
    /// Bidder ID
    pub bidder: u16,
    /// Time remaining in auction (seconds)
    pub ttl: u16,
}

impl MarketPacket {
    pub const SIZE: usize = 13 + 4 + 2 + 2 + 2; // 23 bytes total

    pub fn new(object: ArxObject) -> Self {
        Self {
            object,
            timestamp: SystemTime::now()
                .duration_since(SystemTime::UNIX_EPOCH)
                .unwrap()
                .as_secs() as u32,
            bid: 0,
            bidder: 0,
            ttl: 300, // 5 minute auction default
        }
    }

    pub fn to_bytes(&self) -> [u8; Self::SIZE] {
        let mut bytes = [0u8; Self::SIZE];
        bytes[0..13].copy_from_slice(&self.object.to_bytes());
        bytes[13..17].copy_from_slice(&self.timestamp.to_le_bytes());
        bytes[17..19].copy_from_slice(&self.bid.to_le_bytes());
        bytes[19..21].copy_from_slice(&self.bidder.to_le_bytes());
        bytes[21..23].copy_from_slice(&self.ttl.to_le_bytes());
        bytes
    }

    pub fn from_bytes(bytes: &[u8; Self::SIZE]) -> Self {
        let mut object_bytes = [0u8; 13];
        object_bytes.copy_from_slice(&bytes[0..13]);
        
        Self {
            object: ArxObject::from_bytes(&object_bytes),
            timestamp: u32::from_le_bytes([bytes[13], bytes[14], bytes[15], bytes[16]]),
            bid: u16::from_le_bytes([bytes[17], bytes[18]]),
            bidder: u16::from_le_bytes([bytes[19], bytes[20]]),
            ttl: u16::from_le_bytes([bytes[21], bytes[22]]),
        }
    }
}

/// Market state for a geographic region
pub struct RegionalMarket {
    /// Active auctions by building ID
    pub auctions: std::collections::HashMap<u32, MarketPacket>,
    /// Historical prices for pricing model
    pub price_history: Vec<(SystemTime, u16)>,
    /// Regional multiplier (disaster areas = higher)
    pub heat_multiplier: f32,
}

impl RegionalMarket {
    pub fn new() -> Self {
        Self {
            auctions: std::collections::HashMap::new(),
            price_history: Vec::new(),
            heat_multiplier: 1.0,
        }
    }

    /// Submit new scan to market
    pub fn submit_scan(&mut self, object: ArxObject) -> MarketPacket {
        let mut packet = MarketPacket::new(object);
        
        // Calculate starting price based on data freshness and heat
        let base_price = self.calculate_base_price(&object);
        packet.bid = (base_price * self.heat_multiplier) as u16;
        
        // Add to active auctions
        let building_id = object.building_id as u32 | ((object.x as u32) << 16);
        self.auctions.insert(building_id, packet.clone());
        
        packet
    }

    /// Process incoming bid
    pub fn process_bid(&mut self, building_id: u32, bid: u16, bidder: u16) -> Result<(), &'static str> {
        let auction = self.auctions.get_mut(&building_id)
            .ok_or("No active auction")?;
        
        if bid <= auction.bid {
            return Err("Bid too low");
        }
        
        if auction.ttl == 0 {
            return Err("Auction expired");
        }
        
        auction.bid = bid;
        auction.bidder = bidder;
        
        // Record price for history
        self.price_history.push((SystemTime::now(), bid));
        
        Ok(())
    }

    /// Calculate base price using time-decay model
    fn calculate_base_price(&self, object: &ArxObject) -> f32 {
        use crate::arxobject::object_types;
        
        // Base prices by object type (cents)
        let type_price = match object.object_type {
            t if t == object_types::FLOOR => 10.0,
            t if t == object_types::WALL => 15.0,
            t if t == object_types::CEILING => 8.0,
            t if t == object_types::DOOR => 25.0,
            t if t == object_types::WINDOW => 20.0,
            t if t == object_types::COLUMN => 30.0,
            _ => 5.0,
        };
        
        // Recent history premium
        let recency_multiplier = if self.price_history.is_empty() {
            1.0
        } else {
            let avg_recent = self.price_history.iter()
                .rev()
                .take(10)
                .map(|(_, price)| *price as f32)
                .sum::<f32>() / 10.0.min(self.price_history.len() as f32);
            
            (avg_recent / 100.0).max(1.0)
        };
        
        type_price * recency_multiplier
    }

    /// Update regional heat based on demand
    pub fn update_heat(&mut self) {
        let recent_bids = self.price_history.iter()
            .rev()
            .take(100)
            .map(|(_, price)| *price as f32)
            .collect::<Vec<_>>();
        
        if recent_bids.len() >= 10 {
            let avg = recent_bids.iter().sum::<f32>() / recent_bids.len() as f32;
            let baseline = 50.0; // 50 cents baseline
            
            self.heat_multiplier = (avg / baseline).clamp(0.5, 5.0);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_market_packet_serialization() {
        let object = ArxObject::new(0x0042, 0x01, 1000, 2000, 1500);
        let packet = MarketPacket::new(object);
        
        let bytes = packet.to_bytes();
        assert_eq!(bytes.len(), MarketPacket::SIZE);
        
        let reconstructed = MarketPacket::from_bytes(&bytes);
        assert_eq!(reconstructed.object.building_id, object.building_id);
        assert_eq!(reconstructed.ttl, 300);
    }
    
    #[test]
    fn test_competitive_bidding() {
        let mut market = RegionalMarket::new();
        let object = ArxObject::new(0x0001, 0x02, 0, 0, 0);
        
        let packet = market.submit_scan(object);
        let building_id = 0x0001;
        
        // First bid
        assert!(market.process_bid(building_id, 100, 0x1001).is_ok());
        
        // Higher bid wins
        assert!(market.process_bid(building_id, 150, 0x1002).is_ok());
        
        // Lower bid rejected
        assert!(market.process_bid(building_id, 120, 0x1003).is_err());
        
        let auction = &market.auctions[&building_id];
        assert_eq!(auction.bid, 150);
        assert_eq!(auction.bidder, 0x1002);
    }
    
    #[test]
    fn test_heat_multiplier() {
        let mut market = RegionalMarket::new();
        
        // Simulate high demand
        for i in 0..20 {
            market.price_history.push((SystemTime::now(), 100 + i * 10));
        }
        
        market.update_heat();
        assert!(market.heat_multiplier > 1.0);
    }
}
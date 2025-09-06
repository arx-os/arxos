//! Broker API for Real-time Data Marketplace
//! 
//! RF-mesh compatible protocol for competitive bidding

use crate::arxobject::ArxObject;
use crate::marketplace::{MarketPacket, RegionalMarket};

/// Broker command - fits in LoRaWAN packet
#[repr(C, packed)]
pub struct BrokerCommand {
    pub cmd_type: u8,
    pub broker_id: u16,
    pub payload: [u8; 20], // Flexible payload
}

impl BrokerCommand {
    pub const SIZE: usize = 23;

    pub fn subscribe(broker_id: u16, region: u32, object_types: u8) -> Self {
        let mut payload = [0u8; 20];
        payload[0..4].copy_from_slice(&region.to_le_bytes());
        payload[4] = object_types;
        
        Self {
            cmd_type: CommandType::Subscribe as u8,
            broker_id,
            payload,
        }
    }

    pub fn bid(broker_id: u16, building_id: u32, amount: u16) -> Self {
        let mut payload = [0u8; 20];
        payload[0..4].copy_from_slice(&building_id.to_le_bytes());
        payload[4..6].copy_from_slice(&amount.to_le_bytes());
        
        Self {
            cmd_type: CommandType::Bid as u8,
            broker_id,
            payload,
        }
    }

    pub fn instant_buy(broker_id: u16, building_id: u32) -> Self {
        let mut payload = [0u8; 20];
        payload[0..4].copy_from_slice(&building_id.to_le_bytes());
        
        Self {
            cmd_type: CommandType::InstantBuy as u8,
            broker_id,
            payload,
        }
    }
}

#[repr(u8)]
enum CommandType {
    Subscribe = 0x01,
    Bid = 0x02,
    InstantBuy = 0x03,
    Query = 0x04,
    Cancel = 0x05,
}

/// Broker session managing subscriptions and bids
pub struct BrokerSession {
    pub broker_id: u16,
    pub subscriptions: Vec<Subscription>,
    pub active_bids: Vec<ActiveBid>,
    pub purchase_history: Vec<Purchase>,
    pub credit_balance: u32, // cents
}

pub struct Subscription {
    pub region: u32,
    pub object_types: u8, // Bitmask of interested types
    pub max_price: u16,
    pub auto_buy: bool,
}

pub struct ActiveBid {
    pub building_id: u32,
    pub amount: u16,
    pub timestamp: u64,
    pub status: BidStatus,
}

#[derive(Clone, Copy, PartialEq)]
pub enum BidStatus {
    Pending,
    Winning,
    Outbid,
    Expired,
    Won,
}

pub struct Purchase {
    pub object: ArxObject,
    pub price: u16,
    pub timestamp: u64,
}

impl BrokerSession {
    pub fn new(broker_id: u16, initial_credit: u32) -> Self {
        Self {
            broker_id,
            subscriptions: Vec::new(),
            active_bids: Vec::new(),
            purchase_history: Vec::new(),
            credit_balance: initial_credit,
        }
    }

    /// Process incoming market data against subscriptions
    pub fn process_market_data(&mut self, packet: &MarketPacket) -> Option<BrokerCommand> {
        // Check if this matches any subscription
        for sub in &self.subscriptions {
            if self.matches_subscription(&packet.object, sub) {
                // Auto-buy if enabled and price is right
                if sub.auto_buy && packet.bid <= sub.max_price {
                    if self.credit_balance >= packet.bid as u32 {
                        let building_id = packet.object.building_id as u32 | 
                                        ((packet.object.x as u32) << 16);
                        return Some(BrokerCommand::instant_buy(self.broker_id, building_id));
                    }
                }
                
                // Otherwise prepare bid
                if packet.bid < sub.max_price {
                    let bid_amount = packet.bid + (sub.max_price - packet.bid) / 2;
                    if self.credit_balance >= bid_amount as u32 {
                        let building_id = packet.object.building_id as u32 | 
                                        ((packet.object.x as u32) << 16);
                        return Some(BrokerCommand::bid(self.broker_id, building_id, bid_amount));
                    }
                }
            }
        }
        None
    }

    fn matches_subscription(&self, object: &ArxObject, sub: &Subscription) -> bool {
        // Check object type matches subscription filter
        (sub.object_types & (1 << object.object_type)) != 0
    }

    /// Execute purchase and update balance
    pub fn execute_purchase(&mut self, object: ArxObject, price: u16) -> Result<(), &'static str> {
        if self.credit_balance < price as u32 {
            return Err("Insufficient credit");
        }

        self.credit_balance -= price as u32;
        self.purchase_history.push(Purchase {
            object,
            price,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        });

        Ok(())
    }

    /// Get broker statistics
    pub fn get_stats(&self) -> BrokerStats {
        let total_spent = self.purchase_history.iter()
            .map(|p| p.price as u32)
            .sum();

        let avg_price = if self.purchase_history.is_empty() {
            0
        } else {
            total_spent / self.purchase_history.len() as u32
        };

        BrokerStats {
            total_purchases: self.purchase_history.len() as u32,
            total_spent,
            average_price: avg_price,
            credit_remaining: self.credit_balance,
            active_bids: self.active_bids.iter()
                .filter(|b| b.status == BidStatus::Pending || b.status == BidStatus::Winning)
                .count() as u32,
        }
    }
}

pub struct BrokerStats {
    pub total_purchases: u32,
    pub total_spent: u32,
    pub average_price: u32,
    pub credit_remaining: u32,
    pub active_bids: u32,
}

/// Market maker providing liquidity
pub struct MarketMaker {
    pub broker_id: u16,
    pub spread: f32, // Percentage spread for market making
    pub inventory: Vec<ArxObject>,
    pub max_inventory: usize,
}

impl MarketMaker {
    pub fn new(broker_id: u16) -> Self {
        Self {
            broker_id,
            spread: 0.05, // 5% spread
            inventory: Vec::new(),
            max_inventory: 1000,
        }
    }

    /// Quote bid/ask prices
    pub fn quote(&self, market_price: f32) -> (f32, f32) {
        let bid = market_price * (1.0 - self.spread);
        let ask = market_price * (1.0 + self.spread);
        (bid, ask)
    }

    /// Should buy at this price?
    pub fn should_buy(&self, price: f32, market_avg: f32) -> bool {
        self.inventory.len() < self.max_inventory && 
        price < market_avg * (1.0 - self.spread * 2.0)
    }

    /// Should sell from inventory?
    pub fn should_sell(&self, price: f32, market_avg: f32) -> bool {
        !self.inventory.is_empty() && 
        price > market_avg * (1.0 + self.spread)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::arxobject::object_types;
    
    #[test]
    fn test_broker_session() {
        let mut session = BrokerSession::new(0x1001, 10000);
        
        // Add subscription for doors and windows
        session.subscriptions.push(Subscription {
            region: 12345,
            object_types: (1 << object_types::DOOR) | (1 << object_types::WINDOW),
            max_price: 100,
            auto_buy: false,
        });
        
        // Process market data for a door
        let door = ArxObject::new(0x0001, object_types::DOOR, 0, 0, 0);
        let packet = MarketPacket {
            object: door,
            timestamp: 0,
            bid: 50,
            bidder: 0,
            ttl: 300,
        };
        
        let command = session.process_market_data(&packet);
        assert!(command.is_some()); // Should generate bid
        
        // Execute purchase
        assert!(session.execute_purchase(door, 75).is_ok());
        assert_eq!(session.credit_balance, 9925);
        
        let stats = session.get_stats();
        assert_eq!(stats.total_purchases, 1);
        assert_eq!(stats.total_spent, 75);
    }
    
    #[test]
    fn test_market_maker() {
        let maker = MarketMaker::new(0x2001);
        
        let (bid, ask) = maker.quote(100.0);
        assert!(bid < 100.0);
        assert!(ask > 100.0);
        assert!((ask - bid) > 5.0); // Spread exists
        
        // Should buy when price is low
        assert!(maker.should_buy(85.0, 100.0));
        assert!(!maker.should_buy(99.0, 100.0));
        
        // Should sell when price is high
        // (would need inventory first)
    }
}
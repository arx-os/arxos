//! Market Data Feeds
//! 
//! Provides real-time market data and price feeds for BILT tokens
//! and property valuations, enabling the smart order router functionality.

use anyhow::Result;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::collections::HashMap;
use tokio::sync::RwLock;
use std::sync::Arc;

/// Market data feed providing real-time pricing
pub struct MarketDataFeed {
    price_cache: Arc<RwLock<HashMap<String, PriceData>>>,
    property_values: Arc<RwLock<HashMap<String, f64>>>,
}

impl MarketDataFeed {
    /// Create new market data feed
    pub fn new() -> Self {
        Self {
            price_cache: Arc::new(RwLock::new(HashMap::new())),
            property_values: Arc::new(RwLock::new(HashMap::new())),
        }
    }
    
    /// Get current BILT token price
    pub async fn get_bilt_price(&self, building_id: &str) -> Result<PriceData> {
        let cache = self.price_cache.read().await;
        
        if let Some(price_data) = cache.get(building_id) {
            // Return cached price if fresh (< 1 minute old)
            if price_data.timestamp > Utc::now() - chrono::Duration::minutes(1) {
                return Ok(price_data.clone());
            }
        }
        
        // Simulate fetching from market
        let price_data = self.fetch_market_price(building_id).await?;
        
        // Update cache
        drop(cache);
        let mut cache = self.price_cache.write().await;
        cache.insert(building_id.to_string(), price_data.clone());
        
        Ok(price_data)
    }
    
    /// Get property base value
    pub async fn get_property_base_value(&self, building_id: &str) -> Result<f64> {
        let values = self.property_values.read().await;
        
        if let Some(value) = values.get(building_id) {
            return Ok(*value);
        }
        
        // Simulate property valuation
        let base_value = self.estimate_property_value(building_id).await?;
        
        drop(values);
        let mut values = self.property_values.write().await;
        values.insert(building_id.to_string(), base_value);
        
        Ok(base_value)
    }
    
    /// Subscribe to price updates (for real-time feeds)
    pub async fn subscribe_to_updates(
        &self,
        building_id: &str,
        callback: impl Fn(PriceUpdate) + Send + 'static,
    ) -> Result<SubscriptionHandle> {
        // In production, this would connect to websocket feeds
        let handle = SubscriptionHandle {
            id: uuid::Uuid::new_v4().to_string(),
            building_id: building_id.to_string(),
        };
        
        // Simulate price updates
        let building_id = building_id.to_string();
        tokio::spawn(async move {
            loop {
                tokio::time::sleep(tokio::time::Duration::from_secs(5)).await;
                
                let update = PriceUpdate {
                    building_id: building_id.clone(),
                    old_price: 1.0,
                    new_price: 1.0 + (rand::random::<f64>() - 0.5) * 0.1,
                    change_percent: rand::random::<f64>() * 5.0 - 2.5,
                    volume: rand::random::<f64>() * 100000.0,
                    timestamp: Utc::now(),
                };
                
                callback(update);
            }
        });
        
        Ok(handle)
    }
    
    /// Get market depth (order book)
    pub async fn get_market_depth(
        &self,
        building_id: &str,
    ) -> Result<MarketDepth> {
        // Simulate order book data
        Ok(MarketDepth {
            building_id: building_id.to_string(),
            bids: vec![
                Order { price: 0.95, volume: 1000.0 },
                Order { price: 0.94, volume: 2000.0 },
                Order { price: 0.93, volume: 3000.0 },
            ],
            asks: vec![
                Order { price: 1.01, volume: 1500.0 },
                Order { price: 1.02, volume: 2500.0 },
                Order { price: 1.03, volume: 3500.0 },
            ],
            spread: 0.06,
            mid_price: 0.98,
            timestamp: Utc::now(),
        })
    }
    
    /// Get aggregated market statistics
    pub async fn get_market_stats(&self) -> Result<MarketStatistics> {
        Ok(MarketStatistics {
            total_market_cap: 50_000_000.0,
            total_volume_24h: 5_000_000.0,
            active_buildings: 150,
            average_rating: 65.5,
            top_gainers: vec![
                ("BILT-building1".to_string(), 15.5),
                ("BILT-building2".to_string(), 12.3),
                ("BILT-building3".to_string(), 10.1),
            ],
            top_losers: vec![
                ("BILT-building4".to_string(), -8.2),
                ("BILT-building5".to_string(), -5.5),
            ],
            timestamp: Utc::now(),
        })
    }
    
    /// Simulate fetching market price
    async fn fetch_market_price(&self, building_id: &str) -> Result<PriceData> {
        // In production, this would call external price APIs
        Ok(PriceData {
            building_id: building_id.to_string(),
            price: 1.0 + rand::random::<f64>() * 0.5,
            volume_24h: rand::random::<f64>() * 100000.0,
            change_24h: (rand::random::<f64>() - 0.5) * 10.0,
            high_24h: 1.2,
            low_24h: 0.9,
            timestamp: Utc::now(),
        })
    }
    
    /// Estimate property value
    async fn estimate_property_value(&self, _building_id: &str) -> Result<f64> {
        // In production, would use real estate APIs or valuation models
        Ok(1_000_000.0 + rand::random::<f64>() * 500_000.0)
    }
}

/// Price feed for external integrations
pub struct PriceFeed {
    feed_url: String,
    api_key: Option<String>,
}

impl PriceFeed {
    /// Create new price feed connection
    pub fn new(feed_url: String, api_key: Option<String>) -> Self {
        Self { feed_url, api_key }
    }
    
    /// Push price update to external system
    pub async fn push_price_update(&self, update: &PriceUpdate) -> Result<()> {
        // In production, would POST to webhook or API
        log::info!("Pushing price update to {}: {:?}", self.feed_url, update);
        Ok(())
    }
    
    /// Batch push multiple updates
    pub async fn push_batch_updates(&self, updates: &[PriceUpdate]) -> Result<()> {
        log::info!("Pushing {} price updates to {}", updates.len(), self.feed_url);
        Ok(())
    }
}

/// Price data for a BILT token
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PriceData {
    pub building_id: String,
    pub price: f64,
    pub volume_24h: f64,
    pub change_24h: f64,
    pub high_24h: f64,
    pub low_24h: f64,
    pub timestamp: DateTime<Utc>,
}

/// Real-time price update
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PriceUpdate {
    pub building_id: String,
    pub old_price: f64,
    pub new_price: f64,
    pub change_percent: f64,
    pub volume: f64,
    pub timestamp: DateTime<Utc>,
}

/// Market depth (order book)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDepth {
    pub building_id: String,
    pub bids: Vec<Order>,
    pub asks: Vec<Order>,
    pub spread: f64,
    pub mid_price: f64,
    pub timestamp: DateTime<Utc>,
}

/// Order in the order book
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Order {
    pub price: f64,
    pub volume: f64,
}

/// Subscription handle for price feeds
#[derive(Debug, Clone)]
pub struct SubscriptionHandle {
    pub id: String,
    pub building_id: String,
}

/// Market-wide statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketStatistics {
    pub total_market_cap: f64,
    pub total_volume_24h: f64,
    pub active_buildings: u64,
    pub average_rating: f64,
    pub top_gainers: Vec<(String, f64)>,
    pub top_losers: Vec<(String, f64)>,
    pub timestamp: DateTime<Utc>,
}

// For simulating random prices
use rand;
//! Data Broker Feed System for ArxOS
//! 
//! Manages subscriptions and data feeds for commercial data consumers
//! without requiring a database - uses file-based append-only logs

use std::collections::HashMap;
use std::fs::{File, OpenOptions};
use std::io::{BufReader, BufWriter, Write, BufRead};
use std::path::{Path, PathBuf};
use serde::{Serialize, Deserialize};
use chrono::{DateTime, Utc, Duration};

/// Data broker subscription
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataFeed {
    /// Unique ID for this subscription
    pub subscription_id: String,
    
    /// Company subscribing to the feed
    pub subscriber: String,
    
    /// Company type for reporting
    pub subscriber_type: SubscriberType,
    
    /// Object types to include (pipe-separated)
    /// Example: "fire_extinguisher|smoke_detector|exit_sign"
    pub filter: String,
    
    /// Payment per object per month in cents
    pub payment_cents_per_object: u32,
    
    /// How often to deliver data
    pub delivery: DeliverySchedule,
    
    /// Geographic scope
    pub scope: FeedScope,
    
    /// When subscription started
    pub created_at: DateTime<Utc>,
    
    /// Active status
    pub active: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SubscriberType {
    InsuranceCompany,
    RealEstateInvestor,
    GovernmentAgency,
    MaintenanceCompany,
    SafetyInspector,
    ResearchInstitution,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DeliverySchedule {
    Realtime,        // Stream via websocket (premium)
    Daily,           // Daily aggregate
    Weekly,          // Weekly summary  
    Monthly,         // Monthly report
    Quarterly,       // Quarterly assessment
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FeedScope {
    Building(String),           // Single building
    District(String),          // School district
    City(String),             // City-wide
    Region(String),           // Multi-city region
    National,                 // Entire network
}

/// Payment split configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PaymentSplit {
    pub building_owner_percent: u8,  // 70%
    pub district_node_percent: u8,   // 20%
    pub arxos_protocol_percent: u8,  // 10%
}

impl Default for PaymentSplit {
    fn default() -> Self {
        PaymentSplit {
            building_owner_percent: 70,
            district_node_percent: 20,
            arxos_protocol_percent: 10,
        }
    }
}

/// Aggregated data point for reporting
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataPoint {
    pub timestamp: DateTime<Utc>,
    pub building_id: String,
    pub object_type: String,
    pub count: u32,
    pub status: ObjectStatus,
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ObjectStatus {
    Operational,
    NeedsInspection,
    Failed,
    Unknown,
}

/// Manages data broker subscriptions without a database
pub struct DataBrokerManager {
    /// Base directory for all data broker files
    base_dir: PathBuf,
    
    /// Active subscriptions (loaded from disk)
    subscriptions: HashMap<String, DataFeed>,
    
    /// Payment split configuration
    payment_split: PaymentSplit,
}

impl DataBrokerManager {
    /// Create a new data broker manager
    pub fn new<P: AsRef<Path>>(base_dir: P) -> std::io::Result<Self> {
        let base_dir = base_dir.as_ref().to_path_buf();
        
        // Ensure directories exist
        std::fs::create_dir_all(&base_dir)?;
        std::fs::create_dir_all(base_dir.join("subscriptions"))?;
        std::fs::create_dir_all(base_dir.join("feeds"))?;
        std::fs::create_dir_all(base_dir.join("reports"))?;
        std::fs::create_dir_all(base_dir.join("payments"))?;
        
        let mut manager = DataBrokerManager {
            base_dir,
            subscriptions: HashMap::new(),
            payment_split: PaymentSplit::default(),
        };
        
        // Load existing subscriptions
        manager.load_subscriptions()?;
        
        Ok(manager)
    }
    
    /// Load all subscriptions from disk
    fn load_subscriptions(&mut self) -> std::io::Result<()> {
        let sub_dir = self.base_dir.join("subscriptions");
        
        for entry in std::fs::read_dir(sub_dir)? {
            let entry = entry?;
            let path = entry.path();
            
            if path.extension().and_then(|s| s.to_str()) == Some("json") {
                let file = File::open(&path)?;
                let reader = BufReader::new(file);
                let feed: DataFeed = serde_json::from_reader(reader)?;
                self.subscriptions.insert(feed.subscription_id.clone(), feed);
            }
        }
        
        Ok(())
    }
    
    /// Add a new subscription
    pub fn add_subscription(&mut self, feed: DataFeed) -> std::io::Result<()> {
        // Save to disk
        let path = self.base_dir
            .join("subscriptions")
            .join(format!("{}.json", feed.subscription_id));
        
        let file = File::create(&path)?;
        let writer = BufWriter::new(file);
        serde_json::to_writer_pretty(writer, &feed)?;
        
        // Add to memory
        self.subscriptions.insert(feed.subscription_id.clone(), feed);
        
        // Log the subscription
        self.log_event("subscription_added", &feed.subscription_id)?;
        
        Ok(())
    }
    
    /// Process building data and generate feeds
    pub fn process_building_data(
        &self,
        building_id: &str,
        objects: &[(u16, u8, u16, u16, u16)], // ArxObject tuples
    ) -> std::io::Result<Vec<DataPoint>> {
        let mut data_points = Vec::new();
        let timestamp = Utc::now();
        
        // Count objects by type
        let mut type_counts: HashMap<u8, u32> = HashMap::new();
        for (_id, obj_type, _x, _y, _z) in objects {
            *type_counts.entry(*obj_type).or_insert(0) += 1;
        }
        
        // Convert to data points
        for (obj_type, count) in type_counts {
            data_points.push(DataPoint {
                timestamp,
                building_id: building_id.to_string(),
                object_type: format!("{:02x}", obj_type),
                count,
                status: ObjectStatus::Operational, // Would be determined by actual data
                metadata: HashMap::new(),
            });
        }
        
        Ok(data_points)
    }
    
    /// Generate report for a subscription
    pub fn generate_report(
        &self,
        subscription_id: &str,
        data_points: &[DataPoint],
    ) -> std::io::Result<Report> {
        let subscription = self.subscriptions.get(subscription_id)
            .ok_or_else(|| std::io::Error::new(
                std::io::ErrorKind::NotFound,
                "Subscription not found"
            ))?;
        
        // Filter data points based on subscription filter
        let filters: Vec<&str> = subscription.filter.split('|').collect();
        let filtered_points: Vec<DataPoint> = data_points.iter()
            .filter(|dp| {
                filters.iter().any(|f| dp.object_type.contains(f))
            })
            .cloned()
            .collect();
        
        // Calculate payment
        let total_objects: u32 = filtered_points.iter().map(|dp| dp.count).sum();
        let monthly_payment_cents = total_objects * subscription.payment_cents_per_object;
        
        // Calculate splits
        let building_owner_cents = (monthly_payment_cents * self.payment_split.building_owner_percent as u32) / 100;
        let district_node_cents = (monthly_payment_cents * self.payment_split.district_node_percent as u32) / 100;
        let arxos_protocol_cents = (monthly_payment_cents * self.payment_split.arxos_protocol_percent as u32) / 100;
        
        let report = Report {
            subscription_id: subscription_id.to_string(),
            generated_at: Utc::now(),
            period_start: Utc::now() - Duration::days(30),
            period_end: Utc::now(),
            data_points: filtered_points,
            total_objects,
            monthly_payment_cents,
            payment_splits: PaymentBreakdown {
                building_owner_cents,
                district_node_cents,
                arxos_protocol_cents,
            },
        };
        
        // Save report to disk
        self.save_report(&report)?;
        
        Ok(report)
    }
    
    /// Save report to disk
    fn save_report(&self, report: &Report) -> std::io::Result<()> {
        let filename = format!(
            "{}_{}.json",
            report.subscription_id,
            report.generated_at.format("%Y%m%d_%H%M%S")
        );
        
        let path = self.base_dir.join("reports").join(filename);
        let file = File::create(&path)?;
        let writer = BufWriter::new(file);
        serde_json::to_writer_pretty(writer, &report)?;
        
        Ok(())
    }
    
    /// Export report as CSV for easy consumption
    pub fn export_csv(&self, report: &Report, path: &Path) -> std::io::Result<()> {
        let file = File::create(path)?;
        let mut writer = BufWriter::new(file);
        
        // Write header
        writeln!(writer, "Timestamp,Building ID,Object Type,Count,Status")?;
        
        // Write data
        for point in &report.data_points {
            writeln!(
                writer,
                "{},{},{},{},{:?}",
                point.timestamp.to_rfc3339(),
                point.building_id,
                point.object_type,
                point.count,
                point.status
            )?;
        }
        
        // Write payment summary
        writeln!(writer)?;
        writeln!(writer, "Payment Summary")?;
        writeln!(writer, "Total Objects,{}", report.total_objects)?;
        writeln!(writer, "Monthly Payment (cents),{}", report.monthly_payment_cents)?;
        writeln!(writer, "Building Owner Share,{}", report.payment_splits.building_owner_cents)?;
        writeln!(writer, "District Node Share,{}", report.payment_splits.district_node_cents)?;
        writeln!(writer, "ArxOS Protocol Fee,{}", report.payment_splits.arxos_protocol_cents)?;
        
        Ok(())
    }
    
    /// Stream data points for real-time subscribers
    pub fn stream_data_point(&self, point: &DataPoint) -> std::io::Result<()> {
        // Append to the real-time feed log
        let feed_path = self.base_dir.join("feeds").join("realtime.jsonl");
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(feed_path)?;
        
        writeln!(file, "{}", serde_json::to_string(point)?)?;
        
        Ok(())
    }
    
    /// Process payments and distribute to stakeholders
    pub fn process_payment(&self, report: &Report) -> std::io::Result<PaymentRecord> {
        let payment = PaymentRecord {
            timestamp: Utc::now(),
            subscription_id: report.subscription_id.clone(),
            period: format!("{} to {}", 
                report.period_start.format("%Y-%m-%d"),
                report.period_end.format("%Y-%m-%d")
            ),
            total_amount_cents: report.monthly_payment_cents,
            distributions: vec![
                Distribution {
                    recipient: "building_owner".to_string(),
                    amount_cents: report.payment_splits.building_owner_cents,
                    bilt_tokens: report.payment_splits.building_owner_cents / 10, // 10 cents = 1 BILT
                },
                Distribution {
                    recipient: "district_node".to_string(),
                    amount_cents: report.payment_splits.district_node_cents,
                    bilt_tokens: report.payment_splits.district_node_cents / 10,
                },
                Distribution {
                    recipient: "arxos_protocol".to_string(),
                    amount_cents: report.payment_splits.arxos_protocol_cents,
                    bilt_tokens: report.payment_splits.arxos_protocol_cents / 10,
                },
            ],
        };
        
        // Append to payment ledger
        let ledger_path = self.base_dir.join("payments").join("ledger.jsonl");
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(ledger_path)?;
        
        writeln!(file, "{}", serde_json::to_string(&payment)?)?;
        
        Ok(payment)
    }
    
    /// Log events for audit trail
    fn log_event(&self, event_type: &str, details: &str) -> std::io::Result<()> {
        let log_path = self.base_dir.join("audit.log");
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(log_path)?;
        
        writeln!(
            file,
            "{}\t{}\t{}",
            Utc::now().to_rfc3339(),
            event_type,
            details
        )?;
        
        Ok(())
    }
}

/// Report generated for a subscription
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Report {
    pub subscription_id: String,
    pub generated_at: DateTime<Utc>,
    pub period_start: DateTime<Utc>,
    pub period_end: DateTime<Utc>,
    pub data_points: Vec<DataPoint>,
    pub total_objects: u32,
    pub monthly_payment_cents: u32,
    pub payment_splits: PaymentBreakdown,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PaymentBreakdown {
    pub building_owner_cents: u32,
    pub district_node_cents: u32,
    pub arxos_protocol_cents: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PaymentRecord {
    pub timestamp: DateTime<Utc>,
    pub subscription_id: String,
    pub period: String,
    pub total_amount_cents: u32,
    pub distributions: Vec<Distribution>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Distribution {
    pub recipient: String,
    pub amount_cents: u32,
    pub bilt_tokens: u32,
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;
    
    #[test]
    fn test_subscription_management() {
        let temp_dir = TempDir::new().unwrap();
        let mut manager = DataBrokerManager::new(temp_dir.path()).unwrap();
        
        let feed = DataFeed {
            subscription_id: "INS-001".to_string(),
            subscriber: "SafeGuard Insurance".to_string(),
            subscriber_type: SubscriberType::InsuranceCompany,
            filter: "fire_extinguisher|smoke_detector".to_string(),
            payment_cents_per_object: 10, // $0.10 per object per month
            delivery: DeliverySchedule::Monthly,
            scope: FeedScope::District("LAUSD".to_string()),
            created_at: Utc::now(),
            active: true,
        };
        
        manager.add_subscription(feed.clone()).unwrap();
        assert_eq!(manager.subscriptions.len(), 1);
    }
    
    #[test]
    fn test_payment_splitting() {
        let split = PaymentSplit::default();
        let total = 1000; // $10.00
        
        let building = (total * split.building_owner_percent as u32) / 100;
        let district = (total * split.district_node_percent as u32) / 100;
        let arxos = (total * split.arxos_protocol_percent as u32) / 100;
        
        assert_eq!(building, 700); // $7.00
        assert_eq!(district, 200); // $2.00
        assert_eq!(arxos, 100);    // $1.00
    }
}
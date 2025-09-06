//! Data Aggregation Engine for ArxOS
//! 
//! Efficiently aggregates building data from file-based storage
//! without requiring a database. Optimized for streaming large datasets.

use std::collections::HashMap;
use std::fs::File;
use std::io::{BufReader, BufRead, Seek, SeekFrom};
use std::path::{Path, PathBuf};
use memmap2::{Mmap, MmapOptions};
use serde::{Serialize, Deserialize};
use chrono::{DateTime, Utc, Duration, Datelike};

/// Aggregation request from data broker
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AggregationRequest {
    pub subscription_id: String,
    pub building_ids: Vec<String>,
    pub object_types: Vec<String>,
    pub period: AggregationPeriod,
    pub metrics: Vec<MetricType>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AggregationPeriod {
    LastDay,
    LastWeek,
    LastMonth,
    LastQuarter,
    LastYear,
    Custom { start: DateTime<Utc>, end: DateTime<Utc> },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MetricType {
    Count,              // Total count of objects
    Compliance,         // Compliance percentage
    Age,               // Average age of equipment
    MaintenanceNeeded,  // Count needing maintenance
    FailureRate,       // Failure rate percentage
    Distribution,      // Geographic distribution
}

/// Aggregated result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AggregationResult {
    pub request_id: String,
    pub generated_at: DateTime<Utc>,
    pub period: String,
    pub summary: Summary,
    pub buildings: Vec<BuildingSummary>,
    pub trends: Vec<Trend>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Summary {
    pub total_buildings: usize,
    pub total_objects: u64,
    pub compliance_rate: f32,
    pub critical_issues: u32,
    pub maintenance_backlog: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingSummary {
    pub building_id: String,
    pub name: String,
    pub object_counts: HashMap<String, u32>,
    pub compliance_status: ComplianceStatus,
    pub last_updated: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ComplianceStatus {
    Compliant,
    MinorIssues,
    MajorIssues,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trend {
    pub metric: String,
    pub direction: TrendDirection,
    pub change_percent: f32,
    pub data_points: Vec<(DateTime<Utc>, f32)>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TrendDirection {
    Improving,
    Stable,
    Declining,
}

/// Manages efficient data aggregation from file storage
pub struct DataAggregator {
    data_dir: PathBuf,
    cache: HashMap<String, BuildingCache>,
}

/// Cached building data for fast aggregation
struct BuildingCache {
    mmap: Mmap,
    object_count: usize,
    last_modified: DateTime<Utc>,
}

impl DataAggregator {
    pub fn new<P: AsRef<Path>>(data_dir: P) -> std::io::Result<Self> {
        Ok(DataAggregator {
            data_dir: data_dir.as_ref().to_path_buf(),
            cache: HashMap::new(),
        })
    }
    
    /// Load building data into memory-mapped cache
    pub fn cache_building(&mut self, building_id: &str) -> std::io::Result<()> {
        let path = self.data_dir
            .join("buildings")
            .join(format!("{}.arxb", building_id));
        
        if !path.exists() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                format!("Building data not found: {}", building_id)
            ));
        }
        
        let file = File::open(&path)?;
        let metadata = file.metadata()?;
        let mmap = unsafe { MmapOptions::new().map(&file)? };
        
        // ArxObjects are 13 bytes each
        let object_count = mmap.len() / 13;
        
        self.cache.insert(building_id.to_string(), BuildingCache {
            mmap,
            object_count,
            last_modified: DateTime::from(metadata.modified()?),
        });
        
        Ok(())
    }
    
    /// Process aggregation request
    pub fn aggregate(&mut self, request: &AggregationRequest) -> std::io::Result<AggregationResult> {
        let mut result = AggregationResult {
            request_id: format!("{}-{}", request.subscription_id, Utc::now().timestamp()),
            generated_at: Utc::now(),
            period: format_period(&request.period),
            summary: Summary {
                total_buildings: 0,
                total_objects: 0,
                compliance_rate: 0.0,
                critical_issues: 0,
                maintenance_backlog: 0,
            },
            buildings: Vec::new(),
            trends: Vec::new(),
        };
        
        // Process each building
        for building_id in &request.building_ids {
            // Cache if not already cached
            if !self.cache.contains_key(building_id) {
                self.cache_building(building_id)?;
            }
            
            if let Some(cache) = self.cache.get(building_id) {
                let summary = self.process_building(building_id, cache, &request.object_types)?;
                result.summary.total_objects += summary.object_counts.values().sum::<u32>() as u64;
                result.buildings.push(summary);
            }
        }
        
        result.summary.total_buildings = result.buildings.len();
        
        // Calculate compliance rate
        let compliant_buildings = result.buildings.iter()
            .filter(|b| matches!(b.compliance_status, ComplianceStatus::Compliant))
            .count();
        result.summary.compliance_rate = (compliant_buildings as f32 / result.buildings.len() as f32) * 100.0;
        
        // Generate trends if requested
        for metric in &request.metrics {
            if let Some(trend) = self.calculate_trend(metric, &request.period)? {
                result.trends.push(trend);
            }
        }
        
        Ok(result)
    }
    
    /// Process a single building's data
    fn process_building(
        &self,
        building_id: &str,
        cache: &BuildingCache,
        filter_types: &[String],
    ) -> std::io::Result<BuildingSummary> {
        let mut counts: HashMap<String, u32> = HashMap::new();
        let mut compliance_issues = 0;
        
        // Parse ArxObjects from memory-mapped file
        for i in 0..cache.object_count {
            let offset = i * 13;
            let object_bytes = &cache.mmap[offset..offset + 13];
            
            // Parse ArxObject (simplified - would use actual ArxObject::from_bytes)
            let object_type = object_bytes[2];
            let status = object_bytes[12]; // Last byte could be status
            
            let type_str = format!("type_{:02x}", object_type);
            
            // Apply filter if specified
            if filter_types.is_empty() || filter_types.contains(&type_str) {
                *counts.entry(type_str).or_insert(0) += 1;
                
                // Check compliance (simplified logic)
                if status != 0 {
                    compliance_issues += 1;
                }
            }
        }
        
        // Determine compliance status
        let compliance_status = match compliance_issues {
            0 => ComplianceStatus::Compliant,
            1..=5 => ComplianceStatus::MinorIssues,
            6..=20 => ComplianceStatus::MajorIssues,
            _ => ComplianceStatus::Critical,
        };
        
        Ok(BuildingSummary {
            building_id: building_id.to_string(),
            name: format!("Building {}", building_id), // Would lookup actual name
            object_counts: counts,
            compliance_status,
            last_updated: cache.last_modified,
        })
    }
    
    /// Calculate trend for a metric
    fn calculate_trend(
        &self,
        metric: &MetricType,
        period: &AggregationPeriod,
    ) -> std::io::Result<Option<Trend>> {
        // Read historical data from append-only logs
        let log_path = self.data_dir.join("metrics").join("history.jsonl");
        
        if !log_path.exists() {
            return Ok(None);
        }
        
        let file = File::open(&log_path)?;
        let reader = BufReader::new(file);
        let mut data_points = Vec::new();
        
        let (start_date, _end_date) = get_period_bounds(period);
        
        // Parse historical metrics
        for line in reader.lines() {
            let line = line?;
            if let Ok(point) = serde_json::from_str::<MetricPoint>(&line) {
                if point.timestamp >= start_date && point.metric_type == format!("{:?}", metric) {
                    data_points.push((point.timestamp, point.value));
                }
            }
        }
        
        if data_points.len() < 2 {
            return Ok(None);
        }
        
        // Calculate trend
        let first_value = data_points.first().map(|(_, v)| *v).unwrap_or(0.0);
        let last_value = data_points.last().map(|(_, v)| *v).unwrap_or(0.0);
        let change_percent = ((last_value - first_value) / first_value) * 100.0;
        
        let direction = if change_percent > 5.0 {
            TrendDirection::Improving
        } else if change_percent < -5.0 {
            TrendDirection::Declining
        } else {
            TrendDirection::Stable
        };
        
        Ok(Some(Trend {
            metric: format!("{:?}", metric),
            direction,
            change_percent,
            data_points,
        }))
    }
    
    /// Generate compliance report
    pub fn generate_compliance_report(&mut self, building_ids: &[String]) -> std::io::Result<ComplianceReport> {
        let mut report = ComplianceReport {
            generated_at: Utc::now(),
            total_buildings: building_ids.len(),
            compliant_buildings: 0,
            issues: Vec::new(),
            recommendations: Vec::new(),
        };
        
        for building_id in building_ids {
            if !self.cache.contains_key(building_id) {
                self.cache_building(building_id)?;
            }
            
            if let Some(cache) = self.cache.get(building_id) {
                // Check for required safety equipment
                let safety_equipment = self.check_safety_equipment(cache)?;
                
                if safety_equipment.all_present {
                    report.compliant_buildings += 1;
                } else {
                    report.issues.push(ComplianceIssue {
                        building_id: building_id.clone(),
                        issue_type: IssueType::MissingEquipment,
                        severity: Severity::High,
                        description: format!("Missing: {:?}", safety_equipment.missing),
                    });
                }
            }
        }
        
        // Add recommendations based on issues
        if report.issues.len() > 0 {
            report.recommendations.push(
                "Schedule immediate safety equipment installation".to_string()
            );
        }
        
        Ok(report)
    }
    
    /// Check for required safety equipment
    fn check_safety_equipment(&self, cache: &BuildingCache) -> std::io::Result<SafetyCheck> {
        let mut found_types = vec![];
        
        for i in 0..cache.object_count {
            let offset = i * 13;
            let object_type = cache.mmap[offset + 2];
            found_types.push(object_type);
        }
        
        // Check for required types (simplified)
        let required = vec![0x10, 0x11, 0x12]; // Fire extinguisher, smoke detector, exit sign
        let missing: Vec<u8> = required.iter()
            .filter(|t| !found_types.contains(t))
            .copied()
            .collect();
        
        Ok(SafetyCheck {
            all_present: missing.is_empty(),
            missing,
        })
    }
}

#[derive(Debug, Serialize, Deserialize)]
struct MetricPoint {
    timestamp: DateTime<Utc>,
    metric_type: String,
    value: f32,
}

#[derive(Debug)]
struct SafetyCheck {
    all_present: bool,
    missing: Vec<u8>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ComplianceReport {
    pub generated_at: DateTime<Utc>,
    pub total_buildings: usize,
    pub compliant_buildings: usize,
    pub issues: Vec<ComplianceIssue>,
    pub recommendations: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ComplianceIssue {
    pub building_id: String,
    pub issue_type: IssueType,
    pub severity: Severity,
    pub description: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum IssueType {
    MissingEquipment,
    ExpiredInspection,
    FailedTest,
    Damage,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum Severity {
    Low,
    Medium,
    High,
    Critical,
}

/// Helper functions
fn format_period(period: &AggregationPeriod) -> String {
    match period {
        AggregationPeriod::LastDay => "Last 24 hours".to_string(),
        AggregationPeriod::LastWeek => "Last 7 days".to_string(),
        AggregationPeriod::LastMonth => "Last 30 days".to_string(),
        AggregationPeriod::LastQuarter => "Last 90 days".to_string(),
        AggregationPeriod::LastYear => "Last 365 days".to_string(),
        AggregationPeriod::Custom { start, end } => {
            format!("{} to {}", start.format("%Y-%m-%d"), end.format("%Y-%m-%d"))
        }
    }
}

fn get_period_bounds(period: &AggregationPeriod) -> (DateTime<Utc>, DateTime<Utc>) {
    let now = Utc::now();
    match period {
        AggregationPeriod::LastDay => (now - Duration::days(1), now),
        AggregationPeriod::LastWeek => (now - Duration::days(7), now),
        AggregationPeriod::LastMonth => (now - Duration::days(30), now),
        AggregationPeriod::LastQuarter => (now - Duration::days(90), now),
        AggregationPeriod::LastYear => (now - Duration::days(365), now),
        AggregationPeriod::Custom { start, end } => (*start, *end),
    }
}
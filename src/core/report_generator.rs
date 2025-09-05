//! Report Generation for Data Brokers
//! 
//! Generates various report formats for insurance companies, 
//! maintenance companies, and government agencies - all without a database

use std::fs::File;
use std::io::{Write, BufWriter};
use std::path::{Path, PathBuf};
use chrono::{DateTime, Utc, Datelike};
use serde::{Serialize, Deserialize};

use crate::data_aggregator::{AggregationResult, BuildingSummary, ComplianceStatus};
use crate::data_broker_feed::{SubscriberType, DataPoint, ObjectStatus};

/// Report generator for various output formats
pub struct ReportGenerator {
    output_dir: PathBuf,
}

impl ReportGenerator {
    pub fn new<P: AsRef<Path>>(output_dir: P) -> std::io::Result<Self> {
        let output_dir = output_dir.as_ref().to_path_buf();
        std::fs::create_dir_all(&output_dir)?;
        
        Ok(ReportGenerator { output_dir })
    }
    
    /// Generate insurance compliance report
    pub fn generate_insurance_report(
        &self,
        subscriber: &str,
        aggregation: &AggregationResult,
    ) -> std::io::Result<PathBuf> {
        let report = InsuranceReport {
            header: ReportHeader {
                report_type: "Insurance Compliance Report".to_string(),
                subscriber: subscriber.to_string(),
                generated_at: Utc::now(),
                period: aggregation.period.clone(),
            },
            executive_summary: self.create_executive_summary(aggregation),
            risk_assessment: self.assess_risks(aggregation),
            compliance_details: self.compile_compliance_details(aggregation),
            recommendations: self.generate_recommendations(aggregation),
            financial_impact: self.calculate_financial_impact(aggregation),
        };
        
        let filename = format!(
            "insurance_{}_{}.json",
            subscriber.replace(" ", "_").to_lowercase(),
            Utc::now().format("%Y%m%d")
        );
        
        let path = self.output_dir.join(&filename);
        let file = File::create(&path)?;
        let writer = BufWriter::new(file);
        serde_json::to_writer_pretty(writer, &report)?;
        
        // Also generate PDF-ready markdown
        self.generate_markdown_report(&report, &filename.replace(".json", ".md"))?;
        
        Ok(path)
    }
    
    /// Generate safety inspection report for government
    pub fn generate_safety_report(
        &self,
        agency: &str,
        aggregation: &AggregationResult,
    ) -> std::io::Result<PathBuf> {
        let report = SafetyReport {
            header: ReportHeader {
                report_type: "Safety Inspection Report".to_string(),
                subscriber: agency.to_string(),
                generated_at: Utc::now(),
                period: aggregation.period.clone(),
            },
            total_buildings_inspected: aggregation.summary.total_buildings,
            critical_violations: self.find_critical_violations(aggregation),
            equipment_inventory: self.compile_equipment_inventory(aggregation),
            inspection_schedule: self.generate_inspection_schedule(aggregation),
            compliance_rate: aggregation.summary.compliance_rate,
        };
        
        let filename = format!(
            "safety_{}_{}.json",
            agency.replace(" ", "_").to_lowercase(),
            Utc::now().format("%Y%m%d")
        );
        
        let path = self.output_dir.join(&filename);
        let file = File::create(&path)?;
        let writer = BufWriter::new(file);
        serde_json::to_writer_pretty(writer, &report)?;
        
        Ok(path)
    }
    
    /// Generate maintenance report
    pub fn generate_maintenance_report(
        &self,
        company: &str,
        aggregation: &AggregationResult,
        data_points: &[DataPoint],
    ) -> std::io::Result<PathBuf> {
        let report = MaintenanceReport {
            header: ReportHeader {
                report_type: "Maintenance Planning Report".to_string(),
                subscriber: company.to_string(),
                generated_at: Utc::now(),
                period: aggregation.period.clone(),
            },
            maintenance_queue: self.build_maintenance_queue(data_points),
            preventive_schedule: self.create_preventive_schedule(aggregation),
            parts_forecast: self.forecast_parts_needed(data_points),
            labor_estimates: self.estimate_labor_hours(data_points),
            cost_projections: self.project_maintenance_costs(data_points),
        };
        
        let filename = format!(
            "maintenance_{}_{}.json",
            company.replace(" ", "_").to_lowercase(),
            Utc::now().format("%Y%m%d")
        );
        
        let path = self.output_dir.join(&filename);
        let file = File::create(&path)?;
        let writer = BufWriter::new(file);
        serde_json::to_writer_pretty(writer, &report)?;
        
        Ok(path)
    }
    
    /// Generate CSV export for spreadsheet analysis
    pub fn export_to_csv(
        &self,
        name: &str,
        aggregation: &AggregationResult,
    ) -> std::io::Result<PathBuf> {
        let filename = format!("export_{}_{}.csv", name, Utc::now().format("%Y%m%d"));
        let path = self.output_dir.join(&filename);
        let mut file = File::create(&path)?;
        
        // Header
        writeln!(file, "Building ID,Building Name,Object Type,Count,Compliance Status,Last Updated")?;
        
        // Data rows
        for building in &aggregation.buildings {
            for (obj_type, count) in &building.object_counts {
                writeln!(
                    file,
                    "{},{},{},{},{:?},{}",
                    building.building_id,
                    building.name,
                    obj_type,
                    count,
                    building.compliance_status,
                    building.last_updated.format("%Y-%m-%d %H:%M:%S")
                )?;
            }
        }
        
        Ok(path)
    }
    
    /// Create executive summary
    fn create_executive_summary(&self, aggregation: &AggregationResult) -> ExecutiveSummary {
        ExecutiveSummary {
            key_findings: vec![
                format!("Analyzed {} buildings with {} total objects", 
                    aggregation.summary.total_buildings,
                    aggregation.summary.total_objects
                ),
                format!("Overall compliance rate: {:.1}%", 
                    aggregation.summary.compliance_rate
                ),
                format!("{} critical issues identified requiring immediate attention",
                    aggregation.summary.critical_issues
                ),
            ],
            risk_level: if aggregation.summary.compliance_rate > 90.0 {
                "Low"
            } else if aggregation.summary.compliance_rate > 70.0 {
                "Medium"
            } else {
                "High"
            }.to_string(),
            action_required: aggregation.summary.critical_issues > 0,
        }
    }
    
    /// Assess risks for insurance
    fn assess_risks(&self, aggregation: &AggregationResult) -> RiskAssessment {
        let high_risk_buildings = aggregation.buildings.iter()
            .filter(|b| matches!(b.compliance_status, ComplianceStatus::Critical))
            .count();
        
        RiskAssessment {
            overall_risk_score: self.calculate_risk_score(aggregation),
            high_risk_buildings,
            risk_factors: vec![
                RiskFactor {
                    category: "Fire Safety".to_string(),
                    severity: if aggregation.summary.compliance_rate < 80.0 { "High" } else { "Low" }.to_string(),
                    mitigation: "Install additional smoke detectors".to_string(),
                },
                RiskFactor {
                    category: "Equipment Age".to_string(),
                    severity: "Medium".to_string(),
                    mitigation: "Schedule replacement of aging equipment".to_string(),
                },
            ],
        }
    }
    
    fn calculate_risk_score(&self, aggregation: &AggregationResult) -> f32 {
        // Simple risk scoring algorithm
        let base_score = 100.0;
        let compliance_factor = aggregation.summary.compliance_rate / 100.0;
        let critical_factor = 1.0 - (aggregation.summary.critical_issues as f32 / 10.0).min(1.0);
        
        base_score * compliance_factor * critical_factor
    }
    
    /// Compile compliance details
    fn compile_compliance_details(&self, aggregation: &AggregationResult) -> Vec<ComplianceDetail> {
        aggregation.buildings.iter().map(|building| {
            ComplianceDetail {
                building_id: building.building_id.clone(),
                status: format!("{:?}", building.compliance_status),
                missing_equipment: Vec::new(), // Would be populated from actual data
                expired_inspections: Vec::new(),
                notes: String::new(),
            }
        }).collect()
    }
    
    /// Generate recommendations
    fn generate_recommendations(&self, aggregation: &AggregationResult) -> Vec<String> {
        let mut recommendations = Vec::new();
        
        if aggregation.summary.compliance_rate < 90.0 {
            recommendations.push("Schedule comprehensive safety audit within 30 days".to_string());
        }
        
        if aggregation.summary.critical_issues > 0 {
            recommendations.push("Address critical safety issues immediately".to_string());
        }
        
        if aggregation.summary.maintenance_backlog > 10 {
            recommendations.push("Increase maintenance staff or outsource to reduce backlog".to_string());
        }
        
        recommendations
    }
    
    /// Calculate financial impact
    fn calculate_financial_impact(&self, aggregation: &AggregationResult) -> FinancialImpact {
        FinancialImpact {
            estimated_liability: aggregation.summary.critical_issues as f32 * 10000.0,
            premium_adjustment: if aggregation.summary.compliance_rate > 95.0 {
                -5.0 // 5% discount
            } else if aggregation.summary.compliance_rate < 80.0 {
                10.0 // 10% increase
            } else {
                0.0
            },
            potential_savings: aggregation.summary.total_objects as f32 * 0.10, // $0.10 per object
        }
    }
    
    /// Find critical violations
    fn find_critical_violations(&self, aggregation: &AggregationResult) -> Vec<Violation> {
        let mut violations = Vec::new();
        
        for building in &aggregation.buildings {
            if matches!(building.compliance_status, ComplianceStatus::Critical) {
                violations.push(Violation {
                    building_id: building.building_id.clone(),
                    violation_type: "Missing Critical Safety Equipment".to_string(),
                    severity: "Critical".to_string(),
                    date_discovered: Utc::now(),
                    resolution_deadline: Utc::now() + chrono::Duration::days(7),
                });
            }
        }
        
        violations
    }
    
    /// Compile equipment inventory
    fn compile_equipment_inventory(&self, aggregation: &AggregationResult) -> Vec<EquipmentItem> {
        let mut inventory = Vec::new();
        
        for building in &aggregation.buildings {
            for (obj_type, count) in &building.object_counts {
                inventory.push(EquipmentItem {
                    building_id: building.building_id.clone(),
                    equipment_type: obj_type.clone(),
                    quantity: *count,
                    last_inspection: building.last_updated,
                    next_inspection: building.last_updated + chrono::Duration::days(180),
                });
            }
        }
        
        inventory
    }
    
    /// Generate inspection schedule
    fn generate_inspection_schedule(&self, aggregation: &AggregationResult) -> Vec<ScheduledInspection> {
        aggregation.buildings.iter().map(|building| {
            ScheduledInspection {
                building_id: building.building_id.clone(),
                inspection_type: "Annual Safety Inspection".to_string(),
                scheduled_date: Utc::now() + chrono::Duration::days(30),
                inspector: "TBD".to_string(),
                estimated_duration_hours: 2.0,
            }
        }).collect()
    }
    
    /// Build maintenance queue
    fn build_maintenance_queue(&self, data_points: &[DataPoint]) -> Vec<MaintenanceTask> {
        data_points.iter()
            .filter(|dp| matches!(dp.status, ObjectStatus::NeedsInspection | ObjectStatus::Failed))
            .map(|dp| MaintenanceTask {
                building_id: dp.building_id.clone(),
                object_type: dp.object_type.clone(),
                priority: if matches!(dp.status, ObjectStatus::Failed) { "High" } else { "Medium" }.to_string(),
                estimated_hours: 1.5,
                parts_needed: vec!["Standard replacement kit".to_string()],
            })
            .collect()
    }
    
    /// Create preventive maintenance schedule
    fn create_preventive_schedule(&self, aggregation: &AggregationResult) -> Vec<PreventiveTask> {
        aggregation.buildings.iter().flat_map(|building| {
            building.object_counts.keys().map(|obj_type| {
                PreventiveTask {
                    building_id: building.building_id.clone(),
                    equipment_type: obj_type.clone(),
                    frequency: "Quarterly".to_string(),
                    next_due: Utc::now() + chrono::Duration::days(90),
                    estimated_cost: 150.0,
                }
            }).collect::<Vec<_>>()
        }).collect()
    }
    
    /// Forecast parts needed
    fn forecast_parts_needed(&self, data_points: &[DataPoint]) -> Vec<PartsForecast> {
        let mut parts_map: HashMap<String, u32> = HashMap::new();
        
        for dp in data_points {
            if matches!(dp.status, ObjectStatus::NeedsInspection | ObjectStatus::Failed) {
                *parts_map.entry(format!("{}_kit", dp.object_type)).or_insert(0) += 1;
            }
        }
        
        parts_map.into_iter().map(|(part, quantity)| {
            PartsForecast {
                part_name: part,
                quantity_needed: quantity,
                unit_cost: 50.0,
                total_cost: quantity as f32 * 50.0,
                lead_time_days: 7,
            }
        }).collect()
    }
    
    /// Estimate labor hours
    fn estimate_labor_hours(&self, data_points: &[DataPoint]) -> LaborEstimate {
        let tasks_count = data_points.iter()
            .filter(|dp| !matches!(dp.status, ObjectStatus::Operational))
            .count();
        
        LaborEstimate {
            total_tasks: tasks_count,
            estimated_hours: tasks_count as f32 * 1.5,
            technicians_needed: (tasks_count as f32 / 8.0).ceil() as u32,
            overtime_expected: tasks_count > 20,
        }
    }
    
    /// Project maintenance costs
    fn project_maintenance_costs(&self, data_points: &[DataPoint]) -> CostProjection {
        let repair_count = data_points.iter()
            .filter(|dp| !matches!(dp.status, ObjectStatus::Operational))
            .count();
        
        let parts_cost = repair_count as f32 * 50.0;
        let labor_cost = repair_count as f32 * 1.5 * 75.0; // 1.5 hours @ $75/hour
        
        CostProjection {
            parts_cost,
            labor_cost,
            total_cost: parts_cost + labor_cost,
            budget_variance: 0.0, // Would compare to actual budget
        }
    }
    
    /// Generate markdown report for human reading
    fn generate_markdown_report(&self, report: &InsuranceReport, filename: &str) -> std::io::Result<()> {
        let path = self.output_dir.join(filename);
        let mut file = File::create(&path)?;
        
        writeln!(file, "# {}", report.header.report_type)?;
        writeln!(file, "**Subscriber:** {}", report.header.subscriber)?;
        writeln!(file, "**Generated:** {}", report.header.generated_at.format("%Y-%m-%d %H:%M:%S UTC"))?;
        writeln!(file, "**Period:** {}", report.header.period)?;
        writeln!(file)?;
        
        writeln!(file, "## Executive Summary")?;
        for finding in &report.executive_summary.key_findings {
            writeln!(file, "- {}", finding)?;
        }
        writeln!(file)?;
        
        writeln!(file, "**Risk Level:** {}", report.executive_summary.risk_level)?;
        writeln!(file, "**Action Required:** {}", 
            if report.executive_summary.action_required { "Yes" } else { "No" }
        )?;
        writeln!(file)?;
        
        writeln!(file, "## Risk Assessment")?;
        writeln!(file, "**Overall Risk Score:** {:.1}", report.risk_assessment.overall_risk_score)?;
        writeln!(file, "**High Risk Buildings:** {}", report.risk_assessment.high_risk_buildings)?;
        writeln!(file)?;
        
        writeln!(file, "### Risk Factors")?;
        for factor in &report.risk_assessment.risk_factors {
            writeln!(file, "- **{}** ({}): {}", factor.category, factor.severity, factor.mitigation)?;
        }
        writeln!(file)?;
        
        writeln!(file, "## Recommendations")?;
        for rec in &report.recommendations {
            writeln!(file, "1. {}", rec)?;
        }
        writeln!(file)?;
        
        writeln!(file, "## Financial Impact")?;
        writeln!(file, "- Estimated Liability: ${:.2}", report.financial_impact.estimated_liability)?;
        writeln!(file, "- Premium Adjustment: {:.1}%", report.financial_impact.premium_adjustment)?;
        writeln!(file, "- Potential Savings: ${:.2}", report.financial_impact.potential_savings)?;
        
        Ok(())
    }
}

// Report structures
#[derive(Debug, Serialize, Deserialize)]
struct ReportHeader {
    report_type: String,
    subscriber: String,
    generated_at: DateTime<Utc>,
    period: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct InsuranceReport {
    header: ReportHeader,
    executive_summary: ExecutiveSummary,
    risk_assessment: RiskAssessment,
    compliance_details: Vec<ComplianceDetail>,
    recommendations: Vec<String>,
    financial_impact: FinancialImpact,
}

#[derive(Debug, Serialize, Deserialize)]
struct ExecutiveSummary {
    key_findings: Vec<String>,
    risk_level: String,
    action_required: bool,
}

#[derive(Debug, Serialize, Deserialize)]
struct RiskAssessment {
    overall_risk_score: f32,
    high_risk_buildings: usize,
    risk_factors: Vec<RiskFactor>,
}

#[derive(Debug, Serialize, Deserialize)]
struct RiskFactor {
    category: String,
    severity: String,
    mitigation: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct ComplianceDetail {
    building_id: String,
    status: String,
    missing_equipment: Vec<String>,
    expired_inspections: Vec<String>,
    notes: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct FinancialImpact {
    estimated_liability: f32,
    premium_adjustment: f32,
    potential_savings: f32,
}

#[derive(Debug, Serialize, Deserialize)]
struct SafetyReport {
    header: ReportHeader,
    total_buildings_inspected: usize,
    critical_violations: Vec<Violation>,
    equipment_inventory: Vec<EquipmentItem>,
    inspection_schedule: Vec<ScheduledInspection>,
    compliance_rate: f32,
}

#[derive(Debug, Serialize, Deserialize)]
struct Violation {
    building_id: String,
    violation_type: String,
    severity: String,
    date_discovered: DateTime<Utc>,
    resolution_deadline: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
struct EquipmentItem {
    building_id: String,
    equipment_type: String,
    quantity: u32,
    last_inspection: DateTime<Utc>,
    next_inspection: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ScheduledInspection {
    building_id: String,
    inspection_type: String,
    scheduled_date: DateTime<Utc>,
    inspector: String,
    estimated_duration_hours: f32,
}

#[derive(Debug, Serialize, Deserialize)]
struct MaintenanceReport {
    header: ReportHeader,
    maintenance_queue: Vec<MaintenanceTask>,
    preventive_schedule: Vec<PreventiveTask>,
    parts_forecast: Vec<PartsForecast>,
    labor_estimates: LaborEstimate,
    cost_projections: CostProjection,
}

#[derive(Debug, Serialize, Deserialize)]
struct MaintenanceTask {
    building_id: String,
    object_type: String,
    priority: String,
    estimated_hours: f32,
    parts_needed: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct PreventiveTask {
    building_id: String,
    equipment_type: String,
    frequency: String,
    next_due: DateTime<Utc>,
    estimated_cost: f32,
}

#[derive(Debug, Serialize, Deserialize)]
struct PartsForecast {
    part_name: String,
    quantity_needed: u32,
    unit_cost: f32,
    total_cost: f32,
    lead_time_days: u32,
}

#[derive(Debug, Serialize, Deserialize)]
struct LaborEstimate {
    total_tasks: usize,
    estimated_hours: f32,
    technicians_needed: u32,
    overtime_expected: bool,
}

#[derive(Debug, Serialize, Deserialize)]
struct CostProjection {
    parts_cost: f32,
    labor_cost: f32,
    total_cost: f32,
    budget_variance: f32,
}

use std::collections::HashMap;
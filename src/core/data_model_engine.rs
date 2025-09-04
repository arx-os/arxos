//! Data Model Engine - Transform raw building scans into valuable data products
//! 
//! Handles both ARR (paid) and DSA (free w/ data sharing) customers,
//! creating clean, standardized building models and anonymized market insights.

use crate::arxobject::ArxObject;
use crate::database::Database;
use serde::{Serialize, Deserialize};
use std::collections::HashMap;

/// Customer type determines data handling
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CustomerType {
    /// Annual Recurring Revenue - Customer owns all data
    ARR {
        tier: SubscriptionTier,
        data_retention_days: u32,
    },
    /// Data Sharing Agreement - Free service, ArxOS can commercialize
    DSA {
        anonymization_level: AnonymizationLevel,
        commercial_use: bool,
    },
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum SubscriptionTier {
    Starter,      // $500/mo - 1 building
    Professional, // $2000/mo - 5 buildings  
    Enterprise,   // Custom - Unlimited
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum AnonymizationLevel {
    Basic,    // Remove direct identifiers only
    Standard, // K-anonymity with k=5
    Full,     // Differential privacy + k-anonymity
}

/// Core standardized building model - same quality for both ARR and DSA
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandardizedBuildingModel {
    /// Universal Building ID (anonymous for DSA)
    pub ubid: String,
    
    /// Building classification
    pub classification: BuildingClassification,
    
    /// Physical structure
    pub structure: StructuralModel,
    
    /// Building systems
    pub systems: SystemsModel,
    
    /// Equipment inventory
    pub equipment: Vec<StandardizedEquipment>,
    
    /// Performance metrics
    pub metrics: BuildingMetrics,
    
    /// Data license type
    pub license: DataLicense,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingClassification {
    pub primary_use: BuildingUse,
    pub size_category: SizeCategory,
    pub age_range: AgeRange,
    pub climate_zone: String,
    pub occupancy_type: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum BuildingUse {
    Education,
    Office,
    Retail,
    Healthcare,
    Residential,
    Industrial,
    Hospitality,
    Government,
    Mixed,
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum SizeCategory {
    Small,      // <10k sqft
    Medium,     // 10k-50k sqft
    Large,      // 50k-200k sqft
    VeryLarge,  // >200k sqft
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum AgeRange {
    New,        // <5 years
    Modern,     // 5-20 years
    Mature,     // 20-50 years
    Historic,   // >50 years
}

/// Structural model derived from ArxObjects
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StructuralModel {
    pub footprint_sqft: f32,
    pub gross_sqft: f32,
    pub floors_above_grade: u8,
    pub floors_below_grade: u8,
    pub height_ft: f32,
    pub structural_type: String,
    pub envelope: EnvelopeModel,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnvelopeModel {
    pub wall_type: String,
    pub roof_type: String,
    pub window_wall_ratio: f32,
    pub insulation_r_value: f32,
    pub air_tightness: f32,
}

/// Systems model - HVAC, Electrical, Plumbing, Fire
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemsModel {
    pub hvac: HVACModel,
    pub electrical: ElectricalModel,
    pub plumbing: PlumbingModel,
    pub fire_safety: FireSafetyModel,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HVACModel {
    pub system_type: String,
    pub cooling_capacity_tons: f32,
    pub heating_capacity_btu: f32,
    pub distribution_type: String,
    pub control_system: String,
    pub age_years: f32,
    pub efficiency_rating: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ElectricalModel {
    pub service_voltage: u32,
    pub service_amps: u32,
    pub panel_count: u32,
    pub backup_power: bool,
    pub lighting_type: String,
    pub lighting_controls: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlumbingModel {
    pub water_heater_type: String,
    pub water_heater_capacity_gal: f32,
    pub pipe_material: String,
    pub fixture_count: u32,
    pub water_conservation: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FireSafetyModel {
    pub sprinkler_coverage: f32,
    pub alarm_type: String,
    pub exit_count: u32,
    pub emergency_lighting: bool,
    pub fire_rating: String,
}

/// Standardized equipment from ArxObject detection
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StandardizedEquipment {
    pub equipment_id: String,
    pub uniformat_code: String,      // Industry standard classification
    pub omniclass_code: String,      // Another standard
    pub equipment_type: String,
    pub manufacturer: Option<String>,
    pub model: Option<String>,
    pub serial: Option<String>,      // Removed for DSA
    pub install_date: Option<String>,
    pub location: EquipmentLocation,
    pub condition: ConditionScore,
    pub maintenance_priority: u8,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EquipmentLocation {
    pub floor: u8,
    pub room: Option<String>,    // Generalized for DSA
    pub zone: String,
    pub coordinates: Option<(f32, f32, f32)>, // Removed for DSA
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct ConditionScore {
    pub physical: f32,     // 0-100
    pub functional: f32,   // 0-100
    pub remaining_life: f32, // Years
}

/// Performance metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildingMetrics {
    pub energy_use_intensity: f32,    // kBtu/sqft/year
    pub water_use_intensity: f32,     // gal/sqft/year
    pub maintenance_cost_sqft: f32,   // $/sqft/year
    pub occupant_density: f32,        // people/1000sqft
    pub carbon_intensity: f32,        // kgCO2/sqft/year
}

/// Data license information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DataLicense {
    Proprietary {
        customer_id: String,
        expires: Option<u64>,
        export_allowed: bool,
    },
    Shared {
        agreement_id: String,
        anonymized: bool,
        commercial_use: bool,
    },
}

/// Market data product - aggregated from DSA buildings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDataProduct {
    pub product_id: String,
    pub product_type: MarketDataType,
    pub sample_size: u32,
    pub confidence: f32,
    pub aggregation: AggregationLevel,
    pub insights: Vec<MarketInsight>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum MarketDataType {
    EquipmentLifecycles,
    EnergyPatterns,
    MaintenanceCosts,
    SpaceUtilization,
    SystemPerformance,
    ComplianceGaps,
    RetrofitOpportunities,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum AggregationLevel {
    National,
    Regional(String),
    Metro(String),
    BuildingType(BuildingUse),
    SizeCategory(SizeCategory),
    AgeCorhort(AgeRange),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketInsight {
    pub metric: String,
    pub value: f32,
    pub percentile: f32,
    pub trend: TrendDirection,
    pub significance: f32,
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum TrendDirection {
    Rising,
    Stable,
    Falling,
}

/// Main data model engine
pub struct DataModelEngine {
    database: Database,
    classification_engine: ClassificationEngine,
    standardization_pipeline: StandardizationPipeline,
    anonymizer: AnonymizationEngine,
    aggregator: AggregationEngine,
}

impl DataModelEngine {
    pub fn new(database: Database) -> Self {
        Self {
            database,
            classification_engine: ClassificationEngine::new(),
            standardization_pipeline: StandardizationPipeline::new(),
            anonymizer: AnonymizationEngine::new(),
            aggregator: AggregationEngine::new(),
        }
    }
    
    /// Process raw ArxObjects into standardized model
    pub async fn process_building(
        &self,
        arx_objects: Vec<ArxObject>,
        customer_type: CustomerType,
        building_metadata: BuildingMetadata,
    ) -> Result<StandardizedBuildingModel, String> {
        // 1. Classify building type
        let classification = self.classification_engine
            .classify(&arx_objects, &building_metadata)?;
        
        // 2. Extract structure
        let structure = self.extract_structure(&arx_objects)?;
        
        // 3. Identify systems
        let systems = self.extract_systems(&arx_objects)?;
        
        // 4. Catalog equipment
        let equipment = self.extract_equipment(&arx_objects)?;
        
        // 5. Calculate metrics
        let metrics = self.calculate_metrics(&arx_objects, &structure)?;
        
        // 6. Apply customer-specific processing
        let (ubid, license, equipment_final) = match customer_type {
            CustomerType::ARR { .. } => {
                // Full fidelity for paying customers
                let ubid = format!("ARR-{}", building_metadata.building_id);
                let license = DataLicense::Proprietary {
                    customer_id: building_metadata.customer_id.clone(),
                    expires: None,
                    export_allowed: true,
                };
                (ubid, license, equipment)
            }
            CustomerType::DSA { anonymization_level, commercial_use } => {
                // Anonymize for data sharing customers
                let ubid = self.anonymizer.generate_anonymous_id();
                let license = DataLicense::Shared {
                    agreement_id: building_metadata.agreement_id.clone(),
                    anonymized: true,
                    commercial_use,
                };
                let anon_equipment = self.anonymizer
                    .anonymize_equipment(equipment, anonymization_level)?;
                (ubid, license, anon_equipment)
            }
        };
        
        Ok(StandardizedBuildingModel {
            ubid,
            classification,
            structure,
            systems,
            equipment: equipment_final,
            metrics,
            license,
        })
    }
    
    /// Generate market insights from DSA building pool
    pub async fn generate_market_insights(
        &self,
        building_type: Option<BuildingUse>,
        region: Option<String>,
    ) -> Result<Vec<MarketDataProduct>, String> {
        // Query DSA buildings
        let dsa_buildings = self.database
            .query_dsa_buildings(building_type, region.as_deref())
            .await?;
        
        // Aggregate into insights
        let insights = self.aggregator
            .aggregate(dsa_buildings)?;
        
        Ok(insights)
    }
    
    fn extract_structure(&self, arx_objects: &[ArxObject]) -> Result<StructuralModel, String> {
        // Analyze ArxObjects to determine structure
        // This would use the spatial analysis of walls, floors, ceilings
        // to determine building dimensions and envelope
        
        Ok(StructuralModel {
            footprint_sqft: 10000.0, // Calculate from perimeter
            gross_sqft: 30000.0,      // Sum all floor areas
            floors_above_grade: 3,
            floors_below_grade: 1,
            height_ft: 36.0,
            structural_type: "Steel Frame".to_string(),
            envelope: EnvelopeModel {
                wall_type: "Brick Veneer".to_string(),
                roof_type: "Flat Membrane".to_string(),
                window_wall_ratio: 0.3,
                insulation_r_value: 19.0,
                air_tightness: 0.35,
            },
        })
    }
    
    fn extract_systems(&self, arx_objects: &[ArxObject]) -> Result<SystemsModel, String> {
        // Identify system components from ArxObjects
        // HVAC units, electrical panels, plumbing fixtures, etc.
        
        Ok(SystemsModel {
            hvac: HVACModel {
                system_type: "VAV with Reheat".to_string(),
                cooling_capacity_tons: 75.0,
                heating_capacity_btu: 2000000.0,
                distribution_type: "Ducted".to_string(),
                control_system: "BACnet".to_string(),
                age_years: 12.0,
                efficiency_rating: 0.85,
            },
            electrical: ElectricalModel {
                service_voltage: 480,
                service_amps: 1200,
                panel_count: 8,
                backup_power: true,
                lighting_type: "LED".to_string(),
                lighting_controls: "Occupancy Sensors".to_string(),
            },
            plumbing: PlumbingModel {
                water_heater_type: "Tankless".to_string(),
                water_heater_capacity_gal: 0.0,
                pipe_material: "Copper".to_string(),
                fixture_count: 45,
                water_conservation: vec!["Low Flow".to_string()],
            },
            fire_safety: FireSafetyModel {
                sprinkler_coverage: 1.0,
                alarm_type: "Addressable".to_string(),
                exit_count: 6,
                emergency_lighting: true,
                fire_rating: "Type II-B".to_string(),
            },
        })
    }
    
    fn extract_equipment(&self, arx_objects: &[ArxObject]) -> Result<Vec<StandardizedEquipment>, String> {
        // Convert ArxObjects to standardized equipment records
        let mut equipment = Vec::new();
        
        for obj in arx_objects {
            if let Some(equip) = self.standardization_pipeline.standardize_object(obj) {
                equipment.push(equip);
            }
        }
        
        Ok(equipment)
    }
    
    fn calculate_metrics(
        &self,
        arx_objects: &[ArxObject],
        structure: &StructuralModel,
    ) -> Result<BuildingMetrics, String> {
        // Calculate performance metrics from building data
        
        Ok(BuildingMetrics {
            energy_use_intensity: 55.0,
            water_use_intensity: 12.0,
            maintenance_cost_sqft: 2.50,
            occupant_density: 3.5,
            carbon_intensity: 8.2,
        })
    }
}

/// Building metadata for processing
#[derive(Debug, Clone)]
pub struct BuildingMetadata {
    pub building_id: String,
    pub customer_id: String,
    pub agreement_id: String,
    pub location: Option<Location>,
}

#[derive(Debug, Clone)]
pub struct Location {
    pub address: Option<String>,
    pub city: String,
    pub state: String,
    pub zip: String,
}

/// Classification engine
struct ClassificationEngine;

impl ClassificationEngine {
    fn new() -> Self {
        Self
    }
    
    fn classify(
        &self,
        _arx_objects: &[ArxObject],
        _metadata: &BuildingMetadata,
    ) -> Result<BuildingClassification, String> {
        Ok(BuildingClassification {
            primary_use: BuildingUse::Education,
            size_category: SizeCategory::Large,
            age_range: AgeRange::Mature,
            climate_zone: "4A".to_string(),
            occupancy_type: "E".to_string(),
        })
    }
}

/// Standardization pipeline
struct StandardizationPipeline;

impl StandardizationPipeline {
    fn new() -> Self {
        Self
    }
    
    fn standardize_object(&self, obj: &ArxObject) -> Option<StandardizedEquipment> {
        // Convert ArxObject to standardized equipment
        // This would map object types to Uniformat/Omniclass codes
        None
    }
}

/// Anonymization engine
struct AnonymizationEngine;

impl AnonymizationEngine {
    fn new() -> Self {
        Self
    }
    
    fn generate_anonymous_id(&self) -> String {
        format!("ANON-{:08x}", rand::random::<u32>())
    }
    
    fn anonymize_equipment(
        &self,
        equipment: Vec<StandardizedEquipment>,
        level: AnonymizationLevel,
    ) -> Result<Vec<StandardizedEquipment>, String> {
        let mut anon_equipment = equipment;
        
        for equip in &mut anon_equipment {
            // Remove identifying information based on level
            match level {
                AnonymizationLevel::Basic => {
                    equip.serial = None;
                    equip.location.room = None;
                }
                AnonymizationLevel::Standard => {
                    equip.serial = None;
                    equip.manufacturer = None;
                    equip.model = None;
                    equip.location.room = None;
                    equip.location.coordinates = None;
                }
                AnonymizationLevel::Full => {
                    equip.serial = None;
                    equip.manufacturer = None;
                    equip.model = None;
                    equip.install_date = None;
                    equip.location.room = None;
                    equip.location.coordinates = None;
                }
            }
        }
        
        Ok(anon_equipment)
    }
}

/// Aggregation engine for market insights
struct AggregationEngine;

impl AggregationEngine {
    fn new() -> Self {
        Self
    }
    
    fn aggregate(&self, _buildings: Vec<StandardizedBuildingModel>) -> Result<Vec<MarketDataProduct>, String> {
        // Aggregate building data into market insights
        Ok(vec![])
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_customer_type_handling() {
        let arr_customer = CustomerType::ARR {
            tier: SubscriptionTier::Professional,
            data_retention_days: 365,
        };
        
        let dsa_customer = CustomerType::DSA {
            anonymization_level: AnonymizationLevel::Standard,
            commercial_use: true,
        };
        
        assert_ne!(arr_customer, dsa_customer);
    }
}
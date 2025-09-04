# ArxOS Data Model & Business Architecture

## Business Model Overview

Two paths for building owners:
1. **Annual Recurring Revenue (ARR)**: Pay for service, own your data
2. **Data Sharing Agreement (DSA)**: Free service, ArxOS can commercialize anonymized data

Both get the same quality digital twin, but data rights differ.

## Core Data Architecture

### Layer 1: Raw Building Data (Individual)
```rust
pub struct RawBuildingData {
    // Identity (stripped for DSA users)
    pub building_id: uuid::Uuid,
    pub owner_info: Option<OwnerInfo>,  // None for DSA
    pub address: Option<Address>,       // Generalized for DSA
    
    // Physical structure (always captured)
    pub structure: StructuralData,
    pub systems: SystemsData,
    pub equipment: Vec<Equipment>,
    pub spatial: SpatialData,
    
    // Operational data
    pub maintenance: MaintenanceHistory,
    pub energy: EnergyProfile,
    pub occupancy: OccupancyPatterns,
    
    // Metadata
    pub scan_quality: f32,
    pub last_updated: DateTime<Utc>,
    pub data_license: DataLicense,
}

pub enum DataLicense {
    Proprietary(ARRLicense),    // Customer owns data
    Shared(DSALicense),         // ArxOS can commercialize
}
```

### Layer 2: Standardized Building Model
```rust
/// Clean, standardized data model for both ARR and DSA users
pub struct StandardizedBuildingModel {
    // Universal Building Identifier (anonymous for DSA)
    pub ubid: String,
    
    // Standardized components
    pub envelope: BuildingEnvelope,
    pub mechanical: MechanicalSystems,
    pub electrical: ElectricalSystems,
    pub plumbing: PlumbingSystems,
    pub fire_safety: FireSafetySystems,
    pub accessibility: AccessibilityFeatures,
    
    // Normalized metrics
    pub metrics: BuildingMetrics,
    pub performance: PerformanceProfile,
    pub compliance: ComplianceStatus,
}

pub struct BuildingEnvelope {
    pub footprint_sqft: f32,
    pub floors: u8,
    pub height_ft: f32,
    pub exterior_wall_type: WallType,
    pub roof_type: RoofType,
    pub window_wall_ratio: f32,
    pub insulation_r_value: f32,
}

pub struct MechanicalSystems {
    pub hvac_units: Vec<HVACUnit>,
    pub age_years: f32,
    pub efficiency_rating: f32,
    pub redundancy_level: u8,
    pub control_type: ControlSystem,
}
```

### Layer 3: Aggregated Market Data (DSA Only)
```rust
/// Anonymized, aggregated data for market insights
pub struct MarketDataProduct {
    pub dataset_id: uuid::Uuid,
    pub category: DataCategory,
    pub aggregation_level: AggregationLevel,
    pub sample_size: u32,
    pub confidence_interval: f32,
    pub data_points: Vec<DataPoint>,
}

pub enum DataCategory {
    EquipmentLifecycles,      // When equipment actually fails
    EnergyConsumption,        // Real usage patterns
    MaintenanceCosts,         // Actual maintenance spend
    SpaceUtilization,         // How spaces are really used
    SystemPerformance,        // How systems actually perform
    ComplianceGaps,           // Common code violations
    RetrofitOpportunities,    // Upgrade potential
}

pub enum AggregationLevel {
    National,
    Regional,
    Metropolitan,
    District,
    BuildingType,
    AgeCorhort,
    SizeCategory,
}
```

## Data Processing Pipeline

### Stage 1: Ingestion & Cleaning
```rust
pub struct DataCleaningPipeline {
    /// Raw scan data → Structured objects
    pub fn process_scan(&self, scan: LidarScan) -> Result<CleanedData> {
        // 1. Noise reduction
        let denoised = self.denoise_point_cloud(&scan.points);
        
        // 2. Object detection
        let objects = self.detect_objects(&denoised);
        
        // 3. Classification
        let classified = self.classify_equipment(&objects);
        
        // 4. Validation
        let validated = self.validate_against_schemas(&classified);
        
        // 5. Enrichment
        let enriched = self.enrich_with_context(&validated);
        
        Ok(CleanedData { objects: enriched })
    }
}
```

### Stage 2: Standardization
```rust
pub struct StandardizationEngine {
    /// Convert to industry-standard formats
    pub fn standardize(&self, cleaned: CleanedData) -> StandardizedBuildingModel {
        // Map to standard taxonomies
        let equipment = self.map_to_uniformat(&cleaned.equipment);
        let spaces = self.map_to_omniclass(&cleaned.spaces);
        
        // Normalize measurements
        let metrics = self.normalize_metrics(&cleaned.measurements);
        
        // Apply industry schemas
        let brick_schema = self.apply_brick_schema(&equipment);
        let ifc_model = self.generate_ifc(&spaces);
        
        StandardizedBuildingModel {
            equipment,
            spaces,
            metrics,
            schemas: vec![brick_schema, ifc_model],
        }
    }
}
```

### Stage 3: Anonymization (DSA Path)
```rust
pub struct AnonymizationPipeline {
    /// Remove identifying information while preserving analytical value
    pub fn anonymize(&self, building: StandardizedBuildingModel) -> AnonymousBuilding {
        // 1. Remove direct identifiers
        let stripped = self.strip_identifiers(&building);
        
        // 2. Generalize location
        let generalized = self.generalize_location(&stripped, 
            GeneralizationLevel::ZipCode);
        
        // 3. Add noise to prevent re-identification
        let noised = self.add_differential_privacy(&generalized, 
            epsilon: 0.1);
        
        // 4. K-anonymity guarantee
        let k_anonymous = self.ensure_k_anonymity(&noised, k: 5);
        
        AnonymousBuilding {
            data: k_anonymous,
            anonymization_level: Level::Full,
        }
    }
}
```

## Data Products

### For ARR Customers (Full Control)
```yaml
proprietary_products:
  digital_twin:
    - Complete 3D model
    - All equipment details
    - Historical data
    - Predictive analytics
    - Custom reporting
    
  api_access:
    - Real-time data queries
    - Integration with BMS
    - Custom webhooks
    - Bulk export
    
  analytics_suite:
    - Energy optimization
    - Maintenance predictions
    - Space utilization
    - Cost projections
    
  compliance_tools:
    - Code checking
    - Audit reports
    - Certification tracking
```

### For DSA Customers (Free Service)
```yaml
free_products:
  digital_twin:
    - Same 3D model quality
    - All equipment details
    - Maintenance tracking
    - Basic analytics
    
  standard_reports:
    - Monthly summaries
    - Annual benchmarks
    - Efficiency scores
    
  mobile_access:
    - iOS/Android apps
    - AR navigation
    - Work order management
```

### Market Data Products (From DSA Pool)

#### 1. Equipment Intelligence
```rust
pub struct EquipmentIntelligence {
    pub equipment_type: String,  // "Carrier 30XA Chiller"
    pub sample_size: u32,        // 1,847 units
    pub mean_lifetime: f32,      // 18.3 years
    pub failure_modes: Vec<FailureMode>,
    pub maintenance_costs: CostDistribution,
    pub efficiency_degradation: DegradationCurve,
}

// Valuable to: Manufacturers, Insurance, Service Companies
// Price point: $50K-500K/year subscription
```

#### 2. Building Performance Benchmarks
```rust
pub struct PerformanceBenchmark {
    pub building_type: String,   // "K-12 School"
    pub region: String,          // "Northeast"
    pub sample_size: u32,        // 523 buildings
    pub energy_use_intensity: Distribution,
    pub maintenance_cost_sqft: Distribution,
    pub system_reliability: ReliabilityMetrics,
}

// Valuable to: REITs, Property Managers, Utilities
// Price point: $25K-250K/year subscription
```

#### 3. Retrofit Opportunity Analysis
```rust
pub struct RetrofitOpportunity {
    pub upgrade_type: String,    // "LED Lighting Conversion"
    pub buildings_applicable: u32, // 12,847 buildings
    pub avg_payback_period: f32, // 3.2 years
    pub implementation_cost: CostRange,
    pub energy_savings: SavingsProjection,
    pub case_studies: Vec<AnonymizedCaseStudy>,
}

// Valuable to: ESCOs, Contractors, Utilities
// Price point: $75K-750K/year subscription
```

#### 4. Regulatory Compliance Insights
```rust
pub struct ComplianceInsights {
    pub regulation: String,      // "Local Law 97"
    pub affected_buildings: u32, // 8,234 buildings
    pub common_violations: Vec<Violation>,
    pub compliance_costs: CostDistribution,
    pub solution_patterns: Vec<Solution>,
}

// Valuable to: Regulators, Consultants, Building Owners
// Price point: $100K-1M/year subscription
```

## Privacy & Security Architecture

### Data Segregation
```rust
pub struct DataSegregation {
    // Physical separation
    arr_database: PostgresCluster,     // Encrypted, isolated
    dsa_database: PostgresCluster,     // Separate infrastructure
    market_database: RedshiftCluster,  // Aggregated only
    
    // Access controls
    arr_access: RoleBasedAccess,      // Customer + ArxOS support
    dsa_access: RoleBasedAccess,      // ArxOS data team only
    market_access: ApiKeyAccess,      // Paying subscribers
}
```

### Consent Management
```rust
pub struct ConsentManager {
    pub building_id: uuid::Uuid,
    pub consent_type: ConsentType,
    pub granted_at: DateTime<Utc>,
    pub scope: DataScope,
    pub restrictions: Vec<Restriction>,
    pub audit_log: Vec<ConsentChange>,
}

pub enum ConsentType {
    ARR {
        contract_id: String,
        data_retention: Duration,
        export_rights: bool,
    },
    DSA {
        agreement_id: String,
        anonymization_required: bool,
        commercial_use_allowed: bool,
        opt_out_available: bool,
    },
}
```

## Revenue Model

### ARR Pricing Tiers
```yaml
starter:
  price: $500/month
  buildings: 1
  users: 5
  features: Core digital twin
  
professional:
  price: $2000/month
  buildings: 5
  users: 25
  features: Full analytics
  
enterprise:
  price: Custom
  buildings: Unlimited
  users: Unlimited
  features: Everything + API
```

### Data Product Revenue (from DSA pool)
```yaml
market_data_subscriptions:
  estimated_subscribers: 500-5000
  price_range: $25K-1M/year
  total_addressable_market: $125M-5B/year
  
custom_insights:
  price: $100K-10M per project
  clients: Fortune 500, Government
  
api_access:
  price: $0.10-1.00 per API call
  volume: 100M-10B calls/year
```

## Implementation Roadmap

### Phase 1: Foundation (Months 1-6)
- Build data cleaning pipeline
- Implement standardization engine
- Create ARR customer portal
- Basic anonymization for DSA

### Phase 2: Products (Months 7-12)
- Launch first market data products
- API marketplace
- Advanced analytics for ARR
- Compliance tools

### Phase 3: Scale (Year 2)
- ML-powered insights
- Predictive maintenance
- Energy optimization
- Insurance products

### Phase 4: Ecosystem (Year 3+)
- Third-party data integration
- White-label solutions
- Global expansion
- Regulatory partnerships

## Success Metrics

### Data Quality KPIs
- Scan completeness: >95%
- Object classification accuracy: >98%
- Standardization coverage: 100%
- Anonymization effectiveness: k≥5

### Business KPIs
- ARR customers: 1000+ Year 1
- DSA buildings: 10,000+ Year 1
- Data product revenue: $10M+ Year 2
- Market data subscribers: 100+ Year 2

## Competitive Advantages

1. **Only unified model**: Both individual building management AND market intelligence
2. **Network effects**: More DSA buildings = Better market data = More valuable
3. **No hardware lock-in**: Works with iPhone LiDAR, not proprietary sensors
4. **Gamification**: BILT tokens ensure high-quality data collection
5. **True digital twins**: Not just 3D models, but living, updating systems

This dual model creates a virtuous cycle: Free users provide market data, market data funds platform development, better platform attracts paying customers, paying customers validate market data quality.
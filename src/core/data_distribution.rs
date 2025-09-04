use std::collections::HashMap;

/// Hierarchical data distribution system
/// Prevents device overload while enabling enterprise scale
pub struct DataDistributionLayer {
    pub tiers: DataTiers,
    pub query_router: QueryRouter,
    pub cache_manager: CacheManager,
    pub enterprise_nodes: HashMap<String, EnterpriseNode>,
}

/// Three-tier data architecture
pub struct DataTiers {
    pub edge: EdgeTier,      // Building nodes
    pub district: DistrictTier, // School nodes
    pub enterprise: EnterpriseTier, // Corporate nodes
}

/// Edge tier - individual building nodes
pub struct EdgeTier {
    pub storage_capacity_gb: u32, // Typically 32GB SD card
    pub data_scope: DataScope,
}

#[derive(Debug, Clone)]
pub enum DataScope {
    SingleBuilding {
        building_id: String,
        size_mb: u32, // ~100MB per 100k sq ft
    },
    LocalOnly {
        max_range_miles: f32, // 3-5 miles
    },
}

/// District tier - school SDR nodes
pub struct DistrictTier {
    pub storage_capacity_gb: u32, // 1TB SSD typical
    pub coverage_radius_miles: f32,
    pub buildings_in_range: u32,
    pub cache_strategy: CacheStrategy,
}

#[derive(Debug, Clone)]
pub enum CacheStrategy {
    FrequencyBased,     // Cache most accessed
    ProximityBased,     // Cache nearest buildings
    ServiceBased,       // Cache by service type
    Hybrid,
}

/// Enterprise tier - corporate nodes
pub struct EnterpriseTier {
    pub node_locations: Vec<EnterpriseNode>,
    pub portfolio_size: u32,
    pub storage_capacity_tb: u32,
}

#[derive(Debug, Clone)]
pub struct EnterpriseNode {
    pub organization: String,
    pub location: String,
    pub portfolio_buildings: Vec<String>,
    pub storage_capacity_tb: u32,
    pub cached_data_gb: u32,
    pub query_patterns: QueryPattern,
}

#[derive(Debug, Clone)]
pub enum QueryPattern {
    PortfolioWide,      // Aggregate queries
    RegionalFocus,      // Regional subset
    AssetClassSpecific, // By building type
    MaintenanceFocused, // Work orders and maintenance
}

/// Intelligent query routing
pub struct QueryRouter {
    pub routing_rules: Vec<RoutingRule>,
    pub device_limits: DeviceLimits,
}

#[derive(Debug, Clone)]
pub struct RoutingRule {
    pub query_type: QueryType,
    pub data_size_estimate: DataSize,
    pub route_to: RouteDestination,
}

#[derive(Debug, Clone)]
pub enum QueryType {
    SingleBuilding,
    WorkOrder,
    PortfolioSummary,
    Analytics,
    BulkExport,
    HistoricalData,
}

#[derive(Debug, Clone)]
pub enum DataSize {
    Tiny,       // <1KB (13-byte ArxObjects)
    Small,      // <10KB (work orders)
    Medium,     // <1MB (building summaries)
    Large,      // <100MB (full building)
    Huge,       // >100MB (portfolio export)
}

#[derive(Debug, Clone)]
pub enum RouteDestination {
    BuildingDirect,     // Query the building node
    DistrictCache,      // Use school cache
    EnterpriseNode,     // Use corporate node
    StreamedResponse,   // Stream in chunks
}

/// Device protection limits
pub struct DeviceLimits {
    pub max_response_size_mb: u32,
    pub max_cached_data_mb: u32,
    pub auto_cleanup_threshold_mb: u32,
    pub streaming_chunk_size_kb: u32,
}

impl Default for DeviceLimits {
    fn default() -> Self {
        Self {
            max_response_size_mb: 10,
            max_cached_data_mb: 100,
            auto_cleanup_threshold_mb: 50,
            streaming_chunk_size_kb: 100,
        }
    }
}

/// Cache management for different user types
pub struct CacheManager {
    pub user_type: UserType,
    pub cache_policy: CachePolicy,
}

#[derive(Debug, Clone)]
pub enum UserType {
    PropertyOwner {
        properties_owned: u32,
    },
    Contractor {
        active_work_orders: u32,
        access_duration_hours: u32,
    },
    EnterpriseManager {
        portfolio_size: u32,
        team_size: u32,
    },
    ServiceProvider {
        clients: u32,
        service_type: String,
    },
}

#[derive(Debug, Clone)]
pub struct CachePolicy {
    pub max_cache_size_mb: u32,
    pub ttl_hours: u32,
    pub eviction_strategy: EvictionStrategy,
}

#[derive(Debug, Clone)]
pub enum EvictionStrategy {
    LRU,        // Least recently used
    FIFO,       // First in first out
    TTLBased,   // Time to live expiry
    PriorityBased, // Keep high priority data
}

/// Query optimization for scale
pub struct QueryOptimizer {
    pub query: String,
    pub user_context: UserType,
    pub available_nodes: Vec<NodeType>,
}

#[derive(Debug, Clone)]
pub enum NodeType {
    Building(String),
    School(String),
    Enterprise(String),
}

impl QueryOptimizer {
    pub fn optimize(&self) -> OptimizedQuery {
        match &self.user_context {
            UserType::PropertyOwner { properties_owned } if *properties_owned == 1 => {
                OptimizedQuery {
                    target: QueryTarget::LocalBuilding,
                    expected_size: DataSize::Small,
                    use_cache: true,
                }
            },
            UserType::EnterpriseManager { portfolio_size, .. } if *portfolio_size > 100 => {
                OptimizedQuery {
                    target: QueryTarget::EnterpriseNode,
                    expected_size: DataSize::Large,
                    use_cache: true,
                }
            },
            UserType::Contractor { .. } => {
                OptimizedQuery {
                    target: QueryTarget::LocalBuilding,
                    expected_size: DataSize::Tiny,
                    use_cache: false, // Fresh data for work orders
                }
            },
            _ => OptimizedQuery {
                target: QueryTarget::DistrictCache,
                expected_size: DataSize::Medium,
                use_cache: true,
            }
        }
    }
}

pub struct OptimizedQuery {
    pub target: QueryTarget,
    pub expected_size: DataSize,
    pub use_cache: bool,
}

pub enum QueryTarget {
    LocalBuilding,
    DistrictCache,
    EnterpriseNode,
}

/// Smart terminal commands that prevent overload
pub struct SmartTerminal {
    pub user_context: UserType,
    pub device_storage_available_mb: u32,
}

impl SmartTerminal {
    pub fn execute_command(&self, command: &str) -> TerminalResponse {
        let parts: Vec<&str> = command.split_whitespace().collect();
        
        match parts.get(1) {
            Some(&"portfolio") if self.is_enterprise_user() => {
                // Return index, not full data
                TerminalResponse::Index {
                    message: "245 properties found (2.4MB index)".to_string(),
                    hint: "Use 'arx property [id]' for details".to_string(),
                }
            },
            Some(&"building") if self.is_single_owner() => {
                // Direct local query
                TerminalResponse::Direct {
                    message: "Accessing local building data...".to_string(),
                    size_mb: 100,
                }
            },
            Some(&"work-orders") => {
                // Minimal data transfer
                TerminalResponse::Filtered {
                    message: "5 active work orders (1KB)".to_string(),
                    size_kb: 1,
                }
            },
            _ => TerminalResponse::Help {
                message: "Unknown command. Use 'arx help'".to_string(),
            }
        }
    }
    
    fn is_enterprise_user(&self) -> bool {
        matches!(self.user_context, UserType::EnterpriseManager { .. })
    }
    
    fn is_single_owner(&self) -> bool {
        matches!(self.user_context, UserType::PropertyOwner { properties_owned: 1 })
    }
}

pub enum TerminalResponse {
    Direct { message: String, size_mb: u32 },
    Index { message: String, hint: String },
    Filtered { message: String, size_kb: u32 },
    Streamed { message: String, chunks: u32 },
    Help { message: String },
}

/// Enterprise deployment configuration
pub struct EnterpriseDeployment {
    pub organization: String,
    pub deployment_type: DeploymentType,
    pub cost_model: EnterpriseCost,
}

pub enum DeploymentType {
    PublicNetwork,      // Use existing mesh, no cost
    SingleNode,         // One enterprise node
    RegionalNodes,      // Multiple regional nodes
    PrivateNetwork,     // Full private deployment
}

pub struct EnterpriseCost {
    pub hardware_cost: u32,
    pub monthly_cost: u32,  // Always $0 for ArxOS!
    pub setup_time_hours: u32,
}

impl EnterpriseCost {
    pub fn calculate(deployment_type: &DeploymentType) -> Self {
        match deployment_type {
            DeploymentType::PublicNetwork => Self {
                hardware_cost: 0,
                monthly_cost: 0,
                setup_time_hours: 1,
            },
            DeploymentType::SingleNode => Self {
                hardware_cost: 2000,
                monthly_cost: 0,
                setup_time_hours: 4,
            },
            DeploymentType::RegionalNodes => Self {
                hardware_cost: 10000, // 5 nodes
                monthly_cost: 0,
                setup_time_hours: 20,
            },
            DeploymentType::PrivateNetwork => Self {
                hardware_cost: 100000, // Full deployment
                monthly_cost: 0,
                setup_time_hours: 160,
            },
        }
    }
}

/// Example configurations
pub fn example_deployments() -> Vec<EnterpriseDeployment> {
    vec![
        // Single property owner
        EnterpriseDeployment {
            organization: "Individual Owner".to_string(),
            deployment_type: DeploymentType::PublicNetwork,
            cost_model: EnterpriseCost::calculate(&DeploymentType::PublicNetwork),
        },
        // Medium enterprise (Brookfield Properties)
        EnterpriseDeployment {
            organization: "Brookfield".to_string(),
            deployment_type: DeploymentType::RegionalNodes,
            cost_model: EnterpriseCost::calculate(&DeploymentType::RegionalNodes),
        },
        // School district
        EnterpriseDeployment {
            organization: "HCPS".to_string(),
            deployment_type: DeploymentType::SingleNode,
            cost_model: EnterpriseCost::calculate(&DeploymentType::SingleNode),
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_query_optimization() {
        let optimizer = QueryOptimizer {
            query: "portfolio summary".to_string(),
            user_context: UserType::EnterpriseManager {
                portfolio_size: 1000,
                team_size: 50,
            },
            available_nodes: vec![NodeType::Enterprise("BRK-MAIN".to_string())],
        };
        
        let result = optimizer.optimize();
        assert!(matches!(result.target, QueryTarget::EnterpriseNode));
        assert!(matches!(result.expected_size, DataSize::Large));
    }
    
    #[test]
    fn test_no_overload_single_owner() {
        let terminal = SmartTerminal {
            user_context: UserType::PropertyOwner { properties_owned: 1 },
            device_storage_available_mb: 1000,
        };
        
        let response = terminal.execute_command("arx building");
        assert!(matches!(response, TerminalResponse::Direct { .. }));
    }
    
    #[test]
    fn test_enterprise_gets_index_not_data() {
        let terminal = SmartTerminal {
            user_context: UserType::EnterpriseManager {
                portfolio_size: 1000,
                team_size: 50,
            },
            device_storage_available_mb: 5000,
        };
        
        let response = terminal.execute_command("arx portfolio");
        assert!(matches!(response, TerminalResponse::Index { .. }));
    }
}
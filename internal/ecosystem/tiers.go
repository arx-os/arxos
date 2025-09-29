package ecosystem

// Tier represents the three-tier ecosystem architecture
type Tier string

const (
	// Layer 1: FREE - Like Git
	// Core ArxOS engine, CLI, basic APIs, PostGIS, version control
	TierCore Tier = "core"

	// Layer 2: FREEMIUM - Like GitHub Free
	// Hardware designs, certified marketplace, basic templates
	TierHardware Tier = "hardware"

	// Layer 3: PAID - Like GitHub Pro
	// Visual workflow automation, CMMS/CAFM, enterprise features
	TierWorkflow Tier = "workflow"
)

// TierInfo contains information about each tier
type TierInfo struct {
	Name         string                 `json:"name"`
	Description  string                 `json:"description"`
	Price        string                 `json:"price"`
	Features     []string               `json:"features"`
	Limits       map[string]interface{} `json:"limits"`
	APIEndpoints []string               `json:"api_endpoints"`
}

// GetTierInfo returns information about a specific tier
func GetTierInfo(tier Tier) TierInfo {
	switch tier {
	case TierCore:
		return TierInfo{
			Name:        "ArxOS Core",
			Description: "The 'Git' of buildings - free platform",
			Price:       "FREE",
			Features: []string{
				"Pure Go/TinyGo codebase",
				"Path-based architecture",
				"PostGIS spatial intelligence",
				"CLI commands",
				"Basic REST APIs",
				"Version control",
				"Hardware designs",
			},
			Limits: map[string]interface{}{
				"buildings":  -1, // unlimited
				"users":      5,
				"api_calls":  1000,
				"storage_gb": 10,
				"support":    "community",
			},
			APIEndpoints: []string{
				"/api/v1/buildings",
				"/api/v1/equipment",
				"/api/v1/spatial",
				"/api/v1/export",
				"/api/v1/import",
			},
		}

	case TierHardware:
		return TierInfo{
			Name:        "Hardware Platform",
			Description: "The 'GitHub Free' - IoT ecosystem",
			Price:       "FREEMIUM",
			Features: []string{
				"Certified hardware marketplace",
				"Device templates and SDK",
				"Gateway software",
				"Protocol translation",
				"Basic device management",
				"Community support",
			},
			Limits: map[string]interface{}{
				"certified_devices": 10,
				"marketplace_sales": 5,
				"support":           "community",
				"commission":        "5-10%",
			},
			APIEndpoints: []string{
				"/api/v1/hardware/devices",
				"/api/v1/hardware/templates",
				"/api/v1/hardware/gateway",
				"/api/v1/hardware/marketplace",
			},
		}

	case TierWorkflow:
		return TierInfo{
			Name:        "Workflow Automation",
			Description: "The 'GitHub Pro' - enterprise CMMS/CAFM platform",
			Price:       "PAID",
			Features: []string{
				"Visual workflow builder (n8n)",
				"CMMS/CAFM features",
				"Physical building automation",
				"Enterprise integrations",
				"Advanced analytics",
				"Professional support",
			},
			Limits: map[string]interface{}{
				"buildings":    -1, // unlimited
				"users":        -1, // unlimited
				"workflows":    -1, // unlimited
				"integrations": 400,
				"api_calls":    -1, // unlimited
				"storage_gb":   -1, // unlimited
				"support":      "professional",
				"sla":          "99.9%",
			},
			APIEndpoints: []string{
				"/api/v1/workflows",
				"/api/v1/automation",
				"/api/v1/cmmc",
				"/api/v1/analytics",
				"/api/v1/integrations",
				"/api/v1/enterprise",
			},
		}

	default:
		return TierInfo{}
	}
}

// GetAvailableTiers returns all available tiers
func GetAvailableTiers() []Tier {
	return []Tier{TierCore, TierHardware, TierWorkflow}
}

// IsFeatureAvailable checks if a feature is available in a tier
func IsFeatureAvailable(tier Tier, feature string) bool {
	tierInfo := GetTierInfo(tier)

	for _, tierFeature := range tierInfo.Features {
		if tierFeature == feature {
			return true
		}
	}
	return false
}

// IsEndpointAvailable checks if an API endpoint is available in a tier
func IsEndpointAvailable(tier Tier, endpoint string) bool {
	tierInfo := GetTierInfo(tier)

	for _, tierEndpoint := range tierInfo.APIEndpoints {
		if tierEndpoint == endpoint {
			return true
		}
	}
	return false
}

// GetTierLimits returns the limits for a specific tier
func GetTierLimits(tier Tier) map[string]interface{} {
	tierInfo := GetTierInfo(tier)
	return tierInfo.Limits
}

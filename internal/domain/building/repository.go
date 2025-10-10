package building

import (
	"time"
)

// BuildingRepository represents a version-controlled building repository
// This is the core domain model for the "Git of Buildings" concept
type BuildingRepository struct {
	ID        string              `json:"id"`
	Name      string              `json:"name"`
	Type      BuildingType        `json:"type"`
	Floors    int                 `json:"floors"`
	Structure RepositoryStructure `json:"structure"`
	Versions  []Version           `json:"versions"`
	Current   *Version            `json:"current"`
	CreatedAt time.Time           `json:"created_at"`
	UpdatedAt time.Time           `json:"updated_at"`
}

// BuildingType represents the type of building
type BuildingType string

const (
	BuildingTypeOffice      BuildingType = "office"
	BuildingTypeHospital    BuildingType = "hospital"
	BuildingTypeSchool      BuildingType = "school"
	BuildingTypeResidential BuildingType = "residential"
	BuildingTypeIndustrial  BuildingType = "industrial"
	BuildingTypeRetail      BuildingType = "retail"
)

// RepositoryStructure represents the standardized directory structure
// This implements the BUILDING_REPOSITORY_DESIGN.md structure
type RepositoryStructure struct {
	IFCFiles     []IFCFile      `json:"ifc_files"`
	Plans        []Plan         `json:"plans"`
	Equipment    []Equipment    `json:"equipment"`
	Operations   OperationsData `json:"operations"`
	Integrations []Integration  `json:"integrations"`
}

// IFCFile represents an IFC building model file
type IFCFile struct {
	ID         string    `json:"id"`
	Name       string    `json:"name"`
	Path       string    `json:"path"`
	Version    string    `json:"version"`    // IFC version (4.0, 4.3, etc.)
	Discipline string    `json:"discipline"` // architectural, hvac, electrical, etc.
	Size       int64     `json:"size"`
	Entities   int       `json:"entities"`
	Validated  bool      `json:"validated"`
	CreatedAt  time.Time `json:"created_at"`
	UpdatedAt  time.Time `json:"updated_at"`
}

// Plan represents floor plans and drawings
type Plan struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Path      string    `json:"path"`
	Type      string    `json:"type"` // floor-plan, site-plan, section, etc.
	Floor     string    `json:"floor"`
	Format    string    `json:"format"` // ifc, etc.
	Size      int64     `json:"size"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// Equipment represents equipment specifications
type Equipment struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Path      string    `json:"path"`
	Type      string    `json:"type"`   // hvac, electrical, plumbing, etc.
	Format    string    `json:"format"` // ifc
	Size      int64     `json:"size"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// OperationsData represents operational data
type OperationsData struct {
	Maintenance MaintenanceData `json:"maintenance"`
	Energy      EnergyData      `json:"energy"`
	Occupancy   OccupancyData   `json:"occupancy"`
}

// MaintenanceData represents maintenance records and schedules
type MaintenanceData struct {
	Schedules   []Schedule   `json:"schedules"`
	WorkOrders  []WorkOrder  `json:"work_orders"`
	Inspections []Inspection `json:"inspections"`
}

// EnergyData represents energy data and optimization
type EnergyData struct {
	Consumption  []ConsumptionRecord `json:"consumption"`
	Benchmarks   []Benchmark         `json:"benchmarks"`
	Optimization []OptimizationRule  `json:"optimization"`
}

// OccupancyData represents occupancy and usage data
type OccupancyData struct {
	Schedules   []OccupancySchedule `json:"schedules"`
	Utilization []UtilizationRecord `json:"utilization"`
}

// Integration represents external system integration
type Integration struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Type      string    `json:"type"`   // bms, sensors, api
	Config    string    `json:"config"` // Configuration file path
	Enabled   bool      `json:"enabled"`
	LastSync  time.Time `json:"last_sync"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// Supporting types for operations data
type Schedule struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Type      string    `json:"type"`
	Frequency string    `json:"frequency"`
	CreatedAt time.Time `json:"created_at"`
}

type WorkOrder struct {
	ID          string    `json:"id"`
	Title       string    `json:"title"`
	Description string    `json:"description"`
	Status      string    `json:"status"`
	Priority    string    `json:"priority"`
	CreatedAt   time.Time `json:"created_at"`
}

type Inspection struct {
	ID        string    `json:"id"`
	Type      string    `json:"type"`
	Date      time.Time `json:"date"`
	Status    string    `json:"status"`
	CreatedAt time.Time `json:"created_at"`
}

type ConsumptionRecord struct {
	ID        string    `json:"id"`
	Date      time.Time `json:"date"`
	Value     float64   `json:"value"`
	Unit      string    `json:"unit"`
	CreatedAt time.Time `json:"created_at"`
}

type Benchmark struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Value     float64   `json:"value"`
	Unit      string    `json:"unit"`
	CreatedAt time.Time `json:"created_at"`
}

type OptimizationRule struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Condition string    `json:"condition"`
	Action    string    `json:"action"`
	CreatedAt time.Time `json:"created_at"`
}

type OccupancySchedule struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Schedule  string    `json:"schedule"`
	CreatedAt time.Time `json:"created_at"`
}

type UtilizationRecord struct {
	ID        string    `json:"id"`
	Date      time.Time `json:"date"`
	Value     float64   `json:"value"`
	CreatedAt time.Time `json:"created_at"`
}

package commands

// InitOptions for building initialization
type InitOptions struct {
	Name     string
	UUID     string
	Template string
}

// ImportOptions defines options for the import command
type ImportOptions struct {
	InputFile      string
	Format         string
	BuildingID     string
	BuildingName   string
	ToDatabase     bool
	ToBIM          bool
	OutputFile     string
	ValidateOnly   bool // Only validate, don't save
	MergeExisting  bool // Merge with existing data
	EnhanceSpatial bool // Enhance with spatial data
}

// ExportOptions defines options for the export command
type ExportOptions struct {
	BuildingID        string
	Format            string
	IncludeIntel      bool
	IncludeHistory    bool
	SimulateBeforeExp bool
	OutputFile        string
	Template          string // Report template
	Filters           ExportFilters
	Verbose           bool
}

// ExportFilters for filtering export data
type ExportFilters struct {
	IncludeTypes []string
	ExcludeTypes []string
	Floors       []string
	Systems      []string
}

// SimulateOptions defines options for the simulate command
type SimulateOptions struct {
	BuildingID   string
	Simulations  []string
	SaveResults  bool
	RealtimeMode bool
}

// QueryOptions defines options for the query command
type QueryOptions struct {
	Building   string // Building ID filter
	Status     string
	Type       string
	Floor      int
	System     string // System filter
	Room       string // Room filter
	SQL        string // Raw SQL query
	Output     string // Output format
	Limit      int    // Max results
	Offset     int    // Result offset
	Count      bool   // Count only
	Fields     []string // Fields to display
	Spatial    string
	Format     string
	OutputFile string

	// Spatial query parameters
	Near      string  // Coordinates for proximity search (x,y,z)
	Radius    float64 // Search radius in meters
	Within    string  // Bounding box (minX,minY,minZ,maxX,maxY,maxZ)
	Contains  string  // Point to check containment (x,y,z)
}

// SyncOptions defines options for the sync command
type SyncOptions struct {
	Direction  string
	BuildingID string
	GitRepo    string
	AutoCommit bool
}

// ValidateOptions defines options for the validate command
type ValidateOptions struct {
	InputFile  string
	Strict     bool
	AutoFix    bool
	OutputFile string
}

// ServeOptions defines options for the API server
type ServeOptions struct {
	Port         int
	DatabasePath string
	EnableCORS   bool
	AuthToken    string
}
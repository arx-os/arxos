package commands

// InitOptions for building initialization
type InitOptions struct {
	Name     string
	UUID     string
	Template string
}

// ImportOptions defines options for the import command
type ImportOptions struct {
	InputFile    string
	Format       string
	BuildingID   string
	BuildingName string
	ToDatabase   bool
	ToBIM        bool
	OutputFile   string
}

// ExportOptions defines options for the export command
type ExportOptions struct {
	BuildingID        string
	Format            string
	IncludeIntel      bool
	IncludeHistory    bool
	SimulateBeforeExp bool
	OutputFile        string
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
	BuildingID string
	Status     string
	Type       string
	Floor      int
	Spatial    string
	Format     string
	OutputFile string
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
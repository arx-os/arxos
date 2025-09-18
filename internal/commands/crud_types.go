package commands

// Component represents a building component
type Component struct {
	Path         string                 `json:"path"`
	Type         string                 `json:"type"`
	Name         string                 `json:"name"`
	Status       string                 `json:"status"`
	Position     *Position              `json:"position,omitempty"`
	Manufacturer string                 `json:"manufacturer,omitempty"`
	Model        string                 `json:"model,omitempty"`
	Properties   map[string]interface{} `json:"properties,omitempty"`
}

// Position represents 3D coordinates
type Position struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// ComponentUpdates represents updates to a component
type ComponentUpdates struct {
	Path       string            `json:"path"`
	Name       *string           `json:"name,omitempty"`
	Status     *string           `json:"status,omitempty"`
	Position   *Position         `json:"position,omitempty"`
	Properties map[string]string `json:"properties,omitempty"`
}

// RemoveOptions for removing components
type RemoveOptions struct {
	Path    string `json:"path"`
	Cascade bool   `json:"cascade"`
}

// ListOptions for listing components
type ListOptions struct {
	Path   string `json:"path,omitempty"`
	Type   string `json:"type,omitempty"`
	Status string `json:"status,omitempty"`
	System string `json:"system,omitempty"`
	Floor  int    `json:"floor,omitempty"`
}

// TraceOptions for tracing connections
type TraceOptions struct {
	Path   string `json:"path"`
	System string `json:"system,omitempty"`
}

// TraceResult represents the result of a trace operation
type TraceResult struct {
	StartPath   string       `json:"start_path"`
	Connections []Connection `json:"connections"`
}

// Connection represents a system connection
type Connection struct {
	From     string       `json:"from"`
	To       string       `json:"to"`
	Type     string       `json:"type"`
	Children []Connection `json:"children,omitempty"`
}

// UniversalPath represents the parsed components of a universal address
type UniversalPath struct {
	Building  string `json:"building,omitempty"`
	Floor     string `json:"floor,omitempty"`
	Zone      string `json:"zone,omitempty"`
	Room      string `json:"room,omitempty"`
	System    string `json:"system,omitempty"`
	Equipment string `json:"equipment,omitempty"`
}

// QueryResults represents query results
type QueryResults struct {
	Columns    []string                 `json:"columns"`
	Rows       []map[string]interface{} `json:"rows"`
	Count      int                      `json:"count"`
	Total      int                      `json:"total"`
	JSONOutput string                   `json:"-"` // For JSON formatted output
}

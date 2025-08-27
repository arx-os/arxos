package commands

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/arxos/arxos/cmd/models"
	"github.com/spf13/cobra"
	"gopkg.in/yaml.v3"
)

// InitCmd represents the arx init command
var InitCmd = &cobra.Command{
	Use:   "init [building-id]",
	Short: "Initialize a new building filesystem",
	Long: `Initialize creates a new building filesystem and ArxObject hierarchy.
	
This command sets up the foundational structure that enables all other
Arxos operations. Think of it as 'git init' for buildings.

Examples:
  arx init building:main
  arx init building:hq --type office --floors 5
  arx init building:warehouse --from-pdf "floor_plan.pdf" --type industrial
  arx init building:office --template "standard_office" --floors 3`,
	Args: cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		buildingID := args[0]
		return initializeBuilding(buildingID, cmd)
	},
}

// InitOptions holds all initialization options
type InitOptions struct {
	BuildingType string
	Floors       int
	Area         string
	Location     string
	FromPDF      string
	FromIFC      string
	ConfigFile   string
	Template     string
	Force        bool
}

// BuildingConfig represents the main building configuration
type BuildingConfig struct {
	BuildingID string                  `yaml:"building_id"`
	Type       string                  `yaml:"type"`
	Floors     int                     `yaml:"floors"`
	Area       string                  `yaml:"area"`
	Location   string                  `yaml:"location"`
	Created    time.Time               `yaml:"created"`
	Version    string                  `yaml:"version"`
	Systems    map[string]SystemConfig `yaml:"systems"`
}

// SystemConfig represents a building system configuration
type SystemConfig struct {
	Type   string                 `yaml:"type"`
	Status string                 `yaml:"status"`
	Config map[string]interface{} `yaml:"config,omitempty"`
}

// FloorConfig represents a floor configuration
type FloorConfig struct {
	FloorNumber int    `yaml:"floor_number"`
	Height      int    `yaml:"height"` // in millimeters
	Area        string `yaml:"area"`
	Status      string `yaml:"status"`
}

func init() {
	// Add flags to the init command
	InitCmd.Flags().String("type", "office", "Building type (office, residential, industrial, retail)")
	InitCmd.Flags().Int("floors", 1, "Number of floors")
	InitCmd.Flags().String("area", "", "Total building area (e.g., '25,000 sq ft')")
	InitCmd.Flags().String("location", "", "Building location/address")
	InitCmd.Flags().String("from-pdf", "", "Initialize from PDF floor plan")
	InitCmd.Flags().String("from-ifc", "", "Initialize from IFC file")
	InitCmd.Flags().String("config", "", "Use custom configuration file")
	InitCmd.Flags().String("template", "", "Use predefined building template")
	InitCmd.Flags().Bool("force", false, "Overwrite existing building if it exists")
}

// initializeBuilding is the main initialization function
func initializeBuilding(buildingID string, cmd *cobra.Command) error {
	// 1. Parse and validate options
	options, err := parseInitOptions(cmd)
	if err != nil {
		return fmt.Errorf("failed to parse options: %w", err)
	}

	// 2. Validate building ID format
	if err := validateBuildingID(buildingID); err != nil {
		return fmt.Errorf("invalid building ID: %w", err)
	}

	// 3. Check if building already exists
	if buildingExists(buildingID) && !options.Force {
		return fmt.Errorf("building %s already exists. Use --force to overwrite", buildingID)
	}

	// 4. Create building filesystem structure
	if err := createBuildingFilesystem(buildingID); err != nil {
		return fmt.Errorf("failed to create filesystem: %w", err)
	}

	// 5. Initialize ArxObject hierarchy via CGO
	if err := initializeArxObjectHierarchy(buildingID, options); err != nil {
		return fmt.Errorf("failed to initialize ArxObjects: %w", err)
	}

	// 6. Create initial configuration files
	if err := createInitialConfiguration(buildingID, options); err != nil {
		return fmt.Errorf("failed to create configuration: %w", err)
	}

	// 7. Set up version control
	if err := initializeVersionControl(buildingID); err != nil {
		return fmt.Errorf("failed to initialize version control: %w", err)
	}

	// 8. Process input files if provided
	if err := processInputFiles(buildingID, options); err != nil {
		return fmt.Errorf("failed to process input files: %w", err)
	}

	// 9. Validate the created structure
	if err := validateBuildingStructure(buildingID); err != nil {
		return fmt.Errorf("failed to validate building structure: %w", err)
	}

	// 10. Success feedback
	printSuccessMessage(buildingID)

	return nil
}

// parseInitOptions extracts and validates all initialization options
func parseInitOptions(cmd *cobra.Command) (*InitOptions, error) {
	options := &InitOptions{}

	// Extract string flags
	if val, err := cmd.Flags().GetString("type"); err == nil {
		options.BuildingType = val
	}
	if val, err := cmd.Flags().GetString("area"); err == nil {
		options.Area = val
	}
	if val, err := cmd.Flags().GetString("location"); err == nil {
		options.Location = val
	}
	if val, err := cmd.Flags().GetString("from-pdf"); err == nil {
		options.FromPDF = val
	}
	if val, err := cmd.Flags().GetString("from-ifc"); err == nil {
		options.FromIFC = val
	}
	if val, err := cmd.Flags().GetString("config"); err == nil {
		options.ConfigFile = val
	}
	if val, err := cmd.Flags().GetString("template"); err == nil {
		options.Template = val
	}

	// Extract numeric flags
	if val, err := cmd.Flags().GetInt("floors"); err == nil {
		options.Floors = val
	}

	// Extract boolean flags
	if val, err := cmd.Flags().GetBool("force"); err == nil {
		options.Force = val
	}

	// Validate options
	if err := validateInitOptions(options); err != nil {
		return nil, err
	}

	return options, nil
}

// validateInitOptions validates the initialization options
func validateInitOptions(options *InitOptions) error {
	// Validate building type
	validTypes := []string{"office", "residential", "industrial", "retail", "mixed_use"}
	typeValid := false
	for _, validType := range validTypes {
		if options.BuildingType == validType {
			typeValid = true
			break
		}
	}
	if !typeValid {
		return fmt.Errorf("invalid building type: %s. Must be one of: %v", options.BuildingType, validTypes)
	}

	// Validate floors
	if options.Floors < 1 || options.Floors > 200 {
		return fmt.Errorf("invalid floor count: %d. Must be between 1 and 200", options.Floors)
	}

	// Validate area format if provided
	if options.Area != "" {
		if !isValidAreaFormat(options.Area) {
			return fmt.Errorf("invalid area format: %s. Expected format: '25,000 sq ft'", options.Area)
		}
	}

	// Validate that not both PDF and IFC are specified
	if options.FromPDF != "" && options.FromIFC != "" {
		return fmt.Errorf("cannot specify both --from-pdf and --from-ifc")
	}

	return nil
}

// validateBuildingID validates the building ID format
func validateBuildingID(buildingID string) error {
	// Building ID must follow the pattern: building:name
	if !strings.HasPrefix(buildingID, "building:") {
		return fmt.Errorf("building ID must start with 'building:'")
	}

	name := strings.TrimPrefix(buildingID, "building:")
	if name == "" {
		return fmt.Errorf("building ID must include a name after 'building:'")
	}

	// Name must contain only alphanumeric characters, hyphens, and underscores
	for _, char := range name {
		if !((char >= 'a' && char <= 'z') || (char >= 'A' && char <= 'Z') ||
			(char >= '0' && char <= '9') || char == '-' || char == '_') {
			return fmt.Errorf("building name contains invalid character: %c", char)
		}
	}

	return nil
}

// buildingExists checks if a building already exists
func buildingExists(buildingID string) bool {
	buildingPath := getBuildingPath(buildingID)
	_, err := os.Stat(buildingPath)
	return err == nil
}

// getBuildingPath returns the filesystem path for a building
func getBuildingPath(buildingID string) string {
	// Check for custom building path from environment or config
	if customPath := os.Getenv("ARXOS_BUILDING_PATH"); customPath != "" {
		return filepath.Join(customPath, buildingID)
	}

	// Check for config file override
	if configPath := getConfigBuildingPath(); configPath != "" {
		return filepath.Join(configPath, buildingID)
	}

	// Default: create in current directory
	return buildingID
}

// getConfigBuildingPath reads building path from configuration
func getConfigBuildingPath() string {
	// Check for user config file
	homeDir, err := os.UserHomeDir()
	if err == nil {
		configPath := filepath.Join(homeDir, ".arxos", "config.yaml")
		if _, err := os.Stat(configPath); err == nil {
			// Read and parse YAML config
			if configData, err := os.ReadFile(configPath); err == nil {
				var config map[string]interface{}
				if err := yaml.Unmarshal(configData, &config); err == nil {
					if buildingPath, ok := config["building_path"].(string); ok && buildingPath != "" {
						return buildingPath
					}
				}
			}
		}
	}

	return ""
}

// createBuildingFilesystem creates the directory structure for a building
func createBuildingFilesystem(buildingID string) error {
	basePath := getBuildingPath(buildingID)

	// Create main building directory
	if err := os.MkdirAll(basePath, 0755); err != nil {
		return fmt.Errorf("failed to create building directory: %w", err)
	}

	// Create metadata directory structure
	metadataDirs := []string{
		".arxos/config",
		".arxos/objects",
		".arxos/vcs/snapshots",
		".arxos/vcs/branches",
		".arxos/vcs/metadata",
		".arxos/cache",
		".arxos/logs",
		"systems/electrical",
		"systems/hvac",
		"systems/automation",
		"systems/plumbing",
		"systems/fire_protection",
		"systems/security",
		"schemas",
	}

	for _, dir := range metadataDirs {
		fullPath := filepath.Join(basePath, dir)
		if err := os.MkdirAll(fullPath, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	return nil
}

// ArxObject represents a building element in the hierarchy
type ArxObject struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Description string                 `json:"description,omitempty"`
	Properties  map[string]interface{} `json:"properties,omitempty"`
	Location    *models.Location              `json:"location,omitempty"`
	Children    []*ArxObject           `json:"children,omitempty"`
	Parent      string                 `json:"parent,omitempty"`
	Status      string                 `json:"status"`
	Created     time.Time              `json:"created"`
	Updated     time.Time              `json:"updated"`
}


// initializeArxObjectHierarchy creates the core building hierarchy
func initializeArxObjectHierarchy(buildingID string, options *InitOptions) error {
	fmt.Printf("Initializing ArxObject hierarchy for building: %s\n", buildingID)
	fmt.Printf("Building type: %s, Floors: %d\n", options.BuildingType, options.Floors)

	basePath := getBuildingPath(buildingID)
	objectsPath := filepath.Join(basePath, ".arxos", "objects")

	// Create objects directory if it doesn't exist
	if err := os.MkdirAll(objectsPath, 0755); err != nil {
		return fmt.Errorf("failed to create objects directory: %w", err)
	}

	// Create building root ArxObject
	buildingObject := &ArxObject{
		ID:          buildingID,
		Name:        fmt.Sprintf("Building %s", buildingID),
		Type:        "building",
		Description: fmt.Sprintf("%s building with %d floors", options.BuildingType, options.Floors),
		Properties: map[string]interface{}{
			"building_type": options.BuildingType,
			"floors":        options.Floors,
			"area":          options.Area,
			"location":      options.Location,
		},
		Status:  "active",
		Created: time.Now().UTC(),
		Updated: time.Now().UTC(),
	}

	// Create floor ArxObjects
	var floorObjects []*ArxObject
	for i := 1; i <= options.Floors; i++ {
		floorObject := &ArxObject{
			ID:          fmt.Sprintf("%s:floor:%d", buildingID, i),
			Name:        fmt.Sprintf("Floor %d", i),
			Type:        "floor",
			Description: fmt.Sprintf("Floor %d of building %s", i, buildingID),
			Properties: map[string]interface{}{
				"floor_number": i,
				"height":       3000, // 3 meters in millimeters
				"area":         options.Area,
			},
			Location: &models.Location{
				Z:        float64((i - 1) * 3000), // Stack floors vertically
				Floor:    i,
				Building: buildingID,
			},
			Parent:  buildingID,
			Status:  "active",
			Created: time.Now().UTC(),
			Updated: time.Now().UTC(),
		}
		floorObjects = append(floorObjects, floorObject)
		buildingObject.Children = append(buildingObject.Children, floorObject)
	}

	// Create system ArxObjects
	systemObjects := createSystemArxObjects(buildingID, options)
	for _, systemObj := range systemObjects {
		buildingObject.Children = append(buildingObject.Children, systemObj)
	}

	// Save building ArxObject
	buildingPath := filepath.Join(objectsPath, "building.json")
	if err := writeJSON(buildingPath, buildingObject); err != nil {
		return fmt.Errorf("failed to save building ArxObject: %w", err)
	}

	// Save floor ArxObjects
	for _, floorObj := range floorObjects {
		floorPath := filepath.Join(objectsPath, fmt.Sprintf("floor_%d.json", floorObj.Properties["floor_number"]))
		if err := writeJSON(floorPath, floorObj); err != nil {
			return fmt.Errorf("failed to save floor %d ArxObject: %w", floorObj.Properties["floor_number"], err)
		}
	}

	// Save system ArxObjects
	for _, systemObj := range systemObjects {
		systemPath := filepath.Join(objectsPath, fmt.Sprintf("system_%s.json", systemObj.Type))
		if err := writeJSON(systemPath, systemObj); err != nil {
			return fmt.Errorf("failed to save system %s ArxObject: %w", systemObj.Type, err)
		}
	}

	// Create ArxObject index
	index := createArxObjectIndex(buildingObject, floorObjects, systemObjects)
	indexPath := filepath.Join(objectsPath, "index.json")
	if err := writeJSON(indexPath, index); err != nil {
		return fmt.Errorf("failed to save ArxObject index: %w", err)
	}

	fmt.Printf("✅ Created %d ArxObjects in building hierarchy\n", len(floorObjects)+len(systemObjects)+1)
	return nil
}

// createSystemArxObjects creates ArxObjects for building systems
func createSystemArxObjects(buildingID string, options *InitOptions) []*ArxObject {
	var systems []*ArxObject

	systemTypes := map[string]map[string]interface{}{
		"electrical": {
			"voltage":  "480V",
			"capacity": "800A",
			"panels":   4,
		},
		"hvac": {
			"type":            "vav",
			"zones_per_floor": 4,
			"units":           2,
		},
		"automation": {
			"protocols":   []string{"BACnet", "Modbus"},
			"controllers": 8,
		},
		"plumbing": {
			"water_supply": "municipal",
			"fixtures":     24,
		},
		"fire_protection": {
			"sprinkler_system": true,
			"alarms":           12,
		},
		"security": {
			"access_control": true,
			"surveillance":   true,
			"cameras":        16,
		},
	}

	for systemType, properties := range systemTypes {
		systemObj := &ArxObject{
			ID:          fmt.Sprintf("%s:system:%s", buildingID, systemType),
			Name:        fmt.Sprintf("%s System", strings.Title(systemType)),
			Type:        "system",
			Description: fmt.Sprintf("%s system for building %s", strings.Title(systemType), buildingID),
			Properties:  properties,
			Parent:      buildingID,
			Status:      "inactive",
			Created:     time.Now().UTC(),
			Updated:     time.Now().UTC(),
		}
		systems = append(systems, systemObj)
	}

	return systems
}

// ArxObjectIndex represents the index of all ArxObjects in a building
type ArxObjectIndex struct {
	BuildingID string              `json:"building_id"`
	TotalCount int                 `json:"total_count"`
	ByType     map[string][]string `json:"by_type"`
	ByLocation map[string][]string `json:"by_location"`
	Hierarchy  map[string][]string `json:"hierarchy"`
	Created    time.Time           `json:"created"`
	Updated    time.Time           `json:"updated"`
}

// createArxObjectIndex creates an index of all ArxObjects
func createArxObjectIndex(building *ArxObject, floors []*ArxObject, systems []*ArxObject) *ArxObjectIndex {
	index := &ArxObjectIndex{
		BuildingID: building.ID,
		TotalCount: 1 + len(floors) + len(systems), // building + floors + systems
		ByType:     make(map[string][]string),
		ByLocation: make(map[string][]string),
		Hierarchy:  make(map[string][]string),
		Created:    time.Now().UTC(),
		Updated:    time.Now().UTC(),
	}

	// Index by type
	index.ByType["building"] = []string{building.ID}
	index.ByType["floor"] = make([]string, len(floors))
	index.ByType["system"] = make([]string, len(systems))

	for i, floor := range floors {
		index.ByType["floor"][i] = floor.ID
	}
	for i, system := range systems {
		index.ByType["system"][i] = system.ID
	}

	// Index by location (floor)
	index.ByLocation["ground"] = []string{building.ID}
	for _, floor := range floors {
		floorNum := floor.Properties["floor_number"].(int)
		index.ByLocation[fmt.Sprintf("floor_%d", floorNum)] = []string{floor.ID}
	}

	// Index hierarchy
	index.Hierarchy[building.ID] = make([]string, len(floors)+len(systems))
	for i, floor := range floors {
		index.Hierarchy[building.ID][i] = floor.ID
	}
	for i, system := range systems {
		index.Hierarchy[building.ID][len(floors)+i] = system.ID
	}

	return index
}

// createInitialConfiguration generates the initial configuration files
func createInitialConfiguration(buildingID string, options *InitOptions) error {
	basePath := getBuildingPath(buildingID)

	// Create main building configuration
	mainConfig := BuildingConfig{
		BuildingID: buildingID,
		Type:       options.BuildingType,
		Floors:     options.Floors,
		Area:       options.Area,
		Location:   options.Location,
		Created:    time.Now().UTC(),
		Version:    "1.0.0",
		Systems: map[string]SystemConfig{
			"electrical": {
				Type:   "electrical",
				Status: "inactive",
				Config: map[string]interface{}{
					"voltage":  "480V",
					"capacity": "800A",
				},
			},
			"hvac": {
				Type:   "hvac",
				Status: "inactive",
				Config: map[string]interface{}{
					"type":            "vav",
					"zones_per_floor": 4,
				},
			},
			"automation": {
				Type:   "automation",
				Status: "inactive",
				Config: map[string]interface{}{
					"protocols": []string{"BACnet", "Modbus"},
				},
			},
			"plumbing": {
				Type:   "plumbing",
				Status: "inactive",
				Config: map[string]interface{}{
					"water_supply": "municipal",
				},
			},
			"fire_protection": {
				Type:   "fire_protection",
				Status: "inactive",
				Config: map[string]interface{}{
					"sprinkler_system": true,
				},
			},
			"security": {
				Type:   "security",
				Status: "inactive",
				Config: map[string]interface{}{
					"access_control": true,
					"surveillance":   true,
				},
			},
		},
	}

	// Write main configuration
	mainConfigPath := filepath.Join(basePath, "arxos.yml")
	if err := writeYAML(mainConfigPath, mainConfig); err != nil {
		return fmt.Errorf("failed to write main configuration: %w", err)
	}

	// Create floor configurations
	for i := 1; i <= options.Floors; i++ {
		floorConfig := FloorConfig{
			FloorNumber: i,
			Height:      3000, // 3 meters in millimeters
			Area:        options.Area,
			Status:      "inactive",
		}

		floorConfigPath := filepath.Join(basePath, fmt.Sprintf("floor:%d", i), "arxos.yml")
		if err := writeYAML(floorConfigPath, floorConfig); err != nil {
			return fmt.Errorf("failed to write floor %d configuration: %w", i, err)
		}
	}

	// Create system configurations
	for systemName, systemConfig := range mainConfig.Systems {
		systemConfigPath := filepath.Join(basePath, "systems", systemName, "arxos.yml")
		if err := writeYAML(systemConfigPath, systemConfig); err != nil {
			return fmt.Errorf("failed to write %s system configuration: %w", systemName, err)
		}
	}

	return nil
}

// initializeVersionControl sets up Git-like version control for the building
func initializeVersionControl(buildingID string) error {
	fmt.Printf("Initializing version control for building: %s\n", buildingID)

	basePath := getBuildingPath(buildingID)
	vcsDir := filepath.Join(basePath, ".arxos", "vcs")

	// Create VCS directory structure
	vcsSubdirs := []string{
		"commits",
		"branches",
		"tags",
		"refs",
		"objects",
		"logs",
	}

	for _, subdir := range vcsSubdirs {
		subdirPath := filepath.Join(vcsDir, subdir)
		if err := os.MkdirAll(subdirPath, 0755); err != nil {
			return fmt.Errorf("failed to create VCS directory %s: %w", subdir, err)
		}
	}

	// Create simple initial commit file
	commitData := map[string]interface{}{
		"id":          fmt.Sprintf("init-%s", buildingID),
		"message":     "Initial building structure",
		"author":      "arxos-cli",
		"timestamp":   time.Now().UTC(),
		"building_id": buildingID,
		"parent_id":   "",
		"type":        "initialization",
		"version":     "1.0.0",
	}

	commitPath := filepath.Join(vcsDir, "commits", "initial.json")
	if err := writeJSON(commitPath, commitData); err != nil {
		return fmt.Errorf("failed to save initial commit: %w", err)
	}

	// Create HEAD reference
	headData := map[string]interface{}{
		"name":        "HEAD",
		"type":        "branch",
		"target":      "main",
		"building_id": buildingID,
		"updated":     time.Now().UTC(),
	}

	headPath := filepath.Join(vcsDir, "refs", "HEAD.json")
	if err := writeJSON(headPath, headData); err != nil {
		return fmt.Errorf("failed to save HEAD reference: %w", err)
	}

	// Create main branch reference
	mainData := map[string]interface{}{
		"name":        "main",
		"type":        "branch",
		"target":      commitData["id"],
		"building_id": buildingID,
		"updated":     time.Now().UTC(),
	}

	mainPath := filepath.Join(vcsDir, "refs", "main.json")
	if err := writeJSON(mainPath, mainData); err != nil {
		return fmt.Errorf("failed to save main branch: %w", err)
	}

	// Create VCS configuration
	vcsConfig := map[string]interface{}{
		"building_id":     buildingID,
		"default_branch":  "main",
		"auto_commit":     true,
		"created":         time.Now().UTC(),
		"merge_strategy":  "recursive",
		"commit_template": "Building change: {message}",
	}

	configPath := filepath.Join(vcsDir, "config.json")
	if err := writeJSON(configPath, vcsConfig); err != nil {
		return fmt.Errorf("failed to save VCS config: %w", err)
	}

	// Create initial log entry
	logData := map[string]interface{}{
		"timestamp":   time.Now().UTC(),
		"action":      "init",
		"building_id": buildingID,
		"commit_id":   commitData["id"],
		"message":     "Version control initialized",
		"user":        "arxos-cli",
	}

	logPath := filepath.Join(vcsDir, "logs", "init.log")
	if err := writeJSON(logPath, logData); err != nil {
		return fmt.Errorf("failed to save log entry: %w", err)
	}

	fmt.Printf("✅ Version control initialized with initial commit: %s\n", commitData["id"])
	return nil
}

// processInputFiles handles PDF, IFC, and template processing
func processInputFiles(buildingID string, options *InitOptions) error {
	// Process PDF floor plan if provided
	if options.FromPDF != "" {
		if err := processPDFFloorPlan(buildingID, options.FromPDF); err != nil {
			return fmt.Errorf("PDF processing failed: %w", err)
		}
	}

	// Process IFC file if provided
	if options.FromIFC != "" {
		if err := processIFCFile(buildingID, options.FromIFC); err != nil {
			return fmt.Errorf("IFC processing failed: %w", err)
		}
	}

	// Apply template if provided
	if options.Template != "" {
		if err := applyBuildingTemplate(buildingID, options.Template); err != nil {
			return fmt.Errorf("template application failed: %w", err)
		}
	}

	return nil
}

// processPDFFloorPlan processes a PDF floor plan to extract building information
func processPDFFloorPlan(buildingID, pdfPath string) error {
	fmt.Printf("Processing PDF floor plan: %s\n", pdfPath)

	// Check if PDF file exists
	if _, err := os.Stat(pdfPath); os.IsNotExist(err) {
		return fmt.Errorf("PDF file not found: %s", pdfPath)
	}

	// Create PDF processing directory
	pdfDir := filepath.Join(buildingID, ".arxos", "processing", "pdf")
	if err := os.MkdirAll(pdfDir, 0755); err != nil {
		return fmt.Errorf("failed to create PDF processing directory: %w", err)
	}

	// Copy PDF to processing directory
	destPath := filepath.Join(pdfDir, "floor_plan.pdf")
	if err := copyFile(pdfPath, destPath); err != nil {
		return fmt.Errorf("failed to copy PDF file: %w", err)
	}

	// Extract PDF page count
	pageCount, err := extractPDFPageCount(pdfPath)
	if err != nil {
		fmt.Printf("Warning: Could not extract PDF page count: %v\n", err)
		pageCount = 0
	}

	// Create PDF metadata
	pdfMetadata := &PDFMetadata{
		SourceFile:    pdfPath,
		ProcessedAt:   time.Now(),
		Status:        "uploaded",
		PageCount:     pageCount,
		BuildingID:    buildingID,
		ProcessingLog: []string{"PDF uploaded successfully"},
	}

	// Save PDF metadata
	metadataPath := filepath.Join(pdfDir, "metadata.json")
	if err := writeJSON(metadataPath, pdfMetadata); err != nil {
		return fmt.Errorf("failed to save PDF metadata: %w", err)
	}

	fmt.Printf("✅ PDF floor plan processed and stored\n")
	return nil
}

// processIFCFile processes an IFC file to extract building information
func processIFCFile(buildingID, ifcPath string) error {
	fmt.Printf("Processing IFC file: %s\n", ifcPath)

	// Check if IFC file exists
	if _, err := os.Stat(ifcPath); os.IsNotExist(err) {
		return fmt.Errorf("IFC file not found: %s", ifcPath)
	}

	// Create IFC processing directory
	ifcDir := filepath.Join(buildingID, ".arxos", "processing", "ifc")
	if err := os.MkdirAll(ifcDir, 0755); err != nil {
		return fmt.Errorf("failed to create IFC processing directory: %w", err)
	}

	// Copy IFC to processing directory
	destPath := filepath.Join(ifcDir, "building_model.ifc")
	if err := copyFile(ifcPath, destPath); err != nil {
		return fmt.Errorf("failed to copy IFC file: %w", err)
	}

	// Create IFC metadata
	ifcMetadata := &IFCMetadata{
		SourceFile:    ifcPath,
		ProcessedAt:   time.Now(),
		Status:        "uploaded",
		BuildingID:    buildingID,
		ProcessingLog: []string{"IFC file uploaded successfully"},
	}

	// Save IFC metadata
	metadataPath := filepath.Join(ifcDir, "metadata.json")
	if err := writeJSON(metadataPath, ifcMetadata); err != nil {
		return fmt.Errorf("failed to save IFC metadata: %w", err)
	}

	fmt.Printf("✅ IFC file processed and stored\n")
	return nil
}

// applyBuildingTemplate applies a predefined building template
func applyBuildingTemplate(buildingID, templateName string) error {
	fmt.Printf("Applying building template: %s\n", templateName)

	// Create template directory
	templateDir := filepath.Join(buildingID, ".arxos", "templates")
	if err := os.MkdirAll(templateDir, 0755); err != nil {
		return fmt.Errorf("failed to create template directory: %w", err)
	}

	// Load template configuration
	template, err := loadBuildingTemplate(templateName)
	if err != nil {
		return fmt.Errorf("failed to load template %s: %w", templateName, err)
	}

	// Apply template to building
	if err := applyTemplateToBuilding(buildingID, template); err != nil {
		return fmt.Errorf("failed to apply template: %w", err)
	}

	// Save template metadata
	templateMetadata := &TemplateMetadata{
		TemplateName:  templateName,
		AppliedAt:     time.Now(),
		BuildingID:    buildingID,
		TemplateData:  template,
		ProcessingLog: []string{"Template applied successfully"},
	}

	metadataPath := filepath.Join(templateDir, "applied_template.json")
	if err := writeJSON(metadataPath, templateMetadata); err != nil {
		return fmt.Errorf("failed to save template metadata: %w", err)
	}

	fmt.Printf("✅ Building template applied successfully\n")
	return nil
}

// PDFMetadata represents metadata about a processed PDF
type PDFMetadata struct {
	SourceFile    string    `json:"source_file"`
	ProcessedAt   time.Time `json:"processed_at"`
	Status        string    `json:"status"`
	PageCount     int       `json:"page_count"`
	BuildingID    string    `json:"building_id"`
	ProcessingLog []string  `json:"processing_log"`
}

// IFCMetadata represents metadata about a processed IFC file
type IFCMetadata struct {
	SourceFile    string    `json:"source_file"`
	ProcessedAt   time.Time `json:"processed_at"`
	Status        string    `json:"status"`
	BuildingID    string    `json:"building_id"`
	ProcessingLog []string  `json:"processing_log"`
}

// TemplateMetadata represents metadata about an applied template
type TemplateMetadata struct {
	TemplateName  string                 `json:"template_name"`
	AppliedAt     time.Time              `json:"applied_at"`
	BuildingID    string                 `json:"building_id"`
	TemplateData  map[string]interface{} `json:"template_data"`
	ProcessingLog []string               `json:"processing_log"`
}

// copyFile copies a file from source to destination
func copyFile(src, dst string) error {
	sourceFile, err := os.Open(src)
	if err != nil {
		return fmt.Errorf("failed to open source file: %w", err)
	}
	defer sourceFile.Close()

	destFile, err := os.Create(dst)
	if err != nil {
		return fmt.Errorf("failed to create destination file: %w", err)
	}
	defer destFile.Close()

	// Copy file contents
	if _, err := destFile.ReadFrom(sourceFile); err != nil {
		return fmt.Errorf("failed to copy file contents: %w", err)
	}

	return nil
}

// loadBuildingTemplate loads a predefined building template
func loadBuildingTemplate(templateName string) (map[string]interface{}, error) {
	// Create template manager
	templatesDir := ".arxos/templates"
	tm := NewTemplateManager(templatesDir)

	// Load all templates
	if err := tm.LoadTemplates(); err != nil {
		return nil, fmt.Errorf("failed to load templates: %w", err)
	}

	// Get the requested template
	template, err := tm.GetTemplate(templateName)
	if err != nil {
		return nil, fmt.Errorf("template %s not found: %w", templateName, err)
	}

	// Convert template to map for compatibility
	templateMap := map[string]interface{}{
		"name":           template.Name,
		"description":    template.Description,
		"version":        template.Version,
		"category":       template.Category,
		"building_type":  template.BuildingType,
		"default_floors": template.DefaultFloors,
		"default_area":   template.DefaultArea,
		"systems":        template.Systems,
		"zones":          template.Zones,
		"materials":      template.Materials,
		"standards":      template.Standards,
		"tags":           template.Tags,
	}

	return templateMap, nil
}

// applyTemplateToBuilding applies template configuration to the building
func applyTemplateToBuilding(buildingID string, template map[string]interface{}) error {
	basePath := getBuildingPath(buildingID)

	fmt.Printf("Applying template %s to building %s\n", template["name"], buildingID)

	// Update main building configuration
	mainConfigPath := filepath.Join(basePath, "arxos.yml")
	mainConfig := &BuildingConfig{}

	// Read existing config if it exists
	if _, err := os.Stat(mainConfigPath); err == nil {
		configData, err := os.ReadFile(mainConfigPath)
		if err == nil {
			if err := yaml.Unmarshal(configData, mainConfig); err != nil {
				return fmt.Errorf("failed to parse existing config: %w", err)
			}
		}
	}

	// Apply template overrides
	if template["building_type"] != nil {
		mainConfig.Type = template["building_type"].(string)
	}
	if template["default_floors"] != nil {
		mainConfig.Floors = template["default_floors"].(int)
	}
	if template["default_area"] != nil {
		mainConfig.Area = template["default_area"].(string)
	}

	// Apply template systems
	if template["systems"] != nil {
		if systems, ok := template["systems"].(map[string]interface{}); ok {
			for systemName, systemData := range systems {
				if systemConfig, ok := systemData.(map[string]interface{}); ok {
					mainConfig.Systems[systemName] = SystemConfig{
						Type:   systemName,
						Status: "inactive",
						Config: systemConfig,
					}
				}
			}
		}
	}

	// Write updated configuration
	if err := writeYAML(mainConfigPath, mainConfig); err != nil {
		return fmt.Errorf("failed to write updated config: %w", err)
	}

	// Create template-specific directories and files
	if err := createTemplateDirectories(buildingID, template); err != nil {
		return fmt.Errorf("failed to create template directories: %w", err)
	}

	// Apply template zones if specified
	if template["zones"] != nil {
		if err := applyTemplateZones(buildingID, template["zones"]); err != nil {
			return fmt.Errorf("failed to apply template zones: %w", err)
		}
	}

	// Apply template materials if specified
	if template["materials"] != nil {
		if err := applyTemplateMaterials(buildingID, template["materials"]); err != nil {
			return fmt.Errorf("failed to apply template materials: %w", err)
		}
	}

	// Apply template standards if specified
	if template["standards"] != nil {
		if err := applyTemplateStandards(buildingID, template["standards"]); err != nil {
			return fmt.Errorf("failed to apply template standards: %w", err)
		}
	}

	fmt.Printf("✅ Template applied successfully\n")
	return nil
}

// createTemplateDirectories creates template-specific directory structure
func createTemplateDirectories(buildingID string, template map[string]interface{}) error {
	basePath := getBuildingPath(buildingID)

	// Create template-specific directories
	templateDirs := []string{
		"templates",
		"standards",
		"materials",
		"zones",
	}

	for _, dir := range templateDirs {
		dirPath := filepath.Join(basePath, ".arxos", dir)
		if err := os.MkdirAll(dirPath, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	return nil
}

// applyTemplateZones applies template zone configurations
func applyTemplateZones(buildingID string, zones interface{}) error {
	basePath := getBuildingPath(buildingID)
	zonesPath := filepath.Join(basePath, ".arxos", "zones")

	if zoneMap, ok := zones.(map[string]interface{}); ok {
		for zoneName, zoneData := range zoneMap {
			zonePath := filepath.Join(zonesPath, fmt.Sprintf("%s.json", zoneName))
			if err := writeJSON(zonePath, zoneData); err != nil {
				return fmt.Errorf("failed to write zone %s: %w", zoneName, err)
			}
		}
	}

	return nil
}

// applyTemplateMaterials applies template material configurations
func applyTemplateMaterials(buildingID string, materials interface{}) error {
	basePath := getBuildingPath(buildingID)
	materialsPath := filepath.Join(basePath, ".arxos", "materials")

	if materialMap, ok := materials.(map[string]interface{}); ok {
		for materialName, materialData := range materialMap {
			materialPath := filepath.Join(materialsPath, fmt.Sprintf("%s.json", materialName))
			if err := writeJSON(materialPath, materialData); err != nil {
				return fmt.Errorf("failed to write material %s: %w", materialName, err)
			}
		}
	}

	return nil
}

// applyTemplateStandards applies template standard configurations
func applyTemplateStandards(buildingID string, standards interface{}) error {
	basePath := getBuildingPath(buildingID)
	standardsPath := filepath.Join(basePath, ".arxos", "standards")

	if standardMap, ok := standards.(map[string]interface{}); ok {
		for standardName, standardData := range standardMap {
			standardPath := filepath.Join(standardsPath, fmt.Sprintf("%s.json", standardName))
			if err := writeJSON(standardPath, standardData); err != nil {
				return fmt.Errorf("failed to write standard %s: %w", standardName, err)
			}
		}
	}

	return nil
}

// writeJSON writes data as JSON to a file
func writeJSON(filepath string, data interface{}) error {
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	if err := os.WriteFile(filepath, jsonData, 0644); err != nil {
		return fmt.Errorf("failed to write JSON file: %w", err)
	}

	return nil
}

// validateBuildingStructure verifies the created building structure
func validateBuildingStructure(buildingID string) error {
	basePath := getBuildingPath(buildingID)

	// Check that essential directories exist
	essentialDirs := []string{
		".arxos",
		".arxos/config",
		".arxos/objects",
		".arxos/vcs",
		"systems",
		"schemas",
	}

	for _, dir := range essentialDirs {
		dirPath := filepath.Join(basePath, dir)
		if _, err := os.Stat(dirPath); os.IsNotExist(err) {
			return fmt.Errorf("essential directory missing: %s", dir)
		}
	}

	// Check that main configuration file exists
	mainConfigPath := filepath.Join(basePath, "arxos.yml")
	if _, err := os.Stat(mainConfigPath); os.IsNotExist(err) {
		return fmt.Errorf("main configuration file missing: arxos.yml")
	}

	return nil
}

// printSuccessMessage provides user feedback after successful initialization
func printSuccessMessage(buildingID string) {
	fmt.Printf("\n✅ Building %s initialized successfully!\n", buildingID)
	fmt.Printf("📁 Navigate to building: arx cd %s\n", buildingID)
	fmt.Printf("📋 View structure: arx ls --tree\n")
	fmt.Printf("🔧 Check status: arx status\n")
	fmt.Printf("📝 Make first commit: arx commit -m \"Initial building structure\"\n\n")
}

// isValidAreaFormat validates area format using regex patterns
func isValidAreaFormat(area string) bool {
	if area == "" {
		return false
	}

	// Comprehensive regex patterns for area validation
	patterns := []string{
		// Metric patterns
		`^\d{1,3}(?:,\d{3})*\s*(?:sq\s*)?m(?:eters?)?(?:²|2)?$`,  // 5,000 sq m, 5000m²
		`^\d{1,3}(?:,\d{3})*\s*(?:sq\s*)?km(?:eters?)?(?:²|2)?$`, // 1.5 sq km, 1.5km²
		`^\d{1,3}(?:,\d{3})*\s*(?:sq\s*)?cm(?:eters?)?(?:²|2)?$`, // 10,000 sq cm

		// Imperial patterns
		`^\d{1,3}(?:,\d{3})*\s*(?:sq\s*)?ft(?:eet)?(?:²|2)?$`,   // 25,000 sq ft, 25000ft²
		`^\d{1,3}(?:,\d{3})*\s*(?:sq\s*)?yd(?:ards?)?(?:²|2)?$`, // 5,000 sq yd
		`^\d{1,3}(?:,\d{3})*\s*(?:sq\s*)?in(?:ches?)?(?:²|2)?$`, // 144 sq in
		`^\d{1,3}(?:,\d{3})*\s*(?:sq\s*)?mi(?:les?)?(?:²|2)?$`,  // 1.5 sq mi

		// Decimal patterns
		`^\d+\.\d+\s*(?:sq\s*)?(?:m|km|cm|ft|yd|in|mi)(?:²|2)?$`, // 1.5 sq m, 2.25 ft²

		// Simple patterns (fallback)
		`^\d{1,3}(?:,\d{3})*\s*(?:m2|ft2|km2|cm2|yd2|in2|mi2)$`, // 5000m2, 25000ft2
	}

	area = strings.TrimSpace(area)
	areaLower := strings.ToLower(area)

	for _, pattern := range patterns {
		matched, err := regexp.MatchString(pattern, areaLower)
		if err == nil && matched {
			return true
		}
	}

	return false
}

// writeYAML writes data to a YAML file
func writeYAML(path string, data interface{}) error {
	// Marshal data to YAML
	yamlData, err := yaml.Marshal(data)
	if err != nil {
		return fmt.Errorf("failed to marshal YAML: %w", err)
	}

	// Write to file
	if err := os.WriteFile(path, yamlData, 0644); err != nil {
		return fmt.Errorf("failed to write YAML file %s: %w", path, err)
	}

	return nil
}

// extractPDFPageCount extracts the number of pages from a PDF file
func extractPDFPageCount(pdfPath string) (int, error) {
	// Open the PDF file
	file, err := os.Open(pdfPath)
	if err != nil {
		return 0, fmt.Errorf("failed to open PDF file: %w", err)
	}
	defer file.Close()

	// Read the first 1024 bytes to check PDF header
	buffer := make([]byte, 1024)
	_, err = file.Read(buffer)
	if err != nil {
		return 0, fmt.Errorf("failed to read PDF header: %w", err)
	}

	// Check if it's a valid PDF file
	if !strings.HasPrefix(string(buffer), "%PDF") {
		return 0, fmt.Errorf("not a valid PDF file")
	}

	// Reset file position
	if _, err := file.Seek(0, 0); err != nil {
		return 0, fmt.Errorf("failed to reset file position: %w", err)
	}

	// Read the entire file to find page count
	content, err := os.ReadFile(pdfPath)
	if err != nil {
		return 0, fmt.Errorf("failed to read PDF file: %w", err)
	}

	// Count pages by looking for page objects
	// This is a simple heuristic that counts "/Page" entries
	pageCount := strings.Count(string(content), "/Page")

	// PDFs typically have one /Page entry per page, but this is approximate
	// For more accurate counting, we'd need a full PDF parser library
	if pageCount > 0 {
		return pageCount, nil
	}

	// Fallback: try to find page count in trailer
	if strings.Contains(string(content), "/Count") {
		// Look for /Count followed by a number
		re := regexp.MustCompile(`/Count\s+(\d+)`)
		matches := re.FindStringSubmatch(string(content))
		if len(matches) > 1 {
			if count, err := strconv.Atoi(matches[1]); err == nil {
				return count, nil
			}
		}
	}

	// If we can't determine page count, return 1 as default
	return 1, nil
}

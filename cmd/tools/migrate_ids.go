package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/arxos/arxos/cmd/models"
)

// MigrationReport tracks migration statistics
type MigrationReport struct {
	StartTime       time.Time
	EndTime         time.Time
	TotalObjects    int
	SuccessCount    int
	FailureCount    int
	SkippedCount    int
	Mappings        map[string]string // old ID -> new ID
	Errors          []string
	BackupDirectory string
}

// IDMigrator handles the migration from colon-based to underscore-based IDs
type IDMigrator struct {
	buildingRoot string
	objectsDir   string
	backupDir    string
	dryRun       bool
	report       *MigrationReport
	idMapping    map[string]string // Track all ID transformations
}

// NewIDMigrator creates a new migrator
func NewIDMigrator(buildingRoot string, dryRun bool) *IDMigrator {
	timestamp := time.Now().Format("20060102_150405")
	return &IDMigrator{
		buildingRoot: buildingRoot,
		objectsDir:   filepath.Join(buildingRoot, ".arxos", "objects"),
		backupDir:    filepath.Join(buildingRoot, ".arxos", "backups", "migration_"+timestamp),
		dryRun:       dryRun,
		report: &MigrationReport{
			StartTime:    time.Now(),
			Mappings:     make(map[string]string),
			Errors:       []string{},
		},
		idMapping: make(map[string]string),
	}
}

// Run executes the migration
func (m *IDMigrator) Run() error {
	fmt.Println("=== ArxObject ID Migration Tool ===")
	if m.dryRun {
		fmt.Println("MODE: DRY RUN - No changes will be made")
	} else {
		fmt.Println("MODE: LIVE - Changes will be applied")
	}
	fmt.Printf("Building: %s\n", m.buildingRoot)
	fmt.Printf("Objects: %s\n\n", m.objectsDir)

	// Step 1: Create backup
	if !m.dryRun {
		if err := m.createBackup(); err != nil {
			return fmt.Errorf("backup failed: %w", err)
		}
		fmt.Printf("✅ Backup created: %s\n\n", m.backupDir)
	}

	// Step 2: Scan and analyze all objects
	fmt.Println("Scanning objects...")
	objects, err := m.scanObjects()
	if err != nil {
		return fmt.Errorf("scan failed: %w", err)
	}
	fmt.Printf("Found %d objects\n\n", len(objects))

	// Step 3: Generate new IDs and mappings
	fmt.Println("Generating new IDs...")
	m.generateMappings(objects)
	
	// Step 4: Update all objects with new IDs and references
	fmt.Println("\nMigrating objects...")
	for oldPath, obj := range objects {
		if err := m.migrateObject(oldPath, obj); err != nil {
			m.report.Errors = append(m.report.Errors, fmt.Sprintf("%s: %v", oldPath, err))
			m.report.FailureCount++
			fmt.Printf("❌ Failed: %s\n", filepath.Base(oldPath))
		} else {
			m.report.SuccessCount++
			fmt.Printf("✅ Migrated: %s → %s\n", obj["id"], m.idMapping[obj["id"].(string)])
		}
	}

	// Step 5: Generate report
	m.report.EndTime = time.Now()
	m.report.TotalObjects = len(objects)
	m.generateReport()

	return nil
}

// createBackup creates a backup of all object files
func (m *IDMigrator) createBackup() error {
	if err := os.MkdirAll(m.backupDir, 0755); err != nil {
		return err
	}

	return filepath.Walk(m.objectsDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() {
			return nil
		}

		// Calculate relative path and create backup
		relPath, _ := filepath.Rel(m.objectsDir, path)
		backupPath := filepath.Join(m.backupDir, relPath)
		
		// Create directory structure
		os.MkdirAll(filepath.Dir(backupPath), 0755)
		
		// Copy file
		data, err := ioutil.ReadFile(path)
		if err != nil {
			return err
		}
		
		return ioutil.WriteFile(backupPath, data, 0644)
	})
}

// scanObjects loads all JSON objects
func (m *IDMigrator) scanObjects() (map[string]map[string]interface{}, error) {
	objects := make(map[string]map[string]interface{})

	err := filepath.Walk(m.objectsDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() || !strings.HasSuffix(path, ".json") {
			return nil
		}

		// Skip index and consolidated files
		base := filepath.Base(path)
		if base == "index.json" || base == "building.json" ||
			strings.HasPrefix(base, "floor_") || strings.HasPrefix(base, "system_") {
			m.report.SkippedCount++
			return nil
		}

		// Load object
		data, err := ioutil.ReadFile(path)
		if err != nil {
			return err
		}

		var obj map[string]interface{}
		if err := json.Unmarshal(data, &obj); err != nil {
			return err
		}

		objects[path] = obj
		return nil
	})

	return objects, err
}

// generateMappings creates the ID transformation map
func (m *IDMigrator) generateMappings(objects map[string]map[string]interface{}) {
	for _, obj := range objects {
		if oldID, ok := obj["id"].(string); ok {
			newID := m.transformID(oldID)
			m.idMapping[oldID] = newID
			m.report.Mappings[oldID] = newID
		}
	}
}

// transformID converts from colon to underscore format
func (m *IDMigrator) transformID(oldID string) string {
	// Handle the building prefix specially
	if strings.HasPrefix(oldID, "building:") {
		oldID = strings.TrimPrefix(oldID, "building:")
	}

	// Split by colons
	parts := strings.Split(oldID, ":")
	newParts := []string{}

	for i, part := range parts {
		// Transform specific patterns
		switch {
		case part == "hq":
			// Building ID stays the same
			newParts = append(newParts, part)
		
		case part == "floor" && i+1 < len(parts):
			// floor:1 becomes f1
			if num := parts[i+1]; num != "" {
				newParts = append(newParts, "f"+num)
				i++ // Skip the number part
			}
		
		case strings.HasPrefix(part, "room"):
			// room:101 or just room identifier
			if part == "room" && i+1 < len(parts) {
				newParts = append(newParts, "room", parts[i+1])
			} else if strings.HasPrefix(part, "room") {
				// Handle room101 format
				newParts = append(newParts, "room", strings.TrimPrefix(part, "room"))
			}
		
		case part == "system":
			// system:hvac becomes systems/hvac
			if i+1 < len(parts) {
				newParts = append(newParts, "systems", parts[i+1])
			}
		
		case part == "equipment" || part == "sensor":
			// These stay as-is
			newParts = append(newParts, part)
		
		case strings.Contains(part, "-"):
			// Component IDs like temp-1-1 stay the same but with underscores
			newParts = append(newParts, strings.ReplaceAll(part, "-", "_"))
		
		default:
			// Default transformation
			newParts = append(newParts, strings.ReplaceAll(part, "-", "_"))
		}
	}

	return strings.Join(newParts, "/")
}

// migrateObject updates an object with new IDs
func (m *IDMigrator) migrateObject(oldPath string, obj map[string]interface{}) error {
	// Update main ID
	if oldID, ok := obj["id"].(string); ok {
		obj["id"] = m.idMapping[oldID]
	}

	// Update parent reference
	if parent, ok := obj["parent"].(string); ok && parent != "" {
		if newParent, exists := m.idMapping[parent]; exists {
			obj["parent"] = newParent
		}
	}

	// Update children references
	if children, ok := obj["children"].([]interface{}); ok {
		for i, child := range children {
			if childID, ok := child.(string); ok {
				if newChild, exists := m.idMapping[childID]; exists {
					children[i] = newChild
				}
			}
		}
	}

	// Update spatial_location
	if spatial, ok := obj["spatial_location"].(string); ok && spatial != "" {
		if newSpatial, exists := m.idMapping[spatial]; exists {
			obj["spatial_location"] = newSpatial
		} else {
			// Transform even if not in our object set
			obj["spatial_location"] = m.transformID(spatial)
		}
	}

	// Update relationships
	if relationships, ok := obj["relationships"].(map[string]interface{}); ok {
		for relType, relValue := range relationships {
			if relList, ok := relValue.([]interface{}); ok {
				for i, relID := range relList {
					if relIDStr, ok := relID.(string); ok {
						if newRelID, exists := m.idMapping[relIDStr]; exists {
							relList[i] = newRelID
						} else {
							// Transform even if not in our object set
							relList[i] = m.transformID(relIDStr)
						}
					}
				}
			}
		}
	}

	// Add migration metadata
	if metadata, ok := obj["metadata"].(map[string]interface{}); !ok {
		obj["metadata"] = make(map[string]interface{})
	}
	obj["metadata"].(map[string]interface{})["migrated_at"] = time.Now().Format(time.RFC3339)
	obj["metadata"].(map[string]interface{})["migration_version"] = "v2.0"
	obj["metadata"].(map[string]interface{})["old_id"] = obj["id"]

	if m.dryRun {
		return nil // Don't write in dry run
	}

	// Write updated object
	newPath := m.getNewPath(oldPath, obj["id"].(string))
	
	// Create directory if needed
	os.MkdirAll(filepath.Dir(newPath), 0755)
	
	// Write JSON
	data, err := json.MarshalIndent(obj, "", "  ")
	if err != nil {
		return err
	}

	if err := ioutil.WriteFile(newPath, data, 0644); err != nil {
		return err
	}

	// Remove old file if path changed
	if newPath != oldPath {
		os.Remove(oldPath)
	}

	return nil
}

// getNewPath generates the new file path for an object
func (m *IDMigrator) getNewPath(oldPath string, newID string) string {
	// Replace slashes with double underscores for flat storage
	filename := strings.ReplaceAll(newID, "/", "__") + ".json"
	return filepath.Join(m.objectsDir, filename)
}

// generateReport creates a migration report
func (m *IDMigrator) generateReport() {
	duration := m.report.EndTime.Sub(m.report.StartTime)

	fmt.Println("\n=== Migration Report ===")
	fmt.Printf("Duration: %v\n", duration)
	fmt.Printf("Total Objects: %d\n", m.report.TotalObjects)
	fmt.Printf("✅ Success: %d\n", m.report.SuccessCount)
	fmt.Printf("❌ Failed: %d\n", m.report.FailureCount)
	fmt.Printf("⏭️  Skipped: %d\n", m.report.SkippedCount)

	if len(m.report.Errors) > 0 {
		fmt.Println("\nErrors:")
		for _, err := range m.report.Errors {
			fmt.Printf("  - %s\n", err)
		}
	}

	// Save report to file
	if !m.dryRun {
		reportPath := filepath.Join(m.backupDir, "migration_report.json")
		reportData, _ := json.MarshalIndent(m.report, "", "  ")
		ioutil.WriteFile(reportPath, reportData, 0644)
		fmt.Printf("\nReport saved: %s\n", reportPath)
	}

	// Show sample mappings
	fmt.Println("\nSample ID Mappings:")
	count := 0
	for old, new := range m.report.Mappings {
		fmt.Printf("  %s\n  → %s\n\n", old, new)
		count++
		if count >= 5 {
			break
		}
	}
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: migrate_ids <building_path> [--dry-run]")
		os.Exit(1)
	}

	buildingPath := os.Args[1]
	dryRun := false
	
	if len(os.Args) > 2 && os.Args[2] == "--dry-run" {
		dryRun = true
	}

	migrator := NewIDMigrator(buildingPath, dryRun)
	if err := migrator.Run(); err != nil {
		fmt.Printf("Migration failed: %v\n", err)
		os.Exit(1)
	}
}
package database

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"path/filepath"
	"strings"

	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// JSONMigrator handles migration from JSON files to SQLite database
type JSONMigrator struct {
	db       DB
	stateDir string
}

// NewJSONMigrator creates a new JSON to SQLite migrator
func NewJSONMigrator(db DB, stateDir string) *JSONMigrator {
	return &JSONMigrator{
		db:       db,
		stateDir: stateDir,
	}
}

// MigrateAll migrates all JSON files in the state directory to SQLite
func (m *JSONMigrator) MigrateAll(ctx context.Context) error {
	files, err := ioutil.ReadDir(m.stateDir)
	if err != nil {
		return fmt.Errorf("failed to read state directory: %w", err)
	}
	
	successCount := 0
	failCount := 0
	
	for _, file := range files {
		if file.IsDir() || !strings.HasSuffix(file.Name(), ".json") {
			continue
		}
		
		logger.Info("Migrating %s to database", file.Name())
		
		if err := m.MigrateFile(ctx, filepath.Join(m.stateDir, file.Name())); err != nil {
			logger.Error("Failed to migrate %s: %v", file.Name(), err)
			failCount++
		} else {
			successCount++
		}
	}
	
	logger.Info("Migration complete: %d succeeded, %d failed", successCount, failCount)
	
	if failCount > 0 {
		return fmt.Errorf("migration completed with %d failures", failCount)
	}
	
	return nil
}

// MigrateFile migrates a single JSON file to SQLite
func (m *JSONMigrator) MigrateFile(ctx context.Context, jsonPath string) error {
	// Read JSON file
	data, err := ioutil.ReadFile(jsonPath)
	if err != nil {
		return fmt.Errorf("failed to read JSON file: %w", err)
	}
	
	// Parse JSON
	var plan models.FloorPlan
	if err := json.Unmarshal(data, &plan); err != nil {
		return fmt.Errorf("failed to parse JSON: %w", err)
	}
	
	// Check if floor plan already exists
	existingPlan, err := m.db.GetFloorPlan(ctx, plan.Name)
	if err != nil && err != ErrNotFound {
		return fmt.Errorf("failed to check existing floor plan: %w", err)
	}
	
	if existingPlan != nil {
		logger.Debug("Floor plan %s already exists in database, updating", plan.Name)
		return m.db.UpdateFloorPlan(ctx, &plan)
	}
	
	// Save to database
	if err := m.db.SaveFloorPlan(ctx, &plan); err != nil {
		return fmt.Errorf("failed to save floor plan to database: %w", err)
	}
	
	logger.Info("Successfully migrated floor plan: %s", plan.Name)
	return nil
}

// ExportToJSON exports a floor plan from database back to JSON
func (m *JSONMigrator) ExportToJSON(ctx context.Context, floorPlanID string, outputPath string) error {
	// Get floor plan from database
	plan, err := m.db.GetFloorPlan(ctx, floorPlanID)
	if err != nil {
		return fmt.Errorf("failed to get floor plan: %w", err)
	}
	
	// Convert to JSON
	data, err := json.MarshalIndent(plan, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}
	
	// Write to file
	if err := ioutil.WriteFile(outputPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write JSON file: %w", err)
	}
	
	logger.Info("Exported floor plan %s to %s", floorPlanID, outputPath)
	return nil
}

// SyncJSONToDatabase ensures JSON files and database are in sync
func (m *JSONMigrator) SyncJSONToDatabase(ctx context.Context) error {
	// Get all JSON files
	files, err := ioutil.ReadDir(m.stateDir)
	if err != nil {
		return fmt.Errorf("failed to read state directory: %w", err)
	}
	
	jsonPlans := make(map[string]*models.FloorPlan)
	
	// Load all JSON files
	for _, file := range files {
		if file.IsDir() || !strings.HasSuffix(file.Name(), ".json") {
			continue
		}
		
		data, err := ioutil.ReadFile(filepath.Join(m.stateDir, file.Name()))
		if err != nil {
			logger.Error("Failed to read %s: %v", file.Name(), err)
			continue
		}
		
		var plan models.FloorPlan
		if err := json.Unmarshal(data, &plan); err != nil {
			logger.Error("Failed to parse %s: %v", file.Name(), err)
			continue
		}
		
		jsonPlans[plan.Name] = &plan
	}
	
	// Get all database plans
	dbPlans, err := m.db.GetAllFloorPlans(ctx)
	if err != nil {
		return fmt.Errorf("failed to get database plans: %w", err)
	}
	
	// Create a map for easy lookup
	dbPlanMap := make(map[string]*models.FloorPlan)
	for _, plan := range dbPlans {
		dbPlanMap[plan.Name] = plan
	}
	
	// Sync JSON to database
	for name, jsonPlan := range jsonPlans {
		dbPlan, exists := dbPlanMap[name]
		
		if !exists {
			// Plan exists in JSON but not in database
			logger.Info("Adding floor plan %s to database", name)
			if err := m.db.SaveFloorPlan(ctx, jsonPlan); err != nil {
				logger.Error("Failed to save %s: %v", name, err)
			}
		} else if jsonPlan.UpdatedAt != nil && dbPlan.UpdatedAt != nil && jsonPlan.UpdatedAt.After(*dbPlan.UpdatedAt) {
			// JSON is newer than database
			logger.Info("Updating floor plan %s in database", name)
			if err := m.db.UpdateFloorPlan(ctx, jsonPlan); err != nil {
				logger.Error("Failed to update %s: %v", name, err)
			}
		}
	}
	
	// Export database plans that don't exist in JSON
	for name := range dbPlanMap {
		if _, exists := jsonPlans[name]; !exists {
			logger.Info("Exporting floor plan %s to JSON", name)
			outputPath := filepath.Join(m.stateDir, name+".json")
			if err := m.ExportToJSON(ctx, name, outputPath); err != nil {
				logger.Error("Failed to export %s: %v", name, err)
			}
		}
	}
	
	return nil
}
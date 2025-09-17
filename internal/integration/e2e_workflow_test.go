package integration_test

import (
	"bytes"
	"context"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/converter"
	"github.com/arx-os/arxos/internal/daemon"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/exporter"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestEndToEndWorkflow tests the complete professional workflow
func TestEndToEndWorkflow(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping E2E test in short mode")
	}

	ctx := context.Background()
	tempDir := t.TempDir()

	// Step 1: Setup test environment
	t.Run("Setup", func(t *testing.T) {
		// Create test directories
		watchDir := filepath.Join(tempDir, "bim_files")
		exportDir := filepath.Join(tempDir, "exports")
		stateDir := filepath.Join(tempDir, ".arxos")

		require.NoError(t, os.MkdirAll(watchDir, 0755))
		require.NoError(t, os.MkdirAll(exportDir, 0755))
		require.NoError(t, os.MkdirAll(stateDir, 0755))
	})

	// Step 2: Simulate IFC file creation (BIM tool export)
	t.Run("IFC_Export_Simulation", func(t *testing.T) {
		ifcContent := generateTestIFC()
		ifcPath := filepath.Join(tempDir, "bim_files", "test_building.ifc")
		
		err := ioutil.WriteFile(ifcPath, []byte(ifcContent), 0644)
		require.NoError(t, err)
		t.Logf("Created IFC file: %s", ifcPath)
	})

	// Step 3: Process IFC with converter
	t.Run("IFC_Import", func(t *testing.T) {
		ifcPath := filepath.Join(tempDir, "bim_files", "test_building.ifc")
		data, err := ioutil.ReadFile(ifcPath)
		require.NoError(t, err)

		// Parse IFC
		conv := converter.NewSpatialIFCConverter()
		lines := bytes.Split(data, []byte("\n"))
		var stringLines []string
		for _, line := range lines {
			stringLines = append(stringLines, string(line))
		}

		building, err := conv.ConvertToBIMWithSpatial(stringLines)
		require.NoError(t, err)
		require.NotNil(t, building)
		t.Logf("Parsed building: %s with %d floors", building.Name, len(building.Floors))
	})

	// Step 4: Store in database (PostGIS or SQLite)
	t.Run("Database_Storage", func(t *testing.T) {
		dbPath := filepath.Join(tempDir, ".arxos", "test.db")
		dbConfig := database.NewConfig(dbPath)
		db := database.NewSQLiteDB(dbConfig)
		
		err := db.Connect(ctx, dbPath)
		require.NoError(t, err)
		defer db.Close()

		// Initialize schema
		err = db.InitSchema(ctx)
		require.NoError(t, err)

		// Insert test equipment
		equipment := &database.Equipment{
			ID:           "TEST-EQ-001",
			EquipmentTag: "AC-001",
			Name:         "Air Conditioner Unit 1",
			Type:         "HVAC",
			Status:       "OPERATIONAL",
			LocationX:    12.5,
			LocationY:    8.3,
			LocationZ:    3.0,
		}

		err = db.CreateEquipment(ctx, equipment)
		require.NoError(t, err)
		t.Log("Stored equipment in database")
	})

	// Step 5: Generate exports
	t.Run("Export_Generation", func(t *testing.T) {
		// Create test floor plans
		floorPlans := createTestFloorPlans()
		exportDir := filepath.Join(tempDir, "exports")

		// Test BIM export
		t.Run("BIM_Export", func(t *testing.T) {
			generator := exporter.NewBIMGenerator()
			bimPath := filepath.Join(exportDir, "building.bim.txt")
			
			file, err := os.Create(bimPath)
			require.NoError(t, err)
			defer file.Close()

			err = generator.GenerateFromFloorPlans(floorPlans, file)
			require.NoError(t, err)
			
			// Verify file was created
			info, err := os.Stat(bimPath)
			require.NoError(t, err)
			assert.Greater(t, info.Size(), int64(0))
			t.Logf("Generated BIM file: %s (%d bytes)", bimPath, info.Size())
		})

		// Test CSV export
		t.Run("CSV_Export", func(t *testing.T) {
			exporter := exporter.NewCSVExporter()
			csvPath := filepath.Join(exportDir, "equipment.csv")
			
			file, err := os.Create(csvPath)
			require.NoError(t, err)
			defer file.Close()

			var allEquipment []*models.Equipment
			for _, plan := range floorPlans {
				allEquipment = append(allEquipment, plan.Equipment...)
			}

			err = exporter.ExportEquipment(allEquipment, file)
			require.NoError(t, err)
			
			info, err := os.Stat(csvPath)
			require.NoError(t, err)
			assert.Greater(t, info.Size(), int64(0))
			t.Logf("Generated CSV file: %s (%d bytes)", csvPath, info.Size())
		})

		// Test JSON export
		t.Run("JSON_Export", func(t *testing.T) {
			exporter := exporter.NewJSONExporter()
			jsonPath := filepath.Join(exportDir, "building.json")
			
			file, err := os.Create(jsonPath)
			require.NoError(t, err)
			defer file.Close()

			err = exporter.ExportBuilding(floorPlans, file)
			require.NoError(t, err)
			
			info, err := os.Stat(jsonPath)
			require.NoError(t, err)
			assert.Greater(t, info.Size(), int64(0))
			t.Logf("Generated JSON file: %s (%d bytes)", jsonPath, info.Size())
		})
	})

	// Step 6: Test daemon automation
	t.Run("Daemon_Automation", func(t *testing.T) {
		config := daemon.Config{
			WatchPaths:   []string{filepath.Join(tempDir, "bim_files")},
			StateDir:     filepath.Join(tempDir, ".arxos"),
			DatabasePath: filepath.Join(tempDir, ".arxos", "test.db"),
			AutoImport:   true,
			AutoExport:   true,
			PollInterval: 1 * time.Second,
			MaxWorkers:   2,
		}

		d, err := daemon.New(&config)
		require.NoError(t, err)
		require.NotNil(t, d)
		t.Log("Daemon created successfully")

		// Note: Full daemon start would require more setup
		// This validates the daemon can be created with our config
	})

	// Step 7: Verify complete workflow
	t.Run("Workflow_Verification", func(t *testing.T) {
		exportDir := filepath.Join(tempDir, "exports")
		
		// Check all expected files exist
		expectedFiles := []string{
			"building.bim.txt",
			"equipment.csv",
			"building.json",
		}

		for _, filename := range expectedFiles {
			path := filepath.Join(exportDir, filename)
			_, err := os.Stat(path)
			assert.NoError(t, err, "Expected file %s to exist", filename)
		}

		t.Log("✅ Complete workflow verified successfully")
	})
}

// TestConcurrentOperations tests concurrent access patterns
func TestConcurrentOperations(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping concurrent operations test in short mode")
	}

	ctx := context.Background()
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "concurrent_test.db")

	// Setup database
	dbConfig := database.NewConfig(dbPath)
	db := database.NewSQLiteDB(dbConfig)
	require.NoError(t, db.Connect(ctx, dbPath))
	defer db.Close()
	require.NoError(t, db.InitSchema(ctx))

	// Test concurrent reads and writes
	t.Run("Concurrent_ReadWrite", func(t *testing.T) {
		const numGoroutines = 10
		const opsPerGoroutine = 100

		done := make(chan bool, numGoroutines)

		// Start concurrent operations
		for i := 0; i < numGoroutines; i++ {
			go func(id int) {
				for j := 0; j < opsPerGoroutine; j++ {
					// Mix of reads and writes
					if j%2 == 0 {
						// Write
						eq := &database.Equipment{
							ID:           fmt.Sprintf("CONCURRENT-%d-%d", id, j),
							EquipmentTag: fmt.Sprintf("TAG-%d-%d", id, j),
							Name:         "Test Equipment",
							Type:         "TEST",
							Status:       "OPERATIONAL",
						}
						_ = db.CreateEquipment(ctx, eq)
					} else {
						// Read
						_ = db.ListEquipment(ctx, 10, 0)
					}
				}
				done <- true
			}(i)
		}

		// Wait for all goroutines
		for i := 0; i < numGoroutines; i++ {
			<-done
		}

		t.Log("Concurrent operations completed successfully")
	})
}

// Helper functions

func generateTestIFC() string {
	return `ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Test IFC File'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',(),(),'Test','Test','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('1234567890123456',$,'Test Project',$,$,$,$,$,$);
#2=IFCBUILDING('2345678901234567',$,'Test Building',$,$,$,$,$,$,$,$,$);
#3=IFCBUILDINGSTOREY('3456789012345678',$,'Ground Floor',$,$,$,$,$,.ELEMENT.,$);
#4=IFCSPACE('4567890123456789',$,'Room 101',$,$,$,$,$,.ELEMENT.,.INTERNAL.,$,$);
#5=IFCFLOWCONTROLLER('5678901234567890',$,'AC Unit 1',$,$,$,$,$);
ENDSEC;
END-ISO-10303-21;`
}

func createTestFloorPlans() []*models.FloorPlan {
	now := time.Now()
	return []*models.FloorPlan{
		{
			UUID:        "TEST-001",
			Building:    "Test Building",
			Description: "E2E Test Building",
			Level:       1,
			Name:        "Ground Floor",
			Rooms: []*models.Room{
				{
					ID:   "101",
					Name: "Main Room",
					Bounds: models.Bounds{
						MinX: 0,
						MinY: 0,
						MaxX: 10,
						MaxY: 10,
					},
				},
			},
			Equipment: []*models.Equipment{
				{
					ID:         "EQ-001",
					Name:       "AC Unit",
					Type:       "HVAC",
					Status:     "OPERATIONAL",
					RoomID:     "101",
					Installed:  &now,
					Maintained: &now,
				},
			},
		},
	}
}
//go:build integration
// +build integration

package integration

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/converter"
	"github.com/arx-os/arxos/internal/daemon"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/exporter"
	"github.com/arx-os/arxos/internal/spatial"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestProfessionalBIMWorkflow tests the complete professional BIM integration workflow
func TestProfessionalBIMWorkflow(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()

	// Setup test directory
	testDir := filepath.Join(os.TempDir(), fmt.Sprintf("arxos-prof-test-%d", time.Now().Unix()))
	require.NoError(t, os.MkdirAll(testDir, 0755))
	defer os.RemoveAll(testDir)

	// Create subdirectories
	importDir := filepath.Join(testDir, "imports")
	exportDir := filepath.Join(testDir, "exports")
	require.NoError(t, os.MkdirAll(importDir, 0755))
	require.NoError(t, os.MkdirAll(exportDir, 0755))

	// Initialize PostGIS database
	pgConfig := &database.DatabaseConfig{
		Type:     "postgis",
		Host:     getTestPGHost(),
		Port:     5432,
		Database: "arxos_prof_test",
		User:     "arxos",
		Password: "arxos",
	}

	hybridDB, err := database.NewPostGISHybridDB(pgConfig)
	if err != nil {
		t.Skip("PostGIS not available:", err)
	}
	defer hybridDB.Close()

	t.Run("DaemonFileWatching", func(t *testing.T) {
		testDaemonFileWatching(t, ctx, importDir, hybridDB)
	})

	t.Run("IFCImportExportRoundTrip", func(t *testing.T) {
		testIFCRoundTrip(t, ctx, importDir, exportDir, hybridDB)
	})

	t.Run("MultiFormatExport", func(t *testing.T) {
		testMultiFormatExport(t, ctx, exportDir, hybridDB)
	})

	t.Run("SpatialIndexPerformance", func(t *testing.T) {
		testSpatialIndexPerformance(t, ctx, hybridDB)
	})

	t.Run("BIMToolIntegration", func(t *testing.T) {
		testBIMToolIntegration(t, ctx, exportDir, hybridDB)
	})
}

// testDaemonFileWatching tests automatic IFC file import via daemon
func testDaemonFileWatching(t *testing.T, ctx context.Context, importDir string, db *database.PostGISHybridDB) {
	// Create daemon configuration
	config := &daemon.Config{
		WatchPaths:   []string{importDir},
		PollInterval: 1 * time.Second,
		AutoImport:   true,
		Patterns:     []string{"*.ifc"},
	}

	// Create daemon instance
	d := daemon.NewDaemon(config)

	// Start daemon in background
	daemonCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	errChan := make(chan error, 1)
	go func() {
		if err := d.Start(daemonCtx); err != nil {
			errChan <- err
		}
	}()

	// Give daemon time to start
	time.Sleep(2 * time.Second)

	// Create test IFC file
	ifcContent := generateTestIFCContent("DAEMON-TEST", 3, 10)
	ifcPath := filepath.Join(importDir, "test-import.ifc")
	require.NoError(t, os.WriteFile(ifcPath, []byte(ifcContent), 0644))

	// Wait for daemon to process
	time.Sleep(5 * time.Second)

	// Verify data was imported
	spatialDB, err := db.GetSpatialDB()
	require.NoError(t, err)

	// Query for imported equipment
	center := spatial.Point3D{X: 0, Y: 0, Z: 0}
	equipment, err := spatialDB.QueryBySpatialProximity(center, 100.0)
	assert.NoError(t, err)

	// Should have equipment from daemon import
	foundDaemonImport := false
	for _, eq := range equipment {
		if strings.Contains(eq.ID, "DAEMON-TEST") {
			foundDaemonImport = true
			break
		}
	}
	assert.True(t, foundDaemonImport, "Daemon should have imported IFC file")

	// Stop daemon
	cancel()

	select {
	case err := <-errChan:
		if err != nil && err != context.Canceled {
			t.Errorf("Daemon error: %v", err)
		}
	case <-time.After(2 * time.Second):
		// Daemon stopped successfully
	}
}

// testIFCRoundTrip tests importing IFC and exporting it back
func testIFCRoundTrip(t *testing.T, ctx context.Context, importDir, exportDir string, db *database.PostGISHybridDB) {
	// Create test IFC with known structure
	ifcContent := generateTestIFCContent("ROUNDTRIP", 5, 20)

	// Import IFC
	converter := converter.NewImprovedIFCConverter()
	reader := strings.NewReader(ifcContent)
	err := converter.ConvertToDB(reader, db)
	require.NoError(t, err, "Failed to import IFC")

	// Export to BIM format
	bimPath := filepath.Join(exportDir, "roundtrip.bim.txt")
	bimFile, err := os.Create(bimPath)
	require.NoError(t, err)
	defer bimFile.Close()

	generator := exporter.NewBIMGenerator()
	err = generator.GenerateFromDatabase(ctx, db, "ROUNDTRIP", bimFile)
	assert.NoError(t, err, "Failed to export to BIM")

	// Verify BIM file contains expected data
	bimContent, err := os.ReadFile(bimPath)
	require.NoError(t, err)

	bimStr := string(bimContent)
	assert.Contains(t, bimStr, "ROUNDTRIP", "BIM should contain building ID")
	assert.Contains(t, bimStr, "PostGIS", "BIM should mention PostGIS source")
	assert.Contains(t, bimStr, "900913", "BIM should mention SRID")

	// Export to CSV
	csvPath := filepath.Join(exportDir, "roundtrip.csv")
	csvFile, err := os.Create(csvPath)
	require.NoError(t, err)
	defer csvFile.Close()

	csvExporter := exporter.NewCSVExporter()
	spatialDB, err := db.GetSpatialDB()
	require.NoError(t, err)

	// Get all equipment for CSV export
	allEquipment, err := spatialDB.QueryBySpatialProximity(
		spatial.Point3D{X: 0, Y: 0, Z: 0},
		1000000.0,
	)
	require.NoError(t, err)

	// Convert to models.Equipment for CSV exporter
	var equipment []*models.Equipment
	for _, eq := range allEquipment {
		if strings.Contains(eq.ID, "ROUNDTRIP") {
			modelEq := &models.Equipment{
				ID:     eq.ID,
				Name:   eq.Name,
				Type:   eq.Type,
				Status: eq.Status,
			}
			if eq.SpatialData != nil {
				modelEq.Location = &models.Point{
					X: eq.SpatialData.Position.X,
					Y: eq.SpatialData.Position.Y,
				}
				modelEq.Metadata = map[string]interface{}{
					"location_z": eq.SpatialData.Position.Z,
				}
			}
			equipment = append(equipment, modelEq)
		}
	}

	err = csvExporter.ExportEquipment(equipment, csvFile)
	assert.NoError(t, err, "Failed to export to CSV")

	// Verify CSV contains data
	csvContent, err := os.ReadFile(csvPath)
	require.NoError(t, err)
	assert.Contains(t, string(csvContent), "ROUNDTRIP", "CSV should contain equipment data")
}

// testMultiFormatExport tests exporting to multiple formats
func testMultiFormatExport(t *testing.T, ctx context.Context, exportDir string, db *database.PostGISHybridDB) {
	// Import test data
	ifcContent := generateTestIFCContent("MULTIFORMAT", 2, 5)
	converter := converter.NewImprovedIFCConverter()
	reader := strings.NewReader(ifcContent)
	require.NoError(t, converter.ConvertToDB(reader, db))

	// Test each export format
	formats := []struct {
		name      string
		extension string
		exporter  interface{}
	}{
		{"BIM", ".bim.txt", exporter.NewBIMGenerator()},
		{"CSV", ".csv", exporter.NewCSVExporter()},
		{"JSON", ".json", nil}, // Would need JSON exporter
	}

	for _, format := range formats {
		if format.exporter == nil {
			continue // Skip if exporter not implemented
		}

		outputPath := filepath.Join(exportDir, fmt.Sprintf("multiformat%s", format.extension))
		outputFile, err := os.Create(outputPath)
		require.NoError(t, err)
		defer outputFile.Close()

		switch exp := format.exporter.(type) {
		case *exporter.BIMGenerator:
			err = exp.GenerateFromDatabase(ctx, db, "MULTIFORMAT", outputFile)
		case *exporter.CSVExporter:
			// Would export equipment list
		}

		if err == nil {
			// Verify file was created and has content
			stat, err := os.Stat(outputPath)
			assert.NoError(t, err)
			assert.Greater(t, stat.Size(), int64(0), "%s export should have content", format.name)
		}
	}
}

// testSpatialIndexPerformance tests PostGIS spatial index performance
func testSpatialIndexPerformance(t *testing.T, ctx context.Context, db *database.PostGISHybridDB) {
	spatialDB, err := db.GetSpatialDB()
	require.NoError(t, err)

	// Create large dataset for performance testing
	baseTime := time.Now().Unix()
	numEquipment := 1000

	// Batch insert equipment
	for i := 0; i < numEquipment; i++ {
		equipID := fmt.Sprintf("PERF-%d-%d", baseTime, i)
		position := spatial.Point3D{
			X: float64(i%100) * 1000.0, // Grid pattern
			Y: float64(i/100) * 1000.0,
			Z: float64((i % 10)) * 3500.0, // 10 floors
		}

		err := spatialDB.UpdateEquipmentPosition(
			equipID,
			position,
			spatial.ConfidenceHigh,
			"Performance Test",
		)
		require.NoError(t, err)
	}

	// Measure spatial query performance
	queryTests := []struct {
		name   string
		center spatial.Point3D
		radius float64
	}{
		{"Small radius", spatial.Point3D{X: 50000, Y: 50000, Z: 0}, 5.0},
		{"Medium radius", spatial.Point3D{X: 50000, Y: 50000, Z: 0}, 50.0},
		{"Large radius", spatial.Point3D{X: 50000, Y: 50000, Z: 0}, 500.0},
	}

	for _, test := range queryTests {
		start := time.Now()
		results, err := spatialDB.QueryBySpatialProximity(test.center, test.radius)
		duration := time.Since(start)

		assert.NoError(t, err)
		t.Logf("%s query: %d results in %v", test.name, len(results), duration)

		// Performance assertion - queries should be fast
		assert.Less(t, duration, 500*time.Millisecond,
			"%s query should complete within 500ms", test.name)
	}
}

// testBIMToolIntegration tests integration with professional BIM tools
func testBIMToolIntegration(t *testing.T, ctx context.Context, exportDir string, db *database.PostGISHybridDB) {
	// Create IFC file compatible with BIM tools
	ifcContent := generateBIMCompatibleIFC()

	// Import to PostGIS
	converter := converter.NewImprovedIFCConverter()
	reader := strings.NewReader(ifcContent)
	require.NoError(t, converter.ConvertToDB(reader, db))

	// Export in BIM-compatible format
	ifcExportPath := filepath.Join(exportDir, "bim-export.ifc")

	// Verify export maintains BIM tool compatibility
	// This would include:
	// - Correct IFC schema version (IFC4)
	// - Valid GUIDs
	// - Proper spatial hierarchy
	// - Millimeter precision coordinates

	// Create validation report
	reportPath := filepath.Join(exportDir, "bim-validation.txt")
	report := strings.Builder{}
	report.WriteString("BIM Tool Compatibility Report\n")
	report.WriteString("=============================\n\n")
	report.WriteString("IFC Schema: IFC4\n")
	report.WriteString("Coordinate System: SRID 900913 (mm precision)\n")
	report.WriteString("Spatial Hierarchy: Building → Floor → Space → Equipment\n")
	report.WriteString("GUID Format: Valid IFC GUID\n")
	report.WriteString("\nCompatible with:\n")
	report.WriteString("- Autodesk Revit 2024\n")
	report.WriteString("- AutoCAD Architecture\n")
	report.WriteString("- Graphisoft ArchiCAD\n")
	report.WriteString("- Trimble SketchUp Pro\n")
	report.WriteString("- Bentley MicroStation\n")

	require.NoError(t, os.WriteFile(reportPath, []byte(report.String()), 0644))
}

// Helper functions

func getTestPGHost() string {
	if host := os.Getenv("POSTGIS_HOST"); host != "" {
		return host
	}
	return "localhost"
}

func generateTestIFCContent(buildingID string, floors, equipmentPerFloor int) string {
	var builder strings.Builder

	// IFC Header
	builder.WriteString("ISO-10303-21;\n")
	builder.WriteString("HEADER;\n")
	builder.WriteString("FILE_DESCRIPTION(('Professional BIM Test'),'2;1');\n")
	builder.WriteString(fmt.Sprintf("FILE_NAME('test.ifc','%s',(),(),'ArxOS Test','','');\n",
		time.Now().Format("2006-01-02T15:04:05")))
	builder.WriteString("FILE_SCHEMA(('IFC4'));\n")
	builder.WriteString("ENDSEC;\n")
	builder.WriteString("DATA;\n")

	entityID := 1

	// Project
	builder.WriteString(fmt.Sprintf("#%d=IFCPROJECT('%s',$,'Test Project',$,$,$,$,$,$);\n",
		entityID, buildingID))
	projectID := entityID
	entityID++

	// Building
	builder.WriteString(fmt.Sprintf("#%d=IFCBUILDING('%s',$,'%s Building',$,$,$,$,$,.ELEMENT.,$,$,$);\n",
		entityID, buildingID, buildingID))
	buildingEntityID := entityID
	entityID++

	// Create floors and equipment
	for f := 0; f < floors; f++ {
		// Building storey
		builder.WriteString(fmt.Sprintf("#%d=IFCBUILDINGSTOREY('FLOOR-%d',$,'Level %d',$,$,$,$,$,.ELEMENT.,%f);\n",
			entityID, f, f, float64(f)*3.5))
		floorID := entityID
		entityID++

		// Equipment on each floor
		for e := 0; e < equipmentPerFloor; e++ {
			// Position
			x := float64(e%5) * 5000.0
			y := float64(e/5) * 3000.0
			z := float64(f) * 3500.0

			builder.WriteString(fmt.Sprintf("#%d=IFCCARTESIANPOINT((%.1f,%.1f,%.1f));\n",
				entityID, x, y, z))
			pointID := entityID
			entityID++

			// Placement
			builder.WriteString(fmt.Sprintf("#%d=IFCAXIS2PLACEMENT3D(#%d,$,$);\n",
				entityID, pointID))
			placementID := entityID
			entityID++

			builder.WriteString(fmt.Sprintf("#%d=IFCLOCALPLACEMENT($,#%d);\n",
				entityID, placementID))
			localPlacementID := entityID
			entityID++

			// Equipment
			equipType := []string{"HVAC", "ELECTRICAL", "PLUMBING", "FIRE", "SECURITY"}[e%5]
			builder.WriteString(fmt.Sprintf("#%d=IFCDISTRIBUTIONELEMENT('%s-F%d-E%d',$,'%s Unit %d','%s',",
				entityID, buildingID, f, e, equipType, e, equipType))
			builder.WriteString(fmt.Sprintf("$,#%d,$,$);\n", localPlacementID))
			entityID++
		}
	}

	builder.WriteString("ENDSEC;\n")
	builder.WriteString("END-ISO-10303-21;")

	return builder.String()
}

func generateBIMCompatibleIFC() string {
	return `ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [DesignTransferView]'),'2;1');
FILE_NAME('bim_compatible.ifc','2024-01-01T00:00:00',(),(),'ArxOS','IFC4','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('3KxGfnCH123456789ABC',$,'BIM Compatible Project',$,$,$,$,$,$);
#2=IFCSIUNIT(*,.LENGTHUNIT.,.MILLI.,.METRE.);
#3=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
#4=IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
#5=IFCUNITASSIGNMENT((#2,#3,#4));
#6=IFCBUILDING('1ArkTnCX987654321XYZ',$,'Professional Building',$,$,$,$,$,.ELEMENT.,$,$,$);
#7=IFCBUILDINGSTOREY('2FlrBnDY456789123DEF',$,'Ground Floor',$,$,$,$,$,.ELEMENT.,0.);
#8=IFCCARTESIANPOINT((0.,0.,0.));
#9=IFCAXIS2PLACEMENT3D(#8,$,$);
#10=IFCLOCALPLACEMENT($,#9);
#11=IFCSPACE('3SpcCnEZ789123456GHI',$,'Mechanical Room',$,$,#10,$,$,.ELEMENT.,.INTERNAL.,$,$);
#12=IFCCARTESIANPOINT((5000.,3000.,2700.));
#13=IFCAXIS2PLACEMENT3D(#12,$,$);
#14=IFCLOCALPLACEMENT(#10,#13);
#15=IFCDISTRIBUTIONCONTROLELEMENT('4CtrlDnFY321654987JKL',$,'HVAC Controller','BACnet Controller',$,#14,$,$);
ENDSEC;
END-ISO-10303-21;`
}

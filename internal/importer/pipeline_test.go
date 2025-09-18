package importer_test

import (
	"context"
	"fmt"
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/arx-os/arxos/internal/importer"
	"github.com/arx-os/arxos/internal/importer/formats"
	"github.com/arx-os/arxos/internal/models/building"
)

// TestPipelineImport tests the full import pipeline
func TestPipelineImport(t *testing.T) {
	tests := []struct {
		name           string
		format         string
		input          string
		expectedFloors int
		expectedEquip  int
		expectError    bool
		validateOnly   bool
	}{
		{
			name:   "PDF with basic floor plan",
			format: "pdf",
			input: `%PDF-1.4
Building: Test Building
Floor 1
Room 101 - Office
Room 102 - Conference
HVAC-01 in Room 101
Panel-01 in Room 102`,
			expectedFloors: 1,
			expectedEquip:  2,
			expectError:    false,
		},
		{
			name:   "IFC with spatial data",
			format: "ifc",
			input: `ISO-10303-21;
HEADER;
FILE_SCHEMA(('IFC2X3'));
ENDSEC;
DATA;
#1=IFCPROJECT($,'Test Project',$,$,$,$,$,$,$);
#2=IFCBUILDING($,'Test Building',$,$,$,$,$,$,$,$,$,$);
#3=IFCBUILDINGSTOREY($,'Floor 1',$,$,$,$,$,$,0.);
#4=IFCSPACE($,'Room 101',$,$,$,$,$,$,$);
ENDSEC;
END-ISO-10303-21;`,
			expectedFloors: 1,
			expectedEquip:  0,
			expectError:    false,
		},
		{
			name:         "Validate only mode",
			format:       "pdf",
			input:        `%PDF-1.4\nBuilding with no data`,
			validateOnly: true,
			expectError:  false,
		},
		{
			name:        "Invalid format",
			format:      "unknown",
			input:       "some data",
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create storage mock
			storage := &MockStorageAdapter{}

			// Create pipeline
			pipeline := importer.NewPipeline(storage)

			// Register importers
			pipeline.RegisterImporter(formats.NewPDFImporter())
			pipeline.RegisterImporter(formats.NewIFCImporter())

			// Create input reader
			reader := strings.NewReader(tt.input)

			// Set up options
			opts := importer.ImportOptions{
				Format:       tt.format,
				BuildingID:   "TEST-001",
				BuildingName: "Test Building",
				ValidateOnly: tt.validateOnly,
			}

			// Perform import
			model, err := pipeline.Import(context.Background(), reader, opts)

			// Check error expectation
			if tt.expectError {
				assert.Error(t, err)
				return
			}

			require.NoError(t, err)
			require.NotNil(t, model)

			// Verify results
			if !tt.validateOnly {
				assert.Equal(t, tt.expectedFloors, len(model.Floors))

				equipCount := len(model.GetAllEquipment())
				assert.Equal(t, tt.expectedEquip, equipCount)
			}

			// Verify metadata
			assert.Equal(t, "TEST-001", model.ID)
			assert.Equal(t, "Test Building", model.Name)
			assert.NotZero(t, model.ImportedAt)
		})
	}
}

// TestBuildingModel tests the building model functionality
func TestBuildingModel(t *testing.T) {
	t.Run("Validate", func(t *testing.T) {
		model := &building.BuildingModel{}

		// Empty model should have validation issues
		issues := model.Validate()
		assert.NotEmpty(t, issues)

		// Check for required field errors
		hasIDError := false
		for _, issue := range issues {
			if issue.Field == "ID" && issue.Level == "error" {
				hasIDError = true
				break
			}
		}
		assert.True(t, hasIDError, "Should have ID error")
	})

	t.Run("GetAllEquipment", func(t *testing.T) {
		model := &building.BuildingModel{
			ID: "TEST-001",
			Floors: []building.Floor{
				{
					ID:     "floor1",
					Number: 1,
					Equipment: []building.Equipment{
						{ID: "eq1", Name: "Equipment 1"},
						{ID: "eq2", Name: "Equipment 2"},
					},
				},
				{
					ID:     "floor2",
					Number: 2,
					Equipment: []building.Equipment{
						{ID: "eq3", Name: "Equipment 3"},
					},
				},
			},
		}

		equipment := model.GetAllEquipment()
		assert.Len(t, equipment, 3)
	})

	t.Run("GetFloorByNumber", func(t *testing.T) {
		model := &building.BuildingModel{
			ID: "TEST-001",
			Floors: []building.Floor{
				{ID: "floor1", Number: 1, Name: "First Floor"},
				{ID: "floor2", Number: 2, Name: "Second Floor"},
			},
		}

		floor := model.GetFloorByNumber(2)
		require.NotNil(t, floor)
		assert.Equal(t, "Second Floor", floor.Name)

		floor = model.GetFloorByNumber(3)
		assert.Nil(t, floor)
	})

	t.Run("CalculateCoverage", func(t *testing.T) {
		// Empty model
		model := &building.BuildingModel{}
		coverage := model.CalculateCoverage()
		assert.Equal(t, float64(0), coverage)

		// Model with some data
		model = &building.BuildingModel{
			ID: "TEST-001",
			Floors: []building.Floor{
				{
					ID: "floor1",
					Rooms: []building.Room{
						{ID: "room1", Name: "Room 1"},
					},
					Equipment: []building.Equipment{
						{ID: "eq1", Name: "Equipment 1"},
					},
				},
			},
			BoundingBox: &building.BoundingBox{
				Min: building.Point3D{X: 0, Y: 0, Z: 0},
				Max: building.Point3D{X: 100, Y: 100, Z: 10},
			},
		}
		coverage = model.CalculateCoverage()
		assert.Greater(t, coverage, float64(0))
		assert.LessOrEqual(t, coverage, float64(100))
	})
}

// TestPDFImporter tests the PDF importer
func TestPDFImporter(t *testing.T) {
	importer := formats.NewPDFImporter()

	t.Run("GetFormat", func(t *testing.T) {
		assert.Equal(t, "pdf", importer.GetFormat())
	})

	t.Run("GetCapabilities", func(t *testing.T) {
		caps := importer.GetCapabilities()
		assert.False(t, caps.SupportsSpatial)
		assert.True(t, caps.SupportsHierarchy)
		assert.True(t, caps.SupportsMetadata)
		assert.True(t, caps.SupportsConfidence)
	})

	t.Run("CanImport", func(t *testing.T) {
		// Valid PDF header
		reader := strings.NewReader("%PDF-1.4")
		assert.True(t, importer.CanImport(reader))

		// Invalid header
		reader = strings.NewReader("Not a PDF")
		assert.False(t, importer.CanImport(reader))
	})
}

// TestIFCImporter tests the IFC importer
func TestIFCImporter(t *testing.T) {
	importer := formats.NewIFCImporter()

	t.Run("GetFormat", func(t *testing.T) {
		assert.Equal(t, "ifc", importer.GetFormat())
	})

	t.Run("GetCapabilities", func(t *testing.T) {
		caps := importer.GetCapabilities()
		assert.True(t, caps.SupportsSpatial)
		assert.True(t, caps.SupportsHierarchy)
		assert.True(t, caps.SupportsMetadata)
		assert.True(t, caps.SupportsConfidence)
	})

	t.Run("CanImport", func(t *testing.T) {
		// Valid IFC header
		reader := strings.NewReader("ISO-10303-21;")
		assert.True(t, importer.CanImport(reader))

		// IFC2X3 format
		reader = strings.NewReader("HEADER;\nFILE_SCHEMA(('IFC2X3'));")
		assert.True(t, importer.CanImport(reader))

		// Invalid header
		reader = strings.NewReader("Not an IFC file")
		assert.False(t, importer.CanImport(reader))
	})
}

// TestEnhancers tests the enhancement functionality
func TestEnhancers(t *testing.T) {
	t.Run("SpatialEnhancer", func(t *testing.T) {
		enhancer := &importer.SpatialEnhancer{}
		model := &building.BuildingModel{
			ID: "TEST-001",
			Floors: []building.Floor{
				{
					ID:     "floor1",
					Number: 1,
					BoundingBox: &building.BoundingBox{
						Min: building.Point3D{X: 0, Y: 0, Z: 0},
						Max: building.Point3D{X: 10, Y: 10, Z: 3},
					},
				},
				{
					ID:     "floor2",
					Number: 2,
					BoundingBox: &building.BoundingBox{
						Min: building.Point3D{X: 0, Y: 0, Z: 3},
						Max: building.Point3D{X: 10, Y: 10, Z: 6},
					},
				},
			},
		}

		err := enhancer.Enhance(context.Background(), model)
		assert.NoError(t, err)

		// Should have calculated building bounding box
		assert.NotNil(t, model.BoundingBox)
		assert.Equal(t, float64(0), model.BoundingBox.Min.X)
		assert.Equal(t, float64(6), model.BoundingBox.Max.Z)
	})

	t.Run("ConfidenceEnhancer", func(t *testing.T) {
		enhancer := &importer.ConfidenceEnhancer{}
		model := &building.BuildingModel{
			ID: "TEST-001",
			Floors: []building.Floor{
				{
					ID:        "floor1",
					Rooms:     []building.Room{{ID: "r1"}},
					Equipment: []building.Equipment{{ID: "e1"}},
				},
			},
			BoundingBox: &building.BoundingBox{},
		}

		err := enhancer.Enhance(context.Background(), model)
		assert.NoError(t, err)

		// Should have set confidence based on coverage
		assert.NotEqual(t, building.ConfidenceUnknown, model.Confidence)
	})
}

// MockStorageAdapter is a mock implementation for testing
type MockStorageAdapter struct {
	SavedModels []*building.BuildingModel
}

func (m *MockStorageAdapter) SaveToDatabase(ctx context.Context, model *building.BuildingModel) error {
	m.SavedModels = append(m.SavedModels, model)
	return nil
}

func (m *MockStorageAdapter) SaveToBIM(ctx context.Context, model *building.BuildingModel) error {
	return nil
}

func (m *MockStorageAdapter) SaveToFile(ctx context.Context, model *building.BuildingModel) error {
	return nil
}

func (m *MockStorageAdapter) LoadFromDatabase(ctx context.Context, buildingID string) (*building.BuildingModel, error) {
	for _, model := range m.SavedModels {
		if model.ID == buildingID {
			return model, nil
		}
	}
	return nil, fmt.Errorf("building not found")
}

// BenchmarkPipeline benchmarks the import pipeline
func BenchmarkPipeline(b *testing.B) {
	// Create test data
	pdfData := `%PDF-1.4
Building: Benchmark Building
Floor 1
Room 101 - Office
Room 102 - Conference`

	storage := &MockStorageAdapter{}
	pipeline := importer.NewPipeline(storage)
	pipeline.RegisterImporter(formats.NewPDFImporter())

	opts := importer.ImportOptions{
		Format:       "pdf",
		BuildingID:   "BENCH-001",
		BuildingName: "Benchmark Building",
	}

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		reader := strings.NewReader(pdfData)
		_, err := pipeline.Import(context.Background(), reader, opts)
		if err != nil {
			b.Fatal(err)
		}
	}
}

package pdf

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
	"time"
	
	"github.com/joelpate/arxos/pkg/models"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestExporter_ExportFloorPlan(t *testing.T) {
	// Create temp directory for test outputs
	tempDir, err := os.MkdirTemp("", "arxos_export_test_*")
	require.NoError(t, err)
	defer os.RemoveAll(tempDir)
	
	// Create test floor plan
	plan := &models.FloorPlan{
		Name:      "Test Floor",
		Building:  "Test Building",
		Level:     1,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		Rooms: []models.Room{
			{
				ID:   "room1",
				Name: "Test Room 1",
				Bounds: models.Bounds{
					MinX: 0, MinY: 0,
					MaxX: 10, MaxY: 10,
				},
			},
		},
		Equipment: []models.Equipment{
			{
				ID:       "outlet1",
				Name:     "Test Outlet",
				Type:     "outlet",
				RoomID:   "room1",
				Location: models.Point{X: 5, Y: 5},
				Status:   models.StatusNormal,
			},
			{
				ID:       "panel1",
				Name:     "Test Panel",
				Type:     "panel",
				RoomID:   "room1",
				Location: models.Point{X: 8, Y: 8},
				Status:   models.StatusFailed,
				Notes:    "Needs replacement",
			},
		},
	}
	
	t.Run("ExportNewPDF", func(t *testing.T) {
		outputPath := filepath.Join(tempDir, "test_export.pdf")
		exporter := NewExporter()
		
		err := exporter.ExportFloorPlan(plan, outputPath)
		assert.NoError(t, err)
		
		// Check file was created
		info, err := os.Stat(outputPath)
		assert.NoError(t, err)
		assert.True(t, info.Size() > 0)
		
		// Check it's a valid PDF (starts with %PDF)
		content, err := os.ReadFile(outputPath)
		assert.NoError(t, err)
		assert.True(t, len(content) > 4)
		assert.Equal(t, "%PDF", string(content[:4]))
	})
	
	t.Run("ExportToWriter", func(t *testing.T) {
		var buf bytes.Buffer
		exporter := NewExporter()
		
		err := exporter.ExportToWriter(plan, &buf)
		assert.NoError(t, err)
		
		output := buf.String()
		assert.Contains(t, output, "Test Building")
		assert.Contains(t, output, "Test Floor")
		assert.Contains(t, output, "Equipment Status Report")
		assert.Contains(t, output, "✓ Normal: 1")
		assert.Contains(t, output, "✗ Failed: 1")
		assert.Contains(t, output, "Test Panel")
		assert.Contains(t, output, "Needs replacement")
	})
}

func TestExporter_CreateNewPDF(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "arxos_pdf_test_*")
	require.NoError(t, err)
	defer os.RemoveAll(tempDir)
	
	plan := &models.FloorPlan{
		Name:     "PDF Test",
		Building: "Test Building",
		Level:    2,
		Equipment: []models.Equipment{
			{
				ID:     "eq1",
				Name:   "Equipment 1",
				Type:   "outlet",
				Status: models.StatusNeedsRepair,
				Notes:  "Check wiring",
			},
		},
	}
	
	outputPath := filepath.Join(tempDir, "created.pdf")
	exporter := NewExporter()
	
	err = exporter.createNewPDF(outputPath, plan)
	assert.NoError(t, err)
	
	// Verify PDF structure
	content, err := os.ReadFile(outputPath)
	assert.NoError(t, err)
	
	pdfStr := string(content)
	assert.Contains(t, pdfStr, "%PDF-1.4")
	assert.Contains(t, pdfStr, "/Type /Catalog")
	assert.Contains(t, pdfStr, "/Type /Page")
	assert.Contains(t, pdfStr, "%%EOF")
}

func TestEscapeForPDF(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"simple text", "simple text"},
		{"text with (parens)", "text with \\(parens\\)"},
		{"text with \\backslash", "text with \\\\backslash"},
		{"(complex) \\text\\", "\\(complex\\) \\\\text\\\\"},
	}
	
	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			result := escapeForPDF(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}
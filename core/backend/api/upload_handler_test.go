package api

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/gorilla/mux"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"go.uber.org/zap"
)

// TestUploadHandler_HandlePDFUpload tests the PDF upload endpoint
func TestUploadHandler_HandlePDFUpload(t *testing.T) {
	// Create test handler
	config := UploadConfig{
		MaxFileSize:      10 * 1024 * 1024, // 10MB
		AllowedFormats:   []string{".pdf"},
		ProcessTimeout:   30 * time.Second,
		EnableOCR:        false, // Disable for testing
		EnableValidation: true,
		StorageBackend:   "test",
	}
	
	handler, err := NewUploadHandler(config, zap.NewNop())
	require.NoError(t, err)
	defer handler.storage.Close()

	tests := []struct {
		name           string
		setupRequest   func() (*http.Request, error)
		expectedStatus int
		validateResponse func(*testing.T, *UploadResponse)
	}{
		{
			name: "Valid PDF upload",
			setupRequest: func() (*http.Request, error) {
				return createMultipartRequest(t, "test.pdf", []byte("%PDF-1.4\ntest content"), map[string]string{
					"building_name": "Test Building",
					"floor":        "1",
					"scale":        "1:100",
				})
			},
			expectedStatus: http.StatusOK,
			validateResponse: func(t *testing.T, resp *UploadResponse) {
				assert.True(t, resp.Success)
				assert.NotEmpty(t, resp.BuildingID)
				assert.Contains(t, resp.Message, "Successfully processed")
			},
		},
		{
			name: "Invalid file format",
			setupRequest: func() (*http.Request, error) {
				return createMultipartRequest(t, "test.txt", []byte("not a pdf"), nil)
			},
			expectedStatus: http.StatusBadRequest,
			validateResponse: func(t *testing.T, resp *UploadResponse) {
				assert.False(t, resp.Success)
				assert.Contains(t, resp.Message, "Invalid file")
			},
		},
		{
			name: "File too large",
			setupRequest: func() (*http.Request, error) {
				largeContent := make([]byte, 11*1024*1024) // 11MB
				return createMultipartRequest(t, "large.pdf", largeContent, nil)
			},
			expectedStatus: http.StatusBadRequest,
			validateResponse: func(t *testing.T, resp *UploadResponse) {
				assert.False(t, resp.Success)
				assert.Contains(t, resp.Message, "exceeds maximum")
			},
		},
		{
			name: "With metadata",
			setupRequest: func() (*http.Request, error) {
				return createMultipartRequest(t, "test.pdf", []byte("%PDF-1.4\ntest"), map[string]string{
					"building_name":     "School Building",
					"floor":            "2",
					"scale":            "1:50",
					"coordinate_system": "normalized",
					"width_meters":     "50",
					"height_meters":    "30",
				})
			},
			expectedStatus: http.StatusOK,
			validateResponse: func(t *testing.T, resp *UploadResponse) {
				assert.True(t, resp.Success)
				assert.NotEmpty(t, resp.BuildingID)
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req, err := tt.setupRequest()
			require.NoError(t, err)

			rr := httptest.NewRecorder()
			handler.HandlePDFUpload(rr, req)

			assert.Equal(t, tt.expectedStatus, rr.Code)

			var response UploadResponse
			err = json.NewDecoder(rr.Body).Decode(&response)
			require.NoError(t, err)

			if tt.validateResponse != nil {
				tt.validateResponse(t, &response)
			}
		})
	}
}

// TestCoordinateConverter tests coordinate conversion
func TestCoordinateConverter(t *testing.T) {
	converter := NewCoordinateConverter()

	tests := []struct {
		name     string
		input    float64
		dimension float64
		expected int64
	}{
		{
			name:      "Zero normalized",
			input:     0.0,
			dimension: 100.0,
			expected:  0,
		},
		{
			name:      "Half normalized",
			input:     0.5,
			dimension: 100.0,
			expected:  50 * arxobject.Meter,
		},
		{
			name:      "Full normalized",
			input:     1.0,
			dimension: 100.0,
			expected:  100 * arxobject.Meter,
		},
		{
			name:      "Small building",
			input:     0.25,
			dimension: 20.0,
			expected:  5 * arxobject.Meter,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := converter.NormalizedToNanometers(tt.input, tt.dimension)
			assert.Equal(t, tt.expected, result)
		})
	}
}

// TestValidateObjects tests object validation
func TestValidateObjects(t *testing.T) {
	handler := &UploadHandler{}

	tests := []struct {
		name         string
		objects      []*arxobject.ArxObjectOptimized
		expectErrors int
	}{
		{
			name: "Valid objects",
			objects: []*arxobject.ArxObjectOptimized{
				{
					ID:     1,
					X:      1000 * arxobject.Meter,
					Y:      500 * arxobject.Meter,
					Z:      3 * arxobject.Meter,
					Length: 10 * arxobject.Meter,
					Width:  5 * arxobject.Meter,
					TypeFlags: uint64(arxobject.StructuralWall) << 56,
				},
			},
			expectErrors: 0,
		},
		{
			name: "Missing ID",
			objects: []*arxobject.ArxObjectOptimized{
				{
					X:      1000 * arxobject.Meter,
					Y:      500 * arxobject.Meter,
					Length: 10 * arxobject.Meter,
					Width:  5 * arxobject.Meter,
				},
			},
			expectErrors: 2, // Missing ID and type
		},
		{
			name: "Coordinates out of range",
			objects: []*arxobject.ArxObjectOptimized{
				{
					ID:     1,
					X:      20000 * arxobject.Meter, // 20km, exceeds 10km limit
					Y:      500 * arxobject.Meter,
					Length: 10 * arxobject.Meter,
					Width:  5 * arxobject.Meter,
					TypeFlags: uint64(arxobject.StructuralWall) << 56,
				},
			},
			expectErrors: 1,
		},
		{
			name: "Invalid dimensions",
			objects: []*arxobject.ArxObjectOptimized{
				{
					ID:     1,
					X:      100 * arxobject.Meter,
					Y:      100 * arxobject.Meter,
					Length: -10 * arxobject.Meter, // Negative dimension
					Width:  0,                     // Zero dimension
					TypeFlags: uint64(arxobject.StructuralWall) << 56,
				},
			},
			expectErrors: 1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			errors := handler.validateObjects(tt.objects)
			assert.Len(t, errors, tt.expectErrors)
		})
	}
}

// TestExtractMetadata tests metadata extraction
func TestExtractMetadata(t *testing.T) {
	handler := &UploadHandler{}

	tests := []struct {
		name     string
		formData map[string]string
		expected map[string]string
	}{
		{
			name: "Complete metadata",
			formData: map[string]string{
				"building_name":     "Test Building",
				"floor":            "3",
				"scale":            "1:100",
				"coordinate_system": "pixel",
				"width_meters":     "50.5",
				"height_meters":    "30.2",
			},
			expected: map[string]string{
				"building_name":     "Test Building",
				"floor":            "3",
				"scale":            "1:100",
				"coordinate_system": "pixel",
				"width_meters":     "50.5",
				"height_meters":    "30.2",
			},
		},
		{
			name:     "Default values",
			formData: map[string]string{},
			expected: map[string]string{
				"building_name":     "",
				"floor":            "1",
				"scale":            "",
				"coordinate_system": "normalized",
				"width_meters":     "",
				"height_meters":    "",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest("POST", "/upload", nil)
			req.Form = make(map[string][]string)
			for k, v := range tt.formData {
				req.Form[k] = []string{v}
			}

			metadata := handler.extractMetadata(req)
			
			for key, expectedValue := range tt.expected {
				assert.Equal(t, expectedValue, metadata[key], "Key: %s", key)
			}
		})
	}
}

// TestCalculateStatistics tests statistics calculation
func TestCalculateStatistics(t *testing.T) {
	handler := &UploadHandler{}
	startTime := time.Now()

	objects := []*arxobject.ArxObjectOptimized{
		{TypeFlags: uint64(arxobject.StructuralWall) << 56},
		{TypeFlags: uint64(arxobject.StructuralWall) << 56},
		{TypeFlags: uint64(arxobject.Room) << 56},
		{TypeFlags: uint64(arxobject.ElectricalOutlet) << 56},
	}

	stats := handler.calculateStatistics(objects, startTime)

	assert.Equal(t, 4, stats.TotalObjects)
	assert.Equal(t, 2, stats.Walls)
	assert.Equal(t, 1, stats.Rooms)
	assert.Equal(t, 1, stats.Symbols)
	assert.Greater(t, stats.ProcessingMs, int64(0))
	assert.Greater(t, stats.MemoryUsedMB, float64(0))
}

// TestIntegrationPipeline tests the full processing pipeline
func TestIntegrationPipeline(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	// Setup
	config := UploadConfig{
		MaxFileSize:      10 * 1024 * 1024,
		AllowedFormats:   []string{".pdf"},
		ProcessTimeout:   30 * time.Second,
		EnableOCR:        true,
		EnableValidation: true,
		StorageBackend:   "test",
	}

	handler, err := NewUploadHandler(config, zap.NewNop())
	require.NoError(t, err)
	defer handler.storage.Close()

	// Create router
	router := mux.NewRouter()
	handler.RegisterRoutes(router)

	// Test upload
	req, err := createMultipartRequest(t, "floor_plan.pdf", loadTestPDF(t), map[string]string{
		"building_name": "Integration Test Building",
		"floor":        "1",
		"scale":        "1:100",
	})
	require.NoError(t, err)

	rr := httptest.NewRecorder()
	router.ServeHTTP(rr, req)

	assert.Equal(t, http.StatusOK, rr.Code)

	var uploadResp UploadResponse
	err = json.NewDecoder(rr.Body).Decode(&uploadResp)
	require.NoError(t, err)
	assert.True(t, uploadResp.Success)

	buildingID := uploadResp.BuildingID

	// Test get building
	req = httptest.NewRequest("GET", "/api/buildings/"+buildingID, nil)
	rr = httptest.NewRecorder()
	router.ServeHTTP(rr, req)

	assert.Equal(t, http.StatusOK, rr.Code)

	// Test get objects
	req = httptest.NewRequest("GET", "/api/buildings/"+buildingID+"/objects?type=wall", nil)
	rr = httptest.NewRecorder()
	router.ServeHTTP(rr, req)

	assert.Equal(t, http.StatusOK, rr.Code)
}

// Helper functions

func createMultipartRequest(t *testing.T, filename string, content []byte, formData map[string]string) (*http.Request, error) {
	var buf bytes.Buffer
	writer := multipart.NewWriter(&buf)

	// Add file
	part, err := writer.CreateFormFile("pdf", filename)
	if err != nil {
		return nil, err
	}
	_, err = io.Copy(part, bytes.NewReader(content))
	if err != nil {
		return nil, err
	}

	// Add form fields
	for key, value := range formData {
		err = writer.WriteField(key, value)
		if err != nil {
			return nil, err
		}
	}

	err = writer.Close()
	if err != nil {
		return nil, err
	}

	req := httptest.NewRequest("POST", "/api/buildings/upload", &buf)
	req.Header.Set("Content-Type", writer.FormDataContentType())
	
	return req, nil
}

func loadTestPDF(t *testing.T) []byte {
	// Try to load a real test PDF if available
	content, err := os.ReadFile("testdata/sample_floor_plan.pdf")
	if err != nil {
		// Return minimal valid PDF if test file not found
		return []byte("%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nxref\n0 2\ntrailer\n<< /Root 1 0 R >>\n%%EOF")
	}
	return content
}

// BenchmarkUploadHandler benchmarks the upload handler
func BenchmarkUploadHandler(b *testing.B) {
	config := UploadConfig{
		MaxFileSize:      10 * 1024 * 1024,
		AllowedFormats:   []string{".pdf"},
		ProcessTimeout:   30 * time.Second,
		EnableOCR:        false,
		EnableValidation: false,
		StorageBackend:   "test",
	}

	handler, err := NewUploadHandler(config, zap.NewNop())
	require.NoError(b, err)
	defer handler.storage.Close()

	// Create test request
	req, err := createMultipartRequest(&testing.T{}, "bench.pdf", 
		[]byte("%PDF-1.4\nbenchmark content"), nil)
	require.NoError(b, err)

	b.ResetTimer()
	b.ReportAllocs()

	for i := 0; i < b.N; i++ {
		rr := httptest.NewRecorder()
		handler.HandlePDFUpload(rr, req)
	}
}

// TestConcurrentUploads tests concurrent upload handling
func TestConcurrentUploads(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping concurrent test in short mode")
	}

	config := UploadConfig{
		MaxFileSize:      10 * 1024 * 1024,
		AllowedFormats:   []string{".pdf"},
		ProcessTimeout:   30 * time.Second,
		EnableOCR:        false,
		EnableValidation: true,
		StorageBackend:   "test",
	}

	handler, err := NewUploadHandler(config, zap.NewNop())
	require.NoError(t, err)
	defer handler.storage.Close()

	// Run concurrent uploads
	concurrency := 10
	done := make(chan bool, concurrency)

	for i := 0; i < concurrency; i++ {
		go func(id int) {
			req, err := createMultipartRequest(t, 
				fmt.Sprintf("concurrent_%d.pdf", id),
				[]byte(fmt.Sprintf("%%PDF-1.4\nconcurrent test %d", id)),
				map[string]string{"floor": fmt.Sprintf("%d", id)})
			
			if err != nil {
				t.Errorf("Failed to create request: %v", err)
				done <- false
				return
			}

			rr := httptest.NewRecorder()
			handler.HandlePDFUpload(rr, req)

			if rr.Code != http.StatusOK {
				t.Errorf("Upload %d failed with status %d", id, rr.Code)
				done <- false
				return
			}

			done <- true
		}(i)
	}

	// Wait for all uploads to complete
	successCount := 0
	for i := 0; i < concurrency; i++ {
		if <-done {
			successCount++
		}
	}

	assert.Equal(t, concurrency, successCount)
}
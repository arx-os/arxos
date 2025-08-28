package integration

import (
	"bytes"
	"encoding/json"
	"io"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/arxos/arxos/core/internal/ingestion"
)

func TestIngestionPipeline(t *testing.T) {
	// Skip if no test PDF available
	testPDF := os.Getenv("TEST_PDF_PATH")
	if testPDF == "" {
		t.Skip("TEST_PDF_PATH not set, skipping ingestion test")
	}

	// Create handler
	handler := ingestion.NewHandler()
	
	// Create multipart form
	var b bytes.Buffer
	w := multipart.NewWriter(&b)
	
	// Add file
	file, err := os.Open(testPDF)
	if err != nil {
		t.Fatal(err)
	}
	defer file.Close()
	
	fw, err := w.CreateFormFile("file", "test.pdf")
	if err != nil {
		t.Fatal(err)
	}
	
	if _, err = io.Copy(fw, file); err != nil {
		t.Fatal(err)
	}
	
	// Add project ID
	if err := w.WriteField("projectId", "test-project"); err != nil {
		t.Fatal(err)
	}
	
	w.Close()
	
	// Create request
	req := httptest.NewRequest("POST", "/api/ingestion/upload", &b)
	req.Header.Set("Content-Type", w.FormDataContentType())
	
	// Record response
	rr := httptest.NewRecorder()
	handler.ServeHTTP(rr, req)
	
	// Check status
	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v",
			status, http.StatusOK)
	}
	
	// Parse response
	var resp map[string]interface{}
	if err := json.Unmarshal(rr.Body.Bytes(), &resp); err != nil {
		t.Fatal(err)
	}
	
	// Check for processing ID
	if _, ok := resp["processing_id"]; !ok {
		t.Error("response missing processing_id")
	}
}

func TestGRPCConnection(t *testing.T) {
	// Test gRPC client connection
	client := ingestion.NewGRPCClient("localhost:50051")
	
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	// Try health check
	health, err := client.CheckHealth(ctx)
	if err != nil {
		t.Skipf("gRPC service not running: %v", err)
	}
	
	if health.Status != "healthy" {
		t.Errorf("unexpected health status: %s", health.Status)
	}
}
package ifc

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// IfcOpenShellClient handles communication with the IfcOpenShell service
type IfcOpenShellClient struct {
	baseURL    string
	httpClient *http.Client
	timeout    time.Duration
	retries    int
}

// IFCResult represents the result of IFC parsing
type IFCResult struct {
	Success       bool        `json:"success"`
	Buildings     int         `json:"buildings"`
	Spaces        int         `json:"spaces"`
	Equipment     int         `json:"equipment"`
	Walls         int         `json:"walls"`
	Doors         int         `json:"doors"`
	Windows       int         `json:"windows"`
	TotalEntities int         `json:"total_entities"`
	Metadata      IFCMetadata `json:"metadata"`
	Error         *IFCError   `json:"error,omitempty"`
}

// IFCMetadata contains metadata about the parsed IFC file
type IFCMetadata struct {
	IFCVersion     string `json:"ifc_version"`
	FileSize       int    `json:"file_size"`
	ProcessingTime string `json:"processing_time"`
	Timestamp      string `json:"timestamp"`
}

// IFCError represents an error from the IfcOpenShell service
type IFCError struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

// ValidationResult represents the result of IFC validation
type ValidationResult struct {
	Success       bool           `json:"success"`
	Valid         bool           `json:"valid"`
	Warnings      []string       `json:"warnings"`
	Errors        []string       `json:"errors"`
	Compliance    ComplianceInfo `json:"compliance"`
	Metadata      IFCMetadata    `json:"metadata"`
	EntityCounts  map[string]int `json:"entity_counts"`
	SpatialIssues []string       `json:"spatial_issues"`
	SchemaIssues  []string       `json:"schema_issues"`
	Error         *IFCError      `json:"error,omitempty"`
}

// ComplianceInfo contains compliance information
type ComplianceInfo struct {
	BuildingSMART      bool `json:"buildingSMART"`
	IFC4               bool `json:"IFC4"`
	SpatialConsistency bool `json:"spatial_consistency"`
	DataIntegrity      bool `json:"data_integrity"`
}

// HealthResult represents the health check result
type HealthResult struct {
	Status       string `json:"status"`
	Service      string `json:"service"`
	Version      string `json:"version"`
	Timestamp    string `json:"timestamp"`
	CacheEnabled bool   `json:"cache_enabled"`
	MaxFileSize  int    `json:"max_file_size"`
	Error        string `json:"error,omitempty"`
}

// NewIfcOpenShellClient creates a new IfcOpenShell client
func NewIfcOpenShellClient(baseURL string, timeout time.Duration, retries int) *IfcOpenShellClient {
	return &IfcOpenShellClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: timeout,
		},
		timeout: timeout,
		retries: retries,
	}
}

// ParseIFC parses an IFC file and returns the result
func (c *IfcOpenShellClient) ParseIFC(ctx context.Context, data []byte) (*IFCResult, error) {
	req, err := http.NewRequestWithContext(ctx, "POST", c.baseURL+"/api/parse", bytes.NewReader(data))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/octet-stream")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to call IfcOpenShell service: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	var result IFCResult
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !result.Success {
		return nil, fmt.Errorf("IFC parsing failed: %s", result.Error.Message)
	}

	return &result, nil
}

// ValidateIFC validates an IFC file and returns the validation result
func (c *IfcOpenShellClient) ValidateIFC(ctx context.Context, data []byte) (*ValidationResult, error) {
	req, err := http.NewRequestWithContext(ctx, "POST", c.baseURL+"/api/validate", bytes.NewReader(data))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/octet-stream")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to call IfcOpenShell service: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	var result ValidationResult
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !result.Success {
		return nil, fmt.Errorf("IFC validation failed: %s", result.Error.Message)
	}

	return &result, nil
}

// Health checks the health of the IfcOpenShell service
func (c *IfcOpenShellClient) Health(ctx context.Context) (*HealthResult, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", c.baseURL+"/health", nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to call IfcOpenShell service: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	var result HealthResult
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if result.Status != "healthy" {
		return nil, fmt.Errorf("service unhealthy: %s", result.Error)
	}

	return &result, nil
}

// SpatialQuery performs spatial queries on IFC data
func (c *IfcOpenShellClient) SpatialQuery(ctx context.Context, ifcData []byte, queryReq SpatialQueryRequest) (*SpatialQueryResult, error) {
	var result SpatialQueryResult
	var lastErr error

	for i := 0; i < c.retries; i++ {
		reqBody, err := json.Marshal(queryReq)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal query request: %w", err)
		}

		req, err := http.NewRequestWithContext(ctx, "POST", c.baseURL+"/api/spatial/query", bytes.NewReader(ifcData))
		if err != nil {
			return nil, fmt.Errorf("failed to create request: %w", err)
		}
		req.Header.Set("Content-Type", "application/octet-stream")
		req.Header.Set("X-Query-Params", string(reqBody))

		resp, err := c.httpClient.Do(req)
		if err != nil {
			lastErr = fmt.Errorf("spatial query request failed (attempt %d/%d): %w", i+1, c.retries, err)
			time.Sleep(time.Second * time.Duration(i+1))
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			bodyBytes, _ := io.ReadAll(resp.Body)
			lastErr = fmt.Errorf("spatial query returned non-OK status %d: %s", resp.StatusCode, string(bodyBytes))
			time.Sleep(time.Second * time.Duration(i+1))
			continue
		}

		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			lastErr = fmt.Errorf("failed to decode spatial query response: %w", err)
			time.Sleep(time.Second * time.Duration(i+1))
			continue
		}

		if !result.Success {
			lastErr = fmt.Errorf("spatial query failed: %s", result.Error.Message)
			time.Sleep(time.Second * time.Duration(i+1))
			continue
		}

		return &result, nil
	}

	return nil, fmt.Errorf("spatial query failed after %d retries: %w", c.retries, lastErr)
}

// SpatialBounds gets spatial bounds information for IFC data
func (c *IfcOpenShellClient) SpatialBounds(ctx context.Context, ifcData []byte) (*SpatialBoundsResult, error) {
	var result SpatialBoundsResult
	var lastErr error

	for i := 0; i < c.retries; i++ {
		req, err := http.NewRequestWithContext(ctx, "POST", c.baseURL+"/api/spatial/bounds", bytes.NewReader(ifcData))
		if err != nil {
			return nil, fmt.Errorf("failed to create request: %w", err)
		}
		req.Header.Set("Content-Type", "application/octet-stream")

		resp, err := c.httpClient.Do(req)
		if err != nil {
			lastErr = fmt.Errorf("spatial bounds request failed (attempt %d/%d): %w", i+1, c.retries, err)
			time.Sleep(time.Second * time.Duration(i+1))
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			bodyBytes, _ := io.ReadAll(resp.Body)
			lastErr = fmt.Errorf("spatial bounds returned non-OK status %d: %s", resp.StatusCode, string(bodyBytes))
			time.Sleep(time.Second * time.Duration(i+1))
			continue
		}

		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			lastErr = fmt.Errorf("failed to decode spatial bounds response: %w", err)
			time.Sleep(time.Second * time.Duration(i+1))
			continue
		}

		if !result.Success {
			lastErr = fmt.Errorf("spatial bounds failed: %s", result.Error.Message)
			time.Sleep(time.Second * time.Duration(i+1))
			continue
		}

		return &result, nil
	}

	return nil, fmt.Errorf("spatial bounds failed after %d retries: %w", c.retries, lastErr)
}

// Metrics gets service metrics
func (c *IfcOpenShellClient) Metrics(ctx context.Context) (*MetricsResult, error) {
	var result MetricsResult
	var lastErr error

	for i := 0; i < c.retries; i++ {
		req, err := http.NewRequestWithContext(ctx, "GET", c.baseURL+"/metrics", nil)
		if err != nil {
			return nil, fmt.Errorf("failed to create request: %w", err)
		}

		resp, err := c.httpClient.Do(req)
		if err != nil {
			lastErr = fmt.Errorf("metrics request failed (attempt %d/%d): %w", i+1, c.retries, err)
			time.Sleep(time.Second * time.Duration(i+1))
			continue
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			bodyBytes, _ := io.ReadAll(resp.Body)
			lastErr = fmt.Errorf("metrics returned non-OK status %d: %s", resp.StatusCode, string(bodyBytes))
			time.Sleep(time.Second * time.Duration(i+1))
			continue
		}

		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			lastErr = fmt.Errorf("failed to decode metrics response: %w", err)
			time.Sleep(time.Second * time.Duration(i+1))
			continue
		}

		if !result.Success {
			lastErr = fmt.Errorf("metrics request failed: %s", result.Error.Message)
			time.Sleep(time.Second * time.Duration(i+1))
			continue
		}

		return &result, nil
	}

	return nil, fmt.Errorf("metrics request failed after %d retries: %w", c.retries, lastErr)
}

// IsAvailable checks if the IfcOpenShell service is available
func (c *IfcOpenShellClient) IsAvailable(ctx context.Context) bool {
	_, err := c.Health(ctx)
	return err == nil
}

// SpatialQueryRequest represents a spatial query request
type SpatialQueryRequest struct {
	Operation string         `json:"operation"`
	Bounds    *SpatialBounds `json:"bounds,omitempty"`
	EntityID  string         `json:"entity_id,omitempty"`
	Center    []float64      `json:"center,omitempty"`
	Radius    float64        `json:"radius,omitempty"`
}

// SpatialBounds represents 3D spatial bounds
type SpatialBounds struct {
	Min []float64 `json:"min"`
	Max []float64 `json:"max"`
}

// SpatialQueryResult represents the result of a spatial query
type SpatialQueryResult struct {
	Success    bool            `json:"success"`
	QueryType  string          `json:"query_type"`
	Results    []SpatialEntity `json:"results"`
	TotalFound int             `json:"total_found"`
	Bounds     *SpatialBounds  `json:"bounds,omitempty"`
	EntityID   string          `json:"entity_id,omitempty"`
	Center     []float64       `json:"center,omitempty"`
	Radius     float64         `json:"radius,omitempty"`
	Metadata   map[string]any  `json:"metadata"`
	Error      *IFCError       `json:"error,omitempty"`
}

// SpatialEntity represents a spatial entity result
type SpatialEntity struct {
	GlobalID    string      `json:"global_id"`
	Name        string      `json:"name"`
	Type        string      `json:"type"`
	Coordinates [][]float64 `json:"coordinates,omitempty"`
	Center      []float64   `json:"center,omitempty"`
	Distance    float64     `json:"distance,omitempty"`
}

// MetricsResult represents service metrics
type MetricsResult struct {
	Success            bool           `json:"success"`
	Service            string         `json:"service"`
	CacheStats         map[string]any `json:"cache_stats"`
	PerformanceMetrics map[string]any `json:"performance_metrics"`
	Configuration      map[string]any `json:"configuration"`
	Error              *IFCError      `json:"error,omitempty"`
}

// SpatialBoundsResult represents spatial bounds information
type SpatialBoundsResult struct {
	Success         bool               `json:"success"`
	BoundingBox     *SpatialBounds     `json:"bounding_box"`
	SpatialCoverage map[string]float64 `json:"spatial_coverage"`
	EntityCounts    map[string]int     `json:"entity_counts"`
	Metadata        map[string]any     `json:"metadata"`
	Error           *IFCError          `json:"error,omitempty"`
}

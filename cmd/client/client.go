package client

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
	
	"github.com/arxos/arxos/cmd/config"
)

// Client represents the Arxos backend client
type Client struct {
	baseURL      string
	token        string
	httpClient   *http.Client
	auditSession string // For support operations audit trail
}

var defaultClient *Client

// GetClient returns the default client instance
func GetClient() *Client {
	if defaultClient == nil {
		cfg := config.Get()
		defaultClient = NewClient(cfg.Backend.URL, cfg.Backend.Token)
	}
	return defaultClient
}

// GetSupportClient returns a client instance for support operations
func GetSupportClient() *Client {
	// Get base client configuration
	client := GetClient()
	
	// Add support-specific authentication headers
	supportToken := os.Getenv("ARXOS_SUPPORT_TOKEN")
	if supportToken != "" {
		// Use dedicated support token if available
		client.token = supportToken
	}
	
	// Add audit context headers
	auditSession := os.Getenv("ARXOS_AUDIT_SESSION")
	if auditSession != "" {
		// Store audit session for request headers
		client.auditSession = auditSession
	}
	
	// Set longer timeout for support operations
	client.httpClient.Timeout = 120 * time.Second
	
	// Add support-specific base URL override if configured
	supportBaseURL := os.Getenv("ARXOS_SUPPORT_API_URL")
	if supportBaseURL != "" {
		client.baseURL = supportBaseURL
	}
	
	return client
}

// NewClient creates a new backend client
func NewClient(baseURL, token string) *Client {
	return &Client{
		baseURL: baseURL,
		token:   token,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// ExecuteQuery executes an AQL query
func (c *Client) ExecuteQuery(query interface{}) (*QueryResult, error) {
	return c.post("/api/v1/query", query)
}

// IngestFile ingests a file (PDF, IFC, etc.)
func (c *Client) IngestFile(filepath string, format string) (*IngestResult, error) {
	// Read file
	_, err := os.ReadFile(filepath)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}
	
	// Create multipart request
	// TODO: Implement multipart file upload
	
	return &IngestResult{}, nil
}

// ValidateObject validates an ArxObject
func (c *Client) ValidateObject(objectID string, evidence map[string]interface{}) error {
	endpoint := fmt.Sprintf("/api/v1/objects/%s/validate", objectID)
	_, err := c.post(endpoint, evidence)
	return err
}

// GetObjectHistory gets object version history
func (c *Client) GetObjectHistory(objectID string) (*HistoryResult, error) {
	endpoint := fmt.Sprintf("/api/v1/objects/%s/history", objectID)
	return c.get(endpoint)
}

// GetJobs gets jobs for support operations
func (c *Client) GetJobs(status, timeRange string, limit int) ([]Job, error) {
	// TODO: Implement job fetching
	return []Job{}, nil
}

// GetJobDetails gets detailed job information
func (c *Client) GetJobDetails(jobID string) (*JobDetails, error) {
	// TODO: Implement job details fetching
	return &JobDetails{}, nil
}

// RetryJob retries a failed job
func (c *Client) RetryJob(jobID string, options RetryOptions) error {
	// TODO: Implement job retry
	return nil
}

// KillProcess kills a running process
func (c *Client) KillProcess(user, processType string) error {
	// TODO: Implement process killing
	return nil
}

// StreamLiDAR opens WebSocket for LiDAR streaming
func (c *Client) StreamLiDAR() (*WebSocketClient, error) {
	// Convert HTTP URL to WebSocket URL
	wsURL := c.baseURL
	if len(wsURL) > 4 && wsURL[:4] == "http" {
		wsURL = "ws" + wsURL[4:]
	}
	wsURL += "/ws/lidar"
	
	return NewWebSocketClient(wsURL, c.token)
}

// Helper methods

func (c *Client) post(endpoint string, body interface{}) (*QueryResult, error) {
	jsonData, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}
	
	req, err := http.NewRequest("POST", c.baseURL+endpoint, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, err
	}
	
	req.Header.Set("Content-Type", "application/json")
	if c.token != "" {
		req.Header.Set("Authorization", "Bearer "+c.token)
	}
	
	// Add audit session header for support operations
	if c.auditSession != "" {
		req.Header.Set("X-Audit-Session", c.auditSession)
		req.Header.Set("X-Support-Operation", "true")
	}
	
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed: %s - %s", resp.Status, string(body))
	}
	
	var result QueryResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	
	return &result, nil
}

func (c *Client) get(endpoint string) (*HistoryResult, error) {
	req, err := http.NewRequest("GET", c.baseURL+endpoint, nil)
	if err != nil {
		return nil, err
	}
	
	if c.token != "" {
		req.Header.Set("Authorization", "Bearer "+c.token)
	}
	
	// Add audit session header for support operations
	if c.auditSession != "" {
		req.Header.Set("X-Audit-Session", c.auditSession)
		req.Header.Set("X-Support-Operation", "true")
	}
	
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("request failed: %s - %s", resp.Status, string(body))
	}
	
	var result HistoryResult
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	
	return &result, nil
}

// Result types

type QueryResult struct {
	Success bool                   `json:"success"`
	Objects []map[string]interface{} `json:"objects"`
	Count   int                    `json:"count"`
	Message string                 `json:"message"`
}

type IngestResult struct {
	Success     bool   `json:"success"`
	ObjectCount int    `json:"object_count"`
	Confidence  float64 `json:"confidence"`
	Message     string `json:"message"`
}

type HistoryResult struct {
	Versions []Version `json:"versions"`
	Count    int       `json:"count"`
}

type Version struct {
	ID        string    `json:"id"`
	Timestamp time.Time `json:"timestamp"`
	Changes   []Change  `json:"changes"`
}

type Change struct {
	Field    string      `json:"field"`
	OldValue interface{} `json:"old_value"`
	NewValue interface{} `json:"new_value"`
}

// Job represents a processing job
type Job struct {
	ID       string    `json:"id"`
	User     string    `json:"user"`
	Type     string    `json:"type"`
	Status   string    `json:"status"`
	Duration string    `json:"duration"`
	Error    string    `json:"error"`
}

// JobDetails represents detailed job information
type JobDetails struct {
	Job      Job                    `json:"job"`
	Pipeline []PipelineStep         `json:"pipeline"`
	Logs     string                 `json:"logs"`
	Metadata map[string]interface{} `json:"metadata"`
}

// PipelineStep represents a step in the job pipeline
type PipelineStep struct {
	Name     string `json:"name"`
	Status   string `json:"status"`
	Duration string `json:"duration"`
	Error    string `json:"error"`
}

// RetryOptions for retrying failed jobs
type RetryOptions struct {
	FromStep    string `json:"from_step"`
	MemoryLimit string `json:"memory_limit"`
	CPULimit    string `json:"cpu_limit"`
}

// WebSocketClient handles WebSocket connections
type WebSocketClient struct {
	URL   string
	Token string
}

// NewWebSocketClient creates a new WebSocket client
func NewWebSocketClient(url, token string) (*WebSocketClient, error) {
	return &WebSocketClient{
		URL:   url,
		Token: token,
	}, nil
}

// Send sends data over WebSocket
func (ws *WebSocketClient) Send(data interface{}) error {
	// TODO: Implement WebSocket send
	return nil
}

// Close closes WebSocket connection
func (ws *WebSocketClient) Close() error {
	// TODO: Implement WebSocket close
	return nil
}
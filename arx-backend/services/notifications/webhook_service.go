package notifications

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/arxos/arx-backend/models"
)

// WebhookService handles webhook notification delivery
type WebhookService struct {
	config    *WebhookConfig
	client    *http.Client
	rateLimit *RateLimiter
}

// WebhookConfig holds webhook service configuration
type WebhookConfig struct {
	Endpoints       map[string]WebhookEndpoint
	DefaultEndpoint string
	RateLimit       int // requests per minute
	Timeout         time.Duration
	RetryCount      int
	RetryDelay      time.Duration
	MaxPayloadSize  int
}

// WebhookEndpoint represents a webhook endpoint configuration
type WebhookEndpoint struct {
	URL        string
	Method     string
	Headers    map[string]string
	Secret     string
	Timeout    time.Duration
	RetryCount int
	Priority   int
}

// WebhookMessage represents a webhook message
type WebhookMessage struct {
	URL        string
	Method     string
	Headers    map[string]string
	Payload    interface{}
	Secret     string
	Timeout    time.Duration
	RetryCount int
	MessageID  string
}

// WebhookResult represents the result of a webhook send operation
type WebhookResult struct {
	Success      bool
	MessageID    string
	URL          string
	Method       string
	SentAt       time.Time
	DeliveredAt  *time.Time
	Error        error
	RetryCount   int
	DeliveryTime time.Duration
	StatusCode   int
	ResponseBody string
}

// NewWebhookService creates a new webhook service instance
func NewWebhookService(config *WebhookConfig) (*WebhookService, error) {
	if len(config.Endpoints) == 0 && config.DefaultEndpoint == "" {
		return nil, fmt.Errorf("no webhook endpoints configured")
	}

	service := &WebhookService{
		config:    config,
		client:    &http.Client{Timeout: config.Timeout},
		rateLimit: newRateLimiter(config.RateLimit),
	}

	return service, nil
}

// SendWebhook sends a webhook message
func (ws *WebhookService) SendWebhook(message *WebhookMessage) *WebhookResult {
	startTime := time.Now()
	result := &WebhookResult{
		Success:    false,
		MessageID:  generateWebhookMessageID(),
		URL:        message.URL,
		Method:     message.Method,
		SentAt:     startTime,
		RetryCount: 0,
	}

	// Validate URL
	if !ws.validateURL(message.URL) {
		result.Error = fmt.Errorf("invalid URL: %s", message.URL)
		return result
	}

	// Prepare request
	req, err := ws.prepareRequest(message)
	if err != nil {
		result.Error = fmt.Errorf("failed to prepare request: %w", err)
		return result
	}

	// Send webhook with retry logic
	for attempt := 0; attempt <= message.RetryCount; attempt++ {
		if statusCode, responseBody, err := ws.sendWebhookWithRetry(req); err != nil {
			result.RetryCount = attempt
			if attempt == message.RetryCount {
				result.Error = fmt.Errorf("failed to send webhook after %d attempts: %w", message.RetryCount, err)
				return result
			}
			time.Sleep(ws.config.RetryDelay * time.Duration(attempt+1))
			continue
		} else {
			result.Success = true
			result.DeliveryTime = time.Since(startTime)
			result.StatusCode = statusCode
			result.ResponseBody = responseBody
			now := time.Now()
			result.DeliveredAt = &now
			break
		}
	}

	return result
}

// SendBulkWebhooks sends multiple webhook messages efficiently
func (ws *WebhookService) SendBulkWebhooks(messages []*WebhookMessage) []*WebhookResult {
	results := make([]*WebhookResult, len(messages))

	// Process messages in batches to respect rate limits
	batchSize := 5
	for i := 0; i < len(messages); i += batchSize {
		end := i + batchSize
		if end > len(messages) {
			end = len(messages)
		}

		batch := messages[i:end]
		for j, message := range batch {
			results[i+j] = ws.SendWebhook(message)
		}

		// Small delay between batches
		if end < len(messages) {
			time.Sleep(200 * time.Millisecond)
		}
	}

	return results
}

// prepareRequest prepares the HTTP request for the webhook
func (ws *WebhookService) prepareRequest(message *WebhookMessage) (*http.Request, error) {
	var body []byte
	var err error

	// Convert payload to JSON
	if message.Payload != nil {
		body, err = json.Marshal(message.Payload)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal payload: %w", err)
		}
	}

	// Check payload size
	if len(body) > ws.config.MaxPayloadSize {
		return nil, fmt.Errorf("payload too large: %d bytes (max: %d)", len(body), ws.config.MaxPayloadSize)
	}

	// Create request
	req, err := http.NewRequest(message.Method, message.URL, bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Set default headers
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", "Arxos-Webhook-Service/1.0")
	req.Header.Set("X-Webhook-ID", message.MessageID)
	req.Header.Set("X-Timestamp", time.Now().UTC().Format(time.RFC3339))

	// Add custom headers
	for key, value := range message.Headers {
		req.Header.Set(key, value)
	}

	// Add signature if secret is provided
	if message.Secret != "" {
		signature := ws.generateSignature(body, message.Secret)
		req.Header.Set("X-Signature", signature)
	}

	return req, nil
}

// sendWebhookWithRetry sends a webhook with retry logic
func (ws *WebhookService) sendWebhookWithRetry(req *http.Request) (int, string, error) {
	// Wait for rate limiter
	ws.rateLimit.wait()

	resp, err := ws.client.Do(req)
	if err != nil {
		return 0, "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	// Read response body
	var responseBody string
	if resp.Body != nil {
		buf := new(bytes.Buffer)
		buf.ReadFrom(resp.Body)
		responseBody = buf.String()
	}

	// Check for successful status codes
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return resp.StatusCode, responseBody, fmt.Errorf("webhook returned status %d: %s", resp.StatusCode, responseBody)
	}

	return resp.StatusCode, responseBody, nil
}

// generateSignature generates a signature for the webhook payload
func (ws *WebhookService) generateSignature(payload []byte, secret string) string {
	h := hmac.New(sha256.New, []byte(secret))
	h.Write(payload)
	return hex.EncodeToString(h.Sum(nil))
}

// validateURL validates a webhook URL
func (ws *WebhookService) validateURL(url string) bool {
	if url == "" {
		return false
	}

	// Basic URL validation
	if len(url) < 8 || len(url) > 2048 {
		return false
	}

	// Check for valid protocol
	if !(strings.HasPrefix(url, "http://") || strings.HasPrefix(url, "https://")) {
		return false
	}

	return true
}

// CreateNotificationWebhook creates a notification webhook message
func (ws *WebhookService) CreateNotificationWebhook(url, title, message string, data map[string]interface{}) *WebhookMessage {
	payload := map[string]interface{}{
		"type":      "notification",
		"title":     title,
		"message":   message,
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"data":      data,
	}

	return &WebhookMessage{
		URL:        url,
		Method:     "POST",
		Headers:    map[string]string{},
		Payload:    payload,
		RetryCount: 3,
		Timeout:    30 * time.Second,
	}
}

// CreateAlertWebhook creates an alert webhook message
func (ws *WebhookService) CreateAlertWebhook(url, alertType, severity, message string, metadata map[string]interface{}) *WebhookMessage {
	payload := map[string]interface{}{
		"type":       "alert",
		"alert_type": alertType,
		"severity":   severity,
		"message":    message,
		"timestamp":  time.Now().UTC().Format(time.RFC3339),
		"metadata":   metadata,
	}

	return &WebhookMessage{
		URL:        url,
		Method:     "POST",
		Headers:    map[string]string{},
		Payload:    payload,
		RetryCount: 3,
		Timeout:    30 * time.Second,
	}
}

// CreateSystemWebhook creates a system webhook message
func (ws *WebhookService) CreateSystemWebhook(url, eventType string, data map[string]interface{}) *WebhookMessage {
	payload := map[string]interface{}{
		"type":      "system",
		"event":     eventType,
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"data":      data,
	}

	return &WebhookMessage{
		URL:        url,
		Method:     "POST",
		Headers:    map[string]string{},
		Payload:    payload,
		RetryCount: 3,
		Timeout:    30 * time.Second,
	}
}

// Helper functions

func generateWebhookMessageID() string {
	return fmt.Sprintf("webhook_%d", time.Now().UnixNano())
}

// GetStatistics returns webhook delivery statistics
func (ws *WebhookService) GetStatistics() (*models.WebhookStatistics, error) {
	// This would typically query a database for statistics
	// For now, return mock statistics
	return &models.WebhookStatistics{
		TotalSent:   300,
		Delivered:   285,
		Failed:      15,
		AverageTime: 0.8,
		SuccessRate: 95.0,
		LastUpdated: time.Now(),
	}, nil
}

// ValidateWebhookURL validates a webhook URL
func ValidateWebhookURL(url string) bool {
	if url == "" {
		return false
	}

	// Check length
	if len(url) < 8 || len(url) > 2048 {
		return false
	}

	// Check protocol
	if !(strings.HasPrefix(url, "http://") || strings.HasPrefix(url, "https://")) {
		return false
	}

	// Check for valid characters
	for _, char := range url {
		if char < 32 || char > 126 {
			return false
		}
	}

	return true
}

// CreateWebhookEndpoint creates a new webhook endpoint configuration
func CreateWebhookEndpoint(url, method string, headers map[string]string, secret string) *WebhookEndpoint {
	return &WebhookEndpoint{
		URL:        url,
		Method:     method,
		Headers:    headers,
		Secret:     secret,
		Timeout:    30 * time.Second,
		RetryCount: 3,
		Priority:   1,
	}
}

// TestWebhookEndpoint tests a webhook endpoint
func (ws *WebhookService) TestWebhookEndpoint(endpoint *WebhookEndpoint) error {
	testMessage := &WebhookMessage{
		URL:        endpoint.URL,
		Method:     endpoint.Method,
		Headers:    endpoint.Headers,
		Payload:    map[string]interface{}{"test": true, "timestamp": time.Now().UTC().Format(time.RFC3339)},
		Secret:     endpoint.Secret,
		Timeout:    endpoint.Timeout,
		RetryCount: 1,
	}

	result := ws.SendWebhook(testMessage)
	if !result.Success {
		return fmt.Errorf("webhook test failed: %w", result.Error)
	}

	return nil
}

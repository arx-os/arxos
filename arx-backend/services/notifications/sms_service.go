package notifications

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"time"
)

// SMSService handles SMS notification delivery
type SMSService struct {
	config    *SMSConfig
	client    *http.Client
	providers map[string]SMSProvider
	rateLimit *RateLimiter
}

// SMSConfig holds SMS service configuration
type SMSConfig struct {
	Providers        map[string]SMSProviderConfig
	DefaultProvider  string
	RateLimit        int // messages per minute
	Timeout          time.Duration
	RetryCount       int
	RetryDelay       time.Duration
	MaxMessageLength int
}

// SMSProviderConfig holds configuration for an SMS provider
type SMSProviderConfig struct {
	Name       string
	APIKey     string
	APISecret  string
	Endpoint   string
	FromNumber string
	Region     string
	Priority   int
}

// SMSProvider interface for different SMS providers
type SMSProvider interface {
	Send(message *SMSMessage) (*SMSResult, error)
	ValidateNumber(number string) bool
	GetName() string
}

// SMSMessage represents an SMS message
type SMSMessage struct {
	To           string
	From         string
	Body         string
	Priority     string
	TemplateID   string
	TemplateData map[string]interface{}
	Provider     string
	MessageID    string
}

// SMSResult represents the result of an SMS send operation
type SMSResult struct {
	Success           bool
	MessageID         string
	Provider          string
	To                string
	SentAt            time.Time
	DeliveredAt       *time.Time
	Error             error
	RetryCount        int
	DeliveryTime      time.Duration
	ProviderMessageID string
	Cost              float64
}

// TwilioProvider implements SMSProvider for Twilio
type TwilioProvider struct {
	config SMSProviderConfig
	client *http.Client
}

// AWSSNSProvider implements SMSProvider for AWS SNS
type AWSSNSProvider struct {
	config SMSProviderConfig
	client *http.Client
}

// CustomProvider implements SMSProvider for custom SMS services
type CustomProvider struct {
	config SMSProviderConfig
	client *http.Client
}

// NewSMSService creates a new SMS service instance
func NewSMSService(config *SMSConfig) (*SMSService, error) {
	if len(config.Providers) == 0 {
		return nil, fmt.Errorf("no SMS providers configured")
	}

	service := &SMSService{
		config:    config,
		client:    &http.Client{Timeout: config.Timeout},
		providers: make(map[string]SMSProvider),
		rateLimit: newRateLimiter(config.RateLimit),
	}

	// Initialize providers
	for name, providerConfig := range config.Providers {
		var provider SMSProvider
		var err error

		switch strings.ToLower(name) {
		case "twilio":
			provider, err = NewTwilioProvider(providerConfig)
		case "aws", "sns":
			provider, err = NewAWSSNSProvider(providerConfig)
		default:
			provider, err = NewCustomProvider(providerConfig)
		}

		if err != nil {
			return nil, fmt.Errorf("failed to initialize provider %s: %w", name, err)
		}

		service.providers[name] = provider
	}

	return service, nil
}

// SendMessage sends an SMS message
func (ss *SMSService) SendMessage(message *SMSMessage) *SMSResult {
	startTime := time.Now()
	result := &SMSResult{
		Success:    false,
		MessageID:  generateSMSMessageID(),
		To:         message.To,
		SentAt:     startTime,
		RetryCount: 0,
	}

	// Validate phone number
	if !ss.validatePhoneNumber(message.To) {
		result.Error = fmt.Errorf("invalid phone number: %s", message.To)
		return result
	}

	// Validate message length
	if len(message.Body) > ss.config.MaxMessageLength {
		result.Error = fmt.Errorf("message too long: %d characters (max: %d)", len(message.Body), ss.config.MaxMessageLength)
		return result
	}

	// Determine provider
	providerName := message.Provider
	if providerName == "" {
		providerName = ss.config.DefaultProvider
	}

	provider, exists := ss.providers[providerName]
	if !exists {
		result.Error = fmt.Errorf("SMS provider %s not found", providerName)
		return result
	}

	result.Provider = providerName

	// Send message with retry logic
	for attempt := 0; attempt <= ss.config.RetryCount; attempt++ {
		if providerResult, err := provider.Send(message); err != nil {
			result.RetryCount = attempt
			if attempt == ss.config.RetryCount {
				result.Error = fmt.Errorf("failed to send SMS after %d attempts: %w", ss.config.RetryCount, err)
				return result
			}
			time.Sleep(ss.config.RetryDelay * time.Duration(attempt+1))
			continue
		} else {
			result.Success = true
			result.DeliveryTime = time.Since(startTime)
			result.ProviderMessageID = providerResult.ProviderMessageID
			result.Cost = providerResult.Cost
			now := time.Now()
			result.DeliveredAt = &now
			break
		}
	}

	return result
}

// SendBulkMessages sends multiple SMS messages efficiently
func (ss *SMSService) SendBulkMessages(messages []*SMSMessage) []*SMSResult {
	results := make([]*SMSResult, len(messages))

	// Process messages in batches to respect rate limits
	batchSize := 10
	for i := 0; i < len(messages); i += batchSize {
		end := i + batchSize
		if end > len(messages) {
			end = len(messages)
		}

		batch := messages[i:end]
		for j, message := range batch {
			results[i+j] = ss.SendMessage(message)
		}

		// Small delay between batches
		if end < len(messages) {
			time.Sleep(100 * time.Millisecond)
		}
	}

	return results
}

// validatePhoneNumber validates a phone number
func (ss *SMSService) validatePhoneNumber(number string) bool {
	// Remove all non-digit characters
	cleanNumber := regexp.MustCompile(`[^\d]`).ReplaceAllString(number, "")

	// Check length (7-15 digits)
	if len(cleanNumber) < 7 || len(cleanNumber) > 15 {
		return false
	}

	return true
}

// Helper functions

func generateSMSMessageID() string {
	return fmt.Sprintf("sms_%d", time.Now().UnixNano())
}

// NewTwilioProvider creates a new Twilio SMS provider
func NewTwilioProvider(config SMSProviderConfig) (*TwilioProvider, error) {
	if config.APIKey == "" || config.APISecret == "" {
		return nil, fmt.Errorf("Twilio API key and secret are required")
	}

	return &TwilioProvider{
		config: config,
		client: &http.Client{Timeout: 30 * time.Second},
	}, nil
}

// Send sends an SMS via Twilio
func (tp *TwilioProvider) Send(message *SMSMessage) (*SMSResult, error) {
	data := url.Values{}
	data.Set("To", message.To)
	data.Set("From", tp.config.FromNumber)
	data.Set("Body", message.Body)

	if message.MessageID != "" {
		data.Set("MessagingServiceSid", message.MessageID)
	}

	req, err := http.NewRequest("POST", tp.config.Endpoint, strings.NewReader(data.Encode()))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.SetBasicAuth(tp.config.APIKey, tp.config.APISecret)
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	resp, err := tp.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		return nil, fmt.Errorf("Twilio API returned status %d", resp.StatusCode)
	}

	var twilioResp struct {
		Sid          string `json:"sid"`
		Status       string `json:"status"`
		ErrorCode    string `json:"error_code,omitempty"`
		ErrorMessage string `json:"error_message,omitempty"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&twilioResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if twilioResp.ErrorCode != "" {
		return nil, fmt.Errorf("Twilio error: %s - %s", twilioResp.ErrorCode, twilioResp.ErrorMessage)
	}

	return &SMSResult{
		Success:           true,
		ProviderMessageID: twilioResp.Sid,
		Cost:              0.0075, // Approximate Twilio cost per message
	}, nil
}

// ValidateNumber validates a phone number for Twilio
func (tp *TwilioProvider) ValidateNumber(number string) bool {
	// Twilio accepts international format
	cleanNumber := regexp.MustCompile(`[^\d+]`).ReplaceAllString(number, "")
	return len(cleanNumber) >= 10 && len(cleanNumber) <= 15
}

// GetName returns the provider name
func (tp *TwilioProvider) GetName() string {
	return "Twilio"
}

// NewAWSSNSProvider creates a new AWS SNS SMS provider
func NewAWSSNSProvider(config SMSProviderConfig) (*AWSSNSProvider, error) {
	if config.APIKey == "" || config.APISecret == "" {
		return nil, fmt.Errorf("AWS access key and secret are required")
	}

	return &AWSSNSProvider{
		config: config,
		client: &http.Client{Timeout: 30 * time.Second},
	}, nil
}

// Send sends an SMS via AWS SNS
func (as *AWSSNSProvider) Send(message *SMSMessage) (*SMSResult, error) {
	// AWS SNS requires AWS SDK for proper implementation
	// This is a simplified version
	payload := map[string]interface{}{
		"Message":     message.Body,
		"PhoneNumber": message.To,
		"MessageAttributes": map[string]interface{}{
			"AWS.SNS.SMS.SMSType": map[string]interface{}{
				"DataType":    "String",
				"StringValue": "Transactional",
			},
		},
	}

	jsonPayload, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal payload: %w", err)
	}

	req, err := http.NewRequest("POST", as.config.Endpoint, bytes.NewBuffer(jsonPayload))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Amz-Date", time.Now().UTC().Format("20060102T150405Z"))

	// Note: In a real implementation, you would need to sign the request with AWS credentials
	// This is a simplified version

	resp, err := as.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("AWS SNS API returned status %d", resp.StatusCode)
	}

	var snsResp struct {
		MessageId string `json:"MessageId"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&snsResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &SMSResult{
		Success:           true,
		ProviderMessageID: snsResp.MessageId,
		Cost:              0.00645, // Approximate AWS SNS cost per message
	}, nil
}

// ValidateNumber validates a phone number for AWS SNS
func (as *AWSSNSProvider) ValidateNumber(number string) bool {
	// AWS SNS accepts international format
	cleanNumber := regexp.MustCompile(`[^\d+]`).ReplaceAllString(number, "")
	return len(cleanNumber) >= 10 && len(cleanNumber) <= 15
}

// GetName returns the provider name
func (as *AWSSNSProvider) GetName() string {
	return "AWS SNS"
}

// NewCustomProvider creates a new custom SMS provider
func NewCustomProvider(config SMSProviderConfig) (*CustomProvider, error) {
	if config.Endpoint == "" {
		return nil, fmt.Errorf("custom provider endpoint is required")
	}

	return &CustomProvider{
		config: config,
		client: &http.Client{Timeout: 30 * time.Second},
	}, nil
}

// Send sends an SMS via custom provider
func (cp *CustomProvider) Send(message *SMSMessage) (*SMSResult, error) {
	payload := map[string]interface{}{
		"to":      message.To,
		"from":    cp.config.FromNumber,
		"message": message.Body,
	}

	jsonPayload, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal payload: %w", err)
	}

	req, err := http.NewRequest("POST", cp.config.Endpoint, bytes.NewBuffer(jsonPayload))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if cp.config.APIKey != "" {
		req.Header.Set("Authorization", "Bearer "+cp.config.APIKey)
	}

	resp, err := cp.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		return nil, fmt.Errorf("custom provider API returned status %d", resp.StatusCode)
	}

	var customResp struct {
		MessageID string `json:"message_id"`
		Status    string `json:"status"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&customResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &SMSResult{
		Success:           true,
		ProviderMessageID: customResp.MessageID,
		Cost:              0.005, // Approximate custom provider cost per message
	}, nil
}

// ValidateNumber validates a phone number for custom provider
func (cp *CustomProvider) ValidateNumber(number string) bool {
	// Custom validation logic
	cleanNumber := regexp.MustCompile(`[^\d]`).ReplaceAllString(number, "")
	return len(cleanNumber) >= 7 && len(cleanNumber) <= 15
}

// GetName returns the provider name
func (cp *CustomProvider) GetName() string {
	return cp.config.Name
}

// GetStatistics returns SMS delivery statistics
func (ss *SMSService) GetStatistics() (*models.SMSStatistics, error) {
	// This would typically query a database for statistics
	// For now, return mock statistics
	return &models.SMSStatistics{
		TotalSent:   200,
		Delivered:   190,
		Failed:      10,
		AverageTime: 1.5,
		SuccessRate: 95.0,
		TotalCost:   1.25,
		LastUpdated: time.Now(),
	}, nil
}

// FormatPhoneNumber formats a phone number for display
func FormatPhoneNumber(number string) string {
	// Remove all non-digit characters
	cleanNumber := regexp.MustCompile(`[^\d]`).ReplaceAllString(number, "")

	if len(cleanNumber) == 10 {
		return fmt.Sprintf("(%s) %s-%s", cleanNumber[:3], cleanNumber[3:6], cleanNumber[6:])
	} else if len(cleanNumber) == 11 && cleanNumber[0] == '1' {
		return fmt.Sprintf("+1 (%s) %s-%s", cleanNumber[1:4], cleanNumber[4:7], cleanNumber[7:])
	}

	return number
}

package notifications

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// NotificationService represents the notification service client
type NotificationService struct {
	baseURL    string
	httpClient *http.Client
}

// NotificationPriority represents notification priority levels
type NotificationPriority string

const (
	NotificationPriorityLow    NotificationPriority = "low"
	NotificationPriorityNormal NotificationPriority = "normal"
	NotificationPriorityHigh   NotificationPriority = "high"
	NotificationPriorityUrgent NotificationPriority = "urgent"
)

// NotificationChannel represents notification channels
type NotificationChannel string

const (
	NotificationChannelEmail   NotificationChannel = "email"
	NotificationChannelSlack   NotificationChannel = "slack"
	NotificationChannelSMS     NotificationChannel = "sms"
	NotificationChannelWebhook NotificationChannel = "webhook"
)

// SMTPConfigRequest represents SMTP configuration request
type SMTPConfigRequest struct {
	Host       string `json:"host"`
	Port       int    `json:"port"`
	Username   string `json:"username"`
	Password   string `json:"password"`
	UseTLS     bool   `json:"use_tls"`
	UseSSL     bool   `json:"use_ssl"`
	Timeout    int    `json:"timeout"`
	MaxRetries int    `json:"max_retries"`
}

// SlackWebhookConfigRequest represents Slack webhook configuration request
type SlackWebhookConfigRequest struct {
	WebhookURL     string `json:"webhook_url"`
	Username       string `json:"username"`
	IconEmoji      string `json:"icon_emoji"`
	Channel        string `json:"channel"`
	Timeout        int    `json:"timeout"`
	MaxRetries     int    `json:"max_retries"`
	RateLimitDelay int    `json:"rate_limit_delay"`
}

// SMSProviderConfigRequest represents SMS provider configuration request
type SMSProviderConfigRequest struct {
	Provider       string `json:"provider"`
	APIKey         string `json:"api_key"`
	APISecret      string `json:"api_secret"`
	FromNumber     string `json:"from_number"`
	WebhookURL     string `json:"webhook_url,omitempty"`
	Timeout        int    `json:"timeout"`
	MaxRetries     int    `json:"max_retries"`
	RateLimitDelay int    `json:"rate_limit_delay"`
}

// WebhookConfigRequest represents webhook configuration request
type WebhookConfigRequest struct {
	URL            string            `json:"url"`
	Method         string            `json:"method"`
	Headers        map[string]string `json:"headers"`
	Timeout        int               `json:"timeout"`
	MaxRetries     int               `json:"max_retries"`
	RateLimitDelay int               `json:"rate_limit_delay"`
	AuthToken      string            `json:"auth_token,omitempty"`
}

// EmailNotificationRequest represents email notification request
type EmailNotificationRequest struct {
	To           string                 `json:"to"`
	Subject      string                 `json:"subject"`
	Body         string                 `json:"body"`
	FromAddress  string                 `json:"from_address,omitempty"`
	HTMLBody     string                 `json:"html_body,omitempty"`
	Priority     NotificationPriority   `json:"priority"`
	TemplateID   string                 `json:"template_id,omitempty"`
	TemplateData map[string]interface{} `json:"template_data,omitempty"`
}

// SlackNotificationRequest represents Slack notification request
type SlackNotificationRequest struct {
	Text        string                   `json:"text"`
	Channel     string                   `json:"channel,omitempty"`
	Username    string                   `json:"username,omitempty"`
	IconEmoji   string                   `json:"icon_emoji,omitempty"`
	Attachments []map[string]interface{} `json:"attachments,omitempty"`
	Blocks      []map[string]interface{} `json:"blocks,omitempty"`
	ThreadTS    string                   `json:"thread_ts,omitempty"`
}

// SMSNotificationRequest represents SMS notification request
type SMSNotificationRequest struct {
	To         string `json:"to"`
	Body       string `json:"body"`
	FromNumber string `json:"from_number,omitempty"`
}

// WebhookNotificationRequest represents webhook notification request
type WebhookNotificationRequest struct {
	URL     string                 `json:"url"`
	Payload map[string]interface{} `json:"payload"`
	Method  string                 `json:"method"`
	Headers map[string]string      `json:"headers,omitempty"`
}

// UnifiedNotificationRequest represents unified notification request
type UnifiedNotificationRequest struct {
	Title        string                 `json:"title"`
	Message      string                 `json:"message"`
	Channels     []NotificationChannel  `json:"channels"`
	Priority     NotificationPriority   `json:"priority"`
	TemplateData map[string]interface{} `json:"template_data,omitempty"`
}

// NotificationResponse represents notification response
type NotificationResponse struct {
	Success      bool                   `json:"success"`
	MessageID    string                 `json:"message_id"`
	Status       string                 `json:"status"`
	SentAt       *time.Time             `json:"sent_at,omitempty"`
	DeliveredAt  *time.Time             `json:"delivered_at,omitempty"`
	ErrorMessage string                 `json:"error_message,omitempty"`
	Metadata     map[string]interface{} `json:"metadata"`
}

// ConfigurationResponse represents configuration response
type ConfigurationResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Service string `json:"service"`
}

// NotificationStatistics represents notification statistics
type NotificationStatistics struct {
	TotalNotifications      int            `json:"total_notifications"`
	SuccessfulNotifications int            `json:"successful_notifications"`
	FailedNotifications     int            `json:"failed_notifications"`
	ChannelUsage            map[string]int `json:"channel_usage"`
	PriorityUsage           map[string]int `json:"priority_usage"`
	AverageDeliveryTime     float64        `json:"average_delivery_time"`
}

// NewNotificationService creates a new notification service client
func NewNotificationService(baseURL string) *NotificationService {
	return &NotificationService{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// ConfigureEmail configures the email service
func (ns *NotificationService) ConfigureEmail(config *SMTPConfigRequest) (*ConfigurationResponse, error) {
	jsonData, err := json.Marshal(config)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal email config: %w", err)
	}

	url := fmt.Sprintf("%s/config/email", ns.baseURL)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("email configuration failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result ConfigurationResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// ConfigureSlack configures the Slack service
func (ns *NotificationService) ConfigureSlack(config *SlackWebhookConfigRequest) (*ConfigurationResponse, error) {
	jsonData, err := json.Marshal(config)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal Slack config: %w", err)
	}

	url := fmt.Sprintf("%s/config/slack", ns.baseURL)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("Slack configuration failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result ConfigurationResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// ConfigureSMS configures the SMS service
func (ns *NotificationService) ConfigureSMS(config *SMSProviderConfigRequest) (*ConfigurationResponse, error) {
	jsonData, err := json.Marshal(config)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal SMS config: %w", err)
	}

	url := fmt.Sprintf("%s/config/sms", ns.baseURL)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("SMS configuration failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result ConfigurationResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// ConfigureWebhook configures the webhook service
func (ns *NotificationService) ConfigureWebhook(config *WebhookConfigRequest) (*ConfigurationResponse, error) {
	jsonData, err := json.Marshal(config)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal webhook config: %w", err)
	}

	url := fmt.Sprintf("%s/config/webhook", ns.baseURL)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("webhook configuration failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result ConfigurationResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// SendEmailNotification sends an email notification
func (ns *NotificationService) SendEmailNotification(request *EmailNotificationRequest) (*NotificationResponse, error) {
	jsonData, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal email request: %w", err)
	}

	url := fmt.Sprintf("%s/notifications/email", ns.baseURL)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("email notification failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result NotificationResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// GetEmailNotification gets an email notification by ID
func (ns *NotificationService) GetEmailNotification(messageID string) (*NotificationResponse, error) {
	url := fmt.Sprintf("%s/notifications/email/%s", ns.baseURL, messageID)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("get email notification failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result NotificationResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// GetEmailStatistics gets email statistics
func (ns *NotificationService) GetEmailStatistics() (*NotificationStatistics, error) {
	url := fmt.Sprintf("%s/notifications/email/statistics", ns.baseURL)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("get email statistics failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result NotificationStatistics
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// SendSlackNotification sends a Slack notification
func (ns *NotificationService) SendSlackNotification(request *SlackNotificationRequest) (*NotificationResponse, error) {
	jsonData, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal Slack request: %w", err)
	}

	url := fmt.Sprintf("%s/notifications/slack", ns.baseURL)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("Slack notification failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result NotificationResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// GetSlackNotification gets a Slack notification by ID
func (ns *NotificationService) GetSlackNotification(messageID string) (*NotificationResponse, error) {
	url := fmt.Sprintf("%s/notifications/slack/%s", ns.baseURL, messageID)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("get Slack notification failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result NotificationResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// GetSlackStatistics gets Slack statistics
func (ns *NotificationService) GetSlackStatistics() (*NotificationStatistics, error) {
	url := fmt.Sprintf("%s/notifications/slack/statistics", ns.baseURL)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("get Slack statistics failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result NotificationStatistics
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// SendSMSNotification sends an SMS notification
func (ns *NotificationService) SendSMSNotification(request *SMSNotificationRequest) (*NotificationResponse, error) {
	jsonData, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal SMS request: %w", err)
	}

	url := fmt.Sprintf("%s/notifications/sms", ns.baseURL)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("SMS notification failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result NotificationResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// GetSMSNotification gets an SMS notification by ID
func (ns *NotificationService) GetSMSNotification(messageID string) (*NotificationResponse, error) {
	url := fmt.Sprintf("%s/notifications/sms/%s", ns.baseURL, messageID)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("get SMS notification failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result NotificationResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// GetSMSStatistics gets SMS statistics
func (ns *NotificationService) GetSMSStatistics() (*NotificationStatistics, error) {
	url := fmt.Sprintf("%s/notifications/sms/statistics", ns.baseURL)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("get SMS statistics failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result NotificationStatistics
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// SendWebhookNotification sends a webhook notification
func (ns *NotificationService) SendWebhookNotification(request *WebhookNotificationRequest) (*NotificationResponse, error) {
	jsonData, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal webhook request: %w", err)
	}

	url := fmt.Sprintf("%s/notifications/webhook", ns.baseURL)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("webhook notification failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result NotificationResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// GetWebhookNotification gets a webhook notification by ID
func (ns *NotificationService) GetWebhookNotification(messageID string) (*NotificationResponse, error) {
	url := fmt.Sprintf("%s/notifications/webhook/%s", ns.baseURL, messageID)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("get webhook notification failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result NotificationResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// GetWebhookStatistics gets webhook statistics
func (ns *NotificationService) GetWebhookStatistics() (*NotificationStatistics, error) {
	url := fmt.Sprintf("%s/notifications/webhook/statistics", ns.baseURL)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("get webhook statistics failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result NotificationStatistics
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// SendUnifiedNotification sends a unified notification to multiple channels
func (ns *NotificationService) SendUnifiedNotification(request *UnifiedNotificationRequest) ([]NotificationResponse, error) {
	jsonData, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal unified request: %w", err)
	}

	url := fmt.Sprintf("%s/notifications/unified", ns.baseURL)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unified notification failed with status %d: %s", resp.StatusCode, string(body))
	}

	var results []NotificationResponse
	if err := json.Unmarshal(body, &results); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return results, nil
}

// GetUnifiedStatistics gets unified notification statistics
func (ns *NotificationService) GetUnifiedStatistics() (*NotificationStatistics, error) {
	url := fmt.Sprintf("%s/notifications/unified/statistics", ns.baseURL)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("get unified statistics failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result NotificationStatistics
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return &result, nil
}

// HealthCheck performs a health check on the notification service
func (ns *NotificationService) HealthCheck() (map[string]interface{}, error) {
	url := fmt.Sprintf("%s/health", ns.baseURL)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := ns.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("health check failed with status %d: %s", resp.StatusCode, string(body))
	}

	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w", err)
	}

	return result, nil
}

package notifications

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// SlackService handles Slack notification delivery
type SlackService struct {
	config    *SlackConfig
	client    *http.Client
	rateLimit *RateLimiter
}

// SlackConfig holds Slack service configuration
type SlackConfig struct {
	WebhookURLs map[string]string // channel -> webhook URL
	DefaultURL  string
	RateLimit   int // requests per minute
	Timeout     time.Duration
	RetryCount  int
	RetryDelay  time.Duration
}

// SlackMessage represents a Slack message
type SlackMessage struct {
	Channel        string
	Text           string
	Username       string
	IconEmoji      string
	IconURL        string
	Attachments    []SlackAttachment
	Blocks         []SlackBlock
	ThreadTS       string
	ReplyBroadcast bool
}

// SlackAttachment represents a Slack message attachment
type SlackAttachment struct {
	Color      string       `json:"color,omitempty"`
	Pretext    string       `json:"pretext,omitempty"`
	AuthorName string       `json:"author_name,omitempty"`
	AuthorLink string       `json:"author_link,omitempty"`
	AuthorIcon string       `json:"author_icon,omitempty"`
	Title      string       `json:"title,omitempty"`
	TitleLink  string       `json:"title_link,omitempty"`
	Text       string       `json:"text,omitempty"`
	Fields     []SlackField `json:"fields,omitempty"`
	ImageURL   string       `json:"image_url,omitempty"`
	ThumbURL   string       `json:"thumb_url,omitempty"`
	Footer     string       `json:"footer,omitempty"`
	FooterIcon string       `json:"footer_icon,omitempty"`
	Timestamp  int64        `json:"ts,omitempty"`
}

// SlackField represents a field in a Slack attachment
type SlackField struct {
	Title string `json:"title"`
	Value string `json:"value"`
	Short bool   `json:"short"`
}

// SlackBlock represents a Slack block element
type SlackBlock struct {
	Type      string          `json:"type"`
	Text      *SlackText      `json:"text,omitempty"`
	Fields    []SlackText     `json:"fields,omitempty"`
	Accessory *SlackAccessory `json:"accessory,omitempty"`
}

// SlackText represents text in a Slack block
type SlackText struct {
	Type  string `json:"type"`
	Text  string `json:"text"`
	Emoji bool   `json:"emoji,omitempty"`
}

// SlackAccessory represents an accessory in a Slack block
type SlackAccessory struct {
	Type string    `json:"type"`
	Text SlackText `json:"text,omitempty"`
	URL  string    `json:"url,omitempty"`
}

// SlackResult represents the result of a Slack message send operation
type SlackResult struct {
	Success      bool
	MessageID    string
	Channel      string
	SentAt       time.Time
	DeliveredAt  *time.Time
	Error        error
	RetryCount   int
	DeliveryTime time.Duration
	Response     *SlackResponse
}

// SlackResponse represents the response from Slack API
type SlackResponse struct {
	OK      bool   `json:"ok"`
	Error   string `json:"error,omitempty"`
	Warning string `json:"warning,omitempty"`
	TS      string `json:"ts,omitempty"`
}

// RateLimiter handles rate limiting for Slack API
type RateLimiter struct {
	requests chan struct{}
	ticker   *time.Ticker
}

// NewSlackService creates a new Slack service instance
func NewSlackService(config *SlackConfig) (*SlackService, error) {
	if config.DefaultURL == "" && len(config.WebhookURLs) == 0 {
		return nil, fmt.Errorf("no Slack webhook URLs configured")
	}

	service := &SlackService{
		config: config,
		client: &http.Client{
			Timeout: config.Timeout,
		},
		rateLimit: newRateLimiter(config.RateLimit),
	}

	return service, nil
}

// SendMessage sends a Slack message
func (ss *SlackService) SendMessage(message *SlackMessage) *SlackResult {
	startTime := time.Now()
	result := &SlackResult{
		Success:    false,
		MessageID:  generateSlackMessageID(),
		Channel:    message.Channel,
		SentAt:     startTime,
		RetryCount: 0,
	}

	// Get webhook URL for channel
	webhookURL := ss.getWebhookURL(message.Channel)
	if webhookURL == "" {
		result.Error = fmt.Errorf("no webhook URL found for channel %s", message.Channel)
		return result
	}

	// Prepare message payload
	payload, err := ss.prepareMessagePayload(message)
	if err != nil {
		result.Error = fmt.Errorf("failed to prepare message payload: %w", err)
		return result
	}

	// Send message with retry logic
	for attempt := 0; attempt <= ss.config.RetryCount; attempt++ {
		if response, err := ss.sendMessageWithRetry(webhookURL, payload); err != nil {
			result.RetryCount = attempt
			if attempt == ss.config.RetryCount {
				result.Error = fmt.Errorf("failed to send Slack message after %d attempts: %w", ss.config.RetryCount, err)
				return result
			}
			time.Sleep(ss.config.RetryDelay * time.Duration(attempt+1))
			continue
		} else {
			result.Success = true
			result.DeliveryTime = time.Since(startTime)
			result.Response = response
			now := time.Now()
			result.DeliveredAt = &now
			break
		}
	}

	return result
}

// prepareMessagePayload prepares the Slack message payload
func (ss *SlackService) prepareMessagePayload(message *SlackMessage) ([]byte, error) {
	payload := map[string]interface{}{
		"text": message.Text,
	}

	if message.Username != "" {
		payload["username"] = message.Username
	}

	if message.IconEmoji != "" {
		payload["icon_emoji"] = message.IconEmoji
	}

	if message.IconURL != "" {
		payload["icon_url"] = message.IconURL
	}

	if len(message.Attachments) > 0 {
		payload["attachments"] = message.Attachments
	}

	if len(message.Blocks) > 0 {
		payload["blocks"] = message.Blocks
	}

	if message.ThreadTS != "" {
		payload["thread_ts"] = message.ThreadTS
	}

	if message.ReplyBroadcast {
		payload["reply_broadcast"] = true
	}

	return json.Marshal(payload)
}

// sendMessageWithRetry sends a Slack message with retry logic
func (ss *SlackService) sendMessageWithRetry(webhookURL string, payload []byte) (*SlackResponse, error) {
	// Wait for rate limiter
	ss.rateLimit.wait()

	req, err := http.NewRequest("POST", webhookURL, bytes.NewBuffer(payload))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := ss.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("Slack API returned status %d", resp.StatusCode)
	}

	var slackResp SlackResponse
	if err := json.NewDecoder(resp.Body).Decode(&slackResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !slackResp.OK {
		return &slackResp, fmt.Errorf("Slack API error: %s", slackResp.Error)
	}

	return &slackResp, nil
}

// SendBulkMessages sends multiple Slack messages efficiently
func (ss *SlackService) SendBulkMessages(messages []*SlackMessage) []*SlackResult {
	results := make([]*SlackResult, len(messages))

	// Process messages in batches to respect rate limits
	batchSize := 5
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
			time.Sleep(200 * time.Millisecond)
		}
	}

	return results
}

// CreateSimpleMessage creates a simple text message
func (ss *SlackService) CreateSimpleMessage(channel, text string) *SlackMessage {
	return &SlackMessage{
		Channel: channel,
		Text:    text,
	}
}

// CreateAlertMessage creates an alert message with attachments
func (ss *SlackService) CreateAlertMessage(channel, title, text, severity string) *SlackMessage {
	color := "good"
	if severity == "warning" {
		color = "warning"
	} else if severity == "error" {
		color = "danger"
	}

	return &SlackMessage{
		Channel: channel,
		Text:    title,
		Attachments: []SlackAttachment{
			{
				Color: color,
				Text:  text,
				Title: title,
			},
		},
	}
}

// CreateNotificationMessage creates a notification message
func (ss *SlackService) CreateNotificationMessage(channel, title, text string, fields map[string]string) *SlackMessage {
	slackFields := make([]SlackField, 0, len(fields))
	for key, value := range fields {
		slackFields = append(slackFields, SlackField{
			Title: key,
			Value: value,
			Short: true,
		})
	}

	return &SlackMessage{
		Channel: channel,
		Text:    title,
		Attachments: []SlackAttachment{
			{
				Color:  "good",
				Text:   text,
				Title:  title,
				Fields: slackFields,
			},
		},
	}
}

// Helper functions

func generateSlackMessageID() string {
	return fmt.Sprintf("slack_%d", time.Now().UnixNano())
}

func (ss *SlackService) getWebhookURL(channel string) string {
	if url, exists := ss.config.WebhookURLs[channel]; exists {
		return url
	}
	return ss.config.DefaultURL
}

func newRateLimiter(requestsPerMinute int) *RateLimiter {
	rl := &RateLimiter{
		requests: make(chan struct{}, requestsPerMinute),
		ticker:   time.NewTicker(time.Minute / time.Duration(requestsPerMinute)),
	}

	// Fill the channel initially
	for i := 0; i < requestsPerMinute; i++ {
		rl.requests <- struct{}{}
	}

	go func() {
		for range rl.ticker.C {
			select {
			case rl.requests <- struct{}{}:
			default:
				// Channel is full, skip
			}
		}
	}()

	return rl
}

func (rl *RateLimiter) wait() {
	<-rl.requests
}

// GetStatistics returns Slack delivery statistics
func (ss *SlackService) GetStatistics() (*models.SlackStatistics, error) {
	// This would typically query a database for statistics
	// For now, return mock statistics
	return &models.SlackStatistics{
		TotalSent:   500,
		Delivered:   480,
		Failed:      20,
		AverageTime: 1.2,
		SuccessRate: 96.0,
		LastUpdated: time.Now(),
	}, nil
}

// ValidateChannel validates a Slack channel name
func ValidateChannel(channel string) bool {
	if len(channel) == 0 || len(channel) > 21 {
		return false
	}

	// Check for valid channel format
	if channel[0] != '#' && channel[0] != '@' {
		return false
	}

	// Check for valid characters
	for _, char := range channel[1:] {
		if !((char >= 'a' && char <= 'z') || (char >= '0' && char <= '9') || char == '-' || char == '_') {
			return false
		}
	}

	return true
}

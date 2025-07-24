package notifications

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// SlackAppService handles Slack app integration with OAuth2
type SlackAppService struct {
	config    *SlackAppConfig
	client    *http.Client
	rateLimit *RateLimiter
	oauth2    *SlackOAuth2Config
}

// SlackAppConfig holds Slack app configuration
type SlackAppConfig struct {
	ClientID     string
	ClientSecret string
	RedirectURI  string
	Scopes       []string
	RateLimit    int // requests per minute
	Timeout      time.Duration
	RetryCount   int
	RetryDelay   time.Duration
}

// SlackOAuth2Config holds OAuth2 configuration
type SlackOAuth2Config struct {
	AccessToken  string
	RefreshToken string
	TokenType    string
	ExpiresIn    int
	Scope        string
	TeamID       string
	TeamName     string
	UserID       string
	UserName     string
}

// SlackAppMessage represents a Slack app message
type SlackAppMessage struct {
	Channel        string
	Text           string
	Username       string
	IconEmoji      string
	IconURL        string
	Attachments    []SlackAttachment
	Blocks         []SlackBlock
	ThreadTS       string
	ReplyBroadcast bool
	UnfurlLinks    bool
	UnfurlMedia    bool
}

// SlackAppResult represents the result of a Slack app message send operation
type SlackAppResult struct {
	Success      bool
	MessageID    string
	Channel      string
	TS           string
	SentAt       time.Time
	DeliveredAt  *time.Time
	Error        error
	RetryCount   int
	DeliveryTime time.Duration
	Response     *SlackAppResponse
}

// SlackAppResponse represents Slack API response
type SlackAppResponse struct {
	OK      bool   `json:"ok"`
	Error   string `json:"error,omitempty"`
	Warning string `json:"warning,omitempty"`
	TS      string `json:"ts,omitempty"`
	Channel string `json:"channel,omitempty"`
	Message struct {
		TS   string `json:"ts"`
		Text string `json:"text"`
	} `json:"message,omitempty"`
}

// NewSlackAppService creates a new Slack app service
func NewSlackAppService(config *SlackAppConfig) *SlackAppService {
	return &SlackAppService{
		config: config,
		client: &http.Client{
			Timeout: config.Timeout,
		},
		rateLimit: newRateLimiter(config.RateLimit),
	}
}

// GetOAuthURL generates OAuth2 authorization URL
func (sas *SlackAppService) GetOAuthURL(state string) string {
	params := url.Values{}
	params.Set("client_id", sas.config.ClientID)
	params.Set("scope", strings.Join(sas.config.Scopes, ","))
	params.Set("redirect_uri", sas.config.RedirectURI)
	params.Set("state", state)

	return fmt.Sprintf("https://slack.com/oauth/v2/authorize?%s", params.Encode())
}

// ExchangeCodeForToken exchanges authorization code for access token
func (sas *SlackAppService) ExchangeCodeForToken(code string) (*SlackOAuth2Config, error) {
	data := url.Values{}
	data.Set("client_id", sas.config.ClientID)
	data.Set("client_secret", sas.config.ClientSecret)
	data.Set("code", code)
	data.Set("redirect_uri", sas.config.RedirectURI)

	resp, err := sas.client.PostForm("https://slack.com/api/oauth.v2.access", data)
	if err != nil {
		return nil, fmt.Errorf("failed to exchange code for token: %w", err)
	}
	defer resp.Body.Close()

	var result struct {
		OK          bool   `json:"ok"`
		Error       string `json:"error,omitempty"`
		AccessToken string `json:"access_token,omitempty"`
		TokenType   string `json:"token_type,omitempty"`
		Scope       string `json:"scope,omitempty"`
		Team        struct {
			ID   string `json:"id"`
			Name string `json:"name"`
		} `json:"team,omitempty"`
		AuthedUser struct {
			ID   string `json:"id"`
			Name string `json:"name"`
		} `json:"authed_user,omitempty"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !result.OK {
		return nil, fmt.Errorf("Slack API error: %s", result.Error)
	}

	sas.oauth2 = &SlackOAuth2Config{
		AccessToken: result.AccessToken,
		TokenType:   result.TokenType,
		Scope:       result.Scope,
		TeamID:      result.Team.ID,
		TeamName:    result.Team.Name,
		UserID:      result.AuthedUser.ID,
		UserName:    result.AuthedUser.Name,
	}

	return sas.oauth2, nil
}

// SendMessage sends a message using Slack app API
func (sas *SlackAppService) SendMessage(message *SlackAppMessage) *SlackAppResult {
	startTime := time.Now()
	messageID := generateSlackMessageID()

	// Rate limiting
	sas.rateLimit.wait()

	// Prepare message payload
	payload, err := sas.prepareAppMessagePayload(message)
	if err != nil {
		return &SlackAppResult{
			Success:    false,
			MessageID:  messageID,
			Channel:    message.Channel,
			SentAt:     time.Now(),
			Error:      err,
			RetryCount: 0,
		}
	}

	// Send message with retry logic
	var lastError error
	var response *SlackAppResponse

	for attempt := 0; attempt <= sas.config.RetryCount; attempt++ {
		response, err = sas.sendAppMessageWithRetry(payload)
		if err != nil {
			lastError = err
			if attempt < sas.config.RetryCount {
				time.Sleep(sas.config.RetryDelay * time.Duration(attempt+1))
				continue
			}
		} else {
			// Success
			deliveryTime := time.Since(startTime)
			return &SlackAppResult{
				Success:      true,
				MessageID:    messageID,
				Channel:      message.Channel,
				TS:           response.TS,
				SentAt:       time.Now(),
				DeliveryTime: deliveryTime,
				RetryCount:   attempt,
				Response:     response,
			}
		}
	}

	// All retries failed
	return &SlackAppResult{
		Success:    false,
		MessageID:  messageID,
		Channel:    message.Channel,
		SentAt:     time.Now(),
		Error:      lastError,
		RetryCount: sas.config.RetryCount,
	}
}

// prepareAppMessagePayload prepares message payload for Slack app API
func (sas *SlackAppService) prepareAppMessagePayload(message *SlackAppMessage) ([]byte, error) {
	payload := map[string]interface{}{
		"channel": message.Channel,
		"text":    message.Text,
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

	payload["unfurl_links"] = message.UnfurlLinks
	payload["unfurl_media"] = message.UnfurlMedia

	return json.Marshal(payload)
}

// sendAppMessageWithRetry sends message with retry logic
func (sas *SlackAppService) sendAppMessageWithRetry(payload []byte) (*SlackAppResponse, error) {
	if sas.oauth2 == nil {
		return nil, fmt.Errorf("OAuth2 not configured")
	}

	req, err := http.NewRequest("POST", "https://slack.com/api/chat.postMessage", bytes.NewBuffer(payload))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", sas.oauth2.AccessToken))

	resp, err := sas.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("Slack API returned status: %d", resp.StatusCode)
	}

	var response SlackAppResponse
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	if !response.OK {
		return nil, fmt.Errorf("Slack API error: %s", response.Error)
	}

	return &response, nil
}

// SendBulkMessages sends multiple messages with rate limiting
func (sas *SlackAppService) SendBulkMessages(messages []*SlackAppMessage) []*SlackAppResult {
	results := make([]*SlackAppResult, len(messages))

	for i, message := range messages {
		results[i] = sas.SendMessage(message)
	}

	return results
}

// CreateSimpleMessage creates a simple text message
func (sas *SlackAppService) CreateSimpleMessage(channel, text string) *SlackAppMessage {
	return &SlackAppMessage{
		Channel:     channel,
		Text:        text,
		UnfurlLinks: true,
		UnfurlMedia: true,
	}
}

// CreateAlertMessage creates an alert message with attachments
func (sas *SlackAppService) CreateAlertMessage(channel, title, text, severity string) *SlackAppMessage {
	color := "good"
	if severity == "warning" {
		color = "warning"
	} else if severity == "error" {
		color = "danger"
	}

	attachment := SlackAttachment{
		Color: color,
		Title: title,
		Text:  text,
		Fields: []SlackField{
			{Title: "Severity", Value: severity, Short: true},
			{Title: "Time", Value: time.Now().Format("2006-01-02 15:04:05"), Short: true},
		},
	}

	return &SlackAppMessage{
		Channel:     channel,
		Text:        title,
		Attachments: []SlackAttachment{attachment},
		UnfurlLinks: false,
		UnfurlMedia: false,
	}
}

// CreateNotificationMessage creates a notification message with fields
func (sas *SlackAppService) CreateNotificationMessage(channel, title, text string, fields map[string]string) *SlackAppMessage {
	slackFields := make([]SlackField, 0, len(fields))
	for key, value := range fields {
		slackFields = append(slackFields, SlackField{
			Title: key,
			Value: value,
			Short: len(value) < 30,
		})
	}

	attachment := SlackAttachment{
		Color:  "good",
		Title:  title,
		Text:   text,
		Fields: slackFields,
	}

	return &SlackAppMessage{
		Channel:     channel,
		Text:        title,
		Attachments: []SlackAttachment{attachment},
		UnfurlLinks: false,
		UnfurlMedia: false,
	}
}

// GetTeamInfo gets team information
func (sas *SlackAppService) GetTeamInfo() (map[string]interface{}, error) {
	if sas.oauth2 == nil {
		return nil, fmt.Errorf("OAuth2 not configured")
	}

	req, err := http.NewRequest("GET", "https://slack.com/api/team.info", nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", sas.oauth2.AccessToken))

	resp, err := sas.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return result, nil
}

// GetChannelsList gets list of channels
func (sas *SlackAppService) GetChannelsList() (map[string]interface{}, error) {
	if sas.oauth2 == nil {
		return nil, fmt.Errorf("OAuth2 not configured")
	}

	req, err := http.NewRequest("GET", "https://slack.com/api/conversations.list", nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", sas.oauth2.AccessToken))

	resp, err := sas.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return result, nil
}

// GetStatistics gets Slack app statistics
func (sas *SlackAppService) GetStatistics() (map[string]interface{}, error) {
	// This would typically query a database
	// For now, return mock statistics
	return map[string]interface{}{
		"total_sent":            500,
		"total_delivered":       480,
		"total_failed":          20,
		"success_rate":          96.0,
		"average_delivery_time": 1.2,
		"team_id":               sas.oauth2.TeamID,
		"team_name":             sas.oauth2.TeamName,
	}, nil
}

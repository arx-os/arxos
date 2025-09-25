package email

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// SendGridClient implements EmailClient using SendGrid API
type SendGridClient struct {
	config Config
	client *http.Client
}

// NewSendGridClient creates a new SendGrid email client
func NewSendGridClient(config Config) (EmailClient, error) {
	if config.APIKey == "" {
		return nil, fmt.Errorf("SendGrid API key is required")
	}
	if config.FromEmail == "" {
		return nil, fmt.Errorf("from email is required")
	}

	return &SendGridClient{
		config: config,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}, nil
}

// Send sends a plain text email via SendGrid
func (c *SendGridClient) Send(ctx context.Context, to, subject, body string) error {
	return c.sendEmail(ctx, to, subject, body, "")
}

// SendHTML sends an HTML email via SendGrid
func (c *SendGridClient) SendHTML(ctx context.Context, to, subject, htmlBody, textBody string) error {
	return c.sendEmail(ctx, to, subject, htmlBody, textBody)
}

// sendEmail sends an email via SendGrid API
func (c *SendGridClient) sendEmail(ctx context.Context, to, subject, htmlBody, textBody string) error {
	// Create SendGrid message
	message := map[string]interface{}{
		"personalizations": []map[string]interface{}{
			{
				"to": []map[string]string{
					{"email": to},
				},
			},
		},
		"from": map[string]string{
			"email": c.config.FromEmail,
			"name":  c.config.FromName,
		},
		"subject": subject,
	}

	// Add content based on what's provided
	content := []map[string]string{}
	if textBody != "" {
		content = append(content, map[string]string{
			"type":  "text/plain",
			"value": textBody,
		})
	}
	if htmlBody != "" {
		content = append(content, map[string]string{
			"type":  "text/html",
			"value": htmlBody,
		})
	}

	if len(content) > 0 {
		message["content"] = content
	}

	// Convert to JSON
	payload, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("failed to marshal SendGrid message: %w", err)
	}

	// Create HTTP request
	req, err := http.NewRequestWithContext(ctx, "POST",
		"https://api.sendgrid.com/v3/mail/send",
		bytes.NewBuffer(payload))
	if err != nil {
		return fmt.Errorf("failed to create SendGrid request: %w", err)
	}

	// Set headers
	req.Header.Set("Authorization", "Bearer "+c.config.APIKey)
	req.Header.Set("Content-Type", "application/json")

	// Send request
	resp, err := c.client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send email via SendGrid: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("SendGrid returned error status %d: %s", resp.StatusCode, string(body))
	}

	return nil
}

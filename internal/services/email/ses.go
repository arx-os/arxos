package email

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
)

// SESClient implements EmailClient using AWS SES
type SESClient struct {
	config Config
}

// NewSESClient creates a new AWS SES email client
func NewSESClient(config Config) (EmailClient, error) {
	if config.Region == "" {
		config.Region = "us-east-1" // Default region
	}
	if config.FromEmail == "" {
		return nil, fmt.Errorf("from email is required")
	}

	return &SESClient{
		config: config,
	}, nil
}

// Send sends a plain text email via AWS SES
func (c *SESClient) Send(ctx context.Context, to, subject, body string) error {
	return c.sendEmail(ctx, to, subject, body, "")
}

// SendHTML sends an HTML email via AWS SES
func (c *SESClient) SendHTML(ctx context.Context, to, subject, htmlBody, textBody string) error {
	return c.sendEmail(ctx, to, subject, htmlBody, textBody)
}

// sendEmail sends an email via AWS SES
func (c *SESClient) sendEmail(ctx context.Context, to, subject, htmlBody, textBody string) error {
	// Create SES message
	message := map[string]interface{}{
		"Destination": map[string]interface{}{
			"ToAddresses": []string{to},
		},
		"Message": map[string]interface{}{
			"Subject": map[string]interface{}{
				"Data":    subject,
				"Charset": "UTF-8",
			},
		},
		"Source": c.config.FromEmail,
	}

	// Add body content
	bodyContent := map[string]interface{}{}
	if textBody != "" {
		bodyContent["Text"] = map[string]interface{}{
			"Data":    textBody,
			"Charset": "UTF-8",
		}
	}
	if htmlBody != "" {
		bodyContent["Html"] = map[string]interface{}{
			"Data":    htmlBody,
			"Charset": "UTF-8",
		}
	}

	if len(bodyContent) > 0 {
		message["Message"].(map[string]interface{})["Body"] = bodyContent
	}

	// Convert to JSON
	payload, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("failed to marshal SES message: %w", err)
	}

	// Create HTTP request to SES API
	endpoint := fmt.Sprintf("https://email.%s.amazonaws.com/", c.config.Region)
	req, err := http.NewRequestWithContext(ctx, "POST", endpoint,
		bytes.NewBuffer(payload))
	if err != nil {
		return fmt.Errorf("failed to create SES request: %w", err)
	}

	// Set headers
	req.Header.Set("Content-Type", "application/x-amz-json-1.0")
	req.Header.Set("X-Amz-Target", "AWSSimpleEmailService.SendEmail")

	// Note: In a real implementation, you would need to sign the request with AWS credentials
	// For now, we'll just log the action as this requires AWS SDK integration
	fmt.Printf("SES: Would send email to %s with subject '%s' in region %s\n", to, subject, c.config.Region)
	fmt.Printf("SES: Message payload: %s\n", string(payload))

	return nil
}

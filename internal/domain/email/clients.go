package email

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/smtp"
	"time"
)

// SMTPClient implements EmailClient using SMTP
type SMTPClient struct {
	config Config
	auth   smtp.Auth
}

// NewSMTPClient creates a new SMTP email client
func NewSMTPClient(config Config) (EmailClient, error) {
	if config.SMTPHost == "" {
		return nil, fmt.Errorf("SMTP host is required")
	}
	if config.SMTPPort == 0 {
		config.SMTPPort = 587 // Default to port 587
	}
	if config.FromEmail == "" {
		return nil, fmt.Errorf("from email is required")
	}

	var auth smtp.Auth
	if config.SMTPUsername != "" && config.SMTPPassword != "" {
		auth = smtp.PlainAuth("", config.SMTPUsername, config.SMTPPassword, config.SMTPHost)
	}

	return &SMTPClient{
		config: config,
		auth:   auth,
	}, nil
}

// Send sends a plain text email
func (c *SMTPClient) Send(ctx context.Context, to, subject, body string) error {
	return c.sendEmail(ctx, to, subject, body, "")
}

// SendHTML sends an HTML email with optional text fallback
func (c *SMTPClient) SendHTML(ctx context.Context, to, subject, htmlBody, textBody string) error {
	// Create multipart email body
	boundary := fmt.Sprintf("boundary_%d", time.Now().Unix())

	body := fmt.Sprintf(`MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="%s"

--%s
Content-Type: text/plain; charset=UTF-8

%s

--%s
Content-Type: text/html; charset=UTF-8

%s

--%s--
`, boundary, boundary, textBody, boundary, htmlBody, boundary)

	return c.sendEmail(ctx, to, subject, body, "multipart/alternative")
}

// SendWithAttachments sends an email with attachments
func (c *SMTPClient) SendWithAttachments(ctx context.Context, to, subject, htmlBody, textBody string, attachments []Attachment) error {
	// TODO: Implement attachment support for SMTP
	// For now, just send HTML email without attachments
	return c.SendHTML(ctx, to, subject, htmlBody, textBody)
}

// sendEmail sends an email using SMTP
func (c *SMTPClient) sendEmail(ctx context.Context, to, subject, body, contentType string) error {
	// Create email message
	fromName := c.config.FromName
	if fromName == "" {
		fromName = "ArxOS"
	}

	message := fmt.Sprintf("From: %s <%s>\r\n", fromName, c.config.FromEmail)
	message += fmt.Sprintf("To: %s\r\n", to)
	message += fmt.Sprintf("Subject: %s\r\n", subject)
	message += "Date: " + time.Now().Format(time.RFC1123Z) + "\r\n"

	if contentType != "" {
		message += fmt.Sprintf("Content-Type: %s\r\n", contentType)
	}

	message += "\r\n" + body

	// Send email
	addr := fmt.Sprintf("%s:%d", c.config.SMTPHost, c.config.SMTPPort)

	// Use a channel to handle the async operation with context
	done := make(chan error, 1)
	go func() {
		err := smtp.SendMail(addr, c.auth, c.config.FromEmail, []string{to}, []byte(message))
		done <- err
	}()

	// Wait for completion or context cancellation
	select {
	case err := <-done:
		return err
	case <-ctx.Done():
		return ctx.Err()
	}
}

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

// SendWithAttachments sends an email with attachments via SendGrid
func (c *SendGridClient) SendWithAttachments(ctx context.Context, to, subject, htmlBody, textBody string, attachments []Attachment) error {
	// TODO: Implement attachment support for SendGrid
	// For now, just send HTML email without attachments
	return c.SendHTML(ctx, to, subject, htmlBody, textBody)
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

// SESClient implements EmailClient using AWS SES
type SESClient struct {
	config Config
	client *http.Client
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
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
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

// SendWithAttachments sends an email with attachments via AWS SES
func (c *SESClient) SendWithAttachments(ctx context.Context, to, subject, htmlBody, textBody string, attachments []Attachment) error {
	// TODO: Implement attachment support for SES
	// For now, just send HTML email without attachments
	return c.SendHTML(ctx, to, subject, htmlBody, textBody)
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

// NewEmailClient creates an email client based on configuration
func NewEmailClient(config Config) (EmailClient, error) {
	switch config.Provider {
	case "smtp":
		return NewSMTPClient(config)
	case "sendgrid":
		return NewSendGridClient(config)
	case "ses":
		return NewSESClient(config)
	default:
		return nil, fmt.Errorf("unsupported email provider: %s", config.Provider)
	}
}

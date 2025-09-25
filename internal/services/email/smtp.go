package email

import (
	"context"
	"fmt"
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

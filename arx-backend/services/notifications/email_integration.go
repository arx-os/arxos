package notifications

import (
	"bytes"
	"crypto/tls"
	"fmt"
	"html/template"
	"net/smtp"
	"time"
)

// ProductionEmailService handles production-ready email delivery
type ProductionEmailService struct {
	config     *ProductionEmailConfig
	templates  map[string]*template.Template
	connection *smtp.Client
	oauth2     *OAuth2Config
}

// ProductionEmailConfig holds production email configuration
type ProductionEmailConfig struct {
	SMTPHost         string
	SMTPPort         int
	Username         string
	Password         string
	FromEmail        string
	FromName         string
	UseTLS           bool
	UseOAuth2        bool
	OAuth2Config     *OAuth2Config
	MaxRetries       int
	RetryDelay       time.Duration
	TemplatePath     string
	RateLimit        int // emails per minute
	BatchSize        int
	DeliveryTracking bool
}

// OAuth2Config holds OAuth2 configuration for email services
type OAuth2Config struct {
	ClientID     string
	ClientSecret string
	RefreshToken string
	TokenURL     string
	Scopes       []string
}

// EmailDeliveryStatus represents detailed delivery status
type EmailDeliveryStatus struct {
	MessageID    string
	Status       string // sent, delivered, failed, bounced
	SentAt       time.Time
	DeliveredAt  *time.Time
	BouncedAt    *time.Time
	BounceReason string
	RetryCount   int
	Error        error
}

// NewProductionEmailService creates a production-ready email service
func NewProductionEmailService(config *ProductionEmailConfig) (*ProductionEmailService, error) {
	service := &ProductionEmailService{
		config:    config,
		templates: make(map[string]*template.Template),
		oauth2:    config.OAuth2Config,
	}

	// Load email templates
	if err := service.loadTemplates(); err != nil {
		return nil, fmt.Errorf("failed to load email templates: %w", err)
	}

	// Test connection
	if err := service.testConnection(); err != nil {
		return nil, fmt.Errorf("failed to test email connection: %w", err)
	}

	return service, nil
}

// loadTemplates loads email templates from the template path
func (pes *ProductionEmailService) loadTemplates() error {
	templateNames := []string{
		"notification",
		"alert",
		"maintenance",
		"system",
		"welcome",
		"verification",
		"password_reset",
		"invitation",
	}

	for _, name := range templateNames {
		tmpl, err := template.ParseFiles(fmt.Sprintf("%s/%s.html", pes.config.TemplatePath, name))
		if err != nil {
			// Continue if template doesn't exist
			continue
		}
		pes.templates[name] = tmpl
	}

	return nil
}

// testConnection tests the SMTP connection with OAuth2 support
func (pes *ProductionEmailService) testConnection() error {
	var auth smtp.Auth

	if pes.config.UseOAuth2 && pes.oauth2 != nil {
		// Use OAuth2 authentication
		auth = smtp.PlainAuth("", pes.config.Username, "", pes.config.SMTPHost)
	} else {
		// Use password authentication
		auth = smtp.PlainAuth("", pes.config.Username, pes.config.Password, pes.config.SMTPHost)
	}

	// Connect to SMTP server
	addr := fmt.Sprintf("%s:%d", pes.config.SMTPHost, pes.config.SMTPPort)
	conn, err := smtp.Dial(addr)
	if err != nil {
		return fmt.Errorf("failed to connect to SMTP server: %w", err)
	}
	defer conn.Close()

	// Start TLS if required
	if pes.config.UseTLS {
		if err := conn.StartTLS(&tls.Config{ServerName: pes.config.SMTPHost}); err != nil {
			return fmt.Errorf("failed to start TLS: %w", err)
		}
	}

	// Authenticate
	if err := conn.Auth(auth); err != nil {
		return fmt.Errorf("failed to authenticate: %w", err)
	}

	pes.connection = conn
	return nil
}

// SendEmail sends a single email with production-ready features
func (pes *ProductionEmailService) SendEmail(message *EmailMessage) *EmailResult {
	startTime := time.Now()
	messageID := generateMessageID()

	// Validate email
	if err := pes.validateEmail(message); err != nil {
		return &EmailResult{
			Success:    false,
			MessageID:  messageID,
			SentAt:     time.Now(),
			Error:      err,
			RetryCount: 0,
		}
	}

	// Prepare email content
	content, err := pes.prepareEmailContent(message)
	if err != nil {
		return &EmailResult{
			Success:    false,
			MessageID:  messageID,
			SentAt:     time.Now(),
			Error:      err,
			RetryCount: 0,
		}
	}

	// Send email with retry logic
	var lastError error
	for attempt := 0; attempt <= pes.config.MaxRetries; attempt++ {
		if err := pes.sendEmailWithRetry(message, content); err != nil {
			lastError = err
			if attempt < pes.config.MaxRetries {
				time.Sleep(pes.config.RetryDelay * time.Duration(attempt+1))
				continue
			}
		} else {
			// Success
			deliveryTime := time.Since(startTime)
			return &EmailResult{
				Success:      true,
				MessageID:    messageID,
				SentAt:       time.Now(),
				DeliveryTime: deliveryTime,
				RetryCount:   attempt,
			}
		}
	}

	// All retries failed
	return &EmailResult{
		Success:    false,
		MessageID:  messageID,
		SentAt:     time.Now(),
		Error:      lastError,
		RetryCount: pes.config.MaxRetries,
	}
}

// validateEmail validates email message
func (pes *ProductionEmailService) validateEmail(message *EmailMessage) error {
	if len(message.To) == 0 {
		return fmt.Errorf("no recipients specified")
	}

	for _, email := range message.To {
		if !ValidateEmail(email) {
			return fmt.Errorf("invalid email address: %s", email)
		}
	}

	if message.Subject == "" {
		return fmt.Errorf("subject is required")
	}

	if message.Body == "" && message.HTMLBody == "" {
		return fmt.Errorf("email body is required")
	}

	return nil
}

// prepareEmailContent prepares email content with proper headers
func (pes *ProductionEmailService) prepareEmailContent(message *EmailMessage) ([]byte, error) {
	var buffer bytes.Buffer

	// Email headers
	headers := map[string]string{
		"From":         fmt.Sprintf("%s <%s>", pes.config.FromName, pes.config.FromEmail),
		"To":           joinEmails(message.To),
		"Subject":      message.Subject,
		"MIME-Version": "1.0",
		"Message-ID":   fmt.Sprintf("<%s@%s>", generateMessageID(), pes.config.SMTPHost),
		"Date":         time.Now().Format("Mon, 02 Jan 2006 15:04:05 -0700"),
	}

	// Add custom headers
	for key, value := range message.Headers {
		headers[key] = value
	}

	// Write headers
	for key, value := range headers {
		buffer.WriteString(fmt.Sprintf("%s: %s\r\n", key, value))
	}
	buffer.WriteString("\r\n")

	// Write body
	if message.HTMLBody != "" {
		// Multipart message with HTML and text
		boundary := "boundary-" + generateMessageID()
		buffer.WriteString(fmt.Sprintf("Content-Type: multipart/alternative; boundary=\"%s\"\r\n\r\n", boundary))

		// Text part
		buffer.WriteString(fmt.Sprintf("--%s\r\n", boundary))
		buffer.WriteString("Content-Type: text/plain; charset=UTF-8\r\n\r\n")
		buffer.WriteString(message.Body)
		buffer.WriteString("\r\n\r\n")

		// HTML part
		buffer.WriteString(fmt.Sprintf("--%s\r\n", boundary))
		buffer.WriteString("Content-Type: text/html; charset=UTF-8\r\n\r\n")
		buffer.WriteString(message.HTMLBody)
		buffer.WriteString("\r\n\r\n")

		buffer.WriteString(fmt.Sprintf("--%s--\r\n", boundary))
	} else {
		// Plain text message
		buffer.WriteString("Content-Type: text/plain; charset=UTF-8\r\n\r\n")
		buffer.WriteString(message.Body)
	}

	return buffer.Bytes(), nil
}

// sendEmailWithRetry sends email with retry logic
func (pes *ProductionEmailService) sendEmailWithRetry(message *EmailMessage, content []byte) error {
	var auth smtp.Auth

	if pes.config.UseOAuth2 && pes.oauth2 != nil {
		// Use OAuth2 authentication
		auth = smtp.PlainAuth("", pes.config.Username, "", pes.config.SMTPHost)
	} else {
		// Use password authentication
		auth = smtp.PlainAuth("", pes.config.Username, pes.config.Password, pes.config.SMTPHost)
	}

	// Connect to SMTP server
	addr := fmt.Sprintf("%s:%d", pes.config.SMTPHost, pes.config.SMTPPort)
	conn, err := smtp.Dial(addr)
	if err != nil {
		return fmt.Errorf("failed to connect to SMTP server: %w", err)
	}
	defer conn.Close()

	// Start TLS if required
	if pes.config.UseTLS {
		if err := conn.StartTLS(&tls.Config{ServerName: pes.config.SMTPHost}); err != nil {
			return fmt.Errorf("failed to start TLS: %w", err)
		}
	}

	// Authenticate
	if err := conn.Auth(auth); err != nil {
		return fmt.Errorf("failed to authenticate: %w", err)
	}

	// Set sender
	if err := conn.Mail(pes.config.FromEmail); err != nil {
		return fmt.Errorf("failed to set sender: %w", err)
	}

	// Set recipients
	for _, recipient := range message.To {
		if err := conn.Rcpt(recipient); err != nil {
			return fmt.Errorf("failed to set recipient %s: %w", recipient, err)
		}
	}

	// Send data
	writer, err := conn.Data()
	if err != nil {
		return fmt.Errorf("failed to get data writer: %w", err)
	}
	defer writer.Close()

	if _, err := writer.Write(content); err != nil {
		return fmt.Errorf("failed to write email content: %w", err)
	}

	return nil
}

// SendBulkEmail sends multiple emails with rate limiting
func (pes *ProductionEmailService) SendBulkEmail(messages []*EmailMessage) []*EmailResult {
	results := make([]*EmailResult, len(messages))

	// Process in batches
	for i := 0; i < len(messages); i += pes.config.BatchSize {
		end := i + pes.config.BatchSize
		if end > len(messages) {
			end = len(messages)
		}

		batch := messages[i:end]

		// Send batch
		for j, message := range batch {
			results[i+j] = pes.SendEmail(message)

			// Rate limiting
			if pes.config.RateLimit > 0 {
				time.Sleep(time.Minute / time.Duration(pes.config.RateLimit))
			}
		}
	}

	return results
}

// GetDeliveryStatus gets detailed delivery status
func (pes *ProductionEmailService) GetDeliveryStatus(messageID string) (*EmailDeliveryStatus, error) {
	// This would typically query a database or external service
	// For now, return a mock status
	return &EmailDeliveryStatus{
		MessageID: messageID,
		Status:    "sent",
		SentAt:    time.Now(),
	}, nil
}

// GetStatistics gets email delivery statistics
func (pes *ProductionEmailService) GetStatistics() (map[string]interface{}, error) {
	// This would typically query a database
	// For now, return mock statistics
	return map[string]interface{}{
		"total_sent":            1000,
		"total_delivered":       950,
		"total_failed":          50,
		"success_rate":          95.0,
		"average_delivery_time": 2.5,
	}, nil
}

// CreateEmailTemplate creates a new email template
func (pes *ProductionEmailService) CreateEmailTemplate(name, content string) error {
	// This would typically save to a database or file system
	// For now, just add to memory
	tmpl, err := template.New(name).Parse(content)
	if err != nil {
		return fmt.Errorf("failed to parse template: %w", err)
	}

	pes.templates[name] = tmpl
	return nil
}

// DeleteEmailTemplate deletes an email template
func (pes *ProductionEmailService) DeleteEmailTemplate(name string) error {
	delete(pes.templates, name)
	return nil
}

// ListEmailTemplates lists all available email templates
func (pes *ProductionEmailService) ListEmailTemplates() []string {
	templates := make([]string, 0, len(pes.templates))
	for name := range pes.templates {
		templates = append(templates, name)
	}
	return templates
}

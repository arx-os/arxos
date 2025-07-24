package notifications

import (
	"bytes"
	"crypto/tls"
	"fmt"
	"html/template"
	"net/smtp"
	"time"

	"github.com/arxos/arx-backend/models"
)

// EmailService handles email notification delivery
type EmailService struct {
	config     *EmailConfig
	templates  map[string]*template.Template
	connection *smtp.Client
}

// EmailConfig holds email service configuration
type EmailConfig struct {
	SMTPHost     string
	SMTPPort     int
	Username     string
	Password     string
	FromEmail    string
	FromName     string
	UseTLS       bool
	MaxRetries   int
	RetryDelay   time.Duration
	TemplatePath string
}

// EmailMessage represents an email message
type EmailMessage struct {
	To           []string
	Subject      string
	Body         string
	HTMLBody     string
	Priority     string
	TemplateID   string
	TemplateData map[string]interface{}
	Headers      map[string]string
}

// EmailResult represents the result of an email send operation
type EmailResult struct {
	Success      bool
	MessageID    string
	SentAt       time.Time
	DeliveredAt  *time.Time
	Error        error
	RetryCount   int
	DeliveryTime time.Duration
}

// NewEmailService creates a new email service instance
func NewEmailService(config *EmailConfig) (*EmailService, error) {
	service := &EmailService{
		config:    config,
		templates: make(map[string]*template.Template),
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
func (es *EmailService) loadTemplates() error {
	templateNames := []string{
		"notification",
		"alert",
		"maintenance",
		"system",
		"welcome",
	}

	for _, name := range templateNames {
		tmpl, err := template.ParseFiles(fmt.Sprintf("%s/%s.html", es.config.TemplatePath, name))
		if err != nil {
			return fmt.Errorf("failed to parse template %s: %w", name, err)
		}
		es.templates[name] = tmpl
	}

	return nil
}

// testConnection tests the SMTP connection
func (es *EmailService) testConnection() error {
	auth := smtp.PlainAuth("", es.config.Username, es.config.Password, es.config.SMTPHost)

	addr := fmt.Sprintf("%s:%d", es.config.SMTPHost, es.config.SMTPPort)
	conn, err := smtp.Dial(addr)
	if err != nil {
		return fmt.Errorf("failed to connect to SMTP server: %w", err)
	}
	defer conn.Close()

	if es.config.UseTLS {
		if err := conn.StartTLS(&tls.Config{ServerName: es.config.SMTPHost}); err != nil {
			return fmt.Errorf("failed to start TLS: %w", err)
		}
	}

	if err := conn.Auth(auth); err != nil {
		return fmt.Errorf("failed to authenticate: %w", err)
	}

	return nil
}

// SendEmail sends an email message
func (es *EmailService) SendEmail(message *EmailMessage) *EmailResult {
	startTime := time.Now()
	result := &EmailResult{
		Success:    false,
		MessageID:  generateMessageID(),
		SentAt:     startTime,
		RetryCount: 0,
	}

	// Prepare email content
	content, err := es.prepareEmailContent(message)
	if err != nil {
		result.Error = fmt.Errorf("failed to prepare email content: %w", err)
		return result
	}

	// Send email with retry logic
	for attempt := 0; attempt <= es.config.MaxRetries; attempt++ {
		if err := es.sendEmailWithRetry(message, content); err != nil {
			result.RetryCount = attempt
			if attempt == es.config.MaxRetries {
				result.Error = fmt.Errorf("failed to send email after %d attempts: %w", es.config.MaxRetries, err)
				return result
			}
			time.Sleep(es.config.RetryDelay * time.Duration(attempt+1))
			continue
		}

		result.Success = true
		result.DeliveryTime = time.Since(startTime)
		now := time.Now()
		result.DeliveredAt = &now
		break
	}

	return result
}

// prepareEmailContent prepares the email content using templates
func (es *EmailService) prepareEmailContent(message *EmailMessage) ([]byte, error) {
	var body string
	var err error

	if message.TemplateID != "" {
		// Use template
		tmpl, exists := es.templates[message.TemplateID]
		if !exists {
			return nil, fmt.Errorf("template %s not found", message.TemplateID)
		}

		var buf bytes.Buffer
		if err := tmpl.Execute(&buf, message.TemplateData); err != nil {
			return nil, fmt.Errorf("failed to execute template: %w", err)
		}
		body = buf.String()
	} else {
		// Use provided body
		body = message.HTMLBody
		if body == "" {
			body = message.Body
		}
	}

	// Create email headers
	headers := make(map[string]string)
	headers["From"] = fmt.Sprintf("%s <%s>", es.config.FromName, es.config.FromEmail)
	headers["To"] = joinEmails(message.To)
	headers["Subject"] = message.Subject
	headers["Content-Type"] = "text/html; charset=UTF-8"
	headers["X-Priority"] = message.Priority
	headers["X-Message-ID"] = generateMessageID()

	// Add custom headers
	for key, value := range message.Headers {
		headers[key] = value
	}

	// Build email content
	var emailContent bytes.Buffer
	for key, value := range headers {
		emailContent.WriteString(fmt.Sprintf("%s: %s\r\n", key, value))
	}
	emailContent.WriteString("\r\n")
	emailContent.WriteString(body)

	return emailContent.Bytes(), nil
}

// sendEmailWithRetry sends an email with retry logic
func (es *EmailService) sendEmailWithRetry(message *EmailMessage, content []byte) error {
	auth := smtp.PlainAuth("", es.config.Username, es.config.Password, es.config.SMTPHost)
	addr := fmt.Sprintf("%s:%d", es.config.SMTPHost, es.config.SMTPPort)

	return smtp.SendMail(addr, auth, es.config.FromEmail, message.To, content)
}

// SendBulkEmail sends multiple emails efficiently
func (es *EmailService) SendBulkEmail(messages []*EmailMessage) []*EmailResult {
	results := make([]*EmailResult, len(messages))

	// Process emails in batches to avoid overwhelming the SMTP server
	batchSize := 10
	for i := 0; i < len(messages); i += batchSize {
		end := i + batchSize
		if end > len(messages) {
			end = len(messages)
		}

		batch := messages[i:end]
		for j, message := range batch {
			results[i+j] = es.SendEmail(message)
		}

		// Small delay between batches
		if end < len(messages) {
			time.Sleep(100 * time.Millisecond)
		}
	}

	return results
}

// GetDeliveryStatus returns the delivery status of an email
func (es *EmailService) GetDeliveryStatus(messageID string) (*models.EmailDeliveryStatus, error) {
	// This would typically query a database for delivery status
	// For now, return a mock status
	return &models.EmailDeliveryStatus{
		MessageID:   messageID,
		Status:      "delivered",
		DeliveredAt: time.Now(),
	}, nil
}

// GetStatistics returns email delivery statistics
func (es *EmailService) GetStatistics() (*models.EmailStatistics, error) {
	// This would typically query a database for statistics
	// For now, return mock statistics
	return &models.EmailStatistics{
		TotalSent:   1000,
		Delivered:   950,
		Failed:      50,
		AverageTime: 2.5,
		SuccessRate: 95.0,
		LastUpdated: time.Now(),
	}, nil
}

// Helper functions

func generateMessageID() string {
	return fmt.Sprintf("email_%d", time.Now().UnixNano())
}

func joinEmails(emails []string) string {
	result := ""
	for i, email := range emails {
		if i > 0 {
			result += ", "
		}
		result += email
	}
	return result
}

// ValidateEmail validates an email address
func ValidateEmail(email string) bool {
	// Basic email validation
	if len(email) < 5 || len(email) > 254 {
		return false
	}

	// Check for @ symbol
	atIndex := -1
	for i, char := range email {
		if char == '@' {
			atIndex = i
			break
		}
	}

	if atIndex == -1 || atIndex == 0 || atIndex == len(email)-1 {
		return false
	}

	return true
}

// CreateEmailTemplate creates a new email template
func (es *EmailService) CreateEmailTemplate(name, content string) error {
	// This would typically save the template to the template directory
	// For now, just add it to the templates map
	tmpl, err := template.New(name).Parse(content)
	if err != nil {
		return fmt.Errorf("failed to parse template: %w", err)
	}

	es.templates[name] = tmpl
	return nil
}

// DeleteEmailTemplate deletes an email template
func (es *EmailService) DeleteEmailTemplate(name string) error {
	if _, exists := es.templates[name]; !exists {
		return fmt.Errorf("template %s not found", name)
	}

	delete(es.templates, name)
	return nil
}

// ListEmailTemplates returns a list of available email templates
func (es *EmailService) ListEmailTemplates() []string {
	templates := make([]string, 0, len(es.templates))
	for name := range es.templates {
		templates = append(templates, name)
	}
	return templates
}

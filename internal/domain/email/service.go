package email

import (
	"context"
	"fmt"
	"time"
)

// Service defines the interface for email business logic following Clean Architecture principles
type Service interface {
	// Email operations
	SendPasswordResetEmail(ctx context.Context, email, token string) error
	SendWelcomeEmail(ctx context.Context, email, name string) error
	SendNotificationEmail(ctx context.Context, email, subject, body string) error
	SendVerificationEmail(ctx context.Context, email, token string) error
	SendCustomEmail(ctx context.Context, req SendEmailRequest) error

	// Template operations
	SendTemplatedEmail(ctx context.Context, req TemplatedEmailRequest) error
	GetEmailTemplate(ctx context.Context, templateName string) (*EmailTemplate, error)
	CreateEmailTemplate(ctx context.Context, req CreateTemplateRequest) (*EmailTemplate, error)
	UpdateEmailTemplate(ctx context.Context, id string, req UpdateTemplateRequest) (*EmailTemplate, error)
	DeleteEmailTemplate(ctx context.Context, id string) error
	ListEmailTemplates(ctx context.Context) ([]*EmailTemplate, error)

	// Email history and tracking
	GetEmailHistory(ctx context.Context, email string, limit int) ([]*EmailRecord, error)
	GetEmailStatus(ctx context.Context, messageID string) (*EmailStatus, error)
}

// EmailTemplate represents an email template
type EmailTemplate struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Subject     string                 `json:"subject"`
	HTMLBody    string                 `json:"html_body"`
	TextBody    string                 `json:"text_body"`
	Variables   []string               `json:"variables"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// EmailRecord represents a sent email record
type EmailRecord struct {
	ID          string                 `json:"id"`
	To          string                 `json:"to"`
	Subject     string                 `json:"subject"`
	Status      string                 `json:"status"` // sent, failed, pending
	SentAt      time.Time              `json:"sent_at"`
	Provider    string                 `json:"provider"`
	MessageID   string                 `json:"message_id"`
	Error       string                 `json:"error,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// EmailStatus represents the status of an email
type EmailStatus struct {
	MessageID     string                 `json:"message_id"`
	Status        string                 `json:"status"`
	DeliveredAt   *time.Time             `json:"delivered_at,omitempty"`
	OpenedAt      *time.Time             `json:"opened_at,omitempty"`
	ClickedAt     *time.Time             `json:"clicked_at,omitempty"`
	BouncedAt     *time.Time             `json:"bounced_at,omitempty"`
	ComplainedAt  *time.Time             `json:"complained_at,omitempty"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
}

// Request types
type SendEmailRequest struct {
	To          string                 `json:"to" validate:"required,email"`
	Subject     string                 `json:"subject" validate:"required"`
	HTMLBody    string                 `json:"html_body,omitempty"`
	TextBody    string                 `json:"text_body,omitempty"`
	Attachments []Attachment           `json:"attachments,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

type TemplatedEmailRequest struct {
	To           string                 `json:"to" validate:"required,email"`
	TemplateName string                 `json:"template_name" validate:"required"`
	Variables    map[string]interface{} `json:"variables,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

type CreateTemplateRequest struct {
	Name      string   `json:"name" validate:"required"`
	Subject   string   `json:"subject" validate:"required"`
	HTMLBody  string   `json:"html_body,omitempty"`
	TextBody  string   `json:"text_body,omitempty"`
	Variables []string `json:"variables,omitempty"`
}

type UpdateTemplateRequest struct {
	Name      *string  `json:"name,omitempty"`
	Subject   *string  `json:"subject,omitempty"`
	HTMLBody  *string  `json:"html_body,omitempty"`
	TextBody  *string  `json:"text_body,omitempty"`
	Variables []string `json:"variables,omitempty"`
}

// Attachment represents an email attachment
type Attachment struct {
	Filename    string `json:"filename"`
	ContentType string `json:"content_type"`
	Content     []byte `json:"content"`
}

// EmailClient interface for different email providers
type EmailClient interface {
	Send(ctx context.Context, to, subject, body string) error
	SendHTML(ctx context.Context, to, subject, htmlBody, textBody string) error
	SendWithAttachments(ctx context.Context, to, subject, htmlBody, textBody string, attachments []Attachment) error
}

// Config holds email service configuration
type Config struct {
	Provider     string            `json:"provider"` // smtp, sendgrid, ses
	SMTPHost     string            `json:"smtp_host"`
	SMTPPort     int               `json:"smtp_port"`
	SMTPUsername string            `json:"smtp_username"`
	SMTPPassword string            `json:"smtp_password"`
	FromEmail    string            `json:"from_email"`
	FromName     string            `json:"from_name"`
	APIKey       string            `json:"api_key"` // For SendGrid/SES
	Region       string            `json:"region"`  // For AWS SES
	TemplateDir  string            `json:"template_dir"`
	Options      map[string]string `json:"options"`
}

// service implements the email service following Clean Architecture principles
type service struct {
	config       Config
	client       EmailClient
	templates    map[string]*EmailTemplate
	emailHistory []*EmailRecord
}

// NewService creates a new email service with dependency injection
func NewService(config Config, client EmailClient) Service {
	return &service{
		config:       config,
		client:       client,
		templates:    make(map[string]*EmailTemplate),
		emailHistory: make([]*EmailRecord, 0),
	}
}

// SendPasswordResetEmail sends a password reset email
func (s *service) SendPasswordResetEmail(ctx context.Context, email, token string) error {
	subject := "Reset Your ArxOS Password"
	
	// Generate reset URL (this would come from config)
	resetURL := fmt.Sprintf("https://arxos.example.com/reset-password?token=%s", token)

	htmlBody := fmt.Sprintf(`
		<html>
		<body>
			<h2>Password Reset Request</h2>
			<p>You requested a password reset for your ArxOS account.</p>
			<p>Click the link below to reset your password:</p>
			<p><a href="%s">Reset Password</a></p>
			<p>This link will expire in 24 hours.</p>
			<p>If you didn't request this reset, please ignore this email.</p>
		</body>
		</html>
	`, resetURL)

	textBody := fmt.Sprintf(`
		Password Reset Request
		
		You requested a password reset for your ArxOS account.
		
		Click the link below to reset your password:
		%s
		
		This link will expire in 24 hours.
		
		If you didn't request this reset, please ignore this email.
	`, resetURL)

	return s.client.SendHTML(ctx, email, subject, htmlBody, textBody)
}

// SendWelcomeEmail sends a welcome email to new users
func (s *service) SendWelcomeEmail(ctx context.Context, email, name string) error {
	subject := "Welcome to ArxOS"

	htmlBody := fmt.Sprintf(`
		<html>
		<body>
			<h2>Welcome to ArxOS, %s!</h2>
			<p>Your account has been created successfully.</p>
			<p>You can now access the ArxOS building management system.</p>
			<p>If you have any questions, please contact support.</p>
		</body>
		</html>
	`, name)

	textBody := fmt.Sprintf(`
		Welcome to ArxOS, %s!
		
		Your account has been created successfully.
		
		You can now access the ArxOS building management system.
		
		If you have any questions, please contact support.
	`, name)

	return s.client.SendHTML(ctx, email, subject, htmlBody, textBody)
}

// SendNotificationEmail sends a general notification email
func (s *service) SendNotificationEmail(ctx context.Context, email, subject, body string) error {
	return s.client.Send(ctx, email, subject, body)
}

// SendVerificationEmail sends an email verification email
func (s *service) SendVerificationEmail(ctx context.Context, email, token string) error {
	subject := "Verify Your ArxOS Email"

	verifyURL := fmt.Sprintf("https://arxos.example.com/verify-email?token=%s", token)

	htmlBody := fmt.Sprintf(`
		<html>
		<body>
			<h2>Email Verification</h2>
			<p>Please verify your email address by clicking the link below:</p>
			<p><a href="%s">Verify Email</a></p>
			<p>This link will expire in 24 hours.</p>
		</body>
		</html>
	`, verifyURL)

	textBody := fmt.Sprintf(`
		Email Verification
		
		Please verify your email address by clicking the link below:
		%s
		
		This link will expire in 24 hours.
	`, verifyURL)

	return s.client.SendHTML(ctx, email, subject, htmlBody, textBody)
}

// SendCustomEmail sends a custom email
func (s *service) SendCustomEmail(ctx context.Context, req SendEmailRequest) error {
	// Validate request
	if err := s.validateSendEmailRequest(req); err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}

	// Send email based on content type
	if req.HTMLBody != "" && req.TextBody != "" {
		return s.client.SendHTML(ctx, req.To, req.Subject, req.HTMLBody, req.TextBody)
	} else if req.HTMLBody != "" {
		return s.client.SendHTML(ctx, req.To, req.Subject, req.HTMLBody, "")
	} else {
		return s.client.Send(ctx, req.To, req.Subject, req.TextBody)
	}
}

// SendTemplatedEmail sends an email using a template
func (s *service) SendTemplatedEmail(ctx context.Context, req TemplatedEmailRequest) error {
	// Validate request
	if err := s.validateTemplatedEmailRequest(req); err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}

	// Get template
	template, err := s.GetEmailTemplate(ctx, req.TemplateName)
	if err != nil {
		return fmt.Errorf("failed to get template: %w", err)
	}
	if template == nil {
		return fmt.Errorf("template not found: %s", req.TemplateName)
	}

	// Render template with variables
	subject, htmlBody, textBody, err := s.renderTemplate(template, req.Variables)
	if err != nil {
		return fmt.Errorf("failed to render template: %w", err)
	}

	// Send email
	return s.client.SendHTML(ctx, req.To, subject, htmlBody, textBody)
}

// GetEmailTemplate retrieves an email template by name
func (s *service) GetEmailTemplate(ctx context.Context, templateName string) (*EmailTemplate, error) {
	template, exists := s.templates[templateName]
	if !exists {
		return nil, nil // Template not found
	}
	return template, nil
}

// CreateEmailTemplate creates a new email template
func (s *service) CreateEmailTemplate(ctx context.Context, req CreateTemplateRequest) (*EmailTemplate, error) {
	// Validate request
	if err := s.validateCreateTemplateRequest(req); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Check if template already exists
	if _, exists := s.templates[req.Name]; exists {
		return nil, fmt.Errorf("template with name %s already exists", req.Name)
	}

	// Create template
	template := &EmailTemplate{
		ID:        fmt.Sprintf("template_%d", time.Now().UnixNano()),
		Name:      req.Name,
		Subject:   req.Subject,
		HTMLBody:  req.HTMLBody,
		TextBody:  req.TextBody,
		Variables: req.Variables,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// Store template
	s.templates[req.Name] = template

	return template, nil
}

// UpdateEmailTemplate updates an existing email template
func (s *service) UpdateEmailTemplate(ctx context.Context, id string, req UpdateTemplateRequest) (*EmailTemplate, error) {
	// Find template by ID
	var template *EmailTemplate
	for _, t := range s.templates {
		if t.ID == id {
			template = t
			break
		}
	}

	if template == nil {
		return nil, fmt.Errorf("template not found")
	}

	// Update fields if provided
	if req.Name != nil {
		template.Name = *req.Name
	}
	if req.Subject != nil {
		template.Subject = *req.Subject
	}
	if req.HTMLBody != nil {
		template.HTMLBody = *req.HTMLBody
	}
	if req.TextBody != nil {
		template.TextBody = *req.TextBody
	}
	if req.Variables != nil {
		template.Variables = req.Variables
	}

	// Set updated timestamp
	template.UpdatedAt = time.Now()

	return template, nil
}

// DeleteEmailTemplate deletes an email template
func (s *service) DeleteEmailTemplate(ctx context.Context, id string) error {
	// Find and remove template by ID
	for name, template := range s.templates {
		if template.ID == id {
			delete(s.templates, name)
			return nil
		}
	}

	return fmt.Errorf("template not found")
}

// ListEmailTemplates lists all email templates
func (s *service) ListEmailTemplates(ctx context.Context) ([]*EmailTemplate, error) {
	templates := make([]*EmailTemplate, 0, len(s.templates))
	for _, template := range s.templates {
		templates = append(templates, template)
	}
	return templates, nil
}

// GetEmailHistory retrieves email history for a specific email address
func (s *service) GetEmailHistory(ctx context.Context, email string, limit int) ([]*EmailRecord, error) {
	// Validate inputs
	if email == "" {
		return nil, fmt.Errorf("email is required")
	}
	if limit <= 0 {
		limit = 50 // Default limit
	}

	// Filter emails for the specific address
	var history []*EmailRecord
	for _, record := range s.emailHistory {
		if record.To == email {
			history = append(history, record)
			if len(history) >= limit {
				break
			}
		}
	}

	return history, nil
}

// GetEmailStatus retrieves the status of a sent email
func (s *service) GetEmailStatus(ctx context.Context, messageID string) (*EmailStatus, error) {
	// Validate inputs
	if messageID == "" {
		return nil, fmt.Errorf("message ID is required")
	}

	// TODO: Implement actual status retrieval from email provider
	// For now, return mock status
	return &EmailStatus{
		MessageID: messageID,
		Status:    "delivered",
	}, nil
}

// Helper methods for validation
func (s *service) validateSendEmailRequest(req SendEmailRequest) error {
	if req.To == "" {
		return fmt.Errorf("to email is required")
	}
	if req.Subject == "" {
		return fmt.Errorf("subject is required")
	}
	if req.HTMLBody == "" && req.TextBody == "" {
		return fmt.Errorf("either HTML body or text body is required")
	}
	return nil
}

func (s *service) validateTemplatedEmailRequest(req TemplatedEmailRequest) error {
	if req.To == "" {
		return fmt.Errorf("to email is required")
	}
	if req.TemplateName == "" {
		return fmt.Errorf("template name is required")
	}
	return nil
}

func (s *service) validateCreateTemplateRequest(req CreateTemplateRequest) error {
	if req.Name == "" {
		return fmt.Errorf("template name is required")
	}
	if req.Subject == "" {
		return fmt.Errorf("subject is required")
	}
	return nil
}

// renderTemplate renders a template with variables
func (s *service) renderTemplate(template *EmailTemplate, variables map[string]interface{}) (string, string, string, error) {
	// Simple template rendering - in production, use a proper template engine
	subject := template.Subject
	htmlBody := template.HTMLBody
	textBody := template.TextBody

	// Replace variables in subject and body
	for key, value := range variables {
		placeholder := fmt.Sprintf("{{%s}}", key)
		subject = fmt.Sprintf("%s", subject) // Replace placeholder with value
		htmlBody = fmt.Sprintf("%s", htmlBody)
		textBody = fmt.Sprintf("%s", textBody)
		_ = placeholder // TODO: Implement actual placeholder replacement
		_ = value
	}

	return subject, htmlBody, textBody, nil
}

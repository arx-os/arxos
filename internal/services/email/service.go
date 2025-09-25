package email

import (
	"context"
	"fmt"
)

// Service defines the interface for email operations
type Service interface {
	SendPasswordResetEmail(ctx context.Context, email, token string) error
	SendWelcomeEmail(ctx context.Context, email, name string) error
	SendNotificationEmail(ctx context.Context, email, subject, body string) error
	SendVerificationEmail(ctx context.Context, email, token string) error
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

// EmailService implements the email service interface
type EmailService struct {
	config Config
	client EmailClient
}

// EmailClient defines the interface for different email providers
type EmailClient interface {
	Send(ctx context.Context, to, subject, body string) error
	SendHTML(ctx context.Context, to, subject, htmlBody, textBody string) error
}

// NewEmailService creates a new email service
func NewEmailService(config Config) (Service, error) {
	var client EmailClient
	var err error

	switch config.Provider {
	case "smtp":
		client, err = NewSMTPClient(config)
	case "sendgrid":
		client, err = NewSendGridClient(config)
	case "ses":
		client, err = NewSESClient(config)
	default:
		return nil, fmt.Errorf("unsupported email provider: %s", config.Provider)
	}

	if err != nil {
		return nil, fmt.Errorf("failed to create email client: %w", err)
	}

	return &EmailService{
		config: config,
		client: client,
	}, nil
}

// SendPasswordResetEmail sends a password reset email
func (s *EmailService) SendPasswordResetEmail(ctx context.Context, email, token string) error {
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
func (s *EmailService) SendWelcomeEmail(ctx context.Context, email, name string) error {
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
func (s *EmailService) SendNotificationEmail(ctx context.Context, email, subject, body string) error {
	return s.client.Send(ctx, email, subject, body)
}

// SendVerificationEmail sends an email verification email
func (s *EmailService) SendVerificationEmail(ctx context.Context, email, token string) error {
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

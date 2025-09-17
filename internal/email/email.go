package email

import (
	"bytes"
	"context"
	"fmt"
	"html/template"
	"net/smtp"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// EmailService handles email sending
type EmailService interface {
	SendPasswordReset(ctx context.Context, to, resetToken string) error
	SendWelcome(ctx context.Context, to, name string) error
	SendInvitation(ctx context.Context, to, inviterName, orgName, inviteToken string) error
}

// Config contains email service configuration
type Config struct {
	SMTPHost     string
	SMTPPort     int
	SMTPUser     string
	SMTPPassword string
	FromEmail    string
	FromName     string
	BaseURL      string
}

// SMTPEmailService implements EmailService using SMTP
type SMTPEmailService struct {
	config Config
}

// NewSMTPEmailService creates a new SMTP email service
func NewSMTPEmailService(config Config) EmailService {
	return &SMTPEmailService{
		config: config,
	}
}

// SendPasswordReset sends a password reset email
func (s *SMTPEmailService) SendPasswordReset(ctx context.Context, to, resetToken string) error {
	resetURL := fmt.Sprintf("%s/reset-password?token=%s", s.config.BaseURL, resetToken)
	
	subject := "Reset Your ArxOS Password"
	body := fmt.Sprintf(`
		<html>
		<body>
			<h2>Password Reset Request</h2>
			<p>You requested to reset your password for your ArxOS account.</p>
			<p>Click the link below to reset your password:</p>
			<p><a href="%s">Reset Password</a></p>
			<p>This link will expire in 1 hour.</p>
			<p>If you didn't request this password reset, please ignore this email.</p>
			<br>
			<p>Best regards,<br>The ArxOS Team</p>
		</body>
		</html>
	`, resetURL)
	
	return s.sendEmail(ctx, to, subject, body)
}

// SendWelcome sends a welcome email to new users
func (s *SMTPEmailService) SendWelcome(ctx context.Context, to, name string) error {
	subject := "Welcome to ArxOS!"
	body := fmt.Sprintf(`
		<html>
		<body>
			<h2>Welcome to ArxOS, %s!</h2>
			<p>Thank you for creating an account with ArxOS.</p>
			<p>You can now log in and start managing your building data.</p>
			<p><a href="%s/login">Log In to ArxOS</a></p>
			<br>
			<p>If you have any questions, please don't hesitate to contact our support team.</p>
			<p>Best regards,<br>The ArxOS Team</p>
		</body>
		</html>
	`, name, s.config.BaseURL)
	
	return s.sendEmail(ctx, to, subject, body)
}

// SendInvitation sends an organization invitation email
func (s *SMTPEmailService) SendInvitation(ctx context.Context, to, inviterName, orgName, inviteToken string) error {
	inviteURL := fmt.Sprintf("%s/accept-invite?token=%s", s.config.BaseURL, inviteToken)
	
	subject := fmt.Sprintf("You've been invited to join %s on ArxOS", orgName)
	body := fmt.Sprintf(`
		<html>
		<body>
			<h2>Organization Invitation</h2>
			<p>%s has invited you to join %s on ArxOS.</p>
			<p>Click the link below to accept the invitation:</p>
			<p><a href="%s">Accept Invitation</a></p>
			<p>This invitation will expire in 7 days.</p>
			<br>
			<p>Best regards,<br>The ArxOS Team</p>
		</body>
		</html>
	`, inviterName, orgName, inviteURL)
	
	return s.sendEmail(ctx, to, subject, body)
}

// sendEmail sends an email using SMTP
func (s *SMTPEmailService) sendEmail(ctx context.Context, to, subject, body string) error {
	from := fmt.Sprintf("%s <%s>", s.config.FromName, s.config.FromEmail)
	
	// Build the email message
	message := []string{
		fmt.Sprintf("From: %s", from),
		fmt.Sprintf("To: %s", to),
		fmt.Sprintf("Subject: %s", subject),
		"MIME-Version: 1.0",
		"Content-Type: text/html; charset=UTF-8",
		"",
		body,
	}
	
	msg := []byte(strings.Join(message, "\r\n"))
	
	// Set up authentication
	auth := smtp.PlainAuth("", s.config.SMTPUser, s.config.SMTPPassword, s.config.SMTPHost)
	
	// Send the email
	addr := fmt.Sprintf("%s:%d", s.config.SMTPHost, s.config.SMTPPort)
	err := smtp.SendMail(addr, auth, s.config.FromEmail, []string{to}, msg)
	if err != nil {
		logger.Error("Failed to send email to %s: %v", to, err)
		return fmt.Errorf("failed to send email: %w", err)
	}
	
	logger.Info("Email sent successfully to %s", to)
	return nil
}

// MockEmailService is a mock implementation for testing
type MockEmailService struct {
	SentEmails []SentEmail
}

// SentEmail represents an email that was sent (for testing)
type SentEmail struct {
	To        string
	Type      string
	Token     string
	Timestamp time.Time
}

// NewMockEmailService creates a new mock email service
func NewMockEmailService() *MockEmailService {
	return &MockEmailService{
		SentEmails: make([]SentEmail, 0),
	}
}

// SendPasswordReset mock implementation
func (m *MockEmailService) SendPasswordReset(ctx context.Context, to, resetToken string) error {
	m.SentEmails = append(m.SentEmails, SentEmail{
		To:        to,
		Type:      "password_reset",
		Token:     resetToken,
		Timestamp: time.Now(),
	})
	logger.Info("[MOCK] Password reset email sent to %s with token %s", to, resetToken)
	return nil
}

// SendWelcome mock implementation
func (m *MockEmailService) SendWelcome(ctx context.Context, to, name string) error {
	m.SentEmails = append(m.SentEmails, SentEmail{
		To:        to,
		Type:      "welcome",
		Timestamp: time.Now(),
	})
	logger.Info("[MOCK] Welcome email sent to %s", to)
	return nil
}

// SendInvitation mock implementation
func (m *MockEmailService) SendInvitation(ctx context.Context, to, inviterName, orgName, inviteToken string) error {
	m.SentEmails = append(m.SentEmails, SentEmail{
		To:        to,
		Type:      "invitation",
		Token:     inviteToken,
		Timestamp: time.Now(),
	})
	logger.Info("[MOCK] Invitation email sent to %s for org %s", to, orgName)
	return nil
}

// EmailTemplates provides HTML email templates
type EmailTemplates struct {
	templates map[string]*template.Template
}

// NewEmailTemplates creates a new email template manager
func NewEmailTemplates() *EmailTemplates {
	return &EmailTemplates{
		templates: make(map[string]*template.Template),
	}
}

// RenderPasswordReset renders a password reset email template
func (et *EmailTemplates) RenderPasswordReset(data map[string]interface{}) (string, error) {
	tmpl := `
	<!DOCTYPE html>
	<html>
	<head>
		<style>
			body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
			.container { max-width: 600px; margin: 0 auto; padding: 20px; }
			.header { background-color: #f4f4f4; padding: 20px; text-align: center; }
			.button { display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; }
			.footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }
		</style>
	</head>
	<body>
		<div class="container">
			<div class="header">
				<h1>Password Reset Request</h1>
			</div>
			<p>Hello,</p>
			<p>We received a request to reset your password for your ArxOS account.</p>
			<p>Click the button below to reset your password:</p>
			<p style="text-align: center;">
				<a href="{{.ResetURL}}" class="button">Reset Password</a>
			</p>
			<p>Or copy and paste this link into your browser:</p>
			<p style="word-break: break-all;">{{.ResetURL}}</p>
			<p>This link will expire in {{.ExpireHours}} hour(s).</p>
			<p>If you didn't request this password reset, you can safely ignore this email.</p>
			<div class="footer">
				<p>Best regards,<br>The ArxOS Team</p>
				<p>This is an automated message. Please do not reply to this email.</p>
			</div>
		</div>
	</body>
	</html>
	`
	
	t, err := template.New("passwordReset").Parse(tmpl)
	if err != nil {
		return "", err
	}
	
	var buf bytes.Buffer
	if err := t.Execute(&buf, data); err != nil {
		return "", err
	}
	
	return buf.String(), nil
}
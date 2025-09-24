package services

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// EmailImplementations provides actual email functionality
type EmailImplementations struct {
	// In a real implementation, this would have an email service client
	// For now, we'll just log the emails
}

// NewEmailImplementations creates a new email implementations instance
func NewEmailImplementations() *EmailImplementations {
	return &EmailImplementations{}
}

// EmailTemplate represents an email template
type EmailTemplate struct {
	Subject string
	Body    string
	HTML    string
}

// EmailData represents data for email templates
type EmailData struct {
	User         *models.User
	Organization *models.Organization
	Invitation   *InvitationData
	Reset        *PasswordResetData
	Welcome      *WelcomeData
	Custom       map[string]interface{}
}

// InvitationData represents invitation email data
type InvitationData struct {
	InviterName      string
	OrganizationName string
	InviteURL        string
	ExpiresAt        time.Time
	Role             string
}

// PasswordResetData represents password reset email data
type PasswordResetData struct {
	ResetURL  string
	ExpiresAt time.Time
	UserAgent string
	IPAddress string
}

// WelcomeData represents welcome email data
type WelcomeData struct {
	OrganizationName  string
	DashboardURL      string
	SupportEmail      string
	GettingStartedURL string
}

// SendInvitationEmail sends an organization invitation email
func (ei *EmailImplementations) SendInvitationEmail(ctx context.Context, user *models.User, org *models.Organization, invitationData *InvitationData) error {
	logger.Info("Sending invitation email to %s for organization %s", user.Email, org.Name)

	// Create email data
	data := &EmailData{
		User:         user,
		Organization: org,
		Invitation:   invitationData,
	}

	// Generate email content
	subject, body, html, err := ei.generateInvitationEmail(data)
	if err != nil {
		return fmt.Errorf("failed to generate invitation email: %w", err)
	}

	// Send email (in real implementation, this would use an email service)
	err = ei.sendEmail(ctx, user.Email, subject, body, html)
	if err != nil {
		return fmt.Errorf("failed to send invitation email: %w", err)
	}

	logger.Info("Invitation email sent successfully to %s", user.Email)
	return nil
}

// SendPasswordResetEmail sends a password reset email
func (ei *EmailImplementations) SendPasswordResetEmail(ctx context.Context, user *models.User, resetData *PasswordResetData) error {
	logger.Info("Sending password reset email to %s", user.Email)

	// Create email data
	data := &EmailData{
		User:  user,
		Reset: resetData,
	}

	// Generate email content
	subject, body, html, err := ei.generatePasswordResetEmail(data)
	if err != nil {
		return fmt.Errorf("failed to generate password reset email: %w", err)
	}

	// Send email
	err = ei.sendEmail(ctx, user.Email, subject, body, html)
	if err != nil {
		return fmt.Errorf("failed to send password reset email: %w", err)
	}

	logger.Info("Password reset email sent successfully to %s", user.Email)
	return nil
}

// SendWelcomeEmail sends a welcome email
func (ei *EmailImplementations) SendWelcomeEmail(ctx context.Context, user *models.User, org *models.Organization, welcomeData *WelcomeData) error {
	logger.Info("Sending welcome email to %s", user.Email)

	// Create email data
	data := &EmailData{
		User:         user,
		Organization: org,
		Welcome:      welcomeData,
	}

	// Generate email content
	subject, body, html, err := ei.generateWelcomeEmail(data)
	if err != nil {
		return fmt.Errorf("failed to generate welcome email: %w", err)
	}

	// Send email
	err = ei.sendEmail(ctx, user.Email, subject, body, html)
	if err != nil {
		return fmt.Errorf("failed to send welcome email: %w", err)
	}

	logger.Info("Welcome email sent successfully to %s", user.Email)
	return nil
}

// SendNotificationEmail sends a notification email
func (ei *EmailImplementations) SendNotificationEmail(ctx context.Context, user *models.User, subject string, message string, data map[string]interface{}) error {
	logger.Info("Sending notification email to %s", user.Email)

	// Create email data
	emailData := &EmailData{
		User:   user,
		Custom: data,
	}

	// Generate email content
	body, html, err := ei.generateNotificationEmail(subject, message, emailData)
	if err != nil {
		return fmt.Errorf("failed to generate notification email: %w", err)
	}

	// Send email
	err = ei.sendEmail(ctx, user.Email, subject, body, html)
	if err != nil {
		return fmt.Errorf("failed to send notification email: %w", err)
	}

	logger.Info("Notification email sent successfully to %s", user.Email)
	return nil
}

// Helper methods for email generation

// generateInvitationEmail generates invitation email content
func (ei *EmailImplementations) generateInvitationEmail(data *EmailData) (string, string, string, error) {
	subject := fmt.Sprintf("Invitation to join %s on ArxOS", data.Organization.Name)

	// Text body
	body := fmt.Sprintf(`
Hello %s,

You have been invited to join %s on ArxOS by %s.

Organization: %s
Role: %s
Invitation expires: %s

To accept this invitation, click the link below:
%s

If you have any questions, please contact the organization administrator.

Best regards,
The ArxOS Team
`, data.User.FullName, data.Organization.Name, data.Invitation.InviterName,
		data.Organization.Name, data.Invitation.Role,
		data.Invitation.ExpiresAt.Format("January 2, 2006 at 3:04 PM MST"),
		data.Invitation.InviteURL)

	// HTML body
	html := fmt.Sprintf(`
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Organization Invitation</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .button { display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>You're Invited to Join %s</h1>
        </div>
        
        <p>Hello %s,</p>
        
        <p>You have been invited to join <strong>%s</strong> on ArxOS by %s.</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p><strong>Organization:</strong> %s</p>
            <p><strong>Role:</strong> %s</p>
            <p><strong>Invitation expires:</strong> %s</p>
        </div>
        
        <p>To accept this invitation, click the button below:</p>
        
        <a href="%s" class="button">Accept Invitation</a>
        
        <p>If you have any questions, please contact the organization administrator.</p>
        
        <div class="footer">
            <p>Best regards,<br>The ArxOS Team</p>
        </div>
    </div>
</body>
</html>
`, data.Organization.Name, data.User.FullName, data.Organization.Name,
		data.Invitation.InviterName, data.Organization.Name, data.Invitation.Role,
		data.Invitation.ExpiresAt.Format("January 2, 2006 at 3:04 PM MST"),
		data.Invitation.InviteURL)

	return subject, body, html, nil
}

// generatePasswordResetEmail generates password reset email content
func (ei *EmailImplementations) generatePasswordResetEmail(data *EmailData) (string, string, string, error) {
	subject := "Password Reset Request - ArxOS"

	// Text body
	body := fmt.Sprintf(`
Hello %s,

You requested a password reset for your ArxOS account.

To reset your password, click the link below:
%s

This link will expire on %s.

If you did not request this password reset, please ignore this email or contact support if you have concerns.

Security Information:
- Requested from: %s
- IP Address: %s
- Time: %s

Best regards,
The ArxOS Team
`, data.User.FullName, data.Reset.ResetURL,
		data.Reset.ExpiresAt.Format("January 2, 2006 at 3:04 PM MST"),
		data.Reset.UserAgent, data.Reset.IPAddress,
		time.Now().Format("January 2, 2006 at 3:04 PM MST"))

	// HTML body
	html := fmt.Sprintf(`
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Password Reset Request</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .button { display: inline-block; background-color: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .security { background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        
        <p>Hello %s,</p>
        
        <p>You requested a password reset for your ArxOS account.</p>
        
        <p>To reset your password, click the button below:</p>
        
        <a href="%s" class="button">Reset Password</a>
        
        <p><strong>This link will expire on %s.</strong></p>
        
        <div class="security">
            <h3>Security Information</h3>
            <p><strong>Requested from:</strong> %s</p>
            <p><strong>IP Address:</strong> %s</p>
            <p><strong>Time:</strong> %s</p>
        </div>
        
        <p>If you did not request this password reset, please ignore this email or contact support if you have concerns.</p>
        
        <div class="footer">
            <p>Best regards,<br>The ArxOS Team</p>
        </div>
    </div>
</body>
</html>
`, data.User.FullName, data.Reset.ResetURL,
		data.Reset.ExpiresAt.Format("January 2, 2006 at 3:04 PM MST"),
		data.Reset.UserAgent, data.Reset.IPAddress,
		time.Now().Format("January 2, 2006 at 3:04 PM MST"))

	return subject, body, html, nil
}

// generateWelcomeEmail generates welcome email content
func (ei *EmailImplementations) generateWelcomeEmail(data *EmailData) (string, string, string, error) {
	subject := fmt.Sprintf("Welcome to %s on ArxOS!", data.Organization.Name)

	// Text body
	body := fmt.Sprintf(`
Hello %s,

Welcome to %s on ArxOS! We're excited to have you join our team.

Your account has been successfully created and you now have access to:
- Building management tools
- Equipment tracking
- Collaboration features
- And much more!

Getting Started:
1. Visit your dashboard: %s
2. Check out our getting started guide: %s
3. Explore the features available to your role

If you have any questions or need help getting started, don't hesitate to reach out to our support team at %s.

Best regards,
The ArxOS Team
`, data.User.FullName, data.Organization.Name,
		data.Welcome.DashboardURL, data.Welcome.GettingStartedURL,
		data.Welcome.SupportEmail)

	// HTML body
	html := fmt.Sprintf(`
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Welcome to ArxOS</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #28a745; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; text-align: center; }
        .button { display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
        .features { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to %s!</h1>
            <p>We're excited to have you join our team</p>
        </div>
        
        <p>Hello %s,</p>
        
        <p>Welcome to <strong>%s</strong> on ArxOS! Your account has been successfully created and you now have access to our powerful building management platform.</p>
        
        <div class="features">
            <h3>What you can do:</h3>
            <ul>
                <li>Manage buildings and floor plans</li>
                <li>Track equipment and maintenance</li>
                <li>Collaborate with your team</li>
                <li>Generate reports and analytics</li>
                <li>And much more!</li>
            </ul>
        </div>
        
        <h3>Getting Started:</h3>
        <ol>
            <li>Visit your dashboard: <a href="%s">%s</a></li>
            <li>Check out our getting started guide: <a href="%s">%s</a></li>
            <li>Explore the features available to your role</li>
        </ol>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="%s" class="button">Go to Dashboard</a>
            <a href="%s" class="button">Getting Started Guide</a>
        </div>
        
        <p>If you have any questions or need help getting started, don't hesitate to reach out to our support team at <a href="mailto:%s">%s</a>.</p>
        
        <div class="footer">
            <p>Best regards,<br>The ArxOS Team</p>
        </div>
    </div>
</body>
</html>
`, data.Organization.Name, data.User.FullName, data.Organization.Name,
		data.Welcome.DashboardURL, data.Welcome.DashboardURL,
		data.Welcome.GettingStartedURL, data.Welcome.GettingStartedURL,
		data.Welcome.DashboardURL, data.Welcome.GettingStartedURL,
		data.Welcome.SupportEmail, data.Welcome.SupportEmail)

	return subject, body, html, nil
}

// generateNotificationEmail generates notification email content
func (ei *EmailImplementations) generateNotificationEmail(subject string, message string, data *EmailData) (string, string, error) {
	// Text body
	body := fmt.Sprintf(`
Hello %s,

%s

Best regards,
The ArxOS Team
`, data.User.FullName, message)

	// HTML body
	html := fmt.Sprintf(`
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>%s</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>%s</h1>
        </div>
        
        <p>Hello %s,</p>
        
        <p>%s</p>
        
        <div class="footer">
            <p>Best regards,<br>The ArxOS Team</p>
        </div>
    </div>
</body>
</html>
`, subject, subject, data.User.FullName, message)

	return body, html, nil
}

// sendEmail sends an email (placeholder implementation)
func (ei *EmailImplementations) sendEmail(ctx context.Context, to, subject, body, html string) error {
	// In a real implementation, this would use an email service like SendGrid, SES, etc.
	// For now, we'll just log the email details

	logger.Info("Email sent:")
	logger.Info("  To: %s", to)
	logger.Info("  Subject: %s", subject)
	logger.Info("  Body length: %d characters", len(body))
	logger.Info("  HTML length: %d characters", len(html))

	// Simulate email sending delay
	time.Sleep(100 * time.Millisecond)

	return nil
}

// EmailServiceWithImplementations extends services with email functionality
type EmailServiceWithImplementations struct {
	*UserService
	*OrganizationService
	emailImpl *EmailImplementations
}

// NewEmailServiceWithImplementations creates a new service with email implementations
func NewEmailServiceWithImplementations(db database.DB) *EmailServiceWithImplementations {
	return &EmailServiceWithImplementations{
		UserService:         NewUserService(db),
		OrganizationService: NewOrganizationService(db),
		emailImpl:           NewEmailImplementations(),
	}
}

// SendInvitationEmail sends an organization invitation email
func (s *EmailServiceWithImplementations) SendInvitationEmail(ctx context.Context, userID, orgID string, role string) error {
	// Get user and organization
	user, err := s.UserService.GetUser(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to get user: %w", err)
	}

	org, err := s.OrganizationService.GetOrganization(ctx, orgID)
	if err != nil {
		return fmt.Errorf("failed to get organization: %w", err)
	}

	// Create invitation data
	invitationData := &InvitationData{
		InviterName:      "System Administrator", // This would come from context
		OrganizationName: org.Name,
		InviteURL:        fmt.Sprintf("https://arxos.com/invite/%s", orgID), // This would be generated
		ExpiresAt:        time.Now().Add(7 * 24 * time.Hour),                // 7 days
		Role:             role,
	}

	// Send email
	return s.emailImpl.SendInvitationEmail(ctx, user, org, invitationData)
}

// SendPasswordResetEmail sends a password reset email
func (s *EmailServiceWithImplementations) SendPasswordResetEmail(ctx context.Context, userID string, resetToken string) error {
	// Get user
	user, err := s.UserService.GetUser(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to get user: %w", err)
	}

	// Create reset data
	resetData := &PasswordResetData{
		ResetURL:  fmt.Sprintf("https://arxos.com/reset-password?token=%s", resetToken),
		ExpiresAt: time.Now().Add(1 * time.Hour), // 1 hour
		UserAgent: "Unknown",                     // This would come from request context
		IPAddress: "Unknown",                     // This would come from request context
	}

	// Send email
	return s.emailImpl.SendPasswordResetEmail(ctx, user, resetData)
}

// SendWelcomeEmail sends a welcome email
func (s *EmailServiceWithImplementations) SendWelcomeEmail(ctx context.Context, userID, orgID string) error {
	// Get user and organization
	user, err := s.UserService.GetUser(ctx, userID)
	if err != nil {
		return fmt.Errorf("failed to get user: %w", err)
	}

	org, err := s.OrganizationService.GetOrganization(ctx, orgID)
	if err != nil {
		return fmt.Errorf("failed to get organization: %w", err)
	}

	// Create welcome data
	welcomeData := &WelcomeData{
		OrganizationName:  org.Name,
		DashboardURL:      "https://arxos.com/dashboard",
		SupportEmail:      "support@arxos.com",
		GettingStartedURL: "https://arxos.com/getting-started",
	}

	// Send email
	return s.emailImpl.SendWelcomeEmail(ctx, user, org, welcomeData)
}

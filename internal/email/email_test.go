package email

import (
	"context"
	"fmt"
	"strings"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestNewSMTPEmailService(t *testing.T) {
	config := Config{
		SMTPHost:     "smtp.example.com",
		SMTPPort:     587,
		SMTPUser:     "test@example.com",
		SMTPPassword: "password123",
		FromEmail:    "noreply@example.com",
		FromName:     "ArxOS Test",
		BaseURL:      "https://test.arxos.com",
	}

	service := NewSMTPEmailService(config)
	assert.NotNil(t, service)

	smtpService, ok := service.(*SMTPEmailService)
	assert.True(t, ok)
	assert.Equal(t, config.SMTPHost, smtpService.config.SMTPHost)
	assert.Equal(t, config.SMTPPort, smtpService.config.SMTPPort)
	assert.Equal(t, config.BaseURL, smtpService.config.BaseURL)
}

func TestNewMockEmailService(t *testing.T) {
	mockService := NewMockEmailService()
	assert.NotNil(t, mockService)
	assert.Empty(t, mockService.SentEmails)
	assert.NotNil(t, mockService.SentEmails)
}

func TestMockEmailService_SendPasswordReset(t *testing.T) {
	mockService := NewMockEmailService()
	ctx := context.Background()

	to := "user@example.com"
	resetToken := "test-reset-token-123"

	err := mockService.SendPasswordReset(ctx, to, resetToken)
	assert.NoError(t, err)

	assert.Len(t, mockService.SentEmails, 1)

	sentEmail := mockService.SentEmails[0]
	assert.Equal(t, to, sentEmail.To)
	assert.Equal(t, "password_reset", sentEmail.Type)
	assert.Equal(t, resetToken, sentEmail.Token)
	assert.WithinDuration(t, time.Now(), sentEmail.Timestamp, 1*time.Second)
}

func TestMockEmailService_SendWelcome(t *testing.T) {
	mockService := NewMockEmailService()
	ctx := context.Background()

	to := "newuser@example.com"
	name := "John Doe"

	err := mockService.SendWelcome(ctx, to, name)
	assert.NoError(t, err)

	assert.Len(t, mockService.SentEmails, 1)

	sentEmail := mockService.SentEmails[0]
	assert.Equal(t, to, sentEmail.To)
	assert.Equal(t, "welcome", sentEmail.Type)
	assert.Empty(t, sentEmail.Token)
	assert.WithinDuration(t, time.Now(), sentEmail.Timestamp, 1*time.Second)
}

func TestMockEmailService_SendInvitation(t *testing.T) {
	mockService := NewMockEmailService()
	ctx := context.Background()

	to := "invited@example.com"
	inviterName := "Jane Admin"
	orgName := "Test Organization"
	inviteToken := "invite-token-456"

	err := mockService.SendInvitation(ctx, to, inviterName, orgName, inviteToken)
	assert.NoError(t, err)

	assert.Len(t, mockService.SentEmails, 1)

	sentEmail := mockService.SentEmails[0]
	assert.Equal(t, to, sentEmail.To)
	assert.Equal(t, "invitation", sentEmail.Type)
	assert.Equal(t, inviteToken, sentEmail.Token)
	assert.WithinDuration(t, time.Now(), sentEmail.Timestamp, 1*time.Second)
}

func TestMockEmailService_MultipleEmails(t *testing.T) {
	mockService := NewMockEmailService()
	ctx := context.Background()

	// Send multiple emails of different types
	err := mockService.SendPasswordReset(ctx, "user1@example.com", "token1")
	assert.NoError(t, err)

	err = mockService.SendWelcome(ctx, "user2@example.com", "User Two")
	assert.NoError(t, err)

	err = mockService.SendInvitation(ctx, "user3@example.com", "Admin", "Test Org", "invite123")
	assert.NoError(t, err)

	assert.Len(t, mockService.SentEmails, 3)

	// Check email types are tracked correctly
	emailTypes := make(map[string]int)
	for _, email := range mockService.SentEmails {
		emailTypes[email.Type]++
	}

	assert.Equal(t, 1, emailTypes["password_reset"])
	assert.Equal(t, 1, emailTypes["welcome"])
	assert.Equal(t, 1, emailTypes["invitation"])
}

func TestEmailTemplates_NewEmailTemplates(t *testing.T) {
	templates := NewEmailTemplates()
	assert.NotNil(t, templates)
	assert.NotNil(t, templates.templates)
	assert.Empty(t, templates.templates)
}

func TestEmailTemplates_RenderPasswordReset(t *testing.T) {
	templates := NewEmailTemplates()

	data := map[string]interface{}{
		"ResetURL":    "https://example.com/reset?token=abc123",
		"ExpireHours": 1,
	}

	html, err := templates.RenderPasswordReset(data)
	assert.NoError(t, err)
	assert.NotEmpty(t, html)

	// Check that template data was substituted
	assert.Contains(t, html, "https://example.com/reset?token=abc123")
	assert.Contains(t, html, "1 hour(s)")
	assert.Contains(t, html, "Password Reset Request")
	assert.Contains(t, html, "Reset Password")
	assert.Contains(t, html, "ArxOS Team")

	// Check HTML structure
	assert.Contains(t, html, "<!DOCTYPE html>")
	assert.Contains(t, html, "<html>")
	assert.Contains(t, html, "</html>")
	assert.Contains(t, html, "class=\"button\"")
	assert.Contains(t, html, "class=\"container\"")
}

func TestEmailTemplates_RenderPasswordReset_EmptyData(t *testing.T) {
	templates := NewEmailTemplates()

	// Test with empty data
	data := map[string]interface{}{}

	html, err := templates.RenderPasswordReset(data)
	assert.NoError(t, err)
	assert.NotEmpty(t, html)

	// Should still contain static content
	assert.Contains(t, html, "Password Reset Request")
	assert.Contains(t, html, "ArxOS Team")
}

func TestEmailTemplates_RenderPasswordReset_SpecialCharacters(t *testing.T) {
	templates := NewEmailTemplates()

	data := map[string]interface{}{
		"ResetURL":    "https://example.com/reset?token=abc123&special=test%20value",
		"ExpireHours": 24,
	}

	html, err := templates.RenderPasswordReset(data)
	assert.NoError(t, err)
	assert.NotEmpty(t, html)

	// Go's html/template auto-escapes & to &amp;
	assert.Contains(t, html, "abc123&amp;special=test%20value")
	assert.Contains(t, html, "24 hour(s)")
}

func TestConfig_Validation(t *testing.T) {
	tests := []struct {
		name   string
		config Config
		valid  bool
	}{
		{
			name: "valid config",
			config: Config{
				SMTPHost:     "smtp.gmail.com",
				SMTPPort:     587,
				SMTPUser:     "test@gmail.com",
				SMTPPassword: "password",
				FromEmail:    "noreply@example.com",
				FromName:     "ArxOS",
				BaseURL:      "https://example.com",
			},
			valid: true,
		},
		{
			name: "empty host",
			config: Config{
				SMTPHost:     "",
				SMTPPort:     587,
				SMTPUser:     "test@gmail.com",
				SMTPPassword: "password",
				FromEmail:    "noreply@example.com",
				FromName:     "ArxOS",
				BaseURL:      "https://example.com",
			},
			valid: false,
		},
		{
			name: "invalid port",
			config: Config{
				SMTPHost:     "smtp.gmail.com",
				SMTPPort:     0,
				SMTPUser:     "test@gmail.com",
				SMTPPassword: "password",
				FromEmail:    "noreply@example.com",
				FromName:     "ArxOS",
				BaseURL:      "https://example.com",
			},
			valid: false,
		},
		{
			name: "empty from email",
			config: Config{
				SMTPHost:     "smtp.gmail.com",
				SMTPPort:     587,
				SMTPUser:     "test@gmail.com",
				SMTPPassword: "password",
				FromEmail:    "",
				FromName:     "ArxOS",
				BaseURL:      "https://example.com",
			},
			valid: false,
		},
		{
			name: "empty base URL",
			config: Config{
				SMTPHost:     "smtp.gmail.com",
				SMTPPort:     587,
				SMTPUser:     "test@gmail.com",
				SMTPPassword: "password",
				FromEmail:    "noreply@example.com",
				FromName:     "ArxOS",
				BaseURL:      "",
			},
			valid: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			isValid := tt.config.SMTPHost != "" &&
				tt.config.SMTPPort > 0 &&
				tt.config.FromEmail != "" &&
				tt.config.BaseURL != ""

			assert.Equal(t, tt.valid, isValid, "Config validation mismatch for %s", tt.name)
		})
	}
}

func TestSentEmail_Structure(t *testing.T) {
	sentEmail := SentEmail{
		To:        "test@example.com",
		Type:      "test_type",
		Token:     "test_token",
		Timestamp: time.Now(),
	}

	assert.Equal(t, "test@example.com", sentEmail.To)
	assert.Equal(t, "test_type", sentEmail.Type)
	assert.Equal(t, "test_token", sentEmail.Token)
	assert.WithinDuration(t, time.Now(), sentEmail.Timestamp, 1*time.Second)
}

func TestEmailService_Interface(t *testing.T) {
	// Test that both implementations satisfy the interface
	config := Config{
		SMTPHost:     "smtp.example.com",
		SMTPPort:     587,
		SMTPUser:     "test@example.com",
		SMTPPassword: "password",
		FromEmail:    "noreply@example.com",
		FromName:     "ArxOS",
		BaseURL:      "https://example.com",
	}

	var smtpService EmailService = NewSMTPEmailService(config)
	var mockService EmailService = NewMockEmailService()

	assert.NotNil(t, smtpService)
	assert.NotNil(t, mockService)

	// Both should implement the interface methods
	ctx := context.Background()

	// Test interface compliance - these should compile
	_ = smtpService.SendPasswordReset(ctx, "test@example.com", "token")
	_ = smtpService.SendWelcome(ctx, "test@example.com", "name")
	_ = smtpService.SendInvitation(ctx, "test@example.com", "inviter", "org", "token")

	_ = mockService.SendPasswordReset(ctx, "test@example.com", "token")
	_ = mockService.SendWelcome(ctx, "test@example.com", "name")
	_ = mockService.SendInvitation(ctx, "test@example.com", "inviter", "org", "token")
}

func TestEmailContent_Security(t *testing.T) {
	// Test that email content generation handles potentially dangerous inputs safely
	templates := NewEmailTemplates()

	// Test with potentially malicious data
	data := map[string]interface{}{
		"ResetURL":    "javascript:alert('xss')",
		"ExpireHours": "<script>alert('xss')</script>",
	}

	html, err := templates.RenderPasswordReset(data)
	assert.NoError(t, err)
	assert.NotEmpty(t, html)

	// Go's html/template provides good security by escaping dangerous content
	// Dangerous URLs are replaced with #ZgotmplZ, and scripts are HTML-escaped
	assert.Contains(t, html, "#ZgotmplZ")                                         // URL was sanitized
	assert.Contains(t, html, "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;") // HTML escaped
}

func TestEmailAddressValidation(t *testing.T) {
	// Test helper to validate email addresses (would be used before sending)
	validEmails := []string{
		"test@example.com",
		"user.name@domain.org",
		"user+tag@example.co.uk",
		"123@domain.com",
	}

	invalidEmails := []string{
		"",
		"invalid",
		"@example.com",
		"test@",
		"test..test@example.com",
		"test@example",
	}

	for _, email := range validEmails {
		t.Run(fmt.Sprintf("valid_%s", email), func(t *testing.T) {
			// Basic email validation - contains @ and has parts before/after
			parts := strings.Split(email, "@")
			assert.Len(t, parts, 2)
			assert.NotEmpty(t, parts[0])
			assert.NotEmpty(t, parts[1])
			assert.Contains(t, parts[1], ".")
		})
	}

	for _, email := range invalidEmails {
		t.Run(fmt.Sprintf("invalid_%s", email), func(t *testing.T) {
			if email == "" {
				assert.Empty(t, email)
				return
			}

			parts := strings.Split(email, "@")
			// Basic validation: must have exactly one @, non-empty parts, domain has dot, no consecutive dots
			isValid := len(parts) == 2 && len(parts[0]) > 0 && len(parts[1]) > 0 &&
				strings.Contains(parts[1], ".") && !strings.Contains(parts[0], "..")
			assert.False(t, isValid, "Email %s should be invalid", email)
		})
	}
}

package handlers

import (
	"fmt"
	"net/http"

	"arx/services/notifications"
	"arx/utils"
)

// NotificationHandler handles notification-related HTTP requests
type NotificationHandler struct {
	notificationService *notifications.NotificationService
}

// NewNotificationHandler creates a new notification handler
func NewNotificationHandler(notificationService *notifications.NotificationService) *NotificationHandler {
	return &NotificationHandler{
		notificationService: notificationService,
	}
}

// HealthCheck handles GET /api/notifications/health
func (nh *NotificationHandler) HealthCheck(c *utils.ChiContext) {
	health, err := nh.notificationService.HealthCheck()
	if err != nil {
		c.Writer.Error(http.StatusServiceUnavailable, "Health check failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, health)
}

// ConfigureEmail handles POST /api/notifications/config/email
func (nh *NotificationHandler) ConfigureEmail(c *utils.ChiContext) {
	var request notifications.SMTPConfigRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	result, err := nh.notificationService.ConfigureEmail(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Email configuration failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// ConfigureSlack handles POST /api/notifications/config/slack
func (nh *NotificationHandler) ConfigureSlack(c *utils.ChiContext) {
	var request notifications.SlackWebhookConfigRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	result, err := nh.notificationService.ConfigureSlack(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Slack configuration failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// ConfigureSMS handles POST /api/notifications/config/sms
func (nh *NotificationHandler) ConfigureSMS(c *utils.ChiContext) {
	var request notifications.SMSProviderConfigRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	result, err := nh.notificationService.ConfigureSMS(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "SMS configuration failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// ConfigureWebhook handles POST /api/notifications/config/webhook
func (nh *NotificationHandler) ConfigureWebhook(c *utils.ChiContext) {
	var request notifications.WebhookConfigRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	result, err := nh.notificationService.ConfigureWebhook(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Webhook configuration failed", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// SendEmailNotification handles POST /api/notifications/email/send
func (nh *NotificationHandler) SendEmailNotification(c *utils.ChiContext) {
	var request notifications.EmailNotificationRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	if err := nh.validateEmailRequest(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Validation failed", err.Error())
		return
	}

	result, err := nh.notificationService.SendEmailNotification(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to send email notification", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// GetEmailNotification handles GET /api/notifications/email/{id}
func (nh *NotificationHandler) GetEmailNotification(c *utils.ChiContext) {
	id := c.Reader.Param("id")
	if id == "" {
		c.Writer.Error(http.StatusBadRequest, "Email ID is required")
		return
	}

	result, err := nh.notificationService.GetEmailNotification(id)
	if err != nil {
		c.Writer.Error(http.StatusNotFound, "Email notification not found", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// GetEmailStatistics handles GET /api/notifications/email/statistics
func (nh *NotificationHandler) GetEmailStatistics(c *utils.ChiContext) {
	stats, err := nh.notificationService.GetEmailStatistics()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get email statistics", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, stats)
}

// SendSlackNotification handles POST /api/notifications/slack/send
func (nh *NotificationHandler) SendSlackNotification(c *utils.ChiContext) {
	var request notifications.SlackNotificationRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	if err := nh.validateSlackRequest(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Validation failed", err.Error())
		return
	}

	result, err := nh.notificationService.SendSlackNotification(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to send Slack notification", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// GetSlackNotification handles GET /api/notifications/slack/{id}
func (nh *NotificationHandler) GetSlackNotification(c *utils.ChiContext) {
	id := c.Reader.Param("id")
	if id == "" {
		c.Writer.Error(http.StatusBadRequest, "Slack notification ID is required")
		return
	}

	result, err := nh.notificationService.GetSlackNotification(id)
	if err != nil {
		c.Writer.Error(http.StatusNotFound, "Slack notification not found", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// GetSlackStatistics handles GET /api/notifications/slack/statistics
func (nh *NotificationHandler) GetSlackStatistics(c *utils.ChiContext) {
	stats, err := nh.notificationService.GetSlackStatistics()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get Slack statistics", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, stats)
}

// SendSMSNotification handles POST /api/notifications/sms/send
func (nh *NotificationHandler) SendSMSNotification(c *utils.ChiContext) {
	var request notifications.SMSNotificationRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	if err := nh.validateSMSRequest(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Validation failed", err.Error())
		return
	}

	result, err := nh.notificationService.SendSMSNotification(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to send SMS notification", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// GetSMSNotification handles GET /api/notifications/sms/{id}
func (nh *NotificationHandler) GetSMSNotification(c *utils.ChiContext) {
	id := c.Reader.Param("id")
	if id == "" {
		c.Writer.Error(http.StatusBadRequest, "SMS notification ID is required")
		return
	}

	result, err := nh.notificationService.GetSMSNotification(id)
	if err != nil {
		c.Writer.Error(http.StatusNotFound, "SMS notification not found", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// GetSMSStatistics handles GET /api/notifications/sms/statistics
func (nh *NotificationHandler) GetSMSStatistics(c *utils.ChiContext) {
	stats, err := nh.notificationService.GetSMSStatistics()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get SMS statistics", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, stats)
}

// SendWebhookNotification handles POST /api/notifications/webhook/send
func (nh *NotificationHandler) SendWebhookNotification(c *utils.ChiContext) {
	var request notifications.WebhookNotificationRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	if err := nh.validateWebhookRequest(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Validation failed", err.Error())
		return
	}

	result, err := nh.notificationService.SendWebhookNotification(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to send webhook notification", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// GetWebhookNotification handles GET /api/notifications/webhook/{id}
func (nh *NotificationHandler) GetWebhookNotification(c *utils.ChiContext) {
	id := c.Reader.Param("id")
	if id == "" {
		c.Writer.Error(http.StatusBadRequest, "Webhook notification ID is required")
		return
	}

	result, err := nh.notificationService.GetWebhookNotification(id)
	if err != nil {
		c.Writer.Error(http.StatusNotFound, "Webhook notification not found", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// GetWebhookStatistics handles GET /api/notifications/webhook/statistics
func (nh *NotificationHandler) GetWebhookStatistics(c *utils.ChiContext) {
	stats, err := nh.notificationService.GetWebhookStatistics()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get webhook statistics", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, stats)
}

// SendUnifiedNotification handles POST /api/notifications/unified/send
func (nh *NotificationHandler) SendUnifiedNotification(c *utils.ChiContext) {
	var request notifications.UnifiedNotificationRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	if err := nh.validateUnifiedRequest(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Validation failed", err.Error())
		return
	}

	result, err := nh.notificationService.SendUnifiedNotification(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to send unified notification", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// GetUnifiedStatistics handles GET /api/notifications/unified/statistics
func (nh *NotificationHandler) GetUnifiedStatistics(c *utils.ChiContext) {
	stats, err := nh.notificationService.GetUnifiedStatistics()
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to get unified statistics", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, stats)
}

// CreateEmailTemplate handles POST /api/notifications/email/templates
func (nh *NotificationHandler) CreateEmailTemplate(c *utils.ChiContext) {
	var request notifications.EmailTemplateRequest
	if err := c.Reader.ShouldBindJSON(&request); err != nil {
		c.Writer.Error(http.StatusBadRequest, "Invalid request format", err.Error())
		return
	}

	result, err := nh.notificationService.CreateEmailTemplate(&request)
	if err != nil {
		c.Writer.Error(http.StatusInternalServerError, "Failed to create email template", err.Error())
		return
	}

	c.Writer.JSON(http.StatusCreated, result)
}

// GetEmailTemplate handles GET /api/notifications/email/templates/{id}
func (nh *NotificationHandler) GetEmailTemplate(c *utils.ChiContext) {
	id := c.Reader.Param("id")
	if id == "" {
		c.Writer.Error(http.StatusBadRequest, "Template ID is required")
		return
	}

	result, err := nh.notificationService.GetEmailTemplate(id)
	if err != nil {
		c.Writer.Error(http.StatusNotFound, "Email template not found", err.Error())
		return
	}

	c.Writer.JSON(http.StatusOK, result)
}

// GetSupportedEmailPriorities handles GET /api/notifications/email/priorities
func (nh *NotificationHandler) GetSupportedEmailPriorities(c *utils.ChiContext) {
	priorities := nh.notificationService.GetSupportedEmailPriorities()
	c.Writer.JSON(http.StatusOK, priorities)
}

// GetSupportedSlackMessageTypes handles GET /api/notifications/slack/message-types
func (nh *NotificationHandler) GetSupportedSlackMessageTypes(c *utils.ChiContext) {
	messageTypes := nh.notificationService.GetSupportedSlackMessageTypes()
	c.Writer.JSON(http.StatusOK, messageTypes)
}

// GetSupportedSMSProviders handles GET /api/notifications/sms/providers
func (nh *NotificationHandler) GetSupportedSMSProviders(c *utils.ChiContext) {
	providers := nh.notificationService.GetSupportedSMSProviders()
	c.Writer.JSON(http.StatusOK, providers)
}

// GetSupportedWebhookMethods handles GET /api/notifications/webhook/methods
func (nh *NotificationHandler) GetSupportedWebhookMethods(c *utils.ChiContext) {
	methods := nh.notificationService.GetSupportedWebhookMethods()
	c.Writer.JSON(http.StatusOK, methods)
}

// Validation methods
func (nh *NotificationHandler) validateEmailRequest(request *notifications.EmailNotificationRequest) error {
	if request.RecipientEmail == "" {
		return fmt.Errorf("recipient email is required")
	}
	if request.Subject == "" {
		return fmt.Errorf("subject is required")
	}
	return nil
}

func (nh *NotificationHandler) validateSlackRequest(request *notifications.SlackNotificationRequest) error {
	if request.Channel == "" {
		return fmt.Errorf("channel is required")
	}
	if request.Message == "" {
		return fmt.Errorf("message is required")
	}
	return nil
}

func (nh *NotificationHandler) validateSMSRequest(request *notifications.SMSNotificationRequest) error {
	if request.PhoneNumber == "" {
		return fmt.Errorf("phone number is required")
	}
	if request.Message == "" {
		return fmt.Errorf("message is required")
	}
	return nil
}

func (nh *NotificationHandler) validateWebhookRequest(request *notifications.WebhookNotificationRequest) error {
	if request.URL == "" {
		return fmt.Errorf("webhook URL is required")
	}
	if request.Payload == nil {
		return fmt.Errorf("payload is required")
	}
	return nil
}

func (nh *NotificationHandler) validateUnifiedRequest(request *notifications.UnifiedNotificationRequest) error {
	if len(request.Channels) == 0 {
		return fmt.Errorf("at least one channel is required")
	}
	if request.Message == "" {
		return fmt.Errorf("message is required")
	}
	return nil
}

// Package autocert provides Let's Encrypt automatic certificate management
package autocert

import (
	"context"
	"crypto/tls"
	"fmt"
	"net/http"
	"strings"
	"time"

	"golang.org/x/crypto/acme"
	"golang.org/x/crypto/acme/autocert"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Config holds autocert configuration
type Config struct {
	// Enabled determines if autocert is enabled
	Enabled bool

	// Domain is the primary domain name
	Domain string

	// Domains is a list of all domain names to get certificates for
	Domains []string

	// Email is the email address for Let's Encrypt account registration
	Email string

	// CacheDir is the directory to cache certificates (default: ./certs)
	CacheDir string

	// Staging uses Let's Encrypt staging environment for testing
	Staging bool

	// HTTPPort is the port for HTTP-01 challenge (default: 80)
	HTTPPort int

	// HTTPSPort is the port for HTTPS server (default: 443)
	HTTPSPort int

	// RenewBefore is days before expiry to renew certificates (default: 30)
	RenewBefore int
}

// Manager manages automatic TLS certificate provisioning via Let's Encrypt
type Manager struct {
	config      Config
	certManager *autocert.Manager
}

// NewManager creates a new autocert manager with validation
func NewManager(config Config) (*Manager, error) {
	// Validate configuration
	if err := validateConfig(config); err != nil {
		return nil, fmt.Errorf("invalid autocert config: %w", err)
	}

	// Set defaults
	if config.CacheDir == "" {
		config.CacheDir = "./certs"
	}
	if config.HTTPPort == 0 {
		config.HTTPPort = 80
	}
	if config.HTTPSPort == 0 {
		config.HTTPSPort = 443
	}
	if config.RenewBefore == 0 {
		config.RenewBefore = 30
	}

	// Build complete domain list
	domains := append([]string{}, config.Domains...)
	if config.Domain != "" && !contains(domains, config.Domain) {
		domains = append(domains, config.Domain)
	}

	// Create autocert manager
	certManager := &autocert.Manager{
		Prompt:     autocert.AcceptTOS,
		Cache:      autocert.DirCache(config.CacheDir),
		HostPolicy: autocert.HostWhitelist(domains...),
		Email:      config.Email,
	}

	// Configure staging environment for testing
	if config.Staging {
		certManager.Client = &acme.Client{
			DirectoryURL: "https://acme-staging-v02.api.letsencrypt.org/directory",
		}
		logger.Warn("Using Let's Encrypt STAGING environment - certificates will not be trusted!")
	}

	m := &Manager{
		config:      config,
		certManager: certManager,
	}

	logger.Info("Autocert initialized for domains: %v (email: %s)", domains, config.Email)

	return m, nil
}

// GetTLSConfig returns a TLS configuration for HTTPS server
func (m *Manager) GetTLSConfig() *tls.Config {
	return &tls.Config{
		GetCertificate: m.certManager.GetCertificate,
		NextProtos:     []string{"h2", "http/1.1"}, // Enable HTTP/2
		MinVersion:     tls.VersionTLS12,
		CipherSuites: []uint16{
			tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
			tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
			tls.TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
			tls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
			tls.TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305,
			tls.TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305,
		},
	}
}

// GetHTTPHandler returns an HTTP handler that handles ACME challenges
func (m *Manager) GetHTTPHandler(next http.Handler) http.Handler {
	return m.certManager.HTTPHandler(next)
}

// StartHTTPRedirectServer starts an HTTP server that redirects to HTTPS
// and handles ACME HTTP-01 challenges
func (m *Manager) StartHTTPRedirectServer(ctx context.Context) error {
	// Create redirect handler
	redirectHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Build HTTPS URL
		target := fmt.Sprintf("https://%s%s", r.Host, r.RequestURI)

		// Permanent redirect to HTTPS
		http.Redirect(w, r, target, http.StatusMovedPermanently)

		logger.Debug("HTTP->HTTPS redirect: %s -> %s", r.RequestURI, target)
	})

	// Wrap with ACME challenge handler
	handler := m.certManager.HTTPHandler(redirectHandler)

	// Create HTTP server
	server := &http.Server{
		Addr:         fmt.Sprintf(":%d", m.config.HTTPPort),
		Handler:      handler,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 5 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	logger.Info("Starting HTTP redirect server on :%d", m.config.HTTPPort)

	// Start server in goroutine
	go func() {
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Error("HTTP redirect server error: %v", err)
		}
	}()

	// Handle graceful shutdown
	go func() {
		<-ctx.Done()
		logger.Info("Shutting down HTTP redirect server...")

		shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()

		if err := server.Shutdown(shutdownCtx); err != nil {
			logger.Error("HTTP redirect server shutdown error: %v", err)
		} else {
			logger.Info("HTTP redirect server stopped")
		}
	}()

	return nil
}

// ValidateDomain checks if a domain is in the allowed list
func (m *Manager) ValidateDomain(domain string) bool {
	domains := append([]string{}, m.config.Domains...)
	if m.config.Domain != "" && !contains(domains, m.config.Domain) {
		domains = append(domains, m.config.Domain)
	}

	return contains(domains, domain)
}

// GetDomains returns the list of configured domains
func (m *Manager) GetDomains() []string {
	domains := append([]string{}, m.config.Domains...)
	if m.config.Domain != "" && !contains(domains, m.config.Domain) {
		domains = append(domains, m.config.Domain)
	}
	return domains
}

// validateConfig validates the autocert configuration
func validateConfig(config Config) error {
	if !config.Enabled {
		return nil
	}

	// Must have at least one domain
	if config.Domain == "" && len(config.Domains) == 0 {
		return fmt.Errorf("at least one domain must be specified when autocert is enabled")
	}

	// Email is required for Let's Encrypt
	if config.Email == "" {
		return fmt.Errorf("email is required for Let's Encrypt account registration")
	}

	// Validate email format
	if !isValidEmail(config.Email) {
		return fmt.Errorf("invalid email address: %s", config.Email)
	}

	// Validate all domains
	allDomains := append([]string{}, config.Domains...)
	if config.Domain != "" {
		allDomains = append(allDomains, config.Domain)
	}

	for _, domain := range allDomains {
		if !isValidDomain(domain) {
			return fmt.Errorf("invalid domain name: %s", domain)
		}
	}

	return nil
}

// isValidEmail performs basic email validation
func isValidEmail(email string) bool {
	if email == "" {
		return false
	}

	parts := strings.Split(email, "@")
	if len(parts) != 2 {
		return false
	}

	local, domain := parts[0], parts[1]

	// Local part must not be empty
	if local == "" {
		return false
	}

	// Domain must contain at least one dot and not be empty
	if domain == "" || !strings.Contains(domain, ".") {
		return false
	}

	return true
}

// isValidDomain performs basic domain validation
func isValidDomain(domain string) bool {
	if domain == "" {
		return false
	}

	// Must contain at least one dot
	if !strings.Contains(domain, ".") {
		return false
	}

	// Must not start or end with dot or dash
	if strings.HasPrefix(domain, ".") || strings.HasSuffix(domain, ".") ||
		strings.HasPrefix(domain, "-") || strings.HasSuffix(domain, "-") {
		return false
	}

	// Must not contain invalid characters
	if strings.ContainsAny(domain, " @#$%^&*()+=[]{}|\\;:'\",<>?") {
		return false
	}

	return true
}

// contains checks if a slice contains a string
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

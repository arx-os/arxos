# Frontend Security Configuration Requirements

## Required Backend Security Headers

The backend MUST implement these security headers for the HTMX frontend:

### 1. **HTTP Security Headers**
```go
// Required headers for every response
w.Header().Set("X-Content-Type-Options", "nosniff")
w.Header().Set("X-Frame-Options", "DENY")
w.Header().Set("X-XSS-Protection", "1; mode=block")
w.Header().Set("Referrer-Policy", "strict-origin-when-cross-origin")
w.Header().Set("Permissions-Policy", "geolocation=(), microphone=(), camera=()")

// Strict Transport Security (HTTPS only)
if r.TLS != nil {
    w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")
}
```

### 2. **Content Security Policy (CSP)**
```go
// Generate nonce for each request
nonce := generateCSPNonce()

csp := fmt.Sprintf(`
    default-src 'self';
    script-src 'self' 'nonce-%s' https://unpkg.com;
    style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com;
    font-src 'self' https://cdnjs.cloudflare.com;
    img-src 'self' data: https:;
    connect-src 'self' wss://%s;
    frame-ancestors 'none';
    base-uri 'self';
    form-action 'self';
    upgrade-insecure-requests;
`, nonce, r.Host)

w.Header().Set("Content-Security-Policy", csp)
```

### 3. **CSRF Protection**
```go
// Generate and validate CSRF tokens
type CSRFMiddleware struct {
    // Use gorilla/csrf or similar
}

// Endpoints needed:
POST /api/csrf/refresh  // Get new CSRF token
```

### 4. **HTMX-Specific Security**
```go
// Detect HTMX requests
func isHTMXRequest(r *http.Request) bool {
    return r.Header.Get("HX-Request") == "true"
}

// Validate HTMX requests
func validateHTMXRequest(r *http.Request) error {
    // Check for required headers
    if r.Header.Get("X-Requested-With") != "XMLHttpRequest" {
        return errors.New("invalid request")
    }
    
    // Verify timestamp to prevent replay attacks
    timestamp := r.Header.Get("X-Request-Timestamp")
    if !isValidTimestamp(timestamp, 60) { // 60 second window
        return errors.New("request expired")
    }
    
    return nil
}
```

### 5. **Rate Limiting**
```go
// Implement rate limiting per endpoint
rateLimiter := map[string]*rate.Limiter{
    "/api/auth/login":    rate.NewLimiter(5, 1),   // 5 attempts per minute
    "/api/buildings":     rate.NewLimiter(100, 10), // 100 requests per minute
    "/api/upload":        rate.NewLimiter(10, 1),   // 10 uploads per minute
}
```

### 6. **Input Validation & Sanitization**
```go
// Sanitize all user input before rendering in HTML
func sanitizeHTML(input string) string {
    p := bluemonday.UGCPolicy()
    return p.Sanitize(input)
}

// Validate file uploads
func validateUpload(file multipart.File, header *multipart.FileHeader) error {
    // Check file size
    if header.Size > 50*1024*1024 { // 50MB
        return errors.New("file too large")
    }
    
    // Verify MIME type
    buffer := make([]byte, 512)
    file.Read(buffer)
    file.Seek(0, 0)
    
    mimeType := http.DetectContentType(buffer)
    if mimeType != "application/pdf" {
        return errors.New("invalid file type")
    }
    
    // Check for malicious content
    if containsMaliciousContent(buffer) {
        return errors.New("potentially malicious file")
    }
    
    return nil
}
```

### 7. **Session Security**
```go
// Secure session configuration
sessionStore := sessions.NewCookieStore([]byte(secret))
sessionStore.Options = &sessions.Options{
    Path:     "/",
    MaxAge:   1800, // 30 minutes
    HttpOnly: true,
    Secure:   true, // HTTPS only
    SameSite: http.SameSiteStrictMode,
}
```

### 8. **Authentication Token Security**
```go
// JWT with short expiration and refresh tokens
type TokenPair struct {
    AccessToken  string `json:"access_token"`  // 15 min expiry
    RefreshToken string `json:"refresh_token"` // 7 days expiry
}

// Implement token rotation on refresh
func RefreshToken(oldRefresh string) (*TokenPair, error) {
    // Validate old refresh token
    // Blacklist old refresh token
    // Issue new token pair
}
```

## Frontend Security Checklist

### ✅ Implemented:
- [x] Content Security Policy with nonces
- [x] CSRF token management
- [x] XSS protection via sanitization
- [x] Clickjacking prevention
- [x] Secure token storage (sessionStorage)
- [x] Rate limiting client-side
- [x] Input validation
- [x] Session timeout
- [x] Mutation observer for XSS detection
- [x] Subresource Integrity (SRI) for CDN assets

### ⚠️ Backend Must Implement:
- [ ] Security headers middleware
- [ ] CSRF token generation/validation
- [ ] Rate limiting middleware
- [ ] Input sanitization
- [ ] File upload validation
- [ ] Token rotation
- [ ] Request timestamp validation
- [ ] Session management
- [ ] Audit logging

## Security Testing Checklist

### OWASP Top 10 Coverage:
1. **Injection** - ✅ Input sanitization, parameterized queries
2. **Broken Authentication** - ✅ Secure tokens, session timeout
3. **Sensitive Data Exposure** - ✅ HTTPS, secure storage
4. **XML External Entities** - N/A (using JSON/HTML)
5. **Broken Access Control** - ⚠️ Backend must implement
6. **Security Misconfiguration** - ✅ Security headers
7. **XSS** - ✅ CSP, sanitization, mutation observer
8. **Insecure Deserialization** - N/A (HTML over wire)
9. **Using Components with Known Vulnerabilities** - ✅ SRI for CDN
10. **Insufficient Logging** - ⚠️ Backend must implement

## Recommended Security Tools

### For Testing:
- **OWASP ZAP** - Security scanning
- **Burp Suite** - Penetration testing
- **Mozilla Observatory** - Header analysis
- **CSP Evaluator** - CSP policy testing

### For Monitoring:
- **Sentry** - Error tracking
- **Fail2ban** - Brute force protection
- **ModSecurity** - WAF rules
- **Prometheus** - Security metrics

## Additional Recommendations

1. **Enable HTTPS everywhere** - No mixed content
2. **Implement Subresource Integrity** for all external resources
3. **Use Content-Security-Policy-Report-Only** initially
4. **Implement security.txt** file
5. **Regular security audits** with automated tools
6. **Implement rate limiting** at reverse proxy level (nginx/caddy)
7. **Use Web Application Firewall** (WAF) in production
8. **Enable CORS properly** - No wildcards in production
9. **Implement request signing** for critical operations
10. **Use 2FA** for admin accounts
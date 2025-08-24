# Arxos Security Deployment Checklist

## Pre-Deployment Security Checklist

### 🔴 Critical - Must Complete Before Any Deployment

#### Authentication & Authorization
- [ ] **Set strong admin credentials**
  ```bash
  export ARXOS_ADMIN_USERNAME="your-admin-username"
  export ARXOS_ADMIN_PASSWORD="$(openssl rand -base64 20)"
  ```
- [ ] **Generate and persist JWT secret**
  ```bash
  openssl rand -base64 32 > /etc/arxos/jwt.key
  chmod 600 /etc/arxos/jwt.key
  export JWT_SECRET_FILE=/etc/arxos/jwt.key
  ```
- [ ] **Verify JWT expiration is 1 hour or less**
- [ ] **Disable default/test accounts**

#### CORS & API Security
- [ ] **Configure CORS for specific domains only**
  ```bash
  export CORS_ALLOWED_ORIGINS="https://app.yourdomain.com,https://admin.yourdomain.com"
  ```
- [ ] **Verify CORS does not allow all origins (*)**
- [ ] **Enable rate limiting**
- [ ] **Configure API timeout values**

#### Database Security
- [ ] **Change default database passwords**
- [ ] **Enable SSL/TLS for database connections**
  ```bash
  export DB_SSL_MODE=require
  ```
- [ ] **Configure database user with minimal privileges**
- [ ] **Enable database audit logging**
- [ ] **Set up database backups with encryption**

### 🟡 Important - Complete Before Production

#### Environment Configuration
- [ ] **Set ENVIRONMENT=production**
- [ ] **Copy .env.example to .env and configure all values**
- [ ] **Verify no secrets in source code**
- [ ] **Ensure .env is in .gitignore**
- [ ] **Set proper file permissions**
  ```bash
  chmod 600 .env
  chmod 700 /etc/arxos/
  ```

#### Network Security
- [ ] **Enable HTTPS/TLS**
  ```bash
  export TLS_ENABLED=true
  export TLS_CERT_PATH=/etc/arxos/certs/server.crt
  export TLS_KEY_PATH=/etc/arxos/certs/server.key
  ```
- [ ] **Configure firewall rules**
- [ ] **Set up reverse proxy (nginx/Apache)**
- [ ] **Disable unnecessary ports**
- [ ] **Configure trusted proxies**

#### Monitoring & Logging
- [ ] **Enable audit logging**
  ```bash
  export ENABLE_AUDIT_LOG=true
  export AUDIT_LOG_PATH=/var/log/arxos/audit.log
  ```
- [ ] **Configure log rotation**
- [ ] **Set up security monitoring alerts**
- [ ] **Enable health checks**
- [ ] **Configure error reporting**

### 🟢 Best Practices - Recommended for Production

#### Data Protection
- [ ] **Generate data encryption key**
  ```bash
  export DATA_ENCRYPTION_KEY=$(openssl rand -hex 32)
  ```
- [ ] **Enable backup encryption**
- [ ] **Configure data retention policies**
- [ ] **Set up secure file upload directory**
- [ ] **Validate file upload types and sizes**

#### Security Headers
- [ ] **Verify CSP headers are configured**
- [ ] **Check HSTS is enabled**
- [ ] **Confirm X-Frame-Options is set to DENY**
- [ ] **Verify X-Content-Type-Options is nosniff**

#### Session Management
- [ ] **Configure session timeout (1 hour recommended)**
- [ ] **Enable secure cookie flags**
- [ ] **Set HttpOnly on cookies**
- [ ] **Configure SameSite cookie attribute**

## Deployment Steps

### 1. Local Testing
```bash
# Run security tests
cd core && make security

# Check for vulnerabilities
go list -json -m all | nancy sleuth

# Test with production config
ENVIRONMENT=production go run cmd/server/main.go
```

### 2. Pre-Production Validation
```bash
# Verify environment variables
./scripts/validate-env.sh

# Run integration tests
./tests/test_integration.sh

# Check SSL/TLS configuration
openssl s_client -connect yourdomain.com:443
```

### 3. Production Deployment
```bash
# Set production environment
export ENVIRONMENT=production

# Start with security middleware enabled
./arxos-server --enable-security

# Verify security headers
curl -I https://yourdomain.com/api/health
```

## Post-Deployment Security Tasks

### Immediate (Within 24 hours)
- [ ] Change all default passwords
- [ ] Review audit logs for anomalies
- [ ] Verify all security headers are present
- [ ] Test rate limiting is working
- [ ] Confirm CORS is properly restrictive

### Weekly
- [ ] Review security alerts
- [ ] Check for failed login attempts
- [ ] Audit user permissions
- [ ] Review API usage patterns
- [ ] Update security patches

### Monthly
- [ ] Rotate secrets and API keys
- [ ] Review and update firewall rules
- [ ] Conduct security assessment
- [ ] Test backup restoration
- [ ] Update dependencies

### Quarterly
- [ ] Comprehensive security audit
- [ ] Penetration testing
- [ ] Review security policies
- [ ] Update incident response plan
- [ ] Security training for team

## Emergency Contacts

| Role | Contact | When to Contact |
|------|---------|-----------------|
| Security Team | security@arxos.io | Security incidents |
| DevOps Lead | devops@arxos.io | Infrastructure issues |
| On-Call Engineer | Use PagerDuty | System outages |

## Incident Response

### If Security Breach Suspected:
1. **Isolate** - Disconnect affected systems
2. **Assess** - Determine scope of breach
3. **Contain** - Prevent further damage
4. **Document** - Log all actions taken
5. **Notify** - Alert security team and stakeholders
6. **Recover** - Restore from secure backups
7. **Review** - Post-mortem and improvements

## Security Tools & Commands

```bash
# Generate secure passwords
openssl rand -base64 20

# Check open ports
netstat -tuln

# Monitor real-time connections
ss -tunap

# Check file permissions
find /var/arxos -type f -perm 777

# Audit log analysis
grep "SECURITY" /var/log/arxos/audit.log

# Test rate limiting
for i in {1..100}; do curl -X GET https://api.arxos.io/test; done

# Verify SSL certificate
openssl x509 -in /etc/arxos/certs/server.crt -text -noout
```

## Compliance Notes

- **GDPR**: Ensure data encryption and right to deletion
- **HIPAA**: If handling health data, enable audit trails
- **SOC 2**: Document all security controls
- **PCI DSS**: If processing payments, isolate payment systems

## Final Verification

Before marking deployment complete:
- [ ] All items in Critical section completed
- [ ] Security scan shows no high/critical vulnerabilities
- [ ] Audit logs are being generated
- [ ] Monitoring alerts are configured
- [ ] Incident response plan is accessible
- [ ] Team has security contact information

---

**Remember**: Security is an ongoing process, not a one-time checklist. Regular reviews and updates are essential for maintaining a secure system.

**Last Updated**: August 2024
**Next Review**: November 2024
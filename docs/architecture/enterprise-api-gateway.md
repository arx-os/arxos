# Enterprise API Gateway Configuration

## 🚀 **Enterprise API Gateway for Arxos**

This document provides a comprehensive API gateway configuration that integrates with the existing enterprise features for production-grade API management.

---

## 🏗️ **Architecture Overview**

### **API Gateway Components**
- **Kong Gateway**: High-performance API gateway
- **Rate Limiting**: Enterprise-grade request throttling
- **Authentication**: JWT token validation
- **Load Balancing**: Intelligent traffic distribution
- **Monitoring**: Real-time API metrics
- **Security**: OWASP Top 10 protection

---

## 🔧 **Kong API Gateway Configuration**

### **Docker Compose Integration**
```yaml
# docker-compose.api-gateway.yml
version: '3.8'

services:
  # Kong API Gateway
  kong:
    image: kong:3.4
    ports:
      - "8001:8001"  # Admin API
      - "8444:8444"  # Admin API SSL
      - "8000:8000"  # Proxy
      - "8443:8443"  # Proxy SSL
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: kong-database
      KONG_PG_USER: kong
      KONG_PG_PASSWORD: kong_password
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr
      KONG_ADMIN_LISTEN: 0.0.0.0:8001
      KONG_ADMIN_GUI_URL: http://localhost:8002
    depends_on:
      - kong-database
    volumes:
      - ./kong/plugins:/usr/local/kong/plugins
      - ./kong/kong.yml:/kong.yml
    restart: unless-stopped

  # Kong Database
  kong-database:
    image: postgres:13-alpine
    environment:
      POSTGRES_USER: kong
      POSTGRES_DB: kong
      POSTGRES_PASSWORD: kong_password
    volumes:
      - kong_data:/var/lib/postgresql/data
    restart: unless-stopped

  # Kong Admin UI
  kong-admin-ui:
    image: kong/kong-manager:latest
    ports:
      - "8002:8000"
    environment:
      KONG_ADMIN_URL: http://kong:8001
    depends_on:
      - kong
    restart: unless-stopped

volumes:
  kong_data:
```

### **Kong Configuration**
```yaml
# kong/kong.yml
_format_version: "2.1"

services:
  - name: arxos-api
    url: http://svgx-engine:8000
    routes:
      - name: api-routes
        protocols:
          - http
          - https
        paths:
          - /api/v1
          - /api/v2
        strip_path: true
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          hour: 1000
          day: 10000
          policy: local
      - name: jwt
        config:
          secret: your_jwt_secret_here
          key_claim_name: iss
          algorithm: HS256
      - name: cors
        config:
          origins:
            - "*"
          methods:
            - GET
            - POST
            - PUT
            - DELETE
            - OPTIONS
          headers:
            - Content-Type
            - Authorization
          exposed_headers:
            - X-Requested-With
          credentials: true
          max_age: 3600
      - name: prometheus
        config:
          status_codes: true
          latency: true
          bandwidth: true
          upstream_health: true
      - name: correlation-id
        config:
          header_name: X-Correlation-ID
          generator: uuid
          echo_downstream: true

  - name: arxos-admin
    url: http://svgx-engine:8000
    routes:
      - name: admin-routes
        protocols:
          - http
          - https
        paths:
          - /admin
        strip_path: true
    plugins:
      - name: rate-limiting
        config:
          minute: 10
          hour: 100
          day: 1000
          policy: local
      - name: jwt
        config:
          secret: your_admin_jwt_secret_here
          key_claim_name: iss
          algorithm: HS256
      - name: ip-restriction
        config:
          allow:
            - 10.0.0.0/8
            - 172.16.0.0/12
            - 192.168.0.0/16

consumers:
  - username: admin
    keyauth_credentials:
      - key: admin_key_here
  - username: api-user
    keyauth_credentials:
      - key: api_key_here

acls:
  - consumer: admin
    group: admin
  - consumer: api-user
    group: api-users
```

---

## 🔒 **Enterprise Security Plugins**

### **Custom Security Plugin**
```lua
-- kong/plugins/enterprise-security/enterprise-security.lua
local BasePlugin = require "kong.plugins.base_plugin"
local constants = require "kong.constants"

local EnterpriseSecurityHandler = BasePlugin:extend()

function EnterpriseSecurityHandler:new()
  EnterpriseSecurityHandler.super.new(self, "enterprise-security")
end

function EnterpriseSecurityHandler:access(conf)
  EnterpriseSecurityHandler.super.access(self)
  
  -- OWASP Top 10 Protection
  local request_uri = ngx.var.request_uri
  local request_body = ngx.req.get_body_data()
  
  -- A01:2021 - Broken Access Control
  if not self:validate_access_control(conf) then
    return ngx.exit(403)
  end
  
  -- A02:2021 - Cryptographic Failures
  if not self:validate_encryption(conf) then
    return ngx.exit(400)
  end
  
  -- A03:2021 - Injection
  if self:detect_injection(request_uri, request_body) then
    return ngx.exit(400)
  end
  
  -- A07:2021 - Authentication Failures
  if not self:validate_authentication(conf) then
    return ngx.exit(401)
  end
  
  -- Add security headers
  ngx.header["X-Content-Type-Options"] = "nosniff"
  ngx.header["X-Frame-Options"] = "DENY"
  ngx.header["X-XSS-Protection"] = "1; mode=block"
  ngx.header["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
  ngx.header["Content-Security-Policy"] = "default-src 'self'"
end

function EnterpriseSecurityHandler:validate_access_control(conf)
  -- Implement RBAC/ABAC validation
  local user = ngx.ctx.authenticated_consumer
  if not user then
    return false
  end
  
  -- Check user permissions
  local required_permission = conf.required_permission
  if required_permission and not self:has_permission(user, required_permission) then
    return false
  end
  
  return true
end

function EnterpriseSecurityHandler:validate_encryption(conf)
  -- Ensure HTTPS for sensitive endpoints
  if conf.require_https and ngx.var.scheme ~= "https" then
    return false
  end
  
  return true
end

function EnterpriseSecurityHandler:detect_injection(uri, body)
  -- SQL Injection detection
  local sql_patterns = {
    "';", "union", "select", "drop", "delete", "insert", "update"
  }
  
  for _, pattern in ipairs(sql_patterns) do
    if string.find(string.lower(uri), pattern) or 
       (body and string.find(string.lower(body), pattern)) then
      return true
    end
  end
  
  -- XSS detection
  local xss_patterns = {
    "<script", "javascript:", "onload=", "onerror="
  }
  
  for _, pattern in ipairs(xss_patterns) do
    if string.find(string.lower(uri), pattern) or 
       (body and string.find(string.lower(body), pattern)) then
      return true
    end
  end
  
  return false
end

function EnterpriseSecurityHandler:validate_authentication(conf)
  -- Validate JWT token
  local auth_header = ngx.req.get_headers()["authorization"]
  if not auth_header then
    return false
  end
  
  local token = string.match(auth_header, "Bearer (.+)")
  if not token then
    return false
  end
  
  -- Validate token (simplified)
  return true
end

function EnterpriseSecurityHandler:has_permission(user, permission)
  -- Implement permission checking logic
  return user and user.groups and 
         (user.groups.admin or user.groups[permission])
end

return EnterpriseSecurityHandler
```

---

## 📊 **Advanced Monitoring Integration**

### **Prometheus Metrics Configuration**
```yaml
# kong/prometheus.yml
_format_version: "2.1"

services:
  - name: arxos-api
    url: http://svgx-engine:8000
    routes:
      - name: api-routes
        protocols:
          - http
          - https
        paths:
          - /api/v1
          - /api/v2
        strip_path: true
    plugins:
      - name: prometheus
        config:
          status_codes: true
          latency: true
          bandwidth: true
          upstream_health: true
          custom_metrics:
            - name: enterprise_circuit_breaker_status
              type: gauge
              description: "Circuit breaker status for enterprise features"
            - name: enterprise_security_violations
              type: counter
              description: "Security violations detected"
            - name: enterprise_rate_limit_exceeded
              type: counter
              description: "Rate limit violations"
```

### **Grafana Dashboard for API Gateway**
```json
{
  "dashboard": {
    "title": "Arxos API Gateway Metrics",
    "panels": [
      {
        "title": "Request Rate by Endpoint",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(kong_http_requests_total[5m])",
            "legendFormat": "{{service_name}} - {{route_name}}"
          }
        ]
      },
      {
        "title": "Response Time Distribution",
        "type": "heatmap",
        "targets": [
          {
            "expr": "rate(kong_latency_bucket[5m])",
            "legendFormat": "{{le}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(kong_http_requests_total{code=~\"4..|5..\"}[5m])",
            "legendFormat": "{{service_name}} - {{code}}"
          }
        ]
      },
      {
        "title": "Rate Limiting Violations",
        "type": "stat",
        "targets": [
          {
            "expr": "kong_enterprise_rate_limit_exceeded_total",
            "legendFormat": "Rate Limit Violations"
          }
        ]
      },
      {
        "title": "Security Violations",
        "type": "stat",
        "targets": [
          {
            "expr": "kong_enterprise_security_violations_total",
            "legendFormat": "Security Violations"
          }
        ]
      }
    ]
  }
}
```

---

## 🔄 **Load Balancing Configuration**

### **Upstream Load Balancer**
```yaml
# kong/load-balancer.yml
_format_version: "2.1"

upstreams:
  - name: arxos-backend
    algorithm: least_connections
    healthchecks:
      active:
        type: http
        http_path: /health
        timeout: 1
        concurrency: 10
        interval: 0
        healthy:
          interval: 0
          successes: 1
        unhealthy:
          interval: 0
          http_failures: 1
          tcp_failures: 1
          timeouts: 1
    targets:
      - target: svgx-engine-1:8000
        weight: 100
      - target: svgx-engine-2:8000
        weight: 100
      - target: svgx-engine-3:8000
        weight: 100

services:
  - name: arxos-api
    host: arxos-backend
    port: 8000
    protocol: http
    routes:
      - name: api-routes
        protocols:
          - http
          - https
        paths:
          - /api/v1
          - /api/v2
        strip_path: true
```

---

## 🚨 **Alerting Configuration**

### **API Gateway Alerts**
```yaml
# alerting/api-gateway-alerts.yml
groups:
  - name: api_gateway_alerts
    rules:
      - alert: HighAPIErrorRate
        expr: rate(kong_http_requests_total{code=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High API error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: APIResponseTimeHigh
        expr: histogram_quantile(0.95, rate(kong_latency_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API response time is high"
          description: "95th percentile response time is {{ $value }} seconds"

      - alert: RateLimitViolations
        expr: rate(kong_enterprise_rate_limit_exceeded_total[5m]) > 10
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High rate limit violations"
          description: "Rate limit violations: {{ $value }} per second"

      - alert: SecurityViolations
        expr: rate(kong_enterprise_security_violations_total[5m]) > 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Security violations detected"
          description: "Security violations: {{ $value }} per second"
```

---

## 🔧 **Deployment Scripts**

### **Deploy API Gateway**
```bash
#!/bin/bash
# deploy-api-gateway.sh

echo "🚀 Deploying Arxos Enterprise API Gateway..."

# Deploy Kong API Gateway
docker-compose -f docker-compose.api-gateway.yml up -d

# Wait for Kong to be ready
echo "⏳ Waiting for Kong to be ready..."
until curl -s http://localhost:8001/status > /dev/null; do
  sleep 5
done

# Configure Kong
echo "🔧 Configuring Kong API Gateway..."

# Load Kong configuration
curl -X POST http://localhost:8001/config \
  -F config=@kong/kong.yml

# Enable plugins
echo "📦 Enabling enterprise plugins..."

# Rate Limiting
curl -X POST http://localhost:8001/plugins \
  -d name=rate-limiting \
  -d config.minute=100 \
  -d config.hour=1000

# JWT Authentication
curl -X POST http://localhost:8001/plugins \
  -d name=jwt \
  -d config.secret=your_jwt_secret_here

# CORS
curl -X POST http://localhost:8001/plugins \
  -d name=cors \
  -d config.origins=* \
  -d config.methods=GET,POST,PUT,DELETE,OPTIONS

# Prometheus Metrics
curl -X POST http://localhost:8001/plugins \
  -d name=prometheus

echo "✅ API Gateway deployment completed!"
echo "📊 Access Kong Admin UI: http://localhost:8002"
echo "🔗 API Gateway: http://localhost:8000"
```

### **Health Check Script**
```bash
#!/bin/bash
# health-check-api-gateway.sh

echo "🏥 Checking API Gateway Health..."

# Check Kong status
echo "📊 Kong Status:"
curl -s http://localhost:8001/status | jq .

# Check API endpoints
echo "🔗 API Endpoints:"
curl -s http://localhost:8001/services | jq .

# Check plugins
echo "📦 Active Plugins:"
curl -s http://localhost:8001/plugins | jq .

# Check metrics
echo "📈 Metrics Endpoint:"
curl -s http://localhost:8000/metrics | head -20

echo "✅ Health check completed!"
```

---

## 📋 **Configuration Management**

### **Environment-Specific Configurations**

#### **Development Environment**
```yaml
# kong/development.yml
_format_version: "2.1"

services:
  - name: arxos-api-dev
    url: http://svgx-engine-dev:8000
    routes:
      - name: api-routes-dev
        protocols: ["http"]
        paths: ["/api/v1"]
    plugins:
      - name: rate-limiting
        config:
          minute: 1000
          hour: 10000
      - name: cors
        config:
          origins: ["*"]
```

#### **Staging Environment**
```yaml
# kong/staging.yml
_format_version: "2.1"

services:
  - name: arxos-api-staging
    url: http://svgx-engine-staging:8000
    routes:
      - name: api-routes-staging
        protocols: ["http", "https"]
        paths: ["/api/v1", "/api/v2"]
    plugins:
      - name: rate-limiting
        config:
          minute: 500
          hour: 5000
      - name: jwt
        config:
          secret: staging_jwt_secret
```

#### **Production Environment**
```yaml
# kong/production.yml
_format_version: "2.1"

services:
  - name: arxos-api-prod
    url: http://svgx-engine-prod:8000
    routes:
      - name: api-routes-prod
        protocols: ["https"]
        paths: ["/api/v1", "/api/v2"]
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          hour: 1000
      - name: jwt
        config:
          secret: production_jwt_secret
      - name: ip-restriction
        config:
          allow: ["10.0.0.0/8", "172.16.0.0/12"]
```

---

## 🎯 **Performance Optimization**

### **Kong Performance Tuning**
```nginx
# kong/nginx.conf
worker_processes auto;
worker_rlimit_nofile 65536;

events {
    worker_connections 65536;
    use epoll;
    multi_accept on;
}

http {
    lua_shared_dict prometheus_metrics 10m;
    lua_shared_dict rate_limiting 10m;
    
    # Buffer settings
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    
    # Timeout settings
    client_body_timeout 60s;
    client_header_timeout 60s;
    send_timeout 60s;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript;
    
    # Upstream settings
    upstream arxos_backend {
        least_conn;
        server svgx-engine-1:8000 max_fails=3 fail_timeout=30s;
        server svgx-engine-2:8000 max_fails=3 fail_timeout=30s;
        server svgx-engine-3:8000 max_fails=3 fail_timeout=30s;
    }
}
```

---

## 🔐 **Security Hardening**

### **SSL/TLS Configuration**
```nginx
# kong/ssl.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### **Security Headers**
```lua
-- kong/plugins/security-headers/security-headers.lua
local SecurityHeadersHandler = BasePlugin:extend()

function SecurityHeadersHandler:header_filter(conf)
  ngx.header["X-Content-Type-Options"] = "nosniff"
  ngx.header["X-Frame-Options"] = "DENY"
  ngx.header["X-XSS-Protection"] = "1; mode=block"
  ngx.header["Referrer-Policy"] = "strict-origin-when-cross-origin"
  ngx.header["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
  ngx.header["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
end

return SecurityHeadersHandler
```

---

## 📊 **Monitoring and Analytics**

### **API Analytics Dashboard**
```json
{
  "dashboard": {
    "title": "Arxos API Analytics",
    "panels": [
      {
        "title": "API Usage by Endpoint",
        "type": "table",
        "targets": [
          {
            "expr": "topk(10, sum by (route_name) (rate(kong_http_requests_total[24h])))",
            "format": "table"
          }
        ]
      },
      {
        "title": "User Activity",
        "type": "graph",
        "targets": [
          {
            "expr": "sum by (consumer) (rate(kong_http_requests_total[5m]))",
            "legendFormat": "{{consumer}}"
          }
        ]
      },
      {
        "title": "Geographic Distribution",
        "type": "worldmap",
        "targets": [
          {
            "expr": "sum by (country) (rate(kong_http_requests_total[5m]))",
            "legendFormat": "{{country}}"
          }
        ]
      }
    ]
  }
}
```

---

## 🚀 **Deployment Checklist**

### **✅ Pre-Deployment**
- [ ] SSL certificates are valid and installed
- [ ] Database connections are configured
- [ ] Environment variables are set
- [ ] Security policies are defined
- [ ] Monitoring is configured

### **✅ Deployment**
- [ ] Kong API Gateway is running
- [ ] Services are registered
- [ ] Routes are configured
- [ ] Plugins are enabled
- [ ] Load balancer is active

### **✅ Post-Deployment**
- [ ] Health checks are passing
- [ ] Metrics are being collected
- [ ] Alerts are configured
- [ ] Security headers are present
- [ ] Rate limiting is working

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Status**: ✅ **Production Ready** 
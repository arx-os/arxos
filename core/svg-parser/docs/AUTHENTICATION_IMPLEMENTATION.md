# Authentication & Security Implementation

## Overview

This document describes the comprehensive authentication and security implementation for the Arxos SVG-BIM Integration System. The system implements JWT-based authentication with role-based access control (RBAC), comprehensive security measures, and audit logging.

## Architecture

### Components

1. **JWT Authentication** (`utils/auth.py`)
   - Token creation and validation
   - Password hashing and verification
   - Role-based permissions

2. **Access Control Service** (`services/access_control.py`)
   - Role management and inheritance
   - Permission checking
   - Audit logging

3. **Authentication Middleware** (`middleware/auth.py`)
   - Request authentication
   - Role-based access control
   - Token refresh handling

4. **Security Middleware** (`middleware/security.py`)
   - Rate limiting
   - IP filtering
   - Security headers

5. **User Management** (`routers/auth.py`)
   - User registration and login
   - Profile management
   - Admin endpoints

## JWT Authentication Implementation

### Token Structure

```json
{
  "id": "user-uuid",
  "username": "john_doe",
  "roles": ["viewer", "editor"],
  "is_active": true,
  "jti": "token-unique-id",
  "iat": "2024-01-01T00:00:00Z",
  "exp": "2024-01-01T00:30:00Z",
  "type": "access",
  "iss": "arxos-svg-bim",
  "aud": "arxos-users"
}
```

### Security Features

- **Token Revocation**: Tokens can be revoked using JTI (JWT ID)
- **Enhanced Validation**: Checks issuer, audience, and required claims
- **Password Strength**: Enforces strong password requirements
- **Rate Limiting**: Prevents brute force attacks
- **Audit Logging**: Comprehensive logging of all authentication events

## Role-Based Access Control (RBAC)

### Role Hierarchy

```
superuser
├── admin
│   ├── editor
│   │   └── viewer
│   └── maintenance
└── auditor
```

### Roles and Permissions

| Role | Description | Permissions |
|------|-------------|-------------|
| **viewer** | Read-only access | View symbols, buildings, floors |
| **editor** | Create and edit content | Create/update symbols, export data |
| **admin** | System administration | User management, system settings |
| **superuser** | Complete system control | All permissions |
| **maintenance** | Maintenance operations | System monitoring, reports |
| **auditor** | Audit and compliance | Audit logs, compliance reports |

### Permission Levels

- **NONE**: No access
- **OWN**: Only own resources
- **PROJECT**: Project-level access
- **ORGANIZATION**: Organization-level access
- **GLOBAL**: Global access

## Security Features

### Password Security

```python
# Password hashing with bcrypt
hashed_password = hash_password("SecurePassword123!")

# Password verification
is_valid = verify_password("SecurePassword123!", hashed_password)

# Password strength validation
is_strong, message = validate_password_strength(password)
```

### Rate Limiting

- **Default**: 60 requests per minute per IP
- **Configurable**: Per-endpoint rate limits
- **IP-based**: Tracks requests by client IP
- **Automatic cleanup**: Removes old request records

### Security Headers

```python
# Security headers added to all responses
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

## API Endpoints

### Authentication Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/auth/register` | POST | Register new user | No |
| `/auth/login` | POST | Login user | No |
| `/auth/refresh` | POST | Refresh tokens | No |
| `/auth/me` | GET | Get current user profile | Yes |
| `/auth/me` | PUT | Update current user profile | Yes |
| `/auth/change-password` | POST | Change password | Yes |
| `/auth/logout` | POST | Logout user | Yes |

### Admin Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/auth/users` | GET | List all users | Admin |
| `/auth/users/{user_id}` | GET | Get user details | Admin |
| `/auth/users/{user_id}` | PUT | Update user | Admin |
| `/auth/users/{user_id}` | DELETE | Delete user | Admin |
| `/auth/users/{user_id}/activate` | POST | Activate user | Admin |
| `/auth/users/{user_id}/deactivate` | POST | Deactivate user | Admin |
| `/auth/audit-logs` | GET | Get audit logs | Admin |

## Usage Examples

### User Registration

```python
import requests

# Register new user
response = requests.post("http://localhost:8000/auth/register", json={
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123!",
    "full_name": "John Doe",
    "roles": ["viewer"]
})

print(response.json())
```

### User Login

```python
# Login user
response = requests.post("http://localhost:8000/auth/login", data={
    "username": "john_doe",
    "password": "SecurePassword123!"
})

data = response.json()
access_token = data["access_token"]
refresh_token = data["refresh_token"]
```

### Authenticated Requests

```python
# Use access token for authenticated requests
headers = {"Authorization": f"Bearer {access_token}"}

# Get user profile
response = requests.get("http://localhost:8000/auth/me", headers=headers)
user_data = response.json()

# Update user profile
response = requests.put("http://localhost:8000/auth/me", 
                       headers=headers,
                       json={"full_name": "John Smith"})
```

### Token Refresh

```python
# Refresh access token
response = requests.post("http://localhost:8000/auth/refresh", 
                        json={"refresh_token": refresh_token})

data = response.json()
new_access_token = data["access_token"]
new_refresh_token = data["refresh_token"]
```

## Middleware Configuration

### Authentication Middleware

```python
from middleware.auth import AuthenticationMiddleware

# Configure authentication middleware
auth_middleware = AuthenticationMiddleware(
    app=app,
    require_auth=True,
    excluded_paths=[
        "/auth/login",
        "/auth/register",
        "/auth/refresh",
        "/docs",
        "/health"
    ]
)
```

### Security Middleware

```python
from middleware.security import SecurityMiddleware

# Configure security middleware
security_middleware = SecurityMiddleware(
    app=app,
    rate_limit_per_minute=60,
    blocked_ips=["192.168.1.100"],
    allowed_ips=["127.0.0.1", "192.168.1.0/24"]
)
```

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    roles JSON DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until DATETIME,
    user_metadata JSON
);
```

### Audit Logs Table

```sql
CREATE TABLE audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(255) NOT NULL,
    resource_id VARCHAR(255) NOT NULL,
    details JSON NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    success BOOLEAN NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## Security Best Practices

### 1. Token Management

- **Short-lived access tokens**: 30 minutes
- **Long-lived refresh tokens**: 7 days
- **Token revocation**: Immediate invalidation
- **Secure storage**: Client-side secure storage

### 2. Password Security

- **Strong hashing**: bcrypt with 12 rounds
- **Password strength**: Minimum 8 characters with complexity
- **Salt generation**: Unique salt per password
- **Rate limiting**: Prevent brute force attacks

### 3. Access Control

- **Principle of least privilege**: Minimum required permissions
- **Role inheritance**: Hierarchical permission system
- **Resource-level permissions**: Granular access control
- **Audit logging**: Comprehensive activity tracking

### 4. Network Security

- **HTTPS only**: All communications encrypted
- **Security headers**: Protection against common attacks
- **IP filtering**: Block suspicious IPs
- **Rate limiting**: Prevent abuse

## Testing

### Running Tests

```bash
# Run all authentication tests
pytest tests/test_authentication.py -v

# Run specific test class
pytest tests/test_authentication.py::TestJWTAuthentication -v

# Run with coverage
pytest tests/test_authentication.py --cov=utils.auth --cov=services.access_control
```

### Test Coverage

- **JWT Authentication**: Token creation, validation, expiration
- **Password Security**: Hashing, verification, strength validation
- **Role-Based Access**: Permission checking, role inheritance
- **User Management**: CRUD operations, role assignment
- **Security Middleware**: Rate limiting, IP filtering
- **Integration Tests**: End-to-end authentication flow

## Monitoring and Logging

### Audit Events

The system logs comprehensive audit events:

- **Authentication**: Login success/failure, logout
- **Authorization**: Access granted/denied
- **User Management**: User creation, updates, deletion
- **Security**: Suspicious activity, rate limit violations

### Log Format

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "event_type": "login_success",
  "user_id": "user-uuid",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "details": {
    "login_method": "password",
    "roles": ["viewer"]
  },
  "success": true
}
```

## Deployment Considerations

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Security Configuration
RATE_LIMIT_PER_MINUTE=60
BLOCKED_IPS=192.168.1.100,10.0.0.50
ALLOWED_IPS=127.0.0.1,192.168.1.0/24
```

### Production Security

1. **Use strong JWT secret**: 256-bit random key
2. **Enable HTTPS**: TLS 1.3 encryption
3. **Configure firewalls**: Network-level protection
4. **Monitor logs**: Real-time security monitoring
5. **Regular updates**: Keep dependencies updated
6. **Backup strategy**: Secure data backups

## Troubleshooting

### Common Issues

1. **Token Expired**
   - Use refresh token to get new access token
   - Check token expiration settings

2. **Access Denied**
   - Verify user has required roles
   - Check permission inheritance

3. **Rate Limited**
   - Wait for rate limit reset
   - Check rate limit configuration

4. **Password Issues**
   - Verify password strength requirements
   - Check password hashing configuration

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

1. **Multi-factor Authentication**: TOTP, SMS, email verification
2. **OAuth Integration**: Google, GitHub, Microsoft authentication
3. **Advanced RBAC**: Dynamic permissions, resource-level access
4. **Session Management**: Redis-based session storage
5. **Security Analytics**: Threat detection, anomaly detection
6. **Compliance**: GDPR, SOC2, ISO27001 compliance features

## Conclusion

The authentication and security implementation provides a robust, scalable foundation for the Arxos SVG-BIM Integration System. With comprehensive JWT authentication, role-based access control, and extensive security measures, the system ensures secure access while maintaining flexibility for future enhancements. 
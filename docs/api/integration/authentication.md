# API Authentication Guide

## 🎯 **Overview**

Arxos provides multiple authentication methods for API access, ensuring secure and flexible integration with the platform. This guide covers all authentication methods, setup procedures, and best practices.

**Supported Methods:**
- **API Keys**: Simple, long-lived authentication
- **JWT Tokens**: Short-lived, secure tokens
- **OAuth 2.0**: Standard OAuth flow for third-party applications
- **Service Accounts**: Enterprise-grade service authentication

---

## 🔑 **Authentication Methods**

### **1. API Keys**

API keys are the simplest authentication method, suitable for server-to-server communication and long-term integrations.

#### **Creating API Keys**

##### **Web Interface**
1. Navigate to **Settings** → **API Keys**
2. Click **"Create New API Key"**
3. Enter a descriptive name
4. Select permissions (read/write/admin)
5. Click **"Generate Key"**
6. Copy and securely store the key

##### **CLI**
```bash
# Create API key
arx api key create "My Integration" --permissions read,write

# List API keys
arx api key list

# Delete API key
arx api key delete "key_id"
```

#### **Using API Keys**

##### **HTTP Headers**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     https://api.arxos.com/v1/buildings
```

##### **Python SDK**
```python
import arxos

# Initialize client with API key
client = arxos.Client(api_key="YOUR_API_KEY")

# Make authenticated requests
buildings = client.buildings.list()
```

##### **JavaScript SDK**
```javascript
import { ArxosClient } from '@arxos/sdk';

// Initialize client with API key
const client = new ArxosClient({
  apiKey: 'YOUR_API_KEY'
});

// Make authenticated requests
const buildings = await client.buildings.list();
```

### **2. JWT Tokens**

JWT tokens provide short-lived, secure authentication with automatic refresh capabilities.

#### **Obtaining JWT Tokens**

##### **Username/Password**
```bash
# Get JWT token
curl -X POST https://api.arxos.com/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "user@example.com", "password": "password"}'
```

##### **Python SDK**
```python
import arxos

# Authenticate and get token
client = arxos.Client()
token = client.auth.login("user@example.com", "password")

# Token is automatically managed
buildings = client.buildings.list()
```

##### **JavaScript SDK**
```javascript
import { ArxosClient } from '@arxos/sdk';

// Authenticate and get token
const client = new ArxosClient();
await client.auth.login('user@example.com', 'password');

// Token is automatically managed
const buildings = await client.buildings.list();
```

#### **Token Management**

##### **Refresh Tokens**
```python
# Tokens are automatically refreshed
client = arxos.Client()
client.auth.login("user@example.com", "password")

# Token will be refreshed when needed
buildings = client.buildings.list()
```

##### **Manual Token Management**
```python
import arxos

# Get token manually
client = arxos.Client()
token = client.auth.get_token("user@example.com", "password")

# Use token in requests
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("https://api.arxos.com/v1/buildings", headers=headers)
```

### **3. OAuth 2.0**

OAuth 2.0 is the recommended authentication method for third-party applications and user-facing integrations.

#### **OAuth Flow Setup**

##### **Register Application**
1. Navigate to **Settings** → **OAuth Applications**
2. Click **"Register New Application"**
3. Enter application details:
   - **Name**: Your application name
   - **Redirect URI**: Your callback URL
   - **Scopes**: Required permissions
4. Copy the **Client ID** and **Client Secret**

##### **Authorization Code Flow**
```python
import arxos

# Initialize OAuth client
client = arxos.OAuthClient(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    redirect_uri="https://your-app.com/callback"
)

# Generate authorization URL
auth_url = client.get_authorization_url(
    scope=["read", "write"],
    state="random_state_string"
)

# Redirect user to auth_url
# User will be redirected back to your callback URL with a code

# Exchange code for token
token = client.exchange_code_for_token(authorization_code)
```

##### **Client Credentials Flow**
```python
import arxos

# For server-to-server communication
client = arxos.OAuthClient(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET"
)

# Get access token
token = client.get_client_credentials_token(scope=["read", "write"])

# Use token
api_client = arxos.Client(access_token=token)
buildings = api_client.buildings.list()
```

#### **OAuth Scopes**

| Scope | Description | Access Level |
|-------|-------------|--------------|
| `read` | Read access to buildings and data | Basic |
| `write` | Create and update buildings | Standard |
| `admin` | Full administrative access | Advanced |
| `export` | Export building data | Standard |
| `import` | Import building data | Standard |
| `work_orders` | Work order management | Standard |
| `analytics` | Access to analytics data | Advanced |

### **4. Service Accounts**

Service accounts provide enterprise-grade authentication for automated systems and integrations.

#### **Creating Service Accounts**

##### **Enterprise Dashboard**
1. Navigate to **Enterprise** → **Service Accounts**
2. Click **"Create Service Account"**
3. Enter account details:
   - **Name**: Descriptive name
   - **Description**: Purpose of the account
   - **Permissions**: Required access levels
4. Download the service account key file

#### **Using Service Accounts**

##### **Python SDK**
```python
import arxos

# Load service account from file
client = arxos.Client.from_service_account("path/to/service-account.json")

# Or load from environment variable
import os
client = arxos.Client.from_service_account_json(os.environ["ARXOS_SERVICE_ACCOUNT"])

# Make authenticated requests
buildings = client.buildings.list()
```

##### **Environment Variables**
```bash
# Set service account environment variable
export ARXOS_SERVICE_ACCOUNT='{"type": "service_account", ...}'

# Use in your application
python your_integration.py
```

---

## 🔐 **Security Best Practices**

### **API Key Security**

#### **Storage**
- **Never commit API keys to version control**
- Store keys in environment variables or secure key management systems
- Use different keys for different environments (dev/staging/prod)

#### **Rotation**
```bash
# Rotate API key
arx api key rotate "old_key_id" --new-name "Updated Key"
```

#### **Monitoring**
```bash
# Check API key usage
arx api key usage "key_id"

# List recent API calls
arx api logs --key "key_id"
```

### **JWT Token Security**

#### **Token Storage**
- Store tokens securely in memory or encrypted storage
- Never store tokens in localStorage (web applications)
- Implement automatic token refresh

#### **Token Validation**
```python
import arxos

# Validate token
client = arxos.Client()
is_valid = client.auth.validate_token(token)

# Get token information
token_info = client.auth.get_token_info(token)
```

### **OAuth Security**

#### **State Parameter**
```python
import secrets

# Generate secure state parameter
state = secrets.token_urlsafe(32)

# Include in authorization request
auth_url = client.get_authorization_url(state=state)

# Verify state in callback
if received_state != original_state:
    raise SecurityError("State mismatch")
```

#### **PKCE (Proof Key for Code Exchange)**
```python
import arxos

# Generate PKCE parameters
code_verifier = arxos.auth.generate_code_verifier()
code_challenge = arxos.auth.generate_code_challenge(code_verifier)

# Include in authorization request
auth_url = client.get_authorization_url(
    code_challenge=code_challenge,
    code_challenge_method="S256"
)

# Exchange code with verifier
token = client.exchange_code_for_token(
    authorization_code,
    code_verifier=code_verifier
)
```

---

## 🚨 **Error Handling**

### **Common Authentication Errors**

#### **401 Unauthorized**
```python
try:
    buildings = client.buildings.list()
except arxos.AuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Re-authenticate or refresh token
```

#### **403 Forbidden**
```python
try:
    buildings = client.buildings.create(data)
except arxos.PermissionError as e:
    print(f"Insufficient permissions: {e}")
    # Check required scopes or permissions
```

#### **429 Too Many Requests**
```python
import time

try:
    buildings = client.buildings.list()
except arxos.RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    time.sleep(e.retry_after)
    # Retry request
```

### **Token Refresh Handling**

```python
import arxos

client = arxos.Client()

try:
    # Make API call
    buildings = client.buildings.list()
except arxos.TokenExpiredError:
    # Token will be automatically refreshed
    buildings = client.buildings.list()
except arxos.RefreshTokenExpiredError:
    # Re-authenticate user
    client.auth.login("user@example.com", "password")
    buildings = client.buildings.list()
```

---

## 📊 **Rate Limits**

### **API Rate Limits**

| Authentication Method | Rate Limit | Window |
|----------------------|------------|---------|
| API Key | 1000 requests/minute | 1 minute |
| JWT Token | 500 requests/minute | 1 minute |
| OAuth 2.0 | 200 requests/minute | 1 minute |
| Service Account | 5000 requests/minute | 1 minute |

### **Rate Limit Headers**

```python
import arxos

client = arxos.Client(api_key="YOUR_API_KEY")

# Make request
response = client.buildings.list()

# Check rate limit headers
print(f"Remaining: {response.headers['X-RateLimit-Remaining']}")
print(f"Reset: {response.headers['X-RateLimit-Reset']}")
```

---

## 🔧 **SDK Configuration**

### **Python SDK**

#### **Basic Configuration**
```python
import arxos

# Initialize with API key
client = arxos.Client(api_key="YOUR_API_KEY")

# Initialize with JWT token
client = arxos.Client(access_token="YOUR_JWT_TOKEN")

# Initialize with OAuth
client = arxos.Client(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET"
)
```

#### **Advanced Configuration**
```python
import arxos

# Custom configuration
client = arxos.Client(
    api_key="YOUR_API_KEY",
    base_url="https://custom.arxos.com",
    timeout=30,
    retries=3
)
```

### **JavaScript SDK**

#### **Basic Configuration**
```javascript
import { ArxosClient } from '@arxos/sdk';

// Initialize with API key
const client = new ArxosClient({
  apiKey: 'YOUR_API_KEY'
});

// Initialize with JWT token
const client = new ArxosClient({
  accessToken: 'YOUR_JWT_TOKEN'
});

// Initialize with OAuth
const client = new ArxosClient({
  clientId: 'YOUR_CLIENT_ID',
  clientSecret: 'YOUR_CLIENT_SECRET'
});
```

#### **Advanced Configuration**
```javascript
import { ArxosClient } from '@arxos/sdk';

// Custom configuration
const client = new ArxosClient({
  apiKey: 'YOUR_API_KEY',
  baseUrl: 'https://custom.arxos.com',
  timeout: 30000,
  retries: 3
});
```

---

## 📝 **Examples**

### **Complete Integration Example**

```python
import arxos
import os

# Initialize client
client = arxos.Client(api_key=os.environ["ARXOS_API_KEY"])

try:
    # Create building
    building = client.buildings.create({
        "name": "My Building",
        "type": "commercial",
        "address": "123 Main St"
    })
    
    # Add systems
    client.buildings.systems.create(building.id, {
        "type": "hvac",
        "name": "Main HVAC System"
    })
    
    # Export building
    export_data = client.buildings.export(building.id, format="ifc")
    
    print(f"Successfully created building: {building.name}")
    
except arxos.AuthenticationError:
    print("Authentication failed. Check your API key.")
except arxos.PermissionError:
    print("Insufficient permissions for this operation.")
except arxos.RateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after} seconds.")
```

### **Web Application Example**

```javascript
import { ArxosClient } from '@arxos/sdk';

// Initialize OAuth client
const client = new ArxosClient({
  clientId: process.env.ARXOS_CLIENT_ID,
  clientSecret: process.env.ARXOS_CLIENT_SECRET,
  redirectUri: 'https://myapp.com/callback'
});

// Handle OAuth callback
app.get('/callback', async (req, res) => {
  try {
    const { code, state } = req.query;
    
    // Verify state parameter
    if (state !== req.session.oauthState) {
      throw new Error('State mismatch');
    }
    
    // Exchange code for token
    const token = await client.auth.exchangeCodeForToken(code);
    
    // Store token securely
    req.session.accessToken = token.access_token;
    
    res.redirect('/dashboard');
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Make authenticated API calls
app.get('/buildings', async (req, res) => {
  try {
    const buildings = await client.buildings.list({
      accessToken: req.session.accessToken
    });
    
    res.json(buildings);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

---

## ❓ **Getting Help**

### **Support Resources**
- **API Documentation**: Complete API reference
- **SDK Documentation**: Language-specific guides
- **Community Forum**: Connect with other developers
- **Email Support**: Contact support team

### **Common Issues**
- **Token Expiration**: Implement automatic refresh
- **Rate Limiting**: Implement exponential backoff
- **Permission Errors**: Check required scopes
- **Network Issues**: Implement retry logic

---

**Need Help?** Contact our support team or check the [API Reference](../reference/) for detailed endpoint documentation. 
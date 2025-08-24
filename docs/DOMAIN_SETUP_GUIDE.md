# Domain Setup Guide for arxos.io & arxos.dev

## 🎯 Goal: Private Testing & Sharing Environment

Use your domains for internal testing and controlled sharing without public access.

---

## 📋 Option 1: **Password-Protected Staging** (Simplest)

### Setup:
1. **Host on Cloud Provider** (DigitalOcean, AWS, etc.)
2. **Basic Auth at Nginx Level**
3. **SSL with Let's Encrypt**

### Implementation:

#### A. Server Setup (Ubuntu/Debian)
```bash
# 1. Point DNS A records to your server IP
# arxos.io → YOUR_SERVER_IP
# *.arxos.io → YOUR_SERVER_IP (wildcard)

# 2. Install dependencies
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx

# 3. Create auth file
sudo htpasswd -c /etc/nginx/.htpasswd demo_user
# Enter password when prompted
```

#### B. Nginx Configuration
```nginx
# /etc/nginx/sites-available/arxos.io
server {
    server_name arxos.io www.arxos.io demo.arxos.io;
    
    # Basic authentication
    auth_basic "Arxos Private Demo";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # AI Service
    location /ai/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
    
    listen 80;
}
```

#### C. SSL Setup
```bash
sudo certbot --nginx -d arxos.io -d www.arxos.io -d demo.arxos.io
```

---

## 📋 Option 2: **VPN-Only Access** (Most Secure)

### Setup:
1. **WireGuard or Tailscale VPN**
2. **Domains resolve to private IPs**
3. **No public access at all**

### Tailscale Implementation (Easiest):

```bash
# 1. Install Tailscale on server
curl -fsSL https://tailscale.com/install.sh | sh

# 2. Connect to Tailscale network
sudo tailscale up

# 3. Get Tailscale IP (100.x.x.x)
tailscale ip -4

# 4. Configure DNS (in Tailscale admin)
# arxos.io → 100.x.x.x (Tailscale IP)

# 5. Share access via Tailscale
tailscale share arxos.io --with user@email.com
```

### Benefits:
- Zero public exposure
- End-to-end encryption
- Easy user management
- Works behind any firewall

---

## 📋 Option 3: **Cloudflare Access** (Best Balance)

### Setup:
1. **Cloudflare Zero Trust (Free tier available)**
2. **Email/OAuth authentication**
3. **No VPN needed**

### Implementation:

#### A. Cloudflare Setup
```yaml
# 1. Add domains to Cloudflare
# 2. Enable Cloudflare Access

# 3. Create Access Policy
Policy Name: Arxos Demo Access
Include:
  - Emails ending in: @yourcompany.com
  - Specific emails: 
    - investor@example.com
    - partner@example.com

# 4. Create Access Application
Name: Arxos Demo
Domain: demo.arxos.io
Session Duration: 24 hours
```

#### B. Server Configuration
```nginx
# Only accept traffic from Cloudflare
# /etc/nginx/sites-available/arxos.io

server {
    server_name demo.arxos.io;
    
    # Cloudflare IP validation
    set_real_ip_from 103.21.244.0/22;
    set_real_ip_from 103.22.200.0/22;
    # ... (add all Cloudflare IPs)
    real_ip_header CF-Connecting-IP;
    
    # Verify Cloudflare Access JWT
    location / {
        # Your app proxy config
        proxy_pass http://localhost:3000;
    }
}
```

---

## 📋 Option 4: **IP Whitelist + Auth** (Quick & Simple)

### Implementation:
```nginx
# /etc/nginx/sites-available/arxos.io

geo $allowed_ip {
    default 0;
    # Your office
    203.0.113.0/24 1;
    # Your home
    198.51.100.42 1;
    # Partner office
    192.0.2.0/24 1;
}

server {
    server_name arxos.io;
    
    if ($allowed_ip = 0) {
        return 403;
    }
    
    # Additional password protection
    auth_basic "Arxos Demo";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    location / {
        proxy_pass http://localhost:3000;
    }
}
```

---

## 🚀 Recommended Setup: **Cloudflare Access + Subdomains**

### Domain Structure:
```
arxos.io              → Landing page (public, coming soon)
demo.arxos.io         → Demo environment (Cloudflare Access)
api.arxos.io          → API endpoint (Cloudflare Access)
dev.arxos.dev         → Development environment (VPN only)
staging.arxos.dev     → Staging environment (IP whitelist)
```

### Step-by-Step Implementation:

#### 1. DNS Configuration
```bash
# Cloudflare DNS Records
A    arxos.io          → YOUR_SERVER_IP
A    demo.arxos.io     → YOUR_SERVER_IP  (Proxied)
A    api.arxos.io      → YOUR_SERVER_IP  (Proxied)
A    arxos.dev         → YOUR_DEV_SERVER_IP
A    *.arxos.dev       → YOUR_DEV_SERVER_IP
```

#### 2. Docker Compose for Easy Deployment
```yaml
# docker-compose.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - backend
      - ai_service
      - frontend

  backend:
    build: ./core/backend
    environment:
      - DATABASE_URL=postgres://arxos:password@db:5432/arxos
      - JWT_SECRET=${JWT_SECRET}
    ports:
      - "8080:8080"

  ai_service:
    build: ./ai_service
    environment:
      - BACKEND_URL=http://backend:8080
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    environment:
      - API_URL=https://api.arxos.io
    ports:
      - "3000:3000"

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=arxos
      - POSTGRES_USER=arxos
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### 3. Deployment Script
```bash
#!/bin/bash
# deploy.sh

# For demo.arxos.io
deploy_demo() {
    ssh demo.arxos.io << 'EOF'
        cd /opt/arxos
        git pull origin main
        docker-compose down
        docker-compose up -d --build
        docker-compose logs -f
    EOF
}

# For dev.arxos.dev
deploy_dev() {
    ssh dev.arxos.dev << 'EOF'
        cd /opt/arxos
        git pull origin develop
        make stop
        make start
    EOF
}
```

---

## 🔐 Security Checklist

### Essential Security Measures:
- [ ] SSL/TLS certificates (Let's Encrypt)
- [ ] Authentication layer (Basic Auth minimum)
- [ ] Rate limiting (Nginx or Cloudflare)
- [ ] DDoS protection (Cloudflare)
- [ ] Regular security updates
- [ ] Backup strategy
- [ ] Log monitoring
- [ ] Firewall rules (ufw or iptables)

### Nginx Security Headers:
```nginx
# Add to server block
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

---

## 📱 Sharing Access

### For Investors/Partners:

#### Option A: Temporary Access
```bash
# Create temporary user
sudo htpasswd /etc/nginx/.htpasswd investor_demo
# Share: Username: investor_demo, Password: [generated]
# Expires: Delete after demo
```

#### Option B: Magic Link (Cloudflare Access)
```
1. Go to demo.arxos.io
2. Enter email
3. Receive one-time code
4. Access for 24 hours
```

#### Option C: Demo Account
```javascript
// Create demo account with limited permissions
{
  username: "demo@arxos.io",
  password: "ChangeAfterEachDemo",
  permissions: ["view", "upload_sample"],
  expires: "2024-01-31"
}
```

---

## 🚦 Quick Start Commands

### Initial Setup:
```bash
# 1. Configure DNS
# Point arxos.io to your server

# 2. Clone and setup
ssh your-server
git clone https://github.com/yourrepo/arxos.git /opt/arxos
cd /opt/arxos

# 3. Run setup script
cat > setup-domain.sh << 'EOF'
#!/bin/bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Nginx
apt install nginx certbot python3-certbot-nginx -y

# Setup SSL
certbot --nginx -d demo.arxos.io

# Start services
docker-compose up -d
EOF

chmod +x setup-domain.sh
./setup-domain.sh
```

---

## 📊 Monitoring & Analytics

### Basic Monitoring:
```bash
# Install monitoring
apt install htop nethogs iotop -y

# View access logs
tail -f /var/log/nginx/access.log | grep -v "bot"

# Monitor resources
htop  # CPU/Memory
nethogs  # Network per process
iotop  # Disk I/O
```

### Analytics (Privacy-Focused):
```html
<!-- Add to demo/index.html -->
<!-- Plausible Analytics (self-hosted) -->
<script defer data-domain="demo.arxos.io" 
        src="https://plausible.arxos.io/js/script.js"></script>
```

---

## 🎯 Recommended Approach

For your use case, I recommend:

1. **arxos.io** → Cloudflare Access
   - Easy sharing with investors
   - No VPN needed
   - Professional appearance
   - Email-based access control

2. **arxos.dev** → Tailscale VPN
   - Development/testing only
   - Complete privacy
   - Easy team access
   - No public exposure

3. **Implementation Priority:**
   1. Set up arxos.dev with Tailscale (1 hour)
   2. Configure demo.arxos.io with Cloudflare Access (2 hours)
   3. Add monitoring and analytics (1 hour)
   4. Document access procedures (30 minutes)

---

## 📝 Environment Variables

Create `.env.production`:
```bash
# Server Configuration
DOMAIN=arxos.io
DEMO_DOMAIN=demo.arxos.io
API_DOMAIN=api.arxos.io

# Security
JWT_SECRET=your-secret-key-here
SESSION_SECRET=your-session-secret
ALLOWED_ORIGINS=https://demo.arxos.io,https://arxos.io

# Database
DATABASE_URL=postgres://arxos:password@localhost:5432/arxos

# Cloudflare (optional)
CF_ACCESS_CLIENT_ID=your-client-id
CF_ACCESS_CLIENT_SECRET=your-client-secret

# Basic Auth Users (comma-separated)
AUTH_USERS=demo:password,investor:temppass123
```

---

## 🚀 Next Steps

1. **Choose your approach** (Cloudflare Access recommended)
2. **Set up DNS records** in your domain registrar
3. **Provision a server** (DigitalOcean droplet, AWS EC2, etc.)
4. **Run the setup script** provided above
5. **Test access control** before sharing
6. **Create documentation** for users

Need help with any specific step? Let me know which approach you prefer!
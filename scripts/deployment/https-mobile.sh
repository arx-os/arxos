#!/bin/bash

# HTTPS Mobile Test Script for iOS Camera Access
# iOS requires HTTPS for camera access in some cases

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Setting up HTTPS for iPhone camera access...${NC}"

# Get local IP
if [[ "$OSTYPE" == "darwin"* ]]; then
    LOCAL_IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1)
else
    LOCAL_IP=$(hostname -I | awk '{print $1}')
fi

echo -e "${GREEN}Your local IP: $LOCAL_IP${NC}"

# Check if mkcert is installed
if ! command -v mkcert &> /dev/null; then
    echo -e "${YELLOW}Installing mkcert for HTTPS certificates...${NC}"
    brew install mkcert
    mkcert -install
fi

# Create certificates directory
mkdir -p certs
cd certs

# Generate certificate for local IP
echo -e "${YELLOW}Generating HTTPS certificate...${NC}"
mkcert $LOCAL_IP localhost 127.0.0.1 ::1

# Start HTTPS server
cd ..
echo -e "${GREEN}Starting HTTPS server...${NC}"

# Use Python's built-in HTTPS server
cat > serve-https.py << 'EOF'
import ssl
import http.server
import socketserver
import sys
import os

PORT = 8443
Handler = http.server.SimpleHTTPRequestHandler

# Change to demo directory
os.chdir('demo')

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(
    f"../certs/{sys.argv[1]}+3.pem",
    f"../certs/{sys.argv[1]}+3-key.pem"
)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    print(f"HTTPS Server running on https://{sys.argv[1]}:{PORT}")
    httpd.serve_forever()
EOF

echo -e "${GREEN}✅ HTTPS Ready for iPhone testing!${NC}"
echo ""
echo -e "${BLUE}On your iPhone:${NC}"
echo "1. Open Safari"
echo "2. Go to: ${GREEN}https://$LOCAL_IP:8443/camera-trace.html${NC}"
echo "3. Accept the certificate warning (it's safe - we just created it)"
echo "4. Camera access should now work!"
echo ""
echo -e "${YELLOW}Starting server...${NC}"

python3 serve-https.py $LOCAL_IP
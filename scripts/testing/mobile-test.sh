#!/bin/bash

# Arxos Mobile Testing Script
# Access your local development server from iPhone on same network

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Setting up Arxos for iPhone testing...${NC}"

# Get local IP address
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1)
else
    # Linux
    LOCAL_IP=$(hostname -I | awk '{print $1}')
fi

if [ -z "$LOCAL_IP" ]; then
    echo -e "${RED}Could not detect local IP address${NC}"
    echo "Please check your network connection"
    exit 1
fi

echo -e "${GREEN}Your local IP: $LOCAL_IP${NC}"

# Check if services are running
if ! lsof -ti:8080 >/dev/null 2>&1; then
    echo -e "${YELLOW}Starting services...${NC}"
    make start
    sleep 5
fi

# Update CORS settings to allow mobile access
echo -e "${YELLOW}Configuring CORS for mobile access...${NC}"
export ALLOWED_ORIGINS="http://$LOCAL_IP:3000,http://localhost:3000"

# Start services with mobile-friendly settings
echo -e "${YELLOW}Restarting backend with mobile CORS...${NC}"
pkill -f "go run.*main.go" 2>/dev/null || true
cd core/backend
go run main.go &
cd ../..

echo -e "${GREEN}✅ Ready for iPhone testing!${NC}"
echo ""
echo -e "${BLUE}On your iPhone:${NC}"
echo "1. Make sure you're on the same WiFi network"
echo "2. Open Safari"
echo "3. Go to: ${GREEN}http://$LOCAL_IP:3000/demo${NC}"
echo ""
echo "Or scan this QR code:"
echo ""

# Generate QR code if qrencode is installed
if command -v qrencode &> /dev/null; then
    qrencode -t UTF8 "http://$LOCAL_IP:3000/demo"
else
    echo "Install qrencode to see QR code: brew install qrencode"
fi

echo ""
echo -e "${YELLOW}Troubleshooting:${NC}"
echo "- If connection refused: Check firewall settings"
echo "- If page doesn't load: Verify both devices are on same network"
echo "- If CORS error: Backend needs to restart with new settings"
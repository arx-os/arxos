#!/bin/bash

# Arxos Access Management Script
# Manage demo access for investors, partners, and team members

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
HTPASSWD_FILE="/etc/nginx/.arxos_demo_htpasswd"
ACCESS_LOG="/opt/arxos/logs/access.log"
DEMO_URL="https://demo.arxos.io"

# Function to show usage
show_usage() {
    echo -e "${BLUE}Arxos Access Management${NC}"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  add-user <username>          Add a new user"
    echo "  remove-user <username>       Remove a user"
    echo "  list-users                   List all users"
    echo "  create-temp <name> <hours>   Create temporary access"
    echo "  share-demo <email>           Send demo access to email"
    echo "  revoke-all                   Revoke all access (except admin)"
    echo "  show-stats                   Show access statistics"
    echo ""
}

# Add user
add_user() {
    local username=$1
    
    if [ -z "$username" ]; then
        echo -e "${RED}Username required${NC}"
        exit 1
    fi
    
    # Generate secure password
    local password=$(openssl rand -base64 12)
    
    # Add to htpasswd
    if [ -f "$HTPASSWD_FILE" ]; then
        htpasswd -b "$HTPASSWD_FILE" "$username" "$password"
    else
        htpasswd -cb "$HTPASSWD_FILE" "$username" "$password"
    fi
    
    # Log access creation
    echo "$(date): User $username created" >> "$ACCESS_LOG"
    
    echo -e "${GREEN}✓ User created successfully${NC}"
    echo ""
    echo "Access Details:"
    echo "  URL:      $DEMO_URL"
    echo "  Username: $username"
    echo "  Password: $password"
    echo ""
    echo "Share these credentials securely!"
}

# Remove user
remove_user() {
    local username=$1
    
    if [ -z "$username" ]; then
        echo -e "${RED}Username required${NC}"
        exit 1
    fi
    
    # Remove from htpasswd
    htpasswd -D "$HTPASSWD_FILE" "$username"
    
    # Log removal
    echo "$(date): User $username removed" >> "$ACCESS_LOG"
    
    echo -e "${GREEN}✓ User $username removed${NC}"
}

# List users
list_users() {
    echo -e "${BLUE}Current Users:${NC}"
    
    if [ -f "$HTPASSWD_FILE" ]; then
        cat "$HTPASSWD_FILE" | cut -d: -f1 | while read user; do
            echo "  • $user"
        done
    else
        echo "  No users configured"
    fi
}

# Create temporary access
create_temp() {
    local name=$1
    local hours=${2:-24}
    
    if [ -z "$name" ]; then
        echo -e "${RED}Name required${NC}"
        exit 1
    fi
    
    # Create username with timestamp
    local username="temp_${name}_$(date +%s)"
    local password=$(openssl rand -base64 8)
    
    # Add user
    htpasswd -b "$HTPASSWD_FILE" "$username" "$password"
    
    # Schedule removal
    echo "htpasswd -D $HTPASSWD_FILE $username" | at now + $hours hours 2>/dev/null
    
    # Log
    echo "$(date): Temporary user $username created for $hours hours" >> "$ACCESS_LOG"
    
    echo -e "${GREEN}✓ Temporary access created${NC}"
    echo ""
    echo "Access Details (valid for $hours hours):"
    echo "  URL:      $DEMO_URL"
    echo "  Username: $username"
    echo "  Password: $password"
    echo ""
    echo "Access will automatically expire in $hours hours"
}

# Share demo via email template
share_demo() {
    local email=$1
    local name=${2:-"Guest"}
    
    if [ -z "$email" ]; then
        echo -e "${RED}Email required${NC}"
        exit 1
    fi
    
    # Create account
    local username=$(echo "$email" | cut -d@ -f1 | tr '.' '_')
    local password=$(openssl rand -base64 12)
    
    htpasswd -b "$HTPASSWD_FILE" "$username" "$password"
    
    # Generate email template
    cat > /tmp/arxos_invite.txt << EOF
Subject: Arxos Demo Access

Hi $name,

You've been granted access to the Arxos demo environment. Here are your credentials:

Demo URL: $DEMO_URL
Username: $username
Password: $password

This demo showcases our AI-powered building intelligence platform:
• Upload building plans (PDF)
• Watch AI extract building components
• See confidence scoring in real-time
• Explore the interactive viewer

For the best experience:
1. Use Chrome or Firefox
2. Allow a few seconds for PDF processing
3. Try the different view modes in the viewer

Your access is valid for 7 days. Please don't share these credentials.

Questions? Reply to this email.

Best regards,
The Arxos Team
EOF
    
    echo -e "${GREEN}✓ Access created for $email${NC}"
    echo ""
    echo "Email template saved to: /tmp/arxos_invite.txt"
    echo "Send this to: $email"
    echo ""
    echo "Or copy this share link:"
    echo "---"
    echo "$DEMO_URL"
    echo "Username: $username"
    echo "Password: $password"
    echo "---"
    
    # Log
    echo "$(date): Demo access created for $email" >> "$ACCESS_LOG"
}

# Revoke all access
revoke_all() {
    echo -e "${YELLOW}This will revoke ALL demo access except admin.${NC}"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled"
        exit 0
    fi
    
    # Backup current file
    cp "$HTPASSWD_FILE" "$HTPASSWD_FILE.backup.$(date +%s)"
    
    # Keep only admin
    local admin_line=$(grep "^admin:" "$HTPASSWD_FILE")
    echo "$admin_line" > "$HTPASSWD_FILE"
    
    # Log
    echo "$(date): All access revoked except admin" >> "$ACCESS_LOG"
    
    echo -e "${GREEN}✓ All access revoked (admin retained)${NC}"
}

# Show statistics
show_stats() {
    echo -e "${BLUE}Access Statistics:${NC}"
    echo ""
    
    # User count
    local user_count=$(cat "$HTPASSWD_FILE" 2>/dev/null | wc -l)
    echo "Active users: $user_count"
    
    # Recent access logs
    echo ""
    echo "Recent activity:"
    tail -5 "$ACCESS_LOG" 2>/dev/null | while read line; do
        echo "  $line"
    done
    
    # Nginx access stats (if available)
    if [ -f "/var/log/nginx/access.log" ]; then
        echo ""
        echo "Recent demo visits:"
        grep "$DEMO_URL" /var/log/nginx/access.log | tail -5 | cut -d' ' -f1,4,7 | while read line; do
            echo "  $line"
        done
    fi
}

# Main script logic
case "$1" in
    add-user)
        add_user "$2"
        ;;
    remove-user)
        remove_user "$2"
        ;;
    list-users)
        list_users
        ;;
    create-temp)
        create_temp "$2" "$3"
        ;;
    share-demo)
        share_demo "$2" "$3"
        ;;
    revoke-all)
        revoke_all
        ;;
    show-stats)
        show_stats
        ;;
    *)
        show_usage
        ;;
esac
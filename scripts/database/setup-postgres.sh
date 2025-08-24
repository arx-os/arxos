#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up PostgreSQL with PostGIS for Arxos...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Parse arguments
ENV="${1:-dev}"
case "$ENV" in
    dev|development)
        COMPOSE_FILE="docker-compose.yml"
        SERVICE="postgres"
        DB_PORT="5432"
        DB_NAME="arxos"
        DB_USER="arxos"
        DB_PASSWORD="arxos_dev"
        ;;
    test|testing)
        COMPOSE_FILE="docker-compose.yml -f docker-compose.test.yml"
        SERVICE="postgres"
        DB_PORT="5433"
        DB_NAME="arxos_test"
        DB_USER="arxos_test"
        DB_PASSWORD="arxos_test"
        ;;
    *)
        echo -e "${RED}Invalid environment: $ENV${NC}"
        echo "Usage: $0 [dev|test]"
        exit 1
        ;;
esac

echo -e "${YELLOW}Starting PostgreSQL for $ENV environment...${NC}"

# Start the database container
cd /Users/joelpate/repos/arxos
docker-compose -f $COMPOSE_FILE up -d $SERVICE redis

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
for i in {1..30}; do
    if docker-compose -f $COMPOSE_FILE exec -T $SERVICE pg_isready -U $DB_USER &>/dev/null; then
        echo -e "${GREEN}PostgreSQL is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Enable PostGIS extension
echo -e "${YELLOW}Enabling PostGIS extension...${NC}"
docker-compose -f $COMPOSE_FILE exec -T $SERVICE psql -U $DB_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS postgis;" || true
docker-compose -f $COMPOSE_FILE exec -T $SERVICE psql -U $DB_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" || true

# Create .env file if it doesn't exist
if [ "$ENV" = "dev" ] || [ "$ENV" = "development" ]; then
    ENV_FILE="/Users/joelpate/repos/arxos/core/.env"
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}Creating .env file...${NC}"
        cat > "$ENV_FILE" << EOF
# Database Configuration
DB_DRIVER=postgres
DB_HOST=localhost
DB_PORT=$DB_PORT
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_SSL_MODE=disable
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:$DB_PORT/$DB_NAME?sslmode=disable

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Server Configuration
PORT=8080
ENV=development

# AI Service
AI_SERVICE_URL=http://localhost:8000

# Auth
JWT_SECRET=your-secret-key-change-in-production
ADMIN_PASSWORD=admin-password-change-in-production
EOF
        echo -e "${GREEN}.env file created at $ENV_FILE${NC}"
    fi
fi

# Run migrations
if [ -d "/Users/joelpate/repos/arxos/core/migrations" ]; then
    echo -e "${YELLOW}Running migrations...${NC}"
    cd /Users/joelpate/repos/arxos/core
    
    # Check if migrate tool is installed
    if ! command -v migrate &> /dev/null; then
        echo -e "${YELLOW}Installing golang-migrate...${NC}"
        go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest
    fi
    
    # Run migrations
    export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@localhost:$DB_PORT/$DB_NAME?sslmode=disable"
    migrate -path migrations -database "$DATABASE_URL" up || true
fi

echo -e "${GREEN}✅ PostgreSQL with PostGIS is ready!${NC}"
echo -e "${BLUE}Connection details:${NC}"
echo "  Host: localhost"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo ""
echo -e "${BLUE}Test connection:${NC}"
echo "  psql -h localhost -p $DB_PORT -U $DB_USER -d $DB_NAME"
echo ""
echo -e "${BLUE}Verify PostGIS:${NC}"
echo "  psql -h localhost -p $DB_PORT -U $DB_USER -d $DB_NAME -c \"SELECT PostGIS_version();\""
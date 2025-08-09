# Arxos Backend

A Go-based backend service for the Arxos platform, providing RESTful APIs for asset management, building information modeling (BIM), and facility management.

## Features

- **Asset Management**: Complete CRUD operations for building assets
- **BIM Integration**: Building Information Modeling object management
- **CMMS Integration**: Computerized Maintenance Management System integration
- **Audit Logging**: Comprehensive audit trail for all operations
- **Security**: JWT-based authentication and role-based access control
- **Data Vendor Management**: Integration with external data vendors
- **Export Functionality**: Data export capabilities
- **Monitoring**: System monitoring and performance analytics

## Project Structure

```
arx-backend/
├── cmd/                    # Command-line tools and utilities
├── db/                     # Database connection and setup
├── handlers/               # HTTP request handlers
├── logic_engine/           # Business logic engine
├── middleware/             # HTTP middleware (auth, security, etc.)
├── migrations/             # Database migration files
├── models/                 # Data models and database schemas
├── scripts/                # Utility scripts
├── services/               # Business logic services
├── test_data/              # Test data and fixtures
├── tests/                  # Test files
├── go.mod                  # Go module dependencies
├── go.sum                  # Go module checksums
├── main.go                 # Application entry point
└── README.md              # This file
```

## Prerequisites

- Go 1.21 or higher
- SQLite3 (for development)
- PostgreSQL (for production)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/capstanistan/arx-backend.git
   cd arx-backend
   ```

2. Install dependencies:
   ```bash
   go mod download
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run database migrations:
   ```bash
   go run cmd/database-performance/main.go
   ```

5. Start the server:
   ```bash
   go run main.go
   ```

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/verify` - Verify JWT token

### Asset Management
- `GET /api/assets` - List all assets
- `POST /api/assets` - Create new asset
- `GET /api/assets/{id}` - Get asset by ID
- `PUT /api/assets/{id}` - Update asset
- `DELETE /api/assets/{id}` - Delete asset

### BIM Objects
- `GET /api/bim-objects` - List BIM objects
- `POST /api/bim-objects` - Create BIM object
- `GET /api/bim-objects/{id}` - Get BIM object by ID

### CMMS Integration
- `GET /api/cmms/connections` - List CMMS connections
- `POST /api/cmms/connections` - Create CMMS connection
- `GET /api/cmms/sync` - Sync CMMS data

### Audit Logs
- `GET /api/audit-logs` - List audit logs
- `GET /api/audit-logs/{id}` - Get audit log by ID

## Development

### Running Tests
```bash
go test ./...
```

### Code Formatting
```bash
go fmt ./...
```

### Linting
```bash
golangci-lint run
```

## Deployment

### Docker
```bash
docker build -t arxos-backend .
docker run -p 8080:8080 arxos-backend
```

### Environment Variables

Required environment variables:
- `DB_CONNECTION_STRING` - Database connection string
- `JWT_SECRET` - Secret key for JWT tokens
- `PORT` - Server port (default: 8080)
- `LOG_LEVEL` - Logging level (debug, info, warn, error)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the GitHub repository.

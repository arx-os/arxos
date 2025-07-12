# arx-database

## Overview
Database schema and migration service for the Arxos platform. Uses PostgreSQL with PostGIS extensions for geospatial data support, version tracking, and object metadata.

## Tech Stack
- PostgreSQL 15+
- PostGIS
- SQLC / GORM (Go ORM)
- Flyway or Golang-migrate for migrations

## Features
- Versioned building repositories
- Object metadata & logs
- User accounts & roles
- Permissions, shares, and payout tracking

## Project Structure
```
/arx-database
├── migrations/
├── schemas/
├── seeds/
└── README.txt
```

## Usage
Deployed alongside backend. Accessed via `arx-backend` using ORM or raw SQL.

## User Roles & Data Flow

### User Roles
- Managed in the backend, persisted in the database. See `arx-backend` for role definitions.

### Data Flow
1. All user, building, markup, and log data is stored and versioned in PostgreSQL.
2. Backend mediates all database access and enforces permissions.

## Cross-Reference APIs
- **arx-backend:** Primary consumer of the database; all data access flows through backend logic.
- **arx-web-frontend & arx-ios-app:** Indirectly interact with the database via backend API.
- **arx_svg_parser:** Outputs parsed/annotated SVG data, persisted via backend.

## Development & Testing
- Migration testing: `flyway`/`golang-migrate`
- ORM model/unit tests via backend

## License / Confidentiality
© Arxos — Confidential. Internal MVP development only.

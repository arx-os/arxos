# arx-backend

## Overview
This is the Go-based backend for the Arxos platform. It handles authentication, version-controlled building data, object CRUD, AI integrations, and serves API requests from the frontend and mobile clients.

## Tech Stack
- Golang (Chi framework)
- PostgreSQL + PostGIS
- Azure AD (Auth)
- JSON-based API
- Optional: gRPC for microservice comms

## Features
- SVG-BIM and ASCII-BIM repo management
- User & permission handling
- AI/NLP service proxying
- Arxfile.yaml parsing and validation
- Data sync and share payout handling

## Project Structure
```
/arx-backend
├── cmd/
├── internal/
│   ├── handlers/
│   ├── services/
│   ├── models/
├── config/
├── main.go
└── README.txt
```

## Usage
Primary backend API service for the Arxos platform. Serves both web frontend and mobile clients.

## User Roles & Data Flow

### User Roles
#### Owner / Manager
- Admin privileges over one or more properties.
- Full markup/editing capabilities.
- Can assign edit permissions to contractors.
- Can toggle a building as "open" for collaborative markup.
- Access to maintenance dashboard (CMMS-lite design).

#### Builder / Contractor
- Default: View-only.
- Can be granted markup/edit access for specific MEP categories.
- Must submit markups for Owner approval.
- All actions logged for transparency and reputation tracking.

#### Guest
- View-only access.
- No markup privileges.

### Data Flow
1. Web and mobile clients authenticate via Azure AD through the backend.
2. Backend mediates all data access to the PostgreSQL database.
3. API endpoints expose building, SVG, markup, user, and logbook resources.
4. For SVG parsing/markup, backend calls out to the `arx_svg_parser` microservice.

#### SVG Interaction Model

**View Mode**
- Default mode for all users.
- SVG is interactive but not editable.

**Edit Mode**
- Requires permission toggle.
- Enables markup and annotation tools.
- "Save?" prompt appears after any changes.
- Saved versions become the active state; full edit history is retained.
- > **Note:** Historical versions and markup history will be accessible via a paid subscription tier.

**Edit Permissions**
- By default, only Owners can edit.
- Editing rights can be delegated by trade (e.g., Electrical).
- Trade-specific editing limits Builder access to only relevant layers.

#### MEP Systems & SVG Markup
All system elements are color-coded and filterable via a sidebar toggle:

| System        | Code | Description            | Color       |
|---------------|------|------------------------|-------------|
| Electrical    | E    | Medium/High-voltage    | Purple      |
| Low Voltage   | LV   | Controls, security     | Orange      |
| Fire Alarm    | FA   | FA wiring, panels      | Pink        |
| Network/Data  | N    | Ethernet, Wi-Fi, switch| Yellow      |
| Mechanical    | M    | HVAC/R, motors         | Green       |
| Plumbing      | P    | Cold/Hot water (Red)   | Blue/Red    |
| Structural    | -    | Walls, doors, windows  | Black       |

- Structural elements are editable but do not expose frequent editing tools.
- Each markup action is associated with a user, logged, and auditable.

#### Object ID Naming Convention Version 1
Arxos Object Naming Convention (MVP)
Each object in the SVG/ASCII-BIM system must follow:
`BuildingID_Floor_SystemCode_ObjectType_Instance`

Example: `TCHS_L2_E_Receptacle_015`

Legend:
- BuildingID: 3–10 uppercase alphanumeric characters
- Floor: L1, L2, etc.
- SystemCode: E, LV, FA, N, M, P
- ObjectType: PascalCase (e.g., Receptacle)
- Instance: Zero-padded 3-digit sequence (e.g., 015)

**System Codes & Object Hierarchies**
(Original README includes full breakdown for Electrical, Low Voltage, Fire Alarm, Network/Data, Mechanical, Plumbing; keep those tables here.)

**Validation Schema Pattern:**  
`^[A-Z0-9]{3,10}_L[0-9]{1,2}_(E|LV|FA|N|M|P)_[A-Z][a-zA-Z]+_[0-9]{3}$`

## Cross-Reference APIs
- **Frontend:** Consumes backend API for all building, markup, and logbook operations.
- **Mobile App:** Syncs object, markup, and user data via backend API.
- **arx_svg_parser:** Backend calls `/parse`, `/annotate`, `/scale` endpoints for SVG operations.
- **Database:** Backend uses ORM/raw SQL for all persistent data.

## Development & Testing

### API Documentation
The Arxos backend is composed of two main API surfaces:
1. **Go API (Core Backend)**
2. **Python Microservices (SVG Parsing, File Ingestion, ML/AI Processing)**

#### Go API (Main Application Server)
Base URL: `http://localhost:8080`  
All requests use JSON and follow RESTful conventions.

**Authentication:**  
- All protected routes use bearer token authorization.
- Owners and Builders have scoped access depending on roles and permissions.

Headers:
```
Authorization: Bearer <your_token_here>
Content-Type: application/json
```

**Endpoints (MVP Phase):**

| Method | Endpoint                     | Description                                      | Auth Required |
|--------|------------------------------|--------------------------------------------------|---------------|
| GET    | `/buildings`                | Get all buildings for the current user           | ✅            |
| ...    | ...                          | ...                                              | ...           |

**Example Request: Submit a Markup**
```http
POST /markup HTTP/1.1
Host: localhost:8080
Authorization: Bearer abc123
Content-Type: application/json

{
  "building_id": "bldg-789",
  "floor_id": "floor-2",
  "system": "E",
  "elements": [
    {
      "type": "outlet",
      "coordinates": [120, 340],
      "note": "20A dedicated circuit"
    }
  ]
}
```

#### Testing & QA
- Go’s built-in testing tools (`go test`)
- API & integration tests for handlers/services
- Use mocks/stubs for external services or I/O.
- Coverage reporting via `go test -coverprofile=coverage.out ./...`
- CI Integration planned (GitHub Actions/Drone CI)

### Error Handling

| Error Type         | HTTP Code | Example Message                                 | When Triggered                        |
|--------------------|-----------|------------------------------------------------|---------------------------------------|
| Invalid Object ID  | 400       | Invalid object ID format: <id>                  | On any invalid object ID              |
| ...                | ...       | ...                                            | ...                                   |

**Notes for Integrators**
- Always check for HTTP 400 responses and parse the error message for details.
- Ensure all IDs and references are valid before submitting requests.

## License / Confidentiality
© Arxos — Confidential. Internal MVP development only.

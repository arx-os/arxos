# Onboarding

Welcome to the Arxos platform! This guide will help you get started as a developer, integrator, or contributor.

---

## 1. Prerequisites

- [x] Git and GitHub account access
- [x] Access to the `arx-*` repositories (request if needed)
- [x] Local environment: Go (for backend), Python 3.x (for parser), Node.js (optional for frontend tooling), Swift (for iOS)
- [x] Docker (optional for local services)
- [x] Access to organization secrets (ask admin for credentials)

---

## 2. Repository Structure

- `/arx-backend`: Go backend API server
- `/arx-database`: Database schema, migrations, and seeds
- `/arx-infra`: Infrastructure as Code (Terraform, Docker, CI/CD)
- `/arx-web-frontend`: HTMX/Tailwind web UI
- `/arx-ios-app`: iOS native app
- `/arx_svg_parser`: Python SVG parsing microservice
- `/arx-docs`: Documentation and specs (this repo)

---

## 3. Local Development Setup

### Backend

```bash
git clone https://github.com/<org>/arx-backend.git
cd arx-backend
go mod download
go run main.go
```

### SVG Parser Microservice

```bash
git clone https://github.com/<org>/arx_svg_parser.git
cd arx_svg_parser
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 5000
```

### Web Frontend

```bash
git clone https://github.com/<org>/arx-web-frontend.git
cd arx-web-frontend
# Install dependencies if needed (npm/yarn)
```

### Database

- Provision using `/arx-infra` scripts or use local Postgres (see `/arx-database/README.md`).

---

## 4. Key Documentation

- [BUILDING_SYSTEMS_LIBRARY.md](./BUILDING_SYSTEMS_LIBRARY.md): Object conventions and system codes
- [API_REFERENCE.md](./API_REFERENCE.md): Endpoints and integration
- [CONTRIBUTING.md](./CONTRIBUTING.md): Standards and PR process

---

## 5. Getting Help

- Ask questions in the team chat or open a discussion in `/arx-docs`.
- For access issues, contact your project lead or admin.

---

Welcome aboard!

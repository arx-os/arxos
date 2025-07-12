# arx-android

## Overview
Native Kotlin-based mobile app for interacting with Arxos building data in the field. Enables offline viewing, AR markup, object inspection, and scan capture on Android devices.

## Tech Stack
- Kotlin (Android native)
- ARCore
- CameraX / Android Sensors
- SQLite or offline-first storage
- API sync with Arx Backend

## Features
- Offline-first repo sync
- AR object overlay + inspection
- Room scan & SVG sync
- Markup tools with symbol library
- Role-based access

## Project Structure
```
/arx-android
├── app/
├── views/
├── models/
├── ar/
├── networking/
├── assets/
└── README.md
```

## Usage
Distributed via Google Play internal testing or sideloaded APK. Authenticates with Azure and syncs with backend.

## User Roles & Data Flow

### User Roles
- **Owner / Manager:** Full access to building data, markup, and dashboard.
- **Builder / Contractor:** View and markup permissions as granted.
- **Guest:** View-only.

### Data Flow
1. User authenticates via Azure AD.
2. App syncs data and markups with backend API for both online and offline operation.
3. Markups and scans are uploaded and merged via backend endpoints.

## Cross-Reference APIs
- API calls to `arx-backend` for all object, user, and markup data.
- SVG viewing/markup may interact with backend’s SVG endpoints (which proxy to `arx_svg_parser`).
- For object models, system codes, and API contracts, see [`arx-docs`](https://github.com/capstanistan/arx-docs).

## Development & Testing
- Android Instrumentation Tests, JUnit for unit/UI tests
- Manual QA for AR/scan features

## License / Confidentiality
© Arxos — Confidential. Internal MVP development only.

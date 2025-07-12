# Arx CLI (`arx-cli`)

The Arx command-line interface for infrastructure as code, ASCII-BIM, remote/offline repo management, and workflow automation.

## Overview
`arx-cli` enables developers, integrators, and operators to manage building repositories, sync data, and automate infrastructure workflows from the terminal. It is crucial for representing buildings as code and operating in low-connectivity or air-gapped environments.

## Features
- Git-style commands for initializing, editing, and syncing building models
- ASCII-BIM support for terminal-friendly building markup and review
- P2P and offline sync (via ArxLink protocol)
- Bulk import/export, audit, and simulation tools
- Integration hooks for CI/CD, validation, and remote automation

## Documentation
- **Reference Docs:** [arx-docs](https://github.com/capstanistan/arx-docs)
    - [SYNC_AGENT_SPECIFICATION.md](https://github.com/capstanistan/arx-docs/blob/main/SYNC_AGENT_SPECIFICATION.md) – CLI commands, sync agent, offline usage
    - [API_REFERENCE.md](https://github.com/capstanistan/arx-docs/blob/main/API_REFERENCE.md) – API contracts and integration
- **Conventions:** Follow system codes, object models, and data schemas from `/arx-docs`

## Usage
- Run `arx init`, `arx add`, `arx commit`, `arx sync`, etc., to manage building repositories.
- Reference [arx-docs](https://github.com/capstanistan/arx-docs) for standards, object types, and integration guidance.

## Contribution
- Follow onboarding and contribution guides in [arx-docs](https://github.com/capstanistan/arx-docs)
- All changes require PR review and documentation cross-linking.

## License / Confidentiality
© Arxos — Confidential. Internal MVP documentation only.

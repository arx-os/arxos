# ArxOS Desktop Agent

The desktop companion bridges the browser PWA and the local filesystem/Git repository. It runs on
loopback, authenticates requests with a DID:key token, and exposes a WebSocket API for high-trust
operations that cannot run inside the browser sandbox.

## Features (MVP)

- Health endpoint (`/health`)
- Capability discovery (`/capabilities`)
- WebSocket interface (`/ws`) with:
  - `ping`, `version`, `capabilities`
  - `git.status`, `git.diff`, `git.commit`
  - `files.read` for safe workspace file access
  - `ifc.import` (base64 upload → YAML) and `ifc.export` (full/delta IFC back to browser)
  - `auth.rotate`, `auth.negotiate` for DID token rotation and capability negotiation
- Authentication via DID:key token (`--token` or `ARXOS_AGENT_TOKEN`)
- Structured logging (`--log-format compact|json`)
- Graceful shutdown on SIGINT / SIGTERM

## Running

```bash
cargo run -p arxos-agent -- --host 127.0.0.1 --port 8787 --token did:key:zexample --log-format json
```

If no token is provided, the agent generates an ephemeral DID and prints it to the console. The PWA
must present the same token as a `token` query parameter when opening the WebSocket.

### Token rotation & capability negotiation

- `auth.rotate` lets you replace the active DID token from an authenticated session. The agent returns the new token and rotated timestamp—clients should reconnect with the new credential.
- `auth.negotiate` accepts a list of desired capabilities and narrows the active scope to an approved subset. The response includes both granted and denied capabilities so callers can adapt.

## TODO

- Secure DID:key verification and rotation
- File write APIs with sandbox policies
- Structured logging and metrics forwarding

